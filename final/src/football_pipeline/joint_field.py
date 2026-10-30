"""Bounded output-layer training over the audited local field corpus."""

from __future__ import annotations

import argparse
import gc
import random
import time
from pathlib import Path

import numpy as np

from .contracts import digest_json, read_json, sha256_file, write_json
from .training_budget import TrainingBudget


def train(dataset, runtime_path, output, minutes=90):
    import torch
    from torch.utils.data import DataLoader

    from .field_learning import (
        FieldDataset,
        atomic_torch_save,
        load_model,
        make_runtime,
        run_epoch,
        upstream_runtime,
    )

    output.mkdir(parents=True, exist_ok=False)
    index = read_json(dataset / "index.json")
    runtime = upstream_runtime(runtime_path)
    train_rows = [r for r in index["frames"] if r["split"] == "train"]
    valid_rows = [r for r in index["frames"] if r["image"] in set(index["validation_images"])]
    report = {
        "status": "running",
        "dataset_fingerprint": index["fingerprint"],
        "dataset_version": index.get("dataset_version", "joint-local-v2"),
        "is_smoke_test": False,
        "training_performed": False,
        "independent_accuracy_claim": False,
        "validation_selection": index["validation_images"],
        "models": {},
        "config": {
            "head_only": True,
            "epochs": 8,
            "batch": 1,
            "lr": 0.0001,
            "weight_decay": 0.0001,
            "seed": 42,
            "minutes": minutes,
        },
        "trainer_sha256": sha256_file(__file__),
    }
    report["identity"] = digest_json(report)
    write_json(output / "training-report.json", report)
    torch.set_num_threads(4)
    device = torch.device("cuda:0")
    start = time.monotonic()
    for role in ("keypoints", "lines"):
        budget = TrainingBudget(minutes / 2)
        torch.manual_seed(42)
        random.seed(42)
        np.random.seed(42)
        model = load_model(runtime, role, device)
        head_ids = {id(p) for p in model.head[0][3].parameters()}
        for p in model.parameters():
            p.requires_grad_(id(p) in head_ids)
        parameters = [p for p in model.parameters() if p.requires_grad]
        optimizer = torch.optim.Adam(parameters, lr=0.0001, weight_decay=0.0001)
        scaler = torch.cuda.amp.GradScaler()
        training = DataLoader(
            FieldDataset(train_rows, role, augment=True), batch_size=1, shuffle=True, num_workers=0
        )
        validation = DataLoader(FieldDataset(valid_rows, role), batch_size=1, num_workers=0)
        baseline = run_epoch(model, validation, device)
        best, selected, history, stale = baseline, 0, [], 0
        budget_stop = False
        best_path = output / f"{role}-best-000.pt"
        atomic_torch_save(model.state_dict(), best_path)
        for epoch in range(1, 9):
            if budget.expired:
                break
            progress = {}
            tick = time.monotonic()
            try:
                loss = run_epoch(
                    model,
                    training,
                    device,
                    optimizer,
                    scaler,
                    frozen_features=True,
                    deadline=budget.deadline - 90,
                    progress=progress,
                    progress_callback=lambda samples: write_json(
                        output / "progress.json",
                        {
                            "role": role,
                            "epoch": epoch,
                            "samples": samples,
                            "total_samples": len(train_rows),
                            "remaining_minutes": max(0, (budget.deadline - budget.clock()) / 60),
                        },
                    ),
                )
            except TimeoutError:
                budget_stop = True
                break
            validation_loss = run_epoch(model, validation, device)
            if validation_loss < best:
                best, selected = validation_loss, epoch
                stale = 0
                best_path = output / f"{role}-best-{epoch:03d}.pt"
                atomic_torch_save(model.state_dict(), best_path)
            else:
                stale += 1
            atomic_torch_save(
                {
                    "model": model.state_dict(),
                    "optimizer": optimizer.state_dict(),
                    "scaler": scaler.state_dict(),
                    "epoch": epoch,
                    "identity": report["identity"],
                },
                output / f"{role}-last.pt",
            )
            history.append(
                {
                    "epoch": epoch,
                    "train_loss": loss,
                    "valid_loss": validation_loss,
                    "training_samples": progress.get("samples", 0),
                    "epoch_complete": progress.get("samples", 0) == len(train_rows),
                    "runtime_s": time.monotonic() - tick,
                }
            )
            budget_stop |= progress.get("samples", 0) < len(train_rows)
            report["models"][role] = {
                "status": "running",
                "path": str(best_path.resolve()),
                "sha256": sha256_file(best_path),
                "selected_epoch": selected,
                "history": history,
                "baseline_valid_loss": baseline,
                "best_valid_loss": best,
                "train_frames": len(train_rows),
                "valid_frames": len(valid_rows),
                "completion_reason": "training",
            }
            write_json(output / "training-report.json", report)
            print(role, history[-1], flush=True)
            if stale >= 3:
                break
        report["models"][role] = {
            "status": "complete",
            "path": str(best_path.resolve()),
            "sha256": sha256_file(best_path),
            "selected_epoch": selected,
            "history": history,
            "baseline_valid_loss": baseline,
            "best_valid_loss": best,
            "train_frames": len(train_rows),
            "valid_frames": len(valid_rows),
            "completion_reason": "time_limited" if budget.expired or budget_stop else "epochs_or_early_stop",
            "runtime_s": budget.clock() - budget.started,
        }
        report["training_performed"] |= bool(history)
        write_json(output / "training-report.json", report)
        del model, optimizer, scaler, training, validation
        gc.collect()
        torch.cuda.empty_cache()
    report.update(status="complete", runtime_s=time.monotonic() - start)
    write_json(output / "training-report.json", report)
    make_runtime(runtime_path, output)
    candidate = compare_trained_checkpoints(dataset, runtime_path, output)
    import shutil

    shutil.copy2(candidate / "field-runtime.json", output / "field-runtime.json")
    shutil.copy2(candidate / "comparison.json", output / "comparison.json")


