"""Traint en vergelijkt de PnLCalib-punten- en lijnnetwerken; voorstellen blijven onderscheiden van gereviewde labels.


Run with .tools/field-training-env/Scripts/python.exe; upstream stays unmodified.
"""

from __future__ import annotations

import argparse
import copy
import importlib.metadata
import io
import json
import math
import random
import sys
import time
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from .contracts import atomic_replace, digest_json, read_json, sha256_file, write_json
from .field_layout import LINES_UV, POINTS_UV
from .field_model_spec import RELEASE_WEIGHTS, UPSTREAM_REVISION, validate_runtime_models

LABEL_ROUNDOFF_TOLERANCE = 0.0001


def timestamp():
    """Geef een UTC-tijdstip als ISO-string terug voor trainings- en vergelijkingsadministratie."""
    return datetime.now(UTC).isoformat()


def validate_labels(data):
    """Controleer veldlabelstructuur, semantische namen en coördinaten en retourneer de genormaliseerde
    labelrepresentatie.
    """
    if not isinstance(data, dict) or not data:
        raise ValueError("Missing semantic field annotations")
    normalized = copy.deepcopy(data)
    for name, points in normalized.items():
        if not isinstance(name, str) or not isinstance(points, list):
            raise ValueError("Invalid line annotation")
        for point in points:
            if not all(
                type(point.get(k)) in (int, float)
                and math.isfinite(point[k])
                and -LABEL_ROUNDOFF_TOLERANCE <= point[k] <= 1 + LABEL_ROUNDOFF_TOLERANCE
                for k in ("x", "y")
            ):
                raise ValueError("Field labels must use finite normalized coordinates")
            for k in ("x", "y"):
                point[k] = min(1.0, max(0.0, point[k]))
    return normalized


def clip_provider_lines(data):
    """Clip subpixel/interpolated border overshoots without bending the annotated line."""
    clipped = {}
    for name, points in data.items():
        xy = np.asarray([[p["x"], p["y"]] for p in points], float)
        if not len(xy):
            continue
        if not np.isfinite(xy).all() or (xy < -0.005).any() or (xy > 1.005).any():
            raise ValueError("Provider line exceeds the bounded image-border preprocessing policy")
        visible = []
        for a, b in zip(xy, xy[1:]):
            delta = b - a
            lower, upper = 0.0, 1.0
            for p, q in zip((-delta[0], delta[0], -delta[1], delta[1]), (a[0], 1 - a[0], a[1], 1 - a[1])):
                if abs(p) < 1e-15:
                    if q < 0:
                        upper = -1
                        break
                elif p < 0:
                    lower = max(lower, q / p)
                else:
                    upper = min(upper, q / p)
            if lower <= upper:
                for point in (a + lower * delta, a + upper * delta):
                    if not visible or np.linalg.norm(point - visible[-1]) > 1e-12:
                        visible.append(point)
        if visible:
            clipped[name] = [
                {"x": float(np.clip(p[0], 0, 1)), "y": float(np.clip(p[1], 0, 1))} for p in visible
            ]
    return validate_labels(clipped)


def labels_for_row(row):
    """Lees de labels van deze datasetrij en pas de juiste validatie of clipping van zichtbare
    providerlijnen toe.
    """
    data = read_json(row["label"])
    return (
        clip_provider_lines(data)
        if row.get("label_policy") == "provider_visible_polylines_v1"
        else validate_labels(data)
    )


