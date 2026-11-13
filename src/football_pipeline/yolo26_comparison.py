"""Train and compare isolated YOLO11/26 player candidates with resumable quota pauses."""

from __future__ import annotations

import argparse
import copy
import gc
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from .contracts import atomic_replace, digest_json, read_json, sha256_file, write_json
from .video import ROOT

DEFAULT_OUTPUT = ROOT / "artifacts/yolo26-players-20261113-v1"
DATASET = ROOT / "data/broadcast-multisource-v1"
BASE_PROFILE = ROOT / "configs/models-broadcast.json"
MODELS = ("yolo26s", "yolo11s")
TRAIN_CONFIG = {
    "epochs": 100,
    "patience": 20,
    "seed": 42,
    "imgsz": 1536,
    "batch": 1,
    "optimizer": "AdamW",
    "lr0": 0.001,
    "cos_lr": True,
    "warmup_epochs": 3.0,
    "amp": True,
    "workers": 0,
    "rect": True,
    "deterministic": True,
    "cache": False,
    "nms": True,
}


class ExperimentPaused(RuntimeError):
    """A safe pause with no new experiment phase permitted."""


def configure_environment():
    """Keep model caches and settings local and disable external training integrations."""
    os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / ".cache/yolo26-settings"))
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
    os.environ.setdefault("YOLO_AUTOINSTALL", "false")
    os.environ.setdefault("WANDB_DISABLED", "true")
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    os.environ.setdefault("MKL_NUM_THREADS", "4")


def usage_guard(output, *, starting=False, now=None):
    """Require a fresh account snapshot; reserve ten percent before starting long phases."""
    if (output / "pause.request").exists():
        raise ExperimentPaused("Explicit safe-pause request")
    path = output / "usage.json"
    if not path.exists():
        raise ExperimentPaused("Account usage unavailable; refresh usage.json before resuming")
    usage = read_json(path)
    age = (time.time() if now is None else now) - usage.get("checked_at", 0)
    remaining = usage.get("remaining_percent")
    if age > 900 or age < -60 or remaining is None or not 0 <= remaining <= 100:
        raise ExperimentPaused("Account usage unavailable or older than fifteen minutes")
    if remaining <= (10 if starting else 5):
        raise ExperimentPaused(f"Account remaining {remaining}%; safe-pause threshold reached")
    return usage


def validate_dataset(source):
    """Verify every source hash and reject test access, split leakage and invalid player labels."""
    manifest = read_json(source / "manifest.json")
    games, images, files = {}, {}, set()
    counts = Counter()
    for row in manifest["frames"]:
        split = row["split"]
        if split not in {"train", "val"}:
            raise ValueError("Reserved test data must not be opened")
        for seen, key in ((games, row["game_id"]), (images, row["image_sha256"])):
            if key in seen and seen[key] != split:
                raise ValueError("Match or image crosses training and validation splits")
            seen[key] = split
        for key in ("image", "label"):
            path = Path(row[key])
            if not path.is_absolute():
                path = source / path
            if not path.is_file() or sha256_file(path) != row[key + "_sha256"]:
                raise ValueError(f"Changed or missing dataset source: {path}")
            if key == "image":
                if str(path.resolve()) in files:
                    raise ValueError("Duplicate image entry")
                files.add(str(path.resolve()))
            else:
                for line in path.read_text().splitlines():
                    values = [float(v) for v in line.split()]
                    if len(values) != 5 or values[0] != 0 or not all(0 <= v <= 1 for v in values[1:]):
                        raise ValueError(f"Invalid player label: {path}")
                    if values[3] <= 0 or values[4] <= 0:
                        raise ValueError(f"Empty player box: {path}")
        counts[split] += 1
    return {
        "manifest_sha256": sha256_file(source / "manifest.json"),
        "counts": dict(counts),
        "games": {s: sorted(str(g) for g, split in games.items() if split == s) for s in counts},
        "test_accessed": False,
    }


