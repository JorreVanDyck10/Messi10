import numpy as np
import pytest

from football_pipeline.field_crop_observations import observe_cropped


def test_crop_points_lines_and_source_size_return_to_original_pixels():
    frame = np.zeros((100, 200, 3), np.uint8)
    saved = {
        "image_size": [160, 60],
        "points": [{"id": 2, "x": 4.0, "y": 5.0, "confidence": 0.8}],
        "lines": [{"id": 13, "xy": [[2, 3], [80, 50]], "confidence": 0.9}],
    }

    def observer(crop):
        assert crop.shape == (60, 160, 3)
        return saved

    out = observe_cropped(frame, observer, roi=(20, 40, 180, 100))
    assert out["image_size"] == [200, 100]
    assert out["points"] == [{"id": 2, "x": 24.0, "y": 45.0, "confidence": 0.8}]
    assert out["lines"][0]["xy"] == [[22, 43], [100, 90]]
    assert saved["points"][0]["x"] == 4.0


def test_invalid_crop_and_observer_coordinates_rejected():
    frame = np.zeros((100, 200, 3), np.uint8)
    for roi in ((-1, 0, 100, 100), (0, 0, 201, 100), (0, 100, 100, 100), (0.5, 0, 100, 100)):
        with pytest.raises(ValueError, match="inside original"):
            observe_cropped(frame, lambda _: None, roi=roi)
    with pytest.raises(ValueError, match="coordinate system"):
        observe_cropped(frame, lambda _: {"image_size": [1, 1]}, roi=(0, 0, 200, 100))
