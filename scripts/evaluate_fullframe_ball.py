"""Evaluate frozen COCO ball detectors on new, provisional full-frame development labels."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import cv2

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.pipeline import dependencies
from football_pipeline.video import ROOT
from persoon1.metrics import evaluate
from persoon1.modeling import yolo


def validation_truth(source):
    """Lees alleen de vastgelegde volledige validatiebeelden en vorm de balreferenties met hun
    bestandsidentiteiten.
    """
    manifest = read_json(source / "manifest.json")
    names = manifest["names"]
    if names.count("ball") != 1:
        raise ValueError("Require exactly one explicit ball class")
    target = names.index("ball")
    groups = {}
    for frame in manifest["frames"]:
        if frame["split"] not in {"train", "val"}:
            raise ValueError("Do not open reserved test frames in this development evaluation")
        split = groups.setdefault(frame["group_id"], frame["split"])
        if split != frame["split"]:
            raise ValueError("Fragment group crosses train/val")
    truth, identities = {}, {}
    for frame in manifest["frames"]:
        if frame["split"] != "val":
            continue
        key = frame["frame_id"]
        if key in truth:
            raise ValueError("Duplicate validation frame")
        image, label = source / frame["image"], source / frame["label"]
        if sha256_file(image) != frame["image_sha256"]:
            raise ValueError("Image differs from recorded source")
        width, height = frame["width"], frame["height"]
        pixels = cv2.imread(str(image))
        if pixels is None or pixels.shape[:2] != (height, width):
            raise ValueError("Invalid source size or unreadable image")
        boxes = []
        for line in label.read_text(encoding="utf-8").splitlines():
            cls, x, y, w, h = map(float, line.split())
            if cls != int(cls) or not 0 <= cls < len(names):
                raise ValueError("Unknown annotation class")
            if not (
                0 < w <= 1
                and 0 < h <= 1
                and 0 <= x - w / 2 < x + w / 2 <= 1.00000001
                and 0 <= y - h / 2 < y + h / 2 <= 1.00000001
            ):
                raise ValueError("Invalid normalized box")
            if int(cls) == target:
                boxes.append(
                    {
                        "class_id": 0,
                        "bbox_xyxy": [
                            (x - w / 2) * width,
                            (y - h / 2) * height,
                            (x + w / 2) * width,
                            (y + h / 2) * height,
                        ],
                    }
                )
        truth[key] = boxes
        identities[key] = {
            "image": str(image),
            "image_sha256": frame["image_sha256"],
            "label_sha256": sha256_file(label),
            "frame_index": frame["frame_index"],
            "group_id": frame["group_id"],
            "unresolved_regions": frame.get("unresolved_regions", []),
        }
    return manifest, truth, identities


def main():
    """Meet de bevroren balmodellen op de nieuwe volledige ontwikkelframes met hun voorlopige
    referentielabels.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh output directory")
    args.output.mkdir(parents=True)
    sources = [
        ROOT / "assets/annotations" / name
        for name in (
            "football-fullframe40",
            "football-fullscene16",
        )
    ]
    datasets = {source.name: validation_truth(source) for source in sources}
    all_groups, all_frames, pixel_splits = {}, set(), {}
    for manifest, _, _ in datasets.values():
        for frame in manifest["frames"]:
            identity = (manifest["source"]["sha256"], frame["frame_index"])
            if identity in all_frames:
                raise ValueError("Repeated original frame across full-frame sets")
            all_frames.add(identity)
            if all_groups.setdefault(frame["group_id"], frame["split"]) != frame["split"]:
                raise ValueError("Conflicting splits across datasets")
            if pixel_splits.setdefault(frame["image_sha256"], frame["split"]) != frame["split"]:
                raise ValueError("Identical bytes cross split")
    models = {
        "pretrained": ROOT / "artifacts/appearance-v1/person_proposals.pt",
        "F003": ROOT / "artifacts/football48-ball-v2/EXP-F003-best.pt",
        "F004": ROOT / "artifacts/football48-ball-v2/EXP-F004-best.pt",
    }
    write_json(
        args.output / "plan.json",
        {
            "recorded_before_inference": datetime.now(UTC).isoformat(),
            "weights_frozen": {key: sha256_file(path) for key, path in models.items()},
            "imgsz": args.imgsz,
            "confidence_floor": 0.001,
            "nms_iou": 0.7,
            "max_det": 300,
            "application_workpoint": 0.25,
            "target": "all annotated visible footballs, including reserves",
            "selection_policy": "No weight, training or threshold changes; measure domain transfer only",
            "scope": "New full-frame development measurement, AI labels, no independent human review. "
            "Unresolved tiny regions are retained without ignore masks; AP refers to available labels, "
            "not guaranteed exhaustive ground truth. In-play-only recall is not claimed.",
            "dataset_manifests": {s.name: sha256_file(s / "manifest.json") for s in sources},
            "software": dependencies(),
        },
    )
    summary = {}
    for model_id, path in models.items():
        model = yolo(path)
        if model.names.get(32) != "sports ball":
            raise ValueError("Model class 32 must actually mean sports ball")
        summary[model_id] = {}
        for name, (manifest, truth, identities) in datasets.items():
            predictions = {}
            for key, frame in identities.items():
                result = model.predict(
                    frame["image"],
                    imgsz=args.imgsz,
                    conf=0.001,
                    iou=0.7,
                    max_det=300,
                    classes=[32],
                    device=args.device,
                    half=False,
                    verbose=False,
                )[0]
                predictions[key] = [
                    {
                        "class_id": 0,
                        "bbox_xyxy": box.xyxy[0].cpu().tolist(),
                        "confidence": float(box.conf[0]),
                    }
                    for box in result.boxes
                ]
            metrics = evaluate(truth, predictions, ["ball"], confidence=0.25)
            write_json(
                args.output / f"{model_id}-{name}.json",
                {
                    "dataset_version": manifest["dataset_version"],
                    "frames": len(truth),
                    "validation_groups": dict(Counter(f["group_id"] for f in identities.values())),
                    "weights_sha256": sha256_file(path),
                    "identities": identities,
                    "truth": truth,
                    "predictions": predictions,
                    "metrics": metrics,
                },
            )
            summary[model_id][name] = {
                "frames": len(truth),
                **metrics["per_class"][0],
            }
        del model
    write_json(args.output / "summary.json", summary)
    print(summary)


if __name__ == "__main__":
    main()
