import pytest

from football_pipeline.contracts import Detection
from football_pipeline.tracking import ByteTrackAdapter, Trajectories, load_tracker_config
from football_pipeline.video import ROOT


def item(index, confidence=0.9, semantic="player", x=100):
    return Detection(
        f"{index}:0",
        "test",
        0,
        semantic,
        [x, 80, x + 30, 160],
        confidence,
        field_position=[0.3, 0.5],
        projection_status="valid",
    )


def test_actual_bytetrack_indexes_low_confidence_and_empty_updates():
    config = load_tracker_config(ROOT / "configs/bytetrack.yaml")
    tracker = ByteTrackAdapter(config, 25)
    # Order is deliberately low-score then high-score: idx must refer to the unpartitioned input.
    first = [item(0, 0.15, x=300), item(0, 0.9, x=100), item(0, semantic="referee", x=450)]
    tracker.update(first, 0, (640, 360))
    assert first[0].track_id is None
    assert first[1].track_id == 1
    assert first[2].track_id is None
    second = [item(1, 0.15, x=102)]
    tracker.update(second, 1, (640, 360))
    assert second[0].track_id == 1
    tracker.update([], 2, (640, 360))
    assert tracker.tracker.frame_id == 3
    returning = [item(3, x=104)]
    tracker.update(returning, 3, (640, 360))
    assert returning[0].track_id == 1
    assert tracker.info["effective_buffer_updates"] == 30
    assert tracker.info["effective_buffer_seconds"] == pytest.approx(1.2)
    fresh = ByteTrackAdapter(config, 25)
    assert fresh.tracker.frame_id == 0
    new_item = [item(0)]
    fresh.update(new_item, 0, (640, 360))
    assert new_item[0].track_id == 1


def test_tracking_excludes_off_field_players_and_all_other_roles_inside_field():
    tracker = ByteTrackAdapter(load_tracker_config(ROOT / "configs/bytetrack.yaml"), 25)
    off_field = item(0, x=10)
    off_field.field_position, off_field.projection_status = None, "outside_field"
    people = [
        item(0, semantic=role, x=200)
        for role in ("referee", "assistant_referee", "steward", "spectator", "staff", "person")
    ]
    players = [off_field, *people, item(0, x=100)]
    tracker.update(players, 0, (640, 360))
    assert [d.track_id for d in players] == [None] * 7 + [1]
    missing_field = item(1, x=102)
    missing_field.field_position, missing_field.projection_status = None, "calibration_unavailable"
    tracker.update([missing_field], 1, (640, 360))
    assert missing_field.track_id is None
    assert tracker.tracker.frame_id == 2
    returning = item(2, x=104)
    tracker.update([returning], 2, (640, 360))
    assert returning.track_id == 1


def test_observed_trajectories_keep_gaps_and_expire():
    history = Trajectories(2, seconds=5)
    for index in [0, 1, 3, 4]:
        d = item(index)
        d.track_id, d.field_position = 1, [0.2 + index / 100, 0.5]
        history.update([d], index)
    assert [(a[0], b[0]) for a, b in history.segments(1)] == [(0, 1), (3, 4)]
    history.update([], 15)
    assert not history.points
