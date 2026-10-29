"""Frozen, reproducible ablations on the user's development clip; no invented human references."""

from __future__ import annotations

import argparse
import json
import shutil
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.automatic_calibration import (
    AutomaticCalibration,
    estimate_frame,
    load_automatic_calibration,
)
from football_pipeline.contracts import PipelineError, read_json, sha256_file, write_json
from football_pipeline.field_motion import DEFAULT_SETTINGS, CameraCalibration, estimate_checked
from football_pipeline.field_review import failure_intervals
from football_pipeline.pipeline import code_identity, process_video, validate_completed
from football_pipeline.video import ROOT, VideoWriter, inspect_video, read_frame


def summarize(states, fps, development_indices):
    """Vat de kalibratietoestanden samen in totale dekking, dekking op de ontwikkelselectie en relevante
    statusaantallen.
    """
    valid = [s for s in states if s["status"] == "valid"]
    errors = [e for s in valid for e in s.get("quality", {}).get("control_errors_px", [])]
    intervals = failure_intervals([{"calibration": s} for s in states])
    return {
        "frames": len(states),
        "valid_frames": len(valid),
        "coverage_all_frames": len(valid) / len(states),
        "development_valid_frames": sum(states[i]["status"] == "valid" for i in development_indices),
        "development_frames": len(development_indices),
        "status_counts": dict(Counter(s["status"] for s in states)),
        "source_counts": dict(Counter(s.get("source", "legacy") for s in states)),
        "model_holdout_median_px": float(np.median(errors)) if errors else None,
        "model_holdout_maximum_px": float(max(errors)) if errors else None,
        "human_reference_errors_px": None,
        "human_calibratable_coverage": None,
        "failure_intervals": intervals,
        "longest_failure_s": max((b - a + 1 for a, b in intervals), default=0) / fps,
        "human_reviewed": False,
    }