def dataset_index(root, limits=None, splits=("train", "valid")):
    """Explicit index bypasses upstream Windows basename and missing match_info bugs."""
    root = Path(root).resolve()
    metadata = root.parent / "manifest.json"
    provider_policy = (
        metadata.is_file()
        and read_json(metadata).get("source") == "https://huggingface.co/datasets/SoccerNet/SN-GSR-2024"
    )
    rows, excluded, image_splits, match_splits = [], [], {}, {}
    for split in splits:
        candidates = list(root.rglob(split + "/match_info.json"))
        if len(candidates) != 1:
            raise ValueError(f"Expected one {split}/match_info.json under {root}, found {len(candidates)}")
        info_path = candidates[0]
        match_info = read_json(info_path)
        images = [
            image
            for image in sorted(info_path.parent.glob("*.jpg"))
            if int(match_info[image.name]["ms_time"]) == int(match_info[image.name]["replay_time"])
        ]
        limit = (limits or {}).get(split)
        if limit and limit < len(images):
            images = [images[i] for i in np.linspace(0, len(images) - 1, limit, dtype=int)]
        for image in images:
            info = match_info[image.name]
            if int(info["ms_time"]) != int(info["replay_time"]):
                continue
            label = image.with_suffix(".json")
            try:
                original = read_json(label)
                normalized = clip_provider_lines(original) if provider_policy else validate_labels(original)
            except (ValueError, KeyError, TypeError) as exc:
                excluded.append({"image": str(image), "reason": str(exc)})
                continue
            image_hash = sha256_file(image)
            if image_hash in image_splits and image_splits[image_hash] != split:
                raise ValueError("Exact duplicate image across official train/valid splits")
            image_splits[image_hash] = split
            match_id = None
            if info.get("match") and info.get("date"):
                match_id = digest_json(
                    [str(info.get(k, "")).strip() for k in ("league", "season", "date", "match")]
                )
                if match_id in match_splits and match_splits[match_id] != split:
                    raise ValueError("Same match appears in both train and valid splits")
                match_splits[match_id] = split
            rows.append(
                {
                    "image": str(image),
                    "label": str(label),
                    "split": split,
                    "image_sha256": image_hash,
                    "label_sha256": sha256_file(label),
                    "match_info": info,
                    "match_id": match_id,
                    "label_policy": "provider_visible_polylines_v1" if provider_policy else "strict",
                    "boundary_roundoff_corrections": sum(
                        original[name][i][k] != point[k]
                        for name, points in normalized.items()
                        for i, point in enumerate(points)
                        for k in ("x", "y")
                    )
                    if not provider_policy
                    else 0,
                    "provider_boundary_points": sum(
                        not 0 <= p[k] <= 1 for pts in original.values() for p in pts for k in ("x", "y")
                    )
                    if provider_policy
                    else 0,
                }
            )
    identity = digest_json(rows)
    return {
        "schema_version": 1,
        "root": str(root),
        "fingerprint": identity,
        "frames": rows,
        "excluded": excluded,
        "main_camera_only": True,
        "sampling_limits": limits,
        "label_roundoff_tolerance": LABEL_ROUNDOFF_TOLERANCE,
        "match_counts": {split: sum(s == split for s in match_splits.values()) for split in splits},
        "cross_split_match_overlap": 0,
        "official_splits_preserved": True,
        "pretraining_overlap": True,
        "independent_accuracy_claim": False,
    }


def upstream_runtime(path):
    """Controleer de geïsoleerde PnLCalib-runtime en maak zijn vastgelegde broncode beschikbaar voor de
    veldfuncties.
    """
    import subprocess

    runtime = read_json(path)
    repository = Path(runtime["repository"])
    revision = subprocess.check_output(["git", "-C", str(repository), "rev-parse", "HEAD"], text=True).strip()
    if revision != UPSTREAM_REVISION:
        raise ValueError("Unexpected upstream revision")
    for name, expected in runtime["source_sha256"].items():
        if sha256_file(repository / name) != expected:
            raise ValueError(f"Changed upstream file: {name}")
    validate_runtime_models(runtime)
    sys.path.insert(0, str(repository))
    sys.path.insert(0, str(repository / "sn_calibration/src"))
    return runtime


def load_model(runtime, role, device):
    """Bouw het punten- of lijnnetwerk van de runtime, laad de bijbehorende gewichten en verplaats het
    naar het gevraagde device.
    """
    import torch
    from model.cls_hrnet import get_cls_net
    from model.cls_hrnet_l import get_cls_net as get_lines

    filename = "hrnetv2_w48.yaml" if role == "keypoints" else "hrnetv2_w48_l.yaml"
    cfg = read_yaml(Path(runtime["repository"]) / "config" / filename)
    constructor = get_cls_net if role == "keypoints" else get_lines
    model = constructor(cfg)
    key = "weights_keypoints" if role == "keypoints" else "weights_lines"
    model.load_state_dict(torch.load(runtime[key], map_location="cpu", weights_only=True), strict=True)
    return model.to(device)


def read_yaml(path):
    """Lees een YAML-configuratie met safe_load, zonder YAML-objectconstructors uit te voeren."""
    import yaml

    return yaml.safe_load(Path(path).read_text())


def masked_heatmap_loss(output, target, mask):
    """Mask per-channel squared errors before reduction, normalized by valid pixels."""
    weight = mask.to(output.dtype)[..., None, None]
    error = (output.float() - target.float()).square()
    return (error * weight).sum() / (weight.sum() * output.shape[-1] * output.shape[-2]).clamp_min(1)