def candidate_profile(baseline, weights, model_id):
    """Replace exactly one player supplier while preserving all other model components."""
    result = copy.deepcopy(baseline)
    suppliers = [m for m in result["models"] if "player" in m["class_mapping"].values()]
    if len(suppliers) != 1:
        raise ValueError("Comparison requires exactly one player detector")
    suppliers[0].update(
        model_id=model_id,
        weights=str(Path(weights).resolve()),
        weights_sha256=sha256_file(weights),
        class_mapping={"0": "player"},
        expected_names={"0": "player"},
    )
    result["profile_name"] = f"Player comparison · {model_id} · development only"
    result["handoff"] = {"activated": False, "independent_final_test_completed": False}
    return result


def prepare(output):
    """Freeze validated data, component identities, package versions and comparison configuration."""
    from .detection import load_model_manifest

    output.mkdir(parents=True, exist_ok=True)
    usage_guard(output, starting=True)
    verified = validate_dataset(DATASET)
    if verified["counts"] != {"train": 3936, "val": 348}:
        raise ValueError("Expected the agreed 3936 train / 348 validation images")
    baseline = load_model_manifest(BASE_PROFILE)
    packages = {
        name: importlib.metadata.version(name)
        for name in ("ultralytics", "torch", "torchvision", "ultralytics-thop", "ultralytics-platform")
    }
    if packages["ultralytics"] != "8.4.211":
        raise ValueError("Use the isolated Ultralytics 8.4.211 environment")
    identity = {
        "data": verified,
        "baseline": baseline,
        "training": TRAIN_CONFIG,
        "packages": packages,
        "source_video": str(max((ROOT / "data/uploads").glob("*.mp4"), key=lambda p: p.stat().st_mtime)),
        "python": sys.executable,
    }
    existing = output / "experiment.json"
    if existing.exists():
        old = read_json(existing)
        if digest_json(old) != digest_json(identity):
            raise ValueError("Frozen inputs changed; use a new experiment directory")
    else:
        write_json(existing, identity)
        write_json(output / "current-profile.json", baseline)
        subprocess.run(
            [sys.executable, "-m", "pip", "freeze"], check=True, stdout=(output / "packages.txt").open("w")
        )
    (output / "dataset").mkdir(exist_ok=True)
    import yaml

    (output / "dataset/data.yaml").write_text(
        yaml.safe_dump(
            {"path": str(DATASET), "train": "images/train", "val": "images/val", "names": {0: "player"}}
        ),
        encoding="utf-8",
    )
    handoff(output)
    return identity


def checkpoint_saved(trainer, output, directory, identity):
    """Copy a full optimizer checkpoint before native finalization strips training state."""
    temporary = directory / "resume.pt.tmp"
    shutil.copyfile(trainer.last, temporary)
    atomic_replace(temporary, directory / "resume.pt")
    state = {
        "status": "running",
        "epoch": trainer.epoch + 1,
        "maximum_epochs": trainer.epochs,
        "dataset_identity": identity,
        "checkpoint": str(directory / "resume.pt"),
        "checkpoint_sha256": sha256_file(directory / "resume.pt"),
        "best": str(trainer.best),
        "metrics": {k: float(v) for k, v in trainer.metrics.items()},
        "updated_at": time.time(),
    }
    write_json(directory / "status.json", state)
    print(json.dumps(state), flush=True)
    usage_guard(output)


def loss_values(value):
    """Serialize both tensor losses and YOLO26's separate one-to-many/one-to-one loss dictionary."""
    if isinstance(value, dict):
        return {key: loss_values(item) for key, item in value.items()}
    return value.detach().cpu().tolist() if hasattr(value, "detach") else value


