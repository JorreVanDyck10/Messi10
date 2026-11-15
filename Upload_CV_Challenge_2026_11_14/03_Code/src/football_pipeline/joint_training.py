"""Orkestreert gezamenlijke training, kandidaatselectie en demonstratie van de afzonderlijke deelsystemen."""

from __future__ import annotations

import argparse
import gc
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .contracts import digest_json, read_json, sha256_file, write_json
from .video import ROOT


def choose_player(baseline, candidate):
    """Pas de expliciete selectieregels toe op baseline- en kandidaatspelersmetingen en retourneer de
    modelkeuze.
    """
    b = {r["name"]: r for r in baseline["per_class"]}
    c = {r["name"]: r for r in candidate["per_class"]}
    return (
        sum(c[n]["AP50_95"] or 0 for n in ("player", "referee"))
        > sum(b[n]["AP50_95"] or 0 for n in ("player", "referee"))
        and c["player"]["recall"] >= b["player"]["recall"]
    )


def choose_roles(baseline, candidate):
    """Vergelijk rolmetingen volgens de vastgelegde criteria en kies alleen een ondersteunde verbetering."""
    b = {r["name"]: r for r in baseline["per_class"]}
    c = {r["name"]: r for r in candidate["per_class"]}
    return candidate["macro_f1"] > baseline["macro_f1"] and all(c[n]["recall"] >= b[n]["recall"] for n in b)


def choose_ball(baseline, candidate):
    """Vergelijk de balmetrieken en foutaantallen van baseline en kandidaat onder dezelfde
    evaluatieopzet.
    """
    b, c = baseline["per_class"][0], candidate["per_class"][0]
    return (
        c["AP50_95"] > b["AP50_95"] and c["recall"] >= b["recall"] and c["precision"] >= b["precision"] - 0.05
    )


def choose_field(baseline, candidate):
    """Kies tussen veldbaseline en kandidaat op basis van de beschikbare geometrie- en
    dekkingsvoorwaarden.
    """
    return (
        candidate["valid_frames"]
        - candidate["wrong_calibrations"]
        - candidate.get("unscored_valid_frames", 0)
        > baseline["valid_frames"] - baseline["wrong_calibrations"] - baseline.get("unscored_valid_frames", 0)
        and candidate["wrong_calibrations"] <= baseline["wrong_calibrations"]
        and candidate["median_error_px"] is not None
        and (
            baseline["median_error_px"] is None or candidate["median_error_px"] <= baseline["median_error_px"]
        )
    )


def players(dataset, output):
    """Voer de gezamenlijke spelertraining en bijbehorende baseline-/kandidaatmeting uit en bewaar de
    selectie.
    """
    from .course_experiments import evaluate_model, train_candidate

    baseline = ROOT / "artifacts/players-v3/players_best.pt"
    saved = output / "training/status.json"
    if saved.exists():
        record = read_json(saved)
        best = Path(record["best"])
        bootstrap_path = output.parent / "player-bootstrap.json"
        expected_start = Path(read_json(bootstrap_path)["weights"]) if bootstrap_path.exists() else baseline
        if (
            record.get("status") not in {"complete", "time_limited"}
            or sha256_file(best) != record["best_sha256"]
            or sha256_file(expected_start) != record["base_sha256"]
        ):
            raise ValueError("Cannot recover an incomplete or changed player checkpoint")
    else:
        bootstrap_path = output.parent / "player-bootstrap.json"
        bootstrap = read_json(bootstrap_path) if bootstrap_path.exists() else None
        starting_weights = Path(bootstrap["weights"]) if bootstrap else baseline
        if bootstrap and sha256_file(starting_weights) != bootstrap["weights_sha256"]:
            raise ValueError("Bootstrap checkpoint changed")
        best = train_candidate(
            dataset / "players",
            output / "training",
            augment=True,
            epochs=60 - bootstrap["epochs"] if bootstrap else 60,
            weights=starting_weights,
            max_minutes=60 - bootstrap["runtime_s"] / 60 if bootstrap else 60,
        )
    metrics = {
        "baseline": evaluate_model(baseline, dataset / "players", output / "baseline"),
        "candidate": evaluate_model(best, dataset / "players", output / "candidate"),
    }
    training = read_json(output / "training/status.json")
    bootstrap_path = output.parent / "player-bootstrap.json"
    if bootstrap_path.exists():
        bootstrap = read_json(bootstrap_path)
        training = {
            **training,
            "phases": [bootstrap, training],
            "epochs": bootstrap["epochs"] + training["epochs"],
            "runtime_s": bootstrap["runtime_s"] + training["runtime_s"],
            "data_correction": "16 complete frames restored in v2; only remaining epochs were run before paired v2 evaluation",
        }
    return {
        "metrics": metrics,
        "promoted": choose_player(metrics["baseline"], metrics["candidate"]),
        "baseline": str(baseline),
        "candidate": str(best.resolve()),
        "training": training,
        "criterion": "Higher mean player/referee AP50:95 with no lower player recall at .25",
    }