class FieldDataset:
    def __init__(self, rows, role, augment=False):
        """Bewaar datasetrijen, modeltaak en augmentatiekeuze en maak de begrensde cache voor
        heatmaptargets.
        """
        self.rows, self.role, self.augment = rows, role, augment
        self.target_cache = OrderedDict()

    def __len__(self):
        """Geef het aantal trainings- of validatievoorbeelden in deze velddataset terug."""
        return len(self.rows)

    def __getitem__(self, index):
        """Lees één bronbeeld en zijn heatmaptargets, pas de gekozen augmentatie toe en retourneer de
        tensors en het geldigheidsmasker.
        """
        import torch
        import torchvision.transforms.functional as tf
        from model.transforms import RandomHorizontalFlip
        from PIL import Image
        from utils.utils_keypoints import KeypointsDB
        from utils.utils_lines import LineKeypointsDB

        row = self.rows[index]
        data = copy.deepcopy(labels_for_row(row))
        if "Goal left post left" in data:
            data["Goal left post left "] = data.pop("Goal left post left")
        with Image.open(row["image"]) as source:
            image = tf.resize(tf.to_tensor(source.convert("RGB")), [540, 960], antialias=True)
        if self.augment:
            sample = RandomHorizontalFlip(0.5)({"image": image, "data": data})
            image, data = sample["image"], sample["data"]
            image = tf.adjust_brightness(image, random.uniform(0.95, 1.05))
        key = digest_json({"role": self.role, "labels": data, "shape": list(image.shape[-2:])})
        if key not in self.target_cache:
            # The upstream four-point ellipse interpolation draws random noise. Fix
            # it per geometry, including validation, without consuming augmentation RNG.
            numpy_state = np.random.get_state()
            np.random.seed(int(key[:8], 16))
            try:
                if self.role == "keypoints":
                    target, mask = KeypointsDB(data, image).get_tensor_w_mask()
                else:
                    target = LineKeypointsDB(data, image).get_tensor()
                    mask = np.ones(target.shape[0])
            finally:
                np.random.set_state(numpy_state)
            compressed = io.BytesIO()
            np.savez_compressed(
                compressed, target=np.asarray(target, np.float32), mask=np.asarray(mask, np.float32)
            )
            self.target_cache[key] = compressed.getvalue()
            if len(self.target_cache) > 128:
                self.target_cache.popitem(last=False)
        self.target_cache.move_to_end(key)
        with np.load(io.BytesIO(self.target_cache[key]), allow_pickle=False) as values:
            return image, torch.from_numpy(values["target"]), torch.from_numpy(values["mask"])


def atomic_torch_save(value, path):
    """Sla een PyTorch-toestand eerst tijdelijk op en vervang daarna atomair het definitieve
    checkpointbestand.
    """
    import torch

    temporary = path.with_suffix(path.suffix + ".partial")
    torch.save(value, temporary)
    atomic_replace(temporary, path)


def publish_epoch_checkpoint(report_path, report, role, record, state, checkpoint):
    """Publish a fresh checkpoint, then its pointer; a crash preserves the previous committed epoch."""
    atomic_torch_save(state, checkpoint)
    committed = copy.deepcopy(report)
    committed["models"][role] = {
        **copy.deepcopy(record),
        "last_path": str(checkpoint.resolve()),
        "last_sha256": sha256_file(checkpoint),
    }
    committed["updated_at"] = timestamp()
    committed["training_performed"] = True
    write_json(report_path, committed)
    return committed


def run_epoch(
    model,
    loader,
    device,
    optimizer=None,
    scaler=None,
    max_steps=None,
    *,
    frozen_features=False,
    deadline=None,
    progress=None,
    progress_callback=None,
):
    """Verwerk batches en bereken de gemiddelde heatmaploss; pas alleen gewichten aan als een optimizer
    is meegegeven en respecteer de staplimiet.
    """
    import torch

    training = optimizer is not None
    model.train(training and not frozen_features)
    if training and frozen_features:
        model.head[0][3].train()
    total, samples, tick = 0.0, 0, time.monotonic()
    with torch.set_grad_enabled(training):
        for step, (image, target, mask) in enumerate(loader):
            if deadline is not None and time.monotonic() >= deadline:
                break
            if max_steps and step >= max_steps:
                break
            image, target, mask = image.to(device), target.to(device), mask.to(device)
            if training:
                optimizer.zero_grad(set_to_none=True)
            with torch.autocast("cuda", enabled=device.type == "cuda"):
                prediction = model(image)
                if prediction.shape != target.shape:
                    raise ValueError(f"Heatmap shape mismatch {prediction.shape} != {target.shape}")
                loss = masked_heatmap_loss(prediction, target, mask)
            if not torch.isfinite(loss):
                raise ValueError("Non-finite heatmap loss")
            if training:
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 10.0)
                scaler.step(optimizer)
                scaler.update()
            total += float(loss.detach()) * image.shape[0]
            samples += image.shape[0]
            if progress is not None:
                progress["samples"] = samples
            if step == 0 or (step + 1) % 50 == 0:
                if progress_callback is not None:
                    progress_callback(samples)
                print(
                    json.dumps(
                        {
                            "phase": "train" if training else "valid",
                            "step": step + 1,
                            "samples": samples,
                            "loss": total / samples,
                            "elapsed_s": time.monotonic() - tick,
                        }
                    ),
                    flush=True,
                )
    if not samples:
        if deadline is not None:
            raise TimeoutError("Field training budget expired before an optimizer step")
        raise ValueError("Empty dataset")
    return total / samples


