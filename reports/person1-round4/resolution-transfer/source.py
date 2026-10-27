"""Frozen-weight whole-frame versus native/upsampled tile ball comparison."""

from __future__ import annotations

import argparse
import time
from datetime import UTC, datetime
from pathlib import Path

import cv2
import torch

from football_pipeline.ball_tiles import predict_ball_tiles, tile_windows
from football_pipeline.contracts import sha256_file, write_json
from football_pipeline.pipeline import dependencies
from football_pipeline.video import ROOT
from persoon1.metrics import evaluate
from persoon1.modeling import yolo
from scripts.evaluate_fullframe_ball import validation_truth

MODES = {
    "whole1280": {"imgsz": 1280},
    "whole4096": {"imgsz": 4096},
    "tiles1280": {"size": 1280, "imgsz": 1280},
    "tiles640x2": {"size": 640, "imgsz": 1280},
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="0")
    parser.add_argument("--weights", type=Path)
    parser.add_argument("--model-id", default="new_candidate")
    parser.add_argument("--source-class", type=int, default=32)
    parser.add_argument("--datasets", nargs="+", default=["football-fullframe40", "football-fullscene16"])
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh output directory")
    args.output.mkdir(parents=True)
    datasets = {name: validation_truth(ROOT / "assets/annotations" / name) for name in args.datasets}
    models = (
        {args.model_id: args.weights}
        if args.weights
        else {
            "pretrained": ROOT / "artifacts/appearance-v1/person_proposals.pt",
            "F003": ROOT / "artifacts/football48-ball-v2/EXP-F003-best.pt",
            "F004": ROOT / "artifacts/football48-ball-v2/EXP-F004-best.pt",
        }
    )
    write_json(
        args.output / "plan.json",
        {
            "recorded_before_inference": datetime.now(UTC).isoformat(),
            "modes": MODES,
            "hypothesis": "Preserving source detail improves tiny-ball matching versus global 1280 resize.",
            "primary": "AP50:95 at the same annotated full-frame ball target; AP50 and FP/FN also retained",
            "weights": {
                key: {"path": str(path), "sha256": sha256_file(path)} for key, path in models.items()
            },
            "source_class": args.source_class,
            "confidence_floor": 0.001,
            "workpoint": 0.25,
            "tile_overlap": 0.2,
            "tile_nms_iou": 0.7,
            "global_nms_iou": 0.5,
            "unchanged": "No training, labels, confidence or field-filter tuning within this experiment",
            "human_review_complete": False,
            "independent_final_test": False,
            "scope": "Development labels include reserve balls; not in-play-only recall or independent-match generalization.",
            "datasets": {
                name: sha256_file(ROOT / "assets/annotations" / name / "manifest.json") for name in datasets
            },
            "software": dependencies(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
            "source_sha256": sha256_file(Path(__file__)),
        },
    )
    summary = {}
    for model_id, weights in models.items():
        model = yolo(weights)
        if model.names.get(args.source_class) not in {"ball", "sports ball", "in_play_ball"}:
            raise ValueError("Wrong semantic source class")
        summary[model_id] = {}
        for mode, config in MODES.items():
            for name, (_, truth, identities) in datasets.items():
                predictions, times = {}, []
                for key, identity in identities.items():
                    frame = cv2.imread(identity["image"])
                    start = time.perf_counter()
                    if "size" in config:
                        boxes = predict_ball_tiles(
                            model, frame, **config, device=args.device, source_class=args.source_class
                        )
                    else:
                        result = model.predict(
                            frame,
                            imgsz=config["imgsz"],
                            conf=0.001,
                            iou=0.7,
                            max_det=300,
                            classes=[args.source_class],
                            device=args.device,
                            half=False,
                            verbose=False,
                        )[0]
                        boxes = [
                            {
                                "class_id": 0,
                                "bbox_xyxy": box.xyxy[0].cpu().tolist(),
                                "confidence": float(box.conf[0]),
                            }
                            for box in result.boxes
                        ]
                    predictions[key] = boxes
                    times.append(time.perf_counter() - start)
                metrics = evaluate(truth, predictions, ["ball"], confidence=0.25)
                record = {
                    "model": model_id,
                    "mode": mode,
                    "dataset": name,
                    "frames": len(truth),
                    "truth": truth,
                    "identities": identities,
                    "predictions": predictions,
                    "metrics": metrics,
                    "inference_seconds_including_initialization": times,
                    "tile_count_for_4096x1080": len(tile_windows(4096, 1080, config["size"]))
                    if "size" in config
                    else 1,
                }
                write_json(args.output / f"{model_id}-{mode}-{name}.json", record)
                row = {
                    "dataset": name,
                    "frames": len(truth),
                    **metrics["per_class"][0],
                    "elapsed_s": sum(times),
                }
                summary[model_id].setdefault(mode, []).append(row)
                print(model_id, mode, name, row, flush=True)
                write_json(args.output / "summary.json", summary)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
