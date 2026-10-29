"""Toont opgeslagen analysevideo, instellingen en uitvoerbestanden in de interface."""

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
    metrics = result.manifest["measurements"]
    st.subheader("Wedstrijdanalyse")
    with st.container(horizontal=True, vertical_alignment="center"):
        st.badge("Analyse voltooid", icon=":material/check_circle:", color="green")
        st.link_button(
            "Directe link naar deze analyse", f"?run={result.directory.name}", icon=":material/link:"
        )
    overview, players, teams, details = st.tabs(
        ["Overzicht", "Spelers en afstanden", "Teams", "Details en downloads"],
        key="result_view",
        default=st.session_state.get("active_result_view", "Overzicht"),
        on_change="rerun",
    )
    # Preserve the selected view when widgets are cleaned up while navigating away.
    st.session_state.active_result_view = st.session_state.result_view
    if overview.open:
        with overview:
            video = result.manifest["video"]
            with st.container(horizontal=True):
                st.metric("Clipduur", f"{video['duration_s']:.1f} s", border=True)
                if result.manifest.get("calibration_mode") == "automatic":
                    st.metric(
                        "Bruikbare veldkalibratie",
                        f"{metrics['calibration_usable_fraction']:.1%}",
                        border=True,
                    )
                st.metric("Bronbeeld", f"{video['width']} × {video['height']}", border=True)
            with st.container(border=True):
                st.video(str(result.video_path))
                st.caption(
                    "Video en tactical map delen dezelfde tijdlijn. Afspelen, pauzeren en zoeken blijven gesynchroniseerd."
                )
            st.caption(
                "Bij ontbrekende veldherkenning worden trajecten en afstandsmetingen onderbroken. Speler-ID’s zijn tijdelijk."
            )
            if result.manifest.get("calibration_mode") == "automatic":
                from .field_review_ui import visual_review

                if st.checkbox("Beeld en veld per frame bekijken", key="automatic_frame_review"):
                    visual_review(result.directory)
    if players.open:
        with players:
            from .distance_ui import distance_panel

            distance_panel(result)
    if teams.open:
        with teams:
            if result.manifest.get("team_settings") is not None:
                from .team_ui import show_teams

                show_teams(result)
            else:
                st.info("Deze analyse bevat geen teamindeling. Kies een analyse met teamherkenning.")
    if details.open:
        with details:
            show_details(result)


def show_details(result):
    metrics = result.manifest["measurements"]
    st.caption("Eerder voltooid resultaat hergebruikt." if result.reused else "Video volledig verwerkt.")
    with st.container(horizontal=True):
        st.metric("Verwerkingstijd", f"{metrics['runtime_s']:.1f} s", border=True)
        st.metric("Verwerkingssnelheid", f"{metrics['processing_fps']:.2f} fps", border=True)
        st.metric(
            "Proces-RAM (bemonsterd)",
            f"{metrics['peak_process_ram_bytes_sampled'] / 2**20:.0f} MiB",
            border=True,
        )
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
