"""Inference, training and auditable evaluation. No fake labels or review approvals."""

import contextlib
import csv
import gc
import json
import logging
import os
import shutil
from pathlib import Path

from .core import (canonical_hash, dataset_path, environment, label_pixels, load_manifest, now,
                   read_json, read_labels, require_approval, require_experiment_data, sha256, write_json)
from .metrics import evaluate


def yolo(weights):
    os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(".cache/ultralytics").resolve()))
    (Path(os.environ["YOLO_CONFIG_DIR"]) / "Ultralytics").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(Path(".cache/matplotlib").resolve()))
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    from ultralytics import YOLO, settings
    settings.update({"weights_dir": str(Path("models").resolve()), "datasets_dir": str(Path("data").resolve()),
                     "runs_dir": str(Path("runs").resolve()), "sync": False})
    return YOLO(str(weights))


def fresh_output(path):
    path = Path(path).resolve()
    path.mkdir(parents=True, exist_ok=False)
    return path


def class_mapping(model, path, names):
    """Mapping is by verified model class name, never by assumed integer IDs."""
    mapping = read_json(path)
    raw = model.names
    ids = {}
    for source_name, target_name in mapping.items():
        if source_name not in raw.values() or target_name not in names:
            raise ValueError(f"Unverified source/target class mapping: {source_name} -> {target_name}")
        ids[next(i for i, name in raw.items() if name == source_name)] = names.index(target_name)
    if not ids:
        raise ValueError("No classes mapped")
    return ids


def assert_final_access(manifest, approvals, weights, config, freeze_path):
    report = require_approval(manifest, approvals)
    freeze = read_json(freeze_path)
    identity = {"dataset_fingerprint": report["dataset_fingerprint"], "weights_sha256": sha256(weights),
                "inference_config_hash": canonical_hash(config)}
    if any(freeze.get(k) != v for k, v in identity.items()):
        raise ValueError("Final evaluation differs from the frozen dataset/model/inference settings")
    return identity


def predict_manifest(manifest, weights, mapping_path, out, split="val", imgsz=640, device="0",
                     confidence=0.001, freeze=None, approvals=None):
    data, root = load_manifest(manifest)
    if split not in ("train", "val", "test"):
        raise ValueError("Unknown subset")
    config = {"imgsz": imgsz, "device": device, "confidence": confidence, "nms_iou": 0.7,
              "max_det": 300, "mapping": read_json(mapping_path)}
    if split == "test":
        if not freeze or not approvals:
            raise ValueError("Test inference requires --freeze and --approvals; use development data first")
        identity = assert_final_access(manifest, approvals, weights, config, freeze)
        # Record exposure before inference, including failed attempts. Do not erase this record.
        access = root / "test-access.jsonl"
        test_identity = canonical_hash(sorted([f["video_id"], f["frame_index"], sha256(dataset_path(root, f["image"]))]
                                             for f in data["frames"] if f["split"] == "test"))
        if access.exists():
            for line in access.read_text(encoding="utf-8").splitlines():
                old = json.loads(line)
                if old.get("test_set_fingerprint") == test_identity and any(old.get(k) != v for k, v in identity.items()):
                    raise ValueError("These test images have already been exposed to a different configuration; independent evaluation needs new held-out data")
        with access.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"recorded_at": now(), "test_set_fingerprint": test_identity, **identity}) + "\n")
    if not 0 <= confidence <= 1 or imgsz <= 0:
        raise ValueError("Invalid confidence or image size")
    model = yolo(weights)
    weight_path = Path(model.ckpt_path).resolve()
    ids = class_mapping(model, mapping_path, data["names"])
    selected = [f for f in data["frames"] if f["split"] == split]
    if not selected:
        raise ValueError("No selected frames")
    out = fresh_output(out)
    proposals = out / "proposals"
    proposals.mkdir()
    overlays = out / "overlays"
    overlays.mkdir()
    model_id = f"{weight_path.name}:{sha256(weight_path)[:16]}"
    with (out / "detections.jsonl").open("w", encoding="utf-8") as stream:
        for frame in selected:
            source = dataset_path(root, frame["image"])
            result = model.predict(str(source), imgsz=imgsz, device=device, conf=confidence,
                                   iou=0.7, max_det=300, classes=list(ids), verbose=False)[0]
            if tuple(result.orig_shape) != (frame["height"], frame["width"]):
                raise ValueError("Manifest dimensions do not match decoded source image")
            record = {"schema_version": "1.0", "video_id": frame["video_id"], "frame_id": frame["frame_id"],
                      "frame_index": frame["frame_index"], "timestamp_s": frame["timestamp_s"],
                      "width": frame["width"], "height": frame["height"], "run_id": out.name, "detections": []}
            labels = []
            for box in result.boxes:
                source_cls = int(box.cls.item())
                target = ids[source_cls]
                x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())
                w, h = frame["width"], frame["height"]
                x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
                if x2 <= x1 or y2 <= y1:
                    raise ValueError("Invalid predicted box")
                record["detections"].append({"model_id": model_id, "class_id": source_cls,
                    "dataset_class_id": target, "class_name": model.names[source_cls],
                    "semantic_class": data["names"][target], "confidence": float(box.conf.item()),
                    "bbox_xyxy": [x1, y1, x2, y2]})
                labels.append(f"{target} {(x1+x2)/2/w:.8f} {(y1+y2)/2/h:.8f} {(x2-x1)/w:.8f} {(y2-y1)/h:.8f}")
            stream.write(json.dumps(record, allow_nan=False) + "\n")
            (proposals / f"{frame['frame_id']}.txt").write_text("\n".join(labels) + ("\n" if labels else ""), encoding="utf-8")
            # OpenCV arrays returned by plot() are BGR.
            from PIL import Image
            Image.fromarray(result.plot()[:, :, ::-1]).save(overlays / f"{frame['frame_id']}.jpg")
    write_json(out / "run.json", {"recorded_at": now(), "kind": "inference", "split": split,
                "manifest_sha256": sha256(manifest), "weights": str(weight_path),
                "weights_sha256": sha256(weight_path), "config": config, "environment": environment(),
                "input_hashes": {f["frame_id"]: sha256(dataset_path(root, f["image"])) for f in selected},
                "annotation_status": "automatic_proposals_only_not_human_reviewed"})
    return {"output": str(out), "frames": len(selected), "status": "automatic_proposals_only"}


