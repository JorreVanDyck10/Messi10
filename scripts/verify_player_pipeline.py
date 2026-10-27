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
from football_pipeline.contracts import Detection, FrameRecord, PipelineError, write_json
from football_pipeline.detection import available_roles
from football_pipeline.participants import player_summary
from football_pipeline.pipeline import process_video, validate_completed
from football_pipeline.video import ROOT, inspect_video


def verify_records(directory: Path, manifest: dict) -> dict:
    roles, displayed_roles, projections = Counter(), Counter(), Counter()
    counted_teams, team_methods = Counter(), Counter()
    role_classified, team_assigned = 0, 0
    appearance = manifest["models"].get("appearance")
    roles_available = available_roles(manifest["models"])
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
        restored = FrameRecord(
            row["frame_index"],
            row["timestamp_s"],
            tuple(row["image_size"]),
            [Detection.from_dict(d) for d in detections],
            row.get("calibration"),
            player_model_available=row.get("player_model_available", "player" in roles_available),
        )
        assert summary == player_summary(restored), "Exported role/team totals differ from current detections"
        empty_frames += not detections
        counted = 0
        counted_persons = 0
        for detection in detections:
            role = detection["semantic_class"]
            assert role in roles_available, "Output role missing from selected model capabilities"
            roles[role] += 1
            displayed_roles[role] += detection["confidence"] >= 0.25
            projections[detection["projection_status"]] += 1
            box = np.asarray(detection["bbox_xyxy"])
            assert box.shape == (4,) and np.isfinite(box).all(), "Invalid source box"
            assert 0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height
            assert math.isfinite(detection["confidence"]) and 0 <= detection["confidence"] <= 1
            if appearance and role != "ball":
                assert detection["role_model_id"] == appearance["model_id"], "Wrong role classifier"
                role_id = detection["role_class_id"]
                score = detection["role_confidence"]
                assert type(role_id) is int and 0 <= role_id < len(appearance["role_names"])
                assert score is not None and math.isfinite(score) and 0 <= score <= 1
                expected = (
                    appearance["role_names"][role_id] if score >= appearance["role_confidence"] else "person"
                )
                assert role == expected, "Role output differs from classifier score/class ID"
                role_classified += 1
            team_id = detection.get("team_id")
            if team_id is not None:
                assert role == "player" and team_id in {"team_a", "team_b", "A", "B"}, (
                    "Invalid role/team assignment"
                )
                if team_id in {"A", "B"}:
                    assert manifest.get("team_settings") is not None, "Missing colour-team configuration"
                    source = detection.get("team_source")
                    assert source in {"automatic", "track_history", "manual"}, "Missing team provenance"
                    score = detection.get("team_match_score")
                    assert score is None or (math.isfinite(score) and 0 <= score <= 1)
                    team_methods[source] += 1
                else:
                    score = detection["team_confidence"]
                    assert score is not None and math.isfinite(score) and 0 <= score <= 1
                    assert detection["team_method"] in {"supervised_match", "video_colour_clusters"}
                    if detection["team_method"] == "supervised_match":
                        assert appearance and score >= appearance["team_confidence"]
                        assert detection["team_class_id"] == (0 if team_id == "team_a" else 1)
                    else:
                        assert score >= 0.2 and detection.get("team_class_id") is None
                    team_methods[detection["team_method"]] += 1
                team_assigned += 1
            position = detection["field_position"]
            if position is not None:
                uv = np.asarray(position)
                assert uv.shape == (2,) and np.isfinite(uv).all() and ((uv >= 0) & (uv <= 1)).all()
                assert detection["projection_status"] == "valid"
                counted_persons += role == "person" and detection["confidence"] >= 0.25
            if detection["counted_as_player"]:
                assert (
                    role == "player"
                    and position is not None
                    and (detection["confidence"] >= 0.25 or detection.get("track_id") is not None)
                )
                assert row.get("calibration", {"status": "valid"})["status"] == "valid"
                counted_teams[team_id or "unknown"] += 1
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
                assert row.get("calibration", {"status": "valid"})["status"] != "valid"
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
            "role_classifier_identity_and_abstention",
            "team_assignment_roles_and_totals",
        ],
        "role_classified_detections": role_classified,
        "team_assigned_detections": team_assigned,
        "team_assignment_methods": dict(team_methods),
        "counted_player_observations_by_team": dict(counted_teams),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    field = parser.add_mutually_exclusive_group(required=True)
    field.add_argument("--automatic-calibration", type=Path)
    field.add_argument("--auto-field", action="store_true", help="Run the real field worker before detection")
    parser.add_argument("--field-runtime", type=Path, default=ROOT / ".tools/field-runtime.json")
    parser.add_argument("--source", default="")
    parser.add_argument("--usage", default="")
    parser.add_argument("--models", type=Path, default=ROOT / "configs/models.json")
    parser.add_argument("--runs", type=Path, default=ROOT / "runs")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--replay-run", type=Path, help="Reuse verified real detections for a new render")
    args = parser.parse_args()
    try:
        result = process_video(
            args.video,
            load_automatic_calibration(args.automatic_calibration) if args.automatic_calibration else None,
            args.models,
            args.runs,
            replay_run=args.replay_run,
            field_runtime_path=args.field_runtime if args.auto_field else None,
            field_source=args.source,
            field_usage=args.usage,
            field_progress=lambda n, total, elapsed: print(
                f"Field: {n}/{total} frames | {elapsed:.1f} s", flush=True
            ),
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
            "appearance": manifest["models"].get("appearance"),
            "team_calibration": manifest.get("team_calibration"),
            "field_models": json.loads((result.directory / "calibration.json").read_text(encoding="utf-8"))[
                "models"
            ],
            "field_settings": manifest.get("field_settings"),
            "inference_reused_from": manifest.get("replayed_from"),
            "original_inference_measurements": validate_completed(args.replay_run)["measurements"]
            if args.replay_run
            else None,
            "semantic_classes": sorted(available_roles(manifest["models"])),
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
                "Role and team predictions are experimental; this audit supplies no human accuracy reference.",
                "Team A/B denotes supervised known-match kits or neutral video-local clusters, never player names.",
            ],
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.report, report)
        print(args.report.resolve())
    except (PipelineError, AssertionError, OSError, KeyError, TypeError) as exc:
        raise SystemExit(f"Player pipeline verification failed: {exc}") from exc


if __name__ == "__main__":
    main()