def roles(dataset, output, *, manifest=None, training_name="training", minutes=26):
    """Train en vergelijk de gezamenlijke rolclassifier met de opgeslagen roldataset en het toegewezen
    tijdsbudget.
    """
    from persoon1.role_training import load_training_manifest, train
    from scripts.evaluate_role_extension import infer, summarize

    baseline = ROOT / "artifacts/appearance-v1/roles_teams.pt"
    manifest = manifest or dataset / "roles/manifest.json"
    best = output / training_name / "roles_teams.pt"
    saved = output / training_name / "metrics.json"
    if saved.exists():
        record = read_json(saved)
        if (
            record.get("status") not in {"complete", "time_limited"}
            or record["dataset_sha256"] != sha256_file(manifest)
            or record["weights_sha256"] != sha256_file(best)
        ):
            raise ValueError("Completed role checkpoint or its dataset changed")
    else:
        train(output / training_name, True, baseline, manifest, 1, 8.0, minutes)
    rows = [r for r in load_training_manifest(manifest)["samples"] if r["split"] == "val"]
    metrics = {
        name: summarize(rows, infer(weights, dataset / "roles", rows))
        for name, weights in (("baseline", baseline), ("candidate", best))
    }
    curves = read_json(output / training_name / "curves.json")
    fine_path = output / training_name / "fine-tune-curves.json"
    fine_epochs = len(json.loads(fine_path.read_text(encoding="utf-8"))) if fine_path.exists() else 0
    return {
        "metrics": metrics,
        "promoted": choose_roles(metrics["baseline"], metrics["candidate"]),
        "baseline": str(baseline),
        "candidate": str(best.resolve()),
        "training": {
            **read_json(output / training_name / "metrics.json"),
            "executed_epochs": {
                "backbone": fine_epochs,
                **{name: max((row["epoch"] for row in rows), default=0) for name, rows in curves.items()},
            },
        },
        "criterion": "Higher role macro-F1 at .65 without lower recall in any measured role",
    }


def refit_role_pixels(dataset, output):
    """Bereid de roltrainingspixels voor en train de toegestane encoder-/kopvariant op die expliciete
    invoer.
    """
    import shutil

    from .joint_data import prepare_role_pixel_overlay

    manifest = prepare_role_pixel_overlay(dataset)
    role_output = output / "roles"
    old = read_json(role_output / "comparison.json")
    if old.get("pixel_manifest_sha256") == sha256_file(manifest):
        return
    previous_runtime = old["training"]["runtime_s"]
    write_json(role_output / "comparison-before-pixel-audit.json", old)
    sources = {}
    for source in [
        ROOT / "persoon1/role_training.py",
        Path(__file__),
        ROOT / "src/football_pipeline/joint_data.py",
        ROOT / "src/football_pipeline/appearance.py",
    ]:
        target = role_output / "pixel-sources" / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        sources[source.relative_to(ROOT).as_posix()] = sha256_file(target)
    write_json(role_output / "pixel-source-snapshot.json", sources)
    write_json(
        role_output / "job.json",
        {"status": "running", "stage": "roles", "pid": os.getpid(), "started": time.time()},
    )
    try:
        result = roles(
            dataset,
            role_output,
            manifest=manifest,
            training_name="pixel-training",
            minutes=26 - previous_runtime / 60,
        )
    except BaseException as exc:
        write_json(role_output / "job.json", {"status": "failed", "stage": "roles", "error": str(exc)})
        raise
    training = result["training"]
    result["training"] = {
        **training,
        "phases": [old["training"], training],
        "runtime_s": previous_runtime + training["runtime_s"],
        "data_correction": "2 duplicate training and 14 duplicate validation crops removed by exact padded pixel hash; no cross-split copies found",
    }
    result.update(
        status="complete",
        stage="roles",
        pixel_manifest_sha256=sha256_file(manifest),
        human_review_completed=False,
        independent_final_test_completed=False,
    )
    result["selected"] = result["candidate"] if result["promoted"] else result["baseline"]
    write_json(role_output / "comparison.json", result)
    write_json(
        role_output / "job.json", {"status": "complete", "stage": "roles", "promoted": result["promoted"]}
    )


