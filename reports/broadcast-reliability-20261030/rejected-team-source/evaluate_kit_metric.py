"""Replay a post-context kit transform; detector, context and image tracks stay frozen."""

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from evaluate_temporal_broadcast import score, summarize

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.teams import load_team_settings

ROOT = Path(__file__).resolve().parents[1]


def transformed_observations(cached, transform, original_weights):
    if transform.shape != (32, 32) or not np.isfinite(transform).all():
        raise ValueError("Invalid post-context transform")
    if original_weights.shape != (32,) or not np.isfinite(original_weights).all() or (original_weights <= 0).any():
        raise ValueError("Invalid source histogram weights")
    for frame in cached["frames"]:
        for detection in frame["detections"]:
            embedding = detection.get("team_embedding")
            if embedding is None:
                continue
            vector = np.asarray(embedding, float)
            if vector.shape != (32,) or not np.isfinite(vector).all():
                raise ValueError("Invalid cached histogram embedding")
            vector = transform @ (vector / original_weights)
            detection["team_embedding"] = (vector / max(1e-9, np.linalg.norm(vector))).tolist()
    return cached


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inference", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--metric", type=Path)
    mode.add_argument("--root-histogram", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--split", choices=("train", "val", "all"), default="train")
    parser.add_argument("--preserve-role-evidence", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.metric:
        state = torch.load(args.metric, map_location="cpu", weights_only=True)
        if state.get("format") != "post_context_kit_linear_v1":
            raise ValueError("Unknown metric format")
        transform = state["transform"].numpy()
    else:
        if not args.preserve_role_evidence:
            raise ValueError("Root histogram evaluation requires unchanged role evidence")
        transform = None
    inputs = read_json(args.inference / "inputs.json")
    spec = inputs["models"]["kit_embedding"]
    if sha256_file(spec["weights"]) != spec["weights_sha256"]:
        raise ValueError("Source kit weights changed")
    source = torch.load(spec["weights"], map_location="cpu", weights_only=True)
    if source.get("format") != "broadcast-kit-hist-v2":
        raise ValueError("Replay requires a recoverable histogram representation")
    weights = source["metric_weights"].numpy()
    settings = load_team_settings(ROOT / "configs/teams-broadcast.json")
    grouped = defaultdict(list)
    for row in read_json(ROOT / "data/broadcast-temporal-v1/manifest.json")["frames"]:
        if args.split == "all" or row["split"] == args.split:
            grouped[row["clip"]].append(row)
    scores = []
    record = {
        "stage": "post-context; before team fit and assignment",
        "metric_sha256": sha256_file(args.metric) if args.metric else None,
        "rule": "root_histogram_v1" if args.root_histogram else "learned_linear_v1",
        "source_weights_sha256": spec["weights_sha256"],
        "dataset_sha256": sha256_file(ROOT / "data/broadcast-temporal-v1/manifest.json"),
        "replay_source_sha256": sha256_file(__file__),
        "inference": {},
        "split": args.split,
        "preserve_role_evidence": args.preserve_role_evidence,
        "human_review_completed": False,
        "independent_final_test_completed": False,
    }
    for clip, rows in grouped.items():
        path = args.inference / f"{clip}.json"
        cached = read_json(path)
        if [f["frame_index"] for f in cached["frames"]] != [r["frame_index"] for r in rows]:
            raise ValueError("Source timeline mismatch")
        record["inference"][clip] = sha256_file(path)
        if args.preserve_role_evidence:
            if args.root_histogram and not np.allclose(weights, 1):
                raise ValueError("Root histogram replay expects the unweighted histogram baseline")
            metric = "root_histogram_v1" if args.root_histogram else transform / weights[None, :]
            scores.append(score(rows, cached, settings, metric_transform=metric))
        else:
            changed = transformed_observations(cached, transform, weights)
            scores.append(score(rows, changed, settings))
        print(clip, scores[-1]["teams"]["correct_fraction_all_players"], flush=True)
        write_json(args.output / "metrics.json", {"per_clip": scores, "summary": summarize(scores)})
    write_json(args.output / "inputs.json", record)


if __name__ == "__main__":
    main()
