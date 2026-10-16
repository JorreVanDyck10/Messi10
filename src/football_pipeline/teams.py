"""Per-video kit-colour clustering; new videos never inherit another match's team identities."""

import numpy as np

from .appearance import jersey_feature
from .geometry import valid_box


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
        features = [jersey_feature(frame, d.bbox_xyxy, remove_turf=True) for d in players]
        if self.centers is None:
            self.samples.extend(
                feature for d, feature in zip(players, features) if d.confidence >= 0.4 and feature.any()
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
            # Neutral A/B names, ordered by mean saturation. No home/away identity is inferred.
            order = sorted(range(2), key=lambda i: sum(centers[i, 16:24] * np.arange(8)))
            self.centers = centers[order]
            self.radii = [
                max(0.15, float(np.quantile(np.linalg.norm(values[labels == i] - centers[i], axis=1), 0.9)))
                for i in order
            ]
        for detection, feature in zip(players, features):
            if not feature.any():
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
            "ready": self.centers is not None,
            "samples": len(self.samples),
            "updates": self.updates,
            "centers": self.centers.tolist() if self.centers is not None else None,
            "radii": self.radii,
            "names": "neutral A/B; no club or home-away claim",
            "confidence_meaning": "relative colour distance margin, not probability",
        }
