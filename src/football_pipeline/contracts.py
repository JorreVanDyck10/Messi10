from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


class PipelineError(ValueError):
    """An actionable input, model or processing failure."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def digest_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def read_json(path: str | Path) -> dict:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        if not isinstance(value, dict):
            raise PipelineError("Verwacht een JSON-object met benoemde velden.")
        return value
    except (OSError, ValueError) as exc:
        raise PipelineError(f"Kan JSON-bestand niet lezen: {path}: {exc}") from exc


def write_json(path: str | Path, value: Any) -> None:
    path = Path(path)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    atomic_replace(temporary, path)


def atomic_replace(temporary: Path, path: Path) -> None:
    """Publish a completed file while tolerating short Windows reader locks."""
    for attempt in range(12):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 11:
                raise
            # Windows readers/antivirus can briefly deny replacement even after
            # the writer has closed. Keep the old complete JSON until success.
            time.sleep(0.05 * (attempt + 1))


@dataclass
class VideoMetadata:
    path: str
    sha256: str
    width: int
    height: int
    fps_num: int
    fps_den: int
    frame_count: int
    codec: str
    duration_s: float

    @property
    def fps(self) -> float:
        return self.fps_num / self.fps_den

    @property
    def size(self) -> tuple[int, int]:
        return self.width, self.height


@dataclass
class Detection:
    detection_id: str
    model_id: str
    source_class_id: int
    semantic_class: str
    bbox_xyxy: list[float]
    confidence: float
    track_id: int | None = None
    field_position: list[float] | None = None
    projection_status: str = "not_projected"
    shirt_color_lab: list[float] | None = None
    team_id: str | None = None
    team_status: str = "unknown"
    team_match_score: float | None = None
    team_source: str | None = None
    detector_semantic_class: str | None = None
    role_model_id: str | None = None
    role_confidence: float | None = None
    role_class_id: int | None = None
    team_confidence: float | None = None
    team_method: str | None = None
    team_class_id: int | None = None
    appearance_team: dict | None = None
    role_decision: str | None = None
    team_embedding: list[float] | None = None
    player_kind: str | None = None
    role_evidence: dict | None = None

    @classmethod
    def from_dict(cls, value: dict) -> Detection:
        # These fields are derived for export, never authoritative detection inputs.
        derived = {"counted_as_player", "player_exclusion_reason"}
        return cls(**{key: item for key, item in value.items() if key not in derived})


@dataclass
class FrameRecord:
    frame_index: int
    timestamp_s: float
    image_size: tuple[int, int]
    detections: list[Detection] = field(default_factory=list)
    calibration: dict | None = None
    player_model_available: bool = True
    tracking: dict | None = None
    team_context: dict | None = None
    analysis_scope: str = "all_participants"

    @classmethod
    def from_dict(cls, value: dict) -> FrameRecord:
        return cls(
            frame_index=value["frame_index"],
            timestamp_s=value["timestamp_s"],
            image_size=tuple(value["image_size"]),
            detections=[Detection.from_dict(d) for d in value["detections"]],
            calibration=value.get("calibration"),
            player_model_available=value.get("player_model_available", True),
            tracking=value.get("tracking"),
            team_context=value.get("team_context"),
            analysis_scope=value.get("analysis_scope", "all_participants"),
        )

    def to_dict(self) -> dict:
        from .participants import count_exclusion_reason, counted_as_player, player_summary

        result = asdict(self)
        if self.calibration is None:
            result.pop("calibration")
        if self.tracking is None:
            result.pop("tracking")
        if self.team_context is None:
            result.pop("team_context")
        result["player_summary"] = player_summary(self)
        for detection, serialized in zip(self.detections, result["detections"]):
            serialized["counted_as_player"] = counted_as_player(self, detection)
            serialized["player_exclusion_reason"] = count_exclusion_reason(self, detection)
        return result


@dataclass
class RunResult:
    directory: Path
    manifest: dict
    reused: bool = False

    @property
    def video_path(self) -> Path:
        return self.directory / "samengestelde_video.mp4"
