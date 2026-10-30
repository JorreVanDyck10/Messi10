from copy import deepcopy

import pytest

from football_pipeline.contracts import PipelineError
from football_pipeline.point_picker import apply_point_click, picker_view


def test_click_updates_only_selected_point_in_original_pixels():
    points = [{"name": "a", "x": None, "y": None}, {"name": "b", "x": 20, "y": 30}]
    original = deepcopy(points)
    updated = apply_point_click(
        points,
        {"x": 1920.25, "y": 480.5, "index": 0, "context": "current"},
        context="current",
        selected=0,
        width=3840,
        height=960,
    )
    assert updated[0]["x"] == 1920.25
    assert updated[0]["y"] == 480.5
    assert updated[1] == original[1]
    assert points == original


def test_zoom_and_scroll_state_do_not_change_original_image_coordinates():
    event = {
        "x": 900,
        "y": 400,
        "index": 0,
        "context": "current",
        "zoom": 2.5,
        "scroll_x": 500,
        "scroll_y": 120,
    }
    updated = apply_point_click(
        [{"x": None, "y": None}], event, context="current", selected=0, width=1920, height=1080
    )
    assert updated == [{"x": 900, "y": 400}]
    assert picker_view(event) == {"zoom": 2.5, "scroll_x": 500, "scroll_y": 120}
    assert picker_view({**event, "zoom": float("nan")}) is None
    assert picker_view({**event, "scroll_x": -1}) is None
    assert picker_view({}) is None
    # A low-resolution video may be enlarged on a much wider screen.
    assert picker_view({**event, "zoom": 4, "scroll_x": 5000})["scroll_x"] == 5000


@pytest.mark.parametrize(
    "changes",
    [
        {"context": "previous-frame"},
        {"index": 1},
        {"index": True},
        {"x": None},
        {"x": float("nan")},
        {"x": float("inf")},
        {"x": True},
        {"x": -1},
        {"x": 3840},
        {"y": 960},
    ],
)
def test_invalid_or_stale_click_cannot_change_points(changes):
    event = {"x": 500, "y": 300, "index": 0, "context": "current"} | changes
    points = [{"x": None, "y": None}]
    with pytest.raises(PipelineError):
        apply_point_click(points, event, context="current", selected=0, width=3840, height=960)
    assert points == [{"x": None, "y": None}]


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), "", True])
def test_missing_coordinates_name_the_point_instead_of_numpy_error(demo_fixture, value):
    from football_pipeline.geometry import create_calibration
    from football_pipeline.video import inspect_video

    points = deepcopy(demo_fixture["calibration"].points)
    points[0]["x"] = value
    with pytest.raises(PipelineError, match=points[0]["name"]):
        create_calibration(inspect_video(demo_fixture["video"]), points, 0)