def train_one(output, model_name):
    """Train one candidate, preserving epoch checkpoints and explicit pause/failure status."""
    import torch
    from ultralytics import YOLO

    usage_guard(output, starting=True)
    experiment = read_json(output / "experiment.json")
    if sha256_file(DATASET / "manifest.json") != experiment["data"]["manifest_sha256"]:
        raise ValueError("Dataset manifest changed since preparation")
    resolution = (
        read_json(output / "resolution.json")["imgsz"] if (output / "resolution.json").exists() else 1536
    )
    directory = output / f"{resolution}/{model_name}"
    directory.mkdir(parents=True, exist_ok=True)
    status = read_json(directory / "status.json") if (directory / "status.json").exists() else {}
    if status.get("status") == "complete":
        if sha256_file(status["best"]) != status["best_sha256"]:
            raise ValueError("Completed candidate weights changed")
        return
    identity = digest_json([experiment["data"], TRAIN_CONFIG, resolution, model_name])
    resume = directory / "resume.pt"
    if resume.exists():
        if status.get("dataset_identity") != identity or sha256_file(resume) != status.get(
            "checkpoint_sha256"
        ):
            raise ValueError("Resume checkpoint identity differs")
        saved = torch.load(resume, map_location="cpu", weights_only=False)
        if saved.get("optimizer") is None or saved["epoch"] + 1 != status["epoch"]:
            raise ValueError("Resume checkpoint has no valid optimizer or epoch")
        del saved
        model = YOLO(str(resume))
    else:
        initial = output / f"{model_name}.pt"
        model = YOLO(str(initial))
        write_json(directory / "base.json", {"weights": str(initial), "sha256": sha256_file(initial)})
    write_json(directory / "status.json", {**status, "status": "starting", "dataset_identity": identity})

    def on_save(trainer):
        """Persist optimizer state and honor quota pauses only after a completed epoch."""
        checkpoint_saved(trainer, output, directory, identity)

    def on_batch(trainer):
        """Expose batch-level progress without interrupting an epoch before a safe checkpoint."""
        if getattr(trainer, "comparison_progress_epoch", -1) != trainer.epoch:
            trainer.comparison_progress_epoch = trainer.epoch
            trainer.comparison_batches = 0
        trainer.comparison_batches += 1
        now = time.time()
        if now - getattr(trainer, "comparison_last_progress", 0) >= 30:
            trainer.comparison_last_progress = now
            write_json(
                directory / "progress.json",
                {
                    "epoch": trainer.epoch + 1,
                    "batch": trainer.comparison_batches,
                    "batches_per_epoch": len(trainer.train_loader),
                    "updated_at": now,
                    "loss": loss_values(trainer.tloss),
                },
            )

    model.add_callback("on_model_save", on_save)
    model.add_callback("on_train_batch_end", on_batch)
    try:
        config = {**TRAIN_CONFIG, "imgsz": resolution}
        if resume.exists():
            model.train(resume=True, device=0, workers=0)
        else:
            model.train(
                data=str(output / "dataset/data.yaml"),
                project=str(directory),
                name="training",
                device=0,
                **config,
            )
        if model.names != {0: "player"}:
            raise ValueError("Candidate classes differ from the player-only contract")
        state = read_json(directory / "status.json")
        best = Path(state["best"])
        state.update(status="complete", best=str(best), best_sha256=sha256_file(best))
        write_json(directory / "status.json", state)
        write_json(
            output / f"{model_name}-profile.json", candidate_profile(experiment["baseline"], best, model_name)
        )
    except ExperimentPaused as exc:
        state = read_json(directory / "status.json")
        state.update(status="paused", reason=str(exc))
        write_json(directory / "status.json", state)
        raise
    except Exception as exc:
        state = read_json(directory / "status.json")
        oom = "out of memory" in str(exc).lower()
        state.update(status="out_of_memory" if oom else "failed", error=str(exc))
        write_json(directory / "status.json", state)
        raise
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
        handoff(output)


def train_all(output):
    """Train candidates sequentially and restart both at lower resolution after confirmed OOM."""
    if validate_dataset(DATASET) != read_json(output / "experiment.json")["data"]:
        raise ValueError("Training sources differ from the frozen experiment")
    for model_name in MODELS:
        try:
            train_one(output, model_name)
        except RuntimeError as exc:
            if "out of memory" not in str(exc).lower():
                raise
            if (output / "resolution.json").exists():
                raise RuntimeError(
                    "Batch 1 at 1280 does not fit; do not change the comparison silently"
                ) from exc
            write_json(output / "resolution.json", {"imgsz": 1280, "reason": str(exc)})
            for candidate in MODELS:
                train_one(output, candidate)
            break


