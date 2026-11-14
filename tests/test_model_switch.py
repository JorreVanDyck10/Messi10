import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest

from football_pipeline.contracts import PipelineError, read_json, sha256_file, write_json
from football_pipeline.detection import UltralyticsDetector, load_model_manifest
from football_pipeline.model_switch import local_profile, rebase_profile, register_yolo26, select_profile


@pytest.fixture
def switch_root(tmp_path, model_manifest, monkeypatch):
    """Maak een kleine modelregistratiefixture zonder een echte trainingsrun te simuleren."""
    _, baseline = model_manifest
    root = tmp_path / "checkout"
    (root / "configs").mkdir(parents=True)
    ball = tmp_path / "ball.pt"
    ball.write_bytes(b"synthetic ball weight identity")
    baseline["models"].append(
        {
            **baseline["models"][0],
            "model_id": "ball",
            "weights": str(ball),
            "class_mapping": {"0": "ball"},
            "expected_names": {"0": "ball"},
        }
    )
    baseline["person_geometry"] = True
    baseline["analysis_scope"] = "on_pitch_players"
    baseline["person_box_fusion_weight"] = 0.5
    write_json(root / "configs/models-broadcast-yolo11.json", baseline)
    checkpoint = tmp_path / "candidate.pt"
    checkpoint.write_bytes(b"synthetic checkpoint metadata fixture, not a trained model")
    import ultralytics

    monkeypatch.setattr(
        ultralytics,
        "YOLO",
        lambda path: SimpleNamespace(
            task="detect",
            names={0: "player"},
            model=SimpleNamespace(yaml={"yaml_file": "yolo26s.yaml"}),
        ),
    )
    return root, checkpoint, baseline


def test_missing_yolo26_has_clear_import_path_and_keeps_yolo11_available(switch_root):
    root, _, _ = switch_root
    with pytest.raises(PipelineError, match="Import-Yolo26"):
        select_profile("yolo26", root)
    assert select_profile("yolo11", root).name == "models-broadcast-yolo11.json"


def test_registration_duplicates_weights_and_preserves_other_models_and_settings(switch_root):
    root, checkpoint, baseline = switch_root
    original = (root / "configs/models-broadcast-yolo11.json").read_bytes()
    profile = register_yolo26(checkpoint, root)
    installed = read_json(profile)
    loaded = load_model_manifest(profile)
    assert (root / "configs/models-broadcast-yolo11.json").read_bytes() == original
    assert baseline["models"][0]["weights"] != loaded["models"][0]["weights"]
    assert loaded["models"][1] == load_model_manifest(select_profile("yolo11", root))["models"][1]
    assert installed["models"][0]["confidence"] == baseline["models"][0]["confidence"]
    assert installed["models"][0]["iou"] == baseline["models"][0]["iou"]
    assert installed["person_box_fusion_weight"] == baseline["person_box_fusion_weight"]
    stored = profile.parent / installed["models"][0]["weights"]
    assert stored.resolve() != checkpoint.resolve()
    assert stored.read_bytes() == checkpoint.read_bytes()
    assert installed["models"][0]["weights_sha256"] == sha256_file(checkpoint)
    assert installed["models"][0]["nms"] is True
    assert register_yolo26(checkpoint, root) == profile


def test_registration_does_not_replace_a_different_registered_candidate(switch_root):
    root, checkpoint, _ = switch_root
    profile = register_yolo26(checkpoint, root)
    before = profile.read_bytes()
    checkpoint.write_bytes(b"different synthetic checkpoint")
    with pytest.raises(PipelineError, match="ander YOLO26-profiel"):
        register_yolo26(checkpoint, root)
    assert profile.read_bytes() == before


@pytest.mark.parametrize(
    "architecture,names", [("yolo11s.yaml", {0: "player"}), ("yolo26s.yaml", {0: "person"})]
)
def test_registration_rejects_wrong_architecture_or_generic_person_model(
    switch_root, monkeypatch, architecture, names
):
    root, checkpoint, _ = switch_root
    import ultralytics

    monkeypatch.setattr(
        ultralytics,
        "YOLO",
        lambda path: SimpleNamespace(
            task="detect",
            names=names,
            model=SimpleNamespace(yaml={"yaml_file": architecture}),
        ),
    )
    with pytest.raises(PipelineError):
        register_yolo26(checkpoint, root)
    assert not (root / "configs/models-broadcast-yolo26.json").exists()


def test_relative_profile_movement_preserves_the_actual_referenced_files(tmp_path):
    origin, destination = tmp_path / "configs", tmp_path / "cache"
    baseline = {"models": [{"weights": "../models/p.pt"}], "appearance": {"weights": "../models/a.pt"}}
    before = copy.deepcopy(baseline)
    result = rebase_profile(baseline, origin, destination)
    assert baseline == before
    for a, b in [
        (baseline["models"][0], result["models"][0]),
        (baseline["appearance"], result["appearance"]),
    ]:
        assert (origin / a["weights"]).resolve() == (destination / b["weights"]).resolve()


def test_cpu_working_profile_leaves_the_rollback_profile_unchanged(switch_root):
    root, _, _ = switch_root
    original = select_profile("yolo11", root).read_bytes()
    path = local_profile("yolo11", "cpu", root)
    assert all(s["device"] == "cpu" for s in read_json(path)["models"])
    assert select_profile("yolo11", root).read_bytes() == original
    with pytest.raises(PipelineError, match="Device"):
        local_profile("yolo11", "../../wrong", root)


def test_nms_override_reaches_only_the_model_that_requests_it():
    import torch

    calls = []

    class FakeModel:
        def predict(self, pixels, **kwargs):
            """Leg de echte adapterargumenten vast en geef een lege actuele detectielijst terug."""
            calls.append(kwargs)
            return [
                SimpleNamespace(
                    orig_shape=pixels.shape[:2],
                    boxes=SimpleNamespace(
                        xyxy=torch.empty((0, 4)),
                        conf=torch.empty(0),
                        cls=torch.empty(0),
                    ),
                )
            ]

    standard = {
        "model_id": "fixture",
        "class_mapping": {"0": "player"},
        "imgsz": 320,
        "confidence": 0.1,
        "iou": 0.7,
        "device": "cpu",
    }
    detector = UltralyticsDetector.__new__(UltralyticsDetector)
    detector.appearance = None
    detector.models = [(standard, FakeModel()), ({**standard, "nms": True}, FakeModel())]
    assert detector.detect(np.zeros((320, 320, 3), np.uint8), 0) == []
    assert "nms" not in calls[0]
    assert calls[1]["nms"] is True


def test_manifest_rejects_non_boolean_nms(model_manifest):
    path, manifest = model_manifest
    manifest["models"][0]["nms"] = "true"
    path.write_text(json.dumps(manifest))
    with pytest.raises(PipelineError, match="NMS-keuze"):
        load_model_manifest(path)
