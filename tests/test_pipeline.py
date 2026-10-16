import json

import pytest

from football_pipeline.contracts import PipelineError, read_json
from football_pipeline.demo import SyntheticDetector
from football_pipeline.pipeline import accept_mvp, process_video, processing_lock, validate_completed
from football_pipeline.video import inspect_video


def test_entire_clip_encoding_sync_empty_frames_cache_and_corruption(demo_fixture, tmp_path):
    fixture = demo_fixture
    detector = SyntheticDetector()
    result = process_video(
        fixture["video"], fixture["calibration"], fixture["models"], tmp_path, detector=detector
    )
    assert result.manifest["status"] == "completed"
    assert result.manifest["evidence_kind"] == "synthetic"
    video = inspect_video(result.video_path)
    assert video.frame_count == 20
    assert video.size == (1920, 720)
    assert video.codec == "h264"
    rows = [json.loads(line) for line in (result.directory / "framegegevens.jsonl").read_text().splitlines()]
    assert [r["frame_index"] for r in rows] == list(range(20))
    assert rows[8]["detections"] == []
    assert rows[19]["timestamp_s"] == pytest.approx(1.9)
    assert rows[0]["image_size"] == [640, 360]
    assert len(list((result.directory / "controlebeelden").glob("*.jpg"))) == 3
    cached = process_video(
        fixture["video"], fixture["calibration"], fixture["models"], tmp_path, detector=detector
    )
    assert cached.reused and cached.directory == result.directory
    with pytest.raises(PipelineError, match="geen echte MVP"):
        accept_mvp(result.directory, "tester", True)
    (result.directory / "framegegevens.jsonl").write_text("corrupted", encoding="utf-8")
    with pytest.raises(PipelineError, match="beschadigd"):
        validate_completed(result.directory)
    replacement = process_video(
        fixture["video"], fixture["calibration"], fixture["models"], tmp_path, detector=detector
    )
    assert not replacement.reused and replacement.directory != result.directory


def test_encoder_failure_never_marked_complete(demo_fixture, tmp_path, monkeypatch):
    from football_pipeline import pipeline

    class BrokenWriter:
        closed = False

        def __init__(self, *args):
            pass

        def write(self, frame):
            raise PipelineError("simulated disk failure")

        def close(self, abort=False):
            self.closed = True

    monkeypatch.setattr(pipeline, "VideoWriter", BrokenWriter)
    with pytest.raises(PipelineError, match="simulated disk failure"):
        process_video(
            demo_fixture["video"],
            demo_fixture["calibration"],
            demo_fixture["models"],
            tmp_path,
            detector=SyntheticDetector(),
        )
    manifests = list(tmp_path.glob("*/runmanifest.json"))
    assert len(manifests) == 1
    manifest = read_json(manifests[0])
    assert manifest["status"] == "failed"
    assert not (manifests[0].parent / "samengestelde_video.mp4").exists()


def test_tracking_requires_real_mvp_acceptance(demo_fixture, tmp_path):
    from football_pipeline.video import ROOT

    with pytest.raises(PipelineError, match="Tracking vereist"):
        process_video(
            demo_fixture["video"],
            demo_fixture["calibration"],
            demo_fixture["models"],
            tmp_path,
            detector=SyntheticDetector(),
            tracker_config_path=ROOT / "configs/bytetrack.yaml",
        )


def test_only_one_processing_job_per_root(tmp_path):
    with processing_lock(tmp_path), pytest.raises(PipelineError, match="al een verwerking"):
        with processing_lock(tmp_path):
            pass


def test_tracking_pipeline_preserves_empty_frame_without_predicted_position(
    demo_fixture, tmp_path, monkeypatch
):
    from football_pipeline import pipeline
    from football_pipeline.video import ROOT

    # Test the plumbing under an explicitly stubbed acceptance boundary; production never skips that boundary.
    monkeypatch.setattr(pipeline, "check_mvp_acceptance", lambda *args: {"test_boundary_stub": True})
    result = process_video(
        demo_fixture["video"],
        demo_fixture["calibration"],
        demo_fixture["models"],
        tmp_path,
        detector=SyntheticDetector(),
        tracker_config_path=ROOT / "configs/bytetrack.yaml",
    )
    rows = [json.loads(line) for line in (result.directory / "framegegevens.jsonl").read_text().splitlines()]
    assert rows[7]["detections"][0]["track_id"] == rows[9]["detections"][0]["track_id"] == 1
    assert rows[8]["detections"] == []
    assert result.manifest["tracker_effective"]["effective_buffer_updates"] == 30


