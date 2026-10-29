"""Traint een YOLO-veldpuntenmodel via transfer learning op vastgelegde providerannotaties."""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from .contracts import digest_json, read_json, sha256_file, write_json


def train(dataset, output, epochs=100, batch=8, imgsz=960, workers=4):
    import torch
    from ultralytics import YOLO, __version__

    manifest = read_json(dataset / "manifest.json")
    if manifest["cross_split_match_overlap"] != 0 or manifest["test_accessed"]:
        raise ValueError(
            "Field pose training requires untouched test data and match-separated development splits"
        )
    for row in manifest["frames"]:
        if (
            sha256_file(dataset / row["image"]) != row["image_sha256"]
            or sha256_file(dataset / row["label"]) != row["label_sha256"]
        ):
            raise ValueError("Frozen field-pose data changed")
    output.mkdir(parents=True, exist_ok=True)
    config = dict(
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=0,
        workers=workers,
        seed=42,
        deterministic=True,
        optimizer="AdamW",
        lr0=0.0005,
        lrf=0.1,
        cos_lr=True,
        warmup_epochs=3,
        warmup_bias_lr=0.0,
        weight_decay=0.0001,
        patience=20,
        freeze=0,
        amp=True,
        mosaic=0,
        mixup=0,
        copy_paste=0,
        degrees=12,
        translate=0.2,
        scale=0.4,
        shear=2,
        perspective=0.0002,
        fliplr=0.5,
        flipud=0,
        hsv_h=0.01,
        hsv_s=0.4,
        hsv_v=0.3,
        cache=False,
        plots=True,
        save_period=10,
    )
    identity = digest_json(
        {"dataset": manifest["fingerprint"], "config": config, "source": sha256_file(__file__)}
    )
    report_path = output / "training-report.json"
    if report_path.exists() and read_json(report_path)["identity"] != identity:
        raise ValueError("Training configuration changed; use a new output directory")
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.set_num_threads(4)
    pretrained = Path("models/yolo11n-pose.pt")
    model = YOLO(str(pretrained))
    report = {
        "status": "running",
        "identity": identity,
        "dataset_fingerprint": manifest["fingerprint"],
        "config": config,
        "pretrained_sha256": sha256_file(pretrained),
        "torch": torch.__version__,
        "ultralytics": __version__,
        "gpu": torch.cuda.get_device_name(0),
        "project_human_review_completed": False,
        "independent_final_test_completed": False,
        "ground_point_ids": manifest["ground_point_ids"],
        "trainer_sha256": sha256_file(__file__),
    }
    write_json(report_path, report)

    from .contracts import PipelineError
    from .pipeline import processing_lock

    while True:
        try:
            with processing_lock(Path("runs")):
                pass
            break
        except PipelineError:
            report.update(
                status="waiting_for_current_video",
                wait_reason="Finish the active user analysis before GPU training",
            )
            write_json(report_path, report)
            print("Waiting for the active uploaded video analysis to finish before GPU training", flush=True)
            time.sleep(10)
    report["status"] = "running"
    write_json(report_path, report)

    def progress(trainer):
        report["completed_epoch"] = trainer.epoch + 1
        report["metrics"] = {k: float(v) for k, v in trainer.metrics.items()}
        write_json(report_path, report)

    model.add_callback("on_fit_epoch_end", progress)
    try:
        last = output / "fit/weights/last.pt"
        if last.exists():
            model = YOLO(str(last))
            model.add_callback("on_fit_epoch_end", progress)
            model.train(resume=True)
        else:
            model.train(
                data=str((dataset / "data.yaml").resolve()),
                project=str(output.resolve()),
                name="fit",
                exist_ok=True,
                **config,
            )
        best = output / "fit/weights/best.pt"
        report.update(status="complete", weights=str(best.resolve()), weights_sha256=sha256_file(best))
    except Exception as exc:
        report.update(status="failed", error=str(exc))
        raise
    finally:
        write_json(report_path, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/field-pose-multicamera-v1"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/field-pose-20261019-b8w4"))
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    train(args.dataset, args.output, args.epochs, args.batch, args.imgsz, args.workers)
