"""Prepare, replay and review a field-only v2/v3 comparison without new detection inference."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.automatic_calibration import (
    AutomaticCalibration,
    load_automatic_calibration,
    project_automatic,
)
from football_pipeline.contracts import Detection, PipelineError, read_json, sha256_file, write_json
from football_pipeline.field_comparison import (
    evaluate_field_records,
    release_decision,
    summarize_field_records,
)
from football_pipeline.field_layout import LINES_UV, POINTS_UV
from football_pipeline.field_motion import DEFAULT_SETTINGS, RELIABLE_SETTINGS, CameraCalibration
from football_pipeline.participants import GROUND_ROLES
from football_pipeline.pipeline import validate_completed
from football_pipeline.render import automatic_preview
from football_pipeline.replay import replay_detections
from football_pipeline.video import ROOT, VideoWriter, inspect_video


def prepare(video_path, kind, output, selection_path=None):
    """Leg de bronvideo, bevroren framekeuze en benodigde baseline-/kandidaatinstellingen vast voor de
    latere veldvergelijking.
    """
    video = inspect_video(video_path)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "selection.json").exists():
        raise PipelineError("Selectie bestaat al; behoud de bevroren selectie of kies een nieuwe uitvoermap.")
    now = datetime.now(UTC).isoformat()
    if selection_path:
        selection = read_json(selection_path)
        if selection["video_sha256"] != video.sha256:
            raise PipelineError("Selectie hoort bij een andere video.")
        development, evaluation = selection["development_indices"], selection["evaluation_indices"]
        previous_selection = sha256_file(selection_path)
    else:
        # Alternating contiguous one-second blocks, excluding 0.1s at each boundary.
        buckets = [[], []]
        for i in range(video.frame_count):
            seconds = i / video.fps
            if 0.1 <= seconds % 1 <= 0.9:
                buckets[int(seconds) % 2].append(i)
        if len(buckets[1]) < 30 or len(buckets[0]) < 10:
            raise PipelineError("Video is te kort voor afzonderlijke ontwikkel- en beoordelingsselecties.")
        development = [buckets[0][i] for i in np.linspace(0, len(buckets[0]) - 1, 10, dtype=int)]
        evaluation = [buckets[1][i] for i in np.linspace(0, len(buckets[1]) - 1, 30, dtype=int)]
        previous_selection = None
    if len(set(evaluation)) < 30 or set(development) & set(evaluation):
        raise PipelineError(
            "Gebruik minstens dertig verschillende beoordelingsframes buiten de ontwikkeling."
        )
    files = [
        "field_motion.py",
        "field_bounds.py",
        "automatic_calibration.py",
        "field_comparison.py",
        "render.py",
    ]
    frozen = {
        "baseline": DEFAULT_SETTINGS,
        "candidate": RELIABLE_SETTINGS,
        "settings_frozen_at": now,
        "code_sha256": {name: sha256_file(ROOT / "src/football_pipeline" / name) for name in files},
    }
    selection = {
        "schema_version": 1,
        "kind": kind,
        "video": asdict(video),
        "video_sha256": video.sha256,
        "selection_frozen_at": now,
        "previous_selection_sha256": previous_selection,
        "development_indices": development,
        "evaluation_indices": evaluation,
        "rule": "Existing frozen selection"
        if previous_selection
        else "Alternating one-second blocks with 0.1s margins",
        "previously_inspected_development_video": True,
        "independent_final_test": False,
        "scenario_labels": "Pending human review: overview, partial pitch, occlusion, recognition loss",
    }
    write_json(output / "selection.json", selection)
    write_json(output / "frozen-settings.json", frozen)
    write_json(
        output / "reference-template.json",
        {
            "schema_version": 1,
            "video_sha256": video.sha256,
            "image_size": list(video.size),
            "source": "Bestaande lokale ontwikkelvideo",
            "usage": "Lokale ontwikkeling en beoordeling",
            "selection_frozen_at": now,
            "settings_frozen_at": now,
            "selected_frame_indices": evaluation,
            "used_for_tuning": False,
            "human_reviewed": False,
            "reviewer": "",
            "frames": [],
        },
    )
    print(
        f"Prepared {kind}: {len(development)} development, {len(evaluation)} review frames: {output}",
        flush=True,
    )


def comparison_canvas(frame, records):
    """Teken de verschillende veldtoestanden naast elkaar op hetzelfde bronframe voor een framesynchrone
    vergelijking.
    """
    canvas = np.zeros((720, 1280, 3), np.uint8)
    for column, (name, record) in enumerate(records.items()):
        left = column * 640
        image = automatic_preview(frame, record["calibration"])
        scale = min(640 / image.shape[1], 360 / image.shape[0])
        w, h = round(image.shape[1] * scale), round(image.shape[0] * scale)
        x, y = left + (640 - w) // 2, (360 - h) // 2
        canvas[y : y + h, x : x + w] = cv2.resize(image, (w, h))
        temporal = record["calibration"].get("temporal_quality", {}).get("status", "legacy")
        cv2.putText(
            canvas,
            f"{name} | {temporal}",
            (left + 15, 387),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (240, 230, 200),
            1,
        )
        origin, size = np.array([left + 95, 410]), np.array([450, 280])
        cv2.rectangle(canvas, tuple(origin), tuple(origin + size), (35, 85, 35), -1)
        for line in LINES_UV.values():
            a, b = np.rint(origin + np.asarray(line) * size).astype(int)
            cv2.line(canvas, tuple(a), tuple(b), (140, 170, 140), 1)
        if record["calibration"]["status"] == "valid":
            for d in record["detections"]:
                if d["field_position"] is not None:
                    point = np.rint(origin + np.asarray(d["field_position"]) * size).astype(int)
                    cv2.circle(canvas, tuple(point), 3, (245, 220, 90), -1)
        else:
            cv2.putText(
                canvas,
                "Veldpositie onbekend",
                (left + 160, 550),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (240, 220, 110),
                1,
            )
    row = records["candidate"]
    cv2.putText(
        canvas,
        f"EXPERIMENTEEL | frame {row['frame_index']} | {row['timestamp_s']:.3f}s | menselijke review open",
        (15, 713),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 200, 200),
        1,
    )
    return canvas


def run(bundle_path, detections_path, output, make_video=True):
    """Hergebruik opgeslagen detecties en voer de veldvarianten uit op dezelfde bronvideo; sla hun
    vergelijkingsrecords en optionele video op.
    """
    selection = read_json(output / "selection.json")
    frozen = read_json(output / "frozen-settings.json")
    for name, expected in frozen["code_sha256"].items():
        if sha256_file(ROOT / "src/football_pipeline" / name) != expected:
            raise PipelineError(
                "Code is gewijzigd na het vastzetten van de vergelijking; maak een nieuwe selectie."
            )
    if (output / "comparison.json").exists():
        raise PipelineError("Vergelijking bestaat al; gebruik evaluate voor nieuwe menselijke referenties.")
    video = inspect_video(selection["video"]["path"])
    if video.sha256 != selection["video_sha256"]:
        raise PipelineError("Videobestand gewijzigd sinds selectie.")
    original = load_automatic_calibration(bundle_path)
    original.validate_for(video)
    if original.manifest.get("schema_version") != 2:
        raise PipelineError("Gebruik een volledige bundel met ruwe punten en lijnen.")
    previous_run = validate_completed(detections_path.parent)
    if previous_run["video"]["sha256"] != video.sha256 or detections_path.name != "framegegevens.jsonl":
        raise PipelineError("Detectiereplay hoort bij een andere video of onvolledige run.")
    profiles = {
        name: AutomaticCalibration(original.manifest, original.observations_path, frozen[name])
        for name in ("baseline", "candidate")
    }
    iterators = {name: profile.frames(video) for name, profile in profiles.items()}
    cameras = {name: CameraCalibration(video.fps, frozen[name]) for name in profiles}
    sets, timings = {name: [] for name in profiles}, {name: 0.0 for name in profiles}
    capture = cv2.VideoCapture(video.path)
    writer = (
        VideoWriter(output / "comparison.mp4", 1280, 720, video.fps_num, video.fps_den)
        if make_video
        else None
    )
    started = time.perf_counter()
    try:
        with detections_path.open(encoding="utf-8") as stream:
            for index in range(video.frame_count):
                ok, frame = capture.read()
                if not ok or frame.shape[:2] != (video.height, video.width):
                    raise PipelineError(f"Ontbrekend bronframe {index}.")
                detections = replay_detections(stream, index, video)
                current = {}
                for name in profiles:
                    tick = time.perf_counter()
                    state = cameras[name].update(frame, next(iterators[name]), index)
                    projected = []
                    for d in detections:
                        copy = Detection.from_dict(asdict(d))
                        if copy.semantic_class in GROUND_ROLES:
                            project_automatic(copy, state, video.size)
                        else:
                            copy.projection_status = "not_ground_projected"
                        projected.append(asdict(copy))
                    timings[name] += time.perf_counter() - tick
                    row = {
                        "frame_index": index,
                        "timestamp_s": index / video.fps,
                        "image_size": list(video.size),
                        "calibration": state,
                        "detections": projected,
                    }
                    current[name] = row
                    sets[name].append(row)
                if writer:
                    canvas = comparison_canvas(frame, current)
                    writer.write(canvas)
                    if index in {selection["development_indices"][0], video.frame_count // 2}:
                        cv2.imwrite(str(output / f"preview-{index:06d}.jpg"), canvas)
                if index % 100 == 0 or index == video.frame_count - 1:
                    print(
                        f"{selection['kind']} {index + 1}/{video.frame_count} | {time.perf_counter() - started:.1f}s",
                        flush=True,
                    )
            if stream.readline():
                raise PipelineError("Detectiereplay bevat extra frames.")
            for iterator in iterators.values():
                if next(iterator, None) is not None:
                    raise PipelineError("Veldbundel bevat extra frames.")
        if writer:
            writer.close()
    finally:
        capture.release()
        for iterator in iterators.values():
            iterator.close()
        if writer and not writer.closed:
            writer.close(abort=True)
    for name, rows in sets.items():
        with (output / f"{name}.jsonl").open("w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, allow_nan=False) + "\n")
    report = {
        "schema_version": 1,
        "kind": selection["kind"],
        "video": asdict(video),
        "source": original.manifest["source"],
        "usage": original.manifest["usage"],
        "settings": frozen,
        "observations_sha256": sha256_file(original.observations_path),
        "detections_sha256": sha256_file(detections_path),
        "detections_run": str(detections_path.parent.resolve()),
        "models": original.manifest["models"],
        "new_detection_inference": False,
        "runtime_s": time.perf_counter() - started,
        "human_reviewed": False,
        "profiles": {
            name: {
                **summarize_field_records(sets[name], video.fps),
                "calibration_and_projection_s": timings[name],
                "records_sha256": sha256_file(output / f"{name}.jsonl"),
            }
            for name in profiles
        },
        "artifacts": {"comparison_video": "comparison.mp4" if make_video else None},
        "candidate_status": "experimental_pending_human_validation",
        "activated": False,
    }
    write_json(output / "comparison.json", report)
    print(f"Saved comparison: {output / 'comparison.json'}", flush=True)


def evaluate(outputs, destination):
    """Combineer de bevroren vergelijkingen en eventuele menselijke reviews tot de gerapporteerde
    releasebeslissing.
    """
    comparisons = {}
    for output in outputs:
        report = read_json(output / "comparison.json")
        selection = read_json(output / "selection.json")
        video = inspect_video(report["video"]["path"])
        if video.sha256 != report["video"]["sha256"]:
            raise PipelineError("Bronvideo gewijzigd na vergelijking.")
        reference_path = output / "human-reference.json"
        reference = read_json(
            reference_path if reference_path.exists() else output / "reference-template.json"
        )
        if (
            reference.get("selected_frame_indices") != selection["evaluation_indices"]
            or reference.get("settings_frozen_at") != report["settings"]["settings_frozen_at"]
        ):
            raise PipelineError("Menselijke referenties horen bij een andere selectie of instelling.")
        pair = {}
        for name in ("baseline", "candidate"):
            path = output / f"{name}.jsonl"
            if sha256_file(path) != report["profiles"][name]["records_sha256"]:
                raise PipelineError("Vergelijkingsrecords zijn gewijzigd.")
            metrics = report["profiles"][name]
            if reference.get("human_reviewed") is True:
                rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
                metrics = {**metrics, **evaluate_field_records(rows, video, reference)}
            pair[name] = metrics
        if report["kind"] in comparisons:
            raise PipelineError("Gebruik precies één vergelijking per videotype.")
        comparisons[report["kind"]] = pair
    result = {"schema_version": 1, "comparisons": comparisons, "release": release_decision(comparisons)}
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_json(destination, result)
    print(json.dumps(result["release"], indent=2), flush=True)


def export_review(output):
    """Export original frames without predictions, leaving every human label empty."""
    selection = read_json(output / "selection.json")
    video = inspect_video(selection["video"]["path"])
    if video.sha256 != selection["video_sha256"]:
        raise PipelineError("Bronvideo gewijzigd sinds de selectie.")
    destination = output / "review-frames"
    if (destination / "guide.json").exists():
        raise PipelineError("Referentiebeelden bestaan al; behoud deze bevroren export.")
    destination.mkdir(exist_ok=True)
    indices = selection["evaluation_indices"]
    columns, cell_width, cell_height = 5, 384, 248
    sheet = np.zeros(
        (((len(indices) + columns - 1) // columns) * cell_height, columns * cell_width, 3), np.uint8
    )
    positions = {index: position for position, index in enumerate(indices)}
    capture = cv2.VideoCapture(video.path)
    try:
        for index in range(max(indices) + 1):
            ok, frame = capture.read()
            if not ok:
                raise PipelineError(f"Ontbrekend bronframe {index}.")
            if index not in positions:
                continue
            path = destination / f"frame-{index:06d}.jpg"
            if not cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95]):
                raise PipelineError("Kan referentiebeeld niet opslaan.")
            x, y = positions[index] % columns * cell_width, positions[index] // columns * cell_height
            scale = min(cell_width / video.width, 216 / video.height)
            w, h = round(video.width * scale), round(video.height * scale)
            sheet[y : y + h, x : x + w] = cv2.resize(frame, (w, h))
            cv2.putText(
                sheet,
                f"frame {index} | {index / video.fps:.3f}s",
                (x + 8, y + 239),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (230, 230, 230),
                1,
            )
    finally:
        capture.release()
    cv2.imwrite(str(destination / "contact-sheet.jpg"), sheet)
    write_json(
        destination / "guide.json",
        {
            "image_size": list(video.size),
            "coordinates": "Original source pixels; use full-resolution individual images",
            "field_point_ids_uv": {
                identifier: np.asarray(uv).tolist() for identifier, uv in POINTS_UV.items()
            },
            "human_reviewed": False,
            "selected_frame_indices": indices,
            "no_model_predictions_exported": True,
        },
    )
    print(f"Exported {len(indices)} original review frames: {destination}", flush=True)


def main():
    """Voer de gekozen voorbereidings-, replay-, evaluatie- of reviewexportstap van de veldvergelijking
    uit.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare")
    p.add_argument("video", type=Path)
    p.add_argument("--kind", choices=["broadcast", "fixed"], required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--selection", type=Path)
    p = commands.add_parser("run")
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--detections", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--skip-video", action="store_true")
    p = commands.add_parser("export-review")
    p.add_argument("comparison", type=Path)
    p = commands.add_parser("evaluate")
    p.add_argument("comparisons", type=Path, nargs="+")
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.video, args.kind, args.output, args.selection)
    elif args.command == "run":
        run(args.bundle, args.detections, args.output, not args.skip_video)
    elif args.command == "export-review":
        export_review(args.comparison)
    else:
        evaluate(args.comparisons, args.output)


if __name__ == "__main__":
    main()
