import json

import cv2
import numpy as np
import pytest

from football_pipeline.contracts import sha256_file
from scripts.evaluate_fullframe_ball import validation_truth


def test_fullframe_target_mapping_uses_names_and_original_pixels(tmp_path):
    image = tmp_path / "frame.png"
    cv2.imwrite(str(image), np.zeros((10, 20, 3), dtype=np.uint8))
    (tmp_path / "frame.txt").write_text("0 0.5 0.5 0.2 0.4\n1 0.4 0.4 0.1 0.1\n")
    manifest = {
        "names": ["ball", "player"],
        "frames": [
            {
                "frame_id": "f1",
                "group_id": "g1",
                "split": "val",
                "frame_index": 9,
                "image": "frame.png",
                "label": "frame.txt",
                "image_sha256": sha256_file(image),
                "width": 20,
                "height": 10,
            }
        ],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    _, truth, identity = validation_truth(tmp_path)
    assert len(truth["f1"]) == 1
    assert truth["f1"][0] == {"class_id": 0, "bbox_xyxy": [8.0, 3.0, 12.0, 7.0]}
    assert identity["f1"]["image_sha256"] == sha256_file(image)


def test_fullframe_development_evaluation_rejects_test_before_opening_pixels(tmp_path):
    manifest = {
        "names": ["ball"],
        "frames": [
            {"group_id": "g1", "split": "test", "image": "nonexistent.png"},
        ],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="reserved test"):
        validation_truth(tmp_path)
