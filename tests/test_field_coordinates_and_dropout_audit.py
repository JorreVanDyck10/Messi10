import pytest

from football_pipeline.contracts import FrameRecord, PipelineError
from football_pipeline.dropout_analysis import sequence_summary
from football_pipeline.field_coordinates import observation_from_peaks
from football_pipeline.field_layout import LINES_UV, POINTS_UV


@pytest.mark.parametrize("size", [(1920, 1080), (1280, 720), (1920, 720), (1000, 1000)])
def test_native_roundtrip_uses_separate_axes_without_letterbox_offset(size):
    point_id, line_id = next(iter(POINTS_UV)), next(iter(LINES_UV))
    points = {point_id: {"x": 240.0, "y": 135.0, "p": 0.7}, 999: {"x": 0, "y": 0, "p": 1}}
    lines = {line_id: {"x_1": 0.0, "y_1": 270.0, "x_2": 959.0, "y_2": 539.0, "p_1": 0.9, "p_2": 0.8}}
    obs = observation_from_peaks(points, lines, size)
    assert len(obs["points"]) == 1
    p, line = obs["points"][0], obs["lines"][0]
    assert [p["x"], p["y"]] == pytest.approx([size[0] / 4, size[1] / 4])
    assert [p["x"] / size[0] * 960, p["y"] / size[1] * 540] == pytest.approx([240, 135])
    assert [line["xy"][1][0] / size[0] * 960, line["xy"][1][1] / size[1] * 540] == pytest.approx([959, 539])
    assert line["confidence"] == 0.8 and p["raw_score"] == 0.7


def test_dropout_duration_and_trailing_gap_do_not_depend_on_available_geometry():
    records = [
        FrameRecord(i, i / 25, (640, 360), calibration={"status": status})
        for i, status in enumerate(["missing", "valid", "missing", "missing"])
    ]
    result = sequence_summary(records, 25)
    assert result["dropout_count"] == 2
    assert result["dropout_duration_s"] == 0.12
    assert result["longest_dropout_s"] == 0.08
    assert result["dropouts"][-1]["recovered"] is False
    assert result["accuracy"]["correct_field_coverage"] is None
    records[-1].frame_index = 9
    with pytest.raises(PipelineError, match="consecutive"):
        sequence_summary(records, 25)
