"""Bounded native-ball fine-tuning with frozen, equal-input baseline comparisons."""

from __future__ import annotations

import argparse
import csv
import gc
import os
import time
from pathlib import Path

import cv2
import torch

from football_pipeline.ball_tiles import predict_ball_tiles
from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from persoon1.metrics import evaluate


def measured(weights, rows, image_root, output, *, mode):
    from ultralytics import YOLO, __version__

    output.mkdir(parents=True, exist_ok=True)
    identity = {"weights_sha256": sha256_file(weights), "mode": mode,
                "frames": digest_json(rows), "confidence_floor": 0.001,
                "work_confidence": 0.25, "nms_iou": 0.7, "merge_iou": 0.5,
                "evaluator_sha256": sha256_file(evaluate.__code__.co_filename),
                "tiling_sha256": sha256_file(predict_ball_tiles.__code__.co_filename),
                "torch_version": torch.__version__, "ultralytics_version": __version__,
                "imgsz": 1280 if mode == "full" else 640}
    if (output / "metrics.json").exists():
        saved = read_json(output / "metrics.json")
        if saved["identity"] != identity:
            raise ValueError("Evaluation inputs changed")
        return saved
    model = YOLO(str(weights))
    if model.names.get(32) != "sports ball":
        raise ValueError("Experiment requires the verified COCO sports-ball head")
    truth, predictions = {}, {}
    start = time.monotonic()
    for number, row in enumerate(rows):
        fid = row["frame_id"]
        pixels = cv2.imread(str(image_root / row["image"]))
        if pixels is None or sha256_file(image_root / row["image"]) != row["image_sha256"]:
            raise ValueError("Evaluation image changed")
        box = row.get("bbox_xyxy")
        truth[fid] = [{"class_id": 0, "bbox_xyxy": box}] if box is not None else []
        if mode == "tiled":
            predicted = predict_ball_tiles(model, pixels, size=640, imgsz=640, overlap=0.2,
                                           confidence=0.001, device="0", source_class=32)
        else:
            result = model.predict(pixels, imgsz=identity["imgsz"], conf=0.001, iou=0.7,
                                   device=0, classes=[32], max_det=300, verbose=False)[0]
            predicted = [{"bbox_xyxy": box.tolist(), "confidence": float(conf)} for box, conf
                         in zip(result.boxes.xyxy.cpu(), result.boxes.conf.cpu())]
        predictions[fid] = [{"class_id": 0, "bbox_xyxy": p["bbox_xyxy"], "confidence": p["confidence"]}
                            for p in predicted]
        if (number + 1) % 20 == 0:
            print(f"Evaluation {output.name}/{mode}: {number+1}/{len(rows)}", flush=True)
    result = evaluate(truth, predictions, ["ball"], confidence=0.25)
    errors = result.pop("errors")
    negative_ids = {r["frame_id"] for r in rows if r.get("bbox_xyxy") is None}
    result.update(identity=identity, frames=len(rows), elapsed_s=time.monotonic() - start,
                  negative_frames=len(negative_ids),
                  unmatched_on_negatives=sum(p["confidence"] >= 0.25 for fid in negative_ids for p in predictions[fid]),
                  project_human_review_completed=False,
                  scope="Development AI-reviewed labels; extra physical balls on full frames may be unlabelled")
    write_json(output / "predictions.json", predictions)
    write_json(output / "errors.json", {"errors": errors})
    write_json(output / "metrics.json", result)
    del model
    gc.collect()
    torch.cuda.empty_cache()
    return result


