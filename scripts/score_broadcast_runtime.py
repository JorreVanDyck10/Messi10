"""Compare the fixed-confidence benchmark with actual app player counting rules."""

import argparse
from collections import defaultdict
from pathlib import Path

from evaluate_temporal_broadcast import score, summarize

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.teams import load_team_settings

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inference", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/broadcast-temporal-v1/manifest.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = read_json(args.inference / "inputs.json")
    dataset = read_json(args.dataset)
    if source["dataset_fingerprint"] != dataset["fingerprint"]:
        raise ValueError("Frozen detection observations use a different dataset")
    models = source["models"]
    specs = models["models"] + [
        models[k] for k in ("appearance", "kit_embedding", "role_context") if models.get(k)
    ]
    for spec in specs:
        if sha256_file(spec["weights"]) != spec["weights_sha256"]:
            raise ValueError("A source model checkpoint changed")
    settings = load_team_settings(ROOT / "configs/teams-broadcast.json")
    if settings != source["settings"]:
        raise ValueError("Team policy differs from original native inference")
    grouped = defaultdict(list)
    for row in dataset["frames"]:
        if sha256_file(row["image"]) != row["image_sha256"]:
            raise ValueError("Frozen source pixels changed")
        grouped[row["clip"]].append(row)
    results = {"confidence_025": [], "runtime": []}
    provenance = {
        "replay_kind": "Scoring only; original fresh neural observations retained",
        "source_inputs_sha256": sha256_file(args.inference / "inputs.json"),
        "dataset_sha256": sha256_file(args.dataset),
        "source_sha256": sha256_file(__file__),
        "scoring_sha256": sha256_file(ROOT / "scripts/evaluate_temporal_broadcast.py"),
        "counting_policy_sha256": sha256_file(ROOT / "src/football_pipeline/participants.py"),
        "detections": {},
        "human_review_completed": False,
        "independent_final_test_completed": False,
    }
    for clip, rows in grouped.items():
        path = args.inference / f"{clip}.json"
        cached = read_json(path)
        if [f["frame_index"] for f in cached["frames"]] != [r["frame_index"] for r in rows]:
            raise ValueError("Native observation timeline differs")
        provenance["detections"][clip] = sha256_file(path)
        for policy in results:
            results[policy].append(score(rows, cached, settings, count_policy=policy))
            write_json(
                args.output / f"{policy}-metrics.json",
                {"per_clip": results[policy], "summary": summarize(results[policy])},
            )
        print(
            clip,
            "runtime count MAE",
            results["runtime"][-1]["counts"]["mean_absolute_error_when_available"],
            flush=True,
        )
    write_json(args.output / "inputs.json", provenance)


if __name__ == "__main__":
    main()
