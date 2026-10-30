"""Frozen, single-pass PnL grass-crop experiment; no labels choose the crop."""

import argparse
import copy
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import torch

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.course_field_evaluation import score
from football_pipeline.field_crop_observations import observe_cropped
from football_pipeline.field_learning import image_observation, load_model, upstream_runtime
from football_pipeline.field_motion import MOTION_RANK_SETTINGS, CameraCalibration, estimate_checked
from football_pipeline.field_pose import field_crop

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "artifacts/joint-retrain-20261027-v2/selected-field-runtime.json"


def sources(kind, split):
    if kind == "historical":
        index = read_json(ROOT / "artifacts/course-improvement-20261019/field/dataset-index.json")
        cache = (
            ROOT
            / "artifacts/course-improvement-20261019/field-policy-full-last/observations-6c30ef8aa93dc16a6d5c1f7beb965e9ba17b7759fb77faa08cfb5112381e7ff1.json"
        )
        baseline = read_json(cache)["observations"]
        selected = [
            (r, o)
            for r, o in zip(index["frames"], baseline, strict=True)
            if split == "all" or r["split"] == split
        ]
        for row, observation in selected:
            if (
                sha256_file(row["image"]) != row["image_sha256"]
                or sha256_file(row["label"]) != row["label_sha256"]
            ):
                raise ValueError("Frozen historical frame or annotation changed")
            yield row, cv2.imread(row["image"]), observation
    elif kind == "dense":
        frames = read_json(ROOT / "data/broadcast-temporal-v1/manifest.json")["frames"]
        grouped = defaultdict(list)
        for row in frames:
            if split == "all" or row["split"] == ("val" if split == "valid" else split):
                grouped[row["clip"]].append(row)
        for clip, rows in grouped.items():
            metrics = read_json(
                ROOT
                / "artifacts/broadcast-reliability-day2/field-native-v1"
                / clip
                / "projection-metrics.json"
            )
            observations = [
                json.loads(line) for line in Path(metrics["calibration_bundle"]).read_text().splitlines()
            ]
            for row, observation in zip(rows, observations, strict=True):
                if sha256_file(row["image"]) != row["image_sha256"]:
                    raise ValueError("Frozen continuous frame changed")
                yield row, cv2.imread(row["image"]), observation
    else:
        original = ROOT / "runs/0b2006b23d066695e0c35ebe1d282748e2d083217f3a33ee638783db251c4167"
        manifest = read_json(original / "runmanifest.json")
        video = manifest["video"]
        if sha256_file(video["path"]) != video["sha256"]:
            raise ValueError("Original video changed")
        observations = [
            json.loads(line) for line in (original / "observations.jsonl").read_text().splitlines()
        ]
        capture = cv2.VideoCapture(video["path"])
        try:
            for i, observation in enumerate(observations):
                if not capture.grab():
                    raise ValueError("Incomplete source video")
                if kind == "own-sparse" and i % 25:
                    continue
                ok, frame = capture.retrieve()
                if not ok:
                    raise ValueError("Cannot decode original frame")
                row = {
                    "clip": "own-broadcast",
                    "frame_index": i,
                    "fps": video["fps_num"] / video["fps_den"],
                    "image_sha256": digest_json([video["sha256"], i]),
                }
                yield row, frame, observation
        finally:
            capture.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("historical", "dense", "own-sparse", "own"), required=True)
    parser.add_argument("--split", choices=("train", "valid", "all"), default="train")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    runtime = upstream_runtime(RUNTIME)
    models = None
    identity = {
        "source": args.source,
        "split": args.split,
        "runtime_sha256": sha256_file(RUNTIME),
        "code": {
            str(p): sha256_file(p)
            for p in (
                Path(__file__),
                ROOT / "src/football_pipeline/field_crop_observations.py",
                ROOT / "src/football_pipeline/field_pose.py",
                ROOT / "src/football_pipeline/field_learning.py",
            )
        },
        "settings": MOTION_RANK_SETTINGS,
        "human_review_completed": False,
        "independent_final_test_completed": False,
    }
    inputs = args.output / "inputs.json"
    if inputs.exists() and read_json(inputs) != identity:
        raise ValueError("Crop experiment inputs changed; use a new directory")
    write_json(inputs, identity)
    rows, baseline, changed, states = [], [], [], []
    crops, camera, previous_clip = 0, None, None
    started = time.perf_counter()
    for number, (row, frame, original) in enumerate(sources(args.source, args.split)):
        if frame is None:
            raise ValueError("Unreadable source image")
        roi = field_crop(frame)
        key = digest_json([row["image_sha256"], roi, identity])
        cached_path = args.output / f"observation-{key}.json"
        if roi == (0, 0, frame.shape[1], frame.shape[0]):
            candidate = copy.deepcopy(original)
        elif cached_path.exists():
            candidate = read_json(cached_path)
            crops += 1
        else:
            if models is None:
                models = [load_model(runtime, role, "cuda:0").eval() for role in ("keypoints", "lines")]
            candidate = observe_cropped(
                frame, lambda image: image_observation(models, image, "cuda:0"), roi=roi
            )
            write_json(cached_path, candidate)
            crops += 1
        rows.append(row)
        baseline.append(original)
        changed.append(candidate)
        direct = estimate_checked(candidate, candidate["image_size"], MOTION_RANK_SETTINGS)
        if args.source in {"dense", "own"}:
            if row["clip"] != previous_clip:
                camera = CameraCalibration(row["fps"], MOTION_RANK_SETTINGS)
                previous_clip = row["clip"]
            direct = camera.update(frame, direct, row["frame_index"])
        states.append(direct)
        if (number + 1) % 25 == 0:
            print(
                f"{args.source} {number + 1}: {crops} cropped, {sum(s['status'] == 'valid' for s in states)} valid",
                flush=True,
            )
    summary = {
        "frames": len(rows),
        "cropped": crops,
        "elapsed_s": time.perf_counter() - started,
        "status_counts": dict(Counter(s["status"] for s in states)),
        "direct_baseline_valid": sum(
            estimate_checked(o, o["image_size"], MOTION_RANK_SETTINGS)["status"] == "valid" for o in baseline
        ),
    }
    if args.source == "historical":
        summary["baseline"] = score(baseline, rows, MOTION_RANK_SETTINGS)
        summary["candidate"] = score(changed, rows, MOTION_RANK_SETTINGS)
    groups = defaultdict(list)
    for row, observation, state in zip(rows, changed, states, strict=True):
        groups[row.get("clip", "historical")].append((row, observation, state))
    for clip, entries in groups.items():
        directory = args.output / clip
        directory.mkdir(exist_ok=True)
        write_json(directory / "states.json", {"frames": [e[2] for e in entries]})
        write_json(directory / "observations.json", {"frames": [e[1] for e in entries]})
        write_json(directory / "rows.json", {"frames": [e[0] for e in entries]})
    write_json(args.output / "summary.json", summary)
    print(summary, flush=True)


if __name__ == "__main__":
    main()