def summary_scores(metrics):
    """Return precision, recall, balanced F1 and the two box AP measures."""
    row = metrics["per_class"][0]
    precision, recall = row["precision"], row["recall"] or 0.0
    return {
        "precision": precision,
        "recall": recall,
        "F1": 2 * precision * recall / max(precision + recall, 1e-12),
        "AP50": row["AP50"],
        "AP50_95": row["AP50_95"],
    }


def profiles(output):
    """Return all three frozen comparison profiles, rejecting incomplete candidates."""
    result = {"current": output / "current-profile.json"}
    result.update({name: output / f"{name}-profile.json" for name in MODELS})
    for path in result.values():
        if not path.exists():
            raise ValueError(f"Candidate not ready: {path}")
    return result


def evaluate_detector(output, name, profile):
    """Measure player-only predictions with the same AP and fixed-workpoint matching for all models."""
    import cv2
    import torch
    from ultralytics import YOLO

    from persoon1.metrics import evaluate

    usage_guard(output, starting=True)
    target = output / "evaluation" / name
    target.mkdir(parents=True, exist_ok=True)
    profile_value = read_json(profile)
    spec = next(m for m in profile_value["models"] if "player" in m["class_mapping"].values())
    rows = [r for r in read_json(DATASET / "manifest.json")["frames"] if r["split"] == "val"]
    identity = digest_json([spec, sha256_file(DATASET / "manifest.json"), 1920, 0.001, 0.7])
    cache_path = target / "raw-predictions.json"
    cache = read_json(cache_path) if cache_path.exists() else {"identity": identity, "predictions": {}}
    if cache["identity"] != identity:
        raise ValueError("Evaluation inputs changed")
    predictions = cache["predictions"]
    model = YOLO(spec["weights"])
    try:
        for number, row in enumerate(rows):
            fid = row["frame_id"]
            if fid in predictions:
                continue
            result = model.predict(
                row["image"], imgsz=1920, conf=0.001, iou=0.7, classes=[0], device=0, nms=True, verbose=False
            )[0]
            if getattr(model.predictor.model, "end2end", False):
                raise ValueError("Comparison requires the NMS/one-to-many inference head")
            predictions[fid] = [
                {"class_id": 0, "bbox_xyxy": box[:4], "confidence": box[4]}
                for box in result.boxes.data.cpu().tolist()
            ]
            if number % 25 == 0:
                write_json(cache_path, cache)
                usage_guard(output)
        write_json(cache_path, cache)
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
    truths = {r["frame_id"]: r["boxes"] for r in rows}
    metrics = evaluate(truths, predictions, ["player"], confidence=0.25, match_iou=0.5)
    per_game = {}
    for game in sorted({r["game_id"] for r in rows}):
        keys = [r["frame_id"] for r in rows if r["game_id"] == game]
        per_game[game] = summary_scores(
            evaluate({k: truths[k] for k in keys}, {k: predictions[k] for k in keys}, ["player"])
        )
    errors = metrics.pop("errors")
    record = {
        "identity": identity,
        "overall": summary_scores(metrics),
        "per_game": per_game,
        "macro_F1": sum(v["F1"] for v in per_game.values()) / len(per_game),
        "metrics": metrics,
        "head": "one-to-many/NMS",
        "frames": len(rows),
    }
    write_json(target / "raw-metrics.json", record)
    write_json(target / "raw-errors.json", {"errors": errors})
    by_id = {r["frame_id"]: r for r in rows}
    for kind in ("FP", "FN"):
        for number, error in enumerate([e for e in errors if e["type"] == kind][:4]):
            row = by_id[error["frame_id"]]
            frame = cv2.imread(row["image"])
            for box in truths[row["frame_id"]]:
                x1, y1, x2, y2 = map(round, box["bbox_xyxy"])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (40, 220, 40), 2)
            for box in predictions[row["frame_id"]]:
                if box["confidence"] >= 0.25:
                    x1, y1, x2, y2 = map(round, box["bbox_xyxy"])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (30, 30, 230), 1)
            cv2.putText(
                frame,
                f"{name} {kind} | green: reference, red: prediction",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )
            cv2.imwrite(str(target / f"example-{kind}-{number}.jpg"), frame)
    return record


