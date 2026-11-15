from dataclasses import replace

import numpy as np
import pytest

from football_pipeline.contracts import Detection, FrameRecord
from football_pipeline.participants import displayed_as_player, frame_diagnostics, player_summary
from football_pipeline.render import render_frame


def missing_record():
    return FrameRecord(
        0,
        0.0,
        (640, 360),
        [
            Detection(
                "0",
                "player-model",
                0,
                "player",
                [100, 100, 130, 180],
                0.9,
                projection_status="calibration_unavailable",
            )
        ],
        {"status": "inconsistent_points", "homography": None},
        analysis_scope="on_pitch_players",
    )


def test_box_survives_field_loss_without_creating_count_or_map_position():
    record = missing_record()
    assert displayed_as_player(record, record.detections[0])
    assert player_summary(record)["on_field"] is None
    empty = replace(record, detections=[])
    pixels = np.zeros((360, 640, 3), np.uint8)
    actual, expected = render_frame(pixels, record), render_frame(pixels, empty)
    assert not np.array_equal(actual[:, :1280], expected[:, :1280])
    assert np.array_equal(actual[:, 1280:], expected[:, 1280:])
    # Even a stale saved position must not appear on an unavailable minimap.
    record.detections[0].field_position = [0.5, 0.5]
    assert np.array_equal(render_frame(pixels, record)[:, 1280:], expected[:, 1280:])


@pytest.mark.parametrize(
    "role,status,confidence",
    [
        ("person", "calibration_unavailable", 0.9),
        ("referee", "calibration_unavailable", 0.9),
        ("player", "outside_field", 0.9),
        ("player", "calibration_unavailable", 0.15),
    ],
)
def test_field_dropout_does_not_promote_people_or_show_unreliable_boxes(role, status, confidence):
    record = missing_record()
    d = record.detections[0]
    d.semantic_class, d.projection_status, d.confidence = role, status, confidence
    assert not displayed_as_player(record, d)


def test_diagnostics_and_legacy_frames_roundtrip_without_trusting_derived_data():
    record = missing_record()
    d = record.detections[0]
    d.confidence, d.track_id = 0.15, 7
    metrics = frame_diagnostics(record)
    assert metrics["displayed_players"] == metrics["image_tracked_players"] == 1
    assert metrics["counted_players"] is None
    value = record.to_dict()
    value["diagnostics"]["counted_players"] = 22
    assert FrameRecord.from_dict(value).to_dict()["diagnostics"] == metrics
    value.pop("diagnostics")
    assert FrameRecord.from_dict(value).to_dict()["diagnostics"] == metrics
