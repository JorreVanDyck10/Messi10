from types import SimpleNamespace

import numpy as np
import pytest

from football_pipeline.ball_tiles import (
    axis_starts,
    merge_ball_predictions,
    predict_ball_tiles,
    tile_windows,
    validate_ball_tile_config,
)


def test_tiles_cover_every_pixel_including_small_and_last_edge():
    for width, height in [(4096, 1080), (99, 77), (1280, 1280), (1281, 1290)]:
        covered = np.zeros((height, width), dtype=bool)
        for x, y, right, bottom in tile_windows(width, height, 640):
            assert 0 <= x < right <= width and 0 <= y < bottom <= height
            covered[y:bottom, x:right] = True
        assert covered.all()
    with pytest.raises(ValueError):
        axis_starts(100, 640, float("nan"))


def test_global_nms_removes_overlap_duplicates_but_preserves_nearby_balls():
    predictions = [
        {"class_id": 0, "bbox_xyxy": [10, 10, 20, 20], "confidence": 0.8},
        {"class_id": 0, "bbox_xyxy": [10.1, 10.1, 20.1, 20.1], "confidence": 0.7},
        {"class_id": 0, "bbox_xyxy": [21, 10, 31, 20], "confidence": 0.6},
    ]
    assert merge_ball_predictions(predictions) == [predictions[0], predictions[2]]


def test_tiled_detector_maps_both_axes_to_original_pixels():
    class Tensor:
        def cpu(self):
            return self

        def tolist(self):
            return [10, 20, 15, 25]

    class Model:
        names = {32: "sports ball"}

        def predict(self, pixels, **kwargs):
            return [
                SimpleNamespace(
                    orig_shape=pixels.shape[:2],
                    boxes=[SimpleNamespace(xyxy=[Tensor()], conf=[0.8])],
                )
            ]

    frame = np.zeros((1000, 1400, 3), dtype=np.uint8)
    predictions = predict_ball_tiles(Model(), frame, size=640)
    assert any(b["bbox_xyxy"] == [770, 380, 775, 385] for b in predictions)
    assert all(b["source_class_id"] == 32 for b in predictions)


def test_training_tiles_cannot_turn_a_cut_ball_into_background():
    from scripts.train_fullscene_ball import tile_ball_labels

    objects = [{"class_id": 1, "xyxy": [630, 30, 650, 50]}]
    assert tile_ball_labels(objects, (0, 0, 640, 640)) is None
    complete = tile_ball_labels(objects, (512, 0, 1152, 640))
    assert len(complete) == 1 and complete[0][0] == 32
    assert complete[0][3:] == [20 / 640, 20 / 640]
    assert tile_ball_labels(objects, (1000, 0, 1640, 640)) == []


def test_training_rejects_test_before_opening_images(tmp_path):
    import json

    from scripts.train_fullscene_ball import build_dataset

    source = tmp_path / "source"
    source.mkdir()
    (source / "source-annotations.json").write_text(json.dumps({"frames": []}))
    (source / "manifest.json").write_text(
        json.dumps(
            {
                "names": ["player", "ball"],
                "frames": [{"split": "test", "group_id": "g1"}],
            }
        )
    )
    with pytest.raises(ValueError, match="Reserved test"):
        build_dataset(source, tmp_path / "derived", {32: "sports ball"})
    assert not (tmp_path / "derived").exists()


@pytest.mark.parametrize("sizes", [[1280, 1280], [True], [], [64], [5000], [640, 800, 1000, 1280]])
def test_manifest_rejects_unbounded_or_ambiguous_tile_work(sizes):
    with pytest.raises(ValueError):
        validate_ball_tile_config({"sizes": sizes, "imgsz": 1280, "overlap": 0.2, "merge_iou": 0.5})


def test_runtime_routes_ball_tiles_without_changing_person_path(monkeypatch):
    from football_pipeline import ball_tiles
    from football_pipeline.detection import UltralyticsDetector

    detector = UltralyticsDetector.__new__(UltralyticsDetector)
    detector.appearance = None
    detector.models = [
        (
            {
                "model_id": "ball",
                "class_mapping": {"32": "ball"},
                "confidence": 0.25,
                "iou": 0.7,
                "device": "cpu",
                "ball_tiles": {"sizes": [1280], "imgsz": 1280, "overlap": 0.2, "merge_iou": 0.5},
            },
            object(),
        )
    ]
    monkeypatch.setattr(
        ball_tiles,
        "predict_multiscale_ball",
        lambda *a, **k: [
            {"class_id": 0, "bbox_xyxy": [750, 800, 758, 808], "confidence": 0.8},
        ],
    )
    predictions = detector.detect(np.zeros((1080, 4096, 3), dtype=np.uint8), 17)
    assert len(predictions) == 1
    assert predictions[0].source_class_id == 32 and predictions[0].semantic_class == "ball"
    assert predictions[0].bbox_xyxy == [750, 800, 758, 808]
    assert predictions[0].detection_id == "17:0"


def test_ball_tile_manifest_cannot_relabel_a_person(model_manifest):
    from football_pipeline.contracts import PipelineError, write_json
    from football_pipeline.detection import load_model_manifest

    path, manifest = model_manifest
    spec = manifest["models"][0]
    spec["class_mapping"] = {"0": "ball"}
    spec["expected_names"] = {"0": "person"}
    spec["ball_tiles"] = {"sizes": [1280], "imgsz": 1280, "overlap": 0.2, "merge_iou": 0.5}
    write_json(path, manifest)
    with pytest.raises(PipelineError, match="echte ballenklasse"):
        load_model_manifest(path)
