"""Detached, sequential training worker. Every model runs in its own GPU process."""

from __future__ import annotations

import argparse
import copy
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil
from filelock import FileLock

from .contracts import digest_json, read_json, sha256_file, write_json
from .training_transfer import imported_source_root, rebase
from .training_workbench import local_path
from .video import ROOT


def bind_json(path):
    """Lees bronmetadata en bind alleen oorspronkelijke projectpaden aan de huidige checkout."""
    return rebase(read_json(path), imported_source_root(), ROOT)


def initial_profile(source, destination):
    """Maak een apart startprofiel met geldige absolute gewichtspaden en behoud de bronklassen."""
    from .detection import load_model_manifest

    profile = bind_json(source)
    for model in profile["models"] + [
        profile[k] for k in ("appearance", "kit_embedding", "role_context") if k in profile
    ]:
        model["weights"] = str((source.parent / model["weights"]).resolve())
    write_json(destination, profile)
    return load_model_manifest(destination)


def yolo_data(source, output):
    """Valideer splits en bronhashes en schrijf een aan deze projectmap gebonden YOLO-dataset."""
    import yaml

    source = Path(source)
    metadata = source / "manifest.json"
    if metadata.exists():
        index = bind_json(metadata)
        split_by_match, split_by_image = {}, {}
        for row in index.get("frames", index.get("rows", [])):
            split = row["split"]
            if split not in {"train", "val"}:
                raise ValueError("Testbeelden mogen niet naar training of modelselectie")
            group = row.get(
                "match_id", row.get("game_id", row.get("video_id", row.get("source_frame_group")))
            )
            for seen, identity in ((split_by_match, group), (split_by_image, row.get("image_sha256"))):
                if identity is not None:
                    if identity in seen and seen[identity] != split:
                        raise ValueError("Wedstrijd of bronbeeld komt in beide trainingssplits voor")
                    seen[identity] = split
            for key in ("image", "label"):
                if key in row and key + "_sha256" in row:
                    path = Path(row[key])
                    if not path.is_absolute():
                        path = source / path
                    if not path.is_file() or sha256_file(path) != row[key + "_sha256"]:
                        raise ValueError(f"Trainingsbron ontbreekt of is veranderd: {path}")
    data = rebase(
        yaml.safe_load((source / "data.yaml").read_text(encoding="utf-8")), imported_source_root(), ROOT
    )
    base = Path(data.get("path", source))
    if not base.is_absolute():
        base = (source / base).resolve()
    for split in ("train", "val"):
        values = data.get(split)
        if not values:
            raise ValueError(f"Trainingsdata mist {split}")
        for value in values if isinstance(values, list) else [values]:
            path = Path(value) if Path(value).is_absolute() else base / value
            if not path.exists():
                raise ValueError(f"Beelden ontbreken: {path}")
    data["path"] = str(base)
    output.mkdir(parents=True, exist_ok=True)
    (output / "data.yaml").write_text(yaml.safe_dump(data, sort_keys=True), encoding="utf-8")
    return data


def train_andrew(inputs, directory, *, epochs, minutes):
    """Keep the four-class detector separate from the other component candidates."""
    from ultralytics import YOLO

    from .detection import load_model_manifest
    from .training_budget import train_yolo

    source = local_path(inputs["andrew_profile"])
    profile = load_model_manifest(source)
    names = {0: "ball", 1: "goalkeeper", 2: "player", 3: "referee"}
    initial = profile["models"][0]["weights"]
    if YOLO(initial).names != names:
        raise ValueError("Andrew-startmodel moet bal, keeper, speler en scheidsrechter bevatten")
    data = yolo_data(local_path(inputs["andrew_dataset"]), directory / "dataset")
    dataset_names = data["names"]
    if isinstance(dataset_names, list):
        dataset_names = dict(enumerate(dataset_names))
    if dataset_names != names:
        raise ValueError("De datasetklassen passen niet bij Andrews vierklassendetector")
    weights = train_yolo(
        initial,
        directory / "dataset",
        directory / "training",
        {
            "epochs": epochs,
            "imgsz": 1280,
            "batch": 1,
            "seed": 42,
            "patience": 10,
            "optimizer": "AdamW",
            "lr0": 0.0001,
            "amp": True,
            "plots": True,
            "workers": 0,
        },
        minutes,
    )
    if YOLO(str(weights)).names != names:
        raise ValueError("Getraind Andrew-model heeft onverwachte klassen")
    profile["models"][0].update(
        weights=str(weights.resolve()),
        weights_sha256=sha256_file(weights),
        model_id="andrew-four-class-" + directory.parent.name,
    )
    profile["profile_name"] = "Andrew · getrainde kandidaat · " + directory.parent.name
    profile["handoff"] = {
        "human_review_completed": False,
        "independent_final_test_completed": False,
        "targets_met": False,
        "scope": "Four-class development training; evaluation required",
    }
    candidate = directory / "candidate-profile.json"
    write_json(candidate, profile)
    load_model_manifest(candidate)
    return candidate


