from copy import deepcopy

import cv2
import numpy as np
import pytest
from test_automatic_calibration import bundle_for, observation
from test_field_motion import texture

from football_pipeline.automatic_calibration import AutomaticCalibration, project_automatic, transform
from football_pipeline.contracts import Detection, PipelineError
from football_pipeline.field_bounds import contains_footpoint, visible_field_polygon
from football_pipeline.field_motion import (
    DEFAULT_SETTINGS,
    RELIABLE_SETTINGS,
    CameraCalibration,
    estimate_checked,
)
from football_pipeline.render import automatic_preview


def detected(inverse=None):
    return estimate_checked(observation(inverse=inverse), (640, 360), RELIABLE_SETTINGS)


def missing():
    return estimate_checked({"points": [], "lines": []}, (640, 360), RELIABLE_SETTINGS)


def test_visible_polygon_is_clipped_when_all_pitch_corners_are_offscreen():
    inverse = np.array([[900, 0, -150], [0, 500, -70], [0, 0, 1.0]])
    matrix = np.linalg.inv(inverse)
    polygon = visible_field_polygon(matrix, (640, 360), [[200, 100], [400, 200]])
    assert np.min(polygon, axis=0) == pytest.approx([0, 0])
    assert np.max(polygon, axis=0) == pytest.approx([639, 359])
    assert contains_footpoint(polygon, (200, 180))


def test_horizon_clipping_never_requires_virtual_corners_on_same_branch():
    # u=x/(x+200), v=(y-100)/(x+200): a horizon is in the virtual pitch.
    matrix = np.array([[1, 0, 0], [0, 1, -100], [1, 0, 200]], float)
    polygon = visible_field_polygon(matrix, (640, 360), [[200, 120], [400, 220]])
    assert contains_footpoint(polygon, (200, 120))
    assert not contains_footpoint(polygon, (200, 90))
    assert np.isfinite(polygon).all()
    assert np.asarray(polygon).min() >= 0
    assert transform(polygon, matrix).min() >= -1e-12


def test_projected_footpoints_use_polygon_and_uv_without_snapping():
    state = detected()
    assert state["status"] == "valid"
    assert state["visible_field_polygon_xy"] is not None
    for x, y, expected in [(200, 180, "valid"), (39, 180, "outside_field"), (200, 359, "truncated_bottom")]:
        d = Detection("a", "fixture", 0, "player", [x - 2, y - 20, x + 2, y], 0.9)
        project_automatic(d, state, (640, 360))
        assert d.projection_status == expected
        assert (d.field_position is not None) == (expected == "valid")
    corrupt = dict(state, visible_field_polygon_xy=None)
    d = Detection("a", "fixture", 0, "player", [198, 160, 202, 180], 0.9)
    project_automatic(d, corrupt, (640, 360))
    assert d.field_position is None
    assert d.projection_status == "invalid_transform"
    image = automatic_preview(np.zeros((360, 640, 3), np.uint8), state)
    assert image.any()


def test_direct_semantic_jump_rejected_even_with_internally_perfect_points():
    frame = texture()
    camera = CameraCalibration(25, RELIABLE_SETTINGS)
    camera.update(frame, detected(), 0)
    jumped = detected([[560, 0, 75], [0, 280, 40], [0, 0, 1]])
    assert jumped["status"] == "valid"
    rejected = camera.update(frame, jumped, 1)
    assert rejected["status"] == "temporal_disagreement"
    assert rejected["homography"] is None
    assert rejected["visible_field_polygon_xy"] is None
    assert rejected["temporal_quality"]["maximum_error_px"] > 30
    assert camera.state is camera.previous is camera.anchor is camera.last_recognition is None
    assert camera.update(frame, detected(), 2)["source"] == "detected"


def test_real_pan_zoom_direct_recognition_agrees_with_measured_motion():
    frame = texture()
    inverse = np.array([[560, 0, 40], [0, 280, 40], [0, 0, 1.0]])
    movement = np.array([[1.01, 0, 3], [0, 1.01, 2], [0, 0, 1.0]])
    camera = CameraCalibration(25, RELIABLE_SETTINGS)
    camera.update(frame, detected(inverse), 0)
    moved = cv2.warpPerspective(frame, movement, (640, 360))
    result = camera.update(moved, detected(movement @ inverse), 1)
    assert result["status"] == "valid", result
    assert result["temporal_quality"]["status"] == "consistent"
    assert result["temporal_quality"]["median_error_px"] < 1
    assert result["source"] == "detected"
    assert result["reference_frame"] == 1


