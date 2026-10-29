"""Leert shirtkenmerken uit paren van hetzelfde of verschillende teams; teamnamen blijven wedstrijdafhankelijk."""

from __future__ import annotations

import numpy as np

from .appearance import backbone, crop_tensor
from .contracts import PipelineError
from .video_teams import kit_feature


def projection_head():
    import torch

    return torch.nn.Sequential(torch.nn.Linear(608, 128), torch.nn.ReLU(), torch.nn.Linear(128, 32))


class KitEmbedding:
    def __init__(self, spec):
        import torch

        self.device = str(spec.get("device", "cpu"))
        if self.device.isdigit():
            self.device = "cuda:" + self.device
        state = torch.load(spec["weights"], map_location="cpu", weights_only=True)
        self.metric_weights = None
        if state.get("format") == "broadcast-kit-hist-v2":
            weights = state["metric_weights"].numpy()
            if weights.shape != (32,) or not np.isfinite(weights).all() or (weights <= 0).any():
                raise PipelineError("Ongeldige gewichten voor het shirtmodel.")
            self.metric_weights = weights
            return
        if state.get("format") != "broadcast-kit-v1":
            raise PipelineError("Onbekend teammodel.")
        self.encoder = backbone().to(self.device).eval()
        self.encoder.load_state_dict(state["backbone"])
        self.head = projection_head().to(self.device).eval()
        self.head.load_state_dict(state["projection"])
        self.keeper = torch.nn.Linear(608, 2).to(self.device).eval()
        self.keeper.load_state_dict(state["keeper"])
        self.mean, self.std = state["mean"].to(self.device), state["std"].to(self.device)

    def update(self, frame, detections):
        import torch

        eligible = (
            {"player", "referee", "person"}
            if getattr(self, "metric_weights", None) is not None
            else {"player"}
        )
        players = [
            d
            for d in detections
            if d.semantic_class in eligible
            and d.projection_status == "valid"
            and d.bbox_xyxy[2] - d.bbox_xyxy[0] >= 4
            and d.bbox_xyxy[3] - d.bbox_xyxy[1] >= 12
        ]
        if getattr(self, "metric_weights", None) is not None:
            for d in players:
                vector = kit_feature(frame, d.bbox_xyxy) * self.metric_weights
                d.team_embedding = (vector / max(1e-9, np.linalg.norm(vector))).tolist()
                # A keeper-color guess must not erase an entire unseen kit.
                # Distinct rare kits remain unknown through the distance gate.
                if d.player_kind_source != "detector":
                    d.player_kind, d.player_kind_source = None, None
            return
        for start in range(0, len(players), 32):
            batch = players[start : start + 32]
            pixels = torch.stack([crop_tensor(frame, d.bbox_xyxy) for d in batch]).to(self.device)
            colours = torch.from_numpy(np.stack([kit_feature(frame, d.bbox_xyxy) for d in batch])).to(
                self.device
            )
            with torch.inference_mode():
                raw = torch.cat([self.encoder(pixels), colours], 1)
                features = (raw - self.mean) / self.std
                embeddings = torch.nn.functional.normalize(self.head(features), dim=1).cpu().numpy()
                keepers = self.keeper(features).softmax(1)[:, 1].cpu().numpy()
            for d, embedding, keeper in zip(batch, embeddings, keepers):
                d.team_embedding = embedding.tolist()
                d.player_kind = "goalkeeper" if keeper >= 0.8 else "outfield"
                d.player_kind_source = "appearance_keeper_head"


