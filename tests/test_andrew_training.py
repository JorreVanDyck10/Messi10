from pathlib import Path
from types import SimpleNamespace

import pytest

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.training_transfer import export_models, import_bundle
from football_pipeline.training_worker import train_andrew, yolo_data


def profile_at(root):
    weights = root / "weights/original.pt"
    weights.parent.mkdir(parents=True, exist_ok=True)
    weights.write_bytes(b"original detector")
    profile = root / "configs/models-andrew.json"
    profile.parent.mkdir(parents=True, exist_ok=True)
    write_json(
        profile,
        {
            "schema_version": 1,
            "models": [
                {
                    "model_id": "andrew",
                    "weights": "../weights/original.pt",
                    "weights_sha256": sha256_file(weights),
                    "class_mapping": {"0": "ball", "1": "player", "2": "player", "3": "referee"},
                    "expected_names": {"0": "ball", "1": "goalkeeper", "2": "player", "3": "referee"},
                    "imgsz": 1280,
                    "confidence": 0.03,
                    "iou": 0.5,
                    "device": "0",
                }
            ],
        },
    )
    dataset = root / "data/andrew"
    for split in ("train", "val"):
        (dataset / split).mkdir(parents=True)
    (dataset / "data.yaml").write_text("train: train\nval: val\nnames: [ball, goalkeeper, player, referee]\n")
    return {"andrew_profile": str(profile), "andrew_dataset": str(dataset)}


def test_four_class_training_preserves_classes_and_separate_profile(tmp_path, monkeypatch):
    import ultralytics

    from football_pipeline import training_budget

    inputs = profile_at(tmp_path)
    original_hash = sha256_file(inputs["andrew_profile"])
    calls = []
    monkeypatch.setattr(
        ultralytics,
        "YOLO",
        lambda path: SimpleNamespace(names={0: "ball", 1: "goalkeeper", 2: "player", 3: "referee"}),
    )

    def train(initial, dataset, output, config, minutes):
        calls.append((initial, read_json(Path(inputs["andrew_profile"])), config, minutes))
        output.mkdir()
        target = output / "best.pt"
        target.write_bytes(b"new four-class detector")
        return target

    monkeypatch.setattr(training_budget, "train_yolo", train)
    directory = tmp_path / "round/andrew"
    directory.mkdir(parents=True)
    candidate = train_andrew(inputs, directory, epochs=2, minutes=4)
    trained = read_json(candidate)
    assert trained["models"][0]["class_mapping"] == {
        "0": "ball",
        "1": "player",
        "2": "player",
        "3": "referee",
    }
    assert trained["models"][0]["expected_names"]["1"] == "goalkeeper"
    assert calls[0][2]["imgsz"] == 1280 and calls[0][2]["batch"] == 1
    assert calls[0][2]["epochs"] == 2 and calls[0][3] == 4
    assert sha256_file(inputs["andrew_profile"]) == original_hash
    assert not (directory.parent / "candidate-profile.json").exists()


def test_augmented_source_frame_cannot_leak_across_training_splits(tmp_path):
    inputs = profile_at(tmp_path)
    source = Path(inputs["andrew_dataset"])
    write_json(
        source / "manifest.json",
        {
            "frames": [
                {"split": "train", "source_frame_group": "frame-1", "image_sha256": "a"},
                {"split": "val", "source_frame_group": "frame-1", "image_sha256": "b"},
            ]
        },
    )
    with pytest.raises(ValueError, match="beide trainingssplits"):
        yolo_data(source, tmp_path / "blocked")


def test_andrew_model_package_imports_without_replacing_other_candidates(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    inputs = profile_at(source)
    job = source / "artifacts/training-workbench/round1"
    (job / "andrew").mkdir(parents=True)
    original = read_json(inputs["andrew_profile"])
    original["models"][0]["weights"] = str(source / "weights/original.pt")
    profile = job / "andrew/candidate-profile.json"
    write_json(profile, original)
    write_json(job / "andrew/result.json", {"weights": str(profile)})
    write_json(job / "job.json", {"status": "complete", "completed": ["andrew"]})
    write_json(job / "spec.json", {"inputs": {}})
    package = tmp_path / "andrew.zip"
    manifest = export_models(package, job, source)
    assert set(manifest["profiles"]) == {"andrew"}
    target = tmp_path / "other-laptop"
    (target / "configs").mkdir(parents=True)
    existing = target / "configs/models-shared-candidate.json"
    existing.write_text('{"existing": true}')
    before = existing.read_bytes()
    import_bundle(package, target)
    imported = read_json(next((target / "configs").glob("models-andrew-imported-*.json")))
    assert Path(imported["models"][0]["weights"]).is_relative_to(target)
    assert existing.read_bytes() == before
    assert imported["models"][0]["class_mapping"]["0"] == "ball"


def test_training_package_includes_original_andrew_images_on_another_laptop(tmp_path):
    import torch

    from football_pipeline.training_transfer import export_bundle

    source = tmp_path / "source"
    source.mkdir()
    inputs = profile_at(source)
    dataset = Path(inputs["andrew_dataset"])
    frames = []
    for split in ("train", "val"):
        image = source / f"Andrew_Prototype/archive/{split}/images/frame.jpg"
        label = source / f"Andrew_Prototype/archive/{split}/labels/frame.txt"
        image.parent.mkdir(parents=True)
        label.parent.mkdir(parents=True)
        image.write_bytes(f"{split} image payload".encode())
        label.write_text("2 0.5 0.5 0.1 0.2")
        frames.append(
            {
                "split": split,
                "source_frame_group": split,
                "image": "../../" + image.relative_to(source).as_posix(),
                "label": "../../" + label.relative_to(source).as_posix(),
                "image_sha256": sha256_file(image),
                "label_sha256": sha256_file(label),
            }
        )
    write_json(dataset / "manifest.json", {"frames": frames})
    (dataset / "data.yaml").write_text(
        "path: ../../Andrew_Prototype/archive\ntrain: train/images\nval: val/images\nnames: [ball, goalkeeper, player, referee]\n"
    )
    features = source / "weights/features.pt"
    torch.save({"rows": []}, features)
    field = dataset / "field.json"
    write_json(field, {"frames": []})
    inputs.update(
        profile=inputs["andrew_profile"],
        players=str(dataset),
        ball=str(dataset),
        appearance=str(features),
        field=str(field),
        context_dataset=str(dataset),
    )
    package = tmp_path / "data.zip"
    manifest = export_bundle(package, inputs, source)
    assert "Andrew_Prototype/archive/train/images/frame.jpg" in manifest["files"]
    target = tmp_path / "another-laptop"
    target.mkdir()
    import_bundle(package, target)
    rebound = yolo_data(target / "data/andrew", target / "bound")
    assert rebound["path"] == str(target / "Andrew_Prototype/archive")
    assert rebound["names"] == ["ball", "goalkeeper", "player", "referee"]
