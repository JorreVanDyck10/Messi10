"""Toont bronframe, veldprojectie en minimap op hetzelfde tijdstip voor visuele review."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np
import streamlit as st

from .calibration_input import point_label
from .contracts import Detection, FrameRecord, PipelineError, read_json
from .field_layout import POINTS_UV
from .field_motion import status_label
from .field_review import failure_intervals, finalize_review, save_review
from .pipeline import validate_completed
from .point_picker import apply_point_click, point_picker
from .render import render_frame
from .video import ROOT, inspect_video, read_frame


@st.cache_data(max_entries=4, show_spinner=False)
def review_records(directory, manifest_mtime, records_mtime):
    manifest = validate_completed(Path(directory))
    rows = [
        json.loads(line)
        for line in (Path(directory) / "framegegevens.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    return manifest, rows


@st.cache_data(max_entries=8, show_spinner=False)
def source_frame(path, video_hash, index):
    video = inspect_video(path)
    if video.sha256 != video_hash:
        raise PipelineError("Het oorspronkelijke videobestand is gewijzigd.")
    return read_frame(video, index)


def visual_review(directory):
    directory = Path(directory)
    manifest, rows = review_records(
        str(directory),
        (directory / "runmanifest.json").stat().st_mtime_ns,
        (directory / "framegegevens.jsonl").stat().st_mtime_ns,
    )
    if manifest.get("calibration_mode") != "automatic":
        return
    st.subheader("Zelf het veld controleren")
    st.warning(
        "Experimentele veldkalibratie. Menselijke nauwkeurigheid en de 90%-doelstelling zijn nog te beoordelen."
    )
    token = manifest["cache_key"][:12]
    frame_key = f"review_frame_{token}"
    intervals = failure_intervals(rows)
    failed = st.selectbox(
        "Mislukte intervallen — kies en spring",
        [None, *intervals],
        format_func=lambda item: (
            "Kies een interval"
            if item is None
            else f"{item[0] / manifest['video']['fps_num'] * manifest['video']['fps_den']:.2f}–{(item[1] + 1) / manifest['video']['fps_num'] * manifest['video']['fps_den']:.2f} s (frames {item[0]}–{item[1]})"
        ),
        key=f"failed_{token}",
    )
    if st.button("Spring naar mislukt interval", disabled=failed is None, key=f"jump_{token}"):
        st.session_state[frame_key] = failed[0]
    selection_path = ROOT / "configs/broadcast-field-selection.json"
    selection = read_json(selection_path) if selection_path.is_file() else None
    if selection and selection["video_sha256"] != manifest["video"]["sha256"]:
        selection = None
    role = st.segmented_control(
        "Referentieset", ["Ontwikkeling", "Beoordeling"], default="Ontwikkeling", key=f"role_{token}"
    )
    indices = (
        selection["development_indices" if role == "Ontwikkeling" else "evaluation_indices"]
        if selection
        else []
    )
    if indices:
        chosen = st.selectbox("Vooraf gekozen referentieframe", indices, key=f"reference_{token}_{role}")
        if st.button("Spring naar referentieframe", key=f"reference_jump_{token}_{role}"):
            st.session_state[frame_key] = chosen
    index = st.slider("Exact bronframe", 0, len(rows) - 1, key=frame_key)
    row = rows[index]
    state = row["calibration"]
    st.markdown(f"**{status_label(state)}** · frame {index} · {row['timestamp_s']:.3f} s")
    age = state.get("age_s")
    st.caption(
        f"Punten: {len(state.get('points', []))} · Afwijsreden herkenning: {state.get('recognition_status', state['status'])} · Sinds laatste herkenning: {age:.2f} s"
        if age is not None
        else f"Punten: {len(state.get('points', []))} · Afwijsreden: {state['status']}"
    )
    recognized = st.checkbox("Herkende punten tonen (geel)", value=True, key=f"recognized_{token}")
    tracked = st.checkbox("Gevolgde grasveldkenmerken tonen (paars)", value=True, key=f"tracked_{token}")
    try:
        frame = source_frame(manifest["video"]["path"], manifest["video"]["sha256"], index)
    except (OSError, PipelineError) as exc:
        st.error(f"Oorspronkelijke video nodig voor framecontrole: {exc}")
        return
    record = FrameRecord(
        index,
        row["timestamp_s"],
        tuple(row["image_size"]),
        [Detection.from_dict(d) for d in row["detections"]],
        state,
        player_model_available=row.get(
            "player_model_available",
            any("player" in spec["class_mapping"].values() for spec in manifest["models"]["models"]),
        ),
        team_context=row.get("team_context"),
    )
    st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), caption="Oorspronkelijk beeld — zonder modeloverlay")
    st.image(
        cv2.cvtColor(
            render_frame(frame, record, recognized_points=recognized, tracked_points=tracked),
            cv2.COLOR_BGR2RGB,
        ),
        caption="Veld-overlay en minimap van exact hetzelfde frame; blauw = teruggeprojecteerde veldlijnen",
    )
    with st.expander("Geometrie en camerabeweging"):
        st.json(
            {
                "quality": state.get("quality"),
                "motion_quality": state.get("motion_quality"),
                "reference_frame": state.get("reference_frame"),
            }
        )
    if not selection or index not in indices:
        st.caption("Handmatige referenties worden alleen opgeslagen op de vooraf geselecteerde frames.")
        return
    st.markdown("**Jouw referentiepunten**")
    st.caption(
        "Klik zichtbare bekende veldpunten op het oorspronkelijke beeld. Deze klikpunten gaan uitsluitend naar een apart beoordelingsbestand."
    )
    tuning = role == "Ontwikkeling"
    frozen = tuning or st.checkbox(
        "Ik zet deze instellingen vast vóór ik de beoordelingsreferenties invoer", key=f"freeze_{token}"
    )
    freeze_time_key = f"freeze_time_{token}"
    if frozen and not tuning and freeze_time_key not in st.session_state:
        st.session_state[freeze_time_key] = datetime.now(UTC).isoformat()
    path = (
        ROOT
        / "data/field-reviews"
        / manifest["video"]["sha256"]
        / f"{manifest['calibration_id']}-{'development' if tuning else 'evaluation'}.json"
    )
    existing = read_json(path) if path.is_file() else None
    key = f"human_points_{token}_{role}_{index}"
    if key not in st.session_state:
        saved = next(
            (f["points"] for f in (existing or {}).get("frames", []) if f["frame_index"] == index), []
        )
        saved = {p["id"]: p for p in saved}
        st.session_state[key] = [
            {
                "id": identifier,
                "name": f"{point_label({'u': uv[0], 'v': uv[1], 'name': f'PnL-punt {identifier}'})} · #{identifier}",
                "u": uv[0],
                "v": uv[1],
                "role": "control",
                "x": saved.get(identifier, {}).get("x"),
                "y": saved.get(identifier, {}).get("y"),
            }
            for identifier, uv in POINTS_UV.items()
        ]
    points = st.session_state[key]
    selected = st.selectbox(
        "Bekend vlak veldpunt",
        range(len(points)),
        format_func=lambda i: points[i]["name"],
        key=f"landmark_{token}_{role}_{index}",
    )
    # A canonical diagram makes semantic IDs identifiable without looking at model predictions.
    diagram = np.full((400, 650, 3), (35, 75, 40), dtype="uint8")
    from .field_layout import LINES_UV

    for ends in LINES_UV.values():
        a, b = [tuple(round(v) for v in (30 + 590 * p[0], 30 + 340 * p[1])) for p in ends]
        cv2.line(diagram, a, b, (200, 220, 205), 1)
    for i, p in enumerate(points):
        xy = (round(30 + 590 * p["u"]), round(30 + 340 * p["v"]))
        cv2.circle(
            diagram, xy, 5 if i == selected else 2, (40, 220, 255) if i == selected else (180, 180, 180), -1
        )
        cv2.putText(
            diagram, str(p["id"]), (xy[0] + 3, xy[1] - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (240, 240, 240), 1
        )
    st.image(
        cv2.cvtColor(diagram, cv2.COLOR_BGR2RGB),
        caption="Standaardveld 105 × 68 als geometrische aanname; geel = geselecteerd referentiepunt",
    )
    context = f"{token}:{role}:{index}:{selected}"
    picker_key = f"human_picker_{token}"

    def clicked():
        try:
            st.session_state[key] = apply_point_click(
                st.session_state[key],
                st.session_state[picker_key].clicked,
                context=context,
                selected=selected,
                width=frame.shape[1],
                height=frame.shape[0],
            )
        except PipelineError as exc:
            st.session_state[f"click_error_{token}"] = str(exc)

    point_picker(frame, points, selected, context=context, key=picker_key, on_clicked_change=clicked)
    if st.session_state.get(f"click_error_{token}"):
        st.error(st.session_state.pop(f"click_error_{token}"))
    if st.button("Geselecteerd klikpunt wissen", key=f"clear_point_{token}"):
        st.session_state[key][selected].update(x=None, y=None)
        st.rerun()
    st.caption(f"{sum(p['x'] is not None for p in st.session_state[key])} punten zelf aangewezen")
    reviewer = st.text_input("Jouw naam als beoordelaar", key=f"reviewer_{token}")
    possible = st.segmented_control(
        "Is dit frame kalibreerbaar?",
        ["Nog niet beoordeeld", "Ja", "Nee"],
        default="Nog niet beoordeeld",
        key=f"possible_{token}_{index}_{role}",
    )
    if st.button(
        "Mijn beoordeling van dit frame opslaan",
        disabled=not frozen or not reviewer.strip() or possible == "Nog niet beoordeeld",
        key=f"save_review_{token}",
    ):
        template = {
            "schema_version": 1,
            "video_sha256": selection["video_sha256"],
            "image_size": row["image_size"],
            "selection_frozen_at": selection["selection_frozen_at"],
            "selected_frame_indices": indices,
            "source": selection["source"],
            "usage": selection["usage"],
            "used_for_tuning": tuning,
            "calibration_id": manifest["calibration_id"],
            "settings_frozen_at": st.session_state.get(freeze_time_key) if not tuning else None,
            "settings": manifest.get("field_settings"),
        }
        try:
            existing = save_review(
                path,
                template,
                index=index,
                points=st.session_state[key],
                calibratable=possible == "Ja",
                reviewer=reviewer,
                confirmed=True,
            )
            st.success(f"Jouw beoordeling opgeslagen: {len(existing['frames'])}/{len(indices)} frames.")
        except PipelineError as exc:
            st.error(str(exc))
    if existing:
        st.caption(f"Apart referentiebestand: {path} · {len(existing['frames'])}/{len(indices)} beoordeeld")
        confirm = st.checkbox(
            "Ik bevestig dat ik de volledige referentieset zelf heb beoordeeld",
            key=f"confirm_set_{token}_{role}",
        )
        if st.button(
            "Volledige referentieset afronden",
            disabled=not confirm or len(existing["frames"]) != len(indices),
            key=f"finalize_{token}_{role}",
        ):
            finalize_review(path, confirmed=True)
            st.success("Referentieset expliciet menselijk bevestigd.")
            if not tuning:
                from .calibration_evaluation import evaluate_calibration
                from .contracts import write_json

                evaluation = evaluate_calibration(directory, path)
                report_path = path.with_suffix(".evaluation.json")
                write_json(report_path, evaluation)
                st.json(evaluation)
                st.caption(f"Gemeten rapport: {report_path}")
