"""Evaluate automatic projection against explicitly reviewed, held-out human landmarks."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .automatic_calibration import transform
from .contracts import PipelineError, read_json, sha256_file
from .pipeline import validate_completed


def evaluate_calibration(run_directory, reference_path):
    directory = Path(run_directory)
    manifest = validate_completed(directory)
    reference = read_json(reference_path)
    if manifest.get("calibration_mode") != "automatic":
        raise PipelineError("Kies een run met automatische veldkalibratie.")
    if (
        reference.get("schema_version") != 1
        or reference.get("video_sha256") != manifest["video"]["sha256"]
        or reference.get("human_reviewed") is not True
        or not str(reference.get("reviewer", "")).strip()
        or reference.get("used_for_tuning") is not False
        or not reference.get("selection_frozen_at")
        or not reference.get("source")
        or not reference.get("usage")
        or (
            reference.get("calibration_id") is not None
            and reference["calibration_id"] != manifest["calibration_id"]
        )
        or (manifest.get("schema_version", 1) >= 3 and not reference.get("settings_frozen_at"))
    ):
        raise PipelineError(
            "Referentie vereist dezelfde video, menselijke review en onafhankelijke selectie."
        )
    frames = reference.get("frames", [])
    if not isinstance(frames, list) or len(frames) < 30:
        raise PipelineError("Gebruik minimaal dertig onafhankelijk beoordeelde frames.")
    indices = [f.get("frame_index") for f in frames]
    if (
        any(type(i) is not int or not 0 <= i < manifest["video"]["frame_count"] for i in indices)
        or len(set(indices)) != len(indices)
        or sorted(reference.get("selected_frame_indices", [])) != sorted(indices)
    ):
        raise PipelineError(
            "Referentieframes moeten uniek zijn en overeenkomen met de vooraf gekozen selectie."
        )
    by_index = {f["frame_index"]: f for f in frames}
    width, height = manifest["video"]["width"], manifest["video"]["height"]
    diagonal = float(np.hypot(width, height))
    results, errors, statuses = [], [], {}
    with (directory / "framegegevens.jsonl").open(encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            record = json.loads(line)
            if record["frame_index"] != index:
                raise PipelineError("Run heeft een afwijkende framevolgorde.")
            state = record["calibration"]
            statuses[state["status"]] = statuses.get(state["status"], 0) + 1
            if index not in by_index:
                continue
            truth = by_index[index]
            if type(truth.get("calibratable")) is not bool:
                raise PipelineError("Geef per referentieframe aan of kalibratie mogelijk is.")
            row = {
                "frame_index": index,
                "calibratable": truth["calibratable"],
                "system_status": state["status"],
                "errors_px": [],
                "within_limits": None,
            }
            points = truth.get("points", [])
            if truth["calibratable"]:
                try:
                    pixels = np.asarray([[p["x"], p["y"]] for p in points], dtype=float)
                    uv = np.asarray([[p["u"], p["v"]] for p in points], dtype=float)
                    if len(points) < 2 or pixels.shape != (len(points), 2):
                        raise ValueError("Te weinig controlepunten")
                    if (
                        not np.isfinite(pixels).all()
                        or not np.isfinite(uv).all()
                        or (uv < 0).any()
                        or (uv > 1).any()
                        or (pixels < 0).any()
                        or (pixels[:, 0] >= width).any()
                        or (pixels[:, 1] >= height).any()
                        or len(np.unique(pixels, axis=0)) != len(points)
                        or len(np.unique(uv, axis=0)) != len(points)
                    ):
                        raise ValueError("Ongeldige controlepunten")
                    if state["status"] == "valid":
                        projected = transform(uv, np.linalg.inv(np.asarray(state["homography"])))
                        distances = np.linalg.norm(projected - pixels, axis=1)
                        row["errors_px"] = distances.tolist()
                        row["within_limits"] = bool(
                            np.median(distances) <= diagonal * 0.005 and distances.max() <= diagonal * 0.01
                        )
                        errors.extend(distances.tolist())
                except (KeyError, ValueError, TypeError, np.linalg.LinAlgError) as exc:
                    raise PipelineError(f"Ongeldige menselijke referentie op frame {index}: {exc}") from exc
            elif points:
                raise PipelineError("Een niet-kalibreerbaar frame mag geen referentiepunten claimen.")
            results.append(row)
    if len(results) != len(frames):
        raise PipelineError("Niet alle referentieframes zijn in de run aanwezig.")
    possible = sum(r["calibratable"] for r in results)
    usable = sum(r["calibratable"] and r["system_status"] == "valid" for r in results)
    false_valid = sum(not r["calibratable"] and r["system_status"] == "valid" for r in results)
    within_limits = sum(r["within_limits"] is True for r in results)
    return {
        "schema_version": 1,
        "video_sha256": manifest["video"]["sha256"],
        "calibration_id": manifest["calibration_id"],
        "reference_sha256": sha256_file(reference_path),
        "reviewer": reference["reviewer"],
        "reference_frames": len(results),
        "calibratable_reference_frames": possible,
        "usable_reference_frames": usable,
        "coverage_on_calibratable_frames": within_limits / possible if possible else None,
        "output_coverage_on_calibratable_frames": usable / possible if possible else None,
        "false_valid_on_uncalibratable_frames": false_valid,
        "within_limits_frames": within_limits,
        "numerical_criteria_passed": bool(
            possible
            and within_limits / possible >= 0.9
            and not false_valid
            and errors
            and np.median(errors) <= diagonal * 0.005
            and max(errors) <= diagonal * 0.01
        ),
        "human_content_accepted": None,
        "median_error_px": float(np.median(errors)) if errors else None,
        "maximum_error_px": float(max(errors)) if errors else None,
        "median_limit_px": diagonal * 0.005,
        "maximum_limit_px": diagonal * 0.01,
        "run_status_counts": statuses,
        "frames": results,
        "note": "Accuracy is reported only where a projection exists; always read it together with coverage.",
    }
