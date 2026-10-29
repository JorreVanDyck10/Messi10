"""Vergelijkt een alternatieve veldprojectie uit lijnen op bevroren modelwaarnemingen."""

import argparse
from pathlib import Path

from .contracts import digest_json, read_json, sha256_file, write_json
from .course_field_evaluation import score
from .field_learning import upstream_runtime
from .field_motion import DEFAULT_SETTINGS


def compare(index_path, baseline, cache, inference_sha, output, validation=False):
    index = read_json(index_path)
    rows = index["frames"]
    for row in rows:
        if (
            sha256_file(row["image"]) != row["image_sha256"]
            or sha256_file(row["label"]) != row["label_sha256"]
        ):
            raise ValueError("Frozen dataset changed")
    runtime = upstream_runtime(baseline)
    identity = digest_json(
        {
            "models": {k: v["sha256"] for k, v in runtime["models"].items()},
            "images": [r["image_sha256"] for r in rows],
            "inference_implementation": inference_sha,
        }
    )
    cached = read_json(cache / f"observations-{identity}.json")
    if cached["identity"] != identity:
        raise ValueError("Inference cache identity changed")
    observations = cached["observations"]
    if len(rows) != len(observations):
        raise ValueError("Inference cache length changed")
    train = [i for i, r in enumerate(rows) if r["split"] == "train"]
    valid = [i for i, r in enumerate(rows) if r["split"] == "valid"]
    if {rows[i]["match_id"] for i in train} & {rows[i]["match_id"] for i in valid}:
        raise ValueError("Match overlap")

    def measure(ids, settings, fallback):
        return score([observations[i] for i in ids], [rows[i] for i in ids], settings, line_fallback=fallback)

    base_train = measure(train, DEFAULT_SETTINGS, False)
    candidates = []
    for kp, ln in [(DEFAULT_SETTINGS["keypoint_threshold"], DEFAULT_SETTINGS["line_threshold"])] + [
        (kp, ln) for kp in [0.2, 0.35, 0.5] for ln in [0.3, 0.5, 0.75]
    ]:
        settings = {**DEFAULT_SETTINGS, "keypoint_threshold": kp, "line_threshold": ln}
        candidates.append({"settings": settings, "train": measure(train, settings, True)})
    candidates = [c for c in candidates if c["train"]["wrong"] <= base_train["wrong"]]
    candidates.sort(key=lambda c: (c["train"]["correct"], -c["train"]["wrong"]), reverse=True)
    report = {
        "dataset_fingerprint": index["fingerprint"],
        "method_sha256": sha256_file(Path(__file__).with_name("field_line_geometry.py")),
        "metrics_sha256": sha256_file(Path(__file__).with_name("field_learning.py")),
        "inference_source_sha256": inference_sha,
        "cached_identity": identity,
        "baseline_train": base_train,
        "train_ranked": candidates,
        "validation_accessed_for_this_method": validation,
        "independent_test_accessed": False,
        "selected": None,
    }
    if validation:
        base_valid = measure(valid, DEFAULT_SETTINGS, False)
        report["baseline_valid"] = base_valid
        for record in candidates[:3]:
            record["validation"] = measure(valid, record["settings"], True)
        eligible = [
            c
            for c in candidates[:3]
            if c["validation"]["correct"] > base_valid["correct"]
            and c["validation"]["wrong"] <= base_valid["wrong"]
        ]
        if eligible:
            report["selected"] = max(eligible, key=lambda c: c["validation"]["correct"])
    write_json(output, report)
    print(
        {
            "baseline_train": base_train,
            "best": candidates[0] if candidates else None,
            "selected": report["selected"],
        },
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--inference-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validation", action="store_true")
    args = parser.parse_args()
    compare(args.index, args.baseline, args.cache, args.inference_sha, args.output, args.validation)
