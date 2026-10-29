"""Verzamelt shirtwaarnemingen, zoekt twee wedstrijdgebonden teams en stabiliseert toekenningen over de tijd. Bij onvoldoende bewijs blijft het team onbekend."""

from __future__ import annotations

import hashlib
import heapq
import os
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
from scipy.spatial.distance import cdist

from .contracts import Detection, PipelineError, read_json
from .geometry import valid_box
from .video_teams import VideoTeams as VideoTeams
from .video_teams import kit_feature as kit_feature

DEFAULT_TEAM_SETTINGS = {
    "schema_version": 1,
    "method": "torso_lab_dominant_modes_v1",
    "sample_hz": 5.0,
    "max_samples": 2048,
    "min_track_samples": 3,
    "min_cluster_members": 2,
    "min_cluster_frames": 3,
    "min_box_width": 10,
    "min_box_height": 24,
    "background_distance": 8.0,
    "min_foreground_fraction": 0.3,
    "max_color_spread": 24.0,
    "cluster_radius": 14.0,
    "min_separation": 28.0,
    "max_match_distance": 24.0,
    "min_distance_margin": 8.0,
    "confirmation_samples": 3,
    "switch_samples": 5,
    "history_seconds": 1.2,
    "embedding_radius": 0.32,
    "embedding_separation": 0.4,
    "embedding_max_distance": 0.45,
    "embedding_margin": 0.18,
    "kit_player_recovery": False,
    "referee_kit_consensus": False,
}
TEAM_IDS = ("A", "B")
UNKNOWN_COLOR = "#aab2bd"


def configured_team_path(models):
    from .video import ROOT

    default = "teams-broadcast.json" if models.get("kit_embedding") else "teams.json"
    return Path(os.environ.get("FOOTBALL_TEAMS", ROOT / "configs" / default))


def load_team_settings(path: str | Path | dict) -> dict:
    value = read_json(path) if not isinstance(path, dict) else path
    settings = {**DEFAULT_TEAM_SETTINGS, **value}
    if set(value) - set(DEFAULT_TEAM_SETTINGS) or settings["schema_version"] != 1:
        raise PipelineError("Onbekend teamprofiel of onbekende teaminstellingen.")
    if settings["method"] not in {DEFAULT_TEAM_SETTINGS["method"], "torso_embedding_dominant_modes_v1"}:
        raise PipelineError("Onbekende methode voor teamherkenning.")
    integers = {
        "max_samples",
        "min_track_samples",
        "min_cluster_members",
        "min_cluster_frames",
        "min_box_width",
        "min_box_height",
        "confirmation_samples",
        "switch_samples",
    }
    for key, number in settings.items():
        if key in {"method", "schema_version"}:
            continue
        if key in {"kit_player_recovery", "referee_kit_consensus"}:
            if type(number) is not bool:
                raise PipelineError(f"Ongeldig teambeleid: {key}.")
            continue
        if (
            isinstance(number, bool)
            or not isinstance(number, (float, int))
            or not np.isfinite(number)
            or number <= 0
            or (key in integers and not isinstance(number, int))
        ):
            raise PipelineError(f"Ongeldige teaminstelling: {key}.")
    if (
        settings["min_foreground_fraction"] > 1
        or settings["max_samples"] > 4096
        or settings["sample_hz"] > 30
        or settings["switch_samples"] < settings["confirmation_samples"]
    ):
        raise PipelineError("Ongeldige grenzen voor teamherkenning.")
    return settings


def rgb_to_lab(rgb) -> list[float]:
    return cv2.cvtColor(np.array([[rgb]], np.float32) / 255, cv2.COLOR_RGB2LAB)[0, 0].tolist()


def hex_rgb(value: str) -> list[int]:
    if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
        raise PipelineError("Gebruik een kleur in formaat #RRGGBB.")
    try:
        return [int(value[i : i + 2], 16) for i in (1, 3, 5)]
    except ValueError as exc:
        raise PipelineError("Gebruik een kleur in formaat #RRGGBB.") from exc


def lab_to_hex(lab) -> str:
    rgb = cv2.cvtColor(np.array([[lab]], np.float32), cv2.COLOR_LAB2RGB)[0, 0]
    return "#" + "".join(f"{v:02x}" for v in np.rint(np.clip(rgb, 0, 1) * 255).astype(int))