def _train(args):
    """Train de gevraagde punten- en lijnmodellen met validatie, checkpoints en voortgang, en behoud
    voltooide modelstappen bij hervatten.
    """
    import torch
    from torch.utils.data import DataLoader

    runtime = upstream_runtime(args.runtime)
    if any(runtime["models"][role]["sha256"] != RELEASE_WEIGHTS[role]["sha256"] for role in RELEASE_WEIGHTS):
        raise ValueError("This training route starts from the pinned official base weights")
    limits = (
        {"train": 1, "valid": 1} if args.smoke else {"train": args.limit_train, "valid": args.limit_valid}
    )
    index = dataset_index(args.dataset, limits)
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "dataset-index.json", index)
    config = {
        "epochs": args.epochs,
        "batch": 1,
        "lr": args.lr,
        "optimizer": "Adam",
        "patience": args.patience,
        "weight_decay": args.weight_decay,
        "scheduler": "ReduceLROnPlateau_factor_0.5_patience_1",
        "best_checkpoint_includes_unmodified_baseline": True,
        "head_only": args.head_only,
        "target_generation": "geometry_seeded_interpolation; exact_float32_compressed_cache",
        "seed": 42,
        "amp": True,
        "image_size": [960, 540],
        "smoke": args.smoke,
        "limit_train": args.limit_train,
        "limit_valid": args.limit_valid,
    }
    identity = digest_json(
        {
            "dataset": index["fingerprint"],
            "models": runtime["models"],
            "config": config,
            "trainer_sha256": sha256_file(__file__),
            "upstream": runtime["source_sha256"],
        }
    )
    report_path = args.output / "training-report.json"
    if report_path.exists():
        report = read_json(report_path)
        if report["identity"] != identity:
            raise ValueError("Training inputs/configuration changed; use a new --output directory")
    else:
        report = {
            "schema_version": 1,
            "identity": identity,
            "started_at": timestamp(),
            "dataset_fingerprint": index["fingerprint"],
            "dataset_version": read_json(args.dataset.parent / "manifest.json")["dataset_version"]
            if (args.dataset.parent / "manifest.json").is_file()
            else "SN-Calibration-2023",
            "config": config,
            "models": {},
            "status": "running",
            "training_performed": False,
            "is_smoke_test": args.smoke,
            "independent_accuracy_claim": False,
            "trainer_sha256": sha256_file(__file__),
            "upstream": runtime["upstream"],
            "dependencies": {
                p: importlib.metadata.version(p)
                for p in ("torch", "torchvision", "numpy", "scipy", "lsq-ellipse")
            },
        }
    device = torch.device("cuda:0")
    if not torch.cuda.is_available():
        raise ValueError("CUDA required for the configured local training route")
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = False
    report["status"] = "running"
    report.pop("error", None)
    report["gpu"] = torch.cuda.get_device_name(0)
    write_json(report_path, report)
    try:
        for role in ("keypoints", "lines"):
            saved = report["models"].get(role, {})
            if saved.get("status") == "complete":
                if sha256_file(saved["path"]) != saved["sha256"]:
                    raise ValueError("Completed model checkpoint changed")
                continue
            random.seed(42)
            np.random.seed(42)
            torch.manual_seed(42)
            torch.cuda.manual_seed_all(42)
            model = load_model(runtime, role, device)
            output_ids = {id(p) for p in model.head[0][3].parameters()}
            for parameter in model.parameters():
                parameter.requires_grad_(not args.head_only or id(parameter) in output_ids)
            trainable = [p for p in model.parameters() if p.requires_grad]
            if not trainable:
                raise ValueError("No trainable field output layer")
            optimizer = torch.optim.Adam(trainable, lr=args.lr, weight_decay=args.weight_decay)
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, factor=0.5, patience=1, min_lr=args.lr * 0.01
            )
            scaler = torch.cuda.amp.GradScaler()
            best, stale, start = float("inf"), 0, 0
            last = Path(saved.get("last_path", args.output / (role + "-last.pt")))
            best_path = Path(saved.get("path", args.output / (role + "-best.pt"))).resolve()
            history = list(saved.get("history", []))
            if last.exists():
                if sha256_file(last) != saved.get("last_sha256"):
                    raise ValueError("Resume checkpoint changed or interrupted before publication")
                state = torch.load(last, map_location="cpu", weights_only=False)
                if state["identity"] != identity:
                    raise ValueError("Resume checkpoint belongs to another experiment")
                model.load_state_dict(state["model"])
                optimizer.load_state_dict(state["optimizer"])
                scaler.load_state_dict(state["scaler"])
                scheduler.load_state_dict(state["scheduler"])
                best, stale, start = state["best"], state["stale"], state["epoch"] + 1
                random.setstate(state["random"])
                np.random.set_state(state["numpy"])
                torch.set_rng_state(state["torch_rng"])
                torch.cuda.set_rng_state(state["cuda_rng"])
                state = None
            train_rows = [r for r in index["frames"] if r["split"] == "train"]
            valid_rows = [r for r in index["frames"] if r["split"] == "valid"]
            if args.limit_train:
                train_rows = train_rows[: args.limit_train]
            if args.limit_valid:
                valid_rows = valid_rows[: args.limit_valid]
            train_loader = DataLoader(
                FieldDataset(train_rows, role, augment=not args.smoke),
                batch_size=1,
                shuffle=True,
                num_workers=0,
            )
            valid_loader = DataLoader(FieldDataset(valid_rows, role), batch_size=1, num_workers=0)
            baseline_loss = saved.get("baseline_valid_loss")
            if baseline_loss is None:
                baseline_loss = run_epoch(model, valid_loader, device, max_steps=1 if args.smoke else None)
                best = baseline_loss
                best_path = (args.output / f"{role}-best-000.pt").resolve()
                atomic_torch_save(model.state_dict(), best_path)
                print(json.dumps({"role": role, "baseline_valid_loss": baseline_loss}), flush=True)
            torch.cuda.reset_peak_memory_stats()
            print(f"Training {role}: {len(train_rows)} train, {len(valid_rows)} valid", flush=True)
            for epoch in range(start, 1 if args.smoke else args.epochs):
                if stale >= args.patience:
                    break
                tick = time.monotonic()
                training_loss = run_epoch(
                    model,
                    train_loader,
                    device,
                    optimizer,
                    scaler,
                    1 if args.smoke else None,
                    frozen_features=args.head_only,
                )
                validation_loss = run_epoch(model, valid_loader, device, max_steps=1 if args.smoke else None)
                used_lr = optimizer.param_groups[0]["lr"]
                scheduler.step(validation_loss)
                improved = validation_loss < best
                previous_best = best_path
                if improved:
                    best, stale = validation_loss, 0
                    best_path = (args.output / f"{role}-best-{epoch + 1:03d}.pt").resolve()
                    atomic_torch_save(model.state_dict(), best_path)
                else:
                    stale += 1
                # Reload on CPU without allocating a second GPU model.
                if not all(
                    torch.isfinite(t).all()
                    for t in torch.load(best_path, map_location="cpu", weights_only=True).values()
                ):
                    raise ValueError("Saved checkpoint contains non-finite tensors")
                history.append(
                    {
                        "epoch": epoch + 1,
                        "train_loss": training_loss,
                        "valid_loss": validation_loss,
                        "learning_rate": used_lr,
                        "runtime_s": time.monotonic() - tick,
                        "peak_gpu_bytes": torch.cuda.max_memory_allocated(),
                    }
                )
                checkpoint = args.output / f"{role}-resume-{epoch + 1:03d}.pt"
                state = {
                    "identity": identity,
                    "epoch": epoch,
                    "model": model.state_dict(),
                    "optimizer": optimizer.state_dict(),
                    "scaler": scaler.state_dict(),
                    "scheduler": scheduler.state_dict(),
                    "best": best,
                    "stale": stale,
                    "random": random.getstate(),
                    "numpy": np.random.get_state(),
                    "torch_rng": torch.get_rng_state(),
                    "cuda_rng": torch.cuda.get_rng_state(),
                }
                record = {
                    "status": "running",
                    "path": str(best_path),
                    "sha256": sha256_file(best_path),
                    "history": history,
                    "base_model": RELEASE_WEIGHTS[role],
                    "best_valid_loss": best,
                    "baseline_valid_loss": baseline_loss,
                    "selected_epoch": int(best_path.stem.rsplit("-", 1)[-1]),
                    "improved_over_baseline_loss": best < baseline_loss,
                    "trainable_parameters": sum(p.numel() for p in trainable),
                    "train_frames": len(train_rows),
                    "valid_frames": len(valid_rows),
                }
                report = publish_epoch_checkpoint(report_path, report, role, record, state, checkpoint)
                state = None
                for previous in (last, previous_best):
                    if (
                        previous.exists()
                        and previous.resolve().parent == args.output.resolve()
                        and previous.resolve() not in (checkpoint.resolve(), best_path.resolve())
                    ):
                        previous.unlink()
                last = checkpoint
                print(json.dumps({"role": role, **history[-1]}), flush=True)
                if stale >= args.patience:
                    break
            report["models"][role]["status"] = "complete"
            report["training_performed"] = True
            write_json(report_path, report)
            del model, optimizer, scaler
            torch.cuda.empty_cache()
        report.update(status="complete", completed_at=timestamp())
        write_json(report_path, report)
        make_runtime(args.runtime, args.output)
    except BaseException as exc:
        report.update(
            status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
            error=str(exc),
            updated_at=timestamp(),
        )
        write_json(report_path, report)
        raise