def main():
    """Voer de vastgelegde veldablaties op de ontwikkelclip uit en bewaar dekking en geometrie zonder
    menselijke referenties te verzinnen.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/broadcast-field-v2")
    parser.add_argument("--runs", type=Path, default=ROOT / "runs")
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    if (output / "experiment.json").is_file():
        previous = output / "experiment.json"
        shutil.copyfile(previous, output / f"experiment-{sha256_file(previous)[:12]}.json")
    selection = read_json(ROOT / "configs/broadcast-field-selection.json")
    video = inspect_video(args.video)
    if video.sha256 != selection["video_sha256"]:
        raise PipelineError("Deze vooraf vastgelegde selectie hoort bij een andere video.")
    baseline = validate_completed(args.baseline)
    if baseline["video"]["sha256"] != video.sha256:
        raise PipelineError("Baseline hoort bij een andere video.")
    bundle = load_automatic_calibration(args.bundle)
    bundle.validate_for(video)
    if bundle.manifest.get("score_storage") != "all_ground_peaks_before_threshold":
        raise PipelineError("Vergelijk confidences uitsluitend op dezelfde volledige netwerkuitvoer.")
    observations = [json.loads(line) for line in Path(bundle.observations_path).read_text().splitlines()]
    # Validate every observation index/timestamp and trailing row through the public reader.
    list(bundle.frames(video))
    stages, state_sets = {}, {}
    profiles = {
        "baseline": None,
        "geometry_03434": {**DEFAULT_SETTINGS, "motion": False},
        "confidence_025": {**DEFAULT_SETTINGS, "motion": False, "keypoint_threshold": 0.25},
    }
    for name, profile in profiles.items():
        started = time.perf_counter()
        states = [
            estimate_frame(row, video.size) if profile is None else estimate_checked(row, video.size, profile)
            for row in observations
        ]
        state_sets[name] = states
        stages[name] = {
            "settings": profile or bundle.manifest["policy"],
            **summarize(states, video.fps, selection["development_indices"]),
            "calibration_s": time.perf_counter() - started,
        }
        (output / f"{name}.jsonl").write_text(
            "".join(json.dumps(s, allow_nan=False) + "\n" for s in states), encoding="utf-8"
        )
        print(
            name,
            stages[name]["valid_frames"],
            "valid; development",
            stages[name]["development_valid_frames"],
            flush=True,
        )
    # Choose on development groups only; never read human evaluation references here.
    choice = (
        "confidence_025"
        if stages["confidence_025"]["development_valid_frames"]
        > stages["geometry_03434"]["development_valid_frames"]
        else "geometry_03434"
    )
    settings = {**profiles[choice], "motion": True}
    frozen = {
        "settings": settings,
        "settings_frozen_at": datetime.now(UTC).isoformat(),
        "selection_sha256": sha256_file(ROOT / "configs/broadcast-field-selection.json"),
        "choice": choice,
        "rule": "Highest internally controlled development-frame coverage; tie retains stricter confidence. Provisional until human reference validation.",
        "human_references_used": False,
    }
    write_json(output / "frozen-settings.json", frozen)
    # Run the stateful component on consecutive original frames, using the chosen direct estimates.
    capture = cv2.VideoCapture(video.path)
    camera = CameraCalibration(video.fps, settings)
    started = time.perf_counter()
    motion_states = []
    try:
        for index, direct in enumerate(state_sets[choice]):
            ok, frame = capture.read()
            if not ok:
                raise PipelineError("Ontbrekend ontwikkelframe.")
            motion_states.append(camera.update(frame, direct, index))
    finally:
        capture.release()
    stages["camera_motion"] = {
        "settings": settings,
        **summarize(motion_states, video.fps, selection["development_indices"]),
        "calibration_s": time.perf_counter() - started,
    }
    (output / "camera_motion.jsonl").write_text(
        "".join(json.dumps(s, allow_nan=False) + "\n" for s in motion_states), encoding="utf-8"
    )
    print("camera_motion", stages["camera_motion"]["valid_frames"], "valid", flush=True)
    result = process_video(
        video.path,
        AutomaticCalibration(bundle.manifest, bundle.observations_path, settings),
        ROOT / "configs/models.json",
        args.runs,
        replay_run=args.baseline,
        recalibrate_replay=True,
        progress=lambda n, total, elapsed: (
            print(f"Demo {n}/{total} frames | {elapsed:.1f}s", flush=True)
            if n % 100 < 6 or n == total
            else None
        ),
    )
    actual = [
        json.loads(line)["calibration"]
        for line in (result.directory / "framegegevens.jsonl").read_text().splitlines()
    ]
    if [s["status"] for s in actual] != [s["status"] for s in motion_states]:
        raise PipelineError("Experiment en productiepipeline geven verschillende kalibratiestatussen.")
    for expected, produced in zip(motion_states, actual):
        if (expected.get("source"), expected.get("reference_frame"), expected.get("age_s")) != (
            produced.get("source"),
            produced.get("reference_frame"),
            produced.get("age_s"),
        ):
            raise PipelineError("Kalibratiebron of referentietijdlijn wijkt af bij detectiereplay.")
        if expected["status"] == "valid" and not np.allclose(
            expected["homography"], produced["homography"], rtol=0, atol=1e-12
        ):
            raise PipelineError("Replay geeft een andere veldtransformatie.")
    shutil.copyfile(result.video_path, output / "demonstratie.mp4")
    # Matched-frame visual baseline comparison; no new network inference.
    old = cv2.VideoCapture(str(args.baseline / "samengestelde_video.mp4"))
    new = cv2.VideoCapture(str(result.video_path))
    writer = VideoWriter(output / "vergelijking.mp4", 1920, 720, video.fps_num, video.fps_den)
    try:
        for index in range(video.frame_count):
            a_ok, a = old.read()
            b_ok, b = new.read()
            if not a_ok or not b_ok:
                raise PipelineError("Vergelijkingsvideo mist een frame.")
            canvas = np.zeros((720, 1920, 3), np.uint8)
            canvas[170:530, :960] = cv2.resize(a, (960, 360))
            canvas[170:530, 960:] = cv2.resize(b, (960, 360))
            for x, text in [
                (25, "Baseline: verplichte twee lijnen"),
                (985, "Kandidaat: onafhankelijke controles + camerabeweging"),
            ]:
                cv2.putText(
                    canvas, text, (x, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 235, 230), 1, cv2.LINE_AA
                )
            cv2.putText(
                canvas,
                f"EXPERIMENTEEL | frame {index} | {index / video.fps:.2f}s | menselijke nauwkeurigheid nog open",
                (25, 600),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (80, 200, 245),
                1,
                cv2.LINE_AA,
            )
            writer.write(canvas)
        writer.close()
    finally:
        old.release()
        new.release()
        if not writer.closed:
            writer.close(abort=True)
    # Representative images selected by source/status, plus the frozen development frames.
    selected = set(selection["development_indices"])
    for source in ("detected", "tracked", "unavailable"):
        choices = [i for i, s in enumerate(actual) if s.get("source") == source]
        if choices:
            selected.add(choices[len(choices) // 2])
    demo = inspect_video(result.video_path)
    for index in sorted(selected):
        cv2.imwrite(str(output / f"frame_{index:06d}.jpg"), read_frame(demo, index))
    report = {
        "schema_version": 2,
        "candidate_status": "experimental_pending_human_validation",
        "source": selection,
        "video": {
            "sha256": video.sha256,
            "image_size": list(video.size),
            "fps": video.fps,
            "frames": video.frame_count,
        },
        "baseline_run": args.baseline.name,
        "saved_baseline_measurements": baseline["measurements"],
        "candidate_run": result.directory.name,
        "observations_sha256": bundle.manifest["observations_sha256"],
        "models": bundle.manifest["models"],
        "worker_sha256": bundle.manifest["worker_sha256"],
        "upstream": bundle.manifest["upstream"],
        "dependencies": bundle.manifest["dependencies"],
        "device": bundle.manifest["measurements"]["device"],
        "code": code_identity(),
        "frozen_settings": frozen,
        "stages": stages,
        "inference": bundle.manifest["measurements"],
        "demo_processing": result.manifest["measurements"],
        "limits": {
            "median_px": 0.005 * np.hypot(*video.size),
            "maximum_px": 0.01 * np.hypot(*video.size),
            "target_human_calibratable_coverage": 0.9,
        },
        "human_evaluation": "pending_explicit_user_references",
        "human_reviewed": False,
        "generalization_claim": False,
        "player_model_changed": False,
    }
    write_json(output / "experiment.json", report)
    print("Report:", output / "experiment.json", "Run:", result.directory, flush=True)


if __name__ == "__main__":
    main()
