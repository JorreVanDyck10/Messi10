"""Conservative additional field evidence from a frozen-backbone adapted head."""

from copy import deepcopy

import numpy as np

from .automatic_calibration import transform
from .field_layout import POINTS_UV
from .field_motion import estimate_checked, line_checks


ENSEMBLE_RULE = "preserve_teacher_valid_then_student_fit_with_teacher_peak_controls_v1"


def choose_head_observation(teacher, student, image_size, settings):
    """Keep every accepted teacher fit; recover only with agreement of its peaks.

    Teacher/student heads share a backbone. Their agreement is an automatic
    consistency check, not independent accuracy evidence or human review.
    """
    original = estimate_checked(teacher, image_size, settings)
    evidence = {"rule": ENSEMBLE_RULE, "teacher_status": original["status"], "selected": "teacher"}
    if original["status"] in {"valid", "invalid_observation", "orientation_unknown"}:
        return teacher, evidence
    candidate = estimate_checked(student, image_size, settings)
    evidence["student_status"] = candidate["status"]
    points = original["points"]
    if candidate["status"] != "valid" or len(points) < 2:
        return teacher, evidence
    xy = np.asarray([[p["x"], p["y"]] for p in points])
    diagonal = np.hypot(*image_size)
    if max(np.linalg.norm(xy - point, axis=1).max() for point in xy) < diagonal * 0.05:
        evidence["control_status"] = "insufficient_control_spread"
        return teacher, evidence
    try:
        inverse = np.linalg.inv(np.asarray(candidate["homography"]))
        uv = np.asarray([POINTS_UV[p["id"]] for p in points])
        errors = np.linalg.norm(transform(uv, inverse) - xy, axis=1)
        line_errors, line_ids = line_checks(original["lines"], inverse)
        evidence.update(
            teacher_control_ids=[p["id"] for p in points],
            teacher_control_errors_px=errors.tolist(),
            teacher_line_ids=line_ids,
            teacher_line_errors_px=line_errors,
        )
        for values in (errors, line_errors):
            if len(values) and (
                not np.isfinite(values).all()
                or np.median(values) > diagonal * settings["median_diagonal_fraction"]
                or max(values) > diagonal * settings["maximum_diagonal_fraction"]
            ):
                evidence["control_status"] = "teacher_disagreement"
                return teacher, evidence
    except (ValueError, TypeError, np.linalg.LinAlgError):
        evidence["control_status"] = "unprojectable_teacher_controls"
        return teacher, evidence
    result = deepcopy(student)
    evidence.update(selected="student", control_status="teacher_peak_agreement")
    result["head_ensemble"] = evidence
    return result, evidence
