import io
import json

import numpy as np
import pytest
import torch

from football_pipeline.appearance import ROLE_NAMES, TEAM_NAMES, AppearanceClassifier, backbone
from football_pipeline.contracts import Detection, FrameRecord, sha256_file
from football_pipeline.detection import available_roles, load_model_manifest, merge_person_proposals
from football_pipeline.geometry import project_detection
from football_pipeline.participants import player_summary
from football_pipeline.replay import replay_detections
from football_pipeline.teams import VideoTeams


def fixed_classifier(tmp_path, role):
    encoder = backbone()
    role_head = torch.nn.Linear(608, len(ROLE_NAMES))
    team_head = torch.nn.Linear(608, 2)
    with torch.no_grad():
        role_head.weight.zero_()
        role_head.bias.zero_()
        if role is not None:
            role_head.bias[ROLE_NAMES.index(role)] = 20
        team_head.weight.zero_()
        team_head.bias.copy_(torch.tensor([20.0, 0.0]))
    path = tmp_path / "controlled-heads.pt"
    torch.save(
        {
            "backbone": encoder.state_dict(),
            "role_head": role_head.state_dict(),
            "team_head": team_head.state_dict(),
            "role_names": ROLE_NAMES,
            "team_names": TEAM_NAMES,
            "mean": torch.zeros(608),
            "std": torch.ones(608),
            "team_video_hashes": ["known"],
        },
        path,
    )
    return {
        "weights": str(path),
        "weights_sha256": sha256_file(path),
        "model_id": "controlled_fixture",
        "role_names": ROLE_NAMES,
        "role_confidence": 0.65,
        "team_confidence": 0.65,
        "device": "cpu",
    }


def person(role="player", box=None):
    return Detection("0:0", "fixture", 0, role, box or [100, 100, 130, 180], 0.9)


def test_trained_role_can_override_player_without_using_field_location(tmp_path, calibration):
    model = AppearanceClassifier(fixed_classifier(tmp_path, "steward"))
    detection = person()
    model.classify(np.zeros((360, 640, 3), np.uint8), [detection], "known")
    assert detection.semantic_class == "steward"
    assert detection.detector_semantic_class == "player"
    assert detection.role_model_id == "controlled_fixture"
    assert detection.role_class_id == ROLE_NAMES.index("steward")
    assert detection.team_id is None
    project_detection(detection, calibration)
    assert detection.projection_status == "valid"
    assert player_summary(FrameRecord(0, 0, (640, 360), [detection]))["on_field"] == 0


def test_uncertain_role_abstains_and_new_video_does_not_inherit_supervised_team(tmp_path):
    pixels = np.zeros((360, 640, 3), np.uint8)
    model = AppearanceClassifier(fixed_classifier(tmp_path, "player"))
    known, unknown = person(), person()
    model.classify(pixels, [known], "known")
    model.classify(pixels, [unknown], "another-match")
    assert known.team_id == "team_a" and known.team_method == "supervised_match"
    assert known.team_class_id == 0 and unknown.team_class_id is None
    assert unknown.team_id is None
    uncertain = AppearanceClassifier(fixed_classifier(tmp_path, None))
    d = person()
    uncertain.classify(pixels, [d], "known")
    assert d.semantic_class == "person" and d.team_id is None


def test_person_proposals_are_merged_without_losing_ball_or_source_identity():
    player = person()
    generic = person("person")
    generic.detection_id = "0:1"
    other = person("person", [200, 100, 230, 180])
    other.detection_id = "0:2"
    ball = person("ball")
    ball.detection_id = "0:3"
    merged = merge_person_proposals([generic, player, other, ball])
    assert [d.detection_id for d in merged] == ["0:0", "0:2", "0:3"]
    assert [d.source_class_id for d in merged] == [0, 0, 0]


def test_contained_upper_body_uses_strong_full_body_proposal_and_real_feet():
    upper = person("referee", [2418, 591, 2458, 659])
    upper.model_id = "specialist"
    upper.confidence = 0.98
    complete = person("person", [2413, 586, 2458, 722])
    complete.model_id = "generic"
    complete.confidence = 0.75
    complete.detection_id = "full-body"
    result = merge_person_proposals([complete, upper])
    assert result == [complete]
    assert result[0].model_id == "generic"
    assert result[0].bbox_xyxy[-1] == 722
    # A weak proposal cannot replace a reliable specialized detector's box.
    complete.confidence = 0.3
    assert merge_person_proposals([complete, upper]) == [upper]


def test_containment_does_not_merge_distinct_overlapping_people():
    tall = person("person", [100, 100, 140, 240])
    tall.model_id = "generic"
    short = person("player", [110, 145, 138, 220])
    short.model_id = "specialist"
    # Contained lower body belongs to a different, occluded person: heads differ.
    assert len(merge_person_proposals([short, tall])) == 2
    short.bbox_xyxy = [118, 105, 140, 180]
    # Off-axis subjects also stay separate.
    assert len(merge_person_proposals([short, tall])) == 2
    short.bbox_xyxy = [105, 105, 135, 180]
    short.model_id = "generic"
    assert len(merge_person_proposals([short, tall])) == 2


def test_kit_features_suppress_grey_hue_noise_and_keep_green_clothing():
    from football_pipeline.teams import kit_feature

    frame = np.full((100, 80, 3), (150, 150, 150), np.uint8)
    grey = kit_feature(frame, [0, 0, 80, 100])
    assert not grey[:16].any()  # Undefined hue of a grey shirt contributes no evidence.
    frame[:] = (20, 180, 20)
    green = kit_feature(frame, [0, 0, 80, 100])
    assert green is not None and green[:16].sum() > 0.5


