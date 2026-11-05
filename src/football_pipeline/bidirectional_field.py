"""Experimental offline backfill from a future trusted calibration, without refitting."""

import copy

from .contracts import PipelineError
from .field_motion import CameraCalibration, validate_settings


def backward_backfill(direct, forward, reverse_frames, fps, settings):
    """Keep every forward-valid record and fill gaps only through bounded reverse flow.

    reverse_frames yields (native index, BGR image) in exact descending order.
    Direct recognition remains the only source of anchors in either direction.
    This is an offline operation; it never assigns an anchor beyond maximum_age_s.
    """
    settings = validate_settings(settings)
    if len(direct) != len(forward) or not direct:
        raise PipelineError("Backfill requires matching nonempty calibration timelines")
    result = copy.deepcopy(forward)
    reverse = CameraCalibration(fps, settings)
    count = len(direct)
    consumed = 0
    for step, (index, frame) in enumerate(reverse_frames):
        if index != count - 1 - step:
            raise PipelineError("Reverse calibration requires every source frame in descending order")
        state = reverse.update(frame, copy.deepcopy(direct[index]), step)
        consumed += 1
        if (
            forward[index]["status"] == "valid"
            or state["status"] != "valid"
            or state.get("source") != "tracked"
            or forward[index]["status"]
            in {"invalid_observation", "degenerate_geometry", "orientation_unknown", "camera_cut"}
        ):
            continue
        anchor = count - 1 - state["reference_frame"]
        if not index < anchor < count or (anchor - index) / fps > settings["maximum_age_s"]:
            raise PipelineError("Backward calibration exceeded its trusted-anchor bound")
        if direct[anchor]["status"] != "valid":
            raise PipelineError("A propagated calibration cannot become a new anchor")
        state.update(
            frame_index=index,
            reference_frame=anchor,
            age_s=(anchor - index) / fps,
            source="tracked_backward",
            temporal_direction="backward",
            forward_status=forward[index]["status"],
        )
        result[index] = state
    if consumed != count:
        raise PipelineError("Incomplete reverse frame timeline")
    return result
