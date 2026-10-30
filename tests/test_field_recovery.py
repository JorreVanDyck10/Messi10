from copy import deepcopy

import pytest

from football_pipeline.contracts import digest_json, sha256_file, write_json
from football_pipeline.field_learning import load_training_index
from football_pipeline.field_recovery import development_gate, diverse_rows


def test_recovery_index_rejects_changed_labels_and_match_leakage(tmp_path):
    frames = []
    for split in ("train", "valid"):
        image, label = tmp_path / f"{split}.jpg", tmp_path / f"{split}.json"
        image.write_bytes(split.encode())
        write_json(label, {"Middle line": [{"x": 0.2, "y": 0.1}, {"x": 0.3, "y": 0.8}]})
        frames.append(
            {
                "image": str(image),
                "label": str(label),
                "split": split,
                "image_sha256": sha256_file(image),
                "label_sha256": sha256_file(label),
                "match_id": split,
            }
        )
    target = tmp_path / "index.json"
    write_json(target, {"frames": frames, "fingerprint": digest_json(frames)})
    assert load_training_index(target)["frames"] == frames
    frames[-1]["match_id"] = "train"
    write_json(target, {"frames": frames, "fingerprint": digest_json(frames)})
    with pytest.raises(ValueError, match="crosses"):
        load_training_index(target)
    frames[-1]["match_id"] = "valid"
    write_json(target, {"frames": frames, "fingerprint": digest_json(frames)})
    (tmp_path / "valid.json").write_text("{}")
    with pytest.raises(ValueError, match="changed"):
        load_training_index(target)


def test_development_gate_requires_correct_coverage_and_both_error_controls():
    base = {
        "frames": 10,
        "correct": 6,
        "wrong": 2,
        "unscored_available": 0,
        "median_line_error_px": 3.0,
        "p95_line_error_px": 8.0,
    }
    improved = {**base, "correct": 7}
    assert development_gate(base, improved)
    assert not development_gate(base, {**base, "available": 10})
    for key, value in (
        ("wrong", 3),
        ("median_line_error_px", 4.0),
        ("p95_line_error_px", 9.0),
        ("p95_line_error_px", None),
        ("unscored_available", 1),
    ):
        assert not development_gate(base, {**improved, key: value})
    assert not development_gate({**base, "p95_line_error_px": None}, improved)


def test_diverse_selection_is_order_independent_and_keeps_matches_balanced():
    rows = [{"match_id": str(m), "image_sha256": f"{m}:{i}"} for m in range(3) for i in range(4)]
    selected = diverse_rows(rows, 6)
    assert selected == diverse_rows(list(reversed(deepcopy(rows))), 6)
    assert [sum(r["match_id"] == str(m) for r in selected) for m in range(3)] == [2, 2, 2]