def build_yolo_dataset(manifest, approvals, output, provisional_ai=False):
    require_experiment_data(manifest, approvals, provisional_ai)
    data, root = load_manifest(manifest)
    output = fresh_output(output)
    for split in ("train", "val"):
        for sub in ("images", "labels"):
            (output / sub / split).mkdir(parents=True)
        for frame in data["frames"]:
            if frame["split"] != split:
                continue
            fid = frame["frame_id"]
            # IDs are used as filenames; reject path separators even if manifest paths are valid.
            if Path(fid).name != fid or any(c in fid for c in '/\\:'):
                raise ValueError("Unsafe frame_id")
            source = dataset_path(root, frame["image"])
            shutil.copy2(source, output / "images" / split / f"{fid}{source.suffix}")
            shutil.copy2(dataset_path(root, frame["label"]), output / "labels" / split / f"{fid}.txt")
    import yaml
    (output / "data.yaml").write_text(yaml.safe_dump({"path": str(output), "train": "images/train",
                  "val": "images/val", "names": dict(enumerate(data["names"]))}, sort_keys=False), encoding="utf-8")
    return output / "data.yaml"


def train(manifest, approvals, config_path, weights, output, device="0", smoke=False, provisional_ai=False):
    """Only retry CUDA OOM at batches 4, 2, 1, each from fresh pretrained weights."""
    import torch
    if device != "cpu" and not torch.cuda.is_available():
        raise ValueError("CUDA is unavailable; explicitly select cpu for a separately identified run")
    report = require_experiment_data(manifest, approvals, provisional_ai)
    config = read_json(config_path)
    if config.get("batch") not in (4, 2, 1):
        raise ValueError("Reference batch must follow the 4 → 2 → 1 memory rule")
    output = fresh_output(output)
    data_path = build_yolo_dataset(manifest, approvals, output / "dataset", provisional_ai)
    write_json(output / "provenance.json", {"created_at": now(), "dataset_fingerprint": report["dataset_fingerprint"],
               "manifest_sha256": sha256(manifest), "approval_sha256": sha256(approvals), "environment": environment(),
               "requested_config": config, "smoke_only": smoke,
               "review_policy": "provisional_ai_visual" if provisional_ai else "independent_team_review",
               "human_review_completed": not provisional_ai,
               "initial_weights_sha256": sha256(weights)})
    if smoke:
        config.update(epochs=1, patience=1)
    attempts = []
    for batch in [b for b in (4, 2, 1) if b <= config["batch"]]:
        model = None
        try:
            model = yolo(weights)
            attempt = output / f"batch-{batch}"
            config_used = {**config, "batch": batch, "data": str(data_path), "device": device,
                           "project": str(output), "name": attempt.name, "exist_ok": False, "workers": 0}
            write_json(output / f"requested-batch-{batch}.json", config_used)
            with (output / f"train-batch-{batch}.log").open("w", encoding="utf-8") as log:
                from ultralytics.utils import LOGGER
                handler = logging.StreamHandler(log)
                LOGGER.addHandler(handler)
                try:
                    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                        model.train(**config_used)
                finally:
                    LOGGER.removeHandler(handler)
            best = attempt / "weights" / "best.pt"
            if not best.is_file():
                raise ValueError("Training did not produce best.pt")
            attempts.append({"batch": batch, "status": "completed", "best": str(best), "best_sha256": sha256(best)})
            write_json(output / "status.json", {"status": "smoke_completed" if smoke else "completed", "attempts": attempts})
            return attempts[-1]
        except torch.cuda.OutOfMemoryError as exc:
            attempts.append({"batch": batch, "status": "cuda_out_of_memory", "error": str(exc)})
            write_json(output / "status.json", {"status": "retrying_smaller_batch", "attempts": attempts})
            del model
            gc.collect()
            torch.cuda.empty_cache()
        except Exception as exc:
            attempts.append({"batch": batch, "status": "failed", "error": str(exc)})
            write_json(output / "status.json", {"status": "failed", "attempts": attempts})
            raise
    write_json(output / "status.json", {"status": "failed_all_batches_oom", "attempts": attempts})
    raise RuntimeError("All reference batches failed; record a new technical decision before changing other settings")