def shirt_color(frame: np.ndarray, detection: Detection, settings: dict) -> list[float] | None:
    height, width = frame.shape[:2]
    if detection.semantic_class != "player" or not valid_box(detection, (width, height)):
        return None
    x1, y1, x2, y2 = detection.bbox_xyxy
    bw, bh = x2 - x1, y2 - y1
    if bw < settings["min_box_width"] or bh < settings["min_box_height"]:
        return None
    # Avoid head, arms, shorts and the box edge. No global green/grass exclusion.
    a, b = int(x1 + bw * 0.25), int(x1 + bw * 0.75)
    c, d = int(y1 + bh * 0.20), int(y1 + bh * 0.50)
    crop = frame[c:d, a:b]
    if crop.size == 0:
        return None
    pixels = cv2.cvtColor(cv2.resize(crop, (12, 16)).astype(np.float32) / 255, cv2.COLOR_BGR2LAB)
    pixels = pixels.reshape(-1, 3)
    # Narrow strips outside the person estimate the local background distribution.
    strips = [
        frame[c:d, max(0, int(x1 - bw * 0.3)) : max(0, int(x1))],
        frame[c:d, min(width, int(x2)) : min(width, int(x2 + bw * 0.3))],
    ]
    background = [
        cv2.cvtColor(cv2.resize(strip, (4, 8)).astype(np.float32) / 255, cv2.COLOR_BGR2LAB).reshape(-1, 3)
        for strip in strips
        if strip.size
    ]
    if background:
        center = np.median(np.concatenate(background), axis=0)
        foreground = pixels[np.linalg.norm(pixels - center, axis=1) >= settings["background_distance"]]
        if len(foreground) / len(pixels) < settings["min_foreground_fraction"]:
            return None
        pixels = foreground
    center = np.median(pixels, axis=0)
    if np.median(np.linalg.norm(pixels - center, axis=1)) > settings["max_color_spread"]:
        return None
    return np.round(center, 4).tolist()


class TeamSamples:
    """Bounded deterministic reservoir across the entire clip, then one median per track."""

    def __init__(self, settings: dict, fps: float):
        self.settings = settings
        self.embedding_samples = None
        if settings["method"] == "torso_embedding_dominant_modes_v1":
            from .kit_embedding import PitchTeamSamples

            self.embedding_samples = PitchTeamSamples(settings, fps)
        self.step = max(1, round(fps / settings["sample_hz"]))
        self.samples = []
        self.sequence = 0

    def add(self, detection: Detection, index: int):
        if self.embedding_samples is not None:
            self.embedding_samples.add(detection, index)
            return
        if (
            index % self.step
            or detection.semantic_class != "player"
            or detection.confidence < 0.25
            or detection.shirt_color_lab is None
            or detection.projection_status not in {"valid", "calibration_unavailable"}
        ):
            return
        identity = f"{index}:{detection.detection_id}"
        priority = int.from_bytes(hashlib.sha256(identity.encode()).digest()[:8], "big")
        group = f"track:{detection.track_id}" if detection.track_id is not None else identity
        self.sequence += 1
        item = (-priority, self.sequence, group, detection.shirt_color_lab, index)
        if len(self.samples) < self.settings["max_samples"]:
            heapq.heappush(self.samples, item)
        elif item[0] > self.samples[0][0]:
            heapq.heapreplace(self.samples, item)

    def fit(self) -> dict:
        if self.embedding_samples is not None:
            return self.embedding_samples.fit()
        groups = defaultdict(list)
        group_frames = defaultdict(set)
        for _, _, group, color, index in sorted(self.samples, reverse=True):
            groups[group].append(color)
            group_frames[group].add(index)
        representatives = []
        representative_frames = []
        for group, colors in sorted(groups.items()):
            if group.startswith("track:") and len(colors) < self.settings["min_track_samples"]:
                continue
            center = np.median(colors, axis=0)
            if (
                np.median(np.linalg.norm(np.asarray(colors) - center, axis=1))
                <= self.settings["max_color_spread"]
            ):
                representatives.append(center)
                representative_frames.append(group_frames[group])
        points = np.array(representatives, float).reshape(-1, 3)
        teams = {
            key: {"name": f"Team {key}", "shirt_color": None, "display_color": color, "prototype_lab": None}
            for key, color in zip(TEAM_IDS, ("#ef6262", "#5a9fee"))
        }
        result = {
            "schema_version": 1,
            "status": "insufficient_samples",
            "settings": self.settings,
            "teams": teams,
            "sample_count": len(self.samples),
            "representatives": len(points),
            "score_definition": "max(0, 1 - CIELAB_distance / max_match_distance); assigned team or nearest if unknown; not a probability",
        }
        if len(points) < 2 * self.settings["min_cluster_members"]:
            return result
        # Find the two dominant compact modes instead of letting a lone goalkeeper
        # pull a two-means centroid away from an outfield shirt colour.
        distances = cdist(points, points)
        remaining = np.ones(len(points), bool)
        centers = []
        for _ in TEAM_IDS:
            support = (distances <= self.settings["cluster_radius"]) & remaining[None, :]
            sizes = support.sum(axis=1)
            sizes[~remaining] = 0
            chosen = int(np.argmax(sizes))
            if sizes[chosen] < self.settings["min_cluster_members"]:
                result["status"] = "insufficient_groups"
                return result
            members = support[chosen]
            observed_frames = set().union(*(representative_frames[i] for i in np.flatnonzero(members)))
            if len(observed_frames) < self.settings["min_cluster_frames"]:
                result["status"] = "insufficient_frames"
                return result
            center = np.median(points[members], axis=0)
            centers.append(center)
            remaining &= np.linalg.norm(points - center, axis=1) >= self.settings["min_separation"]
        if np.linalg.norm(centers[0] - centers[1]) < self.settings["min_separation"]:
            result["status"] = "ambiguous_colors"
            return result
        # A stable order prevents arbitrary A/B swaps between identical reruns.
        centers.sort(key=lambda c: tuple(c.tolist()))
        for key, center in zip(TEAM_IDS, centers):
            color = lab_to_hex(center)
            # Shirt prototypes and readable overlay colours are separate settings.
            teams[key].update(prototype_lab=center.tolist(), shirt_color=color)
        result["status"] = "available"
        return result


