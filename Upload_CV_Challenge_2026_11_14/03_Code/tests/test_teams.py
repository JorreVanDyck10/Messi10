import copy
import json

import cv2
import numpy as np
import pytest

from football_pipeline.contracts import Detection, FrameRecord, PipelineError
from football_pipeline.participants import player_summary
from football_pipeline.teams import (
    DEFAULT_TEAM_SETTINGS,
    TeamAssigner,
    TeamSamples,
    load_team_settings,
    rgb_to_lab,
    shirt_color,
)


def player(identity=1, rgb=(220, 30, 30), **kwargs):
    return Detection(
        str(identity),
        "fixture",
        0,
        "player",
        [40, 30, 70, 120],
        0.9,
        track_id=identity,
        field_position=[0.5, 0.5],
        projection_status="valid",
        shirt_color_lab=rgb_to_lab(rgb) if rgb is not None else None,
        **kwargs,
    )


@pytest.fixture
def team_model():
    samples = TeamSamples(DEFAULT_TEAM_SETTINGS, 10)
    for index in range(12):
        for identity in range(1, 7):
            d = player(identity, (220, 30, 30) if identity < 4 else (30, 40, 220))
            d.detection_id = f"{index}:{identity}"
            samples.add(d, index)
    return samples.fit()


def test_profile_is_versioned_and_rejects_invalid_settings():
    from football_pipeline.video import ROOT

    assert load_team_settings(ROOT / "configs/teams.json") == DEFAULT_TEAM_SETTINGS
    for edit in (
        {"method": "new"},
        {"sample_hz": float("nan")},
        {"max_samples": 99999},
        {"confirmation_samples": True},
        {"min_foreground_fraction": 1.1},
        {"unexpected": 1},
    ):
        with pytest.raises(PipelineError):
            load_team_settings(edit)


@pytest.mark.parametrize("rgb", [(220, 30, 30), (25, 210, 90), (240, 240, 240), (15, 15, 15)])
def test_torso_color_preserves_green_white_and_black_shirts(rgb):
    frame = np.full((180, 180, 3), (30, 95, 25), np.uint8)
    cv2.rectangle(frame, (40, 30), (70, 120), tuple(reversed(rgb)), -1)
    color = shirt_color(frame, player(), DEFAULT_TEAM_SETTINGS)
    assert color is not None
    assert np.linalg.norm(np.array(color) - rgb_to_lab(rgb)) < 1


def test_background_tiny_and_mixed_crops_are_unknown_and_roles_stay_intact():
    frame = np.full((180, 180, 3), (30, 95, 25), np.uint8)
    d = player()
    assert shirt_color(frame, d, DEFAULT_TEAM_SETTINGS) is None
    d.bbox_xyxy = [40, 30, 45, 40]
    assert shirt_color(frame, d, DEFAULT_TEAM_SETTINGS) is None
    d = player()
    d.semantic_class = "referee"
    assert shirt_color(frame, d, DEFAULT_TEAM_SETTINGS) is None
    assert d.semantic_class == "referee"
    d.semantic_class = "player"
    frame[48:75, 47:62] = np.random.default_rng(4).integers(0, 256, (27, 15, 3), np.uint8)
    assert shirt_color(frame, d, DEFAULT_TEAM_SETTINGS) is None


def test_fit_has_two_stable_prototypes_and_rejects_sparse_third_color(team_model):
    assert team_model["status"] == "available"
    samples = TeamSamples(DEFAULT_TEAM_SETTINGS, 10)
    for index in range(12):
        for identity in range(1, 8):
            rgb = (220, 30, 30) if identity < 4 else (30, 40, 220) if identity < 7 else (20, 230, 30)
            d = player(identity, rgb)
            d.detection_id = f"{index}:{identity}"
            samples.add(d, index)
    assert samples.fit() == samples.fit()
    prototypes = samples.fit()["teams"]
    assert {tuple(np.rint(t["prototype_lab"])) for t in prototypes.values()} == {
        tuple(np.rint(t["prototype_lab"])) for t in team_model["teams"].values()
    }
    assigner = TeamAssigner(team_model, 10)
    for index in range(3):
        goalie = player(7, (20, 230, 30))
        assigner.update([goalie], index)
        assert goalie.team_id is None


def test_similar_colors_and_insufficient_observations_stay_unknown():
    samples = TeamSamples(DEFAULT_TEAM_SETTINGS, 10)
    assert samples.fit()["status"] == "insufficient_samples"
    for index in range(8):
        for identity in range(1, 7):
            d = player(identity, (220, 30, 30) if identity < 4 else (218, 32, 32))
            d.detection_id = f"{index}:{identity}"
            samples.add(d, index)
    assert samples.fit()["status"] != "available"


def test_single_frame_cannot_establish_team_prototypes():
    samples = TeamSamples(DEFAULT_TEAM_SETTINGS, 5)
    for identity in range(1, 9):
        d = player(identity, (220, 30, 30) if identity < 5 else (30, 40, 220))
        d.track_id = None
        samples.add(d, 0)
    assert samples.fit()["status"] == "insufficient_frames"


def test_labels_need_confirmation_resist_single_error_and_reset_for_new_id(team_model):
    assigner = TeamAssigner(team_model, 10)
    confirmed = None
    for index in range(3):
        d = player()
        assigner.update([d], index)
        if index < 2:
            assert d.team_id is None
        else:
            confirmed = d.team_id
            assert confirmed in {"A", "B"}
    d = player(rgb=(30, 40, 220))
    assigner.update([d], 3)
    assert d.team_id == confirmed and d.team_source == "track_history"
    d = player(rgb=None)
    assigner.update([d], 4)
    assert d.team_id == confirmed
    new_id = player(11)
    assigner.update([new_id], 5)
    assert new_id.team_id is None
    d = player()
    assigner.update([d], 30)
    assert d.team_id is None
    assert team_model["status"] == "available"