def save_result(directory, weights, inputs):
    """Leg een afgeronde kandidaat met gewichtshash en beoordelingsstatus vast zonder activatie."""
    write_json(
        directory / "result.json",
        {
            "status": "complete",
            "weights": str(weights.resolve()),
            "weights_sha256": sha256_file(weights),
            "human_review_completed": False,
            "independent_final_test_completed": False,
            "activated": False,
            "evaluation_required": True,
            "training_data": inputs,
        },
    )


def one_model(spec_path, task):
    """Train een gekozen onderdeel in een eigen GPU-proces en bewaar zijn geisoleerde kandidaat."""
    import torch

    from .detection import load_model_manifest
    from .training_hardware import probe

    spec, directory = read_json(spec_path), spec_path.parent / task
    directory.mkdir(exist_ok=True)
    hardware = probe()
    write_json(directory / "hardware.json", hardware)
    if not hardware["ready"]:
        raise ValueError(hardware.get("error", "GPU-controle mislukt"))
    inputs, epochs, minutes = spec["inputs"], spec["epochs"], spec["minutes_per_model"]
    if task == "andrew":
        candidate = train_andrew(inputs, directory, epochs=epochs, minutes=minutes)
        save_result(directory, candidate, inputs)
        return
    profile_path = spec_path.parent / "candidate-profile.json"
    base_profile_path = spec_path.parent / "base-profile.json"
    if not base_profile_path.exists():
        initial_profile(local_path(inputs["profile"]), base_profile_path)
    if not profile_path.exists():
        models = load_model_manifest(base_profile_path)
        models["profile_name"] = "Trainingskandidaten · " + spec_path.parent.name
        models["handoff"] = {
            "human_review_completed": False,
            "independent_final_test_completed": False,
            "targets_met": False,
            "scope": "Local training candidates; evaluation required",
        }
        write_json(profile_path, models)
    profile = load_model_manifest(profile_path)
    weights = None
    if task in {"players", "ball"}:
        from .training_budget import train_yolo

        data = yolo_data(local_path(inputs[task]), directory / "dataset")
        if task == "players":
            initial = next(m["weights"] for m in profile["models"] if "player" in m["class_mapping"].values())
        else:
            initial = load_model_manifest(ROOT / "configs/models-ball-broadcast-v3.json")["models"][0][
                "weights"
            ]
        weights = train_yolo(
            initial,
            directory / "dataset",
            directory / "training",
            {
                "epochs": epochs,
                "imgsz": 1920 if task == "players" else 640,
                "batch": (1 if torch.cuda.mem_get_info()[0] < 8 * 1024**3 else 2),
                "seed": 42,
                "patience": 10,
                "optimizer": "AdamW",
                "lr0": 0.0001,
                "amp": True,
                "plots": True,
                "workers": 0,
            },
            minutes,
        )
        # Candidate profile is isolated from all default app profiles.
        if task == "players":
            from ultralytics import YOLO

            names = YOLO(str(weights)).names
            mapping = {str(k): name for k, name in names.items() if name in {"player", "referee", "person"}}
            if "player" not in mapping.values():
                raise ValueError("Getrainde klassen bevatten geen echte spelers")
            model = next(m for m in profile["models"] if "player" in m["class_mapping"].values())
            model.update(
                weights=str(weights.resolve()),
                weights_sha256=sha256_file(weights),
                expected_names={k: names[int(k)] for k in mapping},
                class_mapping=mapping,
                model_id="workbench-players-" + spec_path.parent.name,
            )
        else:
            from ultralytics import YOLO

            names = YOLO(str(weights)).names
            ball = copy.deepcopy(
                load_model_manifest(ROOT / "configs/models-ball-broadcast-v3.json")["models"][0]
            )
            mapping = {
                str(k): "ball" for k, name in names.items() if name in {"ball", "sports ball", "sports_ball"}
            }
            if not mapping:
                raise ValueError("Getrainde klassen bevatten geen bal")
            ball.update(
                weights=str(weights.resolve()),
                weights_sha256=sha256_file(weights),
                expected_names={k: names[int(k)] for k in mapping},
                class_mapping=mapping,
                model_id="workbench-ball-" + spec_path.parent.name,
            )
            profile["models"] = [
                m for m in profile["models"] if "ball" not in m["class_mapping"].values()
            ] + [ball]
    elif task in {"roles", "shirt"}:
        from . import broadcast_refine

        data = torch.load(local_path(inputs["appearance"]), map_location="cpu", weights_only=True)
        data["rows"] = rebase(data["rows"], imported_source_root(), ROOT)
        if {r["split"] for r in data["rows"]} - {"train", "val"}:
            raise ValueError("Voorbehouden testbeelden mogen niet naar training")
        originals = {row["image"]: row["image_sha256"] for row in data["rows"]}
        for image, checksum in originals.items():
            if not Path(image).is_file() or sha256_file(image) != checksum:
                raise ValueError("Appearance-bronbeeld ontbreekt of is veranderd")
        if task == "roles":
            # The stored feature statistics belong to this exact encoder state.
            baseline = directory / "feature-encoder.pt"
            torch.save({"backbone": data["backbone"]}, baseline)
            broadcast_refine.BASE_ROLES = baseline
            weights = broadcast_refine.roles(data, directory / "training", minutes=minutes, epochs=epochs)
            key, model_id = "appearance", "workbench-roles"
        else:
            weights = broadcast_refine.teams(data, directory / "training", minutes=minutes)
            key, model_id = "kit_embedding", "workbench-shirt"
        profile[key].update(
            weights=str(weights.resolve()), weights_sha256=sha256_file(weights), model_id=model_id
        )
        # A context head is tied to both dependencies; it cannot silently survive
        # a new role encoder or shirt metric. The context task rebuilds it next.
        profile.pop("role_context", None)
    elif task == "context":
        import shutil

        from .broadcast_observed_context import collect, train
        from .role_context import context_head

        source = local_path(inputs["context_dataset"])
        data = bind_json(source / "manifest.json")
        if any(r["split"] not in {"train", "val"} for r in data["frames"]):
            raise ValueError("Contextdata bevat testbeelden")
        bound = directory / "dataset"
        bound.mkdir(exist_ok=True)
        data["fingerprint"] = digest_json(data["frames"])
        write_json(bound / "manifest.json", data)
        shutil.copytree(source / "provider-labels", bound / "provider-labels")
        original = load_model_manifest(base_profile_path)
        context_spec = copy.deepcopy(original["role_context"])
        state = torch.load(context_spec["weights"], map_location="cpu", weights_only=True)
        # Transfer the frozen projection, then learn a fresh context head on the
        # current encoders. A neutral bootstrap head cannot relabel collection.
        neutral = context_head()
        for parameter in neutral.parameters():
            parameter.data.zero_()
        state.update(
            teacher_sha256=profile["appearance"]["weights_sha256"],
            kit_weights_sha256=profile["kit_embedding"]["weights_sha256"],
            state_dict=neutral.state_dict(),
            projection_source_weights_sha256=context_spec["weights_sha256"],
        )
        bootstrap = directory / "neutral-context.pt"
        torch.save(state, bootstrap)
        context_spec.update(weights=str(bootstrap.resolve()), weights_sha256=sha256_file(bootstrap))
        collection_profile = {**profile, "role_context": context_spec}
        collection_path = directory / "collection-profile.json"
        write_json(collection_path, collection_profile)
        # Regenerate against the just-trained player/role/shirt weights in this queue.
        collect(bound, collection_path, directory / "cache")
        weights = train(
            directory / "cache", directory / "training", epochs=epochs, device="cuda:0", minutes=minutes
        )
        profile["role_context"] = {
            **original["role_context"],
            "weights": str(weights.resolve()),
            "weights_sha256": sha256_file(weights),
            "model_id": "workbench-context",
        }
    elif task in {"field_points", "field_lines"}:
        from .field_learning import main as field_main

        index = bind_json(local_path(inputs["field"]))
        index["fingerprint"] = digest_json(index["frames"])
        bound = directory / "training-index.json"
        write_json(bound, index)
        argv = [
            "field_learning",
            "train",
            "--dataset-index",
            str(bound),
            "--output",
            str(directory / "training"),
            "--epochs",
            str(epochs),
            "--lr",
            "0.00001",
            "--patience",
            "8",
            "--roles",
            "keypoints" if task == "field_points" else "lines",
            "--max-minutes",
            str(minutes),
        ]
        sys.argv = argv
        field_main()
        weights = directory / "training/field-runtime.json"
        merged_path = spec_path.parent / "candidate-field-runtime.json"
        merged = (
            read_json(merged_path) if merged_path.exists() else read_json(ROOT / ".tools/field-runtime.json")
        )
        trained = read_json(weights)
        role = "keypoints" if task == "field_points" else "lines"
        merged["models"][role] = trained["models"][role]
        merged["weights_" + role] = trained["weights_" + role]
        merged.update(schema_version=2, automatic_promotion=False)
        write_json(merged_path, merged)
    else:
        raise ValueError("Onbekende modeltaak")
    if task not in {"field_points", "field_lines"}:
        # Recomputed hashes/expected classes must pass the regular profile validator.
        write_json(profile_path, profile)
        load_model_manifest(profile_path)
    save_result(directory, weights, inputs)


