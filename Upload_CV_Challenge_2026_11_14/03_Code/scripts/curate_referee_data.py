"""Export explicitly reviewed source clips without changing the published referee corpus."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import yaml

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json


def export(root, decisions_path):
    """Exporteer alleen de expliciet beoordeelde bronclips en hun officiallabels zonder het
    oorspronkelijke providercorpus te wijzigen.
    """
    source = read_json(root / "manifest.json")
    decisions = read_json(decisions_path)
    if decisions["source_fingerprint"] != source["fingerprint"]:
        raise ValueError("Clip review belongs to a different source corpus")
    clips = {r["source_clip_id"] for r in source["frames"]}
    decisions_by_clip = {r["source_clip_id"]: r for r in decisions["clips"]}
    if len(decisions_by_clip) != len(decisions["clips"]) or set(decisions_by_clip) != clips:
        raise ValueError("Every source clip needs exactly one explicit decision")
    if any(r["status"] not in {"include", "quarantine"} or not r.get("reason") for r in decisions["clips"]):
        raise ValueError("Invalid clip decision")
    output = root / "curated"
    frames, quarantine = [], []
    for row in source["frames"]:
        decision = decisions_by_clip[row["source_clip_id"]]
        if decision["status"] == "quarantine":
            quarantine.append({"frame_id": row["frame_id"], "reason": decision["reason"]})
            continue
        image = output / row["image"]
        label = output / row["label"]
        for key in ("image", "label"):
            if sha256_file(root / row[key]) != row[key + "_sha256"]:
                raise ValueError("Source image or label changed after review")
        image.parent.mkdir(parents=True, exist_ok=True)
        label.parent.mkdir(parents=True, exist_ok=True)
        if not image.exists():
            image.hardlink_to(root / row["image"])
        text = (root / row["label"]).read_text(encoding="utf-8")
        if label.exists() and label.read_text(encoding="utf-8") != text:
            raise ValueError("Preserve edited labels; use a new dataset version")
        label.write_text(text, encoding="utf-8")
        frames.append(row)
    split_clips = {s: {r["source_clip_id"] for r in frames if r["split"] == s} for s in ("train", "val")}
    if not all(split_clips.values()) or split_clips["train"] & split_clips["val"]:
        raise ValueError("Need nonempty disjoint clip groups")
    result = {
        "source": source["source"],
        "source_revision": source["source_revision"],
        "source_fingerprint": source["fingerprint"],
        "decisions_sha256": sha256_file(decisions_path),
        "names": {0: "referee"},
        "frames": frames,
        "quarantine": quarantine,
        "counts": dict(Counter(r["split"] for r in frames)),
        "visibility_counts": dict(Counter(r["visibility"] for r in frames)),
        "box_count": sum(r["box_count"] for r in frames),
        "source_clip_counts": {s: len(v) for s, v in split_clips.items()},
        "match_independence_verified": False,
        "project_human_review_completed": False,
        "review_scope": "AI inspected three frames per source clip; full human review still open",
        "license": source["license"],
        "credit": source["credit"],
    }
    result["fingerprint"] = digest_json(result)
    write_json(output / "manifest.json", result)
    (output / "data.yaml").write_text(
        yaml.safe_dump(
            {"path": str(output), "train": "images/train", "val": "images/val", "names": {0: "referee"}},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/referee-broadcast-v1"))
    parser.add_argument("--decisions", type=Path, required=True)
    args = parser.parse_args()
    result = export(args.root.resolve(), args.decisions.resolve())
    print({k: result[k] for k in ("counts", "visibility_counts", "box_count", "fingerprint")})