def benchmark(output, name, profile):
    """Time warmed batch-one GPU inference, including separate complete detector timings."""
    import cv2
    import numpy as np
    import torch
    from ultralytics import YOLO

    from .detection import UltralyticsDetector, load_model_manifest

    usage_guard(output, starting=True)
    directory = output / "evaluation" / name
    target = directory / "speed.json"
    if target.exists():
        return read_json(target)
    rows = sorted(
        (r for r in read_json(DATASET / "manifest.json")["frames"] if r["split"] == "val"),
        key=lambda r: (r["game_id"], r["clip"], r["frame_index"]),
    )
    selected = [rows[int(i)] for i in np.linspace(0, len(rows) - 1, 200)]
    frames = [cv2.imread(r["image"]) for r in selected]
    manifest = load_model_manifest(profile)
    spec = next(s for s in manifest["models"] if "player" in s["class_mapping"].values())
    results = {
        "frames": [r["frame_id"] for r in selected],
        "warmup": 30,
        "repetitions": 3,
        "imgsz": 1920,
        "batch": 1,
        "includes_decode": False,
        "automatic_field_included": False,
    }
    for mode in ("raw", "detector_stack"):
        usage_guard(output, starting=True)
        model = YOLO(spec["weights"]) if mode == "raw" else UltralyticsDetector(manifest)

        def infer(frame, index, active_model=model):
            """Use identical confidence and resolution when timing each model's production detector path."""
            if mode == "raw":
                return active_model.predict(
                    frame,
                    imgsz=1920,
                    conf=spec["confidence"],
                    iou=spec["iou"],
                    classes=[0],
                    device=0,
                    nms=True,
                    verbose=False,
                )
            return active_model.detect(frame, index)

        for index in range(30):
            infer(frames[index % len(frames)], index)
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        times, repetitions = [], []
        for repetition in range(3):
            usage_guard(output)
            current = []
            for index, frame in enumerate(frames):
                torch.cuda.synchronize()
                started = time.perf_counter()
                infer(frame, index)
                torch.cuda.synchronize()
                current.append((time.perf_counter() - started) * 1000)
            times.extend(current)
            repetitions.append(float(np.median(current)))
        results[mode] = {
            "median_ms": float(np.median(times)),
            "p95_ms": float(np.percentile(times, 95)),
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
            "repetition_medians_ms": repetitions,
            "includes_role_team_classification": False,
        }
        del infer, model
        gc.collect()
        torch.cuda.empty_cache()
    write_json(target, results)
    return results


def evaluate_all(output):
    """Run raw and fixed-component pipeline evaluations for all three checkpoints."""
    import torch

    from .broadcast_evaluation import evaluate_profile

    for name, profile in profiles(output).items():
        evaluate_detector(output, name, profile)
        usage_guard(output, starting=True)
        metrics = evaluate_profile(
            ROOT / "data/broadcast-pitch-v1",
            profile,
            ROOT / "configs/teams-broadcast.json",
            output / "evaluation" / name / "pipeline",
            confidence=0.25,
        )
        overall = summary_scores(metrics["player_detection_and_roles"])
        games = {r["game_id"]: summary_scores(r["players"]) for r in metrics["per_game"]}
        write_json(
            output / "evaluation" / name / "pipeline-summary.json",
            {
                "overall": overall,
                "per_game": games,
                "macro_F1": sum(v["F1"] for v in games.values()) / len(games),
                "reference_geometry_unavailable": metrics["reference_geometry_unavailable"],
            },
        )
        gc.collect()
        torch.cuda.empty_cache()
        benchmark(output, name, profile)
        handoff(output)


