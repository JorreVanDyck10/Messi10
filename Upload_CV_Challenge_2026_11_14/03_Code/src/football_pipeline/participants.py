"""Houdt modelrollen, veldgeldigheid, zichtbaarheid en spelertelling gescheiden. Een persoon op het veld is niet automatisch een speler.


Being on grass never turns a generic person, steward or official into a player.
These rules filter predictions; they cannot repair an incorrect model class.
"""

from collections import Counter

import numpy as np

from .contracts import Detection, FrameRecord, PipelineError
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


def player_display_policy(confidence: float | None = None) -> dict:
    """Bewaar het oorspronkelijke beleid of maak een strikte spelersweergave zonder de tracker te wijzigen."""
    policy = dict(PLAYER_POLICY)
    if confidence is not None:
        if isinstance(confidence, bool) or not np.isfinite(confidence) or not 0 <= confidence <= 1:
            raise PipelineError("De spelersdrempel moet een eindig getal tussen 0 en 1 zijn.")
        policy.update(version=2, display_confidence=float(confidence), include_matched_low_confidence=False)
    return policy


def record_player_policy(record: FrameRecord, confidence: float | None = None) -> dict:
    """Lees het opgeslagen weergavebeleid; oude records behouden hun oorspronkelijke uitzonderingen."""
    policy = dict(record.player_policy or PLAYER_POLICY)
    if confidence is not None:
        policy["display_confidence"] = confidence
    return policy


def visible_in_record(record: FrameRecord, detection: Detection, confidence: float | None = None) -> bool:
    """Filter uitsluitend spelers met het runbeleid; andere rollen behouden hun oorspronkelijke weergave."""
    if detection.semantic_class != "player":
        return visible_detection(detection, DISPLAY_CONFIDENCE if confidence is None else confidence)
    policy = record_player_policy(record, confidence)
    return detection.confidence >= policy["display_confidence"] or (
        policy["include_matched_low_confidence"] and detection.track_id is not None
    )


def player_exclusion_reason(detection: Detection, image_size: tuple[int, int]) -> str | None:
    """Geef de reden waarom een detectie niet als geldige spelerwaarneming kan worden gebruikt, of None
    wanneer zij voldoet.
    """
    if detection.semantic_class != "player":
        return "not_player"
    return field_exclusion_reason(detection, image_size)


def field_exclusion_reason(detection: Detection, image_size: tuple[int, int]) -> str | None:
    """Toets box, onderrand en projectiestatus los van de voorspelde persoonsrol voor veldgerichte
    verwerking.
    """
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
    """Bepaal of de detectie de zichtbaarheid-/confidencegrens voor weergave haalt."""
    return detection.confidence >= confidence or detection.track_id is not None


def field_available(record: FrameRecord) -> bool:
    # Manual records are produced only after validating the fixed calibration.
    """Bepaal uit het framerecord of er op dit tijdstip bruikbare veldkalibratie bestaat."""
    return record.calibration is None or record.calibration.get("status") == "valid"


def count_exclusion_reason(record: FrameRecord, detection: Detection, confidence=None) -> str | None:
    """Pas de rol-, confidence- en veldvoorwaarden voor spelertelling toe en retourneer een expliciete
    uitsluitreden.
    """
    reason = player_exclusion_reason(detection, record.image_size)
    if reason is not None:
        return reason
    if not record.player_model_available:
        return "player_model_unavailable"
    if not field_available(record):
        return "calibration_unavailable"
    if not visible_in_record(record, detection, confidence):
        return "below_display_confidence"
    return None


def counted_as_player(record: FrameRecord, detection: Detection, confidence=None) -> bool:
    """Pas dezelfde telregels toe voor zowel de interface als opgeslagen analyses."""
    return count_exclusion_reason(record, detection, confidence) is None


def displayed_as_player(record: FrameRecord, detection: Detection, confidence=None) -> bool:
    """An observed image box survives field loss; known off-field boxes stay excluded."""
    if counted_as_player(record, detection, confidence):
        return True
    return (
        record.player_model_available
        and not field_available(record)
        and detection.semantic_class == "player"
        and valid_box(detection, record.image_size)
        and detection.projection_status == "calibration_unavailable"
        and visible_in_record(record, detection, confidence)
    )


def frame_diagnostics(record: FrameRecord, confidence=None) -> dict:
    """Describe retained evidence, not ground truth or pre-NMS detector recall."""
    detections = record.detections
    players = [d for d in detections if d.semantic_class == "player"]
    return {
        "version": 1,
        "retained_predictions": len(detections),
        "detector_player_evidence": sum(
            (d.detector_semantic_class or d.semantic_class) == "player"
            or (d.role_evidence or {}).get("semantic_class") == "player"
            for d in detections
        ),
        "role_players": len(players),
        "visible_player_candidates": sum(
            valid_box(d, record.image_size) and visible_in_record(record, d, confidence) for d in players
        ),
        "image_tracked_players": sum(d.track_id is not None for d in players),
        "displayed_players": sum(displayed_as_player(record, d, confidence) for d in detections)
        if record.analysis_scope == "on_pitch_players"
        else sum(
            valid_box(d, record.image_size) and visible_in_record(record, d, confidence) for d in players
        ),
        "counted_players": sum(counted_as_player(record, d, confidence) for d in detections)
        if field_available(record) and record.player_model_available
        else None,
        "field_status": (record.calibration or {}).get("status", "manual"),
        "field_source": (record.calibration or {}).get("source", "manual"),
        "player_exclusions": dict(
            Counter(count_exclusion_reason(record, d, confidence) or "counted" for d in players)
        ),
        "role_decisions": dict(Counter(d.role_decision or "unchanged" for d in detections)),
        "ground_truth_available": False,
    }


def normalized_team_id(team_id: str | None) -> str:
    """Zet bekende varianten van team-ID's om naar de gedeelde A/B/unknown-indeling."""
    return {"A": "A", "B": "B", "team_a": "A", "team_b": "B"}.get(team_id, "unknown")


def player_summary(record: FrameRecord, confidence=None) -> dict:
    """Tel geldige spelers per team en bewaar waarom andere detecties niet meetellen."""
    visible = [
        d
        for d in record.detections
        if valid_box(d, record.image_size) and visible_in_record(record, d, confidence)
    ]
    players = [d for d in visible if d.semantic_class == "player"]
    reasons = Counter(player_exclusion_reason(d, record.image_size) for d in players)
    available = field_available(record) and record.player_model_available
    teams = Counter(
        {"A": "team_a", "B": "team_b"}.get(normalized_team_id(d.team_id), "unknown")
        for d in players
        if counted_as_player(record, d, confidence)
    )
    return {
        "status": "player_model_unavailable"
        if not record.player_model_available
        else "available"
        if available
        else "field_unavailable",
        "on_field": sum(counted_as_player(record, d, confidence) for d in players) if available else None,
        "by_team": {
            team: sum(
                counted_as_player(record, d, confidence) and normalized_team_id(d.team_id) == team
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
        "teams": {name: teams[name] for name in ("team_a", "team_b", "unknown")} if available else None,
        "persons_on_field": sum(
            field_exclusion_reason(d, record.image_size) is None
            for d in visible
            if d.semantic_class == "person"
        )
        if field_available(record)
        else None,
        "visible_person_candidates": sum(d.semantic_class == "person" for d in visible),
        "display_confidence": record_player_policy(record, confidence)["display_confidence"],
        "include_matched_low_confidence": record_player_policy(record, confidence)[
            "include_matched_low_confidence"
        ],
    }