def evaluate_ball(weights, dataset, output):
    """Meet één balcheckpoint op de vastgelegde gezamenlijke referenties en bewaar de inferentie-
    identiteit bij de scores.
    """
    import cv2

    from persoon1.metrics import evaluate
    from persoon1.modeling import yolo

    from .ball_tiles import merge_ball_predictions, predict_ball_tiles

    all_rows = [r for r in read_json(dataset / "ball/manifest.json")["full_frames"] if r["split"] == "val"]
    rows = [
        r
        for r in all_rows
        if not r.get("crop_xyxy_source") and "crop" not in r.get("preprocessing", "").lower()
    ]
    model = yolo(weights)
    if model.names[32] != "sports ball":
        raise ValueError("Ball model lost its actual source class")
    truth, predictions = {}, {}
    start = time.monotonic()
    for row in rows:
        key = row["image_sha256"]
        truth[key] = [
            {"class_id": 0, "bbox_xyxy": b["bbox_xyxy"]} for b in row["boxes"] if b["name"] == "ball"
        ]
        image = cv2.imread(row["image"])
        boxes = []
        for size in (1280, 640):
            boxes.extend(
                predict_ball_tiles(
                    model, image, size=size, imgsz=1280, source_class=32, device="0", confidence=0.001
                )
            )
        predictions[key] = merge_ball_predictions(boxes, 0.5)
    metrics = evaluate(truth, predictions, ["ball"], confidence=0.25)
    metrics["full_frame_validation_images"] = len(rows)
    metrics["crop_validation_images_excluded_from_full_frame_AP"] = len(all_rows) - len(rows)
    write_json(
        output,
        {
            "metrics": metrics,
            "truth": truth,
            "predictions": predictions,
            "weights_sha256": sha256_file(weights),
            "runtime_s": time.monotonic() - start,
        },
    )
    return metrics


def ball(dataset, output):
    """Train de gezamenlijke balkandidaat, vergelijk haar met de baseline en bewaar de uiteindelijke
    modelkeuze.
    """
    from .training_budget import resume_yolo, train_yolo

    baseline = ROOT / "artifacts/fullscene-ball-v1/fullscene_ball_f005.pt"
    config = read_json(ROOT / "configs/train-fullscene60-ball-native.json")
    pause_path = output.parent / "paused.json"
    saved = output / "training/status.json"
    record = read_json(saved) if saved.exists() else {}
    if record.get("status") in {"complete", "time_limited"}:
        best = Path(record["best"])
        if sha256_file(best) != record["best_sha256"] or sha256_file(baseline) != record["base_sha256"]:
            raise ValueError("Completed ball checkpoint or its baseline changed")
    elif pause_path.exists():
        best = resume_yolo(dataset / "ball", output / "training", read_json(pause_path)["ball"])
    else:
        best = train_yolo(baseline, dataset / "ball", output / "training", config, 55)
    metrics = {
        "baseline": evaluate_ball(baseline, dataset, output / "baseline.json"),
        "candidate": evaluate_ball(best, dataset, output / "candidate.json"),
    }
    return {
        "metrics": metrics,
        "promoted": choose_ball(metrics["baseline"], metrics["candidate"]),
        "baseline": str(baseline),
        "candidate": str(best.resolve()),
        "training": read_json(output / "training/status.json"),
        "criterion": "Higher full-frame multiscale ball AP50:95, no lower recall, precision decrease at most .05",
    }


