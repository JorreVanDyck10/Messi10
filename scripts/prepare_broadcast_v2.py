"""Native ball crops, explicitly reviewed negatives and less redundant player training."""

from __future__ import annotations

import argparse
import math
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
import yaml
from PIL import Image, ImageDraw

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from scripts.review_broadcast_data import font

SIZE = 640


def intersect(a, b):
    """Geef aan of twee xyxy-rechthoeken een positieve overlappende oppervlakte hebben."""
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def positive_window(box, width, height, identity, variant):
    """Kies deterministisch een beeldvenster rond de bal, met de ingestelde variant en begrensd door het
    bronformaat.
    """
    if min(width, height) < SIZE:
        raise ValueError("Native crop requires an image at least 640 pixels in both dimensions")
    if box[2] - box[0] >= SIZE or box[3] - box[1] >= SIZE:
        raise ValueError("Ball does not fit the native crop")
    seed = digest_json([identity, variant])
    fx, fy = [0.25 + int(seed[i : i + 4], 16) / 65535 * 0.5 for i in (0, 4)]
    x = max(0, min(width - SIZE, round((box[0] + box[2]) / 2 - SIZE * fx)))
    y = max(0, min(height - SIZE, round((box[1] + box[3]) / 2 - SIZE * fy)))
    window = [x, y, x + SIZE, y + SIZE]
    if not (x <= box[0] < box[2] <= x + SIZE and y <= box[1] < box[3] <= y + SIZE):
        raise ValueError("Crop would truncate the reviewed ball")
    return window


def tile(root, output, row, window, kind, suffix, box=None):
    """Schrijf één bronpixeltegel en bijbehorende labels en retourneer het framerecord met bronvenster en
    ouderframe.
    """
    fid = row["frame_id"] + suffix
    image = output / "images" / row["split"] / f"{fid}.png"
    label = output / "labels" / row["split"] / f"{fid}.txt"
    for directory in (image.parent, label.parent):
        directory.mkdir(parents=True, exist_ok=True)
    if sha256_file(root / row["image"]) != row["image_sha256"]:
        raise ValueError("Reviewed source image changed")
    with Image.open(root / row["image"]) as original:
        pixels = original.convert("RGB").crop(tuple(window))
        pixels.save(image, compress_level=2)
    labels = ""
    relative_box = None
    if box is not None:
        x, y = window[:2]
        relative_box = [box[0] - x, box[1] - y, box[2] - x, box[3] - y]
        labels = (
            f"0 {((box[0] + box[2]) / 2 - x) / SIZE:.9f} {((box[1] + box[3]) / 2 - y) / SIZE:.9f} "
            f"{(box[2] - box[0]) / SIZE:.9f} {(box[3] - box[1]) / SIZE:.9f}\n"
        )
    label.write_text(labels, encoding="utf-8")
    return {
        "frame_id": fid,
        "parent_frame_id": row["frame_id"],
        "game_id": row["game_id"],
        "clip": row["clip"],
        "split": row["split"],
        "kind": kind,
        "window_xyxy": window,
        "source_image_sha256": row["image_sha256"],
        "source_image": str((root / row["image"]).resolve()),
        "image": image.relative_to(output).as_posix(),
        "label": label.relative_to(output).as_posix(),
        "image_sha256": sha256_file(image),
        "label_sha256": sha256_file(label),
        "bbox_xyxy": relative_box,
        "width": SIZE,
        "height": SIZE,
        "project_human_review_completed": False,
    }


