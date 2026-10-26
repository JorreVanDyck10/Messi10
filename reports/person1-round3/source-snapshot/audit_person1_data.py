"""Inventory P1 development data and prepare truthful human review, never inspect test pictures."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.video import ROOT
from persoon1.role_training import load_training_manifest
from scripts.football48_ball_experiment import truth_and_identity


def difference_hash(frame):
    small = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (17, 16))
    return (small[:, 1:] > small[:, :-1]).reshape(-1)


def audit_roles(path):
    data = load_training_manifest(path)
    counts = defaultdict(Counter)
    source_rows = defaultdict(list)
    crop_ids = set()
    for row in data["samples"]:
        counts[row["split"]][row["role"]] += 1
        crop = (row["image_sha256"], tuple(row["bbox"]))
        if crop in crop_ids:
            raise ValueError("Duplicate raw crop in the same role dataset")
        crop_ids.add(crop)
        source_rows[row["image"]].append(row)
    summaries = []
    for image, rows in source_rows.items():
        summaries.append({
            "image": image, "sha256": rows[0]["image_sha256"], "split": rows[0]["split"],
            "group": rows[0]["group"], "crops": len(rows),
        })
    return {
        "manifest": str(path.relative_to(ROOT)), "manifest_sha256": sha256_file(path),
        "version": data["version"], "raw_crops": len(data["samples"]), "used_source_images": len(source_rows),
        "counts": {k: dict(v) for k, v in counts.items()},
        "sources": summaries, "exact_duplicate_crops": 0,
        "cross_split_source_group_or_image_bytes": 0,
        "human_review_completed": data["human_review_completed"],
        "exhaustive_detection_reference": False,
    }, data


def audit_detection(path):
    data = read_json(path)
    role_path = ROOT / "datasets/roles-teams-v2/manifest.json"
    reference_hashes = {
        (role_path.parent / r["image"]).resolve(): r["image_sha256"]
        for r in read_json(role_path)["samples"]
    }
    counts, classes = Counter(), defaultdict(Counter)
    hashes, group_splits, perceptual, records = {}, {}, [], []
    reserved = []
    for row in data["frames"]:
        if row["split"] == "test":
            reserved.append(row["frame_id"])
            continue  # Do not decode, hash, display or run inference on reserved test images.
        split = row["split"]
        if group_splits.setdefault(row["group_id"], split) != split:
            raise ValueError("Detection source group crosses splits")
        image = path.parent / row["image"]
        label = path.parent / row["label"]
        digest = sha256_file(image)
        reference = row.get("image_sha256", reference_hashes.get(image.resolve()))
        if reference is None or digest != reference:
            raise ValueError("Detection source image changed")
        if hashes.setdefault(digest, split) != split:
            raise ValueError("Identical detection image bytes cross splits")
        frame = cv2.imread(str(image))
        if frame is None:
            raise ValueError("Unreadable detection image")
        height, width = frame.shape[:2]
        if (width, height) != (row["width"], row["height"]):
            raise ValueError("Unexpected original image dimensions")
        for line in label.read_text(encoding="utf-8").splitlines():
            cls, x, y, w, h = map(float, line.split())
            if not (cls.is_integer() and 0 <= cls < len(data["names"]) and np.isfinite([x,y,w,h]).all()
                    and w > 0 and h > 0 and 0 <= x-w/2 < x+w/2 <= 1.000001
                    and 0 <= y-h/2 < y+h/2 <= 1.000001):
                raise ValueError("Invalid detection label")
            classes[split][data["names"][int(cls)]] += 1
        perceptual.append((row, difference_hash(frame)))
        counts[split] += 1
        records.append({"frame_id": row["frame_id"], "split": split, "image_sha256": digest, "label_sha256": sha256_file(label)})
    flags = []
    for (left, lh), (right, rh) in combinations(perceptual, 2):
        if left["split"] != right["split"]:
            distance = int(np.count_nonzero(lh != rh))
            if distance <= 8:
                flags.append({"left": left["frame_id"], "right": right["frame_id"], "hash_distance_256": distance,
                              "status": "review_candidate_only; static background similarity does not prove duplicate action"})
    return {
        "manifest": str(path.relative_to(ROOT)), "manifest_sha256": sha256_file(path),
        "recorded_image_hash_reference": str(role_path.relative_to(ROOT)),
        "recorded_image_hash_reference_sha256": sha256_file(role_path),
        "frames_checked": dict(counts), "class_counts": {k: dict(v) for k,v in classes.items()},
        "reserved_test_frames_not_opened": reserved, "exact_cross_split_image_duplicates": 0,
        "group_crossings": 0, "perceptual_cross_split_review_candidates": flags,
        "image_and_label_identity": records, "human_review_completed": data.get("human_review_completed", False),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    role_reports, all_rows = [], []
    for version in ("roles-teams-v1", "roles-teams-v2", "roles-teams-v3"):
        path = ROOT / "datasets" / version / "manifest.json"
        if not path.is_file():
            continue
        report, data = audit_roles(path)
        role_reports.append(report)
        if version == "roles-teams-v3":
            all_rows = data["samples"]
    detection = audit_detection(ROOT / "datasets/teamtrack-players-v2/manifest.json")
    ball_manifest, _, ball_identity = truth_and_identity(ROOT / "assets/annotations/football48")
    legacy = read_json(ROOT / "datasets/panoris-ball-ai-v1/selection.json")
    report = {
        "scope": "Technical development-data audit, NOT human label review or model accuracy. Dataset versions reuse sources and must not be summed as independent data.",
        "roles": role_reports, "player_detection": detection,
        "football48": {"frames": len(ball_manifest["frames"]), **ball_identity},
        "legacy_panoramic_ball_metadata_only": {
            "frames_by_split": dict(Counter(r["split"] for r in legacy["frames"])),
            "test_images_not_opened": True, "selection_sha256": sha256_file(ROOT / "datasets/panoris-ball-ai-v1/selection.json"),
        },
        "human_review_completed": False,
    }
    write_json(args.output / "inventory.json", report)
    if all_rows:
        with (args.output / "human-review.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            fields = ["id", "split", "group", "image", "bbox", "proposed_role", "proposed_team", "reviewer", "review_status", "corrected_role", "corrected_bbox", "notes"]
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for row in all_rows:
                writer.writerow({
                    "id": row["id"], "split": row["split"], "group": row["group"], "image": row["image"],
                    "bbox": str(row["bbox"]), "proposed_role": row["role"], "proposed_team": row.get("team"),
                    "reviewer": "", "review_status": "pending_human_review",
                })
    print({"role_datasets": len(role_reports), "player_frames": detection["frames_checked"], "near_duplicate_review_flags": len(detection["perceptual_cross_split_review_candidates"]), "human_review": "pending"})


if __name__ == "__main__":
    main()
