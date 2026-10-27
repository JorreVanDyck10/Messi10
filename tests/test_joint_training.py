from pathlib import Path

import cv2
import numpy as np
import pytest

from football_pipeline.app_results import linked_result
from football_pipeline.contracts import PipelineError
from football_pipeline.joint_data import check_split_leakage, load_boxes, unique_role_pixels, unique_rows
from football_pipeline.joint_training import choose_ball, choose_field, choose_player, choose_roles
from football_pipeline.training_budget import TrainingBudget, train_yolo

pytest_plugins = ["test_team_pipeline"]


def test_budget_uses_elapsed_wall_time_and_rejects_invalid_limits():
    now = [100.0]
    budget = TrainingBudget(1, clock=lambda: now[0])
    now[0] = 159.9
    assert not budget.expired
    now[0] = 160
    assert budget.expired
    for value in (0, -1, float("inf"), float("nan")):
        with pytest.raises(ValueError):
            TrainingBudget(value)


def test_atomic_json_retries_windows_reader_lock_without_losing_old_record(tmp_path, monkeypatch):
    from football_pipeline import contracts

    path = tmp_path / "status.json"
    contracts.write_json(path, {"status": "old"})
    replace = Path.replace
    attempts = []

    def locked_once(source, target):
        attempts.append(source)
        if len(attempts) < 3:
            assert contracts.read_json(target) == {"status": "old"}
            raise PermissionError("Windows reader still holds file")
        return replace(source, target)

    monkeypatch.setattr(Path, "replace", locked_once)
    monkeypatch.setattr(contracts.time, "sleep", lambda seconds: None)
    contracts.write_json(path, {"status": "complete"})
    assert len(attempts) == 3
    assert contracts.read_json(path) == {"status": "complete"}
    assert not list(tmp_path.glob("*.tmp"))


def test_worker_dispatch_uses_importable_module_when_launched_as_main(tmp_path, monkeypatch):
    from football_pipeline import joint_training

    calls = []
    monkeypatch.setattr(joint_training, "__name__", "__main__")
    monkeypatch.setattr(joint_training, "sha256_file", lambda path: "a" * 64)
    monkeypatch.setattr(joint_training.subprocess, "run", lambda command, **kwargs: calls.append(command))
    monkeypatch.setattr(joint_training, "demonstrate", lambda *args: {})
    monkeypatch.setattr(joint_training, "refit_role_pixels", lambda *args: None)
    joint_training.run(tmp_path / "data", tmp_path / "run")
    assert len(calls) == 4
    assert all(c[3] == "football_pipeline.joint_training" for c in calls)


def test_field_budget_stops_between_updates_and_returns_trained_progress(monkeypatch):
    import torch

    from football_pipeline import field_learning

    now = [-0.5]

    def clock():
        now[0] += 0.5
        return now[0]

    monkeypatch.setattr(field_learning.time, "monotonic", clock)
    model = torch.nn.Conv2d(1, 1, 1, bias=False)
    before = model.weight.detach().clone()
    loader = [(torch.ones((1, 1, 2, 2)), torch.ones((1, 1, 2, 2)), torch.ones((1, 1)))] * 10
    progress = {}
    updates = []
    loss = field_learning.run_epoch(
        model,
        loader,
        torch.device("cpu"),
        torch.optim.SGD(model.parameters(), lr=0.1),
        torch.amp.GradScaler("cpu"),
        deadline=1.75,
        progress=progress,
        progress_callback=updates.append,
    )
    assert np.isfinite(loss) and progress["samples"] == 2
    assert updates == [1]
    assert not torch.equal(before, model.weight)


