"""Analytic paths and interrupted observations exercise the distance contract."""

from dataclasses import replace

import pytest

from football_pipeline.contracts import Detection, FrameRecord, PipelineError
from football_pipeline.distances import DistanceSettings, estimate_distances, recorded_dimensions


def frame(i, x=0.1, y=0.3, *, track=1, team="A", valid=True, reset=False):
    detection = Detection(
        str(i),
        "test",
        0,
        "player",
        [10, 10, 20, 40],
        0.9,
        track_id=track,
        field_position=[x, y] if valid else None,
        projection_status="valid" if valid else "calibration_unavailable",
        team_id=team,
    )
    return FrameRecord(i, i / 10, (100, 100), [detection], tracking={"reset_tracks": reset})


def test_known_horizontal_vertical_and_diagonal_paths_and_field_scaling():
    records = [frame(i, 0.1 + i * 0.001, 0.3 + i * 0.002) for i in range(11)]
    rows, events = estimate_distances(records, 1.1)
    assert rows[0]["distance_m"] == pytest.approx((1.05**2 + 1.36**2) ** 0.5)
    assert rows[0]["measured_s"] == pytest.approx(1)
    assert rows[0]["coverage"] == pytest.approx(1 / 1.1)
    assert len(events) == 5
    larger, _ = estimate_distances(records, 1.1, DistanceSettings(120, 80))
    assert larger[0]["distance_m"] == pytest.approx((1.2**2 + 1.6**2) ** 0.5)


def test_stationary_is_zero_but_single_or_invalid_observations_are_unavailable():
    rows, _ = estimate_distances([frame(i) for i in range(11)], 1.1)
    assert rows[0]["distance_m"] == 0 and rows[0]["measured_s"] > 0
    for records in ([frame(0)], [frame(i, valid=False) for i in range(11)]):
        rows, events = estimate_distances(records, 1.1)
        assert rows[0]["distance_m"] is None
        assert rows[0]["coverage"] == 0 and not events


@pytest.mark.parametrize("gap", ["missing", "invalid", "calibration", "duplicate", "frame"])
def test_missing_or_invalid_samples_never_bridge(gap):
    records = [frame(i, 0.1 + i * 0.001) for i in range(11)]
    if gap == "missing":
        records[5].detections = []
    elif gap == "invalid":
        records[5].detections[0].field_position = [float("nan"), 0.3]
    elif gap == "calibration":
        records[5].calibration = {"status": "unavailable"}
    elif gap == "duplicate":
        records[5].detections *= 2
    else:
        records.pop(5)
    rows, events = estimate_distances(records, 1.1)
    assert rows[0]["distance_m"] == pytest.approx(0.84)
    assert rows[0]["measured_s"] == pytest.approx(0.8)
    assert not any(e["start_s"] < 0.5 < e["timestamp_s"] for e in events)
    assert len({e["segment"] for e in events}) == 2


def test_reset_separates_reused_id_and_different_ids_never_merge():
    records = [frame(i, 0.1 + i * 0.001, reset=i == 5) for i in range(11)]
    rows, events = estimate_distances(records, 1.1)
    assert len(rows) == 2 and {r["shot"] for r in rows} == {1, 2}
    assert sum(r["distance_m"] for r in rows) == pytest.approx(0.945)
    assert not any(e["start_s"] < 0.5 <= e["timestamp_s"] for e in events)
    records = [frame(i, track=1 if i < 5 else 2) for i in range(11)]
    rows, _ = estimate_distances(records, 1.1)
    assert len(rows) == 2 and {r["track_id"] for r in rows} == {1, 2}


def test_large_jump_rejected_before_smoothing_and_speed_limit_is_configurable():
    records = [frame(i, 0.1 if i < 5 else 0.9) for i in range(11)]
    rows, events = estimate_distances(records, 1.1)
    assert rows[0]["distance_m"] == 0
    assert rows[0]["measured_s"] == pytest.approx(0.9)
    assert len({e["segment"] for e in events}) == 2
    records = [frame(i, 0.1 + i * 0.01) for i in range(11)]
    rows, _ = estimate_distances(records, 1.1, DistanceSettings(max_speed_m_s=5))
    assert rows[0]["distance_m"] is None


def test_roles_teams_and_unknown_intervals():
    records = [frame(i, 0.1 + i * 0.001, team="A" if i < 5 else "B") for i in range(11)]
    rows, events = estimate_distances(records, 1.1)
    assert rows[0]["team"] == "unknown"
    assert {e["team"] for e in events} == {"A", "B", "unknown"}
    for record in records:
        record.detections = [replace(record.detections[0], semantic_class="referee")]
    assert estimate_distances(records, 1.1) == ([], [])


def test_recorded_dimensions_and_invalid_settings():
    assert recorded_dimensions({})[:2] == (105, 68)
    assert recorded_dimensions({"review": {"field_dimensions_m": {"length": 110, "width": 70}}})[:2] == (
        110,
        70,
    )
    assert recorded_dimensions({"review": {"field_dimensions_m": {"length": -1, "width": 70}}})[:2] == (
        105,
        68,
    )
    with pytest.raises(PipelineError):
        DistanceSettings(length_m=float("nan"))
    with pytest.raises(PipelineError):
        estimate_distances([], 0)
