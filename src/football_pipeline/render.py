from __future__ import annotations

import cv2
import numpy as np

from .automatic_calibration import transform
from .contracts import FrameRecord
from .field_layout import LINES_UV
from .field_motion import status_label
from .geometry import valid_box
from .participants import DISPLAY_CONFIDENCE, player_summary, visible_detection
from .teams import UNKNOWN_COLOR, hex_rgb
from .tracking import Trajectories

COLORS = {
    "player": (185, 215, 65),
    "referee": (30, 170, 245),
    "assistant_referee": (20, 210, 245),
    "steward": (90, 130, 245),
    "spectator": (200, 145, 205),
    "staff": (160, 180, 210),
    "person": (225, 190, 120),
    "ball": (245, 245, 245),
}
LABELS = {
    "player": "speler",
    "referee": "scheids/lijnrechter",
    "assistant_referee": "lijnrechter",
    "steward": "steward",
    "spectator": "supporter",
    "staff": "staf",
    "person": "persoon",
    "ball": "bal",
}


def label(image, text, point, color=(235, 240, 235), scale=0.6):
    cv2.putText(image, text, point, cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)


def field_pixel(position):
    return round(40 + 560 * position[0]), round(170 + 360 * position[1])


def detection_color(detection, record):
    if detection.semantic_class == "player" and record.team_context:
        team = record.team_context["teams"].get(detection.team_id)
        return tuple(reversed(hex_rgb(team["display_color"] if team else UNKNOWN_COLOR)))
    return COLORS.get(detection.semantic_class, (190, 190, 190))


def detection_label(detection, record):
    if detection.semantic_class == "player" and record.team_context:
        team = record.team_context["teams"].get(detection.team_id)
        return team["name"][:24] if team else "team onbekend"
    return LABELS.get(detection.semantic_class, detection.semantic_class)


