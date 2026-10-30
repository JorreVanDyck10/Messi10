from copy import deepcopy

import numpy as np
import pytest
from test_automatic_calibration import observation
from test_field_motion import texture

from football_pipeline.automatic_calibration import transform
from football_pipeline.contracts import Detection
from football_pipeline.field_layout import POINTS_UV
from football_pipeline.field_motion import (
    MOTION_RANK_SETTINGS,
    RANK_GUARD_SETTINGS,
    CameraCalibration,
    estimate_checked,
    geometry_holdout_ids,
)
from football_pipeline.keeper_teams import KeeperTeamConsensus
from football_pipeline.temporal_roles import TemporalOfficials
from football_pipeline.tracking_evaluation import identity_metrics


def obj(identity, box=None):
    return {"track_id": identity, "bbox": box or [0, 0, 10, 20]}


def test_identity_global_assignment_penalizes_fragmentation_and_false_tracks():
    frames = [([obj(1)], [obj(10)]), ([obj(1)], [obj(11)]), ([obj(1)], [obj(11)])]
    result = identity_metrics(frames)
    assert result["IDTP"] == 2
    assert result["IDFN"] == result["IDFP"] == 1
    assert result["IDF1"] == pytest.approx(2 / 3)
    assert result["ID_switches"] == 1
    assert identity_metrics([([], [obj(2)])])["IDFP"] == 1
    assert identity_metrics([([obj(1)], [])])["IDFN"] == 1
    assert identity_metrics([([obj(1)], [obj(2, [50, 50, 60, 70])])])["IDTP"] == 0


def test_identity_assignment_is_global_even_with_competing_spatial_pairs():
    # Either predicted track overlaps either reference. Global identity assignment
    # can retain both tracks; a local greedy match must not discard possibilities.
    result = identity_metrics([([obj(1), obj(2)], [obj(10), obj(20)])] * 3)
    assert result["IDF1"] == 1
    with pytest.raises(ValueError, match="unique IDs"):
        identity_metrics([([obj(1), obj(1)], [])])


def official():
    return Detection(
        "d",
        "detector",
        0,
        "player",
        [10, 10, 30, 60],
        0.9,
        field_position=[0.5, 0.5],
        projection_status="valid",
        track_id=3,
        role_probabilities=[0.1, 0.8, 0.1],
        role_context_player_score=0.2,
    )


def test_temporal_official_consensus_protects_resets_players_and_keepers(monkeypatch):
    monkeypatch.setattr("football_pipeline.temporal_roles.embedding_candidate", lambda *args: (None, 0.4))
    consensus = TemporalOfficials(25, {})
    for index in range(3):
        detection = official()
        consensus.update([detection], index)
        assert detection.semantic_class == ("referee" if index == 2 else "player")
    assert detection.track_id is None
    for changes in (
        {"player_kind": "goalkeeper"},
        {"projection_status": "calibration_unavailable"},
        {"role_probabilities": [0.95, 0.04, 0.01]},
        {"field_position": [0.05, 0.5]},
    ):
        protected = official()
        for key, value in changes.items():
            setattr(protected, key, value)
        consensus.update([protected], consensus.last_index + 1)
        assert protected.semantic_class == "player"
    for reset in (True, False):
        fresh = official()
        consensus.update([fresh], consensus.last_index + (1 if reset else 10), reset=reset)
        assert fresh.semantic_class == "player"


def test_temporal_consensus_does_not_transfer_history_between_overlapping_people(monkeypatch):
    monkeypatch.setattr("football_pipeline.temporal_roles.embedding_candidate", lambda *args: (None, 0.4))
    consensus = TemporalOfficials(25, {})
    for index in range(2):
        consensus.update([official()], index)
    first = official()
    second = deepcopy(first)
    consensus.update([first, second], 2)
    assert first.semantic_class == second.semantic_class == "player"


