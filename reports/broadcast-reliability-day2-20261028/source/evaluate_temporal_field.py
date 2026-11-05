"""Measure automatic projection against provider positions on fixed continuous windows."""

import argparse
import gzip
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.automatic_calibration import (
    AutomaticCalibration,
    load_automatic_calibration,
    prepare_automatic_calibration,
    transform,
)
from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.field_motion import (
    DEFAULT_SETTINGS,
    MOTION_RANK_SETTINGS,
    RANK_GUARD_SETTINGS,
    CameraCalibration,
)
from football_pipeline.video import find_tool, inspect_video

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/broadcast-reliability-day2/field-native-v1"


def make_video(rows, directory):
    target = directory / "native-lossless.mp4"
    if target.exists():
        video = inspect_video(target)
        if video.frame_count != len(rows):
            raise ValueError("Incomplete lossless video")
        return target
    legacy = directory / "native-lossless.avi"
    if not legacy.exists():
        partial = directory / "native-partial.avi"
        size = (rows[0]["width"], rows[0]["height"])
        writer = cv2.VideoWriter(str(partial), cv2.VideoWriter_fourcc(*"FFV1"), rows[0]["fps"], size)
        if not writer.isOpened():
            raise ValueError("Lossless video encoder unavailable")
        try:
            for row in rows:
                if sha256_file(row["image"]) != row["image_sha256"]:
                    raise ValueError("Source image changed")
                writer.write(cv2.imread(row["image"]))
        finally:
            writer.release()
        partial.replace(legacy)
    encoded = directory / "native-lossless.partial.mp4"
    subprocess.run(
        [
            find_tool("ffmpeg"),
            "-v",
            "error",
            "-y",
            "-i",
            str(legacy),
            "-c:v",
            "libx264rgb",
            "-crf",
            "0",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "bgr24",
            str(encoded),
        ],
        check=True,
    )
    # The app accepts MP4 only. RGB-lossless H264 preserves the exact source
    # pixels while satisfying that existing interface; no app behavior changes.
    capture = cv2.VideoCapture(str(encoded))
    try:
        for row in rows:
            ok, frame = capture.read()
            if not ok or not np.array_equal(frame, cv2.imread(row["image"])):
                raise ValueError("Lossless video verification failed")
        if capture.read()[0]:
            raise ValueError("Extra video frame")
    finally:
        capture.release()
    encoded.replace(target)
    return target


def compare_clip(rows, directory, geometry_controls=False, motion_rank=False):
    result_path = directory / "projection-metrics.json"
    if result_path.exists():
        return read_json(result_path)
    original = OUTPUT / rows[0]["clip"]
    video_path = make_video(rows, original if geometry_controls else directory)
    video = inspect_video(video_path)
    if geometry_controls:
        baseline = read_json(original / "projection-metrics.json")
        bundle = load_automatic_calibration(
            Path(baseline["calibration_bundle"]).parent / "automatic_calibration.json"
        )
    else:
        bundle = prepare_automatic_calibration(
            video_path,
            ROOT / "artifacts/joint-retrain-20261027-v2/selected-field-runtime.json",
            directory / "calibration",
            source="Existing SoccerNet development games; provider labels only",
            usage="Local educational development comparison; not independent accuracy",
            progress=lambda n, total, elapsed: print(f"Field {rows[0]['clip']}: {n}/{total}", flush=True),
        )
    settings = (
        MOTION_RANK_SETTINGS
        if motion_rank
        else RANK_GUARD_SETTINGS
        if geometry_controls
        else DEFAULT_SETTINGS
    )
    calibrated = AutomaticCalibration(bundle.manifest, bundle.observations_path, settings)
    states = calibrated.frames(video)
    camera = CameraCalibration(video.fps, settings)
    labels = ROOT / "data/broadcast-pitch-v1/provider-labels" / f"{rows[0]['clip']}.json.gz"
    provider = json.loads(gzip.decompress(labels.read_bytes()))
    by_image = defaultdict(list)
    for annotation in provider["annotations"]:
        by_image[str(annotation["image_id"])].append(annotation)
    ids = {int(Path(im["file_name"]).stem) - 1: str(im["image_id"]) for im in provider["images"]}
    errors, statuses, records = [], Counter(), []
    total_points, projected_points = 0, 0
    for row, direct in zip(rows, states, strict=True):
        frame = cv2.imread(row["image"])
        state = camera.update(frame, direct, row["frame_index"])
        statuses[state["status"]] += 1
        records.append(state)
        for a in by_image[ids[row["source_frame_index"]]]:
            box, pitch = a.get("bbox_image"), a.get("bbox_pitch")
            if a.get("category_id") not in {1, 2} or not box or not pitch:
                continue
            x, y = pitch.get("x_bottom_middle"), pitch.get("y_bottom_middle")
            if x is None or y is None or not -52.5 <= x <= 52.5 or not -34 <= y <= 34:
                continue
            total_points += 1
            if state["status"] != "valid":
                continue
            try:
                uv = transform(
                    [[box["x"] + box["w"] / 2, box["y"] + box["h"]]],
                    np.asarray(state["homography"], dtype=float),
                )[0]
            except ValueError:
                continue
            error = np.linalg.norm((uv - [(x + 52.5) / 105, (y + 34) / 68]) * [105, 68])
            errors.append(float(error))
            projected_points += 1
    result = {
        "clip": rows[0]["clip"],
        "split": rows[0]["split"],
        "game_id": rows[0]["game_id"],
        "frames": len(rows),
        "valid_frames": statuses["valid"],
        "status_counts": dict(statuses),
        "coverage": statuses["valid"] / len(rows),
        "reference_player_points": total_points,
        "projected_points": projected_points,
        "errors_m": errors,
        "median_error_m": float(np.median(errors)) if errors else None,
        "p90_error_m": float(np.quantile(errors, 0.9)) if errors else None,
        "reference": "provider pitch positions; 105x68 template; not human-reviewed accuracy",
        "source_frames_pixel_identical": True,
        "video_sha256": video.sha256,
        "dataset_manifest_sha256": sha256_file(ROOT / "data/broadcast-temporal-v1/manifest.json"),
        "calibration_bundle": str(bundle.observations_path),
        "independent_final_test": False,
        "control_selection": "canonical_rank_motion_bridge"
        if motion_rank
        else "canonical_rank_guard"
        if geometry_controls
        else "semantic_tertiles",
    }
    write_json(directory / "states.json", {"frames": records})
    write_json(result_path, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--geometry-controls", action="store_true")
    parser.add_argument("--motion-rank", action="store_true")
    args = parser.parse_args()
    if args.motion_rank:
        args.geometry_controls = True
    groups = defaultdict(list)
    for row in read_json(ROOT / "data/broadcast-temporal-v1/manifest.json")["frames"]:
        groups[row["clip"]].append(row)
    results = []
    output = (
        OUTPUT.parent / "field-motion-rank-v2"
        if args.motion_rank
        else OUTPUT.parent / "field-controls-policy-v2"
        if args.geometry_controls
        else OUTPUT
    )
    for clip, rows in groups.items():
        directory = output / clip
        directory.mkdir(parents=True, exist_ok=True)
        if args.prepare_only:
            make_video(rows, directory)
            print(f"Verified lossless source {clip}", flush=True)
        else:
            results.append(
                compare_clip(
                    rows, directory, geometry_controls=args.geometry_controls, motion_rank=args.motion_rank
                )
            )
            write_json(output / "summary.json", {"per_clip": results, "independent_final_test": False})


if __name__ == "__main__":
    main()
