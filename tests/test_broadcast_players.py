import json
from types import SimpleNamespace

import numpy as np
import pytest
from test_appearance import fixed_classifier

from football_pipeline.appearance import AppearanceClassifier
from football_pipeline.broadcast_data import labelled_people
from football_pipeline.broadcast_evaluation import reference_geometry
from football_pipeline.broadcast_training import team_metrics
from football_pipeline.contracts import Detection, FrameRecord, PipelineError
from football_pipeline.detection import UltralyticsDetector, load_model_manifest, merge_person_proposals
from football_pipeline.kit_embedding import KitEmbedding, PitchTeamSamples, dominant_teams, embedding_candidate
from football_pipeline.render import render_frame
from football_pipeline.teams import TeamAssigner, load_team_settings, validate_team_model


def player(index=0, kit=0, **kwargs):
    vector = np.zeros(32)
    vector[kit] = 1
    return Detection(str(index), "specialist", 0, "player", [100, 100, 130, 180], .9,
                     field_position=[.5, .5], projection_status="valid", team_embedding=vector.tolist(),
                     shirt_color_lab=[50., 50. if kit else -50., 0.], **kwargs)


def settings():
    return load_team_settings({"method": "torso_embedding_dominant_modes_v1", "confirmation_samples": 1})


def test_provider_attributes_follow_annotation_id_and_goalkeepers_remain_players():
    annotations = [{"id": str(i), "supercategory": "object", "category_id": category,
                    "bbox_image": {"x": 10, "y": 20, "w": 10, "h": 40},
                    "attributes": {"team": "left", "role": "irrelevant", "jersey": "3"},
                    "track_id": i, "bbox_pitch": {"x_bottom_middle": 0, "y_bottom_middle": 0}}
                   for i, category in enumerate((1, 2, 3, 7))]
    annotations.insert(0, {**annotations[0], "id": "missing-box", "bbox_image": None})
    people = labelled_people(annotations, 100, 100)
    assert [p["provider_annotation_id"] for p in people] == ["0", "1", "2", "3"]
    assert [p["role"] for p in people] == ["player", "player", "referee", "person"]
    assert people[1]["goalkeeper"] and people[1]["team"] == "left"
    assert people[-1]["team"] is None
    annotations[-1]["bbox_pitch"]["x_bottom_middle"] = 60
    assert not labelled_people(annotations, 100, 100)[-1]["on_pitch"]


def test_pitch_policy_protects_real_players_but_does_not_rename_generic_people(tmp_path):
    spec = {**fixed_classifier(tmp_path, "assistant_referee"), "role_policy": "preserve_detector_players"}
    classifier = AppearanceClassifier(spec)
    actual, generic = player(), player(1)
    generic.semantic_class = "person"
    classifier.classify(np.zeros((360, 640, 3), np.uint8), [actual, generic], "new-match")
    assert actual.semantic_class == "player" and actual.role_decision == "specialist_player_preserved"
    assert actual.role_class_id == 2 and actual.detector_semantic_class == "player"
    assert generic.semantic_class == "assistant_referee"
    actual.semantic_class = "referee"
    classifier.classify(np.zeros((360, 640, 3), np.uint8), [actual], "new-match")
    assert actual.semantic_class == "referee" and actual.team_id is None
    # Positive learned player evidence can rescue, for example, a keeper whose
    # uniform was confused with an official by the specialist detector.
    player_spec = {**fixed_classifier(tmp_path, "player"), "role_policy": "preserve_detector_players"}
    learned_player = AppearanceClassifier(player_spec)
    learned_player.classify(np.zeros((360, 640, 3), np.uint8), [actual], "new-match")
    assert actual.semantic_class == "player"
    assert actual.role_decision == "strong_player_evidence_refines_specialist_referee"


def test_classification_happens_only_for_people_projected_inside_the_current_field():
    received = []
    detector = object.__new__(UltralyticsDetector)
    detector.video_hash = "new-match"
    detector.appearance = SimpleNamespace(classify=lambda frame, detections, identity: received.extend(detections))
    detector.kit_embedding = None
    inside, outside, unavailable, generic = [player(i) for i in range(4)]
    outside.projection_status = "outside_field"
    unavailable.projection_status = "calibration_unavailable"
    generic.semantic_class = "person"
    detector.classify_on_pitch(np.zeros((360, 640, 3), np.uint8), [inside, outside, unavailable, generic])
    assert received == [inside, generic]


