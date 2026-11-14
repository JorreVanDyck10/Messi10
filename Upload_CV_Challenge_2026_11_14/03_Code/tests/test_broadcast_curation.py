import json

import pytest
from PIL import Image

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.referee_dataset import clip_split
from persoon1.core import read_labels
from scripts.curate_broadcast_balls import export
from scripts.curate_referee_data import export as export_referees


def candidates(root):
    rows = []
    for index, split in enumerate(("train", "val", "train")):
        image = root / f"frame-{index}.jpg"
        Image.new("RGB", (32, 32), (index * 50, 100, 80)).save(image)
        rows.append(
            {
                "candidate_id": index,
                "frame_id": f"frame-{index}",
                "split": split,
                "game_id": "1" if split == "train" else "2",
                "clip": f"clip-{index}",
                "image": image.name,
                "image_sha256": sha256_file(image),
                "width": 32,
                "height": 32,
                "bbox_xyxy": [1, 1, 3, 3],
            }
        )
    manifest = {"source_fingerprint": "source", "candidates": rows}
    manifest["fingerprint"] = digest_json(manifest)
    return manifest


def decisions(root, manifest, rows):
    path = root / "decisions.json"
    path.write_text(
        json.dumps({"candidate_fingerprint": manifest["fingerprint"], "decisions": rows}), encoding="utf-8"
    )
    return path


def test_curated_export_preserves_source_and_uses_corrected_full_image_coordinates(tmp_path):
    manifest = candidates(tmp_path)
    source_hash = sha256_file(tmp_path / "frame-1.jpg")
    path = decisions(
        tmp_path,
        manifest,
        [
            {"candidate_id": 0, "status": "accept", "reason": "Visible ball enclosed by source box"},
            {
                "candidate_id": 1,
                "status": "correct",
                "reason": "Source box above the ball",
                "corrected_bbox_xyxy": [2, 4, 6, 8],
            },
            {"candidate_id": 2, "status": "reject", "reason": "Occluded ball"},
        ],
    )
    result = export(tmp_path, tmp_path / "out", manifest, path)
    assert result["counts"] == {"train": 1, "val": 1}
    assert result["project_human_review_completed"] is False
    row = next(r for r in result["frames"] if r["split"] == "val")
    label = read_labels(tmp_path / "out/curated" / row["label"], 1)[0]
    assert label == {"class_id": 0, "xywh": [0.125, 0.1875, 0.125, 0.125]}
    assert sha256_file(tmp_path / "frame-1.jpg") == source_hash
    assert not (tmp_path / "out/curated/images/train/frame-2.jpg").exists()


def test_incomplete_ball_review_never_publishes_training_config(tmp_path):
    manifest = candidates(tmp_path)
    path = decisions(tmp_path, manifest, [{"candidate_id": 0, "status": "accept", "reason": "Visible"}])
    with pytest.raises(ValueError, match="Every candidate"):
        export(tmp_path, tmp_path / "out", manifest, path)
    assert not (tmp_path / "out/curated/data.yaml").exists()
    assert not (tmp_path / "out/curated/manifest.json").exists()


def test_changed_review_candidates_and_match_leakage_are_rejected(tmp_path):
    manifest = candidates(tmp_path)
    path = decisions(
        tmp_path, manifest, [{"candidate_id": i, "status": "accept", "reason": "Visible"} for i in range(3)]
    )
    manifest["candidates"][1]["game_id"] = "1"
    with pytest.raises(ValueError, match="fingerprint"):
        export(tmp_path, tmp_path / "out", manifest, path)
    manifest["fingerprint"] = digest_json({k: v for k, v in manifest.items() if k != "fingerprint"})
    data = read_json(path)
    data["candidate_fingerprint"] = manifest["fingerprint"]
    write_json(path, data)
    with pytest.raises(ValueError, match="disjoint"):
        export(tmp_path, tmp_path / "out", manifest, path)


def test_auxiliary_referee_split_keeps_clips_together_and_contains_explicit_negatives():
    rows = [
        {"video_source": str(i), "visibility": visibility}
        for i in range(10)
        for visibility in ("visible", "not_visible")
        for _ in range(10)
    ]
    assignment = clip_split(rows)
    assert set(assignment.values()) == {"train", "val"}
    assert len(assignment) == 10
    assert assignment == clip_split(list(reversed(rows)))
    assert (
        0
        < sum(assignment[r["video_source"]] == "val" and r["visibility"] == "not_visible" for r in rows)
        < 100
    )


def test_referee_quarantine_removes_whole_clip_and_requires_decisions_for_all_clips(tmp_path):
    rows = candidates(tmp_path)["candidates"]
    for i, row in enumerate(rows):
        label = tmp_path / f"label-{i}.txt"
        label.write_text("0 0.5 0.5 0.25 0.25\n", encoding="utf-8")
        row.update(
            label=label.name,
            label_sha256=sha256_file(label),
            source_clip_id=row["clip"],
            visibility="visible",
            box_count=1,
        )
    write_json(
        tmp_path / "manifest.json",
        {
            "source": "provider",
            "source_revision": "pinned",
            "fingerprint": "source",
            "frames": rows,
            "license": "CC-BY-NC-4.0",
            "credit": "Provider",
        },
    )
    path = tmp_path / "clip-decisions.json"
    data = {
        "source_fingerprint": "source",
        "clips": [
            {
                "source_clip_id": r["clip"],
                "status": "quarantine" if i == 2 else "include",
                "reason": "False positive in clip" if i == 2 else "Sample checked",
            }
            for i, r in enumerate(rows)
        ],
    }
    write_json(path, data)
    result = export_referees(tmp_path, path)
    assert len(result["frames"]) == 2 and len(result["quarantine"]) == 1
    assert not (tmp_path / "curated/frame-2.jpg").exists()
    assert result["match_independence_verified"] is False
    data["clips"].pop()
    write_json(path, data)
    with pytest.raises(ValueError, match="Every source clip"):
        export_referees(tmp_path, path)


@pytest.mark.parametrize("box", [[1, 1, 40, 8], [4, 4, 2, 2], [0, 0, float("nan"), 5]])
def test_invalid_ai_corrections_cannot_be_exported(tmp_path, box):
    manifest = candidates(tmp_path)
    path = decisions(
        tmp_path,
        manifest,
        [{"candidate_id": 0, "status": "correct", "corrected_bbox_xyxy": box, "reason": "Correction"}],
    )
    with pytest.raises(ValueError, match="Invalid reviewed"):
        export(tmp_path, tmp_path / "out", manifest, path)