def test_keeper_team_requires_repeated_unambiguous_local_support():
    consensus = KeeperTeamConsensus(25)

    def group(team="A"):
        keeper = official()
        keeper.player_kind, keeper.field_position = "goalkeeper", [0.04, 0.5]
        players = []
        for i in range(3):
            player = official()
            player.player_kind = None
            player.track_id = i + 10
            player.team_id = team
            player.field_position = [0.1 + i * 0.01, 0.45 + i * 0.05]
            players.append(player)
        return [keeper, *players]

    for index in range(consensus.required):
        detections = group()
        consensus.update(detections, index)
        assert detections[0].team_id == ("A" if index == consensus.required - 1 else None)
    fresh = group()
    consensus.update(fresh, consensus.required, reset=True)
    assert fresh[0].team_id is None
    for index in range(consensus.required + 1, consensus.required * 3):
        ambiguous = group()
        ambiguous[-1].team_id = "B"
        consensus.update(ambiguous, index)
        assert ambiguous[0].team_id is None


def test_geometric_control_split_retains_enough_noncollinear_fit_points():
    points = [
        {"id": i, "x": 100 + 1000 * POINTS_UV[i][0], "y": 100 + 1000 * POINTS_UV[i][1], "confidence": 1.0}
        for i in (8, 13, 17, 20, 21, 24, 25)
    ]
    observation = {"points": points, "lines": []}
    assert estimate_checked(observation, (1920, 1080))["status"] in {
        "degenerate_geometry",
        "inconsistent_controls",
    }
    controls = geometry_holdout_ids(points)
    fitted = estimate_checked(observation, (1920, 1080), control_ids=controls)
    assert fitted["status"] == "valid"
    assert max(fitted["quality"]["control_errors_px"]) < 1e-3
    assert set(fitted["quality"]["fit_ids"]).isdisjoint(controls)
    assert geometry_holdout_ids(list(reversed(points))) == controls
    assert estimate_checked(observation, (1920, 1080), RANK_GUARD_SETTINGS)["status"] == "valid"


def test_rank_guard_does_not_accept_an_underdetermined_full_point_set():
    # Five points on one goal line and only one point away from it cannot
    # determine a projective transformation, regardless of control selection.
    points = [
        {"id": i, "x": 100 + 1000 * POINTS_UV[i][0], "y": 100 + 1000 * POINTS_UV[i][1], "confidence": 1.0}
        for i in (8, 13, 17, 20, 24, 25)
    ]
    assert geometry_holdout_ids(points) is None
    assert (
        estimate_checked({"points": points, "lines": []}, (1920, 1080), RANK_GUARD_SETTINGS)["status"]
        == "degenerate_geometry"
    )


def test_rank_deficient_frame_can_only_bridge_from_a_recent_trusted_anchor():
    anchor = estimate_checked(observation(), (640, 360))
    inverse = np.linalg.inv(np.asarray(anchor["homography"]))
    points = []
    for identifier in (8, 13, 17, 20, 21, 24, 25):
        x, y = transform([POINTS_UV[identifier]], inverse)[0]
        points.append({"id": identifier, "x": float(x), "y": float(y), "confidence": 1.0})
    missing = estimate_checked({"points": points, "lines": []}, (640, 360), MOTION_RANK_SETTINGS)
    assert missing["status"] == "insufficient_fit_geometry"
    assert missing["homography"] is None
    frame = texture()
    assert CameraCalibration(2, MOTION_RANK_SETTINGS).update(frame, missing, 0)["status"] != "valid"
    camera = CameraCalibration(2, MOTION_RANK_SETTINGS)
    camera.update(frame, anchor, 0)
    for index in range(1, 5):
        bridged = camera.update(frame, missing, index)
        assert bridged["status"] == "valid"
        assert bridged["source"] == "tracked"
        assert bridged["reference_frame"] == 0
        assert bridged["age_s"] == index / 2
    assert camera.update(frame, missing, 5)["status"] == "bridge_expired"
    cut = CameraCalibration(2, MOTION_RANK_SETTINGS)
    cut.update(frame, anchor, 0)
    assert cut.update(np.zeros_like(frame), missing, 1)["status"] == "camera_cut"
    assert cut.update(frame, missing, 2)["status"] != "valid"
    gap = CameraCalibration(2, MOTION_RANK_SETTINGS)
    gap.update(frame, anchor, 0)
    assert gap.update(frame, missing, 3)["status"] != "valid"
