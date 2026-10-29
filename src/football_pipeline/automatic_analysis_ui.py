"""Verbindt upload, automatische verwerking en resultaatweergave in de Streamlit-app."""

import os
from pathlib import Path

import streamlit as st

from .app_results import show_result
from .contracts import PipelineError, digest_json, read_json, sha256_file
from .detection import load_model_manifest, player_detection_sources, validate_detection_devices
from .pipeline import code_identity, process_video
from .teams import configured_team_path
from .video import ROOT


def automatic_analysis(video, upload_name, output_root):
    st.subheader("Automatische analyse")
    st.caption("Veldherkenning · teams · speler-ID’s · telling per team · trajecten op de minimap")
    default_models = ROOT / "configs/models-broadcast.json"
    if not default_models.is_file():
        default_models = ROOT / "configs/models-players.json"
    model_path = Path(os.environ.get("FOOTBALL_AUTO_MODELS", default_models))
    runtime = Path(os.environ.get("FOOTBALL_FIELD_RUNTIME", ROOT / ".tools/field-runtime.json"))
    try:
        models = load_model_manifest(model_path)
        team_path = configured_team_path(models)
        validate_detection_devices(models)
        if not player_detection_sources(models):
            raise PipelineError("Automatische speleranalyse vereist getrainde player-klassen.")
        field = read_json(runtime)
        field_weights = {
            name: [Path(field[name]).stat().st_size, Path(field[name]).stat().st_mtime_ns]
            for name in ("weights_keypoints", "weights_lines")
        }
        signature = digest_json(
            {
                "video": video.sha256,
                "upload_name": upload_name,
                "models": models,
                "runtime": field,
                "field_weights": field_weights,
                "worker": sha256_file(ROOT / "scripts/field_calibration_worker.py"),
                "tracker": sha256_file(ROOT / "configs/bytetrack.yaml"),
                "teams": sha256_file(team_path),
                "code": code_identity(),
            }
        )
    except (PipelineError, OSError, KeyError) as exc:
        st.error(f"Automatische analyse kan niet starten: {exc}")
        return

    st.caption(
        "Het spelersmodel kan spelers of officials missen. ID’s zijn tijdelijke volgnummers; "
        "bij camerawissels worden ze vernieuwd. Teams worden op shirtkleur voorgesteld; "
        "onzekere spelers blijven onbekend. Je kunt de indeling na analyse corrigeren."
    )
    if st.session_state.get("result_request_signature") != signature:
        st.session_state.pop("result", None)
    retry = False
    retry_visible = (
        st.session_state.get("automatic_last_attempt") == signature and "result" not in st.session_state
    )
    if retry_visible:
        st.warning("De vorige analyse is onderbroken of mislukt. Je kunt opnieuw proberen.")
        if st.session_state.get("automatic_error"):
            st.error(st.session_state.automatic_error)
        retry = st.button("Opnieuw proberen", key="automatic_retry", type="primary")
    if st.session_state.get("automatic_last_attempt") != signature or retry:
        st.session_state.automatic_last_attempt = signature
        bar = st.progress(0.0, text="Analyse voorbereiden…")

        def field_progress(count, total, elapsed):
            bar.progress(
                count / total * 0.5, text=f"Veld herkennen: {count}/{total} frames · {elapsed:.1f} s"
            )

        def player_progress(count, total, elapsed):
            bar.progress(
                0.5 + count / total * 0.5,
                text=f"Spelers volgen en minimap maken: {count}/{total} frames · {elapsed:.1f} s",
            )

        try:
            result = process_video(
                video.path,
                None,
                model_path,
                output_root,
                field_runtime_path=runtime,
                field_source=f"Gebruikersupload: {upload_name}",
                field_usage="Lokale analyse van een gebruikersupload; gebruiksrechten niet onafhankelijk gecontroleerd.",
                tracker_config_path=ROOT / "configs/bytetrack.yaml",
                team_config_path=team_path,
                progress=player_progress,
                field_progress=field_progress,
            )
            st.session_state.result = result
            st.session_state.pop("automatic_error", None)
            st.session_state.result_request_signature = signature
            bar.progress(1.0, text="Voltooid")
        except (PipelineError, OSError, ValueError, KeyError) as exc:
            st.session_state.automatic_error = f"Analyse niet voltooid: {exc}"
            st.error(st.session_state.automatic_error)
            if not retry_visible:
                st.button("Opnieuw proberen", key="automatic_retry", type="primary")
    if st.session_state.get("result") is not None:
        show_result(st.session_state.result)