def test_embedding_groups_survive_short_tracks_and_exclude_people_outside_the_field():
    sample = PitchTeamSamples(settings(), 10)
    for frame in range(6):
        for i in range(6):
            # Every observation has a new ID: no three-frame track prerequisite.
            d = player(frame * 6 + i, i // 3, track_id=frame * 6 + i)
            sample.add(d, frame)
        outsider = player(1000 + frame, 2)
        outsider.projection_status = "outside_field"
        sample.add(outsider, frame)
        sample.add(player(2000 + frame, 3, player_kind="goalkeeper"), frame)
    model = sample.fit()
    assert model["status"] == "available"
    validate_team_model(model)
    assigner = TeamAssigner(model, 10)
    group = [player(0, 0), player(1, 1), player(2, 2, player_kind="goalkeeper")]
    assigner.update(group, 0)
    assert group[0].team_id and group[1].team_id and group[0].team_id != group[1].team_id
    assert group[2].team_id is None
    assert dominant_teams([np.eye(32)[0]] * 10) is None
    off = player(9)
    off.projection_status = "calibration_unavailable"
    assert embedding_candidate(off, model) == (None, None)


def test_bad_embedding_models_are_rejected():
    sample = PitchTeamSamples(settings(), 10)
    for frame in range(6):
        for i in range(4):
            sample.add(player(frame * 4 + i, i // 2), frame)
    model = sample.fit()
    model["teams"]["A"]["prototype_embedding"] = [float("nan")] * 32
    with pytest.raises(PipelineError, match="teamprototype"):
        validate_team_model(model)


def test_pitch_render_hides_external_people_without_mutating_saved_detections():
    pixels = np.zeros((360, 640, 3), np.uint8)
    outside = player()
    outside.projection_status = "outside_field"
    outside.field_position = None
    record = FrameRecord(0, 0, (640, 360), [outside], analysis_scope="on_pitch_players")
    empty = FrameRecord(0, 0, (640, 360), [], analysis_scope="on_pitch_players")
    assert np.array_equal(render_frame(pixels, record), render_frame(pixels, empty))
    assert len(record.detections) == 1
    assert FrameRecord.from_dict(record.to_dict()).analysis_scope == "on_pitch_players"


def test_profile_rejects_unknown_scope_and_role_policy(model_manifest):
    path, model = model_manifest
    model["analysis_scope"] = "guess_everybody_is_a_player"
    path.write_text(json.dumps(model))
    with pytest.raises(PipelineError, match="analysebereik"):
        load_model_manifest(path)


def test_team_metric_allows_one_swap_per_clip_not_a_different_swap_every_frame():
    rows, vectors = [], []
    for frame in range(4):
        for side in range(2):
            rows.append({"split": "val", "broadcast": True, "role": "player", "group": "match/clip",
                         "team": "left" if (side + frame) % 2 else "right", "goalkeeper": False})
            vectors.append(np.eye(32)[side])
    result = team_metrics(rows, np.array(vectors), np.zeros(8))
    assert result["coverage"] == 1
    assert result["accuracy_assigned"] == .5


def test_reference_geometry_requires_correspondences_and_is_not_an_automatic_field_claim():
    assert reference_geometry([], 640, 360)["status"] != "valid"
    annotations = [{"supercategory": "object", "bbox_image": {"x": x - 10, "y": y - 40, "w": 20, "h": 40},
                    "bbox_pitch": {"x_bottom_middle": x / 640 * 105 - 52.5,
                                   "y_bottom_middle": y / 360 * 68 - 34}}
                   for x, y in ((50, 80), (550, 80), (550, 300), (50, 300))]
    state = reference_geometry(annotations, 640, 360)
    assert state["status"] == "valid"
    assert np.allclose(np.array(state["homography"]) @ [320, 180, 1], [.5, .5, 1])


def test_team_profile_is_selected_with_the_model_and_respects_explicit_override(monkeypatch, tmp_path):
    from football_pipeline.teams import configured_team_path

    monkeypatch.delenv("FOOTBALL_TEAMS", raising=False)
    assert configured_team_path({}).name == "teams.json"
    assert configured_team_path({"kit_embedding": {"weights": "trained.pt"}}).name == "teams-broadcast.json"
    monkeypatch.setenv("FOOTBALL_TEAMS", str(tmp_path / "custom.json"))
    assert configured_team_path({"kit_embedding": {"weights": "trained.pt"}}) == tmp_path / "custom.json"


def test_two_overlapping_players_survive_while_duplicate_proposals_still_merge():
    left, right = player(0), player(1)
    right.bbox_xyxy = [108, 100, 138, 180]
    assert len(merge_person_proposals([left, right])) == 1
    assert len(merge_person_proposals([left, right], preserve_same_source=True)) == 2
    duplicate = player(2)
    duplicate.model_id = "generic-proposals"
    duplicate.semantic_class = "person"
    assert len(merge_person_proposals([left, right, duplicate], preserve_same_source=True)) == 2


def test_unreadable_edge_crop_stays_unknown_instead_of_crashing_team_inference():
    model = object.__new__(KitEmbedding)
    tiny = Detection("edge", "specialist", 0, "player", [639.2, 100, 639.9, 180], .9,
                     field_position=[.9, .5], projection_status="valid")
    model.update(np.zeros((360, 640, 3), np.uint8), [tiny])
    assert tiny.team_embedding is None and tiny.team_id is None
