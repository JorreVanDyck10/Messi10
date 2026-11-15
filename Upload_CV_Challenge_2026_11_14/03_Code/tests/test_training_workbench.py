import json
import time
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from football_pipeline.contracts import PipelineError, read_json, write_json
from football_pipeline.training_transfer import import_bundle, rebase
from football_pipeline.training_workbench import check_inputs, jobs, launch, stop_after_model


def inputs_at(root):
    (root / "configs").mkdir()
    write_json(root / "configs/models.json", {})
    (root / "data/players").mkdir(parents=True)
    (root / "data/players/data.yaml").write_text("names: [player]")
    return {"profile": "configs/models.json", "players": "data/players"}


def test_local_job_uses_argument_list_and_survives_ui_restarts(tmp_path, monkeypatch):
    from football_pipeline import training_workbench as workbench

    inputs = inputs_at(tmp_path)
    calls = []
    monkeypatch.setattr(workbench, "training_processes", lambda: [])
    monkeypatch.setattr(
        workbench.subprocess,
        "Popen",
        lambda command, **kwargs: calls.append((command, kwargs)) or SimpleNamespace(pid=123),
    )
    monkeypatch.setattr(
        workbench.psutil,
        "Process",
        lambda pid: SimpleNamespace(create_time=lambda: 100.0, is_running=lambda: True),
    )
    directory = launch(["players"], inputs, epochs=2, minutes=1, root=tmp_path)
    assert calls[0][0][1:4] == ["-u", "-m", "football_pipeline.training_worker"]
    assert not calls[0][1].get("shell")
    assert read_json(directory / "spec.json")["automatic_activation"] is False
    assert jobs(tmp_path)[0][1]["pid"] == 123
    with pytest.raises(PipelineError, match="al een training"):
        launch(["players"], inputs, root=tmp_path)
    stop_after_model(directory, tmp_path)
    assert (directory / "stop-after-model.json").exists()
    with pytest.raises(PipelineError):
        stop_after_model(tmp_path.parent, tmp_path)


def test_missing_inputs_unknown_models_and_reused_pid_cannot_start(tmp_path, monkeypatch):
    from football_pipeline import training_workbench as workbench

    assert check_inputs(["players"], {}, tmp_path)
    with pytest.raises(PipelineError, match="Onbekend"):
        check_inputs(["arbitrary command"], {}, tmp_path)
    directory = tmp_path / "artifacts/training-workbench/old"
    directory.mkdir(parents=True)
    write_json(
        directory / "job.json",
        {"status": "running", "created_at": time.time() - 60, "pid": 9, "process_created_at": 100},
    )
    monkeypatch.setattr(
        workbench.psutil,
        "Process",
        lambda pid: SimpleNamespace(create_time=lambda: 200.0, is_running=lambda: True),
    )
    assert jobs(tmp_path)[0][1]["status"] == "interrupted"


def test_windows_paths_rebind_under_another_checkout_without_basename_guessing(tmp_path):
    value = {"image": "C:\\Messi10\\data\\train\\one.jpg", "outside": "C:\\Other\\one.jpg"}
    result = rebase(value, "C:\\Messi10", tmp_path)
    assert result["image"] == str(tmp_path / "data/train/one.jpg")
    assert result["outside"] == value["outside"]
    with pytest.raises(PipelineError):
        rebase("C:/Messi10/../secret", "C:/Messi10", tmp_path)


@pytest.mark.parametrize("name", ["../evil.txt", "data/../../evil.txt", "data/evil.py", "C:/evil.txt"])
def test_import_rejects_unsafe_members_before_writing(tmp_path, name):
    path = tmp_path / "bad.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "training-transfer.json", json.dumps({"schema_version": 1, "files": {name: "0" * 64}})
        )
        archive.writestr("payload/" + name, "invalid")
    with pytest.raises(PipelineError):
        import_bundle(path, tmp_path)


def test_transfer_verifies_hashes_and_preserves_different_existing_files(tmp_path):
    import hashlib

    path = tmp_path / "good.zip"
    payload = b"original labels"
    manifest = {
        "schema_version": 1,
        "files": {"data/labels.txt": hashlib.sha256(payload).hexdigest()},
        "source_root": "C:/Messi10",
        "inputs": {"players": "data/players"},
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("training-transfer.json", json.dumps(manifest))
        archive.writestr("payload/data/labels.txt", payload)
    assert import_bundle(path, tmp_path) == 1
    assert (tmp_path / "data/labels.txt").read_bytes() == payload
    assert import_bundle(path, tmp_path) == 1
    (tmp_path / "data/labels.txt").write_text("local edit")
    with pytest.raises(PipelineError, match="verschilt"):
        import_bundle(path, tmp_path)
    assert (tmp_path / "data/labels.txt").read_text() == "local edit"


def test_training_page_only_starts_on_explicit_submit(monkeypatch, tmp_path):
    from streamlit.testing.v1 import AppTest

    from football_pipeline import training_ui

    calls = []
    monkeypatch.setattr(training_ui, "training_processes", lambda: [])
    monkeypatch.setattr(training_ui, "jobs", lambda: [])
    monkeypatch.setattr(
        training_ui,
        "hardware_snapshot",
        lambda: {"ready": True, "gpus": [{"name": "GPU fixture", "memory_gib": 8}]},
    )
    monkeypatch.setattr(
        training_ui,
        "launch",
        lambda tasks, inputs, **kwargs: calls.append((tasks, kwargs)) or Path("fixture-job"),
    )
    app = AppTest.from_string("from football_pipeline.training_ui import training_page\ntraining_page()")
    app.run(timeout=30)
    assert not app.exception and not calls
    next(b for b in app.button if b.label == "Controleer deze GPU").click().run()
    next(b for b in app.button if b.label == "Train spelers").click().run()
    assert calls[0][0] == ["players"]
    app.run()
    assert len(calls) == 1
    next(b for b in app.button if b.label == "Alles trainen").click().run()
    assert set(calls[-1][0]) == set(training_ui.TASKS)
    assert not app.exception


def test_blackwell_with_old_cuda_is_rejected_before_training(monkeypatch):
    import torch

    from football_pipeline.training_hardware import probe

    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 1)
    monkeypatch.setattr(torch.cuda, "get_device_capability", lambda index: (12, 0))
    monkeypatch.setattr(
        torch.cuda,
        "get_device_properties",
        lambda index: SimpleNamespace(name="RTX 5070 fixture", total_memory=8 * 1024**3),
    )
    monkeypatch.setattr(torch.version, "cuda", "12.1")
    assert not probe()["ready"]
    assert "CUDA 12.8" in probe()["error"]


