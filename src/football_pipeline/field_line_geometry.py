"""Experimental dual homography: fit semantic lines, reserve every point as a control."""

from __future__ import annotations

import copy

import cv2
import numpy as np

from .automatic_calibration import transform
from .field_layout import LINES_UV, POINTS_UV
from .field_motion import checked_matrix, line_checks


def line_inverse(lines, image_size):
    """Solve l_image ~ H^-T l_field in normalized coordinates, with rank checks."""
    equations = []
    for item in lines:
        field = np.column_stack((LINES_UV[item["id"]], np.ones(2)))
        image = np.column_stack((np.asarray(item["xy"]) / image_size, np.ones(2)))
        source, target = np.cross(*field), np.cross(*image)
        source /= np.linalg.norm(source)
        target /= np.linalg.norm(target)
        x, y, z = target
        cross = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
        # All three cross-product rows are redundant, but SVD handles their shared scale.
        equations.extend(np.kron(cross, source[None, :]))
    _, singular, vectors = np.linalg.svd(np.asarray(equations), full_matrices=True)
    if len(singular) < 9 or singular[-2] < 1e-7:
        raise ValueError("degenerate_lines")
    dual = vectors[-1].reshape(3, 3)
    if not np.isfinite(dual).all() or np.linalg.cond(dual) > 1e10:
        raise ValueError("degenerate_lines")
    return np.diag([*image_size, 1.0]) @ np.linalg.inv(dual).T


def estimate_from_lines(rejected, image_size, settings):
    """Only recover a rejected point fit when separate point controls verify a line fit."""
    result = copy.deepcopy(rejected)
    if rejected["status"] in {"valid", "invalid_observation", "orientation_unknown"}:
        return result
    points, lines = rejected["points"], rejected["lines"]
    if len(points) < 2 or len(lines) < 4:
        return result
    xy = np.array([[p["x"], p["y"]] for p in points])
    uv = np.array([POINTS_UV[p["id"]] for p in points])
    diagonal = np.hypot(*image_size)
    if max(np.linalg.norm(xy - p, axis=1).max() for p in xy) < diagonal * 0.05:
        return result
    endpoints = np.concatenate([item["xy"] for item in lines]).astype(np.float32)
    if cv2.contourArea(cv2.convexHull(endpoints)) < np.prod(image_size) * 0.001:
        return result
    try:
        inverse = line_inverse(lines, image_size)
        matrix = checked_matrix(inverse, xy, uv)
        point_errors = np.linalg.norm(transform(uv, inverse) - xy, axis=1)
        line_errors, identifiers = line_checks(lines, inverse)
        for errors in (point_errors, line_errors):
            if not len(errors) or not np.isfinite(errors).all():
                return result
            if (
                np.median(errors) > diagonal * settings["median_diagonal_fraction"]
                or max(errors) > diagonal * settings["maximum_diagonal_fraction"]
            ):
                return result
        result.update(status="valid", source="detected", homography=matrix.tolist())
        result["quality"].update(
            method="dual_lines_with_unfitted_point_controls_v1",
            point_fit_status=rejected["status"],
            fit_ids=[],
            fit_line_ids=identifiers,
            control_ids=[p["id"] for p in points],
            control_errors_px=point_errors.tolist(),
            line_errors_px=line_errors,
            independent_human_controls=False,
        )
    except (ValueError, np.linalg.LinAlgError, cv2.error):
        pass
    return result
