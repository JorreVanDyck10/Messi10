"""Training controls stay responsive while a separate local worker uses the GPU."""

import os
import subprocess
import sys
import time

import streamlit as st

from .contracts import PipelineError, read_json, write_json
from .training_workbench import (
    TASKS,
    check_inputs,
    default_inputs,
    hardware_snapshot,
    jobs,
    launch,
    local_path,
    stop_after_model,
    tail,
    training_processes,
)
from .video import ROOT


@st.fragment(run_every="5s")
def show_jobs():
    for directory, job in jobs()[:5]:
        if job.get("technical_only"):
            continue
        with st.container(border=True):
            label = {
                "starting": "Starten",
                "running": "Bezig",
                "complete": "Klaar",
                "failed": "Mislukt",
                "stopped": "Gestopt",
                "interrupted": "Onderbroken",
            }.get(job["status"], job["status"])
            current = TASKS.get(job.get("current_model"), "")
            st.markdown(f"**{label} · {current or 'trainingsronde'}**")
            st.progress(
                len(job.get("completed", [])) / max(1, len(job["tasks"])),
                text=f"{len(job.get('completed', []))}/{len(job['tasks'])} modellen afgerond",
            )
            if job.get("error"):
                st.error(job["error"])
            if job["status"] in {"starting", "running"}:
                if st.button("Stop na dit model", key=f"stop_{directory.name}"):
                    stop_after_model(directory)
                    st.info("Het huidige model mag afronden; volgende modellen starten niet.")
            if job.get("completed"):
                st.caption(f"Gewichten en metingen: {directory}")
                st.caption(
                    "Nieuwe gewichten zijn kandidaten. De analyse blijft het gekozen bestaande profiel gebruiken."
                )
                if job["status"] not in {"starting", "running"}:
                    if st.button("Exporteer modelgewichten", key=f"export_{directory.name}"):
                        try:
                            target = ROOT / "artifacts/training-transfers" / f"modellen-{directory.name}.zip"
                            start_transfer("export-models", target, {}, job=directory)
                            st.info(f"Modelpakket wordt gemaakt: {target}")
                        except (PipelineError, OSError) as exc:
                            st.error(str(exc))
            with st.expander("Voortgang en trainingslog"):
                st.code(tail(directory / "worker.log"), language="text")


def start_transfer(action, source, inputs, job=None):
    directory = ROOT / "artifacts/training-transfers"
    directory.mkdir(parents=True, exist_ok=True)
    tag = str(time.time_ns())
    config, log = directory / f"{tag}-inputs.json", directory / f"{tag}.log"
    write_json(config, inputs)
    command = [sys.executable, "-u", "-m", "football_pipeline.training_transfer", action, str(source)]
    if action == "export":
        command += ["--inputs", str(config)]
    if action == "export-models":
        command += ["--job", str(job)]
    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(ROOT),
    }
    with log.open("ab") as stream:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    st.session_state.training_transfer = {
        "pid": process.pid,
        "log": str(log),
        "path": str(source),
        "action": action,
    }


@st.fragment(run_every="5s")
def show_transfer():
    from pathlib import Path

    if transfer := st.session_state.get("training_transfer"):
        text = tail(Path(transfer["log"]))
        st.caption(f"Trainingspakket: {transfer['path']}")
        st.code(text or "Pakket wordt voorbereid…", language="text")


