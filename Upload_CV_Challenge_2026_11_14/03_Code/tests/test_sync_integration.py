"""Compatibility between the incoming appearance model and colour-team corrections."""

import io
import json

from football_pipeline.contracts import Detection, FrameRecord
from football_pipeline.participants import player_summary
from football_pipeline.replay import replay_detections
from football_pipeline.teams import DEFAULT_TEAM_SETTINGS, TeamAssigner, TeamSamples


def appearance_player():
    return Detection(
        "0:0",
        "detector",
        0,
        "player",
        [80, 60, 100, 120],
        0.9,
        track_id=1,
        field_position=[0.2, 0.5],
        projection_status="valid",
        role_model_id="appearance",
        role_class_id=0,
        role_confidence=0.9,
        team_id="team_b",
        team_confidence=0.95,
        team_method="supervised_match",
        team_class_id=1,
    )


def test_both_team_id_formats_use_identical_totals():
    for identifier in ("A", "team_a"):
        detection = appearance_player()
        detection.team_id = identifier
        summary = player_summary(FrameRecord(0, 0, (640, 360), [detection]))
        assert summary["by_team"] == {"A": 1, "B": 0, "unknown": 0}
        assert summary["teams"] == {"team_a": 1, "team_b": 0, "unknown": 0}


def test_colour_assignment_keeps_appearance_evidence_and_replay_restores_it(video_metadata):
    detection = appearance_player()
    model = TeamSamples(DEFAULT_TEAM_SETTINGS, 25).fit()
    assigner = TeamAssigner(model, 25, {"1": "A"})
    assigner.update([detection], 0)
    assert detection.team_id == "A" and detection.team_source == "manual"
    assert detection.team_confidence is detection.team_method is detection.team_class_id is None
    assert detection.appearance_team == {
        "team_id": "team_b",
        "team_confidence": 0.95,
        "team_method": "supervised_match",
        "team_class_id": 1,
    }
    record = FrameRecord(0, 0, (640, 360), [detection])
    restored = replay_detections(io.StringIO(json.dumps(record.to_dict()) + "\n"), 0, video_metadata)[0]
    assert restored.team_id == "team_b" and restored.team_method == "supervised_match"
    assert restored.team_class_id == 1 and restored.team_confidence == 0.95
    assert restored.role_model_id == "appearance" and restored.semantic_class == "player"
    assert restored.track_id is restored.field_position is restored.team_source is None


def test_replay_discards_colour_labels_without_appearance_evidence(video_metadata):
    detection = appearance_player()
    detection.team_id, detection.team_source = "B", "automatic"
    detection.team_method = detection.team_class_id = detection.team_confidence = None
    detection.shirt_color_lab = [50, 0, 0]
    record = FrameRecord(0, 0, (640, 360), [detection])
    restored = replay_detections(io.StringIO(json.dumps(record.to_dict()) + "\n"), 0, video_metadata)[0]
    assert restored.team_id is restored.team_source is restored.shirt_color_lab is None
    assert restored.role_model_id == "appearance"
