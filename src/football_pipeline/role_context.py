"""Combineert geleerde rolkenmerken met relatieve shirt- en positiecontext voor aanvullende classificatie.


The model sees relationships between participants, not fixed club colours. It
can refine a trained crop decision only inside a currently calibrated pitch.
"""

from __future__ import annotations

import numpy as np

from .contracts import PipelineError


def context_features(probabilities, kits, appearances, positions, boxes, image_size):
    probability = np.asarray(probabilities, np.float32)
    n = len(probability)
    if n < 4:
        raise ValueError("Field role context needs at least four participants")
    position = np.asarray(positions, float)
    box = np.asarray(boxes, float)
    width, height = image_size
    features = [
        probability,
        np.full((n, 1), min(30, n) / 20),
        np.minimum(position, 1 - position),
        np.stack(
            [
                (box[:, 2] - box[:, 0]) / width,
                (box[:, 3] - box[:, 1]) / height,
                np.log(np.maximum(1, box[:, 3] - box[:, 1]) / np.maximum(1, box[:, 2] - box[:, 0])) / 4,
            ],
            1,
        ),
    ]
    distances = np.linalg.norm(position[:, None] - position[None, :], axis=2)
    np.fill_diagonal(distances, 2)
    features.append(np.sort(distances, axis=1)[:, : min(3, n - 1)].mean(1, keepdims=True))
    for vectors in (kits, appearances):
        vectors = np.asarray(vectors, float)
        vectors = vectors / np.maximum(1e-8, np.linalg.norm(vectors, axis=1, keepdims=True))
        distances = np.clip(1 - vectors @ vectors.T, 0, 2)
        np.fill_diagonal(distances, 2)
        nearest = np.sort(distances, axis=1)[:, : min(5, n - 1)]
        nearest = np.pad(nearest, ((0, 0), (0, 5 - nearest.shape[1])), constant_values=1)
        support = np.stack(
            [(distances < t).sum(1) / max(1, n - 1) for t in (0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75)], 1
        )
        weight = np.exp(-distances / 0.15)
        np.fill_diagonal(weight, 0)
        peers = weight @ probability / np.maximum(weight.sum(1, keepdims=True), 1e-8)
        features.extend((nearest, support, peers, probability - peers))
    return np.concatenate(features, 1).astype(np.float32)


def context_head(dimension=46):
    import torch

    return torch.nn.Sequential(
        torch.nn.Linear(dimension, 64),
        torch.nn.SiLU(),
        torch.nn.Linear(64, 32),
        torch.nn.SiLU(),
        torch.nn.Linear(32, 1),
    )


class RoleContext:
    def __init__(self, spec, teacher_sha256, kit_sha256):
        import torch

        state = torch.load(spec["weights"], map_location="cpu", weights_only=True)
        if (
            state.get("format") != "pitch-role-context-v1"
            or state.get("input_dimension") != 46
            or state.get("teacher_sha256") != teacher_sha256
            or state.get("kit_weights_sha256") != kit_sha256
        ):
            raise PipelineError("Veldrolcontext past niet bij de getrainde rol- en shirtmodellen.")
        self.mean, self.std = state["mean"].numpy(), state["std"].numpy()
        self.cnn_center, self.cnn_projection = state["cnn_center"], state["cnn_projection"]
        for tensor, shape in (
            (state["mean"], (46,)),
            (state["std"], (46,)),
            (self.cnn_center, (576,)),
            (self.cnn_projection, (576, 32)),
        ):
            if tuple(tensor.shape) != shape or not torch.isfinite(tensor).all():
                raise PipelineError("Ongeldige invoerschaling voor veldrolcontext.")
        if (self.std <= 0).any():
            raise PipelineError("Veldrolcontext vereist positieve invoerschaling.")
        self.model = context_head().eval()
        self.model.load_state_dict(state["state_dict"], strict=True)
        if any(not torch.isfinite(p).all() for p in self.model.parameters()):
            raise PipelineError("Veldrolcontext bevat ongeldige modelwaarden.")
        self.spec = spec

    def update(self, detections, image_size):
        import torch

        eligible = [
            d
            for d in detections
            if d.projection_status == "valid"
            and d.confidence >= 0.25
            and d.role_model_id
            and d.role_probabilities is not None
            and len(d.role_probabilities) == 3
            and d.context_embedding is not None
            and len(d.context_embedding) == 32
            and d.team_embedding is not None
            and len(d.team_embedding) == 32
        ]
        if len(eligible) < 4:
            return
        matrix = context_features(
            [d.role_probabilities for d in eligible],
            [d.team_embedding for d in eligible],
            [d.context_embedding for d in eligible],
            [d.field_position for d in eligible],
            [d.bbox_xyxy for d in eligible],
            image_size,
        )
        if not np.isfinite(matrix).all():
            return
        with torch.inference_mode():
            nonplayer = (
                self.model(torch.from_numpy((matrix - self.mean) / self.std)).sigmoid().numpy().ravel()
            )
        for d, score in zip(eligible, nonplayer):
            d.role_context_model_id = self.spec["model_id"]
            d.role_context_player_score = 1 - float(score)
            # A source-positive player near either goal is protected from this
            # negative refinement. Position alone never creates a player label.
            end = self.spec.get("protect_end_fraction", 0.08)
            if (
                d.semantic_class == "player"
                and score >= self.spec["nonplayer_threshold"]
                and not (d.player_kind == "goalkeeper" and d.player_kind_source == "detector")
                and end < d.field_position[0] < 1 - end
            ):
                d.semantic_class = "referee" if d.role_probabilities[1] >= 0.5 else "person"
                d.role_decision, d.track_id = "pitch_context_nonplayer", None
            elif d.semantic_class != "player" and 1 - score >= self.spec["player_threshold"]:
                source_referee = (d.detector_semantic_class == "referee" and d.confidence >= 0.25) or (
                    d.role_evidence
                    and d.role_evidence["semantic_class"] == "referee"
                    and d.role_evidence["confidence"] >= 0.5
                )
                if not source_referee:
                    d.semantic_class = "player"
                    d.role_decision = "pitch_context_player"
