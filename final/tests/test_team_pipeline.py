import csv
import json
from copy import deepcopy

import cv2
import numpy as np
import pytest

from football_pipeline.contracts import Detection, PipelineError, read_json, sha256_file, write_json
from football_pipeline.demo import default_points
from football_pipeline.geometry import create_calibration
from football_pipeline.pipeline import process_video, validate_completed
from football_pipeline.team_results import apply_team_corrections
from football_pipeline.video import ROOT, VideoWriter, inspect_video


class TeamFixtureDetector:
    evidence_kind = "synthetic"
    provenance = {"fixture": "six_outfield_players_goalkeeper_official_and_empty_frame"}

    def detect(self, frame, frame_index):
        if frame_index == 8:
            return []
        return [
            Detection(
                f"{frame_index}:{i}",
                "fixture",
                0 if i < 7 else 1,
                "player" if i < 7 else "referee",
                [65 + i * 65, 120, 89 + i * 65, 190],
                0.15 if frame_index == 6 and i == 0 else 0.9,
            )
            for i in range(8)
        ]


@pytest.fixture
def team_run(tmp_path, model_manifest, monkeypatch):
    from football_pipeline import pipeline

    video_path = tmp_path / "team-fixture.mp4"
    writer = VideoWriter(video_path, 640, 360, 10, 1)
    detector = TeamFixtureDetector()
    try:
        for i in range(16):
            frame = np.full((360, 640, 3), (35, 95, 35), np.uint8)
            for j, d in enumerate(detector.detect(frame, i)):
                color = (30, 30, 220) if j < 3 else (220, 40, 30) if j < 6 else (30, 230, 30)
                x1, y1, x2, y2 = map(int, d.bbox_xyxy)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
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
        "temporal_frames": [0, 8, 15],
        "source": "synthetic",
        "usage": "engineering test",
    }
    profile, model = model_manifest
    model["models"][0]["class_mapping"]["1"] = "referee"
    model["models"][0]["expected_names"]["1"] = "referee"
    write_json(profile, model)
    # This is software validation with injected detections, never human acceptance.
    monkeypatch.setattr(pipeline, "check_mvp_acceptance", lambda *a: {"test_stub": True})
    arguments = dict(
        tracker_config_path=ROOT / "configs/bytetrack.yaml",
        detector=detector,
        team_config_path=ROOT / "configs/teams.json",
    )
    result = process_video(video_path, calibration, profile, tmp_path / "runs", **arguments)
    return result, (video_path, calibration, profile, arguments)


def records(result):
    return [json.loads(line) for line in (result.directory / "framegegevens.jsonl").read_text().splitlines()]


def test_full_team_video_exports_and_cache(team_run):
    result, (video_path, calibration, profile, arguments) = team_run
    validate_completed(result.directory)
    assert result.manifest["evidence_kind"] == "synthetic"
    assert result.manifest["team_model_status"] == "available"
    assert result.manifest["measurements"]["teams"]["runtime_s"] > 0
    rows = records(result)
    assert len(rows) == 16
    assert rows[8]["player_summary"]["on_field"] == 0
    for row in rows:
        summary = row["player_summary"]
        assert sum(summary["by_team"].values()) == summary["on_field"]
    assert sorted(rows[7]["player_summary"]["by_team"].values()) == [1, 3, 3]
    assert rows[6]["detections"][0]["track_id"] == rows[5]["detections"][0]["track_id"]
    assert rows[6]["detections"][0]["counted_as_player"]
    assert all(d["team_id"] is None for r in rows for d in r["detections"] if d["semantic_class"] != "player")
    with (result.directory / "teamtelling.csv").open(encoding="utf-8-sig", newline="") as stream:
        table = list(csv.DictReader(stream))
    assert len(table) == 16 and table[7]["on_field"] == "7"
    output = inspect_video(result.video_path)
    assert output.frame_count == 16 and output.fps == 10 and output.size == (1920, 720)
    cached = process_video(video_path, calibration, profile, result.directory.parent, **arguments)
    assert cached.reused and cached.directory == result.directory
    (result.directory / "teamtelling.csv").write_text("corrupt")
    with pytest.raises(PipelineError, match="beschadigd"):
        validate_completed(result.directory)


def test_corrections_are_new_runs_preserve_observations_and_bind_to_root(team_run, monkeypatch):
    result, _ = team_run
    initial = records(result)
    old_hash = sha256_file(result.directory / "framegegevens.jsonl")
    goal_id = str(initial[7]["detections"][6]["track_id"])
    request = read_json(result.directory / "teamcorrecties.json")
    request.update(teams={"A": {"name": "Thuis", "display_color": "#ffbb22"}}, track_overrides={goal_id: "A"})
    # Any accidental inference, geometric projection or tracker invocation must fail.
    monkeypatch.setattr(
        TeamFixtureDetector, "detect", lambda *a: pytest.fail("Detector ran during correction")
    )
    from football_pipeline import tracking

    monkeypatch.setattr(
        tracking.ByteTrackAdapter, "update", lambda *a, **k: pytest.fail("Tracker ran during correction")
    )
    corrected = apply_team_corrections(result.directory, request, result.directory.parent)
    assert corrected.directory != result.directory
    assert sha256_file(result.directory / "framegegevens.jsonl") == old_hash
    validate_completed(corrected.directory)
    assert corrected.manifest["team_origin"]["cache_key"] == result.manifest["cache_key"]
    assert corrected.manifest["measurements"]["inference_or_replay_s"] == 0
    after = records(corrected)
    changed = {"team_id", "team_status", "team_source", "team_match_score"}
    for a, b in zip(initial, after):
        assert a["calibration"] == b["calibration"] if "calibration" in a else "calibration" not in b
        for old, new in zip(a["detections"], b["detections"]):
            assert {k: v for k, v in old.items() if k not in changed} == {
                k: v for k, v in new.items() if k not in changed
            }
            if str(new["track_id"]) == goal_id:
                assert new["team_id"] == "A" and new["team_source"] == "manual"
    assert after[0]["detections"][6]["team_id"] == "A"
    assert apply_team_corrections(corrected.directory, request, result.directory.parent).reused
    other = deepcopy(request)
    other["track_overrides"][goal_id] = "B"
    second = apply_team_corrections(corrected.directory, other, result.directory.parent)
    assert second.directory != corrected.directory
    assert records(second)[0]["detections"][6]["team_id"] == "B"
    with pytest.raises(PipelineError, match="oorspronkelijke analyse"):
        apply_team_corrections(
            result.directory, {**request, "source_run_key": "different"}, result.directory.parent
        )


def test_correction_failure_leaves_original_and_failed_manifest(team_run):
    result, _ = team_run
    request = read_json(result.directory / "teamcorrecties.json")
    source_video = result.manifest["video"]["path"]
    from pathlib import Path

    Path(source_video).write_bytes(b"changed source")
    with pytest.raises(PipelineError, match="oorspronkelijke"):
        apply_team_corrections(result.directory, request, result.directory.parent)
    assert result.manifest["status"] == "completed"
    failed = [
        read_json(path)
        for path in result.directory.parent.glob("*/runmanifest.json")
        if path.parent != result.directory
    ]
    assert len(failed) == 1 and failed[0]["status"] == "failed"
