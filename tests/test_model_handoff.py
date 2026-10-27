from pathlib import Path
from types import SimpleNamespace

import pytest

from football_pipeline.contracts import PipelineError, read_json, sha256_file, write_json
from football_pipeline.detection import load_model_manifest
from football_pipeline.model_handoff import available_model_profiles, register_player_model


@pytest.fixture
def handoff(tmp_path, monkeypatch):
    import ultralytics

    weights = tmp_path / "weights" / "players_best.pt"
    weights.parent.mkdir()
    weights.write_bytes(b"synthetic model metadata fixture; never real trained weights")
    mapping = tmp_path / "mapping.json"
    write_json(mapping, {"0": "player", "1": "referee", "2": "ball"})
    monkeypatch.setattr(
        ultralytics,
        "YOLO",
        lambda path: SimpleNamespace(
            task="detect",
            names={0: "player", 1: "referee", 2: "ball"},
        ),
    )
    return weights, mapping, tmp_path / "configs" / "models-players.json"


def test_register_player_model_verifies_names_hashes_and_preserves_previous_version(handoff):
    weights, mapping, output = handoff
    evaluation = weights.parent / "evaluation.json"
    write_json(evaluation, {"fixture": True})
    register_player_model(weights, mapping, output, evaluation_record=evaluation)
    manifest = load_model_manifest(output)
    assert manifest["models"][0]["expected_names"] == {"0": "player", "1": "referee", "2": "ball"}
    assert manifest["models"][0]["weights_sha256"] == sha256_file(weights)
    assert manifest["models"][0]["confidence"] == 0.10
    assert manifest["handoff"]["evaluation_sha256"] == sha256_file(evaluation)
    assert "human_accepted" not in manifest
    original = output.read_bytes()
    with pytest.raises(PipelineError, match="bestaat al"):
        register_player_model(weights, mapping, output)
    assert output.read_bytes() == original
    assert Path(manifest["models"][0]["weights"]).resolve() == weights.resolve()


@pytest.mark.parametrize("case", ["person", "unknown_class", "high_confidence", "no_player", "not_detect"])
def test_invalid_handoff_cannot_create_ready_profile(handoff, monkeypatch, case):
    import ultralytics

    weights, mapping, output = handoff
    kwargs = {}
    if case == "person":
        monkeypatch.setattr(
            ultralytics,
            "YOLO",
            lambda path: SimpleNamespace(
                task="detect",
                names={0: "person", 1: "referee", 2: "ball"},
            ),
        )
    elif case == "unknown_class":
        write_json(mapping, {"42": "player"})
    elif case == "high_confidence":
        kwargs["confidence"] = 0.25
    elif case == "no_player":
        write_json(mapping, {"0": "person"})
    else:
        monkeypatch.setattr(ultralytics, "YOLO", lambda path: SimpleNamespace(task="segment"))
    with pytest.raises(PipelineError):
        register_player_model(weights, mapping, output, **kwargs)
    assert not output.exists()


def test_profile_discovery_adds_registered_model_without_restarting(handoff):
    weights, mapping, output = handoff
    default = output.parent / "models.json"
    output.parent.mkdir()
    write_json(default, {"schema_version": 1, "profile_name": "Baseline", "models": [{"fixture": True}]})
    assert list(available_model_profiles(default, output.parent).values()) == ["Baseline"]
    register_player_model(weights, mapping, output)
    profiles = available_model_profiles(default, output.parent)
    assert list(profiles)[0] == default.resolve()
    assert output.resolve() in profiles
    assert read_json(output)["profile_name"] == profiles[output.resolve()]


def test_equivalent_model_profiles_are_shown_once_despite_relative_paths(tmp_path):
    weights = tmp_path / "weights.pt"
    weights.write_bytes(b"identity")
    default = tmp_path / "models.json"
    alias = tmp_path / "models-alias.json"
    manifest = {
        "schema_version": 1,
        "profile_name": "Personen op GPU — herkenning",
        "models": [{"model_id": "persons", "weights": "weights.pt", "device": "0"}],
    }
    write_json(default, manifest)
    manifest["models"][0]["weights"] = str(weights)
    write_json(alias, manifest)
    assert available_model_profiles(default, tmp_path) == {default.resolve(): "Personen op GPU — herkenning"}
