import gzip
import io
import json
import zipfile
import zlib

import pytest
from PIL import Image

from football_pipeline import broadcast_dataset as module
from football_pipeline.contracts import read_json, sha256_file
from scripts.review_broadcast_data import export_participants


def test_remote_zip_member_requires_matching_name_size_and_crc():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("clip/image.jpg", b"real image bytes" * 100)
    payload = stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        info = archive.getinfo("clip/image.jpg")
    assert module.unpack_member(payload, info) == b"real image bytes" * 100
    info.CRC ^= 1
    with pytest.raises(ValueError, match="CRC"):
        module.unpack_member(payload, info)
    with pytest.raises(ValueError, match="header"):
        module.unpack_member(b"invalid", info)


def clip(name, game, archive="train", count=31):
    images = [
        {
            "image_id": str(i),
            "file_name": f"{i + 1:06d}.jpg",
            "is_labeled": True,
            "has_labeled_person": True,
            "has_labeled_pitch": True,
            "ignore_regions_x": [],
            "ignore_regions_y": [],
        }
        for i in range(count)
    ]
    annotations = [
        {"image_id": str(i), "supercategory": "pitch", "lines": {"Middle line": []}} for i in range(count)
    ]
    return {
        "info": {"name": name},
        "game_id": game,
        "archive_split": archive,
        "data": {"images": images, "annotations": annotations},
    }


def test_sampling_requires_annotations_and_excludes_ignored_images():
    data = clip("SNGS-001", "1")["data"]
    data["images"][0]["ignore_regions_x"] = [[0, 1]]
    data["images"][1]["has_labeled_pitch"] = False
    selected = module.eligible_images(data)
    indices = [int(im["image_id"]) for im, _ in selected]
    assert indices[0] == 2
    assert all(b - a >= 5 for a, b in zip(indices, indices[1:]))


def test_selection_keeps_validation_games_out_of_training_and_samples_all_clips():
    clips = [
        clip("SNGS-001", "1"),
        clip("SNGS-002", "1"),
        clip("SNGS-003", "2"),
        clip("SNGS-004", "2", "valid"),
    ]
    games = {"train": ["1"], "val": ["2"]}
    train = module.choose_frames(clips, games, "train", 10)
    valid = module.choose_frames(clips, games, "val", 4)
    assert {s["clip"]["game_id"] for s in train} == {"1"}
    assert {s["clip"]["archive_split"] for s in valid} == {"valid"}
    assert len({(s["clip"]["info"]["name"], s["image"]["image_id"]) for s in train}) == 10
    assert {s["clip"]["info"]["name"] for s in train} == {"SNGS-001", "SNGS-002"}
    with pytest.raises(ValueError, match="Not enough"):
        module.choose_frames(clips, games, "train", 100)


def test_selection_can_read_cached_annotations_without_retaining_full_clips(tmp_path):
    cached = clip("SNGS-001", "1")
    path = tmp_path / "annotations.json.gz"
    path.write_bytes(gzip.compress(json.dumps(cached.pop("data")).encode()))
    cached["annotation_path"] = str(path)
    selected = module.choose_frames([cached], {"train": ["1"]}, "train", 4)
    assert len(selected) == 4
    assert "data" not in cached


def test_failed_collection_releases_its_lock_but_does_not_remove_another_writers_lock(tmp_path, monkeypatch):
    def fail(*args):
        raise ValueError("download failed")

    monkeypatch.setattr(module, "_prepare", fail)
    with pytest.raises(ValueError, match="download failed"):
        module.prepare(tmp_path, 1, 1)
    lock = tmp_path / ".writer.lock"
    assert not lock.exists()
    lock.write_text("other writer", encoding="utf-8")
    with pytest.raises(FileExistsError):
        module.prepare(tmp_path, 1, 1)
    assert lock.read_text(encoding="utf-8") == "other writer"


def test_real_image_export_preserves_roles_and_attributes_and_audit_detects_tampering(tmp_path):
    stream = io.BytesIO()
    Image.new("RGB", (100, 100), "green").save(stream, "JPEG")
    pixels = stream.getvalue()
    member = "SNGS-001/img1/000001.jpg"
    info = zipfile.ZipInfo(member)
    info.file_size, info.CRC = len(pixels), zlib.crc32(pixels) & 0xFFFFFFFF

    class Archive:
        members = {member: info}

        def read(self, name):
            assert name == member
            return pixels

    for folder in (
        "images/train",
        "labels/train",
        "roles/images/train",
        "roles/labels/train",
        "field/train",
        "attributes/train",
        "provider-labels",
    ):
        (tmp_path / folder).mkdir(parents=True, exist_ok=True)
    original = tmp_path / "provider-labels/SNGS-001.json.gz"
    original.write_bytes(b"immutable provider evidence")
    annotations = [
        {
            "supercategory": "object",
            "category_id": 2,
            "bbox_image": {"x": -5, "y": 10, "w": 15, "h": 40},
            "attributes": {"role": "goalkeeper", "team": "left", "jersey": "1"},
            "track_id": 13,
        },
        {"supercategory": "object", "category_id": 4, "bbox_image": {"x": 60, "y": 60, "w": 4, "h": 4}},
        {"supercategory": "object", "category_id": 7, "bbox_image": {"x": 120, "y": 10, "w": 10, "h": 20}},
        {"supercategory": "pitch", "lines": {"Middle line": [{"x": 0.5, "y": 0}, {"x": 0.5, "y": 1}]}},
    ]
    selected = {
        "clip": {
            "info": {"name": "SNGS-001"},
            "archive_split": "train",
            "game_id": "4",
            "annotation_sha256": sha256_file(original),
        },
        "image": {"file_name": "000001.jpg", "image_id": "1", "width": 100, "height": 100},
        "annotations": annotations,
        "split": "train",
    }
    row = module.prepare_frame(tmp_path, {"train": Archive()}, selected)
    assert row["clipped_boxes"] == row["dropped_boxes"] == 1
    assert [box["class_id"] for box in row["boxes"]] == [0, 2]
    assert (tmp_path / row["role_label"]).read_text().splitlines()[0].startswith("1 ")
    assert read_json(tmp_path / row["attributes"])["annotations"][0]["track_id"] == 13
    report = module.audit(tmp_path, {"frames": [row]})
    assert report["fully_decoded_images"] == 1
    assert report["role_counts"]["train"] == {"goalkeeper": 1, "ball": 1}
    export_participants(tmp_path, {"frames": [row], "fingerprint": "verified-source"})
    assert (
        (tmp_path / "players/labels/train/SNGS-001_000001.txt").read_text().splitlines()[0].startswith("0 ")
    )
    participant_labels = (tmp_path / "participants/labels/train/SNGS-001_000001.txt").read_text().splitlines()
    assert len(participant_labels) == 1
    assert participant_labels[0].startswith("1 ")  # Keep the goalkeeper role; exclude the ball task.
    (tmp_path / row["label"]).write_text("0 0.5 0.5 1 1\n")
    with pytest.raises(ValueError, match="checksum"):
        module.audit(tmp_path, {"frames": [row]})