def videos(output):
    """Generate the same uploaded clip with each player candidate and unchanged field/ball settings."""
    from .pipeline import process_video

    source = read_json(output / "experiment.json")["source_video"]
    for name, profile in profiles(output).items():
        path = output / f"video-{name}.json"
        if path.exists():
            continue
        usage_guard(output, starting=True)
        result = process_video(
            source,
            None,
            profile,
            ROOT / "runs",
            field_runtime_path=ROOT / ".tools/field-runtime.json",
            field_source="Same user upload for controlled player comparison",
            field_usage="Local comparison of existing user upload",
            tracker_config_path=ROOT / "configs/bytetrack.yaml",
            team_config_path=ROOT / "configs/teams-broadcast.json",
        )
        write_json(path, {"run_directory": str(result.directory)})


def rank_models(rows):
    """Prefer macro balanced F1, using speed only within half a percentage point of the best."""
    maximum = max(r["pipeline"]["macro_F1"] for r in rows.values())
    tied = [k for k, v in rows.items() if maximum - v["pipeline"]["macro_F1"] < 0.005]
    return min(tied, key=lambda k: rows[k]["speed"]["detector_stack"]["median_ms"]), tied


def report(output):
    """Publish the completed comparison, qualification and links without activating any model."""
    rows = {}
    for name in profiles(output):
        directory = output / "evaluation" / name
        rows[name] = {
            "raw": read_json(directory / "raw-metrics.json"),
            "pipeline": read_json(directory / "pipeline-summary.json"),
            "speed": read_json(directory / "speed.json"),
        }
    winner, tied = rank_models(rows)
    result = {
        "models": rows,
        "preferred": winner,
        "practically_tied": tied,
        "independent_final_test": False,
        "seeds": [42],
        "activated": False,
        "qualification": "Reused provider development validation; one training seed",
    }
    write_json(output / "comparison.json", result)
    lines = [
        "# YOLO26-spelersvergelijking",
        "",
        "Ontwikkelvalidatie: 348 eerder gebruikte beelden, één seed.",
        "",
        "| Model | Precision | Recall | Macro F1 | AP50–95 | Detector ms |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, row in rows.items():
        score = row["pipeline"]["overall"]
        lines.append(
            f"| {name} | {score['precision']:.4f} | {score['recall']:.4f} | "
            f"{row['pipeline']['macro_F1']:.4f} | {score['AP50_95']:.4f} | "
            f"{row['speed']['detector_stack']['median_ms']:.1f} |"
        )
    lines.extend(
        [
            "",
            f"Voorkeur: **{winner}**. Praktisch gelijk: {', '.join(tied)}.",
            "Geen kandidaat is automatisch geactiveerd. Snelheid is gemeten zonder videodecodering of veldnetwerk.",
            "",
            "Per-wedstrijdresultaten, losse detectie en piekgeheugen staan in comparison.json.",
            "Foutvoorbeelden: groen is providerreferentie, rood is detectie.",
        ]
    )
    (output / "COMPARISON.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    handoff(output)


def handoff(output):
    """Write a compact restart guide even when training or evaluation has not completed."""
    states = {}
    for size in (1536, 1280):
        for name in MODELS:
            path = output / f"{size}/{name}/status.json"
            if path.exists():
                states[f"{size}/{name}"] = read_json(path)
    write_json(output / "status.json", {"models": states, "updated_at": time.time()})
    python = ROOT / ".tools/yolo26-env/Scripts/python.exe"
    command = f'& "{python}" -m football_pipeline.yolo26_comparison --output "{output}"'
    stages = {}
    for name in ("current", *MODELS):
        directory = output / "evaluation" / name
        stages[name] = {
            "raw": (directory / "raw-metrics.json").exists(),
            "pipeline": (directory / "pipeline-summary.json").exists(),
            "speed": (directory / "speed.json").exists(),
            "video": (output / f"video-{name}.json").exists(),
        }
    lines = [
        "# YOLO26-spelersvergelijking — overdracht",
        "",
        "Alleen spelers; Andrew levert de bal. Geen kandidaat automatisch actief.",
        "De gewone app is tijdens GPU-training gestopt; starten kan na het stoppen van de trainer met scripts/Start-Laptop.ps1.",
        "",
        "## Trainingen",
        "",
        *[
            f"- {name}: {s['status']}; epoch {s.get('epoch', 0)}/100; checkpoint `{s.get('checkpoint', '-')}`"
            for name, s in states.items()
        ],
        "",
        "## Hervatten",
        "",
        "Controleer eerst de Codex-limieten en vernieuw usage.json met --record-remaining.",
        "",
        "```powershell",
        f"{command} --phase all --resume",
        "```",
        "",
        "## Nog controleren",
        "",
        "Zie comparison.json voor afgeronde metingen. Zonder dat bestand is de vergelijking nog niet compleet.",
        *[
            f"- {name}: "
            + ", ".join(f"{stage}={'klaar' if done else 'nog doen'}" for stage, done in status.items())
            for name, status in stages.items()
        ],
        "Visuele QA en softwarecontroles: zie visual-qa.json en checks.json; zonder die bestanden nog niet afgerond.",
        "Ontwikkelvalidatie: 348 eerder gebruikte beelden, één seed; geen onafhankelijke eindtest.",
    ]
    if (output / "comparison.json").exists():
        comparison = read_json(output / "comparison.json")
        lines.extend(["", f"Gemeten voorkeur: {comparison['preferred']}; details in COMPARISON.md."])
    (output / "HANDOFF.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    """Dispatch experiment phases, quota snapshots and explicit safe-pause requests."""
    configure_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--phase",
        choices=("prepare", "train", "evaluate", "videos", "report", "all", "status", "pause"),
        default="all",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--record-remaining", type=float)
    parser.add_argument("--record-unavailable", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.record_unavailable:
        write_json(output / "usage.json", {"remaining_percent": None, "checked_at": time.time()})
        return
    if args.record_remaining is not None:
        if not 0 <= args.record_remaining <= 100:
            raise ValueError("Remaining percent must be within 0..100")
        write_json(
            output / "usage.json", {"remaining_percent": args.record_remaining, "checked_at": time.time()}
        )
        return
    if args.phase == "pause":
        (output / "pause.request").write_text("Pause at next safe checkpoint", encoding="utf-8")
        return
    if args.phase == "status":
        handoff(output)
        print(json.dumps(read_json(output / "status.json")), flush=True)
        return
    if args.resume:
        (output / "pause.request").unlink(missing_ok=True)
    from filelock import FileLock

    locked = False
    try:
        with FileLock(output / "runner.lock", timeout=0):
            locked = True
            write_json(
                output / "control.json",
                {"status": "running", "phase": args.phase, "pid": os.getpid(), "started_at": time.time()},
            )
            if args.phase in {"prepare", "all"}:
                prepare(output)
            if args.phase in {"train", "all"}:
                train_all(output)
            if args.phase in {"evaluate", "all"}:
                evaluate_all(output)
            if args.phase in {"videos", "all"}:
                videos(output)
            if args.phase in {"report", "all"}:
                report(output)
            write_json(
                output / "control.json",
                {"status": "complete", "phase": args.phase, "pid": os.getpid(), "finished_at": time.time()},
            )
    except ExperimentPaused as exc:
        write_json(
            output / "control.json",
            {
                "status": "paused",
                "phase": args.phase,
                "reason": str(exc),
                "pid": os.getpid(),
                "finished_at": time.time(),
            },
        )
        print(f"SAFE PAUSE: {exc}", flush=True)
    except Exception as exc:
        if locked:
            write_json(
                output / "control.json",
                {
                    "status": "failed",
                    "phase": args.phase,
                    "error": str(exc),
                    "pid": os.getpid(),
                    "finished_at": time.time(),
                },
            )
        raise
    finally:
        handoff(output)


if __name__ == "__main__":
    main()
