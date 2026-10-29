"""Reproduce the dev-00 pilot; never convert agent measurements into human approvals."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.contracts import PipelineError, read_json, sha256_file, write_json
from football_pipeline.geometry import create_calibration
from football_pipeline.pipeline import code_identity, process_video, validate_completed
from football_pipeline.render import calibration_preview
from football_pipeline.video import ROOT, find_tool, inspect_video, read_frame, tool_versions


def prepare(output: Path, points_config: dict):
    """Reconstrueer het exacte pilotfragment en controleer bronvideo en gekozen kalibratiepunten voor de
    proef.
    """
    if (points_config.get("source_frame_start"), points_config.get("source_frame_end_exclusive")) != (0, 150):
        raise PipelineError("Deze pilot is uitsluitend voor bronframes 0 tot en met 149.")
    source = ROOT / "assets/videos/HBTFZwMdcCw.mp4"
    source_record = read_json(source.with_suffix(".source.json"))
    if source.stat().st_size != source_record["bytes"]:
        raise PipelineError(
            "Echte bronvideo ontbreekt; voer git lfs pull --include=assets/videos/HBTFZwMdcCw.mp4 uit."
        )
    source_hash = sha256_file(source)
    if source_hash != source_record["sha256"] or source_hash != points_config["source_sha256"]:
        raise PipelineError("Bronvideo wijkt af van de geregistreerde identiteit van deze puntselectie.")
    selection_path = ROOT / "configs/HBTFZwMdcCw-selection.json"
    group = next((w for w in read_json(selection_path)["windows"] if w["group_id"] == "dev-00"), None)
    if not group or (group["split"], group["start_s"], group["end_s"]) != ("train", 0, 6):
        raise PipelineError("De ontwikkelselectie is gewijzigd; stem het fragment opnieuw met persoon 1 af.")
    output.mkdir(parents=True, exist_ok=True)
    inspection_path = output / "source-inspection.json"
    if inspection_path.is_file() and read_json(inspection_path).get("sha256") == source_hash:
        inspection = read_json(inspection_path)
    else:
        inspection = asdict(inspect_video(source))
        write_json(inspection_path, inspection)
    if (inspection["width"], inspection["height"], inspection["fps_num"], inspection["fps_den"]) != (
        3840,
        960,
        25,
        1,
    ):
        raise PipelineError("Bronformaat of framerate wijkt af van de afgesproken PANORIS-bron.")
    clip = output / "dev-00-frames-000000-000149.mp4"
    provenance_path = output / "clip-provenance.json"
    if clip.is_file() and provenance_path.is_file():
        previous = read_json(provenance_path)
        if (
            previous["source"]["sha256"] != source_hash
            or previous["clip"]["sha256"] != sha256_file(clip)
            or previous["source_frame_start"] != 0
            or previous["source_frame_end_exclusive"] != 150
        ):
            raise PipelineError(
                "Bestaand pilotfragment heeft andere provenance; kies een nieuwe --output map."
            )
        command = previous["ffmpeg_command"]
    else:
        if clip.exists():
            raise PipelineError("Pilotbestand bestaat zonder provenance; kies een nieuwe --output map.")
        command = [
            find_tool("ffmpeg"),
            "-v",
            "error",
            "-n",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-frames:v",
            "150",
            "-vf",
            "setpts=PTS-STARTPTS",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-fps_mode",
            "passthrough",
            "-an",
            "-movflags",
            "+faststart",
            str(clip),
        ]
        subprocess.run(command, check=True)
    video = inspect_video(clip)
    if video.size != (3840, 960) or video.fps != 25 or video.frame_count != 150:
        raise PipelineError("Pilotfragment moet exact 150 frames van 3840x960 op 25 fps bevatten.")
    write_json(
        provenance_path,
        {
            "source": inspection,
            "clip": asdict(video),
            "source_frame_start": 0,
            "source_frame_end_exclusive": 150,
            "selection_group": "dev-00",
            "selection_split": "train",
            "selection_sha256": sha256_file(selection_path),
            "test_frames_processed": 0,
            "source_inspection_scope": "Full source decoded for timestamp/format inspection; model inference and visual pilot review use source frames 0-149 only",
            "ffmpeg_command": command,
            "spatial_resize": False,
            "encoding": "H264 CRF18 derived copy; decoded pixels differ from VP9 source",
            "tools": tool_versions(),
        },
    )
    for index in [0, 75, 149]:
        if not cv2.imwrite(str(output / f"bronframe_{index:03d}.png"), read_frame(video, index)):
            raise PipelineError("Broncontrolebeeld kan niet worden bewaard.")
    return video


def assess_geometry(video, config: dict, output: Path):
    """Controleer de aangeklikte kalibratie en de temporele camerastabiliteit en schrijf een technisch
    gemarkeerd geometrieverslag.
    """
    if list(video.size) != config["image_size"]:
        raise PipelineError("Puntselectie hoort niet bij dit beeldformaat.")
    points = config["points"]
    write_json(output / "point-correspondences.json", points)
    try:
        calibration = create_calibration(video, points, config["reference_frame"])
    except PipelineError as exc:
        write_json(
            output / "geometry-report.json",
            {
                "schema_version": 1,
                "clip_sha256": video.sha256,
                "technical_passed": False,
                "human_reviewed": False,
                "reason": str(exc),
                "points": points,
                "video": asdict(video),
            },
        )
        raise
    inverse = np.linalg.inv(np.asarray(calibration.homography))
    reference = read_frame(video, config["reference_frame"])
    minimum_ncc = config["camera_patch_min_ncc"]
    maximum_shift = config["camera_patch_max_shift_px"]
    anchors = set(config["temporal_anchor_names"])
    names = {point["name"] for point in points}
    if not anchors.issubset(names) or len(anchors) < 6:
        raise PipelineError("Cameracontrole vereist minstens zes vastgelegde veldankers.")
    samples, per_frame = [], []
    camera_ok = True
    diagonal = float(np.hypot(*video.size))
    for index in [0, video.frame_count // 2, video.frame_count - 1]:
        frame = read_frame(video, index)
        annotated = calibration_preview(frame, points, grid=False)
        frame_errors = []
        for point in points:
            x, y = round(point["x"]), round(point["y"])
            if x < 20 or y < 20 or x + 21 > video.width or y + 21 > video.height:
                raise PipelineError("Veldanker ligt te dicht bij de beeldrand voor de gekozen patchcontrole.")
            template = cv2.cvtColor(reference[y - 12 : y + 13, x - 12 : x + 13], cv2.COLOR_BGR2GRAY)
            search = cv2.cvtColor(frame[y - 20 : y + 21, x - 20 : x + 21], cv2.COLOR_BGR2GRAY)
            _, score, _, location = cv2.minMaxLoc(cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED))
            dx, dy = location[0] - 8, location[1] - 8
            shift = float(np.hypot(dx, dy))
            is_anchor = point["name"] in anchors
            if is_anchor:
                camera_ok &= score >= minimum_ncc and shift <= maximum_shift
            sample = {
                "frame_index": index,
                "point": point["name"],
                "ncc": score,
                "dx": dx,
                "dy": dy,
                "camera_anchor": is_anchor,
            }
            if point["role"] == "check":
                xyz = inverse @ [point["u"], point["v"], 1]
                prediction = xyz[:2] / xyz[2]
                measured = np.array([point["x"] + dx, point["y"] + dy])
                error = float(np.linalg.norm(prediction - measured))
                sample["reprojection_error_px"] = error
                frame_errors.append(error)
                target = tuple(np.round(prediction).astype(int))
                cv2.drawMarker(annotated, target, (0, 0, 255), cv2.MARKER_CROSS, 16, 2)
                cv2.line(annotated, tuple(np.round(measured).astype(int)), target, (0, 0, 255), 2)
            samples.append(sample)
        per_frame.append(
            {
                "frame_index": index,
                "check_errors_px": frame_errors,
                "median_error_px": float(np.median(frame_errors)),
                "max_error_px": max(frame_errors),
            }
        )
        if not cv2.imwrite(str(output / f"geometrie_{index:03d}.jpg"), annotated):
            raise PipelineError("Geometriecontrolebeeld kan niet worden bewaard.")
    checks_ok = all(
        s["median_error_px"] <= 0.005 * diagonal and s["max_error_px"] <= 0.01 * diagonal for s in per_frame
    )
    report = {
        "schema_version": 1,
        "clip_sha256": video.sha256,
        "technical_passed": bool(camera_ok and checks_ok),
        "human_reviewed": False,
        "point_selection": config["point_selection"],
        "reference_errors_px": calibration.check_errors_px,
        "reference_median_px": float(np.median(calibration.check_errors_px)),
        "reference_max_px": max(calibration.check_errors_px),
        "thresholds": {
            "median_px": 0.005 * diagonal,
            "max_px": 0.01 * diagonal,
            "anchor_min_ncc": minimum_ncc,
            "anchor_max_shift_px": maximum_shift,
        },
        "camera_anchor_check_passed": bool(camera_ok),
        "per_frame": per_frame,
        "patch_samples": samples,
        "limitations": [
            "Agent-selected points; human geometric review pending",
            "Sparse checks do not prove metric accuracy or absence of panoramic distortion",
            "Goal centres estimated from goalpost feet; patch matching on plain lines is ambiguous",
            "Near-touchline midpoint differs from straight corner polygon; no clipping or correction applied",
        ],
    }
    write_json(output / "geometry-report.json", report)
    calibration.review = {
        "kind": "agent_technical",
        "agent": "Codex",
        "approved": False,
        "human_reviewed": False,
        "technical_passed": report["technical_passed"],
        "static_camera_technical_check": bool(camera_ok),
        "temporal_frames": [0, video.frame_count // 2, video.frame_count - 1],
        "source": "User-supplied PANORIS video HBTFZwMdcCw",
        "usage": "Technical dev-00 pilot; human source/use confirmation pending",
    }
    write_json(output / "calibration-technical.json", asdict(calibration))
    if not report["technical_passed"]:
        raise PipelineError(
            "Geometrie/cameracontrole faalt. Rapport bewaard; geen minimapverwerking gestart."
        )
    return calibration, report


def summarize(result, geometry: dict, output: Path) -> dict:
    """Combineer echte rungegevens en geometriecontrole tot het pilotrapport zonder technische controle
    als menselijke acceptatie voor te stellen.
    """
    manifest = validate_completed(result.directory)
    counts, statuses, per_frame = Counter(), Counter(), []
    with (result.directory / "framegegevens.jsonl").open(encoding="utf-8") as stream:
        for record in map(json.loads, stream):
            persons = [d for d in record["detections"] if d["semantic_class"] == "person"]
            for detection in record["detections"]:
                counts[detection["semantic_class"]] += 1
                statuses[detection["projection_status"]] += 1
                if detection["track_id"] is not None:
                    raise PipelineError("Onverwachte track-ID in de trackingvrije pilot.")
                if detection["semantic_class"] == "ball" and detection["field_position"] is not None:
                    raise PipelineError("De bal mag geen grondprojectie krijgen.")
            per_frame.append(
                {
                    "frame_index": record["frame_index"],
                    "timestamp_s": record["timestamp_s"],
                    "person_count_floor_0_10": len(persons),
                    "person_count_display_0_25": sum(d["confidence"] >= 0.25 for d in persons),
                    "minimap_person_count_display_0_25": sum(
                        d["confidence"] >= 0.25 and d["field_position"] is not None for d in persons
                    ),
                }
            )
    if [r["frame_index"] for r in per_frame] != list(range(150)):
        raise PipelineError("Uitvoer mist frames uit het afgesproken fragment.")
    summary = {
        "schema_version": 1,
        "status": "technical_pilot_completed_human_review_pending",
        "run_directory": str(result.directory),
        "video": str(result.video_path),
        "run_key": manifest["cache_key"],
        "clip_sha256": manifest["video"]["sha256"],
        "source_sha256": read_json(output / "clip-provenance.json")["source"]["sha256"],
        "source_frames": [0, 149],
        "frames": len(per_frame),
        "test_frames_processed": 0,
        "geometry_reference_median_px": geometry["reference_median_px"],
        "geometry_reference_max_px": geometry["reference_max_px"],
        "geometry_technical_passed": True,
        "detection_counts_floor_0_10": dict(counts),
        "projection_counts": dict(statuses),
        "person_display_min": min(r["person_count_display_0_25"] for r in per_frame),
        "person_display_max": max(r["person_count_display_0_25"] for r in per_frame),
        "minimap_person_display_min": min(r["minimap_person_count_display_0_25"] for r in per_frame),
        "minimap_person_display_max": max(r["minimap_person_count_display_0_25"] for r in per_frame),
        "measurements": manifest["measurements"],
        "per_frame": per_frame,
        "human_reviewed": False,
        "tracking_enabled": False,
        "mvp_accepted": False,
        "note": "Detection counts are not TP/FP/FN, unique people, or mAP. No final football accuracy claim.",
    }
    write_json(output / "pilot-summary.json", summary)
    return summary


def main(argv=None):
    """Bereid het vaste pilotfragment voor, controleer kalibratie en voer de technisch gemarkeerde
    videopipeline uit.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/panoris-pilot")
    parser.add_argument("--points", type=Path, default=ROOT / "configs/panoris-pilot-points.json")
    parser.add_argument("--models", type=Path, default=ROOT / "configs/models-panoris-pilot-1920.json")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        output = args.output.resolve()
        config = read_json(args.points)
        video = prepare(output, config)
        if args.prepare_only:
            print(video.path)
            return 0
        calibration, geometry = assess_geometry(video, config, output)
        print(
            f"Geometrie: mediaan {geometry['reference_median_px']:.2f} px, max {geometry['reference_max_px']:.2f} px",
            flush=True,
        )
        result = process_video(
            video.path,
            calibration,
            args.models,
            output / "runs",
            technical_pilot=True,
            progress=lambda n, total, elapsed: print(f"{n}/{total} frames | {elapsed:.1f} s", flush=True),
        )
        summary = summarize(result, geometry, output)
        write_json(
            output / "pilot-provenance.json",
            {
                "code": code_identity(),
                "script_sha256": sha256_file(__file__),
                "points_sha256": sha256_file(args.points),
                "models_sha256": sha256_file(args.models),
            },
        )
        print(summary["video"])
        return 0
    except (PipelineError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"Pilot gestopt: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
