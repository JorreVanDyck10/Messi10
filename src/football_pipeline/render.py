from __future__ import annotations

import cv2
import numpy as np

from .automatic_calibration import transform
from .contracts import FrameRecord
from .field_layout import LINES_UV
from .field_motion import status_label
from .geometry import valid_box
from .tracking import Trajectories

COLORS = {
    "player": (185, 215, 65),
    "referee": (30, 170, 245),
    "person": (225, 190, 120),
    "ball": (245, 245, 245),
}
LABELS = {"player": "speler", "referee": "scheidsrechter", "person": "persoon", "ball": "bal"}


def label(image, text, point, color=(235, 240, 235), scale=0.6):
    cv2.putText(image, text, point, cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)


def field_pixel(position):
    return round(40 + 560 * position[0]), round(170 + 360 * position[1])


def render_frame(
    frame: np.ndarray,
    record: FrameRecord,
    histories: Trajectories | None = None,
    display_confidence: float = 0.25,
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
        if detection.track_id is None and detection.confidence < display_confidence:
            continue
        x1, y1, x2, y2 = [round(x * scale) for x in detection.bbox_xyxy]
        color = COLORS.get(detection.semantic_class, (190, 190, 190))
        cv2.rectangle(left, (x1, y1), (x2, y2), color, 2)
        text = LABELS.get(detection.semantic_class, detection.semantic_class)
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
    label(pitch, "Genormaliseerd veld - geen meters", (40, 120), scale=0.55)
    cv2.rectangle(pitch, (40, 170), (600, 530), (40, 85, 52), -1)
    cv2.rectangle(pitch, (40, 170), (600, 530), (205, 225, 210), 2)
    cv2.line(pitch, (320, 170), (320, 530), (205, 225, 210), 2)
    cv2.circle(pitch, (320, 350), 45, (205, 225, 210), 1)
    label(pitch, "u: 0 -> 1", (40, 558), scale=0.5)
    if record.calibration:
        known = record.calibration["status"] == "valid"
        label(
            pitch,
            status_label(record.calibration),
            (40, 150),
            (100, 220, 180) if known else (80, 180, 245),
            scale=0.6,
        )
        state = record.calibration
        label(
            pitch,
            f"Punten: {len(state.get('points', []))} | {state.get('recognition_status', state['status'])}",
            (40, 578),
            scale=0.43,
        )
        age = state.get("age_s")
        if age is not None:
            label(
                pitch,
                f"Sinds herkenning: {age:.2f} s | referentie {state.get('reference_frame')}",
                (40, 598),
                scale=0.43,
            )
    for detection in record.detections:
        if detection.field_position is None:
            continue
        if detection.track_id is None and detection.confidence < display_confidence:
            continue
        color = COLORS.get(detection.semantic_class, (190, 190, 190))
        if histories is not None and detection.track_id is not None:
            for a, b in histories.segments(detection.track_id):
                cv2.line(pitch, field_pixel(a[1:]), field_pixel(b[1:]), color, 2, cv2.LINE_AA)
        point = field_pixel(detection.field_position)
        cv2.circle(pitch, point, 6, color, -1, cv2.LINE_AA)
        if detection.track_id is not None:
            label(pitch, str(detection.track_id), (point[0] + 8, point[1] - 6), color, 0.5)
    for index, (semantic, color) in enumerate(COLORS.items()):
        x, y = 40 + (index % 2) * 280, 610 + (index // 2) * 32
        cv2.circle(pitch, (x, y - 5), 5, color, -1)
        label(pitch, LABELS[semantic], (x + 15, y), scale=0.5)
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
