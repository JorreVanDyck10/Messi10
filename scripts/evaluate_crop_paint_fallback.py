"""Preserve accepted full-frame fits; require paint support for a crop-only recovery."""

import argparse
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.course_field_evaluation import score
from football_pipeline.field_layout import LINES_UV
from football_pipeline.field_learning import upstream_runtime
from football_pipeline.field_motion import MOTION_RANK_SETTINGS, estimate_checked
from football_pipeline.field_paint_checks import distance_paint_evidence

ROOT = Path(__file__).resolve().parents[1]


def supported_by_paint(evidence):
    if evidence["status"] != "checked" or not evidence.get("lines"):
        return False
    if any(line["mismatch"] for line in evidence["lines"]):
        return False
    diagonal = np.hypot(*evidence["measurement_image_size"])
    axes = set()
    for line in evidence["lines"]:
        if line["median_px"] <= diagonal * 0.005 and line["p95_px"] <= diagonal * 0.01:
            ends = LINES_UV[line["id"]]
            axes.add(int(np.argmax(np.abs(ends[1] - ends[0]))))
    return len(axes) == 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("train", "valid"), default="train")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    upstream_runtime(ROOT / "artifacts/joint-retrain-20261027-v2/selected-field-runtime.json")
    index = read_json(ROOT / "artifacts/course-improvement-20261019/field/dataset-index.json")
    baseline = read_json(
        ROOT
        / "artifacts/course-improvement-20261019/field-policy-full-last/observations-6c30ef8aa93dc16a6d5c1f7beb965e9ba17b7759fb77faa08cfb5112381e7ff1.json"
    )["observations"]
    selected = [(r, o) for r, o in zip(index["frames"], baseline, strict=True) if r["split"] == args.split]
    crop_root = ROOT / f"artifacts/broadcast-reliability-20261030/crop-historical-{args.split}-v2/historical"
    cropped = read_json(crop_root / "observations.json")["frames"]
    crop_rows = read_json(crop_root / "rows.json")["frames"]
    if crop_rows != [row for row, _ in selected]:
        raise ValueError("Crop and full-frame sources differ")
    rows, before, after, records = [], [], [], []
    for (row, original), crop in zip(selected, cropped, strict=True):
        if (
            sha256_file(row["image"]) != row["image_sha256"]
            or sha256_file(row["label"]) != row["label_sha256"]
        ):
            raise ValueError("Source or reference changed")
        state = estimate_checked(original, original["image_size"], MOTION_RANK_SETTINGS)
        chosen = original
        record = {"image_sha256": row["image_sha256"], "original_status": state["status"], "recovered": False}
        if state["status"] != "valid" and state["status"] not in {
            "invalid_observation",
            "orientation_unknown",
        }:
            candidate = estimate_checked(crop, crop["image_size"], MOTION_RANK_SETTINGS)
            record["crop_status"] = candidate["status"]
            if candidate["status"] == "valid":
                evidence = distance_paint_evidence(cv2.imread(row["image"]), candidate)
                record["paint"] = evidence
                if supported_by_paint(evidence):
                    chosen = crop
                    record["recovered"] = True
        rows.append(row)
        before.append(original)
        after.append(chosen)
        records.append(record)
    result = {
        "baseline": score(before, rows, MOTION_RANK_SETTINGS),
        "candidate": score(after, rows, MOTION_RANK_SETTINGS),
        "recovered": sum(r["recovered"] for r in records),
        "records": records,
        "inputs_digest": digest_json(selected),
        "source_sha256": sha256_file(__file__),
        "human_review_completed": False,
        "independent_final_test_completed": False,
    }
    write_json(args.output / "metrics.json", result)
    print({k: v for k, v in result.items() if k != "records"}, flush=True)


if __name__ == "__main__":
    main()
