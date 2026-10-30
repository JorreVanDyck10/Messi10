"""Map an image-only grass crop's field observations back to original pixels."""

from copy import deepcopy

from .field_pose import field_crop


def observe_cropped(frame, observe, *, roi=None):
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = field_crop(frame) if roi is None else roi
    if (
        any(type(v) is not int for v in (x1, y1, x2, y2))
        or not 0 <= x1 < x2 <= width
        or not 0 <= y1 < y2 <= height
    ):
        raise ValueError("Crop must stay inside original pixels")
    observation = deepcopy(observe(frame[y1:y2, x1:x2]))
    if observation["image_size"] != [x2 - x1, y2 - y1]:
        raise ValueError("Observer returned a different crop coordinate system")
    for point in observation["points"]:
        point["x"] += x1
        point["y"] += y1
    for line in observation["lines"]:
        line["xy"] = [[x + x1, y + y1] for x, y in line["xy"]]
    observation["image_size"] = [width, height]
    observation["roi"] = [x1, y1, x2, y2]
    observation["view_policy"] = "measured_grass_crop_before_single_network_pass_v1"
    return observation
