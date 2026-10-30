"""Replay motion-only layout eligibility on frozen native broadcast frames."""

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from evaluate_backward_field import point_errors

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.field_layout_bridge import LAYOUT_BRIDGE_RULE, estimate_layout_bridge
from football_pipeline.field_motion import MOTION_RANK_SETTINGS, CameraCalibration, estimate_checked

ROOT = Path(__file__).resolve().parents[1]


def evaluate(name, observations, baseline, frames, fps, output, rows=None):
    directory = output / name
    directory.mkdir(parents=True, exist_ok=True)
    identity = digest_json(
        [
            observations,
            baseline,
            MOTION_RANK_SETTINGS,
            sha256_file(ROOT / "src/football_pipeline/field_layout_bridge.py"),
            sha256_file(ROOT / "src/football_pipeline/field_motion.py"),
            rows,
        ]
    )
    target = directory / "projection-metrics.json"
    if target.exists():
        saved = read_json(target)
        if saved["identity"] != identity:
            raise ValueError("Layout experiment inputs changed")
        return saved
    camera = CameraCalibration(fps, MOTION_RANK_SETTINGS)
    states, direct_anchors, softened = [], set(), []
    started = time.perf_counter()
    for index, (observation, frame) in enumerate(zip(observations, frames, strict=True)):
        original = estimate_checked(observation, observation["image_size"], MOTION_RANK_SETTINGS)
        direct = estimate_layout_bridge(observation, observation["image_size"], MOTION_RANK_SETTINGS)
        if direct["status"] == "valid":
            if original["status"] != "valid":
                raise ValueError("Motion eligibility created a new direct anchor")
            direct_anchors.add(index)
        if direct["status"] != original["status"]:
            softened.append(index)
        state = camera.update(frame, direct, index)
        if state["status"] == "valid" and state["source"] == "tracked":
            if state["reference_frame"] not in direct_anchors or state["age_s"] > 2:
                raise ValueError("An unverified/expired anchor escaped")
        states.append(state)
        if (index + 1) % 150 == 0:
            print(name, index + 1, "valid", sum(s["status"] == "valid" for s in states), flush=True)
    gained = [
        i
        for i, (a, b) in enumerate(zip(baseline, states, strict=True))
        if a["status"] != "valid" and b["status"] == "valid"
    ]
    lost = [
        i
        for i, (a, b) in enumerate(zip(baseline, states, strict=True))
        if a["status"] == "valid" and b["status"] != "valid"
    ]
    common_same = all(
        np.allclose(a["homography"], b["homography"], rtol=0, atol=1e-12)
        for a, b in zip(baseline, states)
        if a["status"] == b["status"] == "valid"
    )
    result = {
        "identity": identity,
        "rule": LAYOUT_BRIDGE_RULE,
        "frames": len(states),
        "baseline_valid": sum(s["status"] == "valid" for s in baseline),
        "valid_frames": sum(s["status"] == "valid" for s in states),
        "gained_frames": gained,
        "lost_frames": lost,
        "common_matrices_unchanged": common_same,
        "softened_frames": softened,
        "status_counts": dict(Counter(s["status"] for s in states)),
        "elapsed_s": time.perf_counter() - started,
        "human_review_completed": False,
        "independent_final_test": False,
    }
    if rows is not None:
        old_errors, new_errors = point_errors(rows, baseline, name), point_errors(rows, states, name)
        errors = [e for k, e in new_errors.items() if k not in old_errors]
        result.update(
            dataset_manifest_sha256=sha256_file(ROOT / "data/broadcast-temporal-v1/manifest.json"),
            added_points=len(errors),
            added_median_m=float(np.median(errors)) if errors else None,
            added_p90_m=float(np.quantile(errors, 0.9)) if errors else None,
            added_errors_m=errors,
            common_point_errors_unchanged=all(
                k in new_errors and abs(e - new_errors[k]) < 1e-10 for k, e in old_errors.items()
            ),
        )
    write_json(directory / "states.json", {"frames": states})
    write_json(target, result)
    print(
        {k: v for k, v in result.items() if k not in {"gained_frames", "softened_frames", "added_errors_m"}},
        flush=True,
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--split", choices=("train", "val", "all"), default="train")
    parser.add_argument("--own-clip", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.own_clip:
        source = ROOT / "runs/0b2006b23d066695e0c35ebe1d282748e2d083217f3a33ee638783db251c4167"
        manifest = read_json(source / "runmanifest.json")
        video = manifest["video"]
        if sha256_file(video["path"]) != video["sha256"]:
            raise ValueError("Original video changed")
        observations = [json.loads(line) for line in (source / "observations.jsonl").read_text().splitlines()]
        baseline = [
            json.loads(line)["calibration"]
            for line in (
                ROOT
                / "runs/316e0824bc9fbb019691a294474bbc008c9701072b5309b6ee3939e759e6c386/framegegevens.jsonl"
            )
            .read_text()
            .splitlines()
        ]

        def frames():
            capture = cv2.VideoCapture(video["path"])
            try:
                for _ in observations:
                    ok, frame = capture.read()
                    if not ok:
                        raise ValueError("Incomplete source video")
                    yield frame
            finally:
                capture.release()

        evaluate(
            "own-broadcast",
            observations,
            baseline,
            frames(),
            video["fps_num"] / video["fps_den"],
            args.output,
        )
        return
    grouped = defaultdict(list)
    for row in read_json(ROOT / "data/broadcast-temporal-v1/manifest.json")["frames"]:
        if args.split == "all" or row["split"] == args.split:
            grouped[row["clip"]].append(row)
    results = []
    for clip, rows in grouped.items():
        original = read_json(
            ROOT / "artifacts/broadcast-reliability-day2/field-native-v1" / clip / "projection-metrics.json"
        )
        observations = [
            json.loads(line) for line in Path(original["calibration_bundle"]).read_text().splitlines()
        ]
        baseline = read_json(
            ROOT / "artifacts/broadcast-reliability-day2/field-motion-rank-v2" / clip / "states.json"
        )["frames"]

        def frames():
            for row in rows:
                if sha256_file(row["image"]) != row["image_sha256"]:
                    raise ValueError("Source image changed")
                frame = cv2.imread(row["image"])
                if frame is None:
                    raise ValueError("Cannot decode source frame")
                yield frame

        results.append(evaluate(clip, observations, baseline, frames(), rows[0]["fps"], args.output, rows))
        write_json(args.output / f"summary-{args.split}.json", {"per_clip": results})


if __name__ == "__main__":
    main()
