"""Slaat menselijke veldreferenties afzonderlijk van modelvoorspellingen op."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from .contracts import PipelineError, read_json, write_json
from .field_layout import POINTS_UV


def failure_intervals(records):
    intervals = []
    start = None
    for index, row in enumerate(records):
        failed = row.get("calibration", {}).get("status") != "valid"
        if failed and start is None:
            start = index
        if start is not None and (not failed or index == len(records) - 1):
            end = index - 1 if not failed else index
            intervals.append((start, end))
            start = None
    return intervals


def save_review(path, template, *, index, points, calibratable, reviewer, confirmed=False):
    """Only an explicit user save can add a human assessment; incomplete sets stay unapproved."""
    if not confirmed or not reviewer.strip() or type(calibratable) is not bool:
        raise PipelineError("Bevestig je eigen beoordeling en vul je naam in.")
    if index not in template["selected_frame_indices"]:
        raise PipelineError("Dit frame behoort niet tot de vooraf vastgelegde selectie.")
    if template.get("used_for_tuning") is False and not template.get("settings_frozen_at"):
        raise PipelineError("Zet de instellingen vast vóór de beoordelingsreferenties.")
    cleaned = []
    if calibratable:
        for p in points:
            if p.get("x") is None or p.get("y") is None:
                continue
            identifier = p["id"]
            if identifier not in POINTS_UV:
                raise PipelineError("Onbekend vlak veldpunt.")
            u, v = POINTS_UV[identifier]
            values = np.array([p["x"], p["y"]], float)
            if (
                not np.isfinite(values).all()
                or (values < 0).any()
                or (values >= template["image_size"]).any()
            ):
                raise PipelineError("Controlepunt valt buiten de oorspronkelijke video.")
            cleaned.append({"id": identifier, "u": u, "v": v, "x": float(values[0]), "y": float(values[1])})
        if (
            len(cleaned) < 2
            or len({p["id"] for p in cleaned}) != len(cleaned)
            or len({(p["x"], p["y"]) for p in cleaned}) != len(cleaned)
        ):
            raise PipelineError("Klik minstens twee verschillende bekende veldpunten.")
    document = read_json(path) if Path(path).is_file() else {**template, "frames": []}
    for key in (
        "video_sha256",
        "selected_frame_indices",
        "calibration_id",
        "used_for_tuning",
        "selection_frozen_at",
    ):
        if document.get(key) != template.get(key):
            raise PipelineError("Bestaande beoordelingen horen bij een andere selectie of kandidaat.")
    document["frames"] = sorted(
        [f for f in document["frames"] if f["frame_index"] != index]
        + [
            {
                "frame_index": index,
                "calibratable": calibratable,
                "points": cleaned,
                "human_reviewed": True,
                "reviewer": reviewer.strip(),
                "reviewed_at": datetime.now(UTC).isoformat(),
            }
        ],
        key=lambda f: f["frame_index"],
    )
    document.update(human_reviewed=False, reviewer=reviewer.strip())
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    write_json(path, document)
    return document


def finalize_review(path, *, confirmed=False):
    document = read_json(path)
    if (
        not confirmed
        or sorted(f["frame_index"] for f in document["frames"]) != sorted(document["selected_frame_indices"])
        or not all(f.get("human_reviewed") is True for f in document["frames"])
    ):
        raise PipelineError("Beoordeel eerst alle geselecteerde frames en bevestig de volledige set.")
    document.update(human_reviewed=True, completed_at=datetime.now(UTC).isoformat())
    write_json(path, document)
    return document
