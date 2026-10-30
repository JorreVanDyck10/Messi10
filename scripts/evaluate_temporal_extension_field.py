"""Paired native-pixel field geometry on preregistered later broadcast windows."""

import argparse
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
import torch
from evaluate_backward_field import point_errors

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.field_layout_bridge import LAYOUT_BRIDGE_RULE, estimate_layout_bridge
from football_pipeline.field_learning import (
    image_observation,
    labels_for_row,
    load_model,
    reprojection_metrics,
    upstream_runtime,
)
from football_pipeline.field_motion import MOTION_RANK_SETTINGS, CameraCalibration, estimate_checked

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/broadcast-temporal-v2/manifest.json"
RUNTIME = ROOT / "artifacts/joint-retrain-20261027-v2/selected-field-runtime.json"


def reference_metrics(rows, observations, states):
    results, errors, relative_errors = [], [], []
    counts = Counter()
    for row, observation, state in zip(rows, observations, states, strict=True):
        if not row.get("field_label"):
            counts["no_field_reference"] += 1
            continue
        scoring_row = {"label": row["field_label"], "label_policy": row["label_policy"]}
        try:
            labels = labels_for_row(scoring_row)
        except ValueError as exc:
            counts["unsupported_field_reference"] += 1
            results.append(
                {
                    "frame_index": row["frame_index"],
                    "status": "unsupported_field_reference",
                    "reason": str(exc),
                }
            )
            continue
        measured = reprojection_metrics(observation, labels, MOTION_RANK_SETTINGS, state=state)
        values = measured["errors_px"]
        diagonal = np.hypot(row["width"], row["height"])
        status = "unavailable"
        if measured["valid"]:
            status = (
                "unscored_valid"
                if not values
                else "correct"
                if np.median(values) <= diagonal * 0.005 and max(values) <= diagonal * 0.01
                else "wrong"
            )
            errors.extend(values)
            relative_errors.extend(e / diagonal for e in values)
        counts[status] += 1
        results.append(
            {
                "frame_index": row["frame_index"],
                "status": status,
                "median_diagonal_fraction": float(np.median(values) / diagonal) if values else None,
                "maximum_diagonal_fraction": float(max(values) / diagonal) if values else None,
            }
        )
    return {
        "frames": len(rows),
        **{
            key: counts[key]
            for key in (
                "correct",
                "wrong",
                "unavailable",
                "unscored_valid",
                "no_field_reference",
                "unsupported_field_reference",
            )
        },
        "median_error_px": float(np.median(errors)) if errors else None,
        "p95_error_px": float(np.quantile(errors, 0.95)) if errors else None,
        "median_diagonal_fraction": float(np.median(relative_errors)) if relative_errors else None,
        "p95_diagonal_fraction": float(np.quantile(relative_errors, 0.95)) if relative_errors else None,
        "per_frame": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--raw-cache", type=Path)
    parser.add_argument("--split", choices=("train", "val", "all"), default="all")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    runtime = upstream_runtime(RUNTIME)
    dataset = read_json(args.dataset)
    grouped = defaultdict(list)
    for row in dataset["frames"]:
        if args.split == "all" or row["split"] == args.split:
            grouped[row["clip"]].append(row)
    models, summaries = None, []
    neural_identity = {
        "runtime_models": runtime["models"],
        "helper_sha256": sha256_file(ROOT / "src/football_pipeline/field_learning.py"),
        "precision": "FP32",
        "torch": torch.__version__,
    }
    for clip, rows in grouped.items():
        inputs = {
            "dataset_manifest_sha256": sha256_file(args.dataset),
            "rows_digest": digest_json(rows),
            "neural_identity": neural_identity,
            "settings": MOTION_RANK_SETTINGS,
            "candidate_rule": LAYOUT_BRIDGE_RULE,
            "source_sha256": sha256_file(__file__),
            "geometry_sha256": sha256_file(ROOT / "src/football_pipeline/field_motion.py"),
            "candidate_sha256": sha256_file(ROOT / "src/football_pipeline/field_layout_bridge.py"),
        }
        complete = args.output / "completion" / f"{clip}.json"
        complete.parent.mkdir(exist_ok=True)
        if complete.exists():
            saved = read_json(complete)
            if saved["inputs"] != inputs:
                raise ValueError("Completed temporal geometry inputs changed")
            summaries.append(saved["summary"])
            continue
        raw_directory = (args.raw_cache or args.output / "raw") / clip
        raw_directory.mkdir(parents=True, exist_ok=True)
        cameras = {
            name: CameraCalibration(rows[0]["fps"], MOTION_RANK_SETTINGS) for name in ("baseline", "layout")
        }
        states = {name: [] for name in cameras}
        observations = []
        anchors = set()
        started = time.perf_counter()
        for row in rows:
            index = row["frame_index"]
            if sha256_file(row["image"]) != row["image_sha256"] or (
                row["field_label"] and sha256_file(row["field_label"]) != row["field_label_sha256"]
            ):
                raise ValueError("Frozen temporal pixels or provider lines changed")
            frame = cv2.imread(row["image"])
            key = digest_json([neural_identity, row["image_sha256"]])
            path = raw_directory / f"{index:06d}.json"
            if path.exists():
                saved = read_json(path)
                if saved["identity"] != key:
                    raise ValueError("Raw field inference inputs changed")
                observation = saved["observation"]
            else:
                if models is None:
                    models = [load_model(runtime, role, "cuda:0").eval() for role in ("keypoints", "lines")]
                observation = image_observation(models, frame, "cuda:0")
                observation.update(frame_index=index, timestamp_s=index / row["fps"])
                write_json(path, {"identity": key, "observation": observation})
            observations.append(observation)
            baseline = estimate_checked(observation, observation["image_size"], MOTION_RANK_SETTINGS)
            candidate = estimate_layout_bridge(observation, observation["image_size"], MOTION_RANK_SETTINGS)
            if baseline["status"] == "valid":
                anchors.add(index)
            if candidate["status"] == "valid" and baseline["status"] != "valid":
                raise ValueError("Candidate created an unverified anchor")
            for name, direct in (("baseline", baseline), ("layout", candidate)):
                state = cameras[name].update(frame, direct, index)
                if (
                    state["status"] == "valid"
                    and state["source"] == "tracked"
                    and (state["reference_frame"] not in anchors or state["age_s"] > 2)
                ):
                    raise ValueError("Motion exceeded trusted-anchor boundaries")
                states[name].append(state)
            if (index + 1) % 50 == 0:
                print(
                    clip,
                    index + 1,
                    "/150",
                    {n: sum(s["status"] == "valid" for s in ss) for n, ss in states.items()},
                    flush=True,
                )
        summary = {
            "clip": clip,
            "game_id": rows[0]["game_id"],
            "split": rows[0]["split"],
            "frames": len(rows),
            "elapsed_s": time.perf_counter() - started,
            "geometry": {},
            "gained_frames": [
                i
                for i, (a, b) in enumerate(zip(states["baseline"], states["layout"]))
                if a["status"] != "valid" and b["status"] == "valid"
            ],
            "lost_frames": [
                i
                for i, (a, b) in enumerate(zip(states["baseline"], states["layout"]))
                if a["status"] == "valid" and b["status"] != "valid"
            ],
            "common_matrices_unchanged": all(
                np.allclose(a["homography"], b["homography"], rtol=0, atol=1e-12)
                for a, b in zip(states["baseline"], states["layout"])
                if a["status"] == b["status"] == "valid"
            ),
            "human_review_completed": False,
            "independent_final_test": False,
        }
        for name, values in states.items():
            directory = args.output / name / clip
            directory.mkdir(parents=True, exist_ok=True)
            reference = reference_metrics(rows, observations, values)
            metrics = {
                "dataset_manifest_sha256": sha256_file(args.dataset),
                "valid_frames": sum(s["status"] == "valid" for s in values),
                "frames": len(rows),
                "reference": reference,
                "status_counts": dict(Counter(s["status"] for s in values)),
                "inputs": inputs,
            }
            write_json(directory / "states.json", {"frames": values})
            write_json(directory / "projection-metrics.json", metrics)
            summary["geometry"][name] = {k: v for k, v in reference.items() if k != "per_frame"}
            summary["geometry"][name]["valid_frames"] = metrics["valid_frames"]
        old_errors, new_errors = (
            point_errors(rows, states["baseline"], clip),
            point_errors(rows, states["layout"], clip),
        )
        added = [e for k, e in new_errors.items() if k not in old_errors]
        summary.update(
            added_points=len(added),
            added_median_m=float(np.median(added)) if added else None,
            added_p90_m=float(np.quantile(added, 0.9)) if added else None,
        )
        write_json(complete, {"inputs": inputs, "summary": summary})
        summaries.append(summary)
        write_json(
            args.output / f"summary-{args.split}.json",
            {"per_clip": summaries, "human_review_completed": False, "independent_final_test": False},
        )
        print(
            clip,
            "complete",
            {n: (v["correct"], v["wrong"], v["valid_frames"]) for n, v in summary["geometry"].items()},
            flush=True,
        )


if __name__ == "__main__":
    main()