def test_field_geometry_measures_trained_weights_when_baseline_wins_loss(tmp_path, monkeypatch):
    import torch

    from football_pipeline import field_learning, joint_field
    from football_pipeline.contracts import read_json, write_json

    training, dataset = tmp_path / "training", tmp_path / "data"
    training.mkdir()
    dataset.mkdir()
    write_json(dataset / "index.json", {})
    report = {"status": "complete", "identity": "fixed", "models": {}}
    for role in ("keypoints", "lines"):
        report["models"][role] = {
            "selected_epoch": 0,
            "history": [{"epoch": 1, "valid_loss": 2.0}],
            "path": "baseline",
            "sha256": "baseline",
        }
        torch.save(
            {"identity": "fixed", "epoch": 1, "model": {"weight": torch.tensor([2.0])}},
            training / f"{role}-last.pt",
        )
    write_json(training / "training-report.json", report)
    original = (training / "training-report.json").read_bytes()
    calls = []

    def runtime(baseline, output):
        saved = read_json(output / "training-report.json")
        for record in saved["models"].values():
            assert record["selected_epoch"] == 1
            assert torch.load(record["path"], weights_only=True)["weight"].item() == 2
        write_json(output / "field-runtime.json", {})

    def compare(index, baseline, candidate, output):
        calls.append(candidate)
        write_json(output, {"status": "complete"})

    monkeypatch.setattr(field_learning, "make_runtime", runtime)
    monkeypatch.setattr(joint_field, "compare", compare)
    result = joint_field.compare_trained_checkpoints(dataset, tmp_path / "baseline.json", training)
    joint_field.compare_trained_checkpoints(dataset, tmp_path / "baseline.json", training)
    assert calls == [result / "field-runtime.json"]
    assert (training / "training-report.json").read_bytes() == original
    write_json(training / "training-report.json", {**report, "changed": True})
    with pytest.raises(ValueError, match="changed"):
        joint_field.compare_trained_checkpoints(dataset, tmp_path / "baseline.json", training)


def test_deduplication_preserves_newest_and_blocks_source_frame_split_leaks():
    rows = [
        {"image": "new.png", "image_sha256": "a", "source_frame_rgb_sha256": "pixels", "split": "train"},
        {"image": "old.jpg", "image_sha256": "b", "source_frame_rgb_sha256": "pixels", "split": "train"},
    ]
    kept, excluded = unique_rows(rows)
    assert kept == rows[:1] and excluded[0]["kept"] == "new.png"
    rows[1]["split"] = "val"
    with pytest.raises(ValueError, match="splits"):
        unique_rows(rows)
    with pytest.raises(ValueError, match="splits"):
        check_split_leakage(rows, [])


def test_complete_frame_outranks_older_crop_of_the_same_source():
    crop = {
        "image": "crop.png",
        "image_sha256": "crop",
        "source_frame_rgb_sha256": "same frame",
        "split": "train",
        "crop_xyxy_source": [0, 0, 20, 20],
        "names": ["person", "ball"],
    }
    full = {
        "image": "full.png",
        "image_sha256": "full",
        "source_frame_rgb_sha256": "same frame",
        "split": "train",
        "names": ["player", "referee", "ball"],
    }
    selected, excluded = unique_rows([crop, full])
    assert selected == [full] and excluded[0]["kept"] == "full.png"


def test_role_validation_image_cannot_be_used_for_detector_training():
    with pytest.raises(ValueError, match="splits"):
        check_split_leakage(
            [{"image": "full.jpg", "image_sha256": "same", "split": "train"}],
            [{"image": "copy.jpg", "image_sha256": "same", "split": "val"}],
        )


def test_role_pixel_deduplication_handles_rounding_and_copied_images(tmp_path):
    pixels = np.random.default_rng(42).integers(0, 255, (14, 12, 3), dtype=np.uint8)
    rows = []
    for index in range(2):
        path = tmp_path / f"copy-{index}.png"
        cv2.imwrite(str(path), pixels)
        rows.append(
            {
                "id": str(index),
                "image": str(path),
                "split": "train",
                "role": "player",
                "bbox": [2 + index * 0.01, 2 + index * 0.01, 6 + index * 0.01, 10 + index * 0.01],
            }
        )
    kept, excluded = unique_role_pixels(rows)
    assert len(kept) == 1 and excluded[0]["kept"] == "0"
    rows[1]["split"] = "val"
    with pytest.raises(ValueError, match="cross splits"):
        unique_role_pixels(rows)
    rows[1].update(split="train", role="person")
    with pytest.raises(ValueError, match="conflicting labels"):
        unique_role_pixels(rows)


