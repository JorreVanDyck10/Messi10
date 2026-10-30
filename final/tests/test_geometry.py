from copy import deepcopy
from dataclasses import replace

import numpy as np
import pytest

from football_pipeline.contracts import Detection, PipelineError
from football_pipeline.geometry import create_calibration, project_detection


def detection(box):
    return Detection("0:0", "test", 0, "player", box, 0.9)


def test_known_perspective_transform_and_independent_checks(video_metadata, calibration):
    # Generate image points using a non-affine perspective transform, then recover its inverse.
    matrix = np.array([[420, 80, 60], [20, 250, 40], [0.1, 0.2, 1]])
    points = deepcopy(calibration.points)
    for p in points:
        projected = matrix @ [p["u"], p["v"], 1]
        p["x"], p["y"] = (projected[:2] / projected[2]).tolist()
    result = create_calibration(video_metadata, points)
    assert max(result.check_errors_px) < 1e-4
    pixel = matrix @ [0.4, 0.6, 1]
    x, y = pixel[:2] / pixel[2]
    item = detection([x - 5, y - 20, x + 5, y])
    project_detection(item, result)
    assert item.field_position == pytest.approx([0.4, 0.6], abs=1e-6)


@pytest.mark.parametrize("mutation", ["crossed", "duplicate", "collinear", "bad_check", "fit_as_check"])
def test_invalid_calibrations_rejected(video_metadata, calibration, mutation):
    points = deepcopy(calibration.points)
    if mutation == "crossed":
        points[1]["x"], points[2]["x"] = points[2]["x"], points[1]["x"]
        points[1]["y"], points[2]["y"] = points[2]["y"], points[1]["y"]
    elif mutation == "duplicate":
        points[1]["x"], points[1]["y"] = points[0]["x"], points[0]["y"]
    elif mutation == "collinear":
        for p in points[:4]:
            p["y"] = 40
    elif mutation == "bad_check":
        points[4]["y"] += 20
    else:
        points[4].update(x=points[0]["x"], y=points[0]["y"], u=0, v=0)
    with pytest.raises(PipelineError):
        create_calibration(video_metadata, points)


def test_failed_independent_check_exposes_diagnostics_without_moving_click(video_metadata, calibration):
    from football_pipeline.geometry import CalibrationControlError

    points = deepcopy(calibration.points)
    original_y = points[4]["y"]
    points[4]["y"] += 20
    with pytest.raises(CalibrationControlError) as caught:
        create_calibration(video_metadata, points)
    failure = caught.value
    assert failure.diagnostics[0]["clicked"][1] == original_y + 20
    assert failure.diagnostics[0]["predicted"][1] == pytest.approx(original_y)
    assert failure.diagnostics[0]["error_px"] == pytest.approx(20)
    assert failure.median_limit_px == pytest.approx(np.hypot(640, 360) * 0.005)
    assert points[4]["y"] == original_y + 20


@pytest.mark.parametrize(
    "box,status",
    [
        ([310, 100, 330, 180], "valid"),
        ([0, 0, 20, 20], "outside_field"),
        ([300, 100, 330, 360], "truncated_bottom"),
        ([100, 100, 90, 130], "invalid_box"),
        ([1, 2, float("nan"), 8], "invalid_box"),
    ],
)
def test_projection_status_and_no_invented_position(calibration, box, status):
    item = detection(box)
    project_detection(item, calibration)
    assert item.projection_status == status
    assert (item.field_position is not None) == (status == "valid")


def test_loaded_matrix_scale_and_review_are_validated(video_metadata, calibration):
    calibration.validate_for(video_metadata)
    with pytest.raises(PipelineError, match="andere clip"):
        calibration.validate_for(replace(video_metadata, width=1280))
    calibration.homography[0][0] *= 2
    with pytest.raises(PipelineError, match="matrix"):
        calibration.validate_for(video_metadata)


def test_display_resize_does_not_change_geometry(calibration):
    from football_pipeline.contracts import FrameRecord
    from football_pipeline.render import render_frame

    item = detection([300, 100, 340, 180])
    project_detection(item, calibration)
    before = item.field_position.copy()
    output = render_frame(np.zeros((360, 640, 3), dtype=np.uint8), FrameRecord(0, 0, (640, 360), [item]))
    assert output.shape == (720, 1920, 3)
    assert item.field_position == before


def test_homogeneous_zero_divisor_never_creates_a_position(calibration):
    calibration.homography[2] = [0, 0, 0]
    item = detection([300, 100, 340, 180])
    project_detection(item, calibration)
    assert item.projection_status == "invalid_transform"
    assert item.field_position is None


def test_malformed_review_is_an_actionable_error(video_metadata, calibration):
    calibration.review = None
    with pytest.raises(PipelineError, match="reviewrecord"):
        calibration.validate_for(video_metadata)


@pytest.mark.parametrize("side", ["left", "right"])
def test_partial_field_calibration_projects_players_outside_the_fit_region(video_metadata, side):
    from football_pipeline.calibration_input import penalty_area_points

    field_to_image = np.array([[420, 80, 60], [20, 250, 40], [0.1, 0.2, 1]])
    points = penalty_area_points(side)
    for point in points:
        xy = field_to_image @ [point["u"], point["v"], 1]
        point["x"], point["y"] = (xy[:2] / xy[2]).tolist()
    calibration = create_calibration(video_metadata, points)
    for u, expected in ((0.5, "valid"), (1.1, "outside_field")):
        xy = field_to_image @ [u, 0.5, 1]
        x, y = xy[:2] / xy[2]
        player = detection([x - 5, y - 20, x + 5, y])
        project_detection(player, calibration)
        assert player.projection_status == expected
        if expected == "valid":
            assert player.field_position == pytest.approx([0.5, 0.5], abs=1e-6)
    assert max(calibration.check_errors_px) < 0.001


def test_a_partial_view_does_not_accept_points_behind_the_camera(video_metadata):
    from football_pipeline.calibration_input import penalty_area_points

    field_to_image = np.array([[100, 0, -60], [150, 60, -80], [1, 0, -0.5]])
    points = penalty_area_points("left")
    for point in points:
        xy = field_to_image @ [point["u"], point["v"], 1]
        point["x"], point["y"] = (xy[:2] / xy[2]).tolist()
    calibration = create_calibration(video_metadata, points)
    for u, expected in ((0.1, "valid"), (0.8, "outside_field")):
        xy = field_to_image @ [u, 0.5, 1]
        x, y = xy[:2] / xy[2]
        player = detection([x - 5, y - 20, x + 5, y])
        project_detection(player, calibration)
        assert player.projection_status == expected
