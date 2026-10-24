"""Per-video kit-colour clustering; new videos never inherit another match's team identities."""

import cv2
import numpy as np

from .geometry import valid_box


def kit_feature(frame, box):
    """Saturation-weighted torso histograms; grey hue cannot dominate a kit.

    A predominantly green torso is retained; mixed green background is filtered.
    Numbers/stripes remain a distribution instead of becoming a median shirt
    colour. This is separate from the trained role classifier's input format.
    """
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    crop = frame[
        max(0, int(y1 + height * 0.18)) : max(1, int(y1 + height * 0.57)),
        max(0, int(x1 + width * 0.2)) : max(1, int(x1 + width * 0.8)),
    ]
    if crop.size == 0:
        return None
    hsv = cv2.cvtColor(cv2.resize(crop, (16, 24)), cv2.COLOR_BGR2HSV).reshape(-1, 3).astype(np.float32)
    green = (hsv[:, 0] > 30) & (hsv[:, 0] < 90) & (hsv[:, 1] > 55)
    if green.mean() < 0.8 and (~green).any():
        hsv = hsv[~green]
    saturation = hsv[:, 1] / 255
    hue = np.histogram(hsv[:, 0], bins=16, range=(0, 180), weights=saturation)[0] / len(hsv)
    sat = np.histogram(hsv[:, 1], bins=8, range=(0, 256))[0] / len(hsv)
    value = np.histogram(hsv[:, 2], bins=8, range=(0, 256))[0] / len(hsv)
    return np.concatenate([hue, sat, 0.6 * value]).astype(np.float32)


class VideoTeams:
    def __init__(self):
        self.samples = []
        self.updates = 0
        self.centers = None
        self.radii = None

    def update(self, frame, detections):
        self.updates += 1
        players = [
            d
            for d in detections
            if d.semantic_class == "player"
            and (d.role_confidence or 0) >= 0.65
            and valid_box(d, (frame.shape[1], frame.shape[0]))
        ]
        for detection in players:
            detection.team_id = None
            detection.team_confidence = None
            detection.team_method = None
            detection.team_class_id = None
        features = [kit_feature(frame, d.bbox_xyxy) for d in players]
        if self.centers is None or len(self.samples) < 200:
            self.samples.extend(
                feature
                for d, feature in zip(players, features)
                if d.confidence >= 0.4 and feature is not None
            )
            self.samples = self.samples[-200:]
            if len(self.samples) < 24 or self.updates < 3:
                return
            values = np.asarray(self.samples, np.float32)
            # Local RNG, deterministic initialization; no change to OpenCV's global random state.
            rng = np.random.default_rng(42)
            best = None
            for _ in range(8):
                centers = values[rng.choice(len(values), 2, replace=False)].copy()
                for _ in range(20):
                    distances = np.linalg.norm(values[:, None] - centers, axis=2)
                    labels = distances.argmin(1)
                    if any(not (labels == i).any() for i in range(2)):
                        break
                    updated = np.stack([values[labels == i].mean(0) for i in range(2)])
                    if np.allclose(updated, centers):
                        break
                    centers = updated
                cost = float(np.linalg.norm(values - centers[labels], axis=1).sum())
                if best is None or cost < best[0]:
                    best = cost, centers, labels
            _, centers, labels = best
            sizes = np.bincount(labels, minlength=2)
            if min(sizes) < len(values) * 0.2 or np.linalg.norm(centers[0] - centers[1]) < 0.25:
                return
            # Neutral A/B names, initially ordered by saturation. Keep the names
            # aligned while refining the first 200 high-confidence observations.
            order = sorted(range(2), key=lambda i: sum(centers[i, 16:24] * np.arange(8)))
            if self.centers is not None:
                direct = np.linalg.norm(centers - self.centers, axis=1).sum()
                swapped = np.linalg.norm(centers[::-1] - self.centers, axis=1).sum()
                order = [0, 1] if direct <= swapped else [1, 0]
            self.centers = centers[order]
            self.radii = [
                max(0.15, float(np.quantile(np.linalg.norm(values[labels == i] - centers[i], axis=1), 0.9)))
                for i in order
            ]
        for detection, feature in zip(players, features):
            if feature is None:
                continue
            distances = np.linalg.norm(self.centers - feature, axis=1)
            closest = int(distances.argmin())
            margin = float(1 - distances[closest] / max(1e-9, distances[1 - closest]))
            if margin >= 0.2 and distances[closest] <= self.radii[closest] + 0.1:
                detection.team_id = "team_a" if closest == 0 else "team_b"
                detection.team_confidence = margin  # separation margin, explicitly not a probability
                detection.team_method = "video_colour_clusters"

    @property
    def info(self):
        return {
            "method": "video_colour_clusters",
            "feature_version": "saturation_weighted_hsv_v2",
            "calibration_observation_limit": 200,
            "ready": self.centers is not None,
            "samples": len(self.samples),
            "updates": self.updates,
            "centers": self.centers.tolist() if self.centers is not None else None,
            "radii": self.radii,
            "names": "neutral A/B; no club or home-away claim",
            "confidence_meaning": "relative colour distance margin, not probability",
        }
