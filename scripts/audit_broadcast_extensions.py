"""Verify curated ball/referee exports and write their compact, reproducible handoff."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from persoon1.core import label_pixels, read_labels


def audit(root, semantic, *, decode=True):
    manifest = read_json(root / "manifest.json")
    if digest_json({k: v for k, v in manifest.items() if k != "fingerprint"}) != manifest["fingerprint"]:
        raise ValueError("Manifest fingerprint mismatch")
    if manifest["names"] != {"0": semantic}:
        raise ValueError("Training class mapping mismatch")

    def check(row):
        for key in ("image", "label"):
            if sha256_file(root / row[key]) != row[key + "_sha256"]:
                raise ValueError(f"Changed {key}: {row['frame_id']}")
        with Image.open(root / row["image"]) as image:
            if image.size != (row["width"], row["height"]):
                raise ValueError("Image dimensions changed")
            if decode:
                image.load()
        boxes = read_labels(root / row["label"], 1)
        if semantic == "ball":
            if len(boxes) != 1:
                raise ValueError("Curated positive ball frame must contain one reviewed box")
            actual = label_pixels(boxes[0], row["width"], row["height"])
            if any(abs(a - b) > 0.00001 for a, b in zip(actual, row["bbox_xyxy"])):
                raise ValueError("Corrected ball coordinates differ from exported YOLO labels")
        elif len(boxes) != row["box_count"] or bool(boxes) != (row["visibility"] == "visible"):
            raise ValueError("Referee labels differ from explicit visibility/count metadata")
        return len(boxes)

    with ThreadPoolExecutor(max_workers=8) as pool:
        boxes = sum(pool.map(check, manifest["frames"]))
    groups = defaultdict(set)
    for row in manifest["frames"]:
        groups[row.get("game_id", row.get("source_clip_id"))].add(row["split"])
    if any(len(splits) > 1 for splits in groups.values()):
        raise ValueError("Dataset groups overlap between training and validation")
    hashes = {r["image_sha256"] for r in manifest["frames"]}
    if len(hashes) != len(manifest["frames"]):
        raise ValueError("Duplicate images in curated corpus")
    return manifest, {
        "status": "passed",
        "frames": len(hashes),
        "boxes": boxes,
        "counts": dict(Counter(r["split"] for r in manifest["frames"])),
        "duplicate_images": 0,
        "split_group_overlap": 0,
        "image_decode": "full" if decode else "header; underlying source fully decoded",
        "fingerprint": manifest["fingerprint"],
    }


def main():
    report_root = Path("reports/broadcast-data")
    base = read_json("data/broadcast-sngsr-v1/manifest.json")
    balls, ball_report = audit(Path("data/broadcast-ball-review-v1/curated"), "ball")
    raw_refs, raw_report = audit(Path("data/referee-broadcast-v1"), "referee")
    refs, ref_report = audit(Path("data/referee-broadcast-v1/curated"), "referee", decode=False)
    if {r["frame_id"] for r in refs["frames"]} & {r["frame_id"] for r in refs["quarantine"]}:
        raise ValueError("Quarantined source frame leaked into curated dataset")
    base_hashes = {r["image_sha256"] for r in base["frames"]}
    ref_hashes = {r["image_sha256"] for r in raw_refs["frames"]}
    if base_hashes & ref_hashes:
        raise ValueError("Auxiliary data overlaps original corpus exactly")
    if not {r["image_sha256"] for r in balls["frames"]} <= base_hashes:
        raise ValueError("Curated balls are not derived from the frozen main corpus")
    decisions = read_json(report_root / "ball-review-decisions.json")
    suite = ET.parse(report_root / "software-tests.xml").getroot().find("testsuite")
    software = {k: int(suite.attrib[k]) for k in ("tests", "failures", "errors", "skipped")}
    if software["failures"] or software["errors"]:
        raise ValueError("Software checks did not pass")
    result = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "ball_dataset": ball_report,
        "ball_review": dict(Counter(r["status"] for r in decisions["decisions"])),
        "raw_referee_dataset": raw_report,
        "curated_referee_dataset": ref_report,
        "referee_quarantine_count": len(refs["quarantine"]),
        "referee_negative_frames": refs["visibility_counts"]["not_visible"],
        "referee_match_independence_verified": False,
        "collected_unique_source_images": len(base_hashes | ref_hashes),
        "recommended_unique_source_images": len(base_hashes | {r["image_sha256"] for r in refs["frames"]}),
        "ball_examples_are_subset_of_main_corpus": True,
        "training_configs": {
            "players": "data/broadcast-sngsr-v1/data-players.yaml",
            "balls": "data/broadcast-ball-review-v1/curated/data.yaml",
            "referees": "data/referee-broadcast-v1/curated/data.yaml",
        },
        "software_tests": software,
        "project_human_review_completed": False,
        "model_training_started": False,
        "active_models_changed": False,
        "source_sha256": {
            p: sha256_file(p)
            for p in (
                "src/football_pipeline/referee_dataset.py",
                "scripts/curate_broadcast_balls.py",
                "scripts/curate_referee_data.py",
                "scripts/audit_broadcast_extensions.py",
                "tests/test_broadcast_curation.py",
            )
        },
    }
    write_json(report_root / "follow-up-summary.json", result)
    initial = read_json(report_root / "summary.json")
    initial["software_tests"] = software
    initial["follow_up_summary"] = "reports/broadcast-data/follow-up-summary.json"
    write_json(report_root / "summary.json", initial)
    print(result)


if __name__ == "__main__":
    main()