def evaluate_run(manifest, prediction_dir, output, work_conf=0.25, freeze=None, approvals=None, provisional_ai=False):
    prediction_dir = Path(prediction_dir)
    run = read_json(prediction_dir / "run.json")
    data, root = load_manifest(manifest)
    if run["manifest_sha256"] != sha256(manifest):
        raise ValueError("Manifest changed since inference; regenerate predictions")
    split = run["split"]
    if provisional_ai:
        if split == "test":
            raise ValueError("Provisional route supports development scores only; final test requires team review")
        require_experiment_data(manifest, approvals, True)
    if split == "test":
        if not freeze or not approvals:
            raise ValueError("Final scoring requires freeze and approvals")
        assert_final_access(manifest, approvals, run["weights"], run["config"], freeze)
    selected = {f["frame_id"]: f for f in data["frames"] if f["split"] == split}
    if run.get("input_hashes") != {fid: sha256(dataset_path(root, f["image"])) for fid, f in selected.items()}:
        raise ValueError("Source images changed since inference; regenerate predictions")
    truth, predicted = {}, {}
    for fid, frame in selected.items():
        if not provisional_ai and (frame.get("review_status") != "approved" or not frame.get("reviewer") or frame.get("reviewer") == frame.get("annotator")):
            raise ValueError(f"{fid}: scored annotations require independent review")
        truth[fid] = [{"class_id": label["class_id"], "bbox_xyxy": label_pixels(label, frame["width"], frame["height"])}
                      for label in read_labels(dataset_path(root, frame["label"]), len(data["names"]))]
    for line in (prediction_dir / "detections.jsonl").read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        fid = record["frame_id"]
        if fid not in selected or fid in predicted:
            raise ValueError("Unexpected or duplicate predicted frame")
        predicted[fid] = [{"class_id": b["dataset_class_id"], "bbox_xyxy": b["bbox_xyxy"], "confidence": b["confidence"]} for b in record["detections"]]
    result = evaluate(truth, predicted, data["names"], confidence=work_conf)
    result.update(recorded_at=now(), split=split, inference_config=run["config"],
                  manifest_sha256=sha256(manifest), label_fingerprint=canonical_hash(truth),
                  prediction_sha256=sha256(prediction_dir / "detections.jsonl"), weights_sha256=run["weights_sha256"],
                  review_policy="provisional_ai_visual" if provisional_ai else "independent_team_review",
                  human_review_completed=not provisional_ai)
    output = fresh_output(output)
    errors = result.pop("errors")
    write_json(output / "metrics.json", result)
    write_json(output / "errors.json", errors)
    with (output / "per-class.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=result["per_class"][0].keys())
        writer.writeheader()
        writer.writerows(result["per_class"])
    text = ["# Detection evaluation", "", f"Subset: {split}", f"Method: {result['method']}", "",
            f"mAP@50: {result['mAP50']}", f"mAP@50:95: {result['mAP50_95']}", "",
            f"FP/FN records at confidence {work_conf}: {len(errors)}. Causes still require visual analysis."]
    (output / "report.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    return result
