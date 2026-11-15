"""Voert een ontwikkelvideo door de herkenningsmodellen zonder ontbrekende veldkalibratie te verzinnen."""

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import cv2

from football_pipeline.contracts import FrameRecord
from football_pipeline.detection import UltralyticsDetector, load_model_manifest
from football_pipeline.render import render_frame
from football_pipeline.video import inspect_video

from .modeling import yolo
from .role_training import ROOT, save


def run(video_path, output, frames=30, model_manifest_path=None):
    """Voer herkenning op geselecteerde frames van een echte ontwikkelvideo uit en bewaar boxen, rollen
    en teaminformatie zonder ontbrekende kalibratie te verzinnen.
    """
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    yolo(ROOT / "models/yolo11n.pt")
    config = load_model_manifest(model_manifest_path or ROOT / "configs/models-players.json")
    detector = UltralyticsDetector(config)
    video = inspect_video(video_path)
    detector.set_video_identity(video.sha256)
    capture = cv2.VideoCapture(video.path)
    rows = []
    start = time.perf_counter()
    for i in range(min(frames, video.frame_count)):
        ok, frame = capture.read()
        assert ok
        record = FrameRecord(
            i,
            i / video.fps,
            video.size,
            detector.detect(frame, i),
            {"status": "calibration_unavailable", "points": []},
        )
        rows.append(record.to_dict())
        if i == min(frames, video.frame_count) - 1:
            cv2.imwrite(str(output / f"frame-{i:06}.jpg"), render_frame(frame, record))
    capture.release()
    elapsed = time.perf_counter() - start
    (output / "detections.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    known = video.sha256 in detector.appearance.team_video_hashes
    report = {
        "video_sha256": video.sha256,
        "source_frames": [0, len(rows) - 1],
        "runtime_s": elapsed,
        "processing_fps": len(rows) / elapsed,
        "models": config,
        "known_team_match": known,
        "scope": "Development video inference only, no accuracy claim without independent role/team GT",
        "team_calibration": detector.appearance.video_teams.info,
        "last_visible_roles": dict(
            Counter(d["semantic_class"] for d in rows[-1]["detections"] if d["confidence"] >= 0.25)
        ),
        "last_visible_teams": dict(
            Counter(
                d["team_id"] or "unknown"
                for d in rows[-1]["detections"]
                if d["confidence"] >= 0.25 and d["semantic_class"] == "player"
            )
        ),
    }
    save(output / "run.json", report)
    print({k: v for k, v in report.items() if k != "models"})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--frames", type=int, default=30)
    p.add_argument("--models")
    args = p.parse_args()
    if args.frames < 1:
        raise ValueError("Choose at least one source frame")
    run(args.video, args.output, args.frames, args.models)
