"""Score a fixed additive head policy on paired, already frozen neural outputs."""

import argparse
from collections import Counter
from pathlib import Path

from evaluate_sparse_field_head import accuracy, source_rows

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.course_field_evaluation import score
from football_pipeline.field_head_ensemble import ENSEMBLE_RULE, choose_head_observation
from football_pipeline.field_learning import upstream_runtime
from football_pipeline.field_motion import MOTION_RANK_SETTINGS

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("historical", "pose"), default="historical")
    parser.add_argument("--split", choices=("train", "val"), default="train")
    parser.add_argument("--paired", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    upstream_runtime(ROOT / "artifacts/joint-retrain-20261027-v2/selected-field-runtime.json")
    inputs = read_json(args.paired / "inputs.json")
    rows = source_rows(args.source, args.split)
    if digest_json(rows) != inputs["dataset_rows_digest"]:
        raise ValueError("Paired output uses different evaluation frames")
    originals, chosen, records, transitions = [], [], [], Counter()
    for row in rows:
        if (
            sha256_file(row["image"]) != row["image_sha256"]
            or sha256_file(row["label"]) != row["label_sha256"]
        ):
            raise ValueError("Source changed")
        path = args.paired / "images" / f"{digest_json([inputs, row])}.json"
        saved = read_json(path)
        observation, evidence = choose_head_observation(
            saved["baseline"], saved["candidate"], saved["baseline"]["image_size"], MOTION_RANK_SETTINGS
        )
        originals.append(saved["baseline"])
        chosen.append(observation)
        old, new = accuracy(saved["baseline"], row), accuracy(observation, row)
        transitions[old + " -> " + new] += 1
        records.append(
            {
                "source_sha256": sha256_file(path),
                "image_sha256": row["image_sha256"],
                "evidence": evidence,
                "baseline": old,
                "candidate": new,
            }
        )
    result = {
        "rule": ENSEMBLE_RULE,
        "baseline": score(originals, rows, MOTION_RANK_SETTINGS),
        "candidate": score(chosen, rows, MOTION_RANK_SETTINGS),
        "transitions": dict(transitions),
        "records": records,
        "algorithm_sha256": sha256_file(ROOT / "src/football_pipeline/field_head_ensemble.py"),
        "paired_inputs": inputs,
        "human_review_completed": False,
        "independent_final_test_completed": False,
    }
    write_json(args.output / "metrics.json", result)
    print({k: result[k] for k in ("baseline", "candidate", "transitions")}, flush=True)


if __name__ == "__main__":
    main()
