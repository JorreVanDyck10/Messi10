"""Keep model roles separate from geometric field membership.

Being on grass never turns a generic person, steward or official into a player.
These rules filter predictions; they cannot repair an incorrect model class.
"""

from collections import Counter

import numpy as np

from .contracts import Detection, FrameRecord
from .geometry import valid_box

GROUND_ROLES = frozenset(
    {"player", "referee", "assistant_referee", "steward", "spectator", "staff", "person"}
)
DISPLAY_CONFIDENCE = 0.25
PLAYER_POLICY = {
    "version": 1,
    "role": "player",
    "position": "bottom_center_inside_normalized_field",
    "requires_valid_current_calibration": True,
    "display_confidence": DISPLAY_CONFIDENCE,
    "include_matched_low_confidence": True,
    "meaning": "current_detected_players_not_unique_people_or_verified_match_roster",
}


def player_exclusion_reason(detection: Detection, image_size: tuple[int, int]) -> str | None:
    if detection.semantic_class != "player":
        return "not_player"
    return field_exclusion_reason(detection, image_size)


def field_exclusion_reason(detection: Detection, image_size: tuple[int, int]) -> str | None:
    if not valid_box(detection, image_size):
        return "invalid_box"
    if detection.projection_status != "valid":
        return detection.projection_status
    position = np.asarray(detection.field_position, dtype=float)
    if position.shape != (2,) or not np.isfinite(position).all():
        return "invalid_field_position"
    if (position < -1e-9).any() or (position > 1 + 1e-9).any():
        return "outside_field"
    return None


def visible_detection(detection: Detection, confidence: float = DISPLAY_CONFIDENCE) -> bool:
    return detection.confidence >= confidence or detection.track_id is not None


def field_available(record: FrameRecord) -> bool:
    # Manual records are produced only after validating the fixed calibration.
    return record.calibration is None or record.calibration.get("status") == "valid"


def count_exclusion_reason(
    record: FrameRecord, detection: Detection, confidence=DISPLAY_CONFIDENCE
) -> str | None:
    reason = player_exclusion_reason(detection, record.image_size)
    if reason is not None:
        return reason
    if not record.player_model_available:
        return "player_model_unavailable"
    if not field_available(record):
        return "calibration_unavailable"
    if not visible_detection(detection, confidence):
        return "below_display_confidence"
    return None


def counted_as_player(record: FrameRecord, detection: Detection, confidence=DISPLAY_CONFIDENCE) -> bool:
    return count_exclusion_reason(record, detection, confidence) is None


def player_summary(record: FrameRecord, confidence=DISPLAY_CONFIDENCE) -> dict:
    visible = [
        d for d in record.detections if valid_box(d, record.image_size) and visible_detection(d, confidence)
    ]
    players = [d for d in visible if d.semantic_class == "player"]
    reasons = Counter(player_exclusion_reason(d, record.image_size) for d in players)
    available = field_available(record) and record.player_model_available
    return {
        "status": "player_model_unavailable"
        if not record.player_model_available
        else "available"
        if available
        else "field_unavailable",
        "on_field": sum(counted_as_player(record, d, confidence) for d in players) if available else None,
        "by_team": {
            team: sum(
                counted_as_player(record, d, confidence)
                and (d.team_id if d.team_id in {"A", "B"} else "unknown") == team
                for d in players
            )
            if available
            else None
            for team in ("A", "B", "unknown")
        },
        "visible_player_candidates": len(players),
        "outside_field": reasons["outside_field"] if available else None,
        "unlocated": sum(n for reason, n in reasons.items() if reason not in {None, "outside_field"})
        if available
        else len(players),
        "other_roles": dict(Counter(d.semantic_class for d in visible if d.semantic_class != "player")),
        "persons_on_field": sum(
            field_exclusion_reason(d, record.image_size) is None
            for d in visible
            if d.semantic_class == "person"
        )
        if field_available(record)
        else None,
        "visible_person_candidates": sum(d.semantic_class == "person" for d in visible),
        "display_confidence": confidence,
        "include_matched_low_confidence": True,
    }
