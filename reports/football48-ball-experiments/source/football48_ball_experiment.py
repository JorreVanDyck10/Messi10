"""Reproducible, provisional ball fine-tuning on the delivered football48 crops.

This development-only route has no independent test split and never grants team review.
The older persoon1 final-test/review gates remain unchanged.
"""

from __future__ import annotations

import argparse
import contextlib
import gc
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np
import torch

from assets.annotations.football48.make_ball_only import create
from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.pipeline import code_identity, dependencies
from football_pipeline.video import ROOT
from persoon1.metrics import evaluate
from persoon1.modeling import yolo


def truth_and_identity(source):
    manifest = read_json(source / "manifest.json")
    truth = {"train": {}, "val": {}}
    files, groups, sizes = {}, {}, []
    for frame in manifest["frames"]:
        assert frame["split"] in truth
        group = groups.setdefault(frame["group_id"], frame["split"])
        assert group == frame["split"]
        image, label = source / frame["image"], source / frame["label"]
        assert sha256_file(image) == frame["image_sha256"]
        files[frame["image"]] = sha256_file(image)
        files[frame["label"]] = sha256_file(label)
        assert cv2.imread(str(image)).shape[:2] == (640, 1280)
        balls = []
        for line in label.read_text().splitlines():
            cls, x, y, width, height = map(float, line.split())
            assert cls in (0, 1) and np.isfinite([x, y, width, height]).all()
            assert width > 0 and height > 0 and 0 <= x - width / 2 < x + width / 2 <= 1.000001
            assert 0 <= y - height / 2 < y + height / 2 <= 1.000001
            if cls == 1:
                balls.append(
                    {
                        "class_id": 0,
                        "bbox_xyxy": [
                            (x - width / 2) * 1280,
                            (y - height / 2) * 640,
                            (x + width / 2) * 1280,
                            (y + height / 2) * 640,
                        ],
                    }
                )
                sizes.append([width * 1280, height * 640])
        assert len(balls) == int(frame["ball_presence"] == "visible_labelled")
        truth[frame["split"]][frame["frame_id"]] = balls
    assert [len(truth[s]) for s in truth] == [36, 12]
    assert [sum(map(len, truth[s].values())) for s in truth] == [26, 10]
    assert len(groups) == 8
    return (
        manifest,
        truth,
        {
            "fingerprint": digest_json({"manifest": manifest, "files": files}),
            "files": files,
            "groups": groups,
            "ball_size_min_median_max_px": [
                np.min(sizes, 0).tolist(),
                np.median(sizes, 0).tolist(),
                np.max(sizes, 0).tolist(),
            ],
            "review_policy": "provisional_ai_visual",
            "human_review_completed": False,
            "independent_final_test_available": False,
        },
    )