def dominant_teams(vectors, *, radius=0.32, separation=0.4):
    """Two supported appearance modes, resistant to isolated goalkeeper kits.

    Cosine distance is used for normalized embeddings. A/B ordering is stable
    for the same clip and never means a fixed club across different matches.
    """
    points = np.asarray(vectors, np.float64)
    if points.ndim != 2 or len(points) < 4 or not np.isfinite(points).all():
        return None
    points /= np.maximum(np.linalg.norm(points, axis=1, keepdims=True), 1e-9)
    distances = np.clip(1 - points @ points.T, 0, 2)
    remaining, centers, groups = np.ones(len(points), bool), [], []
    for _ in range(2):
        support = (distances <= radius) & remaining[None, :]
        sizes = support.sum(1)
        sizes[~remaining] = 0
        chosen = int(sizes.argmax())
        if sizes[chosen] < 2:
            return None
        members = support[chosen]
        center = points[members].mean(0)
        center /= max(1e-9, np.linalg.norm(center))
        centers.append(center)
        groups.append(np.flatnonzero(members))
        remaining &= (1 - points @ center) >= separation
    if 1 - np.dot(*centers) < separation:
        return None
    order = sorted(range(2), key=lambda i: tuple(np.round(centers[i], 6)))
    return [centers[i] for i in order], [groups[i] for i in order]


class PitchTeamSamples:
    """Sample eligible players directly; short tracking IDs do not discard a kit."""

    def __init__(self, settings, fps):
        self.settings, self.fps, self.samples = settings, fps, []

    def add(self, detection, index):
        from .contracts import digest_json

        d = detection
        if (
            d.semantic_class != "player"
            or d.projection_status != "valid"
            or d.confidence < 0.25
            or d.team_embedding is None
            or d.player_kind == "goalkeeper"
            or index % max(1, round(self.fps / self.settings["sample_hz"]))
        ):
            return
        priority = digest_json([index, d.detection_id])
        self.samples.append((priority, index, d.team_embedding, d.shirt_color_lab))
        if len(self.samples) > self.settings["max_samples"] * 2:
            self.samples = sorted(self.samples)[: self.settings["max_samples"]]

    def fit(self):
        from .teams import lab_to_hex

        samples = sorted(self.samples)[: self.settings["max_samples"]]
        teams = {
            k: {
                "name": f"Team {k}",
                "shirt_color": None,
                "display_color": color,
                "prototype_lab": None,
                "prototype_embedding": None,
            }
            for k, color in zip(("A", "B"), ("#ef6262", "#5a9fee"))
        }
        result = {
            "schema_version": 1,
            "status": "insufficient_groups",
            "settings": self.settings,
            "analysis_scope": "on_pitch_players",
            "teams": teams,
            "sample_count": len(samples),
            "representatives": len(samples),
            "score_definition": "1 minus cosine distance; separation margin; not a probability",
        }
        fitted = dominant_teams(
            [s[2] for s in samples],
            radius=self.settings["embedding_radius"],
            separation=self.settings["embedding_separation"],
        )
        if fitted is None:
            return result
        centers, groups = fitted
        for team, center, members in zip(teams.values(), centers, groups):
            if len({samples[i][1] for i in members}) < self.settings["min_cluster_frames"]:
                result["status"] = "insufficient_frames"
                return result
            labs = [samples[i][3] for i in members if samples[i][3] is not None]
            lab = np.median(labs, axis=0).tolist() if labs else [50.0, 0.0, 0.0]
            team.update(prototype_lab=lab, prototype_embedding=center.tolist(), shirt_color=lab_to_hex(lab))
        result["status"] = "available"
        return result


def embedding_candidate(detection, model):
    if (
        detection.team_embedding is None
        or detection.player_kind == "goalkeeper"
        or detection.projection_status != "valid"
        or model["status"] != "available"
    ):
        return None, None
    points = np.asarray(detection.team_embedding, float)
    if points.shape != (32,) or not np.isfinite(points).all() or np.linalg.norm(points) < 1e-9:
        return None, None
    points /= np.linalg.norm(points)
    distances = [
        float(np.clip(1 - np.dot(points, t["prototype_embedding"]), 0, 2)) for t in model["teams"].values()
    ]
    first, second = np.argsort(distances)
    settings = model["settings"]
    score = max(0.0, 1 - distances[first])
    if (
        distances[first] <= settings["embedding_max_distance"]
        and distances[second] - distances[first] >= settings["embedding_margin"]
    ):
        return list(model["teams"])[first], score
    return None, score