def test_yolo_relocation_and_reserved_source_guard(tmp_path, monkeypatch):
    from football_pipeline import training_worker

    source = tmp_path / "dataset"
    (source / "images/train").mkdir(parents=True)
    (source / "images/val").mkdir(parents=True)
    (source / "data.yaml").write_text(
        "path: C:/Messi10/dataset\ntrain: images/train\nval: images/val\nnames: [player]\n"
    )
    monkeypatch.setattr(training_worker, "ROOT", tmp_path)
    monkeypatch.setattr(training_worker, "imported_source_root", lambda: "C:/Messi10")
    assert training_worker.yolo_data(source, tmp_path / "bound")["path"] == str(source)
    write_json(source / "manifest.json", {"frames": [{"split": "test"}]})
    with pytest.raises(ValueError, match="Testbeelden"):
        training_worker.yolo_data(source, tmp_path / "blocked")


def test_context_head_really_trains_on_selected_gpu(tmp_path):
    import numpy as np
    import torch

    from football_pipeline.broadcast_observed_context import train
    from football_pipeline.contracts import sha256_file

    if not torch.cuda.is_available():
        pytest.skip("Actual GPU smoke test; CPU CI still exercises the scheduling and portability guards")
    cache = tmp_path / "cache"
    cache.mkdir()
    write_json(cache / "inputs.json", {"identity": "gpu-smoke"})
    torch.save({"teacher_sha256": "a" * 64, "kit_weights_sha256": "b" * 64}, cache / "projection.pt")
    files = {}
    rng = np.random.default_rng(42)
    for split in ("train", "val"):
        target = cache / f"{split}.npz"
        np.savez(
            target,
            identity="gpu-smoke",
            split=split,
            x=rng.normal(size=(16, 46)).astype("float32"),
            y=np.array([0, 1] * 8),
        )
        files[target.name] = sha256_file(target)
    write_json(
        cache / "complete.json",
        {"identity": "gpu-smoke", "files": files, "projection_sha256": sha256_file(cache / "projection.pt")},
    )
    output = tmp_path / "trained"
    weights = train(cache, output, epochs=2, device="cuda:0", minutes=1)
    assert weights.exists()
    assert read_json(output / "metrics.json")["device"] == "cuda:0"
    state = torch.load(weights, map_location="cpu", weights_only=True)
    assert state["teacher_sha256"] == "a" * 64


def test_model_package_rebinds_profiles_without_changing_dataset_import(tmp_path, monkeypatch):
    from football_pipeline import detection
    from football_pipeline.contracts import sha256_file
    from football_pipeline.training_transfer import export_models

    source, target = tmp_path / "source", tmp_path / "another-laptop"
    job = source / "artifacts/training-workbench/round1"
    weights = job / "players/training/best.pt"
    weights.parent.mkdir(parents=True)
    weights.write_bytes(b"model bytes")
    write_json(job / "job.json", {"status": "complete", "completed": ["players"]})
    write_json(job / "spec.json", {"inputs": {}})
    write_json(job / "players/result.json", {"weights": str(weights)})
    write_json(
        job / "candidate-profile.json",
        {
            "models": [
                {
                    "weights": str(weights),
                    "weights_sha256": sha256_file(weights),
                    "class_mapping": {"0": "player"},
                }
            ]
        },
    )
    bundle = tmp_path / "models.zip"
    export_models(bundle, job, source)
    (target / ".cache").mkdir(parents=True)
    (target / "configs").mkdir()
    write_json(
        target / "configs/models-broadcast.json",
        {
            "models": [
                {"class_mapping": {"0": "player"}, "model_id": "old-player"},
                {"class_mapping": {"0": "person"}, "model_id": "person-proposal"},
            ]
        },
    )
    write_json(target / ".cache/training-import.json", {"source_root": "original-dataset-source"})
    monkeypatch.setattr(detection, "load_model_manifest", lambda path: read_json(path))
    import_bundle(bundle, target)
    rebound = read_json(next((target / "configs").glob("models-imported-*.json")))
    assert rebound["models"][0]["weights"].startswith(str(target))
    shared = read_json(target / "configs/models-shared-candidate.json")
    assert shared["models"][0]["weights"].startswith(str(target))
    assert shared["models"][1]["model_id"] == "person-proposal"
    assert read_json(target / ".cache/training-import.json")["source_root"] == "original-dataset-source"
