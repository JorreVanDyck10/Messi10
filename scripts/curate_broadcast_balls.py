"""Deterministic visual review and explicit curation of broadcast ball labels."""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from scripts.review_broadcast_data import font


def prepare(root, destination):
    source = read_json(root / "manifest.json")
    if (destination / "candidates.json").exists():
        saved = read_json(destination / "candidates.json")
        if digest_json({k: v for k, v in saved.items() if k != "fingerprint"}) != saved["fingerprint"]:
            raise ValueError("Candidate manifest fingerprint changed")
        if saved["source_fingerprint"] != source["fingerprint"]:
            raise ValueError("Source dataset changed")
        return saved
    destination.mkdir(parents=True, exist_ok=True)
    groups = defaultdict(list)
    flagged = {"SNGS-071_000371", "SNGS-097_000376"}
    candidates = []
    for row in source["frames"]:
        if len([b for b in row["boxes"] if b["class_id"] == 2]) == 1:
            groups[row["clip"]].append(row)
            if row["frame_id"] in flagged:
                candidates.append(row)
    for clip in sorted(groups):
        rows = groups[clip]
        for index in sorted({len(rows) // 3, 2 * len(rows) // 3}):
            row = rows[index]
            if row["frame_id"] not in {r["frame_id"] for r in candidates}:
                candidates.append(row)
    records = []
    for index, row in enumerate(candidates):
        box = next(b["bbox_xyxy"] for b in row["boxes"] if b["class_id"] == 2)
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        left, top = math.floor(cx) - 40, math.floor(cy) - 40
        records.append({"candidate_id": index, "frame_id": row["frame_id"], "split": row["split"],
                        "game_id": row["game_id"], "clip": row["clip"], "image": row["image"],
                        "image_sha256": row["image_sha256"], "source_label_sha256": row["label_sha256"],
                        "width": row["width"], "height": row["height"], "bbox_xyxy": box,
                        "crop_origin": [left, top], "crop_size": 80, "display_scale": 3,
                        "page": index // 24 + 1, "tile": index % 24})
    manifest = {"source_fingerprint": source["fingerprint"], "source": source["source"],
                "selection": "known flagged frames, then two evenly distributed positive frames per clip",
                "reviewer_type": "AI visual review; no human approval", "candidates": records}
    manifest["fingerprint"] = digest_json(manifest)
    write_json(destination / "candidates.json", manifest)
    return manifest


def render(root, destination, manifest):
    for page in range(1, max(c["page"] for c in manifest["candidates"]) + 1):
        canvas = Image.new("RGB", (1440, 1080), "#111827")
        for candidate in (c for c in manifest["candidates"] if c["page"] == page):
            left, top = candidate["crop_origin"]
            with Image.open(root / candidate["image"]) as original:
                crop = original.crop((left, top, left + 80, top + 80)).resize((240, 240))
            box = candidate["bbox_xyxy"]
            ImageDraw.Draw(crop).rectangle(((box[0] - left) * 3, (box[1] - top) * 3,
                                           (box[2] - left) * 3, (box[3] - top) * 3), outline="#ff4565", width=1)
            x, y = candidate["tile"] % 6 * 240, candidate["tile"] // 6 * 270
            canvas.paste(crop, (x, y + 30))
            ImageDraw.Draw(canvas).text((x + 4, y + 5),
                f"{candidate['candidate_id']:03d} {candidate['frame_id']}", fill="white", font=font(15))
        canvas.save(destination / f"review-{page:02d}.jpg", quality=97)


def export(root, destination, manifest, decisions_path):
    decisions = read_json(decisions_path)
    if digest_json({k: v for k, v in manifest.items() if k != "fingerprint"}) != manifest["fingerprint"]:
        raise ValueError("Candidate manifest fingerprint changed")
    if decisions["candidate_fingerprint"] != manifest["fingerprint"]:
        raise ValueError("Review decisions belong to a different frozen candidate sample")
    by_id = {c["candidate_id"]: c for c in manifest["candidates"]}
    reviewed, frames = set(), []
    output = destination / "curated"
    for decision in decisions["decisions"]:
        index = decision["candidate_id"]
        if index in reviewed or index not in by_id:
            raise ValueError("Duplicate or unknown candidate review")
        reviewed.add(index)
        if decision["status"] not in {"accept", "correct", "reject"}:
            raise ValueError("Every review needs an explicit disposition")
        if not decision.get("reason"):
            raise ValueError("Review needs a concrete observation")
        if decision["status"] == "reject":
            continue
        row = by_id[index]
        box = decision.get("corrected_bbox_xyxy") if decision["status"] == "correct" else row["bbox_xyxy"]
        if (not isinstance(box, list) or len(box) != 4 or not all(math.isfinite(v) for v in box)
                or not 0 <= box[0] < box[2] <= row["width"]
                or not 0 <= box[1] < box[3] <= row["height"]):
            raise ValueError("Invalid reviewed ball box")
        image = output / "images" / row["split"] / (row["frame_id"] + ".jpg")
        label = output / "labels" / row["split"] / (row["frame_id"] + ".txt")
        image.parent.mkdir(parents=True, exist_ok=True)
        label.parent.mkdir(parents=True, exist_ok=True)
        if sha256_file(root / row["image"]) != row["image_sha256"]:
            raise ValueError("Candidate image changed since review")
        if not image.exists():
            image.hardlink_to(root / row["image"])
        text = (f"0 {(box[0]+box[2])/2/row['width']:.9f} {(box[1]+box[3])/2/row['height']:.9f} "
                f"{(box[2]-box[0])/row['width']:.9f} {(box[3]-box[1])/row['height']:.9f}\n")
        if label.exists() and label.read_text(encoding="utf-8") != text:
            raise ValueError("Preserve existing curated edits; choose a new curation version")
        label.write_text(text, encoding="utf-8")
        frames.append({**row, "bbox_xyxy": box, "label": label.relative_to(output).as_posix(),
                       "image": image.relative_to(output).as_posix(), "label_sha256": sha256_file(label),
                       "decision": decision, "project_human_review_completed": False})
    if reviewed != set(by_id):
        raise ValueError("Every candidate must be reviewed before publishing the curated set")
    games = {s: {r["game_id"] for r in frames if r["split"] == s} for s in ("train", "val")}
    if games["train"] & games["val"] or not all(games.values()):
        raise ValueError("Need disjoint nonempty match splits")
    result = {"dataset_version": "broadcast-balls-ai-curated-v1", "source_fingerprint": manifest["source_fingerprint"],
              "candidate_fingerprint": manifest["fingerprint"], "decisions_sha256": sha256_file(decisions_path),
              "frames": frames, "names": {0: "ball"}, "counts": {s: sum(r["split"] == s for r in frames) for s in games},
              "match_ids": {s: sorted(v) for s, v in games.items()}, "reviewer": "Codex (AI)",
              "project_human_review_completed": False, "negative_frames": 0,
              "limitations": "AI-reviewed positive sample; not an independent test or full ball benchmark"}
    result["fingerprint"] = digest_json(result)
    write_json(output / "manifest.json", result)
    (output / "data.yaml").write_text(yaml.safe_dump({"path": str(output), "train": "images/train",
         "val": "images/val", "names": {0: "ball"}}, sort_keys=False), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/broadcast-sngsr-v1"))
    parser.add_argument("--output", type=Path, default=Path("data/broadcast-ball-review-v1"))
    parser.add_argument("--decisions", type=Path)
    args = parser.parse_args()
    root, destination = args.root.resolve(), args.output.resolve()
    manifest = prepare(root, destination)
    if args.decisions:
        result = export(root, destination, manifest, args.decisions)
        print({k: result[k] for k in ("counts", "match_ids", "fingerprint")})
    else:
        render(root, destination, manifest)
        print(f"Prepared {len(manifest['candidates'])} review candidates")