def test_persistent_new_color_switches_only_after_threshold(team_model):
    assigner = TeamAssigner(team_model, 10)
    for index in range(3):
        d = player()
        assigner.update([d], index)
    original = d.team_id
    for index in range(3, 8):
        d = player(rgb=(30, 40, 220))
        assigner.update([d], index)
        assert (d.team_id == original) == (index < 7)


def test_manual_overrides_apply_whole_track_and_do_not_touch_nonplayers(team_model):
    assigner = TeamAssigner(team_model, 10, {"1": "A", "2": None, "3": "B"})
    d, unknown, official = player(), player(2), player(3)
    official.semantic_class = "referee"
    assigner.update([d, unknown, official], 0)
    assert d.team_id == "A" and d.team_source == "manual"
    assert unknown.team_id is None and unknown.team_source == "manual"
    assert official.team_id is None and official.team_status == "not_player"


def test_team_totals_keep_existing_field_confidence_and_role_rules():
    a, b, unknown, outside, official = [player(i) for i in range(1, 6)]
    a.team_id, b.team_id = "A", "B"
    outside.projection_status, outside.field_position = "outside_field", None
    official.semantic_class = "referee"
    record = FrameRecord(0, 0, (180, 180), [a, b, unknown, outside, official], {"status": "valid"})
    summary = player_summary(record)
    assert summary["on_field"] == 3 and summary["by_team"] == {"A": 1, "B": 1, "unknown": 1}
    b.confidence, b.track_id = 0.15, None
    assert player_summary(record)["on_field"] == 2
    b.track_id = 2
    assert player_summary(record)["on_field"] == 3
    for status in ("insufficient_points", "valid"):
        record.calibration = {"status": status}
        summary = player_summary(record)
        assert summary["by_team"] == (
            {"A": 1, "B": 1, "unknown": 1} if status == "valid" else dict.fromkeys(("A", "B", "unknown"))
        )
    record.player_model_available = False
    assert all(value is None for value in player_summary(record)["by_team"].values())
    empty = FrameRecord(0, 0, (180, 180))
    assert player_summary(empty)["by_team"] == {"A": 0, "B": 0, "unknown": 0}


def test_old_and_new_records_roundtrip_without_trusting_exported_counts():
    d = player()
    raw = FrameRecord(0, 0, (180, 180), [d]).to_dict()
    raw["player_summary"]["on_field"] = 99
    assert FrameRecord.from_dict(raw).to_dict()["player_summary"]["on_field"] == 1
    old = copy.deepcopy(raw)
    for key in ("shirt_color_lab", "team_id", "team_status", "team_match_score", "team_source"):
        del old["detections"][0][key]
    assert FrameRecord.from_dict(old).detections[0].team_id is None
    assert json.loads(json.dumps(raw))["detections"][0]["team_status"] == "unknown"


def test_reservoir_is_bounded_and_order_independent():
    settings = {**DEFAULT_TEAM_SETTINGS, "max_samples": 10, "min_track_samples": 1}
    samples, reverse = TeamSamples(settings, 5), TeamSamples(settings, 5)
    for i in range(50):
        samples.add(player(i, (220, 30, 30) if i % 2 else (30, 40, 220)), i)
    for i in reversed(range(50)):
        reverse.add(player(i, (220, 30, 30) if i % 2 else (30, 40, 220)), i)
    assert len(samples.samples) == 10
    assert samples.fit() == reverse.fit()


def test_correction_validation_binds_source_and_rejects_unknown_ids(team_model):
    from football_pipeline.team_results import validate_corrections

    origin = {"cache_key": "root", "video": {"sha256": "clip"}}
    request = {
        "schema_version": 1,
        "source_run_key": "root",
        "video_sha256": "clip",
        "teams": {"A": {"name": "Rood", "display_color": "#123456"}},
        "track_overrides": {"1": "B"},
    }
    model, overrides = validate_corrections(request, origin, team_model, {"1"})
    assert model["teams"]["A"]["name"] == "Rood" and overrides == {"1": "B"}
    assert team_model["teams"]["A"]["name"] == "Team A"
    for edit in (
        {"source_run_key": "other"},
        {"video_sha256": "other"},
        {"track_overrides": {"2": "A"}},
        {"teams": {"A": {"display_color": "red"}}},
        {"teams": {"A": {"name": ""}}},
    ):
        with pytest.raises(PipelineError):
            validate_corrections({**request, **edit}, origin, team_model, {"1"})


def test_equal_manual_prototypes_remain_ambiguous(team_model):
    from football_pipeline.team_results import validate_corrections

    origin = {"cache_key": "root", "video": {"sha256": "clip"}}
    model, _ = validate_corrections(
        {
            "schema_version": 1,
            "source_run_key": "root",
            "video_sha256": "clip",
            "teams": {k: {"shirt_color": "#ff0000"} for k in ("A", "B")},
        },
        origin,
        team_model,
        set(),
    )
    assert model["status"] == "ambiguous_colors"


def test_team_rendering_colors_boxes_points_and_legend(team_model):
    from football_pipeline.render import detection_color, render_frame
    from football_pipeline.teams import team_context

    d = player()
    d.team_id = "A"
    record = FrameRecord(0, 0, (180, 180), [d], team_context=team_context(team_model))
    image = render_frame(np.zeros((180, 180, 3), np.uint8), record)
    color = detection_color(d, record)
    assert tuple(image[350, 1600]) == color
    assert tuple(image[120, 440]) == color
    assert image.shape == (720, 1920, 3)
