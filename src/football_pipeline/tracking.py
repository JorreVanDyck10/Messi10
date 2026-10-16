from __future__ import annotations

from collections import deque
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import yaml

from .contracts import Detection, PipelineError
from .participants import player_exclusion_reason


def load_tracker_config(path: str | Path) -> dict:
    try:
        config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if config["tracker_type"] != "bytetrack":
            raise PipelineError("Kies expliciet ByteTrack.")
        for name in ("track_high_thresh", "track_low_thresh", "new_track_thresh", "match_thresh"):
            if not np.isfinite(config[name]) or not 0 <= config[name] <= 1:
                raise PipelineError(f"Ongeldige trackinginstelling: {name}.")
        if config["track_low_thresh"] >= config["track_high_thresh"]:
            raise PipelineError("track_low_thresh moet lager zijn dan track_high_thresh.")
        if not isinstance(config["track_buffer"], int) or config["track_buffer"] < 1:
            raise PipelineError("track_buffer moet een positief aantal updates zijn.")
        if not isinstance(config["fuse_score"], bool):
            raise PipelineError("fuse_score moet een boolean zijn.")
        return config
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        raise PipelineError(f"Ongeldige trackerconfiguratie: {exc}") from exc


class ByteTrackAdapter:
    def __init__(self, config: dict, fps: float):
        from ultralytics.trackers.byte_tracker import BYTETracker

        class SourceIndexedTracker(BYTETracker):
            def init_track(self, results, features=None):
                tracks = super().init_track(results, features)
                # 8.3.221 numbers each confidence partition from zero. Preserve
                # the input detection index through both association stages.
                indices = results.source_indices
                if len(tracks) != len(indices):
                    raise PipelineError("ByteTrack initialisatie verloor detectie-indices.")
                for track, index in zip(tracks, indices):
                    track.idx = int(index)
                return tracks

        self.legacy_partition_indices = version("ultralytics") == "8.3.221"
        tracker_class = SourceIndexedTracker if self.legacy_partition_indices else BYTETracker
        self.tracker = tracker_class(SimpleNamespace(**config))
        self.fps = fps
        self.last_frame = -1
        # Guard the pinned API rather than silently assuming historical FPS scaling.
        effective = getattr(self.tracker, "max_frames_lost", None)
        if effective is None:
            effective = getattr(self.tracker, "max_time_lost", None)
        if effective is None:
            raise PipelineError("Onbekende ByteTrack-buffer-API; voer de compatibiliteitstest uit.")
        self.info = {
            "effective_buffer_updates": int(effective),
            "effective_buffer_seconds": effective / fps,
            "fps_scaling": "one_update_per_source_frame",
            "index_compatibility": "8.3.221_source_indices" if self.legacy_partition_indices else "native",
        }

    def update(self, detections: list[Detection], frame_index: int, image_size: tuple[int, int]) -> None:
        from ultralytics.engine.results import Boxes

        if frame_index != self.last_frame + 1:
            raise PipelineError("ByteTrack vereist opeenvolgende frames vanaf index 0.")
        self.last_frame = frame_index
        for detection in detections:
            detection.track_id = None
        players = [d for d in detections if player_exclusion_reason(d, image_size) is None]
        # A single tracker class prevents goalkeeper/player subclass switching.
        raw = np.array([[*d.bbox_xyxy, d.confidence, 0] for d in players], dtype=np.float32).reshape(-1, 6)
        boxes = Boxes(raw, (image_size[1], image_size[0]))
        tracks = self.tracker.update(_IndexedBoxes(boxes) if self.legacy_partition_indices else boxes)
        seen = set()
        for row in tracks:
            if len(row) != 8:
                raise PipelineError("ByteTrack-uitvoerformaat gewijzigd; indexcompatibiliteit controleren.")
            index = int(row[7])
            if row[7] != index or not 0 <= index < len(players) or index in seen:
                raise PipelineError("ByteTrack gaf geen unieke actuele detectie-index terug.")
            seen.add(index)
            players[index].track_id = int(row[4])


class _IndexedBoxes:
    """Carry source indices when ByteTrack slices high/low confidence subsets."""

    def __init__(self, boxes, indices=None):
        self.boxes = boxes
        self.source_indices = np.arange(len(boxes)) if indices is None else indices

    def __len__(self):
        return len(self.boxes)

    def __getitem__(self, item):
        return _IndexedBoxes(self.boxes[item], self.source_indices[item])

    def __getattr__(self, name):
        return getattr(self.boxes, name)


class Trajectories:
    def __init__(self, fps: float, seconds: float = 5.0):
        self.window = max(1, round(fps * seconds))
        self.points: dict[int, deque] = {}

    def update(self, detections: list[Detection], frame_index: int) -> None:
        cutoff = frame_index - self.window + 1
        for key in list(self.points):
            while self.points[key] and self.points[key][0][0] < cutoff:
                self.points[key].popleft()
            if not self.points[key]:
                del self.points[key]
        for detection in detections:
            if detection.track_id is not None and detection.field_position is not None:
                self.points.setdefault(detection.track_id, deque()).append(
                    (frame_index, *detection.field_position)
                )

    def segments(self, track_id: int) -> list[tuple]:
        history = list(self.points.get(track_id, []))
        return [(a, b) for a, b in zip(history, history[1:]) if b[0] == a[0] + 1]
