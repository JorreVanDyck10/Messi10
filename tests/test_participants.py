from dataclasses import replace

import pytest

from football_pipeline.automatic_calibration import project_automatic
from football_pipeline.contracts import Detection, FrameRecord
from football_pipeline.geometry import project_detection
from football_pipeline.participants import player_exclusion_reason, player_summary


def candidate(role="player", confidence=0.9, box=None):
    return Detection("0:0", "fixture", 0, role, box or [100, 100, 120, 180], confidence)


def test_only_players_on_pitch_count_but_other_roles_and_off_pitch_predictions_are_preserved(calibration):
    roles = ["player", "referee", "assistant_referee", "steward", "spectator", "staff", "person"]
    detections = [candidate(role) for role in roles]
    detections += [candidate(box=[5, 100, 15, 150]), candidate(confidence=0.15)]
    for detection in detections:
        project_detection(detection, calibration)
    frame = FrameRecord(0, 0, (640, 360), detections)
    result = frame.to_dict()
    assert result["player_summary"]["on_field"] == 1
    assert result["player_summary"]["outside_field"] == 1
    assert result["player_summary"]["other_roles"] == dict.fromkeys(roles[1:], 1)
    assert len(result["detections"]) == 9
    assert [d["counted_as_player"] for d in result["detections"]] == [True] + [False] * 8
    assert result["detections"][3]["semantic_class"] == "steward"
    assert result["detections"][3]["player_exclusion_reason"] == "not_player"
    # A ByteTrack match may retain a low-confidence current observation, never a predicted-only position.
    detections[-1].track_id = 12
    assert player_summary(frame)["on_field"] == 2
    # Saved-frame review accepts the derived export fields, but recomputes their meaning.
    roundtrip = [Detection.from_dict(d) for d in result["detections"]]
    assert FrameRecord(0, 0, (640, 360), roundtrip).to_dict() == result


def test_field_loss_is_unknown_not_zero_and_recovery_uses_current_transform():
    detection = candidate()
    valid = {"status": "valid", "homography": [[1 / 560, 0, -40 / 560], [0, 1 / 280, -40 / 280], [0, 0, 1]]}
    missing = {"status": "insufficient_points", "homography": None}
    # Same image position goes outside when the recognized field shifts right.
    shifted = {
        "status": "valid",
        "homography": [[1 / 560, 0, -150 / 560], [0, 1 / 280, -40 / 280], [0, 0, 1]],
    }
    for state, expected in [(valid, 1), (missing, None), (shifted, 0), (valid, 1)]:
        project_automatic(detection, state, (640, 360))
        frame = FrameRecord(0, 0, (640, 360), [detection], state)
        assert frame.to_dict()["player_summary"]["on_field"] == expected
        assert frame.to_dict()["detections"][0]["counted_as_player"] == (expected == 1)
    assert player_summary(FrameRecord(0, 0, (640, 360), [], missing))["on_field"] is None
    assert player_summary(FrameRecord(0, 0, (640, 360), [], valid))["on_field"] == 0


@pytest.mark.parametrize("position", [None, [], [0.5], [float("nan"), 0.5], [1.1, 0.5]])
def test_claimed_valid_projection_without_valid_position_cannot_count(position):
    detection = replace(candidate(), projection_status="valid", field_position=position)
    assert player_exclusion_reason(detection, (640, 360)) is not None
    assert player_summary(FrameRecord(0, 0, (640, 360), [detection]))["on_field"] == 0


def test_truncated_feet_and_invalid_boxes_do_not_count(calibration):
    for box in [[100, 100, 130, 360], [100, 100, 90, 150]]:
        detection = candidate(box=box)
        project_detection(detection, calibration)
        assert not FrameRecord(0, 0, (640, 360), [detection]).to_dict()["detections"][0]["counted_as_player"]


def test_generic_person_profile_has_no_available_player_count(calibration):
    detection = candidate("person")
    project_detection(detection, calibration)
    record = FrameRecord(0, 0, (640, 360), [detection], player_model_available=False)
    assert record.to_dict()["player_summary"]["status"] == "player_model_unavailable"
    assert record.to_dict()["player_summary"]["on_field"] is None
    assert record.to_dict()["player_summary"]["other_roles"] == {"person": 1}
