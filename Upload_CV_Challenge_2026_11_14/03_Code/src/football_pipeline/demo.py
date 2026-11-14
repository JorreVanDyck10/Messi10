"""Maakt synthetische beelden voor softwarecontroles. Deze fixtures meten geen herkenningskwaliteit op echte voetbalwedstrijden."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from .contracts import Detection, digest_json, write_json
from .geometry import create_calibration
from .video import VideoWriter, inspect_video


def default_points(width: int, height: int) -> list[dict]:
    # Deliberately empty image coordinates: users must identify their actual field points.
    """Maak de namen en bekende veldcoördinaten van vier fitpunten en twee controles; de beeldpixelvelden
    blijven leeg voor invoer.
    """
    definitions = [
        ("hoek_00", "fit", 0, 0),
        ("hoek_10", "fit", 1, 0),
        ("hoek_11", "fit", 1, 1),
        ("hoek_01", "fit", 0, 1),
        ("middenlijn_v0", "check", 0.5, 0),
        ("middenlijn_v1", "check", 0.5, 1),
    ]
    return [
        {"name": name, "role": role, "x": None, "y": None, "u": u, "v": v} for name, role, u, v in definitions
    ]


class SyntheticDetector:
    evidence_kind = "synthetic"
    provenance = {"fixture": "moving_rectangles_with_empty_frame_v1"}

    def detect(self, frame, frame_index):
        """Geef de voorspelbare bewegende testbox voor dit frame terug; er wordt hier geen neuraal
        netwerk uitgevoerd.
        """
        if frame_index == 8:
            return []
        x = 100 + frame_index * 2
        return [Detection(f"{frame_index}:0", "synthetic", 0, "player", [x, 120, x + 24, 175], 0.9)]


def generate_demo(directory: Path) -> dict:
    """Maak een synthetische video, bijpassende kalibratie en een testmodelmanifest voor een
    reproduceerbare softwareproef.
    """
    directory.mkdir(parents=True, exist_ok=True)
    video_path = directory / "synthetic.mp4"
    writer = VideoWriter(video_path, 640, 360, 10, 1)
    try:
        detector = SyntheticDetector()
        for index in range(20):
            frame = np.full((360, 640, 3), (35, 105, 45), dtype=np.uint8)
            cv2.rectangle(frame, (40, 40), (600, 320), (230, 240, 230), 2)
            cv2.line(frame, (320, 40), (320, 320), (230, 240, 230), 1)
            for detection in detector.detect(frame, index):
                box = tuple(map(int, detection.bbox_xyxy))
                cv2.rectangle(frame, box[:2], box[2:], (190, 90, 50), -1)
            cv2.putText(
                frame, f"SYNTHETISCH {index}", (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (240, 240, 240), 1
            )
            writer.write(frame)
        writer.close()
    finally:
        if not writer.closed:
            writer.close(abort=True)
    video = inspect_video(video_path)
    points = default_points(640, 360)
    for point in points:
        point["x"], point["y"] = 40 + point["u"] * 560, 40 + point["v"] * 280
    calibration = create_calibration(video, points)
    calibration.review = {
        "approved": True,
        "reviewer": "synthetic fixture generator",
        "static_camera_confirmed": True,
        "temporal_frames": [0, 10, 19],
        "source": "generated rectangles",
        "usage": "synthetic engineering check only",
    }
    write_json(directory / "calibration.json", asdict(calibration))
    # A local identity file allows the same manifest/provenance machinery without pretending to be YOLO weights.
    (directory / "synthetic.identity").write_text(digest_json(detector.provenance), encoding="utf-8")
    write_json(
        directory / "models.json",
        {
            "schema_version": 1,
            "profile_name": "SYNTHETISCH — geen modelmeting",
            "models": [
                {
                    "model_id": "synthetic",
                    "weights": "synthetic.identity",
                    "class_mapping": {"0": "player"},
                    "expected_names": {"0": "player"},
                    "imgsz": 640,
                    "confidence": 0.1,
                    "iou": 0.7,
                    "device": "cpu",
                }
            ],
        },
    )
    return {"video": video_path, "calibration": calibration, "models": directory / "models.json"}
