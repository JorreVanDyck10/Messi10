"""Real per-detector examples on one identified development video, in original pixels."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from football_pipeline.contracts import FrameRecord, write_json
from football_pipeline.detection import UltralyticsDetector, available_roles, load_model_manifest
from football_pipeline.geometry import valid_box
from football_pipeline.render import render_frame
from football_pipeline.video import ROOT, inspect_video
from persoon1.modeling import yolo


def main():
    """Voer de afzonderlijke detectors op vaste bronframes uit en schrijf bronpixelvoorbeelden voor de
    modeloverdracht.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    yolo(ROOT / "models/yolo11n.pt")
    video = inspect_video(args.video)
    configurations = {
        "roles_r015": load_model_manifest(ROOT / "configs/models-roles-r015.json"),
        "ball_f003": load_model_manifest(ROOT / "configs/models-ball-f003.json"),
    }
    detectors = {name: UltralyticsDetector(config) for name, config in configurations.items()}
    for detector in detectors.values():
        detector.set_video_identity(video.sha256)
    capture = cv2.VideoCapture(str(args.video))
    records, empty = {}, []
    for index in range(30):
        ok, frame = capture.read()
        if not ok:
            raise ValueError("Development clip too short")
        for name, detector in detectors.items():
            detections = detector.detect(frame, index)
            assert all(valid_box(d, video.size) for d in detections)
            record = FrameRecord(
                index,
                index / video.fps,
                video.size,
                detections,
                {"status": "calibration_unavailable", "points": []},
                player_model_available="player" in available_roles(configurations[name]),
            )
            if not detections:
                empty.append({"stream": name, "frame_index": index})
            records.setdefault(name, []).append({"video_sha256": video.sha256, **record.to_dict()})
            if index in (0, 29):
                cv2.imwrite(str(args.output / f"{name}-frame-{index:06}.jpg"), render_frame(frame, record))
    capture.release()
    for name, rows in records.items():
        import json

        (args.output / (name + ".jsonl")).write_text(
            "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
        )
    write_json(
        args.output / "handoff.json",
        {
            "video_sha256": video.sha256,
            "video": str(args.video),
            "image_size": list(video.size),
            "fps": video.fps,
            "frames": [0, 29],
            "models": configurations,
            "actual_empty_detector_frames": empty,
            "scope": "Technical development handoff on real full frames, not an accuracy evaluation. Ball crop AP does not prove raw-video detection quality. Empty records are PER detector, not a claim that the scene has no people.",
            "human_review_completed": False,
            "independent_final_test": False,
            "coordinates": "All boxes use the original input video pixel dimensions; source class IDs and role-classifier IDs remain distinct.",
        },
    )


if __name__ == "__main__":
    main()
