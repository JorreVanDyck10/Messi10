import gzip
import json
from copy import deepcopy

import numpy as np
import pytest

from football_pipeline import broadcast_evaluation as module
from football_pipeline.contracts import Detection
from scripts.measure_broadcast_baseline import audit_split


def test_split_audit_rejects_game_and_image_leakage():
    rows = [
        {"split": "train", "game_id": "a", "image_sha256": "one"},
        {"split": "val", "game_id": "b", "image_sha256": "two"},
    ]
    assert audit_split({"frames": rows})["cross_split_games"] == []
    for key, value in (("game_id", "a"), ("image_sha256", "one")):
        broken = deepcopy(rows)
        broken[1][key] = value
        with pytest.raises(ValueError, match="leakage"):
            audit_split({"frames": broken})


def test_runtime_workpoint_changes_matches_and_per_game_metrics(tmp_path, monkeypatch):
    dataset = tmp_path / "data"
    (dataset / "provider-labels").mkdir(parents=True)
    rows = []
    for clip, game in (("clip-a", "a"), ("clip-b", "b")):
        rows.append(
            {
                "frame_id": f"{clip}_001",
                "clip": clip,
                "game_id": game,
                "split": "val",
                "frame_index": 0,
                "image": "fake.jpg",
                "image_sha256": "hash",
                "width": 100,
                "height": 100,
                "people": [{"on_pitch": True, "role": "player", "bbox": [10, 10, 20, 40], "team": "left"}],
            }
        )
        labels = {"annotations": [], "images": [{"file_name": "001.jpg", "image_id": 1}]}
        (dataset / "provider-labels" / f"{clip}.json.gz").write_bytes(
            gzip.compress(json.dumps(labels).encode())
        )
    (dataset / "manifest.json").write_text(json.dumps({"frames": rows, "fingerprint": "fixed"}))
    monkeypatch.setattr(module, "load_model_manifest", lambda _: {})
    monkeypatch.setattr(module, "load_team_settings", lambda _: {})
    monkeypatch.setattr(module, "sha256_file", lambda _: "hash")
    monkeypatch.setattr(module.cv2, "imread", lambda _: np.zeros((100, 100, 3), np.uint8))
    monkeypatch.setattr(module, "reference_geometry", lambda *args: {"status": "valid"})

    def project(detection, *args):
        detection.projection_status = "valid"

    monkeypatch.setattr(module, "project_automatic", project)
    monkeypatch.setattr("football_pipeline.teams.shirt_color", lambda *args: None)

    class Detector:
        def __init__(self, *args):
            pass

        def set_video_identity(self, *args):
            pass

        def detect(self, *args):
            return [Detection("one", "fake", 0, "player", [10, 10, 20, 40], 0.15)]

    class Samples:
        def __init__(self, *args):
            pass

        def add(self, *args):
            pass

        def fit(self):
            return {"status": "fake"}

    class Assigner:
        def __init__(self, *args):
            pass

        def update(self, detections, *args):
            for detection in detections:
                detection.team_id = "A"

    monkeypatch.setattr(module, "UltralyticsDetector", Detector)
    monkeypatch.setattr(module, "TeamSamples", Samples)
    monkeypatch.setattr(module, "TeamAssigner", Assigner)
    low = module.evaluate_profile(dataset, None, None, tmp_path / "low", confidence=0.1)
    high = module.evaluate_profile(dataset, None, None, tmp_path / "high", confidence=0.25)
    assert low["teams"]["correct"] == 2
    assert high["teams"]["correct"] == 0
    assert low["player_detection_and_roles"]["per_class"][0]["TP"] == 2
    assert high["player_detection_and_roles"]["per_class"][0]["FN"] == 2
    assert len(low["per_game"]) == 2
    assert all(g["players"]["per_class"][0]["recall"] == 1 for g in low["per_game"])
    assert low["identity"] != high["identity"]
    assert low["independent_final_test"] is False
    # Never reuse a cached score for a different workpoint.
    with pytest.raises(ValueError, match="inputs changed"):
        module.evaluate_profile(dataset, None, None, tmp_path / "low", confidence=0.25)
