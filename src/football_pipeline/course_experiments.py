"""Vergelijkt transferlearninginstellingen op dezelfde vastgelegde ontwikkeldata."""

from __future__ import annotations

import argparse
import gc
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import torch

from .contracts import digest_json, read_json, sha256_file, write_json
from .course_dataset import NAMES
from .video import ROOT


def timestamp():
    return datetime.now(UTC).isoformat()


def evaluate_model(weights, dataset, output, *, imgsz=1280):
    from ultralytics import YOLO

    from persoon1.metrics import evaluate

    output.mkdir(parents=True, exist_ok=True)
    manifest = read_json(dataset / "manifest.json")
    rows = [r for r in manifest["frames"] if r["split"] == "val"]
    config = {
        "evaluator_sha256": sha256_file(__file__),
        "weights_sha256": sha256_file(weights),
        "dataset_fingerprint": manifest["fingerprint"],
        "imgsz": imgsz,
        "confidence": 0.001,
        "iou": 0.7,
        "device": "0",
        "max_det": 300,
    }
    existing = output / "metrics.json"
    if existing.exists():
        saved = read_json(existing)
        if saved["inference_config"] != config:
            raise ValueError(
                "Evaluation inputs changed; preserve existing measurements and choose a fresh output"
            )
        return saved
    model = YOLO(str(weights))
    semantics = {
        index: list(NAMES.values()).index(name)
        for index, name in model.names.items()
        if name in NAMES.values()
    }
    if not semantics or "player" not in model.names.values():
        raise ValueError("Role evaluation requires actual trained player classes")
    truth = {r["frame_id"]: r["boxes"] for r in rows}
    predictions = {}
    start = time.monotonic()
    for row in rows:
        result = model.predict(
            str(dataset / row["image"]),
            imgsz=imgsz,
            device=0,
            conf=0.001,
            iou=0.7,
            max_det=300,
            classes=list(semantics),
            verbose=False,
        )[0]
        predictions[row["frame_id"]] = [
            {"class_id": semantics[int(cls)], "confidence": float(conf), "bbox_xyxy": box.tolist()}
            for box, conf, cls in zip(
                result.boxes.xyxy.cpu(), result.boxes.conf.cpu(), result.boxes.cls.cpu()
            )
        ]
    measured = evaluate(truth, predictions, list(NAMES.values()))
    errors = measured.pop("errors")
    measured.update(
        inference_config=config,
        recorded_at=timestamp(),
        split="val",
        frames=len(rows),
        match_count=len({r.get("game_id", r.get("group")) for r in rows}),
        test_accessed=False,
        annotation_source="SN-GSR-2024 v1.3 provider labels; project human review still open",
        runtime_s=time.monotonic() - start,
    )
    write_json(output / "errors.json", {"errors": errors})
    write_json(output / "predictions.json", predictions)
    write_json(existing, measured)
    del model
    gc.collect()
    torch.cuda.empty_cache()
    return measured


