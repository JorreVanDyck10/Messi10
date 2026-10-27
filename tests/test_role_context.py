import numpy as np
import pytest
import torch

from football_pipeline.contracts import Detection, PipelineError
from football_pipeline.role_context import RoleContext, context_features, context_head


def model(tmp_path, nonplayer):
    head = context_head()
    for parameter in head.parameters():
        parameter.data.zero_()
    head[-1].bias.data.fill_(float(torch.logit(torch.tensor(nonplayer))))
    state = {"format": "pitch-role-context-v1", "input_dimension": 46, "teacher_sha256": "teacher",
             "kit_weights_sha256": "kit", "mean": torch.zeros(46), "std": torch.ones(46),
             "cnn_center": torch.zeros(576), "cnn_projection": torch.zeros(576, 32),
             "state_dict": head.state_dict()}
    path = tmp_path / "context.pt"
    torch.save(state, path)
    return RoleContext({"weights": str(path), "model_id": "trained-context", "player_threshold": .95,
                        "nonplayer_threshold": .99, "protect_end_fraction": .08}, "teacher", "kit")


def person(index=0):
    return Detection(str(index), "generic", 0, "person", [100., 100., 140., 200.], .9,
                     projection_status="valid", field_position=[.5, .5], role_model_id="teacher",
                     detector_semantic_class="person", role_probabilities=[.02, .97, .01],
                     team_embedding=np.eye(32)[index % 2].tolist(),
                     context_embedding=np.eye(32)[index % 2].tolist())


def test_context_features_are_permutation_equivariant_and_use_original_image_size():
    rng = np.random.default_rng(42)
    probability = rng.dirichlet([1, 1, 1], 8)
    kits, embeddings, positions = rng.random((8, 32)), rng.random((8, 32)), rng.random((8, 2))
    boxes = np.array([[50 + 40 * i, 100, 80 + 40 * i, 180] for i in range(8)])
    features = context_features(probability, kits, embeddings, positions, boxes, (1920, 1080))
    order = rng.permutation(8)
    reordered = context_features(probability[order], kits[order], embeddings[order], positions[order],
                                 boxes[order], (1920, 1080))
    assert features.shape == (8, 46)
    assert np.allclose(features[order], reordered)
    assert np.allclose(features, context_features(probability, kits, embeddings, positions, boxes / 3, (640, 360)))


def test_negative_refinement_protects_source_players_near_goals_and_ignores_outside_people(tmp_path):
    classifier = model(tmp_path, .999)
    group = [person(i) for i in range(6)]
    for d in group[:5]:
        d.semantic_class = "player"
    group[3].field_position = [.03, .5]
    group[4].projection_status = "outside_field"
    # A person near a goal must never become a player just because of position.
    group[5].field_position = [.03, .5]
    classifier.update(group, (1920, 1080))
    assert all(d.semantic_class == "referee" for d in group[:3])
    assert group[3].semantic_class == group[4].semantic_class == "player"
    assert group[4].role_context_model_id is None
    assert group[5].semantic_class == "person"
    assert group[0].role_decision == "pitch_context_nonplayer"


def test_positive_refinement_requires_trained_crop_features_and_respects_specialist_referee(tmp_path):
    classifier = model(tmp_path, .001)
    group = [person(i) for i in range(7)]
    group[4].role_evidence = {"semantic_class": "referee", "confidence": .9}
    group[5].role_model_id = None
    group[6].projection_status = "calibration_unavailable"
    classifier.update(group, (1920, 1080))
    assert all(d.semantic_class == "player" for d in group[:4])
    assert all(d.semantic_class == "person" for d in group[4:])
    assert group[5].role_context_player_score is None


def test_short_context_and_mismatched_teachers_do_not_change_roles(tmp_path):
    classifier = model(tmp_path, .001)
    group = [person(i) for i in range(3)]
    classifier.update(group, (1920, 1080))
    assert all(d.semantic_class == "person" for d in group)
    with pytest.raises(PipelineError, match="past niet"):
        RoleContext(classifier.spec, "different-teacher", "kit")


def test_a_trained_goalkeeper_class_is_preserved_even_away_from_the_goal(tmp_path):
    classifier = model(tmp_path, .999)
    group = [person(i) for i in range(4)]
    keeper = group[0]
    keeper.semantic_class, keeper.player_kind, keeper.player_kind_source = "player", "goalkeeper", "detector"
    classifier.update(group, (1920, 1080))
    assert keeper.semantic_class == "player"


def test_context_training_rejects_reserved_splits_before_opening_images(tmp_path, monkeypatch):
    from football_pipeline import broadcast_context_training

    monkeypatch.setattr(torch, "load", lambda *a, **kw: {"rows": [{"split": "test"}]})
    monkeypatch.setattr(broadcast_context_training, "sha256_file", lambda *a: pytest.fail("reserved image was opened"))
    with pytest.raises(ValueError, match="Reserved split"):
        broadcast_context_training.train(tmp_path)


def test_color_recovery_cannot_undo_a_learned_negative_context_decision():
    from football_pipeline.kit_embedding import PitchTeamSamples
    from football_pipeline.teams import TeamAssigner, load_team_settings

    settings = load_team_settings({"method": "torso_embedding_dominant_modes_v1", "confirmation_samples": 1,
                                   "kit_player_recovery": True})
    samples = PitchTeamSamples(settings, 25)
    for frame in range(0, 25, 5):
        for i in range(4):
            d = person(i)
            d.semantic_class = "player"
            samples.add(d, frame)
    target = person(0)
    target.semantic_class, target.role_decision = "referee", "pitch_context_nonplayer"
    TeamAssigner(samples.fit(), 25).update([target], 0)
    assert target.semantic_class == "referee" and target.team_id is None
