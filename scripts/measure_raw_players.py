"""Native-frame specialist detector accuracy, entirely independent of field filtering."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import cv2

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.detection import UltralyticsDetector, load_model_manifest
from persoon1.metrics import evaluate


def measure(manifests, profile, output):
    output.mkdir(parents=True, exist_ok=True)
    manifest = load_model_manifest(profile)
    specialist = [m for m in manifest["models"] if "player" in m["class_mapping"].values()]
    if not specialist:
        raise ValueError("An actual player detector is required")
    rows, seen = [], set()
    for path in manifests:
        for row in read_json(path)["frames"]:
            if row["source_frame_index"] % round(row["fps"]) or row["image_sha256"] in seen:
                continue
            rows.append(row)
            seen.add(row["image_sha256"])
    identity = digest_json([rows, specialist, sha256_file(__file__)])
    record = output / "raw-detections.json"
    if record.exists():
        cached = read_json(record)
        if cached["identity"] != identity:
            raise ValueError("Raw inference inputs changed; use a new output directory")
        predictions = cached["predictions"]
    else:
        detector = UltralyticsDetector({"schema_version": 1, "models": specialist})
        predictions = {}
        for i, row in enumerate(rows):
            if sha256_file(row["image"]) != row["image_sha256"]:
                raise ValueError("Source frame changed")
            image = cv2.imread(row["image"])
            if image is None or image.shape[1::-1] != (row["width"], row["height"]):
                raise ValueError("Detector must receive the native source image")
            ds = detector.detect(image, row["source_frame_index"])
            predictions[row["frame_id"]] = [
                {"class_id": 0, "bbox_xyxy": d.bbox_xyxy, "confidence": d.confidence}
                for d in ds
                if d.semantic_class == "player"
            ]
            if i % 12 == 0:
                print(f"Raw players {i + 1}/{len(rows)}", flush=True)
        write_json(record, {"identity": identity, "predictions": predictions})
    metrics, errors = {}, []
    for split in sorted({r["split"] for r in rows}):
        group = [r for r in rows if r["split"] == split]
        truth = {
            r["frame_id"]: [
                {"class_id": 0, "bbox_xyxy": p["bbox"]}
                for p in r["people"]
                if p["role"] == "player" and p["on_pitch"]
            ]
            for r in group
        }
        result = evaluate(truth, {key: predictions[key] for key in truth}, ["player"])
        errors += [{**e, "split": split} for e in result.pop("errors")]
        metrics[split] = {"frames": len(group), **result}
    by_frame = {r["frame_id"]: r for r in rows}
    error_counts = defaultdict(int)
    # Review metadata identifies hard cases without pretending to know their causes.
    for e in errors:
        row = by_frame[e["frame_id"]]
        box = e.get("annotation", e.get("prediction"))["bbox_xyxy"]
        e.update(
            image=row["image"],
            image_sha256=row["image_sha256"],
            small_box=box[3] - box[1] < 48,
            near_image_edge=min(box[0], row["width"] - box[2]) < row["width"] * 0.03,
            human_reviewed=False,
            eligible_for_training=row["split"] == "train",
        )
        error_counts[e["split"] + ":" + e["type"]] += 1
    summary = {
        "stage": "raw_specialist_detector_before_roles_geometry_tracking_or_display",
        "identity": identity,
        "specialist": specialist,
        "metrics": metrics,
        "error_counts": dict(error_counts),
        "human_review_completed": False,
        "independent_final_test_completed": False,
        "sampling": "one native frame per second in existing fixed windows",
        "reference": "Existing provider on-pitch player boxes, including keepers",
    }
    write_json(output / "metrics.json", summary)
    write_json(output / "errors-for-review.json", {"errors": errors})
    print(json.dumps({split: m["per_class"] for split, m in metrics.items()}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, action="append", required=True)
    parser.add_argument("--profile", type=Path, default=Path("configs/models-broadcast.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    measure(args.dataset, args.profile, args.output)


if __name__ == "__main__":
    main()