def train_candidate(dataset, output, *, augment, epochs, weights=None, max_minutes=None):
    from ultralytics import YOLO

    config = {
        "imgsz": 1280,
        "epochs": epochs,
        "patience": 12,
        "optimizer": "Adam",
        "lr0": 0.0003,
        "lrf": 0.1,
        "cos_lr": True,
        "warmup_epochs": 3,
        "warmup_bias_lr": 0.0,
        "weight_decay": 0.0005,
        "freeze": 0,
        "amp": True,
        "seed": 42,
        "deterministic": True,
        "workers": 0,
        "rect": False,
        "fliplr": 0.5 if augment else 0.0,
        "flipud": 0.0,
        "degrees": 3.0 if augment else 0.0,
        "translate": 0.1 if augment else 0.0,
        "scale": 0.4 if augment else 0.0,
        "hsv_h": 0.015 if augment else 0.0,
        "hsv_s": 0.4 if augment else 0.0,
        "hsv_v": 0.25 if augment else 0.0,
        "mosaic": 0.25 if augment else 0.0,
        "close_mosaic": 10 if augment else 0,
        "mixup": 0.0,
        "copy_paste": 0.0,
        "cutmix": 0.0,
        "bgr": 0.0,
        "multi_scale": False,
        "auto_augment": None,
        "erasing": 0.0,
        "plots": True,
        "val": True,
        "save": True,
    }
    if max_minutes is not None:
        from .training_budget import train_yolo

        return train_yolo(weights or ROOT / "models/yolo11n.pt", dataset, output, config, max_minutes)
    output.mkdir(parents=True, exist_ok=True)
    dataset_manifest = read_json(dataset / "manifest.json")
    identity = digest_json(
        {
            "dataset": dataset_manifest["fingerprint"],
            "config": config,
            "base_sha256": sha256_file(ROOT / "models/yolo11n.pt"),
            "trainer_sha256": sha256_file(__file__),
        }
    )
    status_file = output / "status.json"
    if status_file.exists():
        status = read_json(status_file)
        if status["identity"] != identity:
            raise ValueError("Changed experiment configuration; use a fresh output")
        if status.get("status") == "complete":
            if sha256_file(status["best"]) != status["best_sha256"]:
                raise ValueError("Selected checkpoint changed")
            return Path(status["best"])
        raise ValueError("Interrupted player experiment exists; preserve it and choose a new experiment ID")
    status = {
        "identity": identity,
        "status": "running",
        "started_at": timestamp(),
        "config": config,
        "dataset_fingerprint": dataset_manifest["fingerprint"],
        "attempts": [],
        "project_human_review_completed": False,
        "test_accessed": False,
    }
    write_json(status_file, status)
    for batch in (4, 2, 1):
        model = None
        try:
            model = YOLO(str(ROOT / "models/yolo11n.pt"))
            model.train(
                data=str(dataset / "data.yaml"),
                batch=batch,
                device=0,
                project=str(output),
                name=f"batch-{batch}",
                exist_ok=False,
                **config,
            )
            best = output / f"batch-{batch}/weights/best.pt"
            if not best.is_file():
                raise ValueError("Training did not produce a selected checkpoint")
            status["attempts"].append({"batch": batch, "status": "complete"})
            status.update(
                status="complete", completed_at=timestamp(), best=str(best), best_sha256=sha256_file(best)
            )
            write_json(status_file, status)
            return best
        except torch.cuda.OutOfMemoryError as exc:
            status["attempts"].append({"batch": batch, "status": "cuda_out_of_memory", "error": str(exc)})
            write_json(status_file, status)
        except BaseException as exc:
            status.update(status="failed", error=str(exc), updated_at=timestamp())
            write_json(status_file, status)
            raise
        finally:
            del model
            gc.collect()
            torch.cuda.empty_cache()
    status["status"] = "all_batches_out_of_memory"
    write_json(status_file, status)
    raise ValueError("All reference batches failed; preserve the experiment before changing resolution")


def run(dataset, output, epochs=60):
    output.mkdir(parents=True, exist_ok=True)
    manifest = read_json(dataset / "manifest.json")
    prereg = {
        "recorded_at": timestamp(),
        "dataset_fingerprint": manifest["fingerprint"],
        "selection": manifest["selection"],
        "hypotheses": {
            "EXP-P005": "Provider-supervised broadcast images from multiple training matches improve transfer to held-out matches vs the panorama-only role model.",
            "EXP-P006": "Changing only realistic geometric and color augmentation improves held-out-match AP over EXP-P005.",
        },
        "selection_metric": "mean player/referee AP50:95; player recall at confidence 0.25 must not regress vs incumbent",
        "evaluation": {
            "imgsz": 1280,
            "confidence_for_AP": 0.001,
            "work_confidence": 0.25,
            "matching_IoU": 0.5,
            "AP_IoUs": "0.50:0.05:0.95",
        },
        "course": {
            "challenge_pages": [2, 3, 4],
            "advanced_deep_learning_slides": [30, 33, 40, 48, 58, 59, 62],
        },
        "human_review_completed": False,
        "test_accessed": False,
        "automatic_promotion": False,
        "epochs_per_candidate": epochs,
        "epoch_selection": "native YOLO validation fitness; final candidate comparison uses shared player/referee classes",
    }
    prereg_path = output / "preregistration.json"
    if not prereg_path.exists():
        write_json(prereg_path, prereg)
    comparison = {
        "status": "running",
        "dataset_fingerprint": manifest["fingerprint"],
        "models": {},
        "human_review_completed": False,
        "independent_final_test_completed": False,
    }
    comparison["models"]["incumbent"] = evaluate_model(
        ROOT / "artifacts/players-v2/players_best.pt", dataset, output / "incumbent"
    )
    comparison["models"]["incumbent-production-1920"] = evaluate_model(
        ROOT / "artifacts/players-v2/players_best.pt",
        dataset,
        output / "incumbent-production-1920",
        imgsz=1920,
    )
    write_json(output / "comparison.json", comparison)
    for experiment, augment in (("EXP-P005", False), ("EXP-P006", True)):
        weights = train_candidate(dataset, output / experiment, augment=augment, epochs=epochs)
        comparison["models"][experiment] = evaluate_model(
            weights, dataset, output / experiment / "validation"
        )
        comparison["models"][experiment]["weights"] = str(weights)
        write_json(output / "comparison.json", comparison)
        print(
            json.dumps({"experiment": experiment, "metrics": comparison["models"][experiment]["per_class"]}),
            flush=True,
        )
    comparison["status"] = "complete"
    write_json(output / "comparison.json", comparison)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=60)
    args = parser.parse_args()
    run(args.dataset.resolve(), args.output.resolve(), args.epochs)