def train(args):
    """Start veldtraining onder een exclusieve bestandslock zodat geen tweede schrijver dezelfde uitvoer
    kan wijzigen.
    """
    from filelock import FileLock

    args.output.mkdir(parents=True, exist_ok=True)
    with FileLock(str(args.output / ".training.lock"), timeout=0):
        _train(args)


def make_runtime(base_path, output):
    """Maak een runtimeprofiel voor de werkelijk getrainde veldgewichten met hun bronmodellen en
    trainingsrapporthashes.
    """
    runtime = read_json(base_path)
    report_path = (output / "training-report.json").resolve()
    report = read_json(report_path)
    if report["status"] != "complete":
        raise ValueError("Both networks must finish before model registration")
    for role, key in (("keypoints", "weights_keypoints"), ("lines", "weights_lines")):
        model = report["models"][role]
        if model.get("selected_epoch") == 0:
            # Training ran, but this network did not beat its unmodified baseline.
            continue
        runtime[key] = model["path"]
        runtime["models"][role] = {
            "kind": "finetuned",
            "name": f"local-{role}-{report['identity'][:12]}",
            "path": model["path"],
            "sha256": model["sha256"],
            "base_model": RELEASE_WEIGHTS[role],
            "dataset_fingerprint": report["dataset_fingerprint"],
            "dataset_version": report["dataset_version"],
            "training_report": str(report_path),
            "training_report_sha256": sha256_file(report_path),
            "is_smoke_test": report["is_smoke_test"],
        }
    runtime["schema_version"] = 2
    runtime["automatic_promotion"] = False
    validate_runtime_models(runtime)
    write_json(output / "field-runtime.json", runtime)


