"""Audit saved observations and export blind original-frame review packages.

No model inference, label fabrication or automatic promotion is performed here.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from .contracts import FrameRecord, PipelineError, digest_json, sha256_file, write_json
from .field_layout import POINTS_UV
from .participants import counted_as_player, field_available, frame_diagnostics
from .pipeline import validate_completed


def sequence_summary(records, fps):
    """Count actual consecutive source frames, including trailing failures."""
    if not np.isfinite(fps) or fps <= 0 or not records:
        raise PipelineError("Audit requires frames and a positive finite FPS")
    if [r.frame_index for r in records] != list(range(len(records))):
        raise PipelineError("Audit requires consecutive frames starting at zero")
    if any(abs(r.timestamp_s - r.frame_index / fps) > 1e-6 for r in records):
        raise PipelineError("Audit timestamps disagree with source FPS")
    gaps, start = [], None
    for i in range(len(records) + 1):
        missing = i < len(records) and not field_available(records[i])
        if missing and start is None:
            start = i
        if not missing and start is not None:
            gaps.append(
                {
                    "start_frame": start,
                    "end_frame": i - 1,
                    "start_s": start / fps,
                    "duration_s": (i - start) / fps,
                    "recovered": i < len(records),
                }
            )
            start = None
    missing_records = [r for r in records if not field_available(r)]
    sizes = [frame_diagnostics(r)["visible_player_candidates"] for r in missing_records]
    return {
        "frames": len(records),
        "fps": fps,
        "field_available_frames": len(records) - len(missing_records),
        "field_unavailable_frames": len(missing_records),
        "field_available_fraction": 1 - len(missing_records) / len(records),
        "field_status_counts": dict(Counter((r.calibration or {}).get("status", "manual") for r in records)),
        "field_source_counts": dict(Counter((r.calibration or {}).get("source", "manual") for r in records)),
        "dropout_count": len(gaps),
        "dropout_duration_s": len(missing_records) / fps,
        "longest_dropout_s": max((g["duration_s"] for g in gaps), default=0),
        "dropouts": gaps,
        "missing_field_visible_player_range": [min(sizes), max(sizes)] if sizes else None,
        "missing_field_frames_with_visible_players": sum(n > 0 for n in sizes),
        "accuracy": {
            "player_precision": None,
            "player_recall": None,
            "box_ap": None,
            "correct_field_coverage": None,
            "line_error_px": None,
            "reason": "Independent reference labels required; availability is not accuracy",
        },
    }


def load_run(run):
    manifest = validate_completed(run)
    video = manifest["video"]
    source = Path(video["path"])
    if not source.is_file() or sha256_file(source) != video["sha256"]:
        raise PipelineError("The original source video is missing or changed")
    records = [
        FrameRecord.from_dict(json.loads(line))
        for line in (run / "framegegevens.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    if len(records) != video["frame_count"] or any(
        r.image_size != (video["width"], video["height"]) for r in records
    ):
        raise PipelineError("Saved observations disagree with original video dimensions/frame count")
    return manifest, records


def audit(run, output):
    manifest, records = load_run(run)
    output.mkdir(parents=True, exist_ok=True)
    summary = sequence_summary(records, manifest["video"]["fps_num"] / manifest["video"]["fps_den"])
    summary.update(
        schema_version=1,
        source_video=manifest["video"],
        run=str(run.resolve()),
        frame_data_sha256=sha256_file(run / "framegegevens.jsonl"),
        field_settings=manifest.get("field_settings"),
        model_weights=[m["weights_sha256"] for m in manifest["models"]["models"]],
        human_review_completed=False,
        independent_final_test_completed=False,
    )
    with (output / "stages.jsonl").open("w", encoding="utf-8") as stream:
        for r in records:
            d = frame_diagnostics(r)
            d.update(
                frame_index=r.frame_index,
                timestamp_s=r.timestamp_s,
                legacy_displayed_players=sum(counted_as_player(r, x) for x in r.detections)
                if r.analysis_scope == "on_pitch_players"
                else d["visible_player_candidates"],
                tracking=r.tracking,
                calibration_quality=(r.calibration or {}).get("quality", {}),
            )
            stream.write(json.dumps(d, allow_nan=False) + "\n")
    with (output / "dropouts.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["start_frame", "end_frame", "start_s", "duration_s", "recovered"]
        )
        writer.writeheader()
        writer.writerows(summary["dropouts"])
    write_json(output / "summary.json", summary)
    return summary


def export_review(run, output):
    """Original pixels, uniform coverage plus first/middle/last dropout transitions."""
    manifest, records = load_run(run)
    fps = manifest["video"]["fps_num"] / manifest["video"]["fps_den"]
    summary = sequence_summary(records, fps)
    selected = set(range(0, len(records), max(1, round(fps))))
    gaps = summary["dropouts"]
    for i in sorted({0, len(gaps) // 2, len(gaps) - 1}) if gaps else []:
        gap = gaps[i]
        selected.update(range(max(0, gap["start_frame"] - 2), min(len(records), gap["start_frame"] + 3)))
        selected.update(range(max(0, gap["end_frame"] - 2), min(len(records), gap["end_frame"] + 3)))
    selected = sorted(selected | {len(records) - 1})
    template = {
        "schema_version": 1,
        "video_sha256": manifest["video"]["sha256"],
        "image_size": [manifest["video"]["width"], manifest["video"]["height"]],
        "calibration_id": manifest["calibration_id"],
        "selected_frame_indices": selected,
        "selection_frozen_at": datetime.now(UTC).isoformat(),
        "used_for_tuning": True,
        "human_reviewed": False,
        "reviewer": "",
        "split": "development",
        "frames": [
            {"frame_index": i, "calibratable": None, "points": [], "players": [], "human_reviewed": False}
            for i in selected
        ],
        "instructions": "Label original pixels; do not copy model predictions. Players include keepers. "
        "Mark officials separately. Empty player labels are not reviewed negatives.",
        "known_field_points": [{"id": i, "uv": list(uv)} for i, uv in POINTS_UV.items()],
    }
    output.mkdir(parents=True, exist_ok=True)
    target = output / "reference-template.json"
    if target.exists():
        raise PipelineError("Review package already exists; preserve its frozen selection")
    capture = cv2.VideoCapture(manifest["video"]["path"])
    try:
        for i in selected:
            capture.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, image = capture.read()
            if not ok or image.shape[1::-1] != tuple(template["image_size"]):
                raise PipelineError("Cannot decode original review frame")
            if not cv2.imwrite(str(output / f"frame-{i:06d}.png"), image):
                raise PipelineError("Cannot write review image")
    finally:
        capture.release()
    template["selection_fingerprint"] = digest_json([template["video_sha256"], selected])
    write_json(target, template)
    return {"frames": len(selected), "reference": str(target)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "export-review"))
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run, args.output) if args.command == "audit" else export_review(args.run, args.output)
    print(json.dumps({k: v for k, v in result.items() if k != "dropouts"}, indent=2))


if __name__ == "__main__":
    main()