def training_page():
    st.title("Modellen trainen")
    st.write(
        "Train op de GPU van de computer waarop je deze app start. Iedere laptop kan een eigen model trainen."
    )
    st.caption(
        "Verder trainen vanaf bestaande gewichten. Data en instellingen bepalen de nauwkeurigheid; een sterkere GPU biedt vooral meer rekencapaciteit."
    )
    if st.button("Controleer deze GPU", icon=":material/memory:"):
        with st.spinner("GPU en echte trainingsberekening controleren…"):
            try:
                st.session_state.training_hardware = hardware_snapshot()
            except (OSError, subprocess.TimeoutExpired) as exc:
                st.session_state.training_hardware = {"ready": False, "error": str(exc)}
    hardware = st.session_state.get("training_hardware", {})
    if hardware.get("ready"):
        gpu = hardware["gpus"][0]
        st.success(f"{gpu['name']} · {gpu['memory_gib']} GB · klaar om te trainen")
    elif hardware:
        st.error(hardware.get("error", "GPU-controle niet geslaagd"))
        st.caption(
            "Op een nieuwe laptop: voer scripts/Setup-Laptop.ps1 uit. De RTX 50-installatie gebruikt CUDA 12.8."
        )
    else:
        st.info("Controleer eerst de GPU om de trainingsknoppen te gebruiken.")
    busy = bool(training_processes())
    if busy:
        st.info("Er draait al een training op deze laptop. De voortgang hieronder blijft beschikbaar.")
    defaults = default_inputs()
    imported = ROOT / ".cache/training-import.json"
    if imported.exists():
        defaults.update(read_json(imported).get("inputs", {}))
    with st.form("training_settings"):
        epochs = st.number_input("Maximum epochs", min_value=1, max_value=300, value=20)
        minutes = st.number_input(
            "Maximum trainingstijd per model (minuten)", min_value=1, max_value=1440, value=60
        )
        with st.expander("Trainingsdata en startprofiel"):
            labels = {
                "players": "Spelersdataset",
                "ball": "Baldataset",
                "appearance": "Shirt- en rolfeatures",
                "context_dataset": "Contextdataset",
                "field": "Veldindex",
                "profile": "Startprofiel",
            }
            inputs = {
                key: st.text_input(label, value=defaults[key], key=f"training_input_{key}")
                for key, label in labels.items()
            }
        st.caption(
            "Spelers: 1920 px · bal: 640 px · veld: 960 × 540. Batchgrootte daalt bij onvoldoende VRAM. De veldnetwerken trainen afzonderlijk."
        )
        st.caption(
            "Datacontrole en featureberekening vallen buiten het trainingsbudget. Shirtkenmerken gebruiken trainingsstappen in plaats van epochs."
        )
        submitted = None
        with st.container(horizontal=True):
            for key, name in TASKS.items():
                if st.form_submit_button(f"Train {name.lower()}", disabled=not hardware.get("ready") or busy):
                    submitted = [key]
        if st.form_submit_button("Train veldmodel volledig", disabled=not hardware.get("ready") or busy):
            submitted = ["field_points", "field_lines"]
        if st.form_submit_button("Alles trainen", type="primary", disabled=not hardware.get("ready") or busy):
            submitted = list(TASKS)
        if submitted:
            try:
                path = launch(submitted, inputs, epochs=int(epochs), minutes=int(minutes))
                st.success(f"Training gestart: {path.name}. Je kunt deze pagina sluiten en later terugkomen.")
            except (PipelineError, OSError) as exc:
                st.error(str(exc))
    show_jobs()
    with st.expander("Trainen op een andere laptop"):
        st.write(
            "Gebruik een eigen checkout en voer Setup-Laptop.ps1 en Start-Laptop.ps1 uit. Deel de trainingsdata met het pakket hieronder; virtuele omgevingen worden lokaal opgebouwd."
        )
        export_path = st.text_input(
            "Nieuw deelpakket", value="artifacts/training-transfers/trainingsdata.zip"
        )
        if st.button("Maak trainingspakket"):
            try:
                issues = check_inputs(list(TASKS), inputs)
                # The recipient builds its own field environment; source files must exist here.
                issues = [issue for issue in issues if not issue.startswith("Veldomgeving ontbreekt")]
                if issues:
                    raise PipelineError("\n".join(issues))
                start_transfer("export", local_path(export_path), inputs)
            except (PipelineError, OSError) as exc:
                st.error(str(exc))
        import_path = st.text_input("Gekopieerd pakket op deze laptop", value="")
        if st.button("Importeer data of modelgewichten", disabled=not import_path):
            try:
                source = local_path(import_path)
                if not source.is_file():
                    raise PipelineError("Dit pakket is niet gevonden")
                start_transfer("import", source, inputs)
            except (PipelineError, OSError) as exc:
                st.error(str(exc))
        show_transfer()
