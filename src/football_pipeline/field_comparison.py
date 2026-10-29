"""Vergelijkt veldkandidaten en registreert voorwaarden voor ingebruikname."""

from __future__ import annotations

from collections import Counter

import numpy as np

from .automatic_calibration import transform
from .contracts import PipelineError, digest_json
from .field_review import failure_intervals


def summarize_field_records(records, fps):
    states = [row["calibration"] for row in records]
    intervals = failure_intervals(records)
    valid = sum(s["status"] == "valid" for s in states)
    return {
        "frames": len(states),
        "internally_valid_frames": valid,
        "internal_coverage": valid / len(states) if states else None,
        "status_counts": dict(Counter(s["status"] for s in states)),
        "source_counts": dict(Counter(s.get("source", "unavailable") for s in states)),
        "temporal_status_counts": dict(
            Counter(s.get("temporal_quality", {}).get("status", "legacy") for s in states)
        ),
        "projection_counts": dict(Counter(d["projection_status"] for r in records for d in r["detections"])),
        "failure_intervals": intervals,
        "longest_failure_s": max((b - a + 1 for a, b in intervals), default=0) / fps,
        "correct_coverage": None,
        "wrong_frames": None,
        "median_error_px": None,
        "maximum_error_px": None,
        "p95_error_px": None,
        "human_reviewed": False,
    }


def evaluate_field_records(records, video, reference):
    """Evaluate identical held-out landmarks for either policy, never fit them."""
    frames = reference.get("frames", [])
    indices = reference.get("selected_frame_indices", [])
    if (
        reference.get("schema_version") != 1
        or reference.get("video_sha256") != video.sha256
        or reference.get("image_size") != list(video.size)
        or reference.get("human_reviewed") is not True
        or not str(reference.get("reviewer", "")).strip()
        or reference.get("used_for_tuning") is not False
        or not reference.get("selection_frozen_at")
        or not reference.get("settings_frozen_at")
        or not reference.get("source")
        or not reference.get("usage")
        or not isinstance(frames, list)
        or len(frames) < 30
        or any(type(i) is not int or not 0 <= i < video.frame_count for i in indices)
        or len(set(indices)) != len(indices)
        or sorted(indices) != sorted(f.get("frame_index", -1) for f in frames)
    ):
        raise PipelineError(
            "Veldvergelijking vereist minstens dertig vooraf geselecteerde, menselijk beoordeelde referenties."
        )
    if len(records) != video.frame_count or any(
        r["frame_index"] != i
        or r["image_size"] != list(video.size)
        or abs(r["timestamp_s"] - i / video.fps) > 1e-6
        for i, r in enumerate(records)
    ):
        raise PipelineError("Vergelijkingsrecords hebben een afwijkende tijdlijn of beeldschaal.")
    diagonal = np.hypot(*video.size)
    errors, results = [], []
    for frame in frames:
        if type(frame.get("calibratable")) is not bool or frame.get("human_reviewed") is not True:
            raise PipelineError("Bevestig de menselijke beoordeling van ieder referentieframe.")
        state = records[frame["frame_index"]]["calibration"]
        valid = state["status"] == "valid"
        row = {
            "frame_index": frame["frame_index"],
            "calibratable": frame["calibratable"],
            "output_valid": valid,
            "within_limits": False,
            "errors_px": [],
        }
        points = frame.get("points", [])
        if frame["calibratable"]:
            try:
                xy = np.asarray([[p["x"], p["y"]] for p in points], float)
                uv = np.asarray([[p["u"], p["v"]] for p in points], float)
                if (
                    len(points) < 2
                    or xy.shape != (len(points), 2)
                    or uv.shape != xy.shape
                    or not np.isfinite(xy).all()
                    or not np.isfinite(uv).all()
                    or (xy < 0).any()
                    or (xy >= video.size).any()
                    or (uv < 0).any()
                    or (uv > 1).any()
                    or len(np.unique(xy, axis=0)) != len(points)
                    or len(np.unique(uv, axis=0)) != len(points)
                ):
                    raise ValueError("invalid references")
                if valid:
                    projected = transform(uv, np.linalg.inv(np.asarray(state["homography"])))
                    distances = np.linalg.norm(projected - xy, axis=1)
                    row["errors_px"] = distances.tolist()
                    row["within_limits"] = bool(
                        np.median(distances) <= diagonal * 0.005 and max(distances) <= diagonal * 0.01
                    )
                    errors.extend(distances.tolist())
            except (KeyError, TypeError, ValueError, np.linalg.LinAlgError) as exc:
                raise PipelineError(f"Ongeldige veldreferentie op frame {frame['frame_index']}.") from exc
        elif points:
            raise PipelineError("Niet-kalibreerbare frames mogen geen referentiepunten bevatten.")
        results.append(row)
    possible = sum(r["calibratable"] for r in results)
    correct = sum(r["within_limits"] for r in results)
    wrong = sum(r["output_valid"] and not r["within_limits"] for r in results)
    return {
        "video_sha256": video.sha256,
        "reference_sha256": digest_json(reference),
        "human_reviewed": True,
        "reference_frames": len(results),
        "calibratable_frames": possible,
        "correct_frames": correct,
        "wrong_frames": wrong,
        "false_valid_on_uncalibratable_frames": sum(
            r["output_valid"] and not r["calibratable"] for r in results
        ),
        "correct_coverage": correct / possible if possible else None,
        "median_error_px": float(np.median(errors)) if errors else None,
        "maximum_error_px": float(max(errors)) if errors else None,
        "p95_error_px": float(np.percentile(errors, 95)) if errors else None,
        "numerical_criteria_passed": bool(possible and correct / possible >= 0.9 and not wrong),
        "frames": results,
    }


def release_decision(comparisons):
    """Require reviewed improvements for BOTH video types, with <=5pp coverage loss."""
    reasons = []
    if set(comparisons) != {"broadcast", "fixed"}:
        reasons.append("both_video_types_required")
    for kind, pair in comparisons.items():
        baseline, candidate = pair["baseline"], pair["candidate"]
        if not baseline.get("human_reviewed") or not candidate.get("human_reviewed"):
            reasons.append(f"{kind}:human_review_pending")
            continue
        if not baseline.get("reference_sha256") or baseline["reference_sha256"] != candidate.get(
            "reference_sha256"
        ):
            reasons.append(f"{kind}:references_differ")
            continue
        metrics = ("correct_coverage", "wrong_frames", "median_error_px", "p95_error_px", "maximum_error_px")
        if any(
            report.get(key) is None or not np.isfinite(report[key])
            for report in (baseline, candidate)
            for key in metrics
        ):
            reasons.append(f"{kind}:insufficient_measured_projections")
            continue
        if candidate["correct_coverage"] + 1e-12 < baseline["correct_coverage"] - 0.05:
            reasons.append(f"{kind}:coverage_regression")
        no_error_regression = all(
            candidate[k] <= baseline[k] for k in ("median_error_px", "p95_error_px", "maximum_error_px")
        )
        fewer_wrong = candidate["wrong_frames"] < baseline["wrong_frames"] and no_error_regression
        lower_error = (
            candidate["median_error_px"] < baseline["median_error_px"]
            and candidate["wrong_frames"] <= baseline["wrong_frames"]
            and no_error_regression
        )
        if not (fewer_wrong or lower_error):
            reasons.append(f"{kind}:no_proven_improvement")
    return {
        "eligible_for_activation": not reasons,
        "activated": False,
        "reasons": reasons,
        "full_acceptance": bool(
            not reasons and all(p["candidate"].get("numerical_criteria_passed") for p in comparisons.values())
        ),
    }
