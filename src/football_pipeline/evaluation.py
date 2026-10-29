"""Koppelt voorspelde boxen aan trackingreferenties en telt projectgebonden fouten; dit is geen officiële MOT-metriekimplementatie."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

from .contracts import PipelineError, read_json
from .pipeline import validate_completed


def iou_matrix(predicted: list, references: list) -> np.ndarray:
    """Bereken vectorieel de overlap gedeeld door de vereniging voor ieder paar voorspelde en
    referentieboxen, ook bij lege invoerlijsten.
    """
    if not predicted or not references:
        return np.empty((len(predicted), len(references)))
    p, r = np.asarray(predicted, dtype=float), np.asarray(references, dtype=float)
    intersection_min = np.maximum(p[:, None, :2], r[None, :, :2])
    intersection_max = np.minimum(p[:, None, 2:], r[None, :, 2:])
    intersection = np.maximum(0, intersection_max - intersection_min).prod(axis=2)
    union = (p[:, 2:] - p[:, :2]).prod(axis=1)[:, None] + (r[:, 2:] - r[:, :2]).prod(axis=1) - intersection
    return np.divide(intersection, union, out=np.zeros_like(intersection), where=union > 0)


def evaluate_frames(predictions: list[dict], references: list[dict]) -> dict:
    """Project-specific counts, not standardized MOT/IDF1 metrics."""
    if not references:
        raise PipelineError("Trackingreferentie bevat geen frames.")

    def check_box(box):
        """Weiger referentie- of voorspellingsboxen met verkeerde vorm, ongeldige getallen of omgekeerde
        coördinaten vóór evaluatie.
        """
        try:
            values = np.asarray(box, dtype=float)
            if (
                values.shape != (4,)
                or not np.isfinite(values).all()
                or (values[:2] < 0).any()
                or (values[2:] <= values[:2]).any()
            ):
                raise PipelineError("Evaluatie vereist geldige boxes in oorspronkelijke beeldpixels.")
        except (ValueError, TypeError) as exc:
            if isinstance(exc, PipelineError):
                raise
            raise PipelineError("Evaluatie bevat ongeldige boxcoördinaten.") from exc

    reference_indexes = [r["frame_index"] for r in references]
    if reference_indexes != list(range(reference_indexes[0], reference_indexes[-1] + 1)):
        raise PipelineError("Referentie moet ieder frame in het onderzochte fragment bevatten.")
    prediction_map = {p["frame_index"]: p for p in predictions}
    if len(prediction_map) != len(predictions) or not set(reference_indexes).issubset(prediction_map):
        raise PipelineError("Ontbrekende of dubbele voorspelde frames in evaluatie.")
    counts = {
        "id_switches": 0,
        "id_takeovers": 0,
        "interruptions": 0,
        "missed_visible_observations": 0,
        "false_track_observations": 0,
        "matched_observations": 0,
    }
    previous_id, previous_owner, pending_gap = {}, {}, set()
    known_matched = set()
    events = []
    for reference in references:
        index = reference["frame_index"]
        all_objects = reference["objects"]
        ids = [str(obj["reference_id"]) for obj in all_objects]
        if len(ids) != len(set(ids)) or any(not isinstance(o.get("visible"), bool) for o in all_objects):
            raise PipelineError("Referentie-ID's moeten uniek zijn per frame en visible vereist een boolean.")
        visible = [o for o in all_objects if o["visible"]]
        for obj in visible:
            check_box(obj["bbox_xyxy"])
        visible_ids = {str(o["reference_id"]) for o in visible}
        pending_gap.intersection_update(visible_ids)
        predicted = [
            d
            for d in prediction_map[index]["detections"]
            if d["semantic_class"] == "player" and d.get("track_id") is not None
        ]
        track_ids = [d["track_id"] for d in predicted]
        for detection in predicted:
            check_box(detection["bbox_xyxy"])
        if len(track_ids) != len(set(track_ids)):
            raise PipelineError("Een track-ID verschijnt dubbel in hetzelfde frame.")
        overlap = iou_matrix([d["bbox_xyxy"] for d in predicted], [o["bbox_xyxy"] for o in visible])
        matched_references, matched_predictions = set(), set()
        if overlap.size:
            rows, cols = linear_sum_assignment(np.where(overlap >= 0.5, 1 - overlap, 1e6))
            for row, col in zip(rows, cols):
                if overlap[row, col] < 0.5:
                    continue
                reference_id = str(visible[col]["reference_id"])
                track_id = predicted[row]["track_id"]
                matched_references.add(reference_id)
                matched_predictions.add(row)
                for kind, condition in (
                    ("id_switches", reference_id in previous_id and previous_id[reference_id] != track_id),
                    ("id_takeovers", track_id in previous_owner and previous_owner[track_id] != reference_id),
                    ("interruptions", reference_id in pending_gap),
                ):
                    if condition:
                        counts[kind] += 1
                        events.append(
                            {
                                "frame_index": index,
                                "type": kind,
                                "reference_id": reference_id,
                                "track_id": track_id,
                            }
                        )
                previous_id[reference_id], previous_owner[track_id] = track_id, reference_id
                known_matched.add(reference_id)
                pending_gap.discard(reference_id)
        missed = visible_ids - matched_references
        pending_gap.update(missed & known_matched)
        counts["matched_observations"] += len(matched_references)
        counts["missed_visible_observations"] += len(missed)
        counts["false_track_observations"] += len(predicted) - len(matched_predictions)
    return {
        "definition": "project_counts_iou_0.5_v1",
        "evaluated_frames": len(references),
        "counts": counts,
        "events": events,
        "note": "ID-wissels en ID-overnames kunnen hetzelfde incident beschrijven; tel ze niet bij elkaar op.",
    }


def evaluate_run(run_directory: Path, reference_path: Path) -> dict:
    """Controleer de opgeslagen run en trackingreferenties en schrijf de projectgebonden trackingfouten
    en referentieherkomst naar een evaluatierapport.
    """
    manifest = validate_completed(run_directory)
    reference = read_json(reference_path)
    if not isinstance(reference.get("frames"), list) or not reference["frames"]:
        raise PipelineError("Trackingreferentie bevat geen frames.")
    if (
        reference.get("schema_version") != 1
        or reference.get("video_sha256") != manifest["video"]["sha256"]
        or reference.get("image_size") != [manifest["video"]["width"], manifest["video"]["height"]]
    ):
        raise PipelineError("Trackingreferentie hoort niet bij deze video of beeldschaal.")
    if manifest.get("tracker_config") is None:
        raise PipelineError("Deze uitvoering bevat geen tracking.")
    with (run_directory / "framegegevens.jsonl").open(encoding="utf-8") as stream:
        start, end = reference["frames"][0]["frame_index"], reference["frames"][-1]["frame_index"]
        predictions = [row for row in map(json.loads, stream) if start <= row["frame_index"] <= end]
    report = evaluate_frames(predictions, reference["frames"])
    report.update(
        run_key=manifest["cache_key"],
        measurements=manifest["measurements"],
        reference_source=str(reference_path),
    )
    return report
