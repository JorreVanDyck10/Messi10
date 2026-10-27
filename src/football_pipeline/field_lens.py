"""Measured division-model lens correction, with held-out white-line checks.

This is an image straightness check, not an independent field-accuracy measurement.
"""

from __future__ import annotations

from functools import lru_cache

import cv2
import numpy as np
from scipy.optimize import minimize_scalar


def validate_lens(lens, size):
    if lens is None:
        return None
    if lens.get("model") != "division_radial_v1" or lens.get("image_size") != list(size):
        raise ValueError("Lens calibration belongs to a different coordinate system")
    k = lens["k"]
    if type(k) not in (int, float) or not np.isfinite(k) or not -1.5 < k < 0.5:
        raise ValueError("Invalid lens coefficient")
    return lens


def lens_scale(lens):
    w, h = lens["image_size"]
    return min(1.0, 1 + lens["k"] * (0.25 + (h / w / 2) ** 2))


def rectify_points(points, lens):
    xy = np.asarray(points, float).reshape(-1, 2)
    if lens is None:
        return xy.copy()
    w, h = lens["image_size"]
    validate_lens(lens, (w, h))
    center = np.array([w, h]) / 2
    p = (xy - center) / w
    denominator = 1 + lens["k"] * (p * p).sum(1)
    if not np.isfinite(p).all() or (denominator <= 0.2).any():
        raise ValueError("Lens projection is outside the supported image")
    return center + lens_scale(lens) * w * p / denominator[:, None]


def distort_points(points, lens):
    xy = np.asarray(points, float).reshape(-1, 2)
    if lens is None:
        return xy.copy()
    w, h = lens["image_size"]
    validate_lens(lens, (w, h))
    center = np.array([w, h]) / 2
    q = (xy - center) / (w * lens_scale(lens))
    discriminant = 1 - 4 * lens["k"] * (q * q).sum(1)
    if not np.isfinite(q).all() or (discriminant < 0).any():
        raise ValueError("Lens inverse is outside the supported image")
    return center + w * q * (2 / (1 + np.sqrt(discriminant)))[:, None]


@lru_cache(maxsize=2)
def _maps(width, height, k):
    yy, xx = np.indices((height, width), dtype=np.float32)
    lens = {"model": "division_radial_v1", "image_size": [width, height], "k": k}
    raw = distort_points(np.column_stack((xx.ravel(), yy.ravel())), lens).reshape(height, width, 2)
    return raw[:, :, 0].astype(np.float32), raw[:, :, 1].astype(np.float32)


def rectify_image(frame, lens):
    if lens is None:
        return frame
    h, w = frame.shape[:2]
    validate_lens(lens, (w, h))
    return cv2.remap(frame, *_maps(w, h, lens["k"]), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def thin(mask):
    z = np.pad(mask.astype(np.uint8), 1)
    for _ in range(100):
        removed = 0
        for phase in range(2):
            p = [
                z[:-2, 1:-1],
                z[:-2, 2:],
                z[1:-1, 2:],
                z[2:, 2:],
                z[2:, 1:-1],
                z[2:, :-2],
                z[1:-1, :-2],
                z[:-2, :-2],
            ]
            n = sum(p)
            transitions = sum((a == 0) & (b == 1) for a, b in zip(p, p[1:] + p[:1]))
            keep1 = p[0] * p[2] * (p[4] if phase == 0 else p[6])
            keep2 = (p[2] if phase == 0 else p[0]) * p[4] * p[6]
            delete = (
                (z[1:-1, 1:-1] == 1) & (n >= 2) & (n <= 6) & (transitions == 1) & (keep1 == 0) & (keep2 == 0)
            )
            removed += np.count_nonzero(delete)
            z[1:-1, 1:-1][delete] = 0
        if not removed:
            break
    return z[1:-1, 1:-1]


def white_chains(frame, width=1280):
    h0, w0 = frame.shape[:2]
    width = min(width, w0)
    h = round(h0 * width / w0)
    small = cv2.resize(frame, (width, h))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    grass = cv2.inRange(hsv, np.array([25, 35, 25]), np.array([95, 255, 255])) / 255.0
    near_grass = cv2.boxFilter(grass, -1, (15, 15)) > 0.4
    white = ((hsv[:, :, 1] < 110) & (hsv[:, :, 2] > 135) & near_grass).astype(np.uint8)
    skeleton = thin(cv2.morphologyEx(white, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)))
    z = np.pad(skeleton, 1)
    p = [z[:-2, 1:-1], z[:-2, 2:], z[1:-1, 2:], z[2:, 2:], z[2:, 1:-1], z[2:, :-2], z[1:-1, :-2], z[:-2, :-2]]
    transitions = sum((a == 0) & (b == 1) for a, b in zip(p, p[1:] + p[:1]))
    skeleton[cv2.dilate((transitions >= 3).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0] = 0
    count, labels, stats, _ = cv2.connectedComponentsWithStats(skeleton, 8)
    chains = []
    for i in range(1, count):
        if stats[i, cv2.CC_STAT_AREA] < 100:
            continue
        xy = np.column_stack(np.where(labels == i)[::-1]).astype(float)
        if np.linalg.norm(xy.max(0) - xy.min(0)) >= 150:
            chains.append(xy)
    return chains, (width, h)


def line_rmse(xy):
    centered = xy - xy.mean(0)
    _, _, vectors = np.linalg.svd(centered, full_matrices=False)
    return float(np.sqrt(np.mean((centered @ vectors[-1]) ** 2)))


def estimate_lens(frame):
    chains, size = white_chains(frame)
    w, h = size
    # A long lower touchline provides radial curvature; short arcs/circles cannot select k.
    eligible = [p for p in chains if np.ptp(p[:, 0]) >= w * 0.5 and np.median(p[:, 1]) > h * 0.6]
    if not eligible:
        return None
    anchor = max(eligible, key=len)
    controls = [p for p in chains if p is not anchor and line_rmse(p) <= 1.5]
    if len(controls) < 2 or line_rmse(anchor) < 2:
        return None
    anchor = anchor[np.lexsort((anchor[:, 1], anchor[:, 0]))]
    fit, holdout = anchor[np.arange(len(anchor)) % 4 != 0], anchor[::4]

    def adjusted(points, k):
        lens = {"model": "division_radial_v1", "image_size": list(size), "k": float(k)}
        # Remove the canvas scale for an honest pixel-straightness comparison.
        return (rectify_points(points, lens) - np.array(size) / 2) / lens_scale(lens)

    fit_result = minimize_scalar(
        lambda k: line_rmse(adjusted(fit, k)), bounds=(-1.45, 0.45), method="bounded"
    )
    k = float(fit_result.x)
    if not fit_result.success or abs(k) < 0.03 or not -1.4 < k < 0.4:
        return None
    before, after = line_rmse(holdout), line_rmse(adjusted(holdout, k))
    if after > 1.5 or after > before * 0.3:
        return None
    checked = []
    for control in controls:
        a, b = line_rmse(control), line_rmse(adjusted(control, k))
        if b > max(1.5, a + 0.5):
            return None
        checked.append({"before_rmse_px": a, "after_rmse_px": b})
    h0, w0 = frame.shape[:2]
    return {
        "model": "division_radial_v1",
        "image_size": [w0, h0],
        "k": round(k, 8),
        "estimated_from": "measured_lower_white_chain; separate straight-chain controls",
        "independent_human_accuracy_validation": False,
        "quality": {
            "measurement_image_size": list(size),
            "heldout_before_rmse_px": before,
            "heldout_after_rmse_px": after,
            "separate_controls": checked,
        },
    }
