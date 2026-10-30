"""One mapping from PnLCalib's stretched 960 x 540 input to original pixels."""

from .field_layout import LINES_UV, POINTS_UV

MODEL_SIZE = (960, 540)


def observation_from_peaks(keypoints, lines, image_size):
    width, height = image_size
    if width <= 0 or height <= 0:
        raise ValueError("Field observation requires positive original image dimensions")
    sx, sy = width / MODEL_SIZE[0], height / MODEL_SIZE[1]
    return {
        "image_size": [width, height],
        "points": [
            {
                "id": k,
                "x": p["x"] * sx,
                "y": p["y"] * sy,
                "confidence": min(1.0, max(0.0, p["p"])),
                "raw_score": p["p"],
            }
            for k, p in keypoints.items()
            if k in POINTS_UV
        ],
        "lines": [
            {
                "id": k,
                "xy": [[p["x_1"] * sx, p["y_1"] * sy], [p["x_2"] * sx, p["y_2"] * sy]],
                "confidence": min(1.0, max(0.0, min(p["p_1"], p["p_2"]))),
                "raw_scores": [p["p_1"], p["p_2"]],
            }
            for k, p in lines.items()
            if k in LINES_UV
        ],
    }