def player_selection(root, source, output):
    """Selecteer minder redundante spelersbeelden en schrijf hun datasetweergave met behoud van
    oorspronkelijke splits.
    """
    groups = defaultdict(list)
    rows, metrics = [], []
    for row in source["frames"]:
        if row["split"] == "val":
            rows.append(row)
        else:
            groups[(row["clip"], row["source_frame_index"] // 25)].append(row)
    for key in sorted(groups):
        ranked = []
        for row in groups[key]:
            pixels = cv2.imread(str(root / row["image"]), cv2.IMREAD_GRAYSCALE)
            if pixels is None:
                raise ValueError("Cannot decode selection candidate")
            pixels = cv2.resize(pixels, (320, 180))
            sharpness = float(cv2.Laplacian(pixels, cv2.CV_32F).var())
            refs = sum(b["class_id"] == 1 for b in row["boxes"])
            # Source labels only; no model predictions or validation tuning.
            ranked.append(((refs, math.log1p(sharpness), -row["source_frame_index"]), row))
        score, row = max(ranked, key=lambda item: item[0])
        rows.append(row)
        metrics.append(
            {
                "frame_id": row["frame_id"],
                "bin": list(key),
                "candidate_count": len(ranked),
                "referee_count": score[0],
                "sharpness_log": score[1],
            }
        )
    records = []
    for row in sorted(rows, key=lambda row: (row["split"], row["frame_id"])):
        image = output / row["image"]
        label = output / row["label"]
        image.parent.mkdir(parents=True, exist_ok=True)
        label.parent.mkdir(parents=True, exist_ok=True)
        image.hardlink_to(root / row["image"])
        lines = [
            s
            for s in (root / row["label"]).read_text(encoding="utf-8").splitlines()
            if s.strip() and int(s.split()[0]) in (0, 1)
        ]
        label.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        fields = (
            "frame_id",
            "split",
            "game_id",
            "clip",
            "source_frame_index",
            "width",
            "height",
            "image",
            "label",
            "image_sha256",
        )
        records.append(
            {
                **{k: row[k] for k in fields},
                "label_sha256": sha256_file(label),
                "source_label_sha256": row["label_sha256"],
                "boxes": [b for b in row["boxes"] if b["class_id"] in (0, 1)],
            }
        )
    manifest = {
        "source_fingerprint": source["fingerprint"],
        "frames": records,
        "counts": dict(Counter(r["split"] for r in records)),
        "selection": "one train frame per clip-second, prefer source-labelled referees then sharpness",
        "validation": "all 2000 original validation frames retained unchanged",
        "selection_metrics": metrics,
        "project_human_review_completed": False,
    }
    manifest["fingerprint"] = digest_json(manifest)
    write_json(output / "manifest.json", manifest)
    (output / "data.yaml").write_text(
        yaml.safe_dump(
            {
                "path": str(output),
                "train": "images/train",
                "val": "images/val",
                "names": {0: "player", 1: "referee"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return manifest


def negatives(root, source, original, output):
    """Maak kandidaatbeelden zonder gelabelde bal voor afzonderlijke visuele beoordeling voordat ze als
    negatief mogen meetrainen.
    """
    original_by_id = {r["frame_id"]: r for r in original["frames"]}
    groups = defaultdict(list)
    for row in source["frames"]:
        groups[(row["split"], row["game_id"])].append(row)
    records = []
    for (split, game), group in sorted(groups.items()):
        wanted = 8 if split == "train" else 4
        ordered = sorted(group, key=lambda row: digest_json(["negative-crops-v2", row["frame_id"]]))
        clips, accepted = set(), 0
        for row in ordered:
            if accepted >= wanted:
                break
            if row["clip"] in clips and len(clips) < len({r["clip"] for r in group}):
                continue
            box = row["bbox_xyxy"]
            padded = [box[0] - 48, box[1] - 48, box[2] + 48, box[3] + 48]
            windows = [
                [x, y, x + SIZE, y + SIZE]
                for x in (0, row["width"] - SIZE)
                for y in (0, row["height"] - SIZE)
            ]
            choices = []
            for window in windows:
                if intersect(window, padded):
                    continue
                people = [
                    b
                    for b in original_by_id[row["frame_id"]]["boxes"]
                    if b["class_id"] != 2 and intersect(window, b["bbox_xyxy"])
                ]
                score = len(people) + 3 * sum(b["class_id"] == 1 for b in people)
                choices.append((score, window))
            if not choices:
                continue
            _, window = max(choices)
            record = tile(root, output, row, window, "unreviewed_negative", "-negative")
            record["candidate_id"] = len(records)
            records.append(record)
            clips.add(row["clip"])
            accepted += 1
        if accepted != wanted:
            raise ValueError(f"Not enough distinct negative candidates for game {game}")
    return records


def render_negatives(output, records):
    """Teken de negatieve kandidaten op controlepagina's met voldoende context voor de visuele
    beslissing.
    """
    for page in range(math.ceil(len(records) / 4)):
        canvas = Image.new("RGB", (1280, 1340), "#111827")
        for i, row in enumerate(records[page * 4 : page * 4 + 4]):
            x, y = i % 2 * SIZE, i // 2 * 670
            with Image.open(output / row["image"]) as image:
                canvas.paste(image, (x, y + 30))
            ImageDraw.Draw(canvas).text(
                (x + 5, y + 5),
                f"{row['candidate_id']:02d} {row['parent_frame_id']} {row['split']}",
                font=font(18),
                fill="white",
            )
        canvas.save(output / f"negative-review-{page + 1:02d}.jpg", quality=96)


def prepare(base, balls, output):
    """Maak de spelersselectie, positieve balcrops en negatieve reviewkandidaten als afzonderlijke,
    traceerbare voorbereidingsstappen.
    """
    if output.exists():
        raise ValueError("Choose a fresh version; existing labels and reviews are preserved")
    output.mkdir(parents=True)
    source, curated = read_json(base / "manifest.json"), read_json(balls / "manifest.json")
    players = player_selection(base, source, output / "players")
    positives = []
    for row in curated["frames"]:
        for variant in range(3 if row["split"] == "train" else 1):
            window = positive_window(row["bbox_xyxy"], row["width"], row["height"], row["frame_id"], variant)
            positives.append(
                tile(
                    balls,
                    output / "ball-positives",
                    row,
                    window,
                    "positive",
                    f"-crop{variant}",
                    row["bbox_xyxy"],
                )
            )
    negative_rows = negatives(balls, curated, source, output / "negative-candidates")
    render_negatives(output / "negative-candidates", negative_rows)
    manifest = {
        "source_fingerprint": source["fingerprint"],
        "curated_ball_fingerprint": curated["fingerprint"],
        "positive_frames": positives,
        "negative_candidates": negative_rows,
        "player_counts": players["counts"],
        "negative_review_completed": False,
        "source_frame_count": len(curated["frames"]),
        "native_tile_size": SIZE,
        "training_config_published": False,
        "project_human_review_completed": False,
    }
    manifest["fingerprint"] = digest_json(manifest)
    write_json(output / "preparation.json", manifest)
    print(
        {
            "players": players["counts"],
            "positive_crops": dict(Counter(r["split"] for r in positives)),
            "negative_candidates": len(negative_rows),
        },
        flush=True,
    )


def finalize(base, output, decisions_path, coco_names=None):
    """Verwerk de expliciete negatieve beslissingen, schrijf de definitieve balset en leg de gebruikte
    klassemapping en herkomst vast.
    """
    from persoon1.core import label_pixels, read_labels

    prep = read_json(output / "preparation.json")
    if digest_json({k: v for k, v in prep.items() if k != "fingerprint"}) != prep["fingerprint"]:
        raise ValueError("Prepared data fingerprint changed")
    decisions = read_json(decisions_path)
    if decisions["preparation_fingerprint"] != prep["fingerprint"]:
        raise ValueError("Negative review belongs to a different preparation")
    reviewed = {r["candidate_id"]: r for r in decisions["decisions"]}
    expected = {r["candidate_id"] for r in prep["negative_candidates"]}
    if len(reviewed) != len(decisions["decisions"]) or set(reviewed) != expected:
        raise ValueError("Every negative candidate must be explicitly reviewed once")
    if any(r["status"] not in {"accept", "reject"} or not r.get("reason") for r in reviewed.values()):
        raise ValueError("Negative review needs an explicit disposition and observation")
    destination = output / "balls"
    if destination.exists():
        raise ValueError("Preserve an existing finalized dataset; use a new version")
    rows = [(output / "ball-positives", r) for r in prep["positive_frames"]]
    rows += [
        (
            output / "negative-candidates",
            {**r, "kind": "reviewed_negative", "review": reviewed[r["candidate_id"]]},
        )
        for r in prep["negative_candidates"]
        if reviewed[r["candidate_id"]]["status"] == "accept"
    ]
    records, duplicates, windows, hashes = [], [], set(), set()
    for source_root, row in rows:
        key = (row["parent_frame_id"], tuple(row["window_xyxy"]))
        if key in windows:
            duplicates.append(row["frame_id"])
            continue
        windows.add(key)
        for kind in ("image", "label"):
            if sha256_file(source_root / row[kind]) != row[kind + "_sha256"]:
                raise ValueError("Prepared image or label changed since review")
        if sha256_file(row["source_image"]) != row["source_image_sha256"]:
            raise ValueError("Original image changed")
        with Image.open(row["source_image"]) as original, Image.open(source_root / row["image"]) as crop:
            expected_pixels = np.asarray(original.convert("RGB").crop(tuple(row["window_xyxy"])))
            if crop.size != (SIZE, SIZE) or not np.array_equal(expected_pixels, np.asarray(crop)):
                raise ValueError("Native crop changed pixels or was resized")
        boxes = read_labels(source_root / row["label"], 1)
        if row["kind"] == "positive":
            if len(boxes) != 1 or any(
                abs(a - b) > 0.00001 for a, b in zip(label_pixels(boxes[0], SIZE, SIZE), row["bbox_xyxy"])
            ):
                raise ValueError("Cropped YOLO box does not round-trip to source pixels")
        elif boxes:
            raise ValueError("Reviewed negative unexpectedly contains labels")
        if row["image_sha256"] in hashes:
            raise ValueError("Exact duplicate cropped image")
        hashes.add(row["image_sha256"])
        image, label = destination / row["image"], destination / row["label"]
        image.parent.mkdir(parents=True, exist_ok=True)
        label.parent.mkdir(parents=True, exist_ok=True)
        image.hardlink_to(source_root / row["image"])
        label.write_bytes((source_root / row["label"]).read_bytes())
        records.append(row)
    games = defaultdict(set)
    for row in records:
        games[row["game_id"]].add(row["split"])
    if any(len(splits) != 1 for splits in games.values()):
        raise ValueError("Source match leaked between splits")
    counts = Counter(r["split"] for r in records)
    negative_counts = Counter(r["split"] for r in records if r["kind"] == "reviewed_negative")
    if any(negative_counts[s] < 1 or counts[s] <= negative_counts[s] for s in ("train", "val")):
        raise ValueError("Both splits need positive and reviewed negative examples")
    result = {
        "source_preparation_fingerprint": prep["fingerprint"],
        "negative_decisions_sha256": sha256_file(decisions_path),
        "names": {0: "ball"},
        "frames": records,
        "counts": dict(counts),
        "negative_counts": dict(negative_counts),
        "unique_source_frames": len({r["parent_frame_id"] for r in records}),
        "duplicate_windows_excluded": duplicates,
        "native_pixel_identity_verified": True,
        "project_human_review_completed": False,
        "reviewer": "Codex (AI)",
        "scope": "Development crop task; multiple crops are correlated, full-frame performance must be measured separately",
    }
    result["fingerprint"] = digest_json(result)
    write_json(destination / "manifest.json", result)
    (destination / "data.yaml").write_text(
        yaml.safe_dump(
            {"path": str(destination), "train": "images/train", "val": "images/val", "names": {0: "ball"}},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    if coco_names is not None:
        if set(coco_names) != set(range(80)) or coco_names[32] != "sports ball":
            raise ValueError("Need the actual 80-class COCO head with sports ball at class 32")
        coco = output / "ball-coco"
        coco_rows = []
        for row in records:
            image, label = coco / row["image"], coco / row["label"]
            image.parent.mkdir(parents=True, exist_ok=True)
            label.parent.mkdir(parents=True, exist_ok=True)
            image.hardlink_to(destination / row["image"])
            lines = (destination / row["label"]).read_text(encoding="utf-8").splitlines()
            label.write_text("".join("32 " + s.split(" ", 1)[1] + "\n" for s in lines), encoding="utf-8")
            coco_rows.append({**row, "label_sha256": sha256_file(label)})
        write_json(
            coco / "manifest.json",
            {
                "source_fingerprint": result["fingerprint"],
                "frames": coco_rows,
                "names": coco_names,
                "counts": dict(counts),
                "mapping": "ball 0 -> sports ball 32",
                "supervision_scope": "ball only; other COCO classes intentionally unsupervised",
                "project_human_review_completed": False,
            },
        )
        (coco / "data.yaml").write_text(
            yaml.safe_dump(
                {"path": str(coco), "train": "images/train", "val": "images/val", "names": coco_names},
                sort_keys=False,
            ),
            encoding="utf-8",
        )
    # Normalize the first preparation's old source-only metadata without changing any image or label.
    player_manifest = read_json(output / "players/manifest.json")
    base_rows = {r["frame_id"]: r for r in read_json(base / "manifest.json")["frames"]}
    fields = (
        "frame_id",
        "split",
        "game_id",
        "clip",
        "source_frame_index",
        "width",
        "height",
        "image",
        "label",
        "image_sha256",
        "label_sha256",
        "boxes",
    )
    player_manifest["frames"] = [
        {**{k: r[k] for k in fields}, "source_label_sha256": base_rows[r["frame_id"]]["label_sha256"]}
        for r in player_manifest["frames"]
    ]
    player_manifest["fingerprint"] = digest_json(
        {k: v for k, v in player_manifest.items() if k != "fingerprint"}
    )
    write_json(output / "players/manifest.json", player_manifest)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path("data/broadcast-sngsr-v1"))
    parser.add_argument("--balls", type=Path, default=Path("data/broadcast-ball-review-v1/curated"))
    parser.add_argument("--output", type=Path, default=Path("data/broadcast-training-v2"))
    parser.add_argument("--decisions", type=Path)
    parser.add_argument(
        "--coco-weights", type=Path, default=Path("artifacts/fullscene-ball-v1/fullscene_ball_f005.pt")
    )
    args = parser.parse_args()
    if args.decisions:
        from ultralytics import YOLO

        result = finalize(
            args.base.resolve(), args.output.resolve(), args.decisions, YOLO(str(args.coco_weights)).names
        )
        print({k: result[k] for k in ("counts", "negative_counts", "unique_source_frames", "fingerprint")})
    else:
        prepare(args.base.resolve(), args.balls.resolve(), args.output.resolve())