def field(dataset, output):
    """Start de veldtrainingsfase en vergelijk de getrainde runtime met de vastgelegde veldbaseline."""
    field_python = ROOT / ".tools/field-training-env/Scripts/python.exe"
    baseline = ROOT / ".tools/field-runtime.json"
    subprocess.run(
        [
            str(field_python),
            "-u",
            "-m",
            "football_pipeline.joint_field",
            "--dataset",
            str(dataset / "field"),
            "--runtime",
            str(baseline),
            "--output",
            str(output / "training"),
        ],
        cwd=ROOT,
        check=True,
    )
    comparison = read_json(output / "training/comparison.json")
    return {
        "metrics": comparison["models"],
        "promoted": choose_field(comparison["models"]["baseline"], comparison["models"]["candidate"]),
        "baseline": str(baseline),
        "candidate": str((output / "training/field-runtime.json").resolve()),
        "training": read_json(output / "training/training-report.json"),
        "criterion": "More correct geometric projections, no additional wrong calibrations, no higher median line error; must also pass broadcast coverage check",
    }


def stage(name, dataset, output, resume=False):
    """Voer één deeltraining uit of hergebruik een aantoonbaar voltooide fase; bewaar voortgang en fouten
    voor hervatten.
    """
    import shutil

    import torch

    if resume:
        previous = read_json(output / "job.json")
        if previous["status"] not in {"failed", "paused"}:
            raise ValueError("Only a failed or paused stage can be resumed explicitly")
        write_json(output / "job-before-resume.json", previous)
    output.mkdir(parents=True, exist_ok=resume)
    snapshots = {}
    for path in [*(ROOT / "src/football_pipeline").glob("*.py"), ROOT / "persoon1/role_training.py"]:
        relative = path.relative_to(ROOT)
        destination = output / "sources" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        snapshots[relative.as_posix()] = sha256_file(destination)
    write_json(output / "source-snapshot.json", snapshots)
    write_json(
        output / "source-snapshot-note.json",
        {
            "captured_before": "recovered paired evaluation; original training hash remains in training/status.json"
            if resume
            else "stage training",
            "resume": resume,
        },
    )
    write_json(
        output / "job.json", {"status": "running", "stage": name, "pid": os.getpid(), "started": time.time()}
    )
    try:
        result = globals()[name](dataset, output)
        result.update(
            status="complete",
            stage=name,
            human_review_completed=False,
            independent_final_test_completed=False,
        )
        result["selected"] = result["candidate"] if result["promoted"] else result["baseline"]
        write_json(output / "comparison.json", result)
        write_json(output / "job.json", {"status": "complete", "stage": name, "promoted": result["promoted"]})
        if name == "ball" and (output.parent / "paused.json").exists():
            (output.parent / "paused.json").replace(output.parent / "pause-completed.json")
        print(name, "promoted", result["promoted"], flush=True)
    except BaseException as exc:
        write_json(output / "job.json", {"status": "failed", "stage": name, "error": str(exc)})
        raise
    finally:
        gc.collect()
        torch.cuda.empty_cache()