def test_role_pixel_revision_retains_originals_and_remaining_budget(tmp_path, monkeypatch):
    from football_pipeline import joint_training
    from football_pipeline.contracts import read_json, write_json

    dataset, output = tmp_path / "data", tmp_path / "run"
    (dataset / "roles").mkdir(parents=True)
    (output / "roles").mkdir(parents=True)
    image = tmp_path / "source.png"
    cv2.imwrite(str(image), np.zeros((14, 12, 3), np.uint8))
    manifest = {
        "samples": [
            {"id": str(i), "image": str(image), "bbox": [2, 2, 6, 10], "role": "player", "split": "train"}
            for i in range(2)
        ],
        "excluded": [],
    }
    path = dataset / "roles/manifest.json"
    write_json(path, manifest)
    original = path.read_bytes()
    write_json(
        dataset / "inventory.json", {"counts": {"roles": {"train": 2}}, "fingerprints": {"roles": "original"}}
    )
    write_json(output / "roles/comparison.json", {"training": {"runtime_s": 120}, "promoted": False})
    calls = []

    def refit(data, target, **kwargs):
        calls.append(kwargs)
        assert len(read_json(kwargs["manifest"])["samples"]) == 1
        return {"training": {"runtime_s": 30}, "promoted": False, "baseline": "current", "candidate": "new"}

    monkeypatch.setattr(joint_training, "roles", refit)
    joint_training.refit_role_pixels(dataset, output)
    joint_training.refit_role_pixels(dataset, output)
    assert len(calls) == 1 and calls[0]["minutes"] == 24
    result = read_json(output / "roles/comparison.json")
    assert result["selected"] == "current" and result["training"]["runtime_s"] == 150
    assert path.read_bytes() == original
    assert read_json(dataset / "inventory-final.json")["counts"]["roles"] == {"train": 1}


def test_yolo_label_loader_preserves_person_semantics(tmp_path):
    image, label = tmp_path / "a.png", tmp_path / "a.txt"
    cv2.imwrite(str(image), np.zeros((40, 80, 3), np.uint8))
    label.write_text("0 .5 .5 .5 .5\n1 .25 .25 .1 .1\n")
    width, height, boxes = load_boxes(image, label, {0: "person", 1: "ball"})
    assert (width, height) == (80, 40)
    assert [b["name"] for b in boxes] == ["person", "ball"]
    label.write_text("0 .1 .5 1 1\n")
    with pytest.raises(ValueError, match="outside"):
        load_boxes(image, label, {0: "person"})


def test_candidate_selection_rejects_regressions_and_equal_scores():
    def metric(name, ap=0.5, recall=0.8):
        return {"name": name, "AP50_95": ap, "recall": recall, "precision": 0.9}

    baseline = {"per_class": [metric("player"), metric("referee")]}
    assert not choose_player(baseline, baseline)
    assert choose_player(baseline, {"per_class": [metric("player", 0.6), metric("referee")]})
    assert not choose_player(baseline, {"per_class": [metric("player", 0.6, 0.7), metric("referee")]})
    b = {"macro_f1": 0.7, "per_class": [metric("player")]}
    assert not choose_roles(b, {"macro_f1": 0.8, "per_class": [metric("player", recall=0.7)]})
    ball = {"per_class": [metric("ball")]}
    assert choose_ball(ball, {"per_class": [metric("ball", 0.6)]})
    assert not choose_ball(ball, {"per_class": [{**metric("ball", 0.6), "precision": 0.7}]})
    field = {"valid_frames": 10, "wrong_calibrations": 2, "median_error_px": 3}
    assert not choose_field(field, field)
    assert not choose_field(field, {"valid_frames": 20, "wrong_calibrations": 3, "median_error_px": 2})
    assert choose_field(field, {"valid_frames": 11, "wrong_calibrations": 2, "median_error_px": 3})


def test_bounded_yolo_retries_only_batch_and_preserves_resolution(tmp_path, monkeypatch):
    import torch
    import ultralytics

    calls = []
    weights = tmp_path / "base.pt"
    weights.write_bytes(b"fixed baseline")

    class Model:
        def __init__(self, path):
            assert path == str(weights)

        def add_callback(self, *args):
            pass

        def train(self, **kwargs):
            calls.append(kwargs)
            if kwargs["batch"] > 1:
                raise torch.cuda.OutOfMemoryError("test allocation")
            target = Path(kwargs["project"]) / kwargs["name"]
            (target / "weights").mkdir(parents=True)
            (target / "weights/best.pt").write_bytes(b"candidate")
            (target / "results.csv").write_text("epoch,loss\n1,.1\n")

    monkeypatch.setattr(ultralytics, "YOLO", Model)
    best = train_yolo(
        weights, tmp_path, tmp_path / "output", {"epochs": 3, "imgsz": 1280, "batch": 4, "workers": 0}, 1
    )
    assert best.is_file()
    assert [c["batch"] for c in calls] == [4, 2, 1]
    assert all(c["imgsz"] == 1280 and c["time"] > 0 for c in calls)
    assert weights.read_bytes() == b"fixed baseline"