def image_observation(models, image, device, *, amp=False):
    """Voer punten- en lijninferentie uit op één beeld en zet de netwerkcoördinaten terug naar de
    oorspronkelijke beeldafmetingen.
    """
    import cv2
    import torch
    import torchvision.transforms.functional as tf
    from utils.utils_heatmap import (
        coords_to_dict,
        get_keypoints_from_heatmap_batch_maxpool,
        get_keypoints_from_heatmap_batch_maxpool_l,
    )

    height, width = image.shape[:2]
    tensor = tf.resize(tf.to_tensor(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)), [540, 960], antialias=True)
    with torch.inference_mode(), torch.autocast("cuda", enabled=amp):
        kp = coords_to_dict(
            get_keypoints_from_heatmap_batch_maxpool(models[0](tensor[None].to(device))[:, :-1]),
            threshold=float("-inf"),
            ground_plane_only=True,
        )[0]
        ln = coords_to_dict(
            get_keypoints_from_heatmap_batch_maxpool_l(models[1](tensor[None].to(device))[:, :-1]),
            threshold=float("-inf"),
            ground_plane_only=True,
        )[0]
    return {
        "image_size": [width, height],
        "points": [
            {
                "id": k,
                "x": p["x"] * width / 960,
                "y": p["y"] * height / 540,
                "confidence": min(1.0, max(0.0, p["p"])),
                "raw_score": p["p"],
            }
            for k, p in kp.items()
            if k in POINTS_UV
        ],
        "lines": [
            {
                "id": k,
                "xy": [
                    [p["x_1"] * width / 960, p["y_1"] * height / 540],
                    [p["x_2"] * width / 960, p["y_2"] * height / 540],
                ],
                "confidence": min(1.0, max(0.0, min(p["p_1"], p["p_2"]))),
                "raw_scores": [p["p_1"], p["p_2"]],
            }
            for k, p in ln.items()
            if k in LINES_UV
        ],
    }


def _propose(args):
    """Bereken veldlabelvoorstellen voor de geselecteerde corpusframes en bewaar die los van gereviewde
    annotaties.
    """
    import cv2
    import torch

    from .field_data import CorpusBudget

    runtime = upstream_runtime(args.runtime)
    torch.set_num_threads(4)
    models = [load_model(runtime, r, "cuda:0").eval() for r in ("keypoints", "lines")]
    budget = CorpusBudget(args.root)
    budget.start_tracking()
    for manifest_path in sorted((args.root / "frames").glob("*/manifest.json")):
        manifest = read_json(manifest_path)
        output = manifest_path.parent / "proposals"
        output.mkdir(exist_ok=True)
        for frame in manifest["frames"]:
            target = output / (Path(frame["image"]).stem + ".json")
            image_path = manifest_path.parent / frame["image"]
            if sha256_file(image_path) != frame["sha256"]:
                raise ValueError("Proposal image hash mismatch")
            legacy_identity = digest_json({"image": frame["sha256"], "models": runtime["models"]})
            identity = digest_json(
                {"image": frame["sha256"], "models": runtime["models"], "precision": "amp_fp16"}
            )
            if target.exists():
                if read_json(target)["identity"] not in (identity, legacy_identity):
                    raise ValueError("Existing proposals belong to another image/model")
                continue
            observation = image_observation(models, cv2.imread(str(image_path)), "cuda:0", amp=True)
            result = {
                "identity": identity,
                "image_sha256": frame["sha256"],
                "models": runtime["models"],
                "observation": observation,
                "label_status": "model_proposal_unreviewed",
                "training_eligible": False,
                "human_reviewed": False,
                "precision": "amp_fp16",
            }
            budget.require(len(json.dumps(result).encode()) + 4096)
            budget.write_json(target, result)
        print(f"Proposals complete: {manifest_path.parent.name}", flush=True)


