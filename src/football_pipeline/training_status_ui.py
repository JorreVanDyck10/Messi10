"""Small, independently refreshed status alongside the existing result player."""

import streamlit as st

from .contracts import PipelineError, read_json


@st.fragment(run_every="30s")
def show_training_status(directory, latest_demo=None):
    if latest_demo is not None and latest_demo.is_file():
        import re
        from pathlib import Path

        try:
            demo = read_json(latest_demo)
            identifier = demo.get("run_id", Path(demo.get("new_run", "")).name)
            st.caption("Spelers en teams bijgewerkt · analyse binnen het herkende veld.")
            if (re.fullmatch(r"[0-9a-f]{64}", identifier)
                    and (directory.parent.parent / "runs" / identifier / "runmanifest.json").is_file()):
                st.link_button("Nieuwe broadcastanalyse", f"?run={identifier}")
            return
        except (PipelineError, OSError):
            pass
    if not directory.is_dir():
        return
    if (directory / "finished.json").exists():
        st.caption("De gezamenlijke trainingsronde en demonstraties zijn voltooid.")
        import re
        from pathlib import Path

        demos = read_json(directory / "finished.json").get("demonstrations", {})
        for name, demo in demos.items():
            identifier = Path(demo["run_directory"]).name
            if re.fullmatch(r"[0-9a-f]{64}", identifier):
                label = {"broadcast": "Nieuwe broadcastanalyse", "panorama": "Nieuwe panoramaanalyse"}.get(
                    name, name
                )
                st.link_button(label, f"?run={identifier}")
        return
    labels = {"players": "Spelers", "roles": "Rollen", "ball": "Bal", "field": "Veld"}
    statuses = []
    for name, label in labels.items():
        path = directory / name / "job.json"
        try:
            job = read_json(path) if path.exists() else {}
        except PipelineError:
            job = {}
        status = {"running": "bezig", "complete": "klaar", "failed": "mislukt", "paused": "gepauzeerd"}.get(
            job.get("status"), "wacht"
        )
        statuses.append(f"{label}: {status}")
    st.caption("Nieuwe trainingsronde · " + " · ".join(statuses))
    ball_job = directory / "ball/job.json"
    if ball_job.exists() and read_json(ball_job).get("status") == "running":
        import csv

        for history in sorted((directory / "ball/training").glob("batch-*/results.csv")):
            with history.open() as stream:
                rows = list(csv.DictReader(stream))
            if rows:
                epoch = rows[-1].get("epoch", "?")
                st.caption(f"Baltraining: epoch {epoch} opgeslagen (maximaal 50).")
    field_progress = directory / "field/training/progress.json"
    field_job = directory / "field/job.json"
    if field_progress.exists() and field_job.exists() and read_json(field_job).get("status") == "running":
        p = read_json(field_progress)
        report = read_json(directory / "field/training/training-report.json")
        if report.get("status") == "complete":
            st.caption("Veld: geometrische vergelijking van de gewichten.")
        elif (
            p["role"] == "keypoints"
            and report.get("models", {}).get("keypoints", {}).get("status") == "complete"
        ):
            st.caption("Veldlijnen: beginmeting van de startgewichten.")
        else:
            role = {"keypoints": "veldpunten", "lines": "veldlijnen"}[p["role"]]
            st.caption(
                f"Training {role}: epoch {p['epoch']}/8 · {p['samples']}/{p['total_samples']} beelden · "
                f"resterend budget {p['remaining_minutes']:.1f} min."
            )
    st.caption("De opgeslagen video hieronder verandert pas wanneer een nieuwe analyse is geopend.")
