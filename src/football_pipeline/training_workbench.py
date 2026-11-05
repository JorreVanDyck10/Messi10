"""Local, restart-safe training jobs; no shell commands or automatic model activation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import psutil
from filelock import FileLock

from .contracts import PipelineError, read_json, write_json
from .video import ROOT

TASKS = {
    "players": "Spelers",
    "ball": "Bal",
    "roles": "Rollen",
    "shirt": "Shirtkenmerken",
    "context": "Spelerscontext",
    "field_points": "Veldpunten",
    "field_lines": "Veldlijnen",
    "andrew": "Andrew-model (4 klassen)",
}


def default_inputs(root=ROOT):
    """Geef de gedeelde bronpaden voor de acht trainingsonderdelen terug."""
    return {
        "players": "data/broadcast-multisource-v1",
        "ball": "data/joint-local-20261027-v2/ball",
        "appearance": "artifacts/broadcast-pitch-v1/appearance/features.pt",
        "context_dataset": "data/broadcast-pitch-v1",
        "field": "artifacts/player-field-reliability-20261030/field-recovery/training-index.json",
        "profile": "configs/models-broadcast.json",
        "andrew_dataset": "data/andrew-four-class-v1",
        "andrew_profile": "configs/models-andrew.json",
    }


def local_path(value, root=ROOT):
    """Zet een relatief bronpad om naar een absoluut pad vanuit de gekozen projectmap."""
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def training_processes():
    """Zoek bestaande lokale trainingsworkers om gelijktijdig GPU-gebruik te begrenzen."""
    found = []
    for process in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmd = process.info["cmdline"] or []
            if "python" not in (process.info["name"] or "").lower():
                continue
            if any(
                x in cmd
                for x in (
                    "football_pipeline.training_worker",
                    "football_pipeline.field_learning",
                    "football_pipeline.joint_training",
                    "football_pipeline.joint_field",
                    "football_pipeline.field_recovery",
                )
            ):
                if (
                    "train" in cmd
                    or "run" in cmd
                    or "football_pipeline.training_worker" in cmd
                    or "football_pipeline.field_recovery" in cmd
                ):
                    found.append({"pid": process.pid, "command": cmd})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return found


def check_inputs(tasks, inputs, root=ROOT):
    """Controleer vereiste datasets, startprofielen en veldomgevingen voor de gekozen taken."""
    issues = []
    required = {"profile"}
    for task in tasks:
        if task not in TASKS:
            raise PipelineError("Onbekend trainingsmodel")
        required.update(
            {
                "players": ["players"],
                "ball": ["ball"],
                "roles": ["appearance"],
                "shirt": ["appearance"],
                "context": ["context_dataset"],
                "field_points": ["field"],
                "field_lines": ["field"],
                "andrew": ["andrew_dataset", "andrew_profile"],
            }[task]
        )
    for key in sorted(required):
        path = local_path(inputs.get(key, ""), root)
        if not inputs.get(key) or not path.exists():
            issues.append(f"Ontbreekt: {key} ({path})")
        elif key in {"players", "ball", "andrew_dataset"} and not (path / "data.yaml").is_file():
            issues.append(f"Geen data.yaml bij {key}")
        elif key == "context_dataset" and not (path / "manifest.json").is_file():
            issues.append("Contextdata mist manifest.json")
    for task in tasks:
        if task.startswith("field_"):
            for name in (".tools/field-training-env/Scripts/python.exe", ".tools/field-runtime.json"):
                if not (root / name).is_file():
                    issues.append(f"Veldomgeving ontbreekt: {name}; voer Setup-Laptop.ps1 uit")
    return sorted(set(issues))


def job_alive(job):
    """Controleer procesidentiteit en starttijd zodat hergebruik van een PID geen actieve training simuleert."""
    try:
        process = psutil.Process(job["pid"])
        return abs(process.create_time() - job["process_created_at"]) < 1 and process.is_running()
    except (KeyError, psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def jobs(root=ROOT):
    """Laad trainingsrondes en markeer verdwenen workers als onderbroken zonder hun checkpoints te verwijderen."""
    result = []
    for path in sorted((root / "artifacts/training-workbench").glob("*/job.json"), reverse=True):
        try:
            job = read_json(path)
            if job["status"] in {"starting", "running"} and not job_alive(job):
                # A launch gets a short grace period before PID publication.
                if time.time() - job["created_at"] > 20:
                    job.update(
                        status="interrupted", error="Proces gestopt; bestaande checkpoints zijn behouden."
                    )
                    write_json(path, job)
            result.append((path.parent, job))
        except (PipelineError, OSError):
            continue
    return result


def launch(tasks, inputs, *, epochs=20, minutes=60, root=ROOT):
    """Valideer taken en limieten en start precies een onafhankelijke, herstartbestendige trainingsronde."""
    if not tasks or len(set(tasks)) != len(tasks) or not 1 <= epochs <= 300 or not 1 <= minutes <= 1440:
        raise PipelineError("Kies modellen en geldige trainingslimieten")
    issues = check_inputs(tasks, inputs, root)
    if issues:
        raise PipelineError("\n".join(issues))
    directory = root / "artifacts/training-workbench"
    directory.mkdir(parents=True, exist_ok=True)
    with FileLock(str(directory / ".launch.lock"), timeout=0):
        if training_processes() or any(j["status"] in {"starting", "running"} for _, j in jobs(root)):
            raise PipelineError("Er draait al een training op deze laptop. Wacht tot die klaar is.")
        path = directory / (time.strftime("%Y%m%d-%H%M%S", time.gmtime()) + "-" + uuid.uuid4().hex[:8])
        path.mkdir()
        spec = {
            "schema_version": 1,
            "tasks": tasks,
            "inputs": inputs,
            "epochs": epochs,
            "minutes_per_model": minutes,
            "workspace_root": str(root.resolve()),
            "python": sys.executable,
            "automatic_activation": False,
        }
        write_json(path / "spec.json", spec)
        job = {"status": "starting", "created_at": time.time(), "tasks": tasks, "completed": []}
        write_json(path / "job.json", job)
        env = {
            **os.environ,
            "PYTHONUNBUFFERED": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONPATH": str(root / "src") + os.pathsep + str(root) + os.pathsep + str(root / "scripts"),
        }
        try:
            with (path / "worker.log").open("ab") as log:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-u",
                        "-m",
                        "football_pipeline.training_worker",
                        str(path / "spec.json"),
                    ],
                    cwd=root,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            job.update(pid=process.pid, process_created_at=psutil.Process(process.pid).create_time())
            write_json(path / "job.json", job)
        except (OSError, psutil.Error) as exc:
            job.update(status="failed", error=str(exc))
            write_json(path / "job.json", job)
            raise PipelineError(f"Training starten mislukt: {exc}") from exc
        return path


def stop_after_model(path, root=ROOT):
    """Registreer binnen de bekende trainingsronde dat volgende modellen niet meer mogen starten."""
    path = Path(path).resolve()
    if not path.is_relative_to((root / "artifacts/training-workbench").resolve()):
        raise PipelineError("Onbekende trainingsmap")
    write_json(path / "stop-after-model.json", {"requested_at": time.time()})


def tail(path, limit=12000):
    """Lees het laatste deel van een trainingslog voor de voortgangsweergave."""
    if not path.exists():
        return ""
    with path.open("rb") as stream:
        stream.seek(max(0, path.stat().st_size - limit))
        return stream.read().decode("utf-8", errors="replace")


def hardware_snapshot(root=ROOT):
    """Laat een apart proces de echte lokale GPU-controle uitvoeren en lees het resultaat."""
    result = subprocess.run(
        [sys.executable, "-m", "football_pipeline.training_hardware"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        return json.loads(result.stdout)
    except ValueError:
        return {"ready": False, "error": (result.stderr or result.stdout)[-2000:]}
