import numpy as np
import pytest
from PIL import Image

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from scripts.prepare_broadcast_v2 import finalize, player_selection, positive_window, tile


@pytest.mark.parametrize("box", [[1, 1, 5, 5], [795, 795, 800, 800], [350, 150, 365, 175]])
def test_native_window_preserves_the_whole_ball_at_image_edges(box):
    window = positive_window(box, 800, 800, "source", 0)
    assert window[2] - window[0] == window[3] - window[1] == 640
    assert window[0] <= box[0] < box[2] <= window[2]
    assert window[1] <= box[1] < box[3] <= window[3]
    assert window == positive_window(box, 800, 800, "source", 0)


def test_native_window_does_not_silently_resize_small_sources():
    with pytest.raises(ValueError, match="at least 640"):
        positive_window([10, 10, 20, 20], 320, 240, "source", 0)


def test_negative_candidates_require_complete_review_before_a_training_config_is_published(tmp_path):
    prep = {"negative_candidates": [{"candidate_id": 0}, {"candidate_id": 1}]}
    prep["fingerprint"] = digest_json(prep)
    write_json(tmp_path / "preparation.json", prep)
    decisions = tmp_path / "review.json"
    write_json(decisions, {"preparation_fingerprint": prep["fingerprint"],
                          "decisions": [{"candidate_id": 0, "status": "accept", "reason": "No ball visible"}]})
    with pytest.raises(ValueError, match="Every negative candidate"):
        finalize(tmp_path, tmp_path, decisions)
    assert not (tmp_path / "balls/data.yaml").exists()


def test_finalization_preserves_native_pixels_and_deduplicates_clamped_windows(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    output = tmp_path / "prepared"
    positives, negatives = [], []
    for i, split in enumerate(("train", "val")):
        y, x = np.mgrid[:800, :800]
        pixels = np.stack(((x + i * 17) % 251, (y + i * 29) % 249, (x + y + i) % 253), axis=2).astype("uint8")
        path = source / f"parent-{i}.png"
        Image.fromarray(pixels).save(path)
        row = {"frame_id": f"parent-{i}", "game_id": str(i), "split": split, "clip": str(i),
               "image": path.name, "image_sha256": sha256_file(path)}
        positives.append(tile(source, output / "ball-positives", row, [0, 0, 640, 640], "positive", "-p", [20, 20, 30, 30]))
        neg = tile(source, output / "negative-candidates", row, [160, 160, 800, 800], "unreviewed_negative", "-n")
        negatives.append({**neg, "candidate_id": i})
    positives.append({**positives[0], "frame_id": "duplicate-window"})
    prep = {"positive_frames": positives, "negative_candidates": negatives}
    prep["fingerprint"] = digest_json(prep)
    write_json(output / "preparation.json", prep)
    review = tmp_path / "decisions.json"
    write_json(review, {"preparation_fingerprint": prep["fingerprint"], "decisions": [
        {"candidate_id": i, "status": "accept", "reason": "Full native crop inspected; no ball visible"}
        for i in range(2)]})
    (output / "players").mkdir()
    write_json(output / "players/manifest.json", {"frames": []})
    write_json(source / "manifest.json", {"frames": []})
    names = {i: "sports ball" if i == 32 else f"class-{i}" for i in range(80)}
    result = finalize(source, output, review, names)
    assert result["counts"] == {"train": 2, "val": 2}
    assert result["negative_counts"] == {"train": 1, "val": 1}
    assert result["duplicate_windows_excluded"] == ["duplicate-window"]
    assert result["native_pixel_identity_verified"] is True
    coco = read_json(output / "ball-coco/manifest.json")
    assert (output / "ball-coco" / coco["frames"][0]["label"]).read_text().startswith("32 ")


def test_player_selection_thins_training_only_and_keeps_all_validation_frames(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    rows = []
    for i, (split, frame, refs) in enumerate((("train", 0, 0), ("train", 5, 2), ("train", 30, 1), ("val", 5, 0))):
        image, label = f"image-{i}.png", f"label-{i}.txt"
        Image.new("RGB", (640, 640), (i * 20, 100, 70)).save(source / image)
        (source / label).write_text("0 0.5 0.5 0.2 0.2\n2 0.7 0.7 0.01 0.01\n", encoding="utf-8")
        rows.append({"frame_id": str(i), "split": split, "clip": "clip", "game_id": split,
                     "source_frame_index": frame, "width": 640, "height": 640, "image": image, "label": label,
                     "image_sha256": sha256_file(source / image), "label_sha256": sha256_file(source / label),
                     "boxes": [{"class_id": 1, "bbox_xyxy": [10, 10, 30, 40]}] * refs})
    result = player_selection(source, {"frames": rows, "fingerprint": "source"}, tmp_path / "players")
    assert {r["frame_id"] for r in result["frames"] if r["split"] == "train"} == {"1", "2"}
    assert {r["frame_id"] for r in result["frames"] if r["split"] == "val"} == {"3"}
    assert all("role_label" not in r for r in result["frames"])
