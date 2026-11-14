from dataclasses import asdict

from football_pipeline.contracts import Detection
from football_pipeline.teams import load_team_settings
from scripts.evaluate_temporal_broadcast import score


def sample():
    people, detections = [], []
    for i, (confidence, track) in enumerate(((0.15, 10), (0.15, None), (0.3, None))):
        box = [10 + 20 * i, 10, 20 + 20 * i, 30]
        people.append({"role": "player", "on_pitch": True, "bbox": box, "track_id": i + 1, "team": "left"})
        detections.append(
            asdict(
                Detection(
                    str(i),
                    "test",
                    0,
                    "player",
                    box,
                    confidence,
                    track_id=track,
                    projection_status="valid",
                    field_position=[0.5, 0.5],
                )
            )
        )
    rows = [
        {
            "fps": 25,
            "frame_index": 0,
            "frame_id": "frame",
            "width": 100,
            "height": 100,
            "people": people,
            "clip": "fixture",
            "game_id": "fixture",
            "split": "val",
        }
    ]
    cached = {
        "frames": [{"frame_index": 0, "geometry_status": "valid", "reset": False, "detections": detections}]
    }
    return rows, cached


def test_runtime_scoring_counts_matched_low_confidence_but_not_unmatched_low_confidence():
    rows, cached = sample()
    runtime = score(rows, cached, load_team_settings({}), count_policy="runtime")
    benchmark = score(rows, cached, load_team_settings({}))
    assert runtime["players"]["per_class"][0]["TP"] == 2
    assert runtime["players"]["per_class"][0]["FN"] == 1
    assert benchmark["players"]["per_class"][0]["TP"] == 1
    assert benchmark["players"]["per_class"][0]["FN"] == 2
    assert runtime["counts"]["mean_absolute_error_when_available"] == 1
    assert runtime["counts"]["available_frames"] == 1


def test_runtime_scoring_requires_a_current_valid_calibration_even_with_stale_positions():
    rows, cached = sample()
    cached["frames"][0]["geometry_status"] = "insufficient_points"
    runtime = score(rows, cached, load_team_settings({}), count_policy="runtime")
    assert runtime["players"]["per_class"][0]["TP"] == 0
    assert runtime["players"]["per_class"][0]["FN"] == 3
    assert runtime["counts"]["mean_absolute_error_when_available"] is None
    assert runtime["counts"]["per_frame"][0]["predicted_players"] is None
