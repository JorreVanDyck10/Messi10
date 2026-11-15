from copy import deepcopy

import numpy as np
from test_automatic_calibration import observation
from test_field_motion import texture

from football_pipeline.automatic_calibration import transform
from football_pipeline.field_layout import POINTS_UV
from football_pipeline.field_layout_bridge import estimate_layout_bridge
from football_pipeline.field_motion import MOTION_RANK_SETTINGS, CameraCalibration, estimate_checked


def collinear():
    ids = [1, 4, 8, 13]
    xy = transform([POINTS_UV[i] for i in ids], np.array([[560, 0, 40], [0, 280, 40], [0, 0, 1]]))
    return {
        "points": [{"id": i, "x": float(x), "y": float(y), "confidence": 0.95} for i, (x, y) in zip(ids, xy)],
        "lines": [],
    }


def test_four_collinear_points_do_not_invent_a_direct_fit_but_can_use_a_trusted_anchor():
    row = collinear()
    before = deepcopy(row)
    assert estimate_checked(row, (640, 360), MOTION_RANK_SETTINGS)["status"] == "degenerate_geometry"
    direct = estimate_layout_bridge(row, (640, 360), MOTION_RANK_SETTINGS)
    assert direct["status"] == "insufficient_fit_geometry"
    assert direct["homography"] is None
    camera = CameraCalibration(2, MOTION_RANK_SETTINGS)
    assert camera.update(texture(), direct, 0)["status"] != "valid"
    anchor = estimate_checked(observation(), (640, 360), MOTION_RANK_SETTINGS)
    camera = CameraCalibration(2, MOTION_RANK_SETTINGS)
    camera.update(texture(), anchor, 0)
    for i in range(1, 5):
        state = camera.update(texture(), direct, i)
        assert state["status"] == "valid"
        assert state["reference_frame"] == 0
        assert state["source"] == "tracked"
    assert camera.update(texture(), direct, 5)["status"] == "bridge_expired"
    assert row == before


def test_collapsed_identifiable_layout_and_invalid_pixels_remain_hard_failures():
    collapsed = observation()
    for p in collapsed["points"]:
        p["x"] = 100
    assert (
        estimate_layout_bridge(collapsed, (640, 360), MOTION_RANK_SETTINGS)["status"] == "degenerate_geometry"
    )
    invalid = collinear()
    invalid["points"][0]["x"] = -1
    assert (
        estimate_layout_bridge(invalid, (640, 360), MOTION_RANK_SETTINGS)["status"] == "invalid_observation"
    )


def test_semantic_disagreement_and_camera_cut_still_close_the_bridge():
    anchor = estimate_checked(observation(), (640, 360), MOTION_RANK_SETTINGS)
    for cut in (False, True):
        row = collinear()
        if not cut:
            row["points"][0]["x"] += 70
        direct = estimate_layout_bridge(row, (640, 360), MOTION_RANK_SETTINGS)
        camera = CameraCalibration(25, MOTION_RANK_SETTINGS)
        camera.update(texture(), anchor, 0)
        state = camera.update(np.full_like(texture(), 255) if cut else texture(), direct, 1)
        assert state["status"] == ("camera_cut" if cut else "motion_semantic_disagreement")
        assert state["homography"] is None
