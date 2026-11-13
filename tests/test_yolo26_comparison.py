import copy
import time
from types import SimpleNamespace

import pytest

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.yolo26_comparison import (
    ExperimentPaused,
    candidate_profile,
    checkpoint_saved,
    loss_values,
    rank_models,
    usage_guard,
    validate_dataset,
)


def dataset(tmp_path):
    rows = []
    for split, game in (("train", "train-match"), ("val", "val-match")):
        image, label = tmp_path / f"{split}.jpg", tmp_path / f"{split}.txt"
        image.write_bytes(split.encode())
        label.write_text("0 0.5 0.5 0.1 0.2\n")
        rows.append(
            {
                "split": split,
                "game_id": game,
                "image": str(image),
                "label": str(label),
                "image_sha256": sha256_file(image),
                "label_sha256": sha256_file(label),
            }
        )
    write_json(tmp_path / "manifest.json", {"frames": rows})
    return rows


def test_dataset_checks_source_hashes_and_disjoint_matches(tmp_path):
    rows = dataset(tmp_path)
    assert validate_dataset(tmp_path)["counts"] == {"train": 1, "val": 1}
    (tmp_path / "val.txt").write_text("0 0.3 0.3 0.1 0.2\n")
    with pytest.raises(ValueError, match="Changed or missing"):
        validate_dataset(tmp_path)
    rows[1]["label_sha256"] = sha256_file(tmp_path / "val.txt")
    rows[1]["game_id"] = rows[0]["game_id"]
    write_json(tmp_path / "manifest.json", {"frames": rows})
    with pytest.raises(ValueError, match="crosses"):
        validate_dataset(tmp_path)


def test_reserved_images_rejected_before_access(tmp_path):
    write_json(tmp_path / "manifest.json", {"frames": [{"split": "test", "image": "must-not-open"}]})
    with pytest.raises(ValueError, match="Reserved"):
        validate_dataset(tmp_path)


@pytest.mark.parametrize(
    "remaining,starting,allowed",
    [(11, True, True), (10, True, False), (6, False, True), (5, False, False), (0, False, False)],
)
def test_account_quota_reserves_handoff_capacity(tmp_path, remaining, starting, allowed):
    write_json(tmp_path / "usage.json", {"remaining_percent": remaining, "checked_at": 1000})
    if allowed:
        usage_guard(tmp_path, starting=starting, now=1000)
    else:
        with pytest.raises(ExperimentPaused):
            usage_guard(tmp_path, starting=starting, now=1000)


def test_stale_unknown_and_explicit_pause_block_training(tmp_path):
    with pytest.raises(ExperimentPaused, match="unavailable"):
        usage_guard(tmp_path)
    write_json(tmp_path / "usage.json", {"remaining_percent": 99, "checked_at": 1000})
    with pytest.raises(ExperimentPaused, match="older"):
        usage_guard(tmp_path, now=1901)
    write_json(tmp_path / "usage.json", {"remaining_percent": None, "checked_at": 1000})
    with pytest.raises(ExperimentPaused):
        usage_guard(tmp_path, now=1000)
    (tmp_path / "pause.request").touch()
    with pytest.raises(ExperimentPaused, match="Explicit"):
        usage_guard(tmp_path)


def test_pause_preserves_completed_checkpoint_before_unwinding(tmp_path):
    output = tmp_path / "experiment"
    directory = output / "candidate"
    directory.mkdir(parents=True)
    last = directory / "last.pt"
    last.write_bytes(b"native optimizer and epoch state, before strip_optimizer")
    write_json(output / "usage.json", {"remaining_percent": 5, "checked_at": time.time()})
    trainer = SimpleNamespace(last=last, best=last, epoch=7, epochs=100, metrics={"score": 0.75})
    with pytest.raises(ExperimentPaused):
        checkpoint_saved(trainer, output, directory, "verified-inputs")
    assert (directory / "resume.pt").read_bytes() == last.read_bytes()
    state = read_json(directory / "status.json")
    assert state["epoch"] == 8 and state["dataset_identity"] == "verified-inputs"
    assert state["checkpoint_sha256"] == sha256_file(directory / "resume.pt")


def test_candidate_changes_only_player_supplier_and_retains_andrew(model_manifest, tmp_path):
    _, baseline = model_manifest
    baseline["models"].append(
        {"model_id": "andrew", "class_mapping": {"0": "ball"}, "weights": "andrew.pt", "confidence": 0.03}
    )
    baseline["appearance"] = {"weights": "roles.pt"}
    before = copy.deepcopy(baseline)
    weights = tmp_path / "candidate.pt"
    weights.write_bytes(b"candidate")
    result = candidate_profile(baseline, weights, "yolo26s")
    assert baseline == before
    assert result["models"][1:] == baseline["models"][1:]
    assert result["appearance"] == baseline["appearance"]
    assert result["models"][0]["class_mapping"] == {"0": "player"}
    assert result["models"][0]["confidence"] == before["models"][0]["confidence"]


def test_speed_breaks_only_practically_equal_balanced_f1():
    rows = {
        "accurate": {"pipeline": {"macro_F1": 0.9}, "speed": {"detector_stack": {"median_ms": 50}}},
        "close": {"pipeline": {"macro_F1": 0.897}, "speed": {"detector_stack": {"median_ms": 40}}},
        "fast": {"pipeline": {"macro_F1": 0.88}, "speed": {"detector_stack": {"median_ms": 10}}},
    }
    winner, tied = rank_models(rows)
    assert winner == "close" and set(tied) == {"accurate", "close"}


def test_progress_supports_yolo26_dual_head_losses():
    import torch

    losses = {"one2many": torch.tensor([1.0, 2.0]), "one2one": torch.tensor([3.0, 4.0])}
    assert loss_values(losses) == {"one2many": [1.0, 2.0], "one2one": [3.0, 4.0]}
    assert loss_values(None) is None
