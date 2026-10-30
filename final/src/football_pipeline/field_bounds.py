"""Visible pitch geometry in source pixels, clipped before perspective division."""

from __future__ import annotations

import cv2
import numpy as np


def visible_field_polygon(matrix, image_size, support_xy):
    """Intersect the image with 0 <= H(x,y) <= 1 on the observed horizon branch.

    Clipping homogeneous half-planes avoids inventing offscreen corners, including
    when the virtual pitch corners straddle the projective horizon.
    """
    h = np.asarray(matrix, float)
    support = np.asarray(support_xy, float)
    width, height = image_size
    if h.shape != (3, 3) or not np.isfinite(h).all() or np.linalg.cond(h) > 1e12:
        raise ValueError("invalid_visible_field")
    if support.ndim != 2 or support.shape[1] != 2 or not len(support) or not np.isfinite(support).all():
        raise ValueError("invalid_visible_field")
    h = h / np.linalg.norm(h)
    denominators = np.column_stack((support, np.ones(len(support)))) @ h[2]
    if (np.abs(denominators) < 1e-10).any() or not ((denominators > 0).all() or (denominators < 0).all()):
        raise ValueError("invalid_visible_field")
    h *= 1 if denominators[0] > 0 else -1
    polygon = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], float)
    planes = [h[2] - [0, 0, 1e-10], h[0], h[2] - h[0], h[1], h[2] - h[1]]
    for plane in planes:
        clipped = []
        if not len(polygon):
            break
        for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
            da, db = np.dot([*a, 1], plane), np.dot([*b, 1], plane)
            if da >= 0:
                clipped.append(a)
            if (da >= 0) != (db >= 0):
                clipped.append(a + (b - a) * da / (da - db))
        polygon = np.asarray(clipped, float)
    if len(polygon) < 3 or not np.isfinite(polygon).all():
        raise ValueError("invalid_visible_field")
    if cv2.contourArea(polygon.astype(np.float32)) < 1:
        raise ValueError("invalid_visible_field")
    return polygon.tolist()


def contains_footpoint(polygon, point):
    """No margin or snapping outside the pitch; boundaries themselves are valid."""
    values = np.asarray(polygon, float)
    if values.ndim != 2 or values.shape[1] != 2 or len(values) < 3 or not np.isfinite(values).all():
        raise ValueError("invalid_visible_field")
    return cv2.pointPolygonTest(values.astype(np.float32), tuple(point), False) >= 0


def attach_visible_field(state, image_size):
    result = dict(state, visible_field_polygon_xy=None)
    if result["status"] != "valid":
        return result
    support = result.get("tracked_points") or [[p["x"], p["y"]] for p in result.get("points", [])]
    try:
        result["visible_field_polygon_xy"] = visible_field_polygon(result["homography"], image_size, support)
    except (ValueError, TypeError, np.linalg.LinAlgError):
        result.update(status="invalid_visible_field", source="unavailable", homography=None)
    return result
