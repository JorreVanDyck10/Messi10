import pytest

from football_pipeline import broadcast_multisource_training as training
from football_pipeline.contracts import sha256_file, write_json
from football_pipeline.sportsmot_data import ARCHIVE_SHA256, REVISION


def dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(training, "ROOT", tmp_path)
    root = tmp_path / "mixed"
    root.mkdir()
    image, label = root / "image.jpg", root / "label.txt"
    image.write_bytes(b"frozen fixture")
    label.write_text("0 0.5 0.5 0.1 0.2\n")
    row = {"frame_id": "validation", "split": "val", "provider": "soccernet", "game_id": "2",
           "image": str(image), "image_sha256": sha256_file(image),
           "label": str(label), "label_sha256": sha256_file(label)}
    original = tmp_path / "data/broadcast-pitch-v1"
    original.mkdir(parents=True)
    write_json(original / "manifest.json", {"fingerprint": "frozen", "frames": [row]})
    sport_image = root / "sports.jpg"
    sport_image.write_bytes(b"separate official training image")
    manifest = {"names": {0: "player"}, "test_accessed": False,
                "selection": {"revision": REVISION, "archive_sha256": ARCHIVE_SHA256,
                              "split": "train", "test_accessed": False, "sequences": ["football"]},
                "source_fingerprints": {"soccernet": "frozen"}, "frames": [row,
                    {**row, "frame_id": "sports", "provider": "sportsmot", "split": "train",
                     "clip": "football", "game_id": "sportsmot:new-game", "image": str(sport_image),
                     "image_sha256": sha256_file(sport_image)}]}
    write_json(root / "manifest.json", manifest)
    return root, manifest


def test_mixed_training_keeps_original_validation_and_verifies_new_image_bytes(tmp_path, monkeypatch):
    root, manifest = dataset(tmp_path, monkeypatch)
    _, games = training.validate_dataset(root)
    assert games == {"sportsmot:new-game": 1}
    (root / "sports.jpg").write_bytes(b"changed")
    with pytest.raises(ValueError, match="image or target changed"):
        training.validate_dataset(root)


def test_reserved_sports_split_is_rejected_before_reading_its_image(tmp_path, monkeypatch):
    root, manifest = dataset(tmp_path, monkeypatch)
    manifest["frames"][1].update(split="test", image="must-not-open.jpg")
    write_json(root / "manifest.json", manifest)
    with pytest.raises(ValueError, match="Reserved or unknown"):
        training.validate_dataset(root)


def test_mixed_training_cannot_drop_hard_validation_frames(tmp_path, monkeypatch):
    root, manifest = dataset(tmp_path, monkeypatch)
    manifest["frames"] = manifest["frames"][1:]
    write_json(root / "manifest.json", manifest)
    with pytest.raises(ValueError, match="complete validation selection"):
        training.validate_dataset(root)