def propose(args):
    """Beveilig het schrijven van nieuwe veldvoorstellen met een exclusieve corpuslock."""
    from filelock import FileLock

    with FileLock(str(args.root / ".writer.lock")):
        _propose(args)


def reprojection_metrics(observation, labels, settings, *, state=None):
    """Bereken een kandidaatkalibratie en vergelijk haar projectie met de bekende veldlabels; retourneer
    geldigheid en pixelafwijkingen.
    """
    from sn_calibration.src.soccerpitch import SoccerPitch

    from .field_motion import estimate_checked

    if state is None:
        state = estimate_checked(observation, observation["image_size"], settings)
    if state["status"] != "valid":
        return {"valid": False, "errors_px": [], "wrong": False}
    inverse = np.linalg.inv(np.asarray(state["homography"]))
    width, height = observation["image_size"]
    pitch = SoccerPitch()
    errors = []
    for name, points in labels.items():
        if name not in pitch.line_extremities or "Goal" in name or "Circle" in name or len(points) < 2:
            continue
        ends = np.asarray(pitch.line_extremities[name])
        uv = (ends[:, :2] + [52.5, 34]) / [105, 68]
        projected = np.column_stack((uv, np.ones(2))) @ inverse.T
        coefficients = np.cross(projected[0], projected[1])
        length = np.hypot(*coefficients[:2])
        if length < 1e-6:
            continue
        for point in points:
            xy = [point["x"] * width, point["y"] * height, 1]
            errors.append(float(abs(np.dot(xy, coefficients)) / length))
    return {
        "valid": True,
        "errors_px": errors,
        "wrong": bool(errors and max(errors) > np.hypot(width, height) * 0.01),
    }