def test_cut_resets_history_even_with_valid_direct_recognition():
    camera = CameraCalibration(25, RELIABLE_SETTINGS)
    camera.update(texture(), detected(), 0)
    new_scene = np.full((360, 640, 3), 230, np.uint8)
    result = camera.update(new_scene, detected(), 1)
    assert result["status"] == "valid"
    assert result["temporal_quality"]["status"] == "camera_cut"
    assert result["temporal_quality"]["camera_reset"] is True
    assert camera.anchor == camera.last_recognition == 1
    assert result["reference_frame"] == 1
    assert camera.update(new_scene, missing(), 2)["status"] != "valid"
    assert camera.state is camera.last_recognition is None


def test_no_motion_evidence_still_allows_independently_checked_direct_recognition():
    camera = CameraCalibration(25, RELIABLE_SETTINGS)
    frame = np.full((360, 640, 3), (50, 100, 50), np.uint8)
    camera.update(frame, detected(), 0)
    result = camera.update(frame, detected(), 1)
    assert result["status"] == "valid"
    assert result["temporal_quality"]["status"] == "motion_unavailable"
    assert result["temporal_quality"]["reason"] == "insufficient_motion_matches"


def test_gap_failure_and_expiry_clear_all_calibration_metadata():
    frame = texture()
    camera = CameraCalibration(10, RELIABLE_SETTINGS)
    camera.update(frame, detected(), 0)
    assert camera.update(frame, missing(), 1)["status"] == "valid"
    expired = camera.update(frame, missing(), 21)
    assert expired["status"] != "valid"
    assert expired["temporal_quality"]["status"] == "frame_gap"
    assert expired["reference_frame"] is expired["age_s"] is None
    camera.update(frame, detected(), 22)
    for i in range(23, 43):
        assert camera.update(frame, missing(), i)["status"] == "valid"
    assert camera.update(frame, missing(), 43)["status"] == "bridge_expired"
    assert camera.anchor is camera.last_recognition is camera.state is None


def test_legacy_profile_remains_active_and_does_not_gain_new_behavior(demo_fixture, tmp_path):
    from football_pipeline.video import inspect_video

    assert DEFAULT_SETTINGS["version"] == 2
    frame = texture()
    camera = CameraCalibration(25)
    camera.update(frame, detected(), 0)
    jumped = detected([[560, 0, 75], [0, 280, 40], [0, 0, 1]])
    assert camera.update(frame, jumped, 1)["status"] == "valid"
    video = inspect_video(demo_fixture["video"])
    original = bundle_for(video, tmp_path)
    old = AutomaticCalibration(original.manifest, original.observations_path, DEFAULT_SETTINGS)
    new = AutomaticCalibration(original.manifest, original.observations_path, RELIABLE_SETTINGS)
    assert len({old.identity, new.identity, original.identity}) == 3
    assert next(new.frames(video))["schema_version"] == 3
    assert "visible_field_polygon_xy" not in next(old.frames(video))
    invalid = deepcopy(RELIABLE_SETTINGS)
    invalid["maximum_age_s"] = 3
    with pytest.raises(PipelineError):
        CameraCalibration(25, invalid)


def test_candidate_pipeline_and_saved_profile_roundtrip(demo_fixture, tmp_path):
    import json

    from football_pipeline.automatic_calibration import load_automatic_calibration
    from football_pipeline.demo import SyntheticDetector
    from football_pipeline.pipeline import process_video, validate_completed
    from football_pipeline.video import inspect_video

    video = inspect_video(demo_fixture["video"])
    original = bundle_for(video, tmp_path / "bundle")
    candidate = AutomaticCalibration(original.manifest, original.observations_path, RELIABLE_SETTINGS)
    result = process_video(
        video.path, candidate, demo_fixture["models"], tmp_path / "runs", detector=SyntheticDetector()
    )
    manifest = validate_completed(result.directory)
    assert manifest["field_settings"]["version"] == 3
    loaded = load_automatic_calibration(result.directory / "calibration.json")
    assert loaded.settings == candidate.settings
    assert loaded.identity == candidate.identity
    records = [
        json.loads(line) for line in (result.directory / "framegegevens.jsonl").read_text().splitlines()
    ]
    assert len(records) == video.frame_count
    assert records[1]["calibration"]["temporal_quality"]["status"] in {"consistent", "motion_unavailable"}
    assert records[0]["calibration"]["visible_field_polygon_xy"] is not None
