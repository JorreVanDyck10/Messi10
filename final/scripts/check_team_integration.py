"""Repeat a real-video engineering check; never substitute model output for human labels."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path

from football_pipeline.automatic_calibration import load_automatic_calibration
from football_pipeline.contracts import PipelineError, write_json
from football_pipeline.pipeline import process_video, validate_completed
from football_pipeline.video import ROOT, inspect_video


def check_result(result) -> dict:
    manifest = validate_completed(result.directory)
    encoded = inspect_video(result.video_path)
    video = manifest["video"]
    fps = video["fps_num"] / video["fps_den"]
    if (
        encoded.frame_count != video["frame_count"]
        or encoded.size != (1920, 720)
        or not math.isclose(encoded.fps, fps, rel_tol=1e-6)
    ):
        raise PipelineError("Afwijkende teamvideo.")
    available, assignment, ids = [], Counter(), set()
    closed_ids, reset_frames, unknown_field_frames = set(), [], 0
    with (
        (result.directory / "framegegevens.jsonl").open(encoding="utf-8") as stream,
        (result.directory / "teamtelling.csv").open(encoding="utf-8-sig", newline="") as csv_stream,
    ):
        table = csv.DictReader(csv_stream)
        frames = 0
        for index, line in enumerate(stream):
            row = json.loads(line)
            exported = next(table, None)
            if exported is None or int(exported["frame_index"]) != index or row["frame_index"] != index:
                raise PipelineError("Framevolgorde van exports verschilt.")
            if not all(
                math.isclose(float(value), index / fps, abs_tol=1e-6)
                for value in (row["timestamp_s"], exported["timestamp_s"])
            ):
                raise PipelineError("Tijdstempels van video en exports verschillen.")
            if row.get("tracking", {}).get("reset_tracks"):
                closed_ids.update(ids)
                reset_frames.append(index)
            field_unknown = row.get("calibration", {}).get("status") not in {None, "valid"}
            if field_unknown:
                unknown_field_frames += 1
                if any(d["field_position"] is not None for d in row["detections"]):
                    raise PipelineError("Veldverlies bevat toch bekende veldposities.")
            summary = row["player_summary"]
            values = summary["by_team"]
            if summary["on_field"] is None:
                if any(value is not None for value in values.values()):
                    raise PipelineError("Ontbrekende veldtelling is niet onbekend gebleven.")
            else:
                available.append(index)
                if sum(values.values()) != summary["on_field"]:
                    raise PipelineError("Teamtotalen verschillen van de spelertelling.")
            expected = {
                "on_field": summary["on_field"],
                "team_A": values["A"],
                "team_B": values["B"],
                "unknown": values["unknown"],
            }
            if any(exported[key] != ("" if value is None else str(value)) for key, value in expected.items()):
                raise PipelineError("CSV en JSONL bevatten verschillende tellingen.")
            for d in row["detections"]:
                if d["semantic_class"] != "player" and d["team_id"] is not None:
                    raise PipelineError("Een andere rol heeft een spelerteam gekregen.")
                if d["semantic_class"] == "player":
                    assignment[d["team_id"] or "unknown"] += 1
                    if d["track_id"] is not None:
                        if d["track_id"] in closed_ids:
                            raise PipelineError("Speler-ID is hergebruikt na een camerawissel.")
                        ids.add(d["track_id"])
            frames += 1
        if frames != video["frame_count"] or next(table, None) is not None:
            raise PipelineError("Export heeft een afwijkend frameaantal.")
    return {
        "status": "passed",
        "kind": "real_video_engineering_check_not_accuracy_evaluation",
        "run_directory": str(result.directory),
        "video_sha256": video["sha256"],
        "frames": frames,
        "output_image_size": list(encoded.size),
        "fps": encoded.fps,
        "model_evidence": manifest["evidence_kind"],
        "team_model_status": manifest["team_model_status"],
        "frames_with_count": len(available),
        "first_count_frame": available[0] if available else None,
        "player_observations_by_team": dict(assignment),
        "distinct_temporary_ids": len(ids),
        "camera_reset_frames": reset_frames,
        "unknown_field_frames": unknown_field_frames,
        "timestamp_and_fps_checks": "passed",
        "measurements": manifest["measurements"],
        "code": manifest["code"],
        "team_accuracy_measured": False,
        "tracking_accuracy_measured": False,
        "limitations": [
            "Existing development clip and existing field observations; no independent test.",
            "Counts are observations, not a verified roster or unique-person count.",
            "Colour grouping, detector errors and identity fragmentation require human review.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("calibration", type=Path, help="Bestaande automatische calibration.json")
    parser.add_argument("--models", type=Path, default=ROOT / "configs/models-players.json")
    parser.add_argument("--teams", type=Path, default=ROOT / "configs/teams.json")
    parser.add_argument("--output", type=Path, default=ROOT / "runs")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/team-analysis/integration-check.json")
    args = parser.parse_args()
    result = process_video(
        args.video,
        load_automatic_calibration(args.calibration),
        args.models,
        args.output,
        tracker_config_path=ROOT / "configs/bytetrack.yaml",
        team_config_path=args.teams,
    )
    report = check_result(result)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.report, report)
    print(
        json.dumps(
            {key: value for key, value in report.items() if key not in {"code", "measurements"}}, indent=2
        )
    )


if __name__ == "__main__":
    main()
