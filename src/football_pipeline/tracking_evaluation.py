"""Identity assignment at bbox IoU .5; no benchmark ignore-region processing.

IDF1 follows the global potential-match assignment used by TrackEval Identity:
https://github.com/JonathonLuiten/TrackEval/blob/master/trackeval/metrics/identity.py
"""

from collections import Counter

import numpy as np
from scipy.optimize import linear_sum_assignment

from persoon1.metrics import iou


def identity_metrics(frames):
    potential, gt_counts, pred_counts = Counter(), Counter(), Counter()
    previous, switches = {}, 0
    for truth, predicted in frames:
        gt_ids = [str(d["track_id"]) for d in truth]
        pred_ids = [str(d["track_id"]) for d in predicted]
        if len(set(gt_ids)) != len(gt_ids) or len(set(pred_ids)) != len(pred_ids):
            raise ValueError("Identity metrics require unique IDs within each frame")
        if any(d.get("track_id") is None for d in truth + predicted):
            raise ValueError("Identity metrics require explicit IDs")
        gt_counts.update(gt_ids)
        pred_counts.update(pred_ids)
        if not truth or not predicted:
            continue
        overlap = np.asarray([[iou(g["bbox"], p["bbox"]) for p in predicted] for g in truth])
        for r, c in zip(*np.nonzero(overlap >= 0.5)):
            potential[gt_ids[r], pred_ids[c]] += 1
        # Preserve a previous valid pair before allocating competing matches.
        continuity = np.asarray([[previous.get(g) == p for p in pred_ids] for g in gt_ids])
        reward = (overlap >= 0.5) * (overlap + 1 + continuity)
        rows, cols = linear_sum_assignment(-reward)
        for r, c in zip(rows, cols):
            if overlap[r, c] < 0.5:
                continue
            g, p = gt_ids[r], pred_ids[c]
            switches += int(g in previous and previous[g] != p)
            previous[g] = p
    ground, predictions = sorted(gt_counts), sorted(pred_counts)
    tp = 0
    if ground and predictions:
        counts = np.asarray([[potential[g, p] for p in predictions] for g in ground])
        rows, cols = linear_sum_assignment(-counts)
        tp = int(counts[rows, cols].sum())
    fn, fp = sum(gt_counts.values()) - tp, sum(pred_counts.values()) - tp
    return {
        "IDTP": tp,
        "IDFN": fn,
        "IDFP": fp,
        "IDF1": 2 * tp / max(1, 2 * tp + fp + fn),
        "ID_switches": switches,
        "ground_truth_detections": sum(gt_counts.values()),
        "tracked_detections": sum(pred_counts.values()),
        "iou_threshold": 0.5,
        "scope": "fully labelled on-pitch people; no benchmark ignore/crowd handling",
    }
