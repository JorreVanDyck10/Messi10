"""Supervised crop roles and match-specific team appearance, independent of pitch position."""

from pathlib import Path

import cv2
import numpy as np

from .contracts import PipelineError, sha256_file
from .geometry import valid_box

ROLE_NAMES = ["player", "referee", "assistant_referee", "steward", "spectator", "person"]
PITCH_ROLE_NAMES = ["player", "referee", "person"]
TEAM_NAMES = ["team_a", "team_b"]
INPUT_SIZE = (128, 192)  # width, height; retain the complete person rather than a central square crop


def crop_tensor(frame, box):
    import torch

    height, width = frame.shape[:2]
    x1, y1, x2, y2 = box
    dx, dy = (x2 - x1) * 0.08, (y2 - y1) * 0.04
    left, top = max(0, int(x1 - dx)), max(0, int(y1 - dy))
    right, bottom = min(width, int(np.ceil(x2 + dx))), min(height, int(np.ceil(y2 + dy)))
    if right <= left or bottom <= top:
        raise PipelineError("Lege persoonsuitsnede voor rolherkenning.")
    rgb = cv2.cvtColor(cv2.resize(frame[top:bottom, left:right], INPUT_SIZE), cv2.COLOR_BGR2RGB)
    tensor = torch.from_numpy(rgb.copy()).permute(2, 0, 1).float() / 255
    return (tensor - torch.tensor([0.485, 0.456, 0.406])[:, None, None]) / torch.tensor(
        [0.229, 0.224, 0.225]
    )[:, None, None]


def jersey_feature(frame, box, *, remove_turf=False):
    """Central upper torso colour; no pitch-coordinate or person-location features."""
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    crop = frame[
        max(0, int(y1 + h * 0.18)) : max(1, int(y1 + h * 0.57)),
        max(0, int(x1 + w * 0.2)) : max(1, int(x2 - w * 0.2)),
    ]
    if crop.size == 0:
        return np.zeros(32, np.float32)
    hsv = cv2.cvtColor(cv2.resize(crop, (16, 24)), cv2.COLOR_BGR2HSV)
    # Keep high-visibility yellow/green clothing: it overlaps turf in HSV hue.
    # The tight central torso crop limits background without deleting a role cue.
    pixels = hsv.reshape(-1, 3)
    if remove_turf:
        # Only the unsupervised player-kit stage removes turf. Role cues keep fluorescent clothing.
        keep = ~((pixels[:, 0] > 30) & (pixels[:, 0] < 90) & (pixels[:, 1] > 55))
        if not keep.any():
            return np.zeros(32, np.float32)
        pixels = pixels[keep]
    hist = [
        np.histogram(pixels[:, i], bins=b, range=(0, limit))[0]
        for i, b, limit in [(0, 16, 180), (1, 8, 256), (2, 8, 256)]
    ]
    return np.concatenate([v / max(1, v.sum()) for v in hist]).astype(np.float32)


def backbone(pretrained=False):
    import torch
    from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small

    model = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.IMAGENET1K_V1 if pretrained else None)
    return torch.nn.Sequential(model.features, model.avgpool, torch.nn.Flatten())


