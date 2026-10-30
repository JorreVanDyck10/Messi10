"""Read saved output frames and coordinates without running detection again."""

from __future__ import annotations

import json
import math
from pathlib import Path

import cv2
import pandas as pd
import streamlit as st

from .contracts import PipelineError
from .render import LABELS


@st.cache_data(max_entries=4, show_spinner=False)
def record_offsets(path: str, size: int, modified_ns: int) -> list[int]:
    # Size and modification time invalidate the cache when the saved file changes.
    offsets = []
    with Path(path).open("rb") as stream:
        while True:
            offset = stream.tell()
            line = stream.readline()
            if not line:
                break
            if not line.strip():
                raise PipelineError("De opgeslagen framegegevens bevatten een lege regel.")
            offsets.append(offset)
    return offsets


def saved_record(path: Path, index: int, offsets: list[int]) -> dict:
    if type(index) is not int or not 0 <= index < len(offsets):
        raise PipelineError("Dit frame bestaat niet in de opgeslagen analyse.")
    try:
        with path.open("rb") as stream:
            stream.seek(offsets[index])
            record = json.loads(stream.readline())
        if (
            not isinstance(record, dict)
            or type(record.get("frame_index")) is not int
            or record["frame_index"] != index
        ):
            raise ValueError("Framevolgorde komt niet overeen.")
        timestamp = record.get("timestamp_s")
        if type(timestamp) not in (int, float) or not math.isfinite(timestamp) or timestamp < 0:
            raise ValueError("Het opgeslagen tijdstip is ongeldig.")
        if not isinstance(record.get("detections"), list) or any(
            not isinstance(detection, dict) for detection in record["detections"]
        ):
            raise ValueError("Detectiegegevens ontbreken of zijn ongeldig.")
        return record
    except (OSError, ValueError) as exc:
        raise PipelineError(f"Opgeslagen framegegevens kunnen niet worden gelezen: {exc}") from exc


@st.cache_data(max_entries=6, show_spinner=False)
def saved_video_frame(path: str, size: int, modified_ns: int, index: int):
    if type(index) is not int or index < 0:
        raise PipelineError("Kies een geldig framenummer.")
    capture = cv2.VideoCapture(path)
    try:
        capture.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = capture.read()
        if not ok:
            raise PipelineError(f"Frame {index} kan niet uit de uitvoervideo worden gelezen.")
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    finally:
        capture.release()


def position_table(record: dict) -> pd.DataFrame:
    statuses = {
        "valid": "Op het veld",
        "outside_field": "Buiten het veld",
        "truncated_bottom": "Onderkant afgesneden",
        "invalid_box": "Ongeldige box",
        "invalid_transform": "Ongeldige projectie",
        "not_ground_projected": "Geen grondprojectie",
    }
    rows = []
    for detection in record["detections"]:
        position = detection.get("field_position")
        coordinates_valid = (
            isinstance(position, (list, tuple))
            and len(position) == 2
            and all(
                type(value) in (int, float) and math.isfinite(value) and -1e-9 <= value <= 1 + 1e-9
                for value in position
            )
        )
        valid = detection.get("projection_status") == "valid" and coordinates_valid
        status = statuses.get(detection.get("projection_status"), "Onbekend")
        if detection.get("projection_status") == "valid" and not coordinates_valid:
            status = "Ongeldige coördinaten"
        counted = detection.get("counted_as_player")
        rows.append(
            {
                "Frame": record["frame_index"],
                "Tijd (s)": record["timestamp_s"],
                "Detectie": detection.get("detection_id", ""),
                "Rol": LABELS.get(detection.get("semantic_class"), "Onbekende rol"),
                "Track-ID": detection.get("track_id"),
                "Confidence": detection.get("confidence"),
                "u": position[0] if valid else None,
                "v": position[1] if valid else None,
                "Veldpositie": status,
                "Telt als speler": "Ja"
                if counted is True
                else "Nee"
                if counted is False
                else "Niet opgeslagen",
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "Frame",
            "Tijd (s)",
            "Detectie",
            "Rol",
            "Track-ID",
            "Confidence",
            "u",
            "v",
            "Veldpositie",
            "Telt als speler",
        ],
    )


def show_saved_frame(result):
    """Inspect the encoded video and saved records, including manual school runs."""
    token = result.directory.name
    if not st.checkbox("Een exact frame en de veldposities bekijken", key=f"inspect_frame_{token}"):
        return
    try:
        path = result.directory / "framegegevens.jsonl"
        stat = path.stat()
        offsets = record_offsets(str(path), stat.st_size, stat.st_mtime_ns)
        if not offsets:
            raise PipelineError("Deze analyse bevat geen opgeslagen frames.")
        index = (
            st.slider("Frame in de uitvoervideo", 0, len(offsets) - 1, key=f"inspect_index_{token}")
            if len(offsets) > 1
            else 0
        )
        record = saved_record(path, index, offsets)
        timestamp = float(record["timestamp_s"])
        st.caption(f"Frame {index} · {timestamp:.3f} seconden · beeld en gegevens van hetzelfde moment.")
        video_stat = result.video_path.stat()
        frame = saved_video_frame(str(result.video_path), video_stat.st_size, video_stat.st_mtime_ns, index)
        st.image(
            frame,
            caption="Opgeslagen uitvoer met dezelfde detecties en minimap; er wordt niets opnieuw geanalyseerd.",
        )
        summary = record.get("player_summary", {})
        if "on_field" in summary:
            count = summary["on_field"]
            st.metric("Spelers op het veld in dit frame", "Onbekend" if count is None else str(count))
        table = position_table(record)
        if table.empty:
            st.info("In dit frame zijn geen detecties opgeslagen.")
        else:
            st.dataframe(table, hide_index=True)
        st.caption(
            "u en v lopen van 0 tot 1 over het veld; dit zijn geen meters. "
            "Onbekende posities blijven leeg. Niet elke opgeslagen detectie telt mee of is zichtbaar in de video."
        )
        st.download_button(
            "Gegevens van dit frame downloaden (CSV)",
            table.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"frame_{index:06d}.csv",
            mime="text/csv",
            key=f"frame_csv_{token}",
        )
    except (PipelineError, OSError, ValueError, KeyError, TypeError) as exc:
        st.error(f"Framecontrole niet beschikbaar: {exc}")
