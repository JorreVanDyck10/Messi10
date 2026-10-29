"""Voert veldpuntinferentie uit met herleidbare bronpixelcoördinaten en optionele lenscorrectie."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .contracts import read_json, sha256_file
from .field_layout import POINTS_UV
from .field_lens import rectify_image
from .field_motion import DEFAULT_SETTINGS, estimate_checked


def field_crop(frame):
    """Remove empty sky only when a large lower grass region supplies a stable bound."""
    h, w = frame.shape[:2]
    small = cv2.resize(frame, (640, round(h * 640 / w)))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    grass = cv2.inRange(hsv, np.array([25, 35, 25]), np.array([95, 255, 255]))
    grass = cv2.morphologyEx(grass, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(grass, 8)
    if n <= 1:
        return (0, 0, w, h)
    candidates = []
    for identifier in range(1, n):
        area = stats[identifier, cv2.CC_STAT_AREA]
        if area >= small.shape[0] * small.shape[1] * 0.1:
            lower = np.count_nonzero(labels[round(small.shape[0] * 0.6) :] == identifier)
            candidates.append((lower, identifier))
    if not candidates:
        return (0, 0, w, h)
    _, identifier = max(candidates)
    top = stats[identifier, cv2.CC_STAT_TOP] / small.shape[0]
    if top < 0.15:
        return (0, 0, w, h)
    top = max(0, min(0.5, top - 0.04))
    return (0, int(top * h), w, h)


def validate_pose_runtime(runtime):
    if runtime.get("backend") != "field_pose" or set(runtime.get("models", {})) != {"keypoints"}:
        raise ValueError("Unknown field-pose runtime")
    spec = runtime["models"]["keypoints"]
    if runtime.get("ground_point_ids") != sorted(POINTS_UV):
        raise ValueError("Field-pose semantics differ from the calibrated pitch template")
    if Path(runtime["weights_keypoints"]).resolve() != Path(spec["path"]).resolve():
        raise ValueError("Field-pose weight paths disagree")
    if sha256_file(spec["path"]) != spec["sha256"]:
        raise ValueError("Field-pose weights changed")
    report = read_json(spec["training_report"])
    if sha256_file(spec["training_report"]) != spec["training_report_sha256"]:
        raise ValueError("Field-pose training report changed")
    if report.get("status") != "complete" or report.get("weights_sha256") != spec["sha256"]:
        raise ValueError("Field-pose weights do not match a completed training")
    if report.get("ground_point_ids") != runtime["ground_point_ids"]:
        raise ValueError("Field-pose training landmark order changed")


class FieldPoseEstimator:
    def __init__(self, weights, *, device=0, imgsz=960, settings=None):
        from ultralytics import YOLO

        self.model = YOLO(str(weights))
        if self.model.task != "pose" or self.model.names != {0: "football_field"}:
            raise ValueError("Expected a trained football-field pose model")
        if list(self.model.model.kpt_shape) != [len(POINTS_UV), 3]:
            raise ValueError("Expected all 53 ground-plane landmark channels")
        self.device, self.imgsz = device, imgsz
        self.settings = settings or DEFAULT_SETTINGS

    def predict_view(self, frame, roi):
        x1, y1, x2, y2 = roi
        result = self.model.predict(
            frame[y1:y2, x1:x2],
            imgsz=self.imgsz,
            device=self.device,
            conf=0.1,
            max_det=1,
            rect=False,
            verbose=False,
        )[0]
        coordinates = np.zeros((len(POINTS_UV), 3))
        instance_confidence = 0.0
        if result.boxes is not None and len(result.boxes):
            instance_confidence = float(result.boxes.conf[0])
            coordinates = result.keypoints.data[0].detach().cpu().numpy().astype(float)
            coordinates[:, :2] += [x1, y1]
        h, w = frame.shape[:2]
        points = []
        for identifier, (x, y, confidence) in zip(sorted(POINTS_UV), coordinates):
            if not np.isfinite([x, y, confidence]).all() or not 0 <= x < w or not 0 <= y < h:
                x = y = confidence = 0.0
            if instance_confidence < 0.25:
                confidence = 0.0
            confidence = min(1.0, max(0.0, float(confidence)))
            points.append(
                {
                    "id": identifier,
                    "x": float(x),
                    "y": float(y),
                    "confidence": confidence,
                    "raw_score": confidence,
                }
            )
        return {
            "image_size": [w, h],
            "points": points,
            "lines": [],
            "roi": list(roi),
            "instance_confidence": instance_confidence,
        }

    def observe(self, frame, *, lens=None, crop=True):
        image = rectify_image(frame, lens)
        h, w = image.shape[:2]
        first = self.predict_view(image, (0, 0, w, h))
        observations = [first]
        roi = field_crop(image) if crop else (0, 0, w, h)
        if roi != (0, 0, w, h):
            observations.append(self.predict_view(image, roi))
        states = [estimate_checked(row, (w, h), self.settings) for row in observations]
        valid = [i for i, state in enumerate(states) if state["status"] == "valid"]
        # Full-frame predictions win if both views pass. No ground-truth-based per-frame selection.
        chosen = (
            valid[0]
            if valid
            else max(range(len(states)), key=lambda i: states[i]["quality"].get("ground_points", 0))
        )
        row = observations[chosen]
        row["lens"] = lens
        row["view_policy"] = "full_frame_then_measured_grass_crop; accept only checked geometry"
        return row
