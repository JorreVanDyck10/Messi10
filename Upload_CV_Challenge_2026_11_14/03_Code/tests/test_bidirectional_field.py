from copy import deepcopy

import numpy as np
import pytest
from test_automatic_calibration import observation
from test_field_motion import texture

from football_pipeline.bidirectional_field import backward_backfill
from football_pipeline.contracts import PipelineError
from football_pipeline.field_motion import MOTION_RANK_SETTINGS, CameraCalibration, estimate_checked


def timeline(count=7):
    frame = texture()
    unknown = estimate_checked({"points": [], "lines": []}, (640, 360), MOTION_RANK_SETTINGS)
    direct = [deepcopy(unknown) for _ in range(count)]
    direct[-1] = estimate_checked(observation(), (640, 360), MOTION_RANK_SETTINGS)
    camera = CameraCalibration(2, MOTION_RANK_SETTINGS)
    forward = [camera.update(frame, d, i) for i, d in enumerate(direct)]
    return frame, direct, forward


def test_future_anchor_fills_only_its_bounded_window_and_keeps_forward_valid_data():
    frame, direct, forward = timeline()
    before = deepcopy(forward)
    result = backward_backfill(
        direct, forward, ((i, frame) for i in range(6, -1, -1)), 2, MOTION_RANK_SETTINGS
    )
    assert result[-1] == forward[-1]
    assert forward == before
    for index in range(2, 6):
        assert result[index]["status"] == "valid"
        assert result[index]["source"] == "tracked_backward"
        assert result[index]["reference_frame"] == 6
        assert result[index]["age_s"] == (6 - index) / 2
    assert all(result[i]["status"] != "valid" for i in (0, 1))


def test_reverse_motion_cannot_cross_a_camera_cut_or_start_without_an_anchor():
    frame, direct, forward = timeline(3)
    result = backward_backfill(
        direct, forward, [(2, frame), (1, np.zeros_like(frame)), (0, frame)], 2, MOTION_RANK_SETTINGS
    )
    assert all(result[i]["status"] != "valid" for i in (0, 1))
    no_anchor = [deepcopy(direct[0]) for _ in range(3)]
    result = backward_backfill(no_anchor, forward, ((i, frame) for i in (2, 1, 0)), 2, MOTION_RANK_SETTINGS)
    assert all(result[i]["status"] != "valid" for i in (0, 1))


def test_reverse_frame_validation_rejects_gaps_and_incomplete_timelines():
    frame, direct, forward = timeline(3)
    with pytest.raises(PipelineError, match="descending"):
        backward_backfill(direct, forward, [(2, frame), (0, frame)], 2, MOTION_RANK_SETTINGS)
    with pytest.raises(PipelineError, match="Incomplete"):
        backward_backfill(direct, forward, [(2, frame)], 2, MOTION_RANK_SETTINGS)