def test_pipeline_projects_before_tracking_and_preserves_nonplayers(demo_fixture, tmp_path, monkeypatch):
    from football_pipeline import pipeline
    from football_pipeline.contracts import Detection
    from football_pipeline.video import ROOT

    class MixedRoles(SyntheticDetector):
        def detect(self, frame, frame_index):
            players = super().detect(frame, frame_index)
            if not players:
                return []
            # Deliberately place an excluded candidate first to exercise ByteTrack's index mapping.
            return [
                Detection(f"{frame_index}:off", "fixture", 0, "player", [5, 100, 15, 150], 0.9),
                Detection(f"{frame_index}:s", "fixture", 3, "steward", [200, 100, 220, 180], 0.9),
                *players,
            ]

    monkeypatch.setattr(pipeline, "check_mvp_acceptance", lambda *args: {"test_boundary_stub": True})
    result = process_video(
        demo_fixture["video"],
        demo_fixture["calibration"],
        demo_fixture["models"],
        tmp_path,
        detector=MixedRoles(),
        tracker_config_path=ROOT / "configs/bytetrack.yaml",
    )
    rows = [json.loads(line) for line in (result.directory / "framegegevens.jsonl").read_text().splitlines()]
    first = rows[0]
    assert len(first["detections"]) == 3
    assert first["player_summary"]["on_field"] == 1
    assert first["player_summary"]["outside_field"] == 1
    assert first["player_summary"]["other_roles"] == {"steward": 1}
    assert [d["track_id"] for d in first["detections"]] == [None, None, 1]
    assert first["detections"][1]["projection_status"] == "valid"
    assert rows[8]["player_summary"]["on_field"] == 0
    assert rows[9]["detections"][2]["track_id"] == 1
    assert result.manifest["player_policy"]["requires_valid_current_calibration"] is True


def test_technical_pilot_never_impersonates_human_review_or_enables_tracking(demo_fixture, tmp_path):
    from dataclasses import replace

    from football_pipeline.video import ROOT

    calibration = replace(
        demo_fixture["calibration"],
        review={
            "kind": "agent_technical",
            "technical_passed": True,
            "approved": False,
            "human_reviewed": False,
            "static_camera_technical_check": True,
            "temporal_frames": [0, 10, 19],
        },
    )
    with pytest.raises(PipelineError, match="Bevestig reviewer"):
        process_video(
            demo_fixture["video"], calibration, demo_fixture["models"], tmp_path, detector=SyntheticDetector()
        )
    result = process_video(
        demo_fixture["video"],
        calibration,
        demo_fixture["models"],
        tmp_path,
        detector=SyntheticDetector(),
        technical_pilot=True,
    )
    assert result.manifest["technical_pilot"] is True
    assert result.manifest["evidence_kind"] == "synthetic_technical_pilot"
    assert read_json(result.directory / "calibration.json")["review"]["approved"] is False
    with pytest.raises(PipelineError, match="geen echte MVP"):
        accept_mvp(result.directory, "tester", True)
    with pytest.raises(PipelineError, match="zonder tracking"):
        process_video(
            demo_fixture["video"],
            calibration,
            demo_fixture["models"],
            tmp_path,
            technical_pilot=True,
            tracker_config_path=ROOT / "configs/bytetrack.yaml",
        )


def test_technical_pilot_requires_explicit_technical_evidence(demo_fixture, tmp_path):
    with pytest.raises(PipelineError, match="expliciete technische"):
        process_video(
            demo_fixture["video"],
            demo_fixture["calibration"],
            demo_fixture["models"],
            tmp_path,
            technical_pilot=True,
            detector=SyntheticDetector(),
        )
