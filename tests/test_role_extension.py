import json

import cv2
import numpy as np
import pytest

from football_pipeline.appearance import ROLE_NAMES, TEAM_NAMES
from football_pipeline.contracts import sha256_file
from persoon1 import role_training


def extension(tmp_path, monkeypatch):
    monkeypatch.setattr(role_training, "ROOT", tmp_path)
    rows = []
    for i, split in enumerate(("train", "val")):
        image = tmp_path / f"{split}.jpg"
        assert cv2.imwrite(str(image), np.full((20, 20, 3), i * 70, np.uint8))
        rows.append(
            {
                "id": split,
                "image": image.name,
                "image_sha256": sha256_file(image),
                "split": split,
                "group": split,
                "bbox": [1, 1, 19, 19],
                "role": "player",
                "team": None,
            }
        )
    manifest = {
        "review_policy": "provisional_ai_visual",
        "human_review_completed": False,
        "role_names": ROLE_NAMES,
        "team_names": TEAM_NAMES,
        "samples": rows,
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, manifest


def test_extension_loads_without_mutating_existing_labels(tmp_path, monkeypatch):
    path, manifest = extension(tmp_path, monkeypatch)
    before = path.read_bytes()
    assert role_training.load_training_manifest(path) == manifest
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "damage,message",
    [
        ("test", "reserved test"),
        ("group", "crosses"),
        ("hash", "identity"),
        ("box", "outside"),
        ("team", "verified player"),
    ],
)
def test_extension_rejects_bad_data_before_training(tmp_path, monkeypatch, damage, message):
    path, data = extension(tmp_path, monkeypatch)
    row = data["samples"][1]
    if damage == "test":
        row["split"] = "test"
    elif damage == "group":
        row["group"] = "train"
    elif damage == "hash":
        row["image_sha256"] = "0" * 64
    elif damage == "box":
        row["bbox"][2] = 21
    else:
        row.update(role="referee", team="team_a")
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        role_training.load_training_manifest(path)


def test_role_only_match_never_inherits_an_untrained_supervised_team_head():
    rows = [
        {"video_sha256": "new_role_only", "team": None},
        {"video_sha256": "verified_addition", "team": "team_a"},
    ]
    base = {"frames": [{"video_id": "known_source_match"}]}
    assert role_training.supervised_team_videos(rows, base) == ["known_source_match", "verified_addition"]
