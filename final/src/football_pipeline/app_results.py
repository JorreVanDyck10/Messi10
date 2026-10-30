"""Shared result view for automatic and manually configured analyses."""

import re
from datetime import UTC, datetime
from pathlib import Path

import streamlit as st

from .contracts import PipelineError, read_json

RESULT_ID = re.compile(r"[0-9a-f]{64}(?:-[0-9a-f]{8})?")


def linked_result(root, identifier):
    """Resolve only a completed, direct child of the configured results root."""
    from pathlib import Path

    from .contracts import PipelineError, RunResult
    from .pipeline import validate_completed

    if not RESULT_ID.fullmatch(identifier):
        raise PipelineError("Ongeldige analyselink.")
    root = Path(root).resolve()
    directory = (root / identifier).resolve()
    if directory.parent != root:
        raise PipelineError("Analyse ligt buiten de uitvoermap.")
    return RunResult(directory, validate_completed(directory), reused=True)


def saved_analyses(root):
    """List lightweight metadata; verify the selected result before opening it."""
    root = Path(root).resolve()
    found = []
    for path in root.glob("*/runmanifest.json"):
        directory = path.parent.resolve()
        if directory.parent != root or not RESULT_ID.fullmatch(directory.name):
            continue
        try:
            manifest = read_json(path)
            if manifest.get("status") != "completed":
                continue
            timestamp = str(manifest.get("completed_at", manifest.get("started_at", "")))
            try:
                moment = datetime.fromisoformat(timestamp)
                if moment.tzinfo is None:
                    moment = moment.replace(tzinfo=UTC)
                moment = moment.astimezone(UTC)
                date = moment.strftime("%d/%m/%Y %H:%M UTC")
            except ValueError:
                moment = datetime.min.replace(tzinfo=UTC)
                date = "Datum onbekend"
            mode = {"manual": "Handmatig", "automatic": "Automatisch"}.get(
                manifest.get("calibration_mode"), "Kalibratie onbekend"
            )
            video = manifest.get("video", {})
            duration = video.get("duration_s") if isinstance(video, dict) else None
            duration_text = f" · {duration:.1f} s" if type(duration) in (int, float) else ""
            found.append(
                {
                    "directory": directory,
                    "timestamp": timestamp,
                    "sort_time": moment,
                    "label": f"{date} · {mode}{duration_text} · {directory.name[:12]}",
                }
            )
        except (PipelineError, OSError):
            continue
    return sorted(found, key=lambda item: (item["sort_time"], item["directory"].name), reverse=True)


def show_saved_analyses(root):
    with st.expander("Opgeslagen analyses"):
        browse = st.checkbox("Een eerdere analyse openen", key="open_saved_analysis")
        if browse:
            items = saved_analyses(root)
            if not items:
                st.info("Er zijn nog geen voltooide analyses in deze uitvoermap.")
                st.stop()
            lookup = {item["directory"]: item["label"] for item in items}
            selected = st.selectbox(
                "Kies een analyse", list(lookup), format_func=lookup.get, key="saved_analysis"
            )
            refresh = st.button("Opnieuw laden", key="refresh_saved_analysis")
    if not browse:
        return
    try:
        if refresh or st.session_state.get("history_selection") != str(selected):
            st.session_state.history_result = linked_result(root, selected.name)
            st.session_state.history_selection = str(selected)
        # Browsing must not replace the active upload's result or run new processing.
        show_result(st.session_state.history_result, team_controls=False)
    except (PipelineError, OSError) as exc:
        st.error(f"Deze opgeslagen analyse kan niet worden geopend: {exc}")
    st.stop()


def show_result(result, *, team_controls=True):
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
                st.metric("Bronbeeld", f"{video['width']} Ã— {video['height']}", border=True)
            with st.container(border=True):
                st.video(str(result.video_path))
                st.caption(
                    "Video en tactical map delen dezelfde tijdlijn. Afspelen, pauzeren en zoeken blijven gesynchroniseerd."
                )
            from .result_inspection import show_saved_frame

            show_saved_frame(result)
            st.caption(
                "Bij ontbrekende veldherkenning worden trajecten en afstandsmetingen onderbroken. Speler-IDâ€™s zijn tijdelijk."
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
            if team_controls and result.manifest.get("team_settings") is not None:
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
            "De verwerkingstijd betreft deze teamcorrectie; detectie, veldposities en speler-IDâ€™s zijn hergebruikt."
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
