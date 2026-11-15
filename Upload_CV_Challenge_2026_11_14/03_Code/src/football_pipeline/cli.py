"""Verwerkt commandoregelargumenten en roept inspectie, verwerking en evaluatie aan."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .automatic_calibration import load_automatic_calibration, prepare_automatic_calibration
from .contracts import PipelineError, read_json, write_json
from .geometry import Calibration, create_calibration
from .pipeline import accept_mvp, process_video
from .video import ROOT, inspect_video, tool_versions


def main(argv=None) -> int:
    """Lees het gevraagde CLI-commando, controleer zijn argumenten en start de passende inspectie-,
    verwerkings-, evaluatie- of demofunctie.
    """
    parser = argparse.ArgumentParser(description="Voetbalvideo, gekalibreerde minimap en ByteTrack")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Controleer FFmpeg, ffprobe en Python-dependencies")
    sub.add_parser("download-baseline", help="Download expliciet COCO YOLO11n; geen spelersclassificatie")
    register = sub.add_parser(
        "register-player-model", help="Controleer getrainde gewichten en maak een spelersprofiel"
    )
    register.add_argument("weights", type=Path)
    register.add_argument(
        "--mapping", type=Path, required=True, help="JSON-object: modelklasse-ID naar semantische klasse"
    )
    register.add_argument("--output", type=Path, default=ROOT / "configs/models-players.json")
    register.add_argument("--model-id", default="players_v1")
    register.add_argument("--imgsz", type=int, default=1920)
    register.add_argument("--confidence", type=float, default=0.10)
    register.add_argument("--iou", type=float, default=0.70)
    register.add_argument("--device", default="cpu")
    register.add_argument("--evaluation-record", type=Path)
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
    calibration_source = process.add_mutually_exclusive_group(required=True)
    calibration_source.add_argument("--calibration", type=Path)
    calibration_source.add_argument(
        "--automatic-calibration", type=Path, help="Bestaande framekalibratiebundel"
    )
    calibration_source.add_argument(
        "--auto-field", action="store_true", help="Automatische veldkalibratie per frame"
    )
    process.add_argument("--field-runtime", type=Path, default=ROOT / ".tools/field-runtime.json")
    process.add_argument("--source", default="")
    process.add_argument("--usage", default="")
    process.add_argument("--models", type=Path, default=ROOT / "configs/models.json")
    process.add_argument("--output", type=Path, default=ROOT / "runs")
    process.add_argument("--tracker", type=Path)
    process.add_argument("--teams", type=Path, help="Versieerbaar profiel voor automatische teamherkenning")
    process.add_argument("--mvp-acceptance", type=Path)
    process.add_argument("--replay-run", type=Path)
    process.add_argument(
        "--recalibrate-replay",
        action="store_true",
        help="Hergebruik uitsluitend echte detecties; bereken nieuwe veldkalibraties",
    )
    process.add_argument(
        "--field-settings", type=Path, help="JSON-profiel voor gecontroleerde geometrie en camerabeweging"
    )
    process.add_argument(
        "--technical-pilot",
        action="store_true",
        help="Technisch gecontroleerde pilot zonder menselijke MVP-acceptatie",
    )
    accept = sub.add_parser("accept-mvp")
    accept.add_argument("run", type=Path)
    accept.add_argument("--reviewer", required=True)
    accept.add_argument("--confirm-review", required=True, action="store_true")
    evaluation = sub.add_parser("evaluate-tracking")
    evaluation.add_argument("run", type=Path)
    evaluation.add_argument("reference", type=Path)
    evaluation.add_argument("--output", type=Path, required=True)
    field = sub.add_parser("calibrate-auto", help="Draai het veldmodel in de afzonderlijke omgeving")
    field.add_argument("video", type=Path)
    field.add_argument("--runtime", type=Path, default=ROOT / ".tools/field-runtime.json")
    field.add_argument("--output", type=Path, default=ROOT / "data/field-calibration")
    field.add_argument("--source", required=True)
    field.add_argument("--usage", required=True)
    field_evaluation = sub.add_parser(
        "evaluate-calibration", help="Meet tegen onafhankelijke menselijke veldpunten"
    )
    field_evaluation.add_argument("run", type=Path)
    field_evaluation.add_argument("reference", type=Path)
    field_evaluation.add_argument("--output", type=Path, required=True)
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
        elif args.command == "register-player-model":
            from .model_handoff import register_player_model

            registered = register_player_model(
                args.weights,
                args.mapping,
                args.output,
                model_id=args.model_id,
                imgsz=args.imgsz,
                confidence=args.confidence,
                iou=args.iou,
                device=args.device,
                evaluation_record=args.evaluation_record,
            )
            print(
                json.dumps(
                    {
                        "profile": str(args.output),
                        "models": registered["models"],
                        "next_step": "Kies het profiel in Streamlit en controleer eerst een MVP zonder tracking.",
                    },
                    indent=2,
                )
            )
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
            calibration = (
                Calibration(**read_json(args.calibration))
                if args.calibration
                else load_automatic_calibration(args.automatic_calibration)
                if args.automatic_calibration
                else None
            )
            result = process_video(
                args.video,
                calibration,
                args.models,
                args.output,
                tracker_config_path=args.tracker,
                team_config_path=args.teams,
                mvp_acceptance_path=args.mvp_acceptance,
                replay_run=args.replay_run,
                technical_pilot=args.technical_pilot,
                field_runtime_path=args.field_runtime if args.auto_field else None,
                field_source=args.source,
                field_usage=args.usage,
                field_settings=read_json(args.field_settings) if args.field_settings else None,
                recalibrate_replay=args.recalibrate_replay,
                progress=lambda n, total, elapsed: print(f"{n}/{total} frames | {elapsed:.1f} s"),
                field_progress=lambda n, total, elapsed: print(
                    f"Veldherkenning: {n}/{total} frames | {elapsed:.1f} s"
                ),
            )
            print(result.video_path)
        elif args.command == "calibrate-auto":
            bundle = prepare_automatic_calibration(
                args.video, args.runtime, args.output, source=args.source, usage=args.usage
            )
            print(Path(bundle.observations_path).with_name("automatic_calibration.json"))
        elif args.command == "evaluate-calibration":
            from .calibration_evaluation import evaluate_calibration

            write_json(args.output, evaluate_calibration(args.run, args.reference))
            print(args.output)
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
