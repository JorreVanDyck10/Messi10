"""Run real player inference, field projection and video encoding, then audit the result."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch

from football_pipeline.automatic_calibration import load_automatic_calibration
from football_pipeline.contracts import PipelineError, write_json
from football_pipeline.pipeline import process_video, validate_completed
from football_pipeline.video import ROOT, inspect_video


def verify_records(directory: Path, manifest: dict) -> dict:
    roles, displayed_roles, projections = Counter(), Counter(), Counter()
    known_counts, unknown_frames, empty_frames = [], 0, 0
    known_person_counts, unknown_person_frames = [], 0
    count = 0
    for line in (directory / "framegegevens.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        assert row["frame_index"] == count, "Non-sequential source frames"
        assert math.isclose(
            row["timestamp_s"], count / (manifest["video"]["fps_num"] / manifest["video"]["fps_den"])
        ), "Timestamp differs from source"
        width, height = row["image_size"]
        summary = row["player_summary"]
        detections = row["detections"]
        empty_frames += not detections
        counted = 0
        counted_persons = 0
        for detection in detections:
            role = detection["semantic_class"]
            roles[role] += 1
            displayed_roles[role] += detection["confidence"] >= 0.25
            projections[detection["projection_status"]] += 1
            box = np.asarray(detection["bbox_xyxy"])
            assert box.shape == (4,) and np.isfinite(box).all(), "Invalid source box"
            assert 0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height
            assert math.isfinite(detection["confidence"]) and 0 <= detection["confidence"] <= 1
            position = detection["field_position"]
            if position is not None:
                uv = np.asarray(position)
                assert uv.shape == (2,) and np.isfinite(uv).all() and ((uv >= 0) & (uv <= 1)).all()
                assert detection["projection_status"] == "valid"
                counted_persons += role == "person" and detection["confidence"] >= 0.25
            if detection["counted_as_player"]:
                assert role == "player" and position is not None and detection["confidence"] >= 0.25
                assert row["calibration"]["status"] == "valid"
                counted += 1
        if summary["on_field"] is None:
            unknown_frames += 1
            assert counted == 0
        else:
            assert summary["on_field"] == counted
            known_counts.append(counted)
        if "persons_on_field" in summary:
            if summary["persons_on_field"] is None:
                unknown_person_frames += 1
                assert row["calibration"]["status"] != "valid"
                assert counted_persons == 0
            else:
                assert summary["persons_on_field"] == counted_persons
                known_person_counts.append(counted_persons)
        count += 1
    encoded = inspect_video(directory / "samengestelde_video.mp4")
    assert count == manifest["video"]["frame_count"] == encoded.frame_count
    assert encoded.codec == "h264" and encoded.size == (1920, 720)
    return {
        "frames": count,
        "detections_by_role": dict(roles),
        "displayed_detections_by_role": dict(displayed_roles),
        "projection_status_counts": dict(projections),
        "unknown_player_count_frames": unknown_frames,
        "empty_detection_frames": empty_frames,
        "unknown_person_count_frames": unknown_person_frames,
        "known_person_count_min_median_max": [
            int(min(known_person_counts)),
            float(np.median(known_person_counts)),
            int(max(known_person_counts)),
        ]
        if known_person_counts
        else None,
        "known_player_count_min_median_max": [
            int(min(known_counts)),
            float(np.median(known_counts)),
            int(max(known_counts)),
        ]
        if known_counts
        else None,
        "checks": [
            "source_coordinates",
            "finite_confidence",
            "normalized_field_positions",
            "role_and_field_count_filter",
            "unknown_count_without_field",
            "frame_synchronization",
            "h264_encoding",
            "artifact_hashes",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--automatic-calibration", type=Path, required=True)
    parser.add_argument("--models", type=Path, default=ROOT / "configs/models.json")
    parser.add_argument("--runs", type=Path, default=ROOT / "runs")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--replay-run", type=Path, help="Reuse verified real detections for a new render")
    args = parser.parse_args()
    try:
        result = process_video(
            args.video,
            load_automatic_calibration(args.automatic_calibration),
            args.models,
            args.runs,
            replay_run=args.replay_run,
            progress=lambda n, total, elapsed: print(f"{n}/{total} frames | {elapsed:.1f} s", flush=True),
        )
        manifest = validate_completed(result.directory)
        report = {
            "status": "passed",
            "recorded_at": datetime.now(UTC).isoformat(),
            "run_directory": str(result.directory),
            "video_sha256": manifest["video"]["sha256"],
            "model_profile": str(args.models.resolve()),
            "models": manifest["models"]["models"],
            "inference_reused_from": manifest.get("replayed_from"),
            "original_inference_measurements": validate_completed(args.replay_run)["measurements"]
            if args.replay_run
            else None,
            "semantic_classes": sorted(
                {role for spec in manifest["models"]["models"] for role in spec["class_mapping"].values()}
            ),
            "dependencies": manifest["dependencies"],
            "cuda_available": torch.cuda.is_available(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "audit": verify_records(result.directory, manifest),
            "measurements": manifest["measurements"],
            "human_accuracy_reference": None,
            "tracking_enabled": False,
            "limitations": [
                "Technical integration check; no new detection accuracy score.",
                "Automatic-camera player IDs remain disabled pending camera-motion validation.",
                "Only the recorded model classes are recognized; no individual identity or team recognition.",
            ],
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.report, report)
        print(args.report.resolve())
    except (PipelineError, AssertionError) as exc:
        raise SystemExit(f"Player pipeline verification failed: {exc}") from exc


if __name__ == "__main__":
    main()
