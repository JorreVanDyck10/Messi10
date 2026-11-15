import cv2
import numpy as np
import pytest

from football_pipeline.field_lens import (
    distort_points,
    estimate_lens,
    rectify_image,
    rectify_points,
    validate_lens,
)


@pytest.mark.parametrize("k", [-1.2, -0.8, 0, 0.2])
def test_lens_coordinate_roundtrip_preserves_raw_player_footpoints(k):
    lens = {"model": "division_radial_v1", "image_size": [1280, 720], "k": k}
    original = np.random.default_rng(42).uniform([0, 0], [1279, 719], (200, 2))
    rectified = rectify_points(original, lens)
    assert (rectified >= 0).all() and (rectified < [1280, 720]).all()
    np.testing.assert_allclose(distort_points(rectified, lens), original, atol=1e-8)
    with pytest.raises(ValueError, match="coordinate system"):
        validate_lens(lens, (640, 360))


def test_straight_or_uninformative_grass_does_not_invent_lens_correction():
    frame = np.full((360, 640, 3), (40, 120, 40), np.uint8)
    assert estimate_lens(frame) is None
    cv2.line(frame, (20, 300), (620, 300), (235, 235, 235), 3)
    cv2.line(frame, (60, 40), (60, 330), (235, 235, 235), 3)
    cv2.line(frame, (540, 40), (540, 330), (235, 235, 235), 3)
    assert estimate_lens(frame) is None
    assert rectify_image(frame, None) is frame


def test_curved_touchline_has_held_out_pixels_and_separate_controls():
    lens = {"model": "division_radial_v1", "image_size": [1280, 720], "k": -1.0}
    frame = np.full((720, 1280, 3), (40, 120, 40), np.uint8)
    lines = [
        np.column_stack((np.linspace(20, 1260, 900), np.full(900, 620))),
        np.column_stack((np.full(400, 400), np.linspace(150, 650, 400))),
        np.column_stack((np.full(400, 900), np.linspace(150, 650, 400))),
        np.column_stack((np.linspace(100, 1180, 600), np.full(600, 360))),
    ]
    for line in lines:
        cv2.polylines(
            frame, [np.rint(distort_points(line, lens)).astype(np.int32)], False, (235, 235, 235), 3
        )
    estimated = estimate_lens(frame)
    assert estimated is not None
    assert (
        estimated["quality"]["heldout_after_rmse_px"] < estimated["quality"]["heldout_before_rmse_px"] * 0.3
    )
    assert len(estimated["quality"]["separate_controls"]) >= 2
    assert not estimated["independent_human_accuracy_validation"]
