"""Experimental image-paint veto; it cannot create a homography or an anchor.

Long, straight white chains near grass supply pixel evidence separately from
the neural semantic peaks. This remains an automatic consistency check.
"""

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