def test_native_resume_preserves_optimizer_epochs_and_uses_remaining_budget(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import torch
    import ultralytics

    from football_pipeline.contracts import read_json, sha256_file, write_json
    from football_pipeline.training_budget import resume_yolo

    output = tmp_path / "training"
    saved = output / "batch-2"
    (saved / "weights").mkdir(parents=True)
    (saved / "weights/best.pt").write_bytes(b"best")
    (saved / "results.csv").write_text("epoch,loss\n15,.1\n16,.09\n")
    checkpoint = tmp_path / "resume.pt"
    torch.save(
        {
            "epoch": 14,
            "optimizer": {"state": {}},
            "train_args": {"data": str(tmp_path / "data.yaml"), "save_dir": str(saved)},
        },
        checkpoint,
    )
    write_json(output / "status.json", {"status": "running"})
    calls = []

    class Model:
        def __init__(self, path):
            assert path == str(checkpoint)
            self.callbacks = {}

        def add_callback(self, name, callback):
            self.callbacks[name] = callback

        def train(self, **kwargs):
            calls.append(kwargs)
            trainer = SimpleNamespace(
                args=SimpleNamespace(time=55 / 60),
                epochs=49,
                epoch=15,
                scheduler=SimpleNamespace(last_epoch=0),
                _setup_scheduler=lambda: None,
                stopper=SimpleNamespace(best_epoch=15, patience=10),
                stop=True,
            )
            self.callbacks["on_pretrain_routine_start"](trainer)
            assert 0 < trainer.args.time <= 5 / 60
            self.callbacks["on_fit_epoch_end"](trainer)
            assert trainer.epochs == 50 and trainer.args.epochs == 50 and not trainer.stop

    monkeypatch.setattr(ultralytics, "YOLO", Model)
    resume_yolo(
        tmp_path,
        output,
        {
            "resume_checkpoint": str(checkpoint),
            "sha256": sha256_file(checkpoint),
            "last_completed_epoch": 15,
            "remaining_training_minutes": 5,
            "maximum_epochs_total": 50,
            "elapsed_stage_wall_seconds": 100,
        },
    )
    assert calls == [{"resume": True, "device": 0, "workers": 0}]
    assert read_json(output / "status.json")["runtime_s"] >= 100
    checkpoint.write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        resume_yolo(tmp_path, output, {"resume_checkpoint": str(checkpoint), "sha256": "old"})


@pytest.mark.parametrize("identifier", ["../outside", "A" * 64, "a" * 63, "C:\\private"])
def test_result_links_reject_paths_before_opening_files(tmp_path, identifier):
    with pytest.raises(PipelineError, match="analyselink"):
        linked_result(tmp_path, identifier)


def test_app_result_link_opens_without_upload_and_rejects_bad_link(team_run, monkeypatch):
    from streamlit.testing.v1 import AppTest

    result, _ = team_run
    monkeypatch.setenv("FOOTBALL_RUNS", str(result.directory.parent))
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "streamlit_app.py", default_timeout=30)
    app.query_params["run"] = result.directory.name
    app.run()
    assert not app.exception
    assert app.session_state["result"].directory == result.directory
    assert not app.get("file_uploader")
    token = result.manifest["cache_key"][:16]
    app.slider(key=f"team_frame_{token}").set_value(7).run()
    assert {m.label: m.value for m in app.metric}["Totaal"] == "7"
    app.text_input(key=f"team_name_A_{token}").set_value("Thuis")
    next(button for button in app.button if button.label == "Correcties toepassen").click().run()
    assert not app.exception
    corrected = app.session_state["result"]
    assert corrected.directory != result.directory
    assert app.session_state["linked_run"] == corrected.directory.name
    app.run()
    assert app.session_state["result"].directory == corrected.directory
    app.query_params["run"] = "../outside"
    app.run()
    assert not app.exception and app.error


def test_joint_export_check_rejects_mismatched_timestamps(team_run, monkeypatch):
    import json

    from scripts import check_team_integration

    result, _ = team_run
    report = check_team_integration.check_result(result)
    assert report["timestamp_and_fps_checks"] == "passed"
    path = result.directory / "framegegevens.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[1]["timestamp_s"] += 0.1
    path.write_text("\n".join(json.dumps(row) for row in rows))
    monkeypatch.setattr(check_team_integration, "validate_completed", lambda directory: result.manifest)
    with pytest.raises(PipelineError, match="Tijdstempels"):
        check_team_integration.check_result(result)
