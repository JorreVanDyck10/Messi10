"""Berekent boxoverlap, één-op-één klassekoppelingen en AP met 101 recallpunten voor volledig gelabelde beelden.


Both reference and fine-tuned predictions use the same implementation. This is not
advertised as the complete COCO benchmark (area ranges/crowd handling are absent).
"""

import math


def iou(a, b):
    """Bereken doorsnede gedeeld door vereniging van twee xyxy-boxen en retourneer nul wanneer de
    vereniging leeg is.
    """
    inter = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    area_a = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
    area_b = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union else 0.0


def match_class(ground_truth, predictions, class_id, threshold):
    """Sorteer de voorspellingen van één klasse op confidence en koppel elke referentie hoogstens eenmaal
    boven de opgegeven IoU-grens.
    """
    gt = {fid: [box for box in boxes if box["class_id"] == class_id] for fid, boxes in ground_truth.items()}
    ordered = sorted(
        [(fid, box) for fid, boxes in predictions.items() for box in boxes if box["class_id"] == class_id],
        key=lambda x: (-x[1]["confidence"], x[0]),
    )
    used, flags = set(), []
    for fid, box in ordered:
        candidates = [(iou(box["bbox_xyxy"], label["bbox_xyxy"]), j) for j, label in enumerate(gt.get(fid, [])) if (fid, j) not in used]
        overlap, index = max(candidates, default=(0.0, -1))
        hit = index >= 0 and overlap >= threshold
        if hit:
            used.add((fid, index))
        flags.append((fid, box, hit))
    return sum(map(len, gt.values())), flags, used, gt


def ap101(total, flags):
    """Bereken geïnterpoleerde AP op 101 recallniveaus uit de confidencegesorteerde true-/false-
    positivevlaggen.
    """
    if not total:
        return None
    tp = 0
    curve = []
    for index, (_, _, hit) in enumerate(flags, 1):
        tp += hit
        curve.append((tp / total, tp / index))
    return sum(max((p for r, p in curve if r + 1e-12 >= k / 100), default=0.0) for k in range(101)) / 101


def evaluate(ground_truth, predictions, names, confidence=0.25, match_iou=0.5):
    """Bereken klassegewijze AP over de IoU-drempels, precision/recall op de werkconfidence en expliciete
    FP/FN-gevallen voor review.
    """
    if set(predictions) != set(ground_truth):
        raise ValueError("Predictions must cover exactly the evaluated frames, including empty frames")
    for boxes in predictions.values():
        for box in boxes:
            if type(box["class_id"]) is not int or not 0 <= box["class_id"] < len(names):
                raise ValueError("Unmapped predicted class")
            coords = box["bbox_xyxy"]
            if len(coords) != 4 or not all(math.isfinite(v) for v in coords) or coords[0] >= coords[2] or coords[1] >= coords[3]:
                raise ValueError("Invalid predicted box")
            if not math.isfinite(box["confidence"]) or not 0 <= box["confidence"] <= 1:
                raise ValueError("Invalid confidence")
    per_class, errors = [], []
    work = {fid: [b for b in boxes if b["confidence"] >= confidence] for fid, boxes in predictions.items()}
    for cls, name in enumerate(names):
        aps = []
        for k in range(10):
            total, flags, _, _ = match_class(ground_truth, predictions, cls, 0.5 + k * 0.05)
            aps.append(ap101(total, flags))
        total, flags, used, gt = match_class(ground_truth, work, cls, match_iou)
        tp = sum(hit for _, _, hit in flags)
        fp, fn = len(flags) - tp, total - tp
        for fid, box, hit in flags:
            if not hit:
                errors.append({"frame_id": fid, "type": "FP", "class_id": cls, "prediction": box, "cause": "not established"})
        for fid, boxes in gt.items():
            for index, box in enumerate(boxes):
                if (fid, index) not in used:
                    errors.append({"frame_id": fid, "type": "FN", "class_id": cls, "annotation": box, "cause": "not established"})
        per_class.append({"class_id": cls, "name": name, "objects": total, "AP50": aps[0],
                          "AP50_95": sum(aps) / 10 if total else None, "TP": tp, "FP": fp, "FN": fn,
                          "precision": tp / (tp + fp) if tp + fp else 0.0,
                          "recall": tp / total if total else None})
    valid = [c for c in per_class if c["objects"]]
    return {"method": "101-point interpolated box AP, IoU 0.50:0.05:0.95, no crowd/ignore",
            "mAP50": sum(c["AP50"] for c in valid) / len(valid) if valid else None,
            "mAP50_95": sum(c["AP50_95"] for c in valid) / len(valid) if valid else None,
            "workpoint": {"confidence": confidence, "matching_iou": match_iou},
            "per_class": per_class, "errors": errors}