def run(dataset, output, epochs):
    os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(".cache/ultralytics-broadcast-v2").resolve()))
    (Path(os.environ["YOLO_CONFIG_DIR"]) / "Ultralytics").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(Path(".cache/matplotlib").resolve()))
    os.environ.setdefault("WANDB_MODE", "disabled")
    from ultralytics import YOLO, settings

    if not torch.cuda.is_available():
        raise ValueError("This bounded experiment requires the available CUDA GPU")
    output.mkdir(parents=True, exist_ok=True)
    settings.update({k: False for k in ("sync", "clearml", "comet", "dvc", "mlflow", "neptune", "wandb") if k in settings})
    settings.update({"weights_dir": str(Path("models").resolve())})
    weights = Path("artifacts/fullscene-ball-v1/fullscene_ball_f005.pt").resolve()
    crops = read_json(dataset / "balls/manifest.json")
    full_root = Path("data/broadcast-ball-review-v1/curated").resolve()
    full = read_json(full_root / "manifest.json")
    crop_rows = [r for r in crops["frames"] if r["split"] == "val"]
    full_rows = [r for r in full["frames"] if r["split"] == "val"]
    training = {"epochs": epochs, "imgsz": 640, "batch": 4, "freeze": 10, "optimizer": "AdamW",
                "lr0": 0.0001, "lrf": 0.1, "cos_lr": True, "warmup_epochs": 3,
                "weight_decay": 0.0005, "patience": epochs, "amp": True,
                "workers": 0, "seed": 42, "deterministic": True, "cache": False,
                "mosaic": 0.0, "mixup": 0.0, "copy_paste": 0.0, "degrees": 0.0,
                "scale": 0.0, "translate": 0.0, "fliplr": 0.5, "flipud": 0.0,
                "hsv_h": 0.01, "hsv_s": 0.2, "hsv_v": 0.15, "plots": False}
    prereg = {"weights_sha256": sha256_file(weights), "dataset_fingerprint": crops["fingerprint"],
              "script_sha256": sha256_file(__file__), "training": training,
              "validation_crop_frames": len(crop_rows), "validation_full_frames": len(full_rows),
              "primary_comparison": "same native crops and same full frames with identical tiled inference",
              "promotion": "no automatic change to active models", "project_human_review_completed": False}
    frozen = output / "preregistration.json"
    if frozen.exists() and read_json(frozen) != prereg:
        raise ValueError("Experiment inputs changed; use a new output version")
    write_json(frozen, prereg)
    snapshot = output / "experiment-source.py"
    if not snapshot.exists():
        snapshot.write_bytes(Path(__file__).read_bytes())
    elif sha256_file(snapshot) != prereg["script_sha256"]:
        raise ValueError("Saved experiment source differs from the frozen run")
    baseline = {}
    for mode, rows, root in (("crops", crop_rows, dataset / "balls"), ("full", full_rows, full_root),
                             ("tiled", full_rows, full_root)):
        baseline[mode] = measured(weights, rows, root, output / "baseline" / mode, mode=mode)
    best = output / "fine-tune/weights/best.pt"
    results_file = output / "fine-tune/results.csv"
    if best.parent.parent.exists() and not best.exists():
        raise ValueError("Interrupted training directory exists without a completed checkpoint; use a fresh output")
    if best.exists():
        with results_file.open(newline="", encoding="utf-8-sig") as stream:
            completed = list(csv.DictReader(stream))
        if len(completed) != epochs or int(completed[-1]["epoch"]) != epochs:
            raise ValueError("Interrupted training checkpoint is not a completed experiment; preserve it and use a fresh output")
    if not best.exists():
        print("Starting bounded fine-tuning", flush=True)
        model = YOLO(str(weights))
        model.train(data=str(dataset / "ball-coco/data.yaml"), device=0, project=str(output),
                    name="fine-tune", exist_ok=False, **training)
        del model
        gc.collect()
        torch.cuda.empty_cache()
    with results_file.open(newline="", encoding="utf-8-sig") as stream:
        completed = list(csv.DictReader(stream))
    if len(completed) != epochs:
        raise ValueError("Training did not complete the preregistered epoch budget")
    candidate = {}
    for mode, rows, root in (("crops", crop_rows, dataset / "balls"), ("full", full_rows, full_root),
                             ("tiled", full_rows, full_root)):
        candidate[mode] = measured(best, rows, root, output / "candidate" / mode, mode=mode)
    comparison = {"preregistration": prereg, "baseline": baseline, "candidate": candidate,
                  "candidate_weights": str(best), "candidate_weights_sha256": sha256_file(best),
                  "active_model_changed": False, "project_human_review_completed": False,
                  "independent_final_test_completed": False,
                  "limitations": "Small AI-curated development validation from three matches; crop and full-frame tasks differ"}
    write_json(output / "comparison.json", comparison)
    report = Path("reports/broadcast-data") / f"{output.name}-experiment.json"
    write_json(report, comparison)
    print({mode: {"baseline_AP50_95": baseline[mode]["mAP50_95"],
                  "candidate_AP50_95": candidate[mode]["mAP50_95"]} for mode in baseline}, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/broadcast-training-v2"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/broadcast-ball-v2"))
    parser.add_argument("--epochs", type=int, default=12)
    args = parser.parse_args()
    run(args.dataset.resolve(), args.output.resolve(), args.epochs)
