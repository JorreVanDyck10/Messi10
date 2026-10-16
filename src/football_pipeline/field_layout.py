"""PnLCalib's semantic IDs on its assumed 105 x 68 template (not measured pitch dimensions)."""

from __future__ import annotations

import numpy as np

from .field_model_spec import (
    RELEASE_WEIGHTS as RELEASE_WEIGHTS,
)
from .field_model_spec import (
    UPSTREAM_REVISION as UPSTREAM_REVISION,
)
from .field_model_spec import (
    UPSTREAM_URL as UPSTREAM_URL,
)

# Geometric coordinates, from the upstream utils/utils_calib.py at the pinned revision.
POINTS_M = [
    (0, 0),
    (52.5, 0),
    (105, 0),
    (0, 13.84),
    (16.5, 13.84),
    (88.5, 13.84),
    (105, 13.84),
    (0, 24.84),
    (5.5, 24.84),
    (99.5, 24.84),
    (105, 24.84),
    (0, 30.34),
    (0, 30.34),
    (105, 30.34),
    (105, 30.34),
    (0, 37.66),
    (0, 37.66),
    (105, 37.66),
    (105, 37.66),
    (0, 43.16),
    (5.5, 43.16),
    (99.5, 43.16),
    (105, 43.16),
    (0, 54.16),
    (16.5, 54.16),
    (88.5, 54.16),
    (105, 54.16),
    (0, 68),
    (52.5, 68),
    (105, 68),
    (16.5, 26.68),
    (52.5, 24.85),
    (88.5, 26.68),
    (16.5, 41.31),
    (52.5, 43.15),
    (88.5, 41.31),
    (19.99, 32.29),
    (43.68, 31.53),
    (61.31, 31.53),
    (85, 32.29),
    (19.99, 35.7),
    (43.68, 36.46),
    (61.31, 36.46),
    (85, 35.7),
    (11, 34),
    (16.5, 34),
    (20.15, 34),
    (46.03, 27.53),
    (58.97, 27.53),
    (43.35, 34),
    (52.5, 34),
    (61.5, 34),
    (46.03, 40.47),
    (58.97, 40.47),
    (84.85, 34),
    (88.5, 34),
    (94, 34),
]
ABOVE_GROUND = {12, 15, 16, 19}
POINTS_UV = {
    i: np.array(p, dtype=float) / [105, 68] for i, p in enumerate(POINTS_M, 1) if i not in ABOVE_GROUND
}
LINES_M = {
    1: ((0, 54.16), (16.5, 54.16)),
    2: ((16.5, 13.84), (16.5, 54.16)),
    3: ((16.5, 13.84), (0, 13.84)),
    4: ((88.5, 54.16), (105, 54.16)),
    5: ((88.5, 13.84), (88.5, 54.16)),
    6: ((88.5, 13.84), (105, 13.84)),
    13: ((52.5, 0), (52.5, 68)),
    14: ((0, 68), (105, 68)),
    15: ((0, 0), (0, 68)),
    16: ((105, 0), (105, 68)),
    17: ((0, 0), (105, 0)),
    18: ((0, 43.16), (5.5, 43.16)),
    19: ((5.5, 43.16), (5.5, 24.84)),
    20: ((5.5, 24.84), (0, 24.84)),
    21: ((99.5, 43.16), (105, 43.16)),
    22: ((99.5, 43.16), (99.5, 24.84)),
    23: ((99.5, 24.84), (105, 24.84)),
}
LINES_UV = {i: np.array(p, dtype=float) / [105, 68] for i, p in LINES_M.items()}

COORDINATE_SYSTEM = "normalized_u_length_v_width_v1"
POLICY = {
    "version": 1,
    "keypoint_threshold": 0.3434,
    "line_threshold": 0.7867,
    "minimum_points": 6,
    "minimum_lines": 2,
    "median_diagonal_fraction": 0.005,
    "maximum_diagonal_fraction": 0.01,
    "minimum_image_hull_fraction": 0.001,
    "orientation": "main_sideline_camera_u_right_v_down",
}