def validate_team_model(model: dict) -> None:
    if model.get("schema_version") != 1 or set(model.get("teams", {})) != set(TEAM_IDS):
        raise PipelineError("Ongeldig teammodel.")
    load_team_settings(model["settings"])
    if model.get("status") == "available" and any(
        t.get("prototype_lab") is None for t in model["teams"].values()
    ):
        raise PipelineError("Een beschikbaar teammodel vereist twee shirtprototypes.")
    if (
        model["settings"]["method"] == "torso_embedding_dominant_modes_v1"
        and model.get("status") == "available"
    ):
        for team in model["teams"].values():
            vector = np.asarray(team.get("prototype_embedding"), float)
            if (
                vector.shape != (32,)
                or not np.isfinite(vector).all()
                or not np.isclose(np.linalg.norm(vector), 1)
            ):
                raise PipelineError("Ongeldig teamprototype van het geleerde uiterlijkmodel.")
    for team in model["teams"].values():
        if not isinstance(team.get("name"), str) or not 1 <= len(team["name"].strip()) <= 40:
            raise PipelineError("Een teamnaam moet 1 tot 40 tekens bevatten.")
        hex_rgb(team["display_color"])
        prototype = team.get("prototype_lab")
        if prototype is not None:
            values = np.asarray(prototype, dtype=float)
            if (
                values.shape != (3,)
                or not np.isfinite(values).all()
                or not (0 <= values[0] <= 100 and (np.abs(values[1:]) <= 128).all())
            ):
                raise PipelineError("Ongeldig CIELAB-shirtprototype.")
        if team.get("shirt_color") is not None:
            hex_rgb(team["shirt_color"])


def team_context(model: dict) -> dict:
    return {
        "status": model["status"],
        "teams": {
            key: {"name": team["name"], "display_color": team["display_color"]}
            for key, team in model["teams"].items()
        },
    }


def refine_referee_consensus(detection, model):
    """Three independent learned/relative cues can reject a specialist false player.

    A crop alone cannot erase a whole unfamiliar team. Require referee crop
    probability >= .85, nonplayer context >= .75 and a kit cosine distance of
    at least .4 from both supported team prototypes. Restrict this additional
    rejection to the central 60% of the pitch to protect untyped goalkeepers.
    These fixed development thresholds are recorded in each decision's evidence.
    """
    from .kit_embedding import embedding_candidate

    d = detection
    if (
        d.semantic_class != "player"
        or d.projection_status != "valid"
        or d.confidence < 0.25
        or d.player_kind == "goalkeeper"
        or not d.role_context_model_id
        or d.role_context_player_score is None
        or d.role_context_player_score > 0.25
        or not d.role_probabilities
        or len(d.role_probabilities) != 3
        or d.role_probabilities[1] < 0.85
        or not d.field_position
        or not 0.2 < d.field_position[0] < 0.8
    ):
        return
    _, score = embedding_candidate(d, model)
    if score is None or score > 0.6:
        return
    d.semantic_class, d.track_id = "referee", None
    d.role_decision = "pitch_referee_consensus"
    vector = np.asarray(d.team_embedding, float)
    vector /= np.linalg.norm(vector)
    distance = min(
        float(np.clip(1 - vector @ t["prototype_embedding"], 0, 2)) for t in model["teams"].values()
    )
    d.role_consensus_evidence = {
        "rule": "referee_crop_context_kit_v1",
        "crop_referee_probability": d.role_probabilities[1],
        "context_nonplayer_probability": 1 - d.role_context_player_score,
        "nearest_team_cosine_distance": distance,
        "thresholds": {
            "crop_referee": 0.85,
            "context_nonplayer": 0.75,
            "kit_distance": 0.4,
            "protect_end_fraction": 0.2,
        },
    }