def run(spec_path):
    """Voer taken achter elkaar onder de lokale GPU-lock uit en bewaar stop-, fout- en voltooiingsstatussen."""
    directory, spec = spec_path.parent, read_json(spec_path)
    path = directory / "job.json"
    # The launcher publishes the exact PID before this worker mutates job state.
    for _ in range(100):
        job = read_json(path)
        launcher = job.get("pid")
        if launcher == os.getpid() or launcher in {p.pid for p in psutil.Process().parents()}:
            job.update(pid=os.getpid(), process_created_at=psutil.Process().create_time())
            break
        time.sleep(0.1)
    else:
        raise ValueError("Launcher heeft geen procesidentiteit gepubliceerd")
    job.update(status="running")
    write_json(path, job)
    (ROOT / ".cache").mkdir(exist_ok=True)
    try:
        with FileLock(str(ROOT / ".cache/training-workbench-gpu.lock"), timeout=0):
            for task in spec["tasks"]:
                if (directory / "stop-after-model.json").exists():
                    job.update(status="stopped")
                    break
                job.update(current_model=task)
                write_json(path, job)
                python = (
                    (ROOT / ".tools/field-training-env/Scripts/python.exe")
                    if task.startswith("field_")
                    else Path(spec["python"])
                )
                print(f"Start {task}", flush=True)
                subprocess.run(
                    [
                        str(python),
                        "-u",
                        "-m",
                        "football_pipeline.training_worker",
                        str(spec_path),
                        "--task",
                        task,
                    ],
                    cwd=ROOT,
                    check=True,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                job["completed"].append(task)
                write_json(path, job)
            else:
                job.update(status="complete")
    except BaseException as exc:
        job.update(status="failed", error=str(exc))
        raise
    finally:
        job.update(finished_at=time.time())
        write_json(path, job)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--task")
    args = parser.parse_args()
    one_model(args.spec, args.task) if args.task else run(args.spec)
