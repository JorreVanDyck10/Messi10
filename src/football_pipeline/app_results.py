"""Shared result view for automatic and manually configured analyses."""

import streamlit as st


def linked_result(root, identifier):
    """Resolve only a completed, direct child of the configured results root."""
    import re
    from pathlib import Path

    from .contracts import PipelineError, RunResult
    from .pipeline import validate_completed

    if not re.fullmatch(r"[0-9a-f]{64}", identifier):
        raise PipelineError("Ongeldige analyselink.")
    root = Path(root).resolve()
    directory = (root / identifier).resolve()
    if directory.parent != root:
        raise PipelineError("Analyse ligt buiten de uitvoermap.")
    return RunResult(directory, validate_completed(directory), reused=True)


def show_result(result):
    st.subheader("Resultaat")
    st.success("Eerder voltooid resultaat hergebruikt." if result.reused else "Video volledig verwerkt.")
    st.link_button("Directe link naar deze analyse", f"?run={result.directory.name}")
    st.video(str(result.video_path))
    metrics = result.manifest["measurements"]
    with st.container(horizontal=True):
        st.metric("Verwerkingstijd", f"{metrics['runtime_s']:.1f} s")
        st.metric("Verwerkingssnelheid", f"{metrics['processing_fps']:.2f} fps")
        st.metric("Proces-RAM (bemonsterd)", f"{metrics['peak_process_ram_bytes_sampled'] / 2**20:.0f} MiB")
    if result.manifest.get("calibration_mode") == "automatic":
        st.metric("Frames met bruikbare veldkalibratie", f"{metrics['calibration_usable_fraction']:.1%}")
        st.caption(
            "Bij onbekende veldherkenning blijven beeld-ID’s zichtbaar; de minimap onderbreekt de trajecten."
        )
        from .field_review_ui import visual_review

        if st.checkbox("Beeld en veld per frame bekijken", key="automatic_frame_review"):
            visual_review(result.directory)
    if result.manifest.get("team_settings") is not None:
        from .team_ui import show_teams

        show_teams(result)
    if metrics.get("runtime_kind") == "team_render_only":
        st.caption(
            "De verwerkingstijd betreft deze teamcorrectie; detectie, veldposities en speler-ID’s zijn hergebruikt."
        )
    with st.expander("Bestanden en analysedetails"):
        st.caption(f"Uitvoermap: {result.directory}")
        for name, description, mime in (
            ("samengestelde_video.mp4", "Video downloaden", "video/mp4"),
            ("framegegevens.jsonl", "Framegegevens downloaden", "application/x-ndjson"),
            ("runmanifest.json", "Runmanifest downloaden", "application/json"),
            ("teamtelling.csv", "Teamtelling downloaden", "text/csv"),
            ("teaminstellingen.json", "Teaminstellingen downloaden", "application/json"),
            ("teamcorrecties.json", "Teamcorrecties downloaden", "application/json"),
        ):
            if not (result.directory / name).is_file():
                continue
            with (result.directory / name).open("rb") as stream:
                st.download_button(description, stream, file_name=name, mime=mime, key=f"download_{name}")