def compare_trained_checkpoints(dataset, runtime_path, training):
    """Measure trained weights even when baseline wins heatmap-loss selection."""
    import copy

    import torch

    from .field_learning import atomic_torch_save, make_runtime

    source = training / "training-report.json"
    report = read_json(source)
    if report["status"] != "complete":
        raise ValueError("Field training must finish before checkpoint comparison")
    output = training / "trained-candidate"
    if (output / "comparison.json").exists():
        saved = read_json(output / "training-report.json")
        if saved["parent_report_sha256"] != sha256_file(source):
            raise ValueError("Field checkpoint comparison inputs changed")
        if read_json(output / "comparison.json")["status"] == "complete":
            return output
    output.mkdir(parents=True, exist_ok=True)
    report = copy.deepcopy(report)
    report["parent_report_sha256"] = sha256_file(source)
    report["checkpoint_policy"] = (
        "Best trained checkpoint; when baseline wins loss selection, compare the saved final trained checkpoint geometrically. No activation based on training loss."
    )
    for role, record in report["models"].items():
        if record["selected_epoch"] == 0 and record["history"]:
            last = training / f"{role}-last.pt"
            state = torch.load(last, map_location="cpu", weights_only=True)
            if state["identity"] != report["identity"] or state["epoch"] != record["history"][-1]["epoch"]:
                raise ValueError("Field checkpoint identity or epoch changed")
            path = output / f"{role}-trained-final.pt"
            atomic_torch_save(state["model"], path)
            record.update(
                path=str(path.resolve()),
                sha256=sha256_file(path),
                selected_epoch=state["epoch"],
                best_valid_loss=record["history"][-1]["valid_loss"],
                source_checkpoint_sha256=sha256_file(last),
                checkpoint_selection="final trained checkpoint for geometric comparison; baseline had lower heatmap loss",
            )
            del state
    write_json(output / "training-report.json", report)
    make_runtime(runtime_path, output)
    compare(
        read_json(dataset / "index.json"),
        runtime_path,
        output / "field-runtime.json",
        output / "comparison.json",
    )
    return output


def compare(index, baseline, candidate, output):
    import cv2
    import torch

    from .field_learning import (
        image_observation,
        labels_for_row,
        load_model,
        reprojection_metrics,
        upstream_runtime,
    )
    from .field_motion import DEFAULT_SETTINGS

    rows = [r for r in index["frames"] if r["image"] in set(index["validation_images"])]
    report = {
        "status": "running",
        "selection": index["validation_images"],
        "pretraining_overlap": True,
        "independent_accuracy_claim": False,
        "models": {},
    }
    for name, path in (("baseline", baseline), ("candidate", candidate)):
        runtime = upstream_runtime(path)
        models = [load_model(runtime, r, "cuda:0").eval() for r in ("keypoints", "lines")]
        metrics = [
            reprojection_metrics(
                image_observation(models, cv2.imread(r["image"]), "cuda:0"),
                labels_for_row(r),
                DEFAULT_SETTINGS,
            )
            for r in rows
        ]
        errors = [v for m in metrics for v in m["errors_px"]]
        report["models"][name] = {
            "frames": len(rows),
            "valid_frames": sum(m["valid"] for m in metrics),
            "wrong_calibrations": sum(m["wrong"] for m in metrics),
            "unscored_valid_frames": sum(m["valid"] and not m["errors_px"] for m in metrics),
            "median_error_px": float(np.median(errors)) if errors else None,
            "per_frame": metrics,
        }
        del models
        gc.collect()
        torch.cuda.empty_cache()
        write_json(output, report)
    report["status"] = "complete"
    write_json(output, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minutes", type=float, default=90)
    args = parser.parse_args()
    train(args.dataset, args.runtime, args.output, args.minutes)
