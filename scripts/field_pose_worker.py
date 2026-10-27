"""Write checked, traceable field-pose observations for a complete local video."""

import argparse
import importlib.metadata
import json
import time
from pathlib import Path

import cv2
import torch

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.field_layout import COORDINATE_SYSTEM, POLICY
from football_pipeline.field_lens import estimate_lens
from football_pipeline.field_motion import DEFAULT_SETTINGS
from football_pipeline.field_pose import FieldPoseEstimator, validate_pose_runtime


def run(args):
    runtime = read_json(args.runtime)
    validate_pose_runtime(runtime)
    torch.set_num_threads(4)
    estimator = FieldPoseEstimator(
        runtime["weights_keypoints"],
        device=runtime.get("device", 0),
        imgsz=runtime.get("imgsz", 960),
        settings=runtime.get("calibration_settings", DEFAULT_SETTINGS),
    )
    capture = cv2.VideoCapture(str(args.video))
    w, h = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    args.output.mkdir(parents=True, exist_ok=True)
    pending = args.output / "observations.partial.jsonl"
    lens, count, started = None, 0, time.monotonic()
    with pending.open("w", encoding="utf-8") as stream:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if count == 0 and runtime.get("automatic_lens_correction", True):
                lens = estimate_lens(frame)
            row = estimator.observe(frame, lens=lens, crop=runtime.get("grass_crop", True))
            row.update(frame_index=count, timestamp_s=count * args.fps_den / args.fps_num)
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            count += 1
            if count % 10 == 0:
                print(f"{count}/{args.frames} frames", flush=True)
    capture.release()
    if count != args.frames:
        raise ValueError("Decoded frame count does not match the checked source")
    destination = args.output / "observations.jsonl"
    pending.replace(destination)
    package = Path(__file__).resolve().parents[1] / "src/football_pipeline"
    manifest = {
        "schema_version": 3,
        "score_storage": "all_field_pose_keypoints_before_threshold",
        "kind": "automatic_field_observations",
        "evidence_kind": "field_pose",
        "coordinate_system": COORDINATE_SYSTEM,
        "policy": POLICY,
        "video": {
            "sha256": sha256_file(args.video),
            "image_size": [w, h],
            "frame_count": count,
            "fps_num": args.fps_num,
            "fps_den": args.fps_den,
        },
        "source": args.source,
        "usage": args.usage,
        "models": runtime["models"],
        "worker_sha256": sha256_file(__file__),
        "dependencies": {
            k: importlib.metadata.version(k) for k in ("torch", "ultralytics", "numpy", "opencv-python")
        },
        "implementation_sha256": {
            n: sha256_file(package / n) for n in ("field_pose.py", "field_lens.py", "field_motion.py")
        },
        "observations_sha256": sha256_file(destination),
        "runtime_s": time.monotonic() - started,
        "lens": lens,
        "lens_policy": "first_frame_measured_static_lens; image controls are not human accuracy evidence",
        "project_human_review_completed": False,
        "independent_final_test_completed": False,
    }
    write_json(args.output / "automatic_calibration.json", manifest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("video", "runtime", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("source", "usage"):
        parser.add_argument("--" + name, required=True)
    for name in ("fps-num", "fps-den", "frames"):
        parser.add_argument("--" + name, type=int, required=True)
    run(parser.parse_args())
