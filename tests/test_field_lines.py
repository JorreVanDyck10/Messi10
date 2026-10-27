import copy

import numpy as np

from football_pipeline.automatic_calibration import transform
from football_pipeline.field_layout import LINES_UV, POINTS_UV
from football_pipeline.field_line_geometry import estimate_from_lines, line_inverse
from football_pipeline.field_motion import DEFAULT_SETTINGS, estimate_checked


def example():
    inverse = np.array([[560, 20, 30], [0, 280, 40], [0, 0.04, 1.0]])
    observation = {"points": [], "lines": []}
    for i in [5, 26]:
        x, y = transform([POINTS_UV[i]], inverse)[0]
        observation["points"].append({"id": i, "x": x, "y": y, "confidence": 0.99})
    for i in [2, 5, 14, 17]:
        observation["lines"].append(
            {"id": i, "xy": transform(LINES_UV[i], inverse).tolist(), "confidence": 0.99}
        )
    return observation, inverse


def test_dual_homography_preserves_unfitted_point_controls():
    observation, expected = example()
    actual = line_inverse(observation["lines"], (640, 360))
    np.testing.assert_allclose(actual / actual[2, 2], expected, atol=1e-8)
    rejected = estimate_checked(observation, (640, 360))
    assert rejected["status"] == "insufficient_points"
    recovered = estimate_from_lines(rejected, (640, 360), DEFAULT_SETTINGS)
    assert recovered["status"] == "valid"
    assert recovered["quality"]["fit_ids"] == []
    assert recovered["quality"]["control_ids"] == [5, 26]
    changed = copy.deepcopy(observation)
    changed["points"][0]["y"] += 30
    failed = estimate_from_lines(estimate_checked(changed, (640, 360)), (640, 360), DEFAULT_SETTINGS)
    assert failed["status"] != "valid"
