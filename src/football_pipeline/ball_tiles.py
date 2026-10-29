"""Detecteert kleine ballen in overlappende beeldtegels. Boxen gaan terug naar bronpixels en globale NMS verwijdert dubbele tegelvoorspellingen."""

from __future__ import annotations

import math


def axis_starts(length: int, size: int, overlap: float) -> list[int]:
    """Bepaal tegelstarts inclusief de laatste beeldrand, ook als de stap daar niet exact uitkomt."""
    if type(length) is not int or type(size) is not int or length <= 0 or size <= 0:
        raise ValueError("Positive integer image/tile dimensions required")
    if not math.isfinite(overlap) or not 0 <= overlap < 0.5:
        raise ValueError("Tile overlap must be in [0,.5)")
    if length <= size:
        return [0]
    stride = max(1, round(size * (1 - overlap)))
    return sorted({*range(0, length - size + 1, stride), length - size})


def tile_windows(width: int, height: int, size: int, overlap: float = 0.2):
    """Maak overlappende rechthoeken in oorspronkelijke pixels, zonder het bronbeeld te wijzigen."""
    return [
        (x, y, min(x + size, width), min(y + size, height))
        for y in axis_starts(height, size, overlap)
        for x in axis_starts(width, size, overlap)
    ]


def validate_ball_tile_config(config):
    """Weiger ongeldige tegelgroottes, invoerresolutie, overlap of globale NMS-drempel voordat inferentie
    begint.
    """
    sizes = config.get("sizes") if isinstance(config, dict) else None
    if (
        not isinstance(sizes, list)
        or not 1 <= len(sizes) <= 3
        or any(type(size) is not int or not 128 <= size <= 4096 for size in sizes)
        or len(sizes) != len(set(sizes))
    ):
        raise ValueError("Ball tile sizes require 1–3 distinct integers in [128,4096]")
    if type(config.get("imgsz")) is not int or not 128 <= config["imgsz"] <= 4096:
        raise ValueError("Invalid ball tile input resolution")
    overlap, merge = config.get("overlap"), config.get("merge_iou")
    if not isinstance(overlap, (float, int)) or not math.isfinite(overlap) or not 0 <= overlap < 0.5:
        raise ValueError("Invalid ball tile overlap")
    if not isinstance(merge, (float, int)) or not math.isfinite(merge) or not 0 < merge <= 1:
        raise ValueError("Invalid ball tile global NMS")


def predict_multiscale_ball(
    model, frame, config, *, confidence=0.25, local_iou=0.7, device="0", source_class=32
):
    """Voer baldetectie uit voor elke geconfigureerde tegelgrootte en voeg alle bronpixelboxen met één
    globale NMS samen.
    """
    validate_ball_tile_config(config)
    predictions = []
    for size in config["sizes"]:
        predictions.extend(
            predict_ball_tiles(
                model,
                frame,
                size=size,
                imgsz=config["imgsz"],
                overlap=config["overlap"],
                confidence=confidence,
                local_iou=local_iou,
                merge_iou=config["merge_iou"],
                device=device,
                source_class=source_class,
            )
        )
    return merge_ball_predictions(predictions, config["merge_iou"])


def merge_ball_predictions(predictions, iou_threshold=0.5):
    """Deterministic same-class NMS; keep distinct nearby ball instances."""
    if not 0 < iou_threshold <= 1:
        raise ValueError("NMS IoU must be in (0,1]")
    kept = []
    for candidate in sorted(predictions, key=lambda b: (-b["confidence"], *b["bbox_xyxy"])):
        x1, y1, x2, y2 = candidate["bbox_xyxy"]
        if not all(math.isfinite(v) for v in [x1, y1, x2, y2, candidate["confidence"]]):
            raise ValueError("Non-finite ball prediction")
        if x2 <= x1 or y2 <= y1 or not 0 <= candidate["confidence"] <= 1:
            raise ValueError("Invalid ball prediction")
        duplicate = False
        for other in kept:
            if other["class_id"] != candidate["class_id"]:
                continue
            a, b, c, d = other["bbox_xyxy"]
            intersection = max(0, min(x2, c) - max(x1, a)) * max(0, min(y2, d) - max(y1, b))
            union = (x2 - x1) * (y2 - y1) + (c - a) * (d - b) - intersection
            if intersection / union > iou_threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append(candidate)
    return kept


def predict_ball_tiles(
    model,
    frame,
    *,
    size=1280,
    imgsz=1280,
    overlap=0.2,
    confidence=0.001,
    local_iou=0.7,
    merge_iou=0.5,
    device="0",
    source_class=32,
):
    """Return source-pixel boxes with tile provenance, without any field filter."""
    if model.names.get(source_class) not in {"ball", "sports ball", "in_play_ball"}:
        raise ValueError("Source class is not explicitly a trained ball class")
    height, width = frame.shape[:2]
    predictions = []
    for x, y, right, bottom in tile_windows(width, height, size, overlap):
        pixels = frame[y:bottom, x:right]
        result = model.predict(
            pixels,
            imgsz=imgsz,
            conf=confidence,
            iou=local_iou,
            classes=[source_class],
            device=device,
            half=False,
            max_det=300,
            verbose=False,
        )[0]
        if tuple(result.orig_shape) != pixels.shape[:2]:
            raise ValueError("Tile prediction has wrong original dimensions")
        for box in result.boxes:
            a, b, c, d = box.xyxy[0].cpu().tolist()
            mapped = [max(0, a + x), max(0, b + y), min(width, c + x), min(height, d + y)]
            if mapped[2] <= mapped[0] or mapped[3] <= mapped[1]:
                continue
            predictions.append(
                {
                    "class_id": 0,
                    "bbox_xyxy": mapped,
                    "confidence": float(box.conf[0]),
                    "source_class_id": source_class,
                    "tile_xyxy": [x, y, right, bottom],
                }
            )
    return merge_ball_predictions(predictions, merge_iou)