def measure(weights, source_class, manifest, truth, source, output, imgsz, device):
    output.mkdir()
    model = yolo(weights)
    ids = [i for i, name in model.names.items() if name == source_class]
    if len(ids) != 1:
        raise ValueError(f"Actual weights do not contain exactly one {source_class} class")
    predictions = {}
    started = time.perf_counter()
    with (output / "detections.jsonl").open("w", encoding="utf-8") as stream:
        for frame in manifest["frames"]:
            if frame["split"] != "val":
                continue
            image = cv2.imread(str(source / frame["image"]))
            result = model.predict(
                image,
                imgsz=imgsz,
                conf=0.001,
                iou=0.7,
                max_det=300,
                classes=ids,
                device=device,
                verbose=False,
            )[0]
            boxes = [
                {"class_id": 0, "bbox_xyxy": box.tolist(), "confidence": float(score)}
                for box, score in zip(result.boxes.xyxy.cpu().numpy(), result.boxes.conf.cpu().numpy())
            ]
            fid = frame["frame_id"]
            predictions[fid] = boxes
            stream.write(json.dumps({"frame_id": fid, "detections": boxes}) + "\n")
            for gt in truth["val"][fid]:
                x1, y1, x2, y2 = map(round, gt["bbox_xyxy"])
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 1)
            for box in boxes:
                if box["confidence"] >= 0.25:
                    x1, y1, x2, y2 = map(round, box["bbox_xyxy"])
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 150, 255), 1)
            cv2.imwrite(str(output / (fid + ".jpg")), image)
    metrics = evaluate(truth["val"], predictions, ["ball"], confidence=0.25)
    errors = metrics.pop("errors")
    metrics.update(
        weights_sha256=sha256_file(weights),
        actual_model_names=model.names,
        source_class_id=ids[0],
        source_class_name=source_class,
        dataset_class_id=0,
        split="val",
        frames=12,
        objects=10,
        human_review_completed=False,
        inference={
            "imgsz": imgsz,
            "confidence_floor": 0.001,
            "nms_iou": 0.7,
            "max_det": 300,
            "device": device,
        },
        runtime_s=time.perf_counter() - started,
    )
    write_json(output / "metrics.json", metrics)
    write_json(output / "errors.json", {"errors": errors})
    del model
    gc.collect()
    torch.cuda.empty_cache()
    return metrics


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--device", default="0")
    p.add_argument("--provisional-ai-labels", action="store_true", required=True)
    p.add_argument(
        "--candidate-weights", type=Path, help="Evaluate an existing candidate instead of retraining"
    )
    args = p.parse_args()
    run = args.run.resolve()
    if run.exists():
        p.error("Use a new run directory; existing experiments are not overwritten")
    run.mkdir(parents=True)
    source = ROOT / "assets/annotations/football48"
    manifest, truth, data_identity = truth_and_identity(source)
    config = read_json(args.config)
    weights = ROOT / "models/yolo11n.pt"
    assert sha256_file(weights) == "0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1"
    write_json(
        run / "preregistration.json",
        {
            "recorded_at": datetime.now(UTC).isoformat(),
            "dataset": data_identity,
            "config": config,
            "code": code_identity(),
            "script_sha256": sha256_file(__file__),
            "dependencies": dependencies(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "gpu_memory_bytes": torch.cuda.get_device_properties(0).total_memory
            if torch.cuda.is_available()
            else None,
            "hypothesis": "Native-scale ball crops retain detail lost in full panorama resizing; limited fine-tuning may beat the pretrained sports-ball baseline.",
            "selection": "Primary target AP50:95, then AP50, plus FP/FN examples; no independent final test claim.",
            "limits": [
                "One match, 26 train/10 val ball objects, AI labels only.",
                "Masked native crops; performance does not establish full raw-video detection quality.",
            ],
        },
    )
    baseline = measure(
        weights, "sports ball", manifest, truth, source, run / "baseline", config["imgsz"], args.device
    )
    if args.candidate_weights:
        best = args.candidate_weights.resolve()
    else:
        dataset = run / "dataset"
        create(dataset)
        # An explicit root avoids Ultralytics resolving relative paths under a different datasets_dir.
        (dataset / "data.yaml").write_text(
            f"path: {dataset.as_posix()}\ntrain: images/train\nval: images/val\nnames:\n  0: ball\n",
            encoding="utf-8",
        )
        attempts = []
        best = None
        for batch in (4, 2, 1):
            if batch > config["batch"]:
                continue
            model = yolo(weights)
            try:
                used = {
                    **config,
                    "batch": batch,
                    "data": str(dataset / "data.yaml"),
                    "device": args.device,
                    "workers": 0,
                    "project": str(run),
                    "name": f"batch-{batch}",
                    "exist_ok": False,
                }
                write_json(run / f"requested-batch-{batch}.json", used)
                with (run / f"train-batch-{batch}.log").open("w", encoding="utf-8") as log:
                    from ultralytics.utils import LOGGER

                    handler = logging.StreamHandler(log)
                    LOGGER.addHandler(handler)
                    try:
                        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                            model.train(**used)
                    finally:
                        LOGGER.removeHandler(handler)
                best = run / f"batch-{batch}/weights/best.pt"
                assert best.is_file()
                attempts.append({"batch": batch, "status": "completed", "best_sha256": sha256_file(best)})
                break
            except torch.cuda.OutOfMemoryError:
                attempts.append({"batch": batch, "status": "out_of_memory"})
            finally:
                del model
                gc.collect()
                torch.cuda.empty_cache()
                write_json(run / "attempts.json", {"attempts": attempts})
        if best is None:
            raise RuntimeError("All batches ran out of GPU memory")
    candidate = measure(
        best, "ball", manifest, truth, source, run / "candidate", config["imgsz"], args.device
    )
    assert data_identity == truth_and_identity(source)[2], "Dataset changed during experiment"
    report = {
        "status": "completed",
        "baseline": baseline,
        "candidate": candidate,
        "candidate_weights": str(best),
        "delta_AP50": candidate["mAP50"] - baseline["mAP50"],
        "delta_AP50_95": candidate["mAP50_95"] - baseline["mAP50_95"],
        "human_review_completed": False,
        "independent_final_test": False,
    }
    write_json(run / "comparison.json", report)
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
