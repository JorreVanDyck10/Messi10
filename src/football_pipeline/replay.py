from __future__ import annotations

import json

from .contracts import Detection, PipelineError, VideoMetadata


def replay_detections(stream, frame_index: int, video: VideoMetadata) -> list[Detection]:
    try:
        record = json.loads(stream.readline())
        if (
            record["frame_index"] != frame_index
            or record["image_size"] != list(video.size)
            or abs(record["timestamp_s"] - frame_index / video.fps) > 1e-6
        ):
            raise PipelineError("Replay heeft een afwijkende framevolgorde, schaal of tijdlijn.")
        detections = [Detection.from_dict(d) for d in record["detections"]]
        for detection in detections:
            # Role/team appearance is model output; field positions and track IDs must be recomputed.
            detection.track_id, detection.field_position = None, None
            detection.projection_status = "not_projected"
        return detections
    except (ValueError, KeyError, TypeError) as exc:
        raise PipelineError(f"Ongeldig replayframe {frame_index}: {exc}") from exc