class AppearanceClassifier:
    def __init__(self, spec):
        import torch

        path = Path(spec["weights"])
        if not path.is_file() or sha256_file(path) != spec["weights_sha256"]:
            raise PipelineError("Rol-/teamgewichten ontbreken of hun hash wijkt af.")
        self.device = spec.get("device", "cpu")
        if self.device.isdigit():
            self.device = "cuda:" + self.device
        state = torch.load(path, map_location="cpu", weights_only=True)
        if state["role_names"] not in (ROLE_NAMES, PITCH_ROLE_NAMES) or state["team_names"] != TEAM_NAMES:
            raise PipelineError("Onverwachte uitvoerklassen van de rol-/teamclassifier.")
        self.role_names = state["role_names"]
        if spec.get("role_names", self.role_names) != self.role_names:
            raise PipelineError("Rolklassen in profiel en checkpoint verschillen.")
        self.backbone = backbone().to(self.device).eval()
        self.backbone.load_state_dict(state["backbone"])
        self.role_head = torch.nn.Linear(608, len(self.role_names)).to(self.device).eval()
        self.team_head = torch.nn.Linear(608, 2).to(self.device).eval()
        self.role_head.load_state_dict(state["role_head"])
        self.team_head.load_state_dict(state["team_head"])
        self.mean = state["mean"].to(self.device)
        self.std = state["std"].to(self.device)
        self.colour_scale = float(state.get("role_colour_scale", 1.0))
        self.team_video_hashes = set(state["team_video_hashes"])
        self.model_id = spec["model_id"]
        self.threshold = float(spec.get("role_confidence", 0.65))
        self.team_threshold = float(spec.get("team_confidence", 0.65))
        self.role_policy = spec.get("role_policy", "classifier")
        from .teams import VideoTeams

        self.video_teams = VideoTeams()

    def classify(self, frame, detections, video_hash):
        import torch

        people = [
            d
            for d in detections
            if d.semantic_class in {"player", "referee", "person"}
            and valid_box(d, (frame.shape[1], frame.shape[0]))
        ]
        for start in range(0, len(people), 32):
            batch = people[start : start + 32]
            pixels = torch.stack([crop_tensor(frame, d.bbox_xyxy) for d in batch]).to(self.device)
            colours = torch.from_numpy(np.stack([jersey_feature(frame, d.bbox_xyxy) for d in batch])).to(
                self.device
            )
            with torch.inference_mode():
                features = torch.cat([self.backbone(pixels), colours], 1)
                context = None
                if getattr(self, "context_projection", None) is not None:
                    mean, projection = self.context_projection
                    context = (
                        torch.nn.functional.normalize((features[:, :576] - mean) @ projection, dim=1)
                        .cpu()
                        .numpy()
                    )
                features = (features - self.mean) / self.std
                role_features = features.clone()
                role_features[:, 576:] *= self.colour_scale
                roles = self.role_head(role_features).softmax(1).cpu().numpy()
                teams = self.team_head(features).softmax(1).cpu().numpy()
            for position, (d, role, team) in enumerate(zip(batch, roles, teams)):
                d.role_probabilities = role.tolist()
                if context is not None:
                    d.context_embedding = context[position].tolist()
                d.detector_semantic_class = d.semantic_class
                d.role_model_id = self.model_id
                d.role_confidence = float(role.max())
                d.role_class_id = int(role.argmax())
                d.semantic_class = (
                    self.role_names[int(role.argmax())] if role.max() >= self.threshold else "person"
                )
                if self.role_policy == "preserve_detector_players":
                    source_role, source_confidence = d.detector_semantic_class, d.confidence
                    if d.role_evidence and d.role_evidence["confidence"] >= 0.5:
                        source_role = d.role_evidence["semantic_class"]
                        source_confidence = d.role_evidence["confidence"]
                    # A specialist's actual player class is direct role evidence.
                    # A generic person still needs a learned positive player label.
                    if source_role == "player" and source_confidence >= 0.25:
                        d.semantic_class = "player"
                        d.role_decision = (
                            "matched_specialist_player" if d.role_evidence else "specialist_player_preserved"
                        )
                    elif source_role == "referee" and source_confidence >= 0.25:
                        positive_player = int(role.argmax()) == 0 and role.max() >= 0.95
                        d.semantic_class = "player" if positive_player else "referee"
                        d.role_decision = (
                            "strong_player_evidence_refines_specialist_referee"
                            if positive_player
                            else "specialist_referee_preserved"
                        )
                    else:
                        d.role_decision = "crop_classifier"
                d.team_id, d.team_confidence = None, None
                d.team_method = None
                d.team_class_id = None
                if d.semantic_class == "player" and video_hash in self.team_video_hashes:
                    d.team_confidence = float(team.max())
                    d.team_class_id = int(team.argmax())
                    if team.max() >= self.team_threshold:
                        d.team_id = TEAM_NAMES[int(team.argmax())]
                        d.team_method = "supervised_match"
        if video_hash not in self.team_video_hashes and self.role_policy == "classifier":
            self.video_teams.update(frame, detections)
