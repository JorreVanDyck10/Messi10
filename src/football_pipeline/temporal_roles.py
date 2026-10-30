"""Experimental causal official consensus; never enabled by a default profile."""

from collections import deque

import numpy as np
from scipy.optimize import linear_sum_assignment

from persoon1.metrics import iou

from .kit_embedding import embedding_candidate


class TemporalOfficials:
    """Link unambiguous adjacent boxes, including officials without player track IDs."""

    def __init__(self, fps, model, required=3, window=5):
        if not 1 <= required <= window or fps <= 0:
            raise ValueError("Invalid temporal consensus settings")
        self.model, self.required, self.window = model, required, window
        self.previous = []
        self.last_index = None

    def update(self, detections, index, *, reset=False):
        if reset or self.last_index is None or index != self.last_index + 1:
            self.previous = []
        self.last_index = index
        current = [d for d in detections if d.semantic_class in {"player", "referee", "person"}]
        links = {}
        if self.previous and current:
            overlap = np.asarray([[iou(d.bbox_xyxy, p[0]) for p in self.previous] for d in current])
            rows, cols = linear_sum_assignment(-overlap)
            for row, col in zip(rows, cols):
                alternatives = np.delete(overlap[row], col)
                competitors = np.delete(overlap[:, col], row)
                runner_up = max(float(alternatives.max(initial=0)), float(competitors.max(initial=0)))
                if overlap[row, col] >= 0.5 and overlap[row, col] - runner_up >= 0.15:
                    links[row] = self.previous[col][1]
        following = []
        for row, detection in enumerate(current):
            history = deque(links.get(row, ()), maxlen=self.window)
            probabilities = detection.role_probabilities or []
            context = detection.role_context_player_score
            position = detection.field_position
            protected = (
                detection.player_kind == "goalkeeper"
                or detection.projection_status != "valid"
                or not position
                or not 0.2 < position[0] < 0.8
                or len(probabilities) != 3
                or context is None
            )
            score = None
            if not protected:
                _, score = embedding_candidate(detection, self.model)
            supported = bool(
                not protected
                and probabilities[1] >= 0.75
                and context <= 0.4
                and score is not None
                and score <= 0.6
            )
            history.append(supported)
            # Strong current player evidence or field uncertainty defeats history.
            reject = (
                not protected and probabilities[0] < 0.9 and context <= 0.6 and sum(history) >= self.required
            )
            if reject and detection.semantic_class == "player":
                detection.semantic_class = "referee"
                detection.track_id = None
                detection.team_id = None
                detection.team_status = "not_player"
                detection.role_decision = "experimental_temporal_official_consensus"
                detection.role_consensus_evidence = {
                    "rule": "temporal_official_adjacent_boxes_v1",
                    "votes": list(history),
                    "required": self.required,
                    "window": self.window,
                    "current_crop_referee": probabilities[1],
                    "current_context_player": context,
                }
            following.append((list(detection.bbox_xyxy), history))
        self.previous = following
