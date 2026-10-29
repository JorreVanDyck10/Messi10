"""Execute combined roles/teams/tiled balls on real video and verify source coordinates."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2

from football_pipeline.contracts import FrameRecord, sha256_file, write_json
from football_pipeline.detection import UltralyticsDetector, available_roles, load_model_manifest
from football_pipeline.geometry import valid_box
from football_pipeline.render import render_frame
from football_pipeline.video import ROOT, inspect_video


def main():
    """Verwerk echte video met rollen, teams en baltegels en controleer de terugvertaalde
    broncoördinaten.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--models", type=Path, default=ROOT / "configs/models-players-ball-tiles.json")
    parser.add_argument("--frames", type=int, default=30)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.frames <= 0:
        raise ValueError("Require a fresh output and positive frame count")
    args.output.mkdir(parents=True)
    video = inspect_video(args.video)
    spec = load_model_manifest(args.models)
    detector = UltralyticsDetector(spec)
    detector.set_video_identity(video.sha256)
    cap = cv2.VideoCapture(str(args.video))
    rows, times = [], []
    for index in range(args.frames):
        ok, frame = cap.read()
        if not ok:
            raise ValueError("Video shorter than requested handoff")
        start = time.perf_counter()
        detections = detector.detect(frame, index)
        times.append(time.perf_counter() - start)
        assert all(valid_box(d, video.size) for d in detections)
        record = FrameRecord(
            index,
            index / video.fps,
            video.size,
            detections,
            {"status": "calibration_unavailable", "points": []},
            player_model_available="player" in available_roles(spec),
        )
        row = {"video_sha256": video.sha256, **record.to_dict()}
        assert row["player_summary"]["on_field"] is None
        rows.append(row)
        if index in (0, args.frames - 1):
            cv2.imwrite(str(args.output / f"frame-{index:06}.jpg"), render_frame(frame, record))
    cap.release()
    (args.output / "detections.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
    )
    write_json(
        args.output / "handoff.json",
        {
            "video_sha256": video.sha256,
            "frames": args.frames,
            "video_size": list(video.size),
            "fps": video.fps,
            "model_manifest_sha256": sha256_file(args.models),
            "models": spec,
            "ball_detections": sum(d["semantic_class"] == "ball" for r in rows for d in r["detections"]),
            "ball_empty_frames": [
                r["frame_index"]
                for r in rows
                if not any(d["semantic_class"] == "ball" for d in r["detections"])
            ],
            "inference_seconds": times,
            "scope": "Real combined detector/role/team/rendering technical handoff; not calibrated field, tactical-map, tracking, accuracy or comparative 4050 benchmark.",
            "counting_gate_verified_unknown_without_field": True,
            "human_review_completed": False,
        },
    )
    print("Verified combined real-video handoff:", args.output)


if __name__ == "__main__":
    main()