class TeamAssigner:
    def __init__(self, model: dict, fps: float, overrides: dict | None = None):
        validate_team_model(model)
        self.model, self.settings = model, model["settings"]
        self.overrides = overrides or {}
        self.history = {}
        self.fps = fps

    def update(self, detections: list[Detection], index: int):
        cutoff = index - max(1, round(self.fps * self.settings["history_seconds"]))
        self.history = {key: state for key, state in self.history.items() if state["last"] >= cutoff}
        for d in detections:
            embedding_method = self.settings["method"] == "torso_embedding_dominant_modes_v1"
            if (
                embedding_method
                and self.settings.get("kit_player_recovery")
                and d.role_decision not in {"pitch_context_nonplayer", "pitch_referee_consensus"}
                and d.semantic_class in {"person", "referee"}
                and d.detector_semantic_class == "person"
                and d.role_model_id
                and d.confidence >= 0.25
                and not (
                    d.role_evidence
                    and d.role_evidence["semantic_class"] == "referee"
                    and d.role_evidence["confidence"] >= 0.5
                )
            ):
                from .kit_embedding import embedding_candidate

                strict = {
                    **self.model,
                    "settings": {
                        **self.settings,
                        "embedding_max_distance": min(0.15, self.settings["embedding_max_distance"]),
                        "embedding_margin": max(0.15, self.settings["embedding_margin"]),
                    },
                }
                recovered, _ = embedding_candidate(d, strict)
                if recovered:
                    d.semantic_class = "player"
                    d.role_decision = "strong_kit_context_from_trained_player_prototypes"
            if embedding_method and self.settings.get("referee_kit_consensus"):
                refine_referee_consensus(d, self.model)
            # The optional appearance model's match-specific labels are separate
            # evidence from this run's colour clusters and manual corrections.
            if d.team_method is not None:
                d.appearance_team = {
                    "team_id": d.team_id,
                    "team_confidence": d.team_confidence,
                    "team_method": d.team_method,
                    "team_class_id": d.team_class_id,
                }
            d.team_confidence = d.team_method = d.team_class_id = None
            d.team_id = d.team_match_score = d.team_source = None
            d.team_status = "not_player" if d.semantic_class != "player" else "unknown"
            if d.semantic_class != "player":
                continue
            if (
                embedding_method or self.model.get("analysis_scope") == "on_pitch_players"
            ) and d.projection_status != "valid":
                continue
            key = str(d.track_id) if d.track_id is not None else None
            if key in self.overrides:
                d.team_id, d.team_source = self.overrides[key], "manual"
                d.team_status = "assigned" if d.team_id is not None else "unknown"
                continue
            if embedding_method and d.player_kind == "goalkeeper":
                continue
            candidate = None
            if embedding_method:
                from .kit_embedding import embedding_candidate

                candidate, d.team_match_score = embedding_candidate(d, self.model)
            elif d.shirt_color_lab is not None and self.model["status"] == "available":
                distances = [
                    np.linalg.norm(np.array(d.shirt_color_lab) - t["prototype_lab"])
                    for t in self.model["teams"].values()
                ]
                order = np.argsort(distances)
                nearest, other = distances[order[0]], distances[order[1]]
                d.team_match_score = max(0.0, 1 - float(nearest) / self.settings["max_match_distance"])
                if (
                    nearest <= self.settings["max_match_distance"]
                    and other - nearest >= self.settings["min_distance_margin"]
                ):
                    candidate = list(self.model["teams"])[order[0]]
            if key is None:
                d.team_id, d.team_source = candidate, "automatic" if candidate else None
            else:
                state = self.history.setdefault(key, {"team": None, "pending": None, "n": 0, "last": index})
                state["last"] = index
                if candidate is not None:
                    state["n"] = state["n"] + 1 if state["pending"] == candidate else 1
                    state["pending"] = candidate
                    required = (
                        self.settings["switch_samples"]
                        if state["team"]
                        else self.settings["confirmation_samples"]
                    )
                    if state["n"] >= required:
                        state["team"] = candidate
                else:
                    state["pending"], state["n"] = None, 0
                d.team_id = state["team"]
                d.team_source = (
                    ("automatic" if candidate == d.team_id else "track_history") if d.team_id else None
                )
            if d.team_id is not None:
                d.team_status = "assigned"
                if d.shirt_color_lab is not None and not embedding_method:
                    distance = np.linalg.norm(
                        np.array(d.shirt_color_lab) - self.model["teams"][d.team_id]["prototype_lab"]
                    )
                    d.team_match_score = max(0.0, 1 - float(distance) / self.settings["max_match_distance"])