def make_profile(output):
    """Maak een gecombineerd runtimeprofiel uit de werkelijk geselecteerde checkpoints van de
    deeltrainingen.
    """
    from .detection import load_model_manifest

    reports = {n: read_json(output / n / "comparison.json") for n in ("players", "roles", "ball", "field")}
    profile = read_json(ROOT / "configs/models-roles-r007.json")
    for spec in profile["models"]:
        spec["weights"] = str((ROOT / "configs" / spec["weights"]).resolve())
    first = profile["models"][0]
    first.update(
        weights=reports["players"]["selected"],
        weights_sha256=sha256_file(reports["players"]["selected"]),
        model_id="joint-selected-players",
        imgsz=1280,
    )
    profile["appearance"].update(
        weights=reports["roles"]["selected"],
        weights_sha256=sha256_file(reports["roles"]["selected"]),
        model_id="joint-selected-roles",
    )
    spec = read_json(ROOT / "configs/models-ball-f005.json")["models"][0]
    spec.update(
        weights=reports["ball"]["selected"],
        weights_sha256=sha256_file(reports["ball"]["selected"]),
        model_id="joint-selected-ball",
    )
    profile["models"].append(spec)
    profile["profile_name"] = "Gezamenlijke training 27 oktober — spelers, rollen, bal en teams"
    profile["handoff"] = {
        "evaluation_record": str((output / "comparison.json").resolve()),
        "human_review_completed": False,
        "independent_final_test_completed": False,
        "scope": "Local development validation; no general accuracy or in-play ball claim",
    }
    write_json(output / "comparison.json", reports)
    profile_path = ROOT / "configs/models-integrated-20261027.json"
    write_json(profile_path, profile)
    load_model_manifest(profile_path)
    selected_runtime = read_json(reports["field"]["selected"])
    write_json(output / "selected-field-runtime.json", selected_runtime)
    return profile_path, output / "selected-field-runtime.json"


