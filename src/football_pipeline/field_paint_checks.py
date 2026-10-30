"""Experimental image-paint veto; it cannot create a homography or an anchor.

Long, straight white chains near grass supply pixel evidence separately from
the neural semantic peaks. This remains an automatic consistency check.
"""

import cv2
import numpy as np

from .field_layout import LINES_UV
from .field_lens import line_rmse, white_chains


def paint_evidence(frame, state, *, chains_and_size=None):
    if state["status"] != "valid":
        return {"status": "not_applicable", "reject": False, "chains": []}
    chains, size = white_chains(frame) if chains_and_size is None else chains_and_size
    width, height = size
    original_h, original_w = frame.shape[:2]
    # Field -> measurement-image, not original image pixels.
    inverse = np.diag([width / original_w, height / original_h, 1]) @ np.linalg.inv(
        np.asarray(state["homography"])
    )
    coefficients = []
    for endpoints in LINES_UV.values():
        field = np.column_stack((endpoints, np.ones(2)))
        projected = field @ inverse.T
        line = np.cross(*projected)
        length = np.hypot(*line[:2])
        if np.isfinite(line).all() and length > 1e-10:
            coefficients.append(line / length)
    if not coefficients:
        return {"status": "unavailable", "reject": False, "chains": []}
    diagonal = np.hypot(width, height)
    measured, bad_directions = [], []
    for chain in chains:
        # Paint outside the current pitch (boards, fences, goal structure) is
        # unrelated evidence. The veto never turns missing support into trust.
        source = chain * [original_w / width, original_h / height]
        homogeneous = np.column_stack((source, np.ones(len(source)))) @ np.asarray(state["homography"]).T
        usable = np.abs(homogeneous[:, 2]) > 1e-10
        uv = np.full((len(source), 2), np.nan)
        uv[usable] = homogeneous[usable, :2] / homogeneous[usable, 2:]
        chain = chain[usable & ((uv >= 0) & (uv <= 1)).all(1)]
        if len(chain) < 100:
            continue
        if line_rmse(chain) > 1.5 or np.linalg.norm(np.ptp(chain, axis=0)) < width * 0.15:
            continue
        # The same projected primitive must explain the whole observed chain.
        residuals = np.abs(np.column_stack((chain, np.ones(len(chain)))) @ np.asarray(coefficients).T)
        primitive = int(np.median(residuals, axis=0).argmin())
        errors = residuals[:, primitive]
        median, p95 = float(np.median(errors)), float(np.quantile(errors, 0.95))
        bad = bool(median > diagonal * 0.005 and p95 > diagonal * 0.01)
        measured.append({"pixels": len(chain), "median_px": median, "p95_px": p95, "mismatch": bad})
        if bad:
            _, _, vectors = np.linalg.svd(chain - chain.mean(0), full_matrices=False)
            bad_directions.append(vectors[0])
    # Two different directions protect against a single fence or an arc fragment.
    reject = any(abs(np.linalg.det(np.stack((a, b)))) >= 0.1 for a in bad_directions for b in bad_directions)
    return {
        "status": "disagreement" if reject else "checked" if measured else "unavailable",
        "reject": bool(reject),
        "measurement_image_size": list(size),
        "chains": measured,
    }


def distance_paint_evidence(frame, state, *, measurement_width=640):
    """Check two directions of predicted paint against a grass-local white mask.

    This fast alternative samples only actual field segments in the visible
    image. Occluded/non-grass samples cannot establish a disagreement.
    """
    if state["status"] != "valid":
        return {"status": "not_applicable", "reject": False, "lines": []}
    original_h, original_w = frame.shape[:2]
    width = min(measurement_width, original_w)
    height = round(original_h * width / original_w)
    hsv = cv2.cvtColor(cv2.resize(frame, (width, height)), cv2.COLOR_BGR2HSV)
    grass = cv2.inRange(hsv, np.array([25, 35, 25]), np.array([95, 255, 255])) / 255.0
    near_grass = cv2.boxFilter(grass, -1, (15, 15)) > 0.4
    white = (hsv[:, :, 1] < 110) & (hsv[:, :, 2] > 135) & near_grass
    if not white.any():
        return {"status": "unavailable", "reject": False, "lines": []}
    distances = cv2.distanceTransform((~white).astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    matrix = np.asarray(state["homography"])
    inverse = np.linalg.inv(matrix)
    support = state.get("tracked_points") or [[p["x"], p["y"]] for p in state.get("points", [])]
    support = support or [[original_w / 2, original_h / 2]]
    branch = np.sign(np.dot([*support[0], 1], matrix[2]))
    measured, bad_axes = [], set()
    diagonal = np.hypot(width, height)
    for identifier, endpoints in LINES_UV.items():
        uv = endpoints[0] + np.linspace(0, 1, 101)[:, None] * (endpoints[1] - endpoints[0])
        projected = np.column_stack((uv, np.ones(len(uv)))) @ inverse.T
        usable = np.abs(projected[:, 2]) > 1e-10
        xy = np.full((len(uv), 2), np.nan)
        xy[usable] = projected[usable, :2] / projected[usable, 2:]
        denominator = np.column_stack((xy, np.ones(len(xy)))) @ matrix[2]
        xy *= [width / original_w, height / original_h]
        inside = usable & (np.sign(denominator) == branch) & ((xy >= 0) & (xy < [width, height])).all(1)
        pixels = np.rint(xy[inside]).astype(int)
        pixels = np.clip(pixels, [0, 0], [width - 1, height - 1])
        if len(pixels):
            pixels = pixels[near_grass[pixels[:, 1], pixels[:, 0]]]
        if len(pixels) < 10 or np.linalg.norm(np.ptp(pixels, axis=0)) < width * 0.15:
            continue
        errors = distances[pixels[:, 1], pixels[:, 0]]
        median, p95 = float(np.median(errors)), float(np.quantile(errors, 0.95))
        mismatch = bool(median > diagonal * 0.005 and p95 > diagonal * 0.01)
        measured.append(
            {
                "id": identifier,
                "samples": len(pixels),
                "median_px": median,
                "p95_px": p95,
                "mismatch": mismatch,
            }
        )
        if mismatch:
            bad_axes.add(int(np.argmax(np.abs(endpoints[1] - endpoints[0]))))
    reject = len(bad_axes) == 2
    return {
        "status": "disagreement" if reject else "checked" if measured else "unavailable",
        "reject": reject,
        "measurement_image_size": [width, height],
        "lines": measured,
    }