def test_refining_video_clusters_keeps_team_names_stable():
    frame = np.zeros((360, 640, 3), np.uint8)
    players = []
    for i in range(8):
        x = 20 + i * 65
        box = [x, 100, x + 30, 180]
        frame[100:180, x : x + 30] = (240, 240, 240) if i < 4 else (200, 40, 10)
        d = person(box=box)
        d.role_confidence = 0.9
        players.append(d)
    model = VideoTeams()
    for _ in range(3):
        model.update(frame, players)
    original = [d.team_id for d in players]
    # Opposite proposal order and more observations must not swap A and B.
    for _ in range(30):
        model.update(frame, list(reversed(players)))
        assert [d.team_id for d in players] == original
    assert len(model.samples) == 200


def test_manifest_pins_appearance_weights_and_capabilities(model_manifest, tmp_path):
    from football_pipeline.contracts import PipelineError, write_json

    path, manifest = model_manifest
    manifest["appearance"] = fixed_classifier(tmp_path, "player")
    write_json(path, manifest)
    assert "steward" in available_roles(load_model_manifest(path))
    manifest["appearance"]["weights_sha256"] = "bad"
    write_json(path, manifest)
    with pytest.raises(PipelineError, match="hash"):
        load_model_manifest(path)


def test_new_video_colour_clusters_wait_for_two_kits_and_keep_other_roles_out():
    frame = np.zeros((360, 640, 3), np.uint8)
    players = []
    for i in range(8):
        x = 20 + i * 65
        box = [x, 100, x + 30, 180]
        frame[100:180, x : x + 30] = (240, 240, 240) if i < 4 else (200, 40, 10)
        d = person(box=box)
        d.role_confidence = 0.9
        players.append(d)
    steward = person("steward")
    steward.role_confidence = 0.9
    model = VideoTeams()
    for _ in range(2):
        model.update(frame, [*players, steward])
    assert not model.info["ready"] and not any(d.team_id for d in players)
    model.update(frame, [*players, steward])
    assert model.info["ready"]
    assert len({d.team_id for d in players[:4]}) == len({d.team_id for d in players[4:]}) == 1
    assert players[0].team_id != players[-1].team_id
    assert all(d.team_method == "video_colour_clusters" for d in players)
    assert steward.team_id is None
    one_kit = VideoTeams()
    for _ in range(6):
        one_kit.update(frame, players[:4])
    assert not one_kit.info["ready"]


def test_team_counts_and_replay_preserve_appearance_but_recompute_geometry(calibration, video_metadata):
    detections = [person(), person(), person()]
    for d, team in zip(detections, ["team_a", "team_b", None]):
        project_detection(d, calibration)
        d.team_id = team
        d.role_model_id = "model"
    detections[-1].bbox_xyxy = [5, 100, 15, 150]
    project_detection(detections[-1], calibration)
    record = FrameRecord(0, 0, (640, 360), detections)
    assert record.to_dict()["player_summary"]["teams"] == {"team_a": 1, "team_b": 1, "unknown": 0}
    restored = replay_detections(io.StringIO(json.dumps(record.to_dict()) + "\n"), 0, video_metadata)
    assert [d.team_id for d in restored] == ["team_a", "team_b", None]
    assert all(d.field_position is None and d.track_id is None for d in restored)
    assert all(d.projection_status == "not_projected" for d in restored)


def test_tiled_proposals_restore_source_coordinates_and_reject_cut_person_boxes():
    from types import SimpleNamespace

    from football_pipeline.detection import UltralyticsDetector

    class Proposals:
        calls = 0

        def predict(self, pixels, **kwargs):
            self.calls += 1
            boxes = (
                [] if self.calls == 1 else [[280, 50, 299, 150]] if self.calls == 2 else [[100, 40, 140, 160]]
            )
            return [
                SimpleNamespace(
                    orig_shape=pixels.shape[:2],
                    boxes=SimpleNamespace(
                        xyxy=torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4),
                        conf=torch.tensor([0.9] * len(boxes)),
                        cls=torch.tensor([7.0] * len(boxes)),
                    ),
                )
            ]

    detector = object.__new__(UltralyticsDetector)
    detector.appearance = None
    detector.models = [
        (
            {
                "model_id": "tile_fixture",
                "class_mapping": {"7": "person"},
                "imgsz": 640,
                "confidence": 0.1,
                "iou": 0.7,
                "tile_width": 300,
                "tile_overlap": 0.25,
                "tile_imgsz": 640,
            },
            Proposals(),
        )
    ]
    output = detector.detect(np.zeros((200, 500, 3), np.uint8), 9)
    assert len(output) == 1
    assert output[0].bbox_xyxy == [300, 40, 340, 160]
    assert output[0].source_class_id == 7 and output[0].model_id == "tile_fixture"


def test_changing_video_identity_resets_only_video_local_team_calibration():
    from types import SimpleNamespace

    from football_pipeline.detection import UltralyticsDetector

    detector = object.__new__(UltralyticsDetector)
    detector.video_hash = "old"
    existing = VideoTeams()
    existing.samples = [np.zeros(32)]
    existing.updates = 8
    detector.appearance = SimpleNamespace(video_teams=existing)
    detector.set_video_identity("old")
    assert detector.appearance.video_teams is existing
    detector.set_video_identity("new")
    assert detector.appearance.video_teams is not existing
    assert detector.appearance.video_teams.info["updates"] == 0


def test_role_dataset_builder_never_overwrites_recorded_human_review(tmp_path, monkeypatch):
    from persoon1 import role_training

    monkeypatch.setattr(role_training, "DATA", tmp_path)
    path = tmp_path / "manifest.json"
    original = '{"human_review_completed":true}'
    path.write_text(original, encoding="utf-8")
    with pytest.raises(ValueError, match="menselijke reviews"):
        role_training.build()
    assert path.read_text() == original