def render_frame(
    frame: np.ndarray,
    record: FrameRecord,
    histories: Trajectories | None = None,
    display_confidence: float = DISPLAY_CONFIDENCE,
    technical_pilot: bool = False,
    recognized_points: bool = True,
    tracked_points: bool = True,
) -> np.ndarray:
    canvas = np.full((720, 1920, 3), (22, 35, 29), dtype=np.uint8)
    h, w = frame.shape[:2]
    scale = min(1280 / w, 720 / h)
    target_w, target_h = round(w * scale), round(h * scale)
    source = (
        automatic_preview(
            frame, record.calibration, recognized_points=recognized_points, tracked_points=tracked_points
        )
        if record.calibration
        else frame
    )
    left = cv2.resize(source, (target_w, target_h), interpolation=cv2.INTER_AREA)
    offset_x, offset_y = (1280 - target_w) // 2, (720 - target_h) // 2
    for detection in record.detections:
        if not valid_box(detection, record.image_size):
            continue
        # Matched low-confidence observations remain visible with the same ID on both sides.
        if not visible_detection(detection, display_confidence):
            continue
        x1, y1, x2, y2 = [round(x * scale) for x in detection.bbox_xyxy]
        color = detection_color(detection, record)
        cv2.rectangle(left, (x1, y1), (x2, y2), color, 2)
        text = detection_label(detection, record)
        if detection.track_id is not None:
            text += f" #{detection.track_id}"
        label(left, f"{text} {detection.confidence:.2f}", (x1, max(18, y1 - 5)), color, 0.45)
    canvas[offset_y : offset_y + target_h, offset_x : offset_x + target_w] = left
    cv2.rectangle(canvas, (0, 0), (470, 42), (20, 30, 25), -1)
    stamp = f"Frame {record.frame_index} | {record.timestamp_s:.3f} s"
    label(canvas, stamp, (20, 28))
    if technical_pilot:
        label(canvas, "TECHNISCHE PILOT - personen, geen speler-ID's", (20, 65), (80, 205, 245), 0.65)
    pitch = canvas[:, 1280:]
    label(pitch, "PILOT MINIMAP" if technical_pilot else "TACTICAL MAP", (40, 52), scale=0.9)
    label(pitch, stamp, (40, 88))
    summary = player_summary(record, display_confidence)
    count = summary["on_field"]
    count_label = "Spelers op veld: onbekend" if count is None else f"Spelers op veld: {count} (detecties)"
    if not record.player_model_available:
        persons = summary["persons_on_field"]
        count_label = "Personen op veld: onbekend" if persons is None else f"Personen op veld: {persons}"
        count_label += " (rollen onbekend)"
    label(pitch, count_label, (40, 120), scale=0.6)
    if record.team_context:
        values = summary["by_team"]
        parts = [
            f"{team['name'][:14]}: {values[key] if values[key] is not None else '?'}"
            for key, team in record.team_context["teams"].items()
        ]
        parts.append(f"Onbekend: {values['unknown'] if values['unknown'] is not None else '?'}")
        label(pitch, " | ".join(parts), (40, 145), scale=0.44)
    cv2.rectangle(pitch, (40, 170), (600, 530), (40, 85, 52), -1)
    cv2.rectangle(pitch, (40, 170), (600, 530), (205, 225, 210), 2)
    cv2.line(pitch, (320, 170), (320, 530), (205, 225, 210), 2)
    cv2.circle(pitch, (320, 350), 45, (205, 225, 210), 1)
    label(pitch, "u: 0 -> 1 | Genormaliseerd veld - geen meters", (40, 558), scale=0.5)
    if record.calibration:
        known = record.calibration["status"] == "valid"
        label(
            pitch,
            status_label(record.calibration),
            (40, 578) if record.team_context else (40, 150),
            (100, 220, 180) if known else (80, 180, 245),
            scale=0.6,
        )
        state = record.calibration
        age = state.get("age_s")
        if record.team_context:
            age_text = f" | leeftijd {age:.2f} s" if age is not None else ""
            label(pitch, f"Veldpunten: {len(state.get('points', []))}{age_text}", (40, 598), scale=0.43)
        else:
            label(
                pitch,
                f"Punten: {len(state.get('points', []))} | {state.get('recognition_status', state['status'])}",
                (40, 578),
                scale=0.43,
            )
        if age is not None and not record.team_context:
            label(
                pitch,
                f"Sinds herkenning: {age:.2f} s | referentie {state.get('reference_frame')}",
                (40, 598),
                scale=0.43,
            )
    for detection in record.detections:
        if detection.field_position is None:
            continue
        if not visible_detection(detection, display_confidence):
            continue
        color = detection_color(detection, record)
        if histories is not None and detection.track_id is not None:
            for a, b in histories.segments(detection.track_id):
                cv2.line(pitch, field_pixel(a[1:]), field_pixel(b[1:]), color, 2, cv2.LINE_AA)
        point = field_pixel(detection.field_position)
        cv2.circle(pitch, point, 6, color, -1, cv2.LINE_AA)
        if detection.track_id is not None:
            label(pitch, str(detection.track_id), (point[0] + 8, point[1] - 6), color, 0.5)
    present_roles = {d.semantic_class for d in record.detections}
    legend = [
        role
        for role in COLORS
        if role in present_roles or (role == "player" and record.player_model_available)
    ]
    entries = [(COLORS[role], LABELS[role]) for role in legend if role != "player" or not record.team_context]
    if record.team_context:
        entries = (
            [
                (tuple(reversed(hex_rgb(t["display_color"]))), t["name"][:22])
                for t in record.team_context["teams"].values()
            ]
            + [(tuple(reversed(hex_rgb(UNKNOWN_COLOR))), "team onbekend")]
            + entries
        )
    for index, (color, text) in enumerate(entries):
        columns = 3 if record.team_context else 2
        x, y = 40 + (index % columns) * (185 if record.team_context else 280), 618 + (index // columns) * 22
        cv2.circle(pitch, (x, y - 5), 5, color, -1)
        label(pitch, text, (x + 12, y), scale=0.38 if record.team_context else 0.5)
    label(
        pitch,
        "Menselijke review: nog open" if technical_pilot else "Alleen actuele waarnemingen",
        (40, 700),
        scale=0.5,
    )
    return canvas


def automatic_preview(
    frame: np.ndarray, state: dict, *, recognized_points=True, tracked_points=True
) -> np.ndarray:
    """Draw only visible portions; virtual offscreen corners are never fabricated observations."""
    preview = frame.copy()
    height, width = frame.shape[:2]
    polygon = state.get("visible_field_polygon_xy")
    if state["status"] == "valid" and polygon is not None:
        cv2.polylines(preview, [np.rint(polygon).astype(np.int32)], True, (240, 220, 70), 2, cv2.LINE_AA)
    if state.get("homography") is not None and state["status"] == "valid":
        inverse = np.linalg.inv(np.asarray(state["homography"]))
        for points in LINES_UV.values():
            try:
                projected = transform(points, inverse)
                if not np.isfinite(projected).all() or np.abs(projected).max() > 1e7:
                    continue
                a, b = [tuple(map(int, p)) for p in projected]
                visible, a, b = cv2.clipLine((0, 0, width, height), a, b)
                if visible:
                    cv2.line(preview, a, b, (255, 190, 20), 2, cv2.LINE_AA)
            except (ValueError, cv2.error):
                continue
    for line in state.get("lines", []):
        a, b = [tuple(map(int, p)) for p in line["xy"]]
        cv2.line(preview, a, b, (90, 220, 120), 1, cv2.LINE_AA)
    for point in state.get("points", []) if recognized_points else []:
        x, y = round(point["x"]), round(point["y"])
        cv2.circle(preview, (x, y), 4, (60, 220, 245), -1)
        label(preview, str(point["id"]), (x + 5, max(15, y - 5)), scale=0.4)
    for point in state.get("tracked_points", []) if tracked_points else []:
        cv2.circle(preview, tuple(round(v) for v in point), 2, (235, 120, 245), -1)
    label(preview, f"{status_label(state)} | {state['status']}", (20, max(22, height - 20)), scale=0.65)
    return preview


def calibration_preview(frame: np.ndarray, points: list[dict], grid: bool = True) -> np.ndarray:
    preview = frame.copy()
    height, width = frame.shape[:2]
    if grid:
        step = max(50, round(max(width, height) / 12 / 50) * 50)
        for x in range(0, width, step):
            cv2.line(preview, (x, 0), (x, height - 1), (105, 115, 105), 1)
            label(preview, str(x), (x + 2, 20), scale=0.5)
        for y in range(step, height, step):
            cv2.line(preview, (0, y), (width - 1, y), (105, 115, 105), 1)
            label(preview, str(y), (3, y - 3), scale=0.5)
    for point in points:
        try:
            x, y = int(point["x"]), int(point["y"])
            color = (40, 220, 230) if point["role"] == "fit" else (240, 160, 60)
            cv2.circle(preview, (x, y), 6, color, -1)
            label(preview, str(point["name"]), (x + 8, max(20, y - 8)), color)
        except (ValueError, TypeError, KeyError, OverflowError):
            continue
    return preview
