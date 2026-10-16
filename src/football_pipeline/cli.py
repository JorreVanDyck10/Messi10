from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .contracts import PipelineError, read_json, write_json
from .geometry import Calibration, create_calibration
from .pipeline import accept_mvp, process_video
from .video import ROOT, inspect_video, tool_versions


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Voetbalvideo, gekalibreerde minimap en ByteTrack")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Controleer FFmpeg, ffprobe en Python-dependencies")
    sub.add_parser("download-baseline", help="Download expliciet COCO YOLO11n; geen spelersclassificatie")
    inspect = sub.add_parser("inspect")
    inspect.add_argument("video", type=Path)
    calibrate = sub.add_parser("calibrate")
    calibrate.add_argument("video", type=Path)
    calibrate.add_argument(
        "points", type=Path, help="JSON-array met vier fit- en minstens twee controlepunten"
    )
    calibrate.add_argument("output", type=Path)
    calibrate.add_argument("--reviewer", required=True)
    calibrate.add_argument("--source", required=True)
    calibrate.add_argument("--usage", required=True)
    calibrate.add_argument("--confirm-static-camera", action="store_true", required=True)
    process = sub.add_parser("process")
    process.add_argument("video", type=Path)
    process.add_argument("--calibration", type=Path, required=True)
    process.add_argument("--models", type=Path, default=ROOT / "configs/models.json")
    process.add_argument("--output", type=Path, default=ROOT / "runs")
    process.add_argument("--tracker", type=Path)
    process.add_argument("--mvp-acceptance", type=Path)
    process.add_argument("--replay-run", type=Path)
    accept = sub.add_parser("accept-mvp")
    accept.add_argument("run", type=Path)
    accept.add_argument("--reviewer", required=True)
    accept.add_argument("--confirm-review", required=True, action="store_true")
    evaluation = sub.add_parser("evaluate-tracking")
    evaluation.add_argument("run", type=Path)
    evaluation.add_argument("reference", type=Path)
    evaluation.add_argument("--output", type=Path, required=True)
    demo = sub.add_parser("demo", help="Maak en verwerk uitsluitend synthetische testbeelden")
    demo.add_argument("--output", type=Path, default=ROOT / "artifacts/demo")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            from .pipeline import dependencies

            print(json.dumps({"tools": tool_versions(), "dependencies": dependencies()}, indent=2))
        elif args.command == "inspect":
            print(json.dumps(asdict(inspect_video(args.video)), indent=2))
        elif args.command == "download-baseline":
            from ultralytics.utils.downloads import attempt_download_asset

            path = ROOT / "weights/yolo11n.pt"
            path.parent.mkdir(exist_ok=True)
            attempt_download_asset(str(path))
            if not path.is_file():
                raise PipelineError("Modeldownload leverde geen gewichten op.")
            print(path)
        elif args.command == "calibrate":
            video = inspect_video(args.video)
            points = json.loads(args.points.read_text(encoding="utf-8-sig"))
            calibration = create_calibration(video, points)
            calibration.review = {
                "approved": True,
                "reviewer": args.reviewer,
                "static_camera_confirmed": args.confirm_static_camera,
                "temporal_frames": [0, video.frame_count // 2, video.frame_count - 1],
                "source": args.source,
                "usage": args.usage,
            }
            calibration.validate_for(video)
            write_json(args.output, asdict(calibration))
            print(args.output)
        elif args.command == "process":
            result = process_video(
                args.video,
                Calibration(**read_json(args.calibration)),
                args.models,
                args.output,
                tracker_config_path=args.tracker,
                mvp_acceptance_path=args.mvp_acceptance,
                replay_run=args.replay_run,
                progress=lambda n, total, elapsed: print(f"{n}/{total} frames | {elapsed:.1f} s"),
            )
            print(result.video_path)
        elif args.command == "accept-mvp":
            print(accept_mvp(args.run, args.reviewer, args.confirm_review))
        elif args.command == "evaluate-tracking":
            from .evaluation import evaluate_run

            write_json(args.output, evaluate_run(args.run, args.reference))
            print(args.output)
        elif args.command == "demo":
            from .demo import SyntheticDetector, generate_demo

            fixture = generate_demo(args.output / "input")
            result = process_video(
                fixture["video"],
                fixture["calibration"],
                fixture["models"],
                args.output / "runs",
                detector=SyntheticDetector(),
            )
            print("SYNTHETISCHE CONTROLE — geen bewijs van voetbaldetectie of menselijke MVP-acceptatie")
            print(result.video_path)
        return 0
    except (PipelineError, OSError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"Fout: {exc}", file=sys.stderr)
        return 1
