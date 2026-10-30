"""Paired field-network geometry: share the frozen backbone, compare two heads."""

import argparse
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import torch
import torchvision.transforms.functional as tf

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.course_field_evaluation import score
from football_pipeline.field_learning import (
    image_observation,
    labels_for_row,
    load_model,
    reprojection_metrics,
    upstream_runtime,
)
from football_pipeline.field_motion import MOTION_RANK_SETTINGS

ROOT = Path(__file__).resolve().parents[1]
BASE_RUNTIME = ROOT / "artifacts/joint-retrain-20261027-v2/selected-field-runtime.json"


class HeadPair:
    def __init__(self, candidate):
        self.base = upstream_runtime(BASE_RUNTIME)
        self.candidate = upstream_runtime(candidate)
        original = torch.load(self.base["weights_keypoints"], map_location="cpu", weights_only=True)
        changed = torch.load(self.candidate["weights_keypoints"], map_location="cpu", weights_only=True)
        if original.keys() != changed.keys():
            raise ValueError("Field architecture changed")
        differences = [k for k in original if not torch.equal(original[k], changed[k])]
        if set(differences) - {"head.0.3.weight", "head.0.3.bias"}:
            raise ValueError("The supposedly frozen field backbone changed")
        self.differences = differences
        self.points = load_model(self.base, "keypoints", "cuda:0").eval()
        self.lines = load_model(self.base, "lines", "cuda:0").eval()
        self.alternate = torch.nn.Conv2d(changed["head.0.3.weight"].shape[1], 58, 1).cuda().eval()
        self.alternate.weight.data.copy_(changed["head.0.3.weight"])
        self.alternate.bias.data.copy_(changed["head.0.3.bias"])
        self.captured = []
        self.points.head[0][3].register_forward_pre_hook(lambda _, inputs: self.captured.append(inputs[0]))

    def observe(self, frame):
        tensor = tf.resize(tf.to_tensor(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), [540, 960], antialias=True)[
            None
        ].cuda()
        with torch.inference_mode():
            original = self.points(tensor)
            alternate = self.alternate(self.captured.pop()).softmax(1)
            lines = self.lines(tensor)
            before = image_observation([lambda _: original, lambda _: lines], frame, "cuda:0")
            after = image_observation([lambda _: alternate, lambda _: lines], frame, "cuda:0")
        return before, after


def source_rows(source, split):
    if source == "historical":
        index = read_json(ROOT / "artifacts/course-improvement-20261019/field/dataset-index.json")
        return [r for r in index["frames"] if r["split"] == ("valid" if split == "val" else split)]
    dataset = ROOT / "data/field-pose-multicamera-v1"
    manifest = read_json(dataset / "manifest.json")
    train_games = {r["match_id"] for r in manifest["frames"] if r["split"] == "train"}
    validation_games = {r["match_id"] for r in manifest["frames"] if r["split"] == "val"}
    if train_games & validation_games:
        raise ValueError("Training and validation matches overlap")
    return [
        {
            **r,
            "image": str(dataset / r["image"]),
            "label": r["source_label"],
            "label_sha256": r["source_label_sha256"],
        }
        for r in manifest["frames"]
        if r["split"] == split
    ]


def accuracy(observation, row):
    measured = reprojection_metrics(observation, labels_for_row(row), MOTION_RANK_SETTINGS)
    if not measured["valid"]:
        return "unavailable"
    errors = measured["errors_px"]
    if not errors:
        return "unscored"
    diagonal = np.hypot(*observation["image_size"])
    return "correct" if np.median(errors) <= diagonal * 0.005 and max(errors) <= diagonal * 0.01 else "wrong"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--source", choices=("historical", "pose"), default="historical")
    parser.add_argument("--split", choices=("train", "val"), default="train")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cache = args.output / "images"
    cache.mkdir(exist_ok=True)
    torch.set_num_threads(4)
    rows = source_rows(args.source, args.split)
    inputs = {
        "candidate_runtime_sha256": sha256_file(args.candidate),
        "base_runtime_sha256": sha256_file(BASE_RUNTIME),
        "source_sha256": sha256_file(__file__),
        "dataset_rows_digest": digest_json(rows),
        "settings": MOTION_RANK_SETTINGS,
        "human_review_completed": False,
        "independent_final_test_completed": False,
    }
    if (args.output / "inputs.json").exists() and read_json(args.output / "inputs.json") != inputs:
        raise ValueError("Paired inference inputs changed; use a new directory")
    write_json(args.output / "inputs.json", inputs)
    pair, before, after, transitions, records = None, [], [], Counter(), []
    started = time.perf_counter()
    for i, row in enumerate(rows):
        if (
            sha256_file(row["image"]) != row["image_sha256"]
            or sha256_file(row["label"]) != row["label_sha256"]
        ):
            raise ValueError("Frozen evaluation source changed")
        key = digest_json([inputs, row])
        path = cache / f"{key}.json"
        if path.exists():
            saved = read_json(path)
            original, candidate = saved["baseline"], saved["candidate"]
        else:
            if pair is None:
                pair = HeadPair(args.candidate)
            original, candidate = pair.observe(cv2.imread(row["image"]))
            write_json(path, {"baseline": original, "candidate": candidate})
        before.append(original)
        after.append(candidate)
        # Scoring requires the pinned pitch geometry classes even on cache-only replay.
        if pair is None:
            upstream_runtime(BASE_RUNTIME)
        old, new = accuracy(original, row), accuracy(candidate, row)
        transitions[old + " -> " + new] += 1
        records.append({"image_sha256": row["image_sha256"], "baseline": old, "candidate": new})
        if (i + 1) % 25 == 0:
            print(f"Geometry {i + 1}/{len(rows)}: {dict(transitions)}", flush=True)
    result = {
        "baseline": score(before, rows, MOTION_RANK_SETTINGS),
        "candidate": score(after, rows, MOTION_RANK_SETTINGS),
        "transitions": dict(transitions),
        "records": records,
        "changed_tensors": pair.differences if pair is not None else ["cached observations"],
        "elapsed_s": time.perf_counter() - started,
        **inputs,
    }
    write_json(args.output / "metrics.json", result)
    print({k: result[k] for k in ("baseline", "candidate", "transitions", "elapsed_s")}, flush=True)


if __name__ == "__main__":
    main()