def _compare(args):
    """Meet baseline en kandidaat op dezelfde veldbeelden en schrijf de vergelijking met de herkomst van
    beide gewichtssets.
    """
    import cv2
    import torch

    from .automatic_calibration import prepare_automatic_calibration
    from .field_motion import DEFAULT_SETTINGS, CameraCalibration
    from .video import inspect_video

    args.output.mkdir(parents=True, exist_ok=True)
    index = dataset_index(args.dataset, {"valid": args.limit_valid}, splits=("valid",))
    rows = [r for r in index["frames"] if r["split"] == "valid"]
    # Evenly spaced validation selection fixed before either network is evaluated.
    if args.limit_valid and args.limit_valid < len(rows):
        rows = [rows[i] for i in np.linspace(0, len(rows) - 1, args.limit_valid, dtype=int)]
    selection = [{"image": r["image"], "sha256": r["image_sha256"]} for r in rows]
    selection_path = args.output / "selection.json"
    if selection_path.exists() and json.loads(selection_path.read_text(encoding="utf-8")) != selection:
        raise ValueError("Comparison selection changed; use a new output")
    write_json(selection_path, selection)
    result = {
        "status": "running",
        "settings": DEFAULT_SETTINGS,
        "validation_selection": selection,
        "pretraining_overlap": True,
        "independent_accuracy_claim": False,
        "models": {},
        "human_broadcast_reference": "pending",
        "promoted": False,
    }
    torch.set_num_threads(4)
    for name, runtime_path in (("baseline", args.runtime), ("candidate", args.candidate)):
        runtime = upstream_runtime(runtime_path)
        models = [load_model(runtime, r, "cuda:0").eval() for r in ("keypoints", "lines")]
        metrics = []
        for row in rows:
            observation = image_observation(models, cv2.imread(row["image"]), "cuda:0")
            metrics.append(reprojection_metrics(observation, labels_for_row(row), DEFAULT_SETTINGS))
        errors = [e for m in metrics for e in m["errors_px"]]
        result["models"][name] = {
            "models": runtime["models"],
            "validation_frames": len(rows),
            "valid_frames": sum(m["valid"] for m in metrics),
            "wrong_calibrations": sum(m["wrong"] for m in metrics),
            "reprojection_median_px": float(np.median(errors)) if errors else None,
            "reprojection_p95_px": float(np.percentile(errors, 95)) if errors else None,
            "unscored_valid_frames": sum(m["valid"] and not m["errors_px"] for m in metrics),
        }
        del models
        torch.cuda.empty_cache()
        if args.video:
            bundle = prepare_automatic_calibration(
                args.video,
                runtime_path,
                args.output / (name + "-bundles"),
                source="User supplied Broadcast development clip",
                usage="Local development and comparison",
            )
            video = inspect_video(args.video)
            estimator = CameraCalibration(video.fps, DEFAULT_SETTINGS)
            states = []
            cap = cv2.VideoCapture(str(args.video))
            try:
                with Path(bundle.observations_path).open() as stream:
                    for line in stream:
                        ok, frame = cap.read()
                        if not ok:
                            raise ValueError("Broadcast decode ended early")
                        obs = json.loads(line)
                        from .field_motion import estimate_checked

                        direct = estimate_checked(obs, video.size, DEFAULT_SETTINGS)
                        states.append(estimator.update(frame, direct, obs["frame_index"]))
            finally:
                cap.release()
            longest, current = 0, 0
            for state in states:
                current = current + 1 if state["status"] != "valid" else 0
                longest = max(longest, current)
            result["models"][name]["broadcast"] = {
                "frames": len(states),
                "coverage": sum(s["status"] == "valid" for s in states) / len(states),
                "longest_failure_s": longest / video.fps,
                "human_reprojection_error": None,
                "wrong_calibrations": None,
                "development_clip": True,
            }
        write_json(args.output / "comparison.json", result)
    result["status"] = "complete"
    write_json(args.output / "comparison.json", result)
    lines = [
        "# Veldmodelvergelijking",
        "",
        "SoccerNet-validatie overlapt met de voortraining. Dit is geen onafhankelijke eindtest.",
        "",
        "| Model | Geldige frames | Mediane lijnfout (px) | Kalibraties boven 1% fout |",
        "|---|---:|---:|---:|",
    ]
    broadcast_notes = []
    for name, model in result["models"].items():
        median = model["reprojection_median_px"]
        lines.append(
            f"| {name} | {model['valid_frames']}/{model['validation_frames']} | "
            f"{median if median is not None else 'onbekend'} | {model['wrong_calibrations']} |"
        )
        broadcast = model.get("broadcast")
        if broadcast:
            broadcast_notes += [
                "",
                f"{name}: Broadcast-dekking {broadcast['coverage']:.1%}; "
                f"langste uitval {broadcast['longest_failure_s']:.2f} s.",
            ]
    lines += broadcast_notes
    if any(m.get("is_smoke_test") for m in result["models"]["candidate"]["models"].values()):
        lines += ["", "De kandidaat is een smoketest met één trainingsstap per netwerk."]
    lines += [
        "",
        "Menselijke Broadcast-projectiefouten en foutieve kalibraties blijven onbekend.",
        "Er is geen model automatisch als standaard ingesteld.",
    ]
    (args.output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result["models"], indent=2), flush=True)


def compare(args):
    """Voer de veldvergelijking uit onder een eigen lock op de uitvoermap."""
    from filelock import FileLock

    args.output.mkdir(parents=True, exist_ok=True)
    with FileLock(str(args.output / ".comparison.lock"), timeout=0):
        _compare(args)


def main():
    """Parse het veldcommando en start de aangevraagde training, datasetindexering, runtimebouw,
    voorstellen of vergelijking.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["index", "train", "propose", "compare"])
    parser.add_argument("--runtime", type=Path, default=Path(".tools/field-runtime.json"))
    parser.add_argument("--dataset", type=Path, default=Path("data/field-corpus/soccernet"))
    parser.add_argument("--root", type=Path, default=Path("data/field-corpus"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/field-training"))
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--video", type=Path)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--lr", type=float, default=0.0001)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--weight-decay", type=float, default=0.0001)
    parser.add_argument(
        "--head-only",
        action="store_true",
        help="Freeze pretrained features and their normalization statistics",
    )
    parser.add_argument("--limit-train", type=int)
    parser.add_argument("--limit-valid", type=int)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if (
        not math.isfinite(args.lr)
        or args.lr <= 0
        or args.patience < 1
        or not math.isfinite(args.weight_decay)
        or args.weight_decay < 0
    ):
        parser.error(
            "Learning rate and patience must be positive; weight decay must be finite and nonnegative"
        )
    if args.epochs < 1 or any(
        value is not None and value < 1 for value in (args.limit_train, args.limit_valid)
    ):
        parser.error("Epochs and optional sample limits must be positive")
    if args.command == "train":
        train(args)
    elif args.command == "index":
        result = dataset_index(args.dataset)
        args.output.mkdir(parents=True, exist_ok=True)
        write_json(args.output / "dataset-index.json", result)
        print(json.dumps({"frames": len(result["frames"]), "excluded": len(result["excluded"])}))
    elif args.command == "propose":
        propose(args)
    elif args.command == "compare":
        if not args.candidate:
            parser.error("--candidate required")
        compare(args)


if __name__ == "__main__":
    main()
