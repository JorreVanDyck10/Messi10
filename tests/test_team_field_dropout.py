"""Team appearance must survive missing geometry without fabricating field evidence."""

import json
from dataclasses import asdict
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from football_pipeline.contracts import Detection, FrameRecord
from football_pipeline.detection import UltralyticsDetector
from football_pipeline.kit_embedding import KitEmbedding, PitchTeamSamples
from football_pipeline.participants import player_summary
from football_pipeline.teams import TeamAssigner, load_team_settings, shirt_color


def scene(status="calibration_unavailable"):
    frame = np.full((200, 400, 3), (25, 95, 30), dtype=np.uint8)
    detections = []
    for i in range(6):
        x = 15 + i * 60
        color = (235, 235, 235) if i < 3 else (150, 35, 20)
        cv2.rectangle(frame, (x, 30), (x + 30, 150), color, -1)
        detections.append(
            Detection(
                str(i),
                "trained-player-detector",
                0,
                "player",
                [x, 30, x + 30, 150],
                0.9,
                projection_status=status,
                field_position=[0.5, 0.5] if status == "valid" else None,
                detector_semantic_class="player",
            )
        )
    return frame, detections


def kit():
    # Exercise the actual released histogram inference path without loading weights.
    model = object.__new__(KitEmbedding)
    model.metric_weights = np.ones(32, dtype=np.float32)
    return model


def settings():
    return load_team_settings({"method": "torso_embedding_dominant_modes_v1", "confirmation_samples": 1})


def test_team_embedding_is_still_computed_for_observed_players_during_field_dropout():
    frame, players = scene()
    kit().update(frame, players)
    assert all(d.team_embedding is not None for d in players)
    assert all(d.field_position is None for d in players)


def test_pitch_classifier_keeps_role_context_strict_but_passes_missing_field_players_to_kit():
    frame, players = scene()
    generic = Detection(
        "generic",
        "person-detector",
        0,
        "person",
        [0, 0, 20, 40],
        0.9,
        projection_status="calibration_unavailable",
    )
    received = []
    detector = object.__new__(UltralyticsDetector)
    detector.video_hash = "new-video"
    detector.appearance = SimpleNamespace(classify=lambda f, ds, v: received.extend(ds))
    detector.role_context = SimpleNamespace(update=lambda ds, size: received.extend(ds))
    detector.kit_embedding = kit()
    detector.classify_on_pitch(frame, [*players, generic])
    assert received == []  # Missing geometry must not enable pitch-specific role inference.
    assert all(d.team_embedding is not None for d in players)
    assert generic.team_embedding is None and generic.semantic_class == "person"


def test_team_fit_and_labels_survive_a_clip_without_any_valid_field_frame():
    samples = PitchTeamSamples(settings(), 25)
    for index in range(0, 30, 5):
        frame, players = scene()
        kit().update(frame, players)
        for d in players:
            d.detection_id = f"{index}:{d.detection_id}"
            d.shirt_color_lab = shirt_color(frame, d, settings())
            samples.add(d, index)
    model = samples.fit()
    assert model["status"] == "available"
    frame, players = scene()
    kit().update(frame, players)
    TeamAssigner(model, 25).update(players, 0)
    assert len({d.team_id for d in players[:3]}) == 1
    assert len({d.team_id for d in players[3:]}) == 1
    assert {d.team_id for d in players} == {"A", "B"}
    record = FrameRecord(0, 0, (400, 200), players, {"status": "insufficient_points"})
    summary = player_summary(record)
    assert summary["on_field"] is None
    assert all(value is None for value in summary["by_team"].values())
    assert all(d.field_position is None and d.projection_status == "calibration_unavailable" for d in players)


@pytest.mark.parametrize("status", ["outside_field", "invalid_box", "truncated_bottom", "not_projected"])
def test_known_exclusions_do_not_gain_a_team_embedding(status):
    frame, players = scene(status)
    kit().update(frame, players)
    assert all(d.team_embedding is None for d in players)


def test_missing_geometry_does_not_promote_a_generic_person_into_a_player():
    samples = PitchTeamSamples({**settings(), "kit_player_recovery": True}, 25)
    for index in range(0, 30, 5):
        frame, players = scene("valid")
        kit().update(frame, players)
        for d in players:
            samples.add(d, index)
    target = scene()[1][0]
    target.semantic_class = target.detector_semantic_class = "person"
    target.role_model_id = "trained-role-classifier"
    target.team_embedding = players[0].team_embedding
    TeamAssigner(samples.fit(), 25).update([target], 0)
    assert target.semantic_class == "person" and target.team_id is None


def test_saved_frames_export_team_colored_video_without_inventing_field_counts(tmp_path):
    """Exercise phase-two team fitting, JSONL reload and H.264 export on synthetic input."""
    from football_pipeline.team_results import finish_teams
    from football_pipeline.video import VideoWriter, inspect_video

    source_video = tmp_path / "source.mp4"
    writer = VideoWriter(source_video, 400, 200, 25, 1)
    directory = tmp_path / "run"
    directory.mkdir()
    with (directory / "framegegevens.jsonl").open("w", encoding="utf-8") as stream:
        for index in range(30):
            frame, players = scene()
            writer.write(frame)
            kit().update(frame, players)
            for d in players:
                d.detection_id = f"{index}:{d.detection_id}"
                d.shirt_color_lab = shirt_color(frame, d, settings())
            record = FrameRecord(
                index,
                index / 25,
                (400, 200),
                players,
                {"status": "insufficient_points", "homography": None},
                analysis_scope="on_pitch_players",
            )
            stream.write(json.dumps(record.to_dict()) + "\n")
    writer.close()
    manifest = {
        "video": asdict(inspect_video(source_video)),
        "team_settings": settings(),
        "cache_key": "synthetic-test",
    }
    result = finish_teams(directory, manifest)
    assert result["observations"] == {"assigned": 180, "unknown": 0}
    output = inspect_video(directory / "samengestelde_video.mp4")
    assert output.frame_count == 30 and output.size == (1920, 720)
    records = [json.loads(line) for line in (directory / "framegegevens.jsonl").read_text().splitlines()]
    assert all(r["player_summary"]["on_field"] is None for r in records)
    assert all({d["team_id"] for d in r["detections"]} == {"A", "B"} for r in records)