def demonstrate(output, dataset=None):
    """Verwerk de geselecteerde echte clips met het gezamenlijke profiel en registreer de resulterende
    demonstratieruns.
    """
    from scripts.check_team_integration import check_result

    from .pipeline import process_video
    from .video import find_tool

    profile, runtime = make_profile(output)
    sources = {
        "broadcast": ROOT
        / "data/uploads/6cdaf4089cb578636bc4773bde0ebdc1e68b8554e169d413e855bdf144780f4a.mp4",
        "panorama": ROOT
        / "data/uploads/caaf63af7750eb56c6f31fbb9bceeb5d51bc06a1654659f110b34f5462ae542d.mp4",
    }
    results = {}
    field_report = read_json(output / "field/comparison.json")
    if field_report["promoted"]:
        # The existing broadcast smoke clip is fixed before either field model
        # is compared. It has its own video hash and is never given another
        # recording's calibration.
        smoke = ROOT / ".cache/automatic-upload-real-smoke.mp4"
        coverage = {}
        for label, path in (("baseline", field_report["baseline"]), ("candidate", field_report["candidate"])):
            coverage[label] = field_coverage(smoke, Path(path), output / f"field-broadcast-{label}")
        field_report["broadcast_coverage"] = coverage
        if coverage["candidate"] < coverage["baseline"]:
            field_report.update(
                promoted=False, selected=field_report["baseline"], rejection="Broadcast coverage regressed"
            )
        write_json(output / "field/comparison.json", field_report)
        profile, runtime = make_profile(output)
    for name, source in sources.items():
        clip = output / f"demo-{name}-{sha256_file(source)[:12]}.mp4"
        subprocess.run(
            [
                find_tool("ffmpeg"),
                "-y",
                "-i",
                str(source),
                "-t",
                "6",
                "-an",
                "-c:v",
                "libx264",
                "-crf",
                "18",
                "-preset",
                "fast",
                "-pix_fmt",
                "yuv420p",
                str(clip),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        result = process_video(
            clip,
            None,
            profile,
            ROOT / "runs",
            field_runtime_path=runtime,
            field_source="Existing locally supplied development clip",
            field_usage="Local project development",
            tracker_config_path=ROOT / "configs/bytetrack.yaml",
            team_config_path=ROOT / "configs/teams.json",
        )
        results[name] = check_result(result)
        write_json(output / "demonstrations.json", results)
    if dataset is not None:
        from .joint_report import write_report

        write_report(dataset, output)
    return results


def field_coverage(video_path, runtime_path, output):
    """Voer veldherkenning uit voor de opgegeven video en vat samen op hoeveel frames bruikbare
    veldkalibratie beschikbaar is.
    """
    import cv2

    from .automatic_calibration import prepare_automatic_calibration
    from .field_motion import DEFAULT_SETTINGS, CameraCalibration, estimate_checked
    from .video import inspect_video

    bundle = prepare_automatic_calibration(
        video_path,
        runtime_path,
        output,
        source="Existing broadcast development smoke clip",
        usage="Local development comparison",
    )
    video = inspect_video(video_path)
    estimator = CameraCalibration(video.fps, DEFAULT_SETTINGS)
    capture = cv2.VideoCapture(str(video_path))
    states = []
    try:
        with Path(bundle.observations_path).open(encoding="utf-8") as stream:
            for line in stream:
                success, frame = capture.read()
                if not success:
                    raise ValueError("Incomplete broadcast field comparison")
                observation = json.loads(line)
                direct = estimate_checked(observation, video.size, DEFAULT_SETTINGS)
                states.append(estimator.update(frame, direct, observation["frame_index"]))
    finally:
        capture.release()
    if len(states) != video.frame_count:
        raise ValueError("Field comparison frame count differs")
    write_json(
        output / "coverage.json",
        {"frames": len(states), "valid": sum(s["status"] == "valid" for s in states)},
    )
    return sum(s["status"] == "valid" for s in states) / len(states)


def run(dataset, output):
    """Orkestreer de gezamenlijke trainingsfasen, vergelijkingen, profielbouw en demonstratie met behoud
    van eerdere resultaten.
    """
    output.mkdir(parents=True, exist_ok=True)
    identity = digest_json(
        {
            "datasets": {
                name: sha256_file(dataset / name)
                for name in (
                    "inventory.json",
                    "players/manifest.json",
                    "roles/manifest.json",
                    "ball/manifest.json",
                    "field/index.json",
                )
            },
            "ball_config": sha256_file(ROOT / "configs/train-fullscene60-ball-native.json"),
            "baselines": {
                name: sha256_file(ROOT / name)
                for name in (
                    "artifacts/players-v3/players_best.pt",
                    "artifacts/appearance-v1/roles_teams.pt",
                    "artifacts/fullscene-ball-v1/fullscene_ball_f005.pt",
                    ".tools/field-runtime.json",
                )
            },
            "minutes": {"players": 60, "roles": 30, "ball": 60, "field": 90},
        }
    )
    round_path = output / "round.json"
    if round_path.exists() and read_json(round_path)["identity"] != identity:
        raise ValueError("Dataset, training configuration or baseline changed; choose a new output round")
    write_json(
        round_path,
        {
            "identity": identity,
            "dataset": str(dataset),
            "seed": 42,
            "automatic_promotion": "only after validation and integration",
            "gpu_minutes": 240,
        },
    )
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(ROOT),
        "PYTHONUNBUFFERED": "1",
        "OMP_NUM_THREADS": "4",
        "MKL_NUM_THREADS": "4",
    }
    for name in ("players", "roles", "ball", "field"):
        job_path = output / name / "job.json"
        if job_path.exists() and read_json(job_path).get("status") == "running":
            import psutil

            while read_json(job_path).get("status") == "running":
                if not psutil.pid_exists(read_json(job_path)["pid"]):
                    raise RuntimeError(f"Interrupted {name} stage; inspect its saved logs before retrying")
                time.sleep(2)
        if (output / name / "comparison.json").exists():
            continue
        with (
            (output / f"{name}.stdout.log").open("w", encoding="utf-8") as stdout,
            (output / f"{name}.stderr.log").open("w", encoding="utf-8") as stderr,
        ):
            subprocess.run(
                [
                    sys.executable,
                    "-u",
                    "-m",
                    "football_pipeline.joint_training",
                    name,
                    "--dataset",
                    str(dataset),
                    "--output",
                    str(output / name),
                    *(
                        ["--resume"]
                        if job_path.exists() and read_json(job_path).get("status") == "paused"
                        else []
                    ),
                ],
                cwd=ROOT,
                env=env,
                stdout=stdout,
                stderr=stderr,
                check=True,
            )
    refit_role_pixels(dataset, output)
    demonstrations = demonstrate(output, dataset)
    write_json(output / "finished.json", {"status": "complete", "demonstrations": demonstrations})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["players", "roles", "ball", "field", "run", "finish"])
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.stage == "run":
        run(args.dataset.resolve(), args.output.resolve())
    elif args.stage == "finish":
        demonstrate(args.output.resolve(), args.dataset.resolve())
    else:
        stage(args.stage, args.dataset.resolve(), args.output.resolve(), args.resume)
