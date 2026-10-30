"""Freeze a pixel-paint consistency veto and measure existing provider geometry."""

import argparse
from collections import Counter
from pathlib import Path

import cv2

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.course_field_evaluation import score
from football_pipeline.field_learning import upstream_runtime
from football_pipeline.field_lens import white_chains
from football_pipeline.field_motion import MOTION_RANK_SETTINGS, estimate_checked
from football_pipeline.field_paint_checks import distance_paint_evidence, paint_evidence

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("train", "valid"), default="train")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--chain-cache", type=Path)
    parser.add_argument("--method", choices=("chains", "distance"), default="chains")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    chain_cache = args.chain_cache or args.output
    chain_cache.mkdir(parents=True, exist_ok=True)
    upstream_runtime(ROOT / "artifacts/joint-retrain-20261027-v2/selected-field-runtime.json")
    all_rows = read_json(ROOT / "artifacts/course-improvement-20261019/field/dataset-index.json")["frames"]
    observations = read_json(
        ROOT
        / "artifacts/course-improvement-20261019/field-policy-full-last/observations-6c30ef8aa93dc16a6d5c1f7beb965e9ba17b7759fb77faa08cfb5112381e7ff1.json"
    )["observations"]
    selected = [(r, o) for r, o in zip(all_rows, observations, strict=True) if r["split"] == args.split]
    rows, baseline, candidate, records = [], [], [], []
    counts = Counter()
    for i, (row, observation) in enumerate(selected):
        if (
            sha256_file(row["image"]) != row["image_sha256"]
            or sha256_file(row["label"]) != row["label_sha256"]
        ):
            raise ValueError("Frozen source changed")
        state = estimate_checked(observation, observation["image_size"], MOTION_RANK_SETTINGS)
        evidence = {"status": "not_applicable", "reject": False}
        if state["status"] == "valid":
            frame = cv2.imread(row["image"])
            cache_path = chain_cache / f"chains-{row['image_sha256']}.json"
            if args.method == "distance":
                evidence = distance_paint_evidence(frame, state)
            elif cache_path.exists():
                saved = read_json(cache_path)
                import numpy as np

                chains_and_size = ([np.asarray(c) for c in saved["chains"]], saved["size"])
            else:
                chains_and_size = white_chains(frame)
                write_json(
                    cache_path,
                    {"chains": [c.tolist() for c in chains_and_size[0]], "size": list(chains_and_size[1])},
                )
            if args.method == "chains":
                evidence = paint_evidence(frame, state, chains_and_size=chains_and_size)
        counts[evidence["status"]] += 1
        filtered = observation
        if evidence["reject"]:
            # Scoring-only mask: no observations are rewritten in production.
            filtered = {**observation, "points": [], "lines": []}
        rows.append(row)
        baseline.append(observation)
        candidate.append(filtered)
        records.append({"image_sha256": row["image_sha256"], "evidence": evidence})
        if (i + 1) % 10 == 0:
            print(i + 1, dict(counts), flush=True)
    write_json(
        args.output / "metrics.json",
        {
            "baseline": score(baseline, rows, MOTION_RANK_SETTINGS),
            "candidate": score(candidate, rows, MOTION_RANK_SETTINGS),
            "records": records,
            "source_sha256": sha256_file(ROOT / "src/football_pipeline/field_paint_checks.py"),
            "input_digest": digest_json(selected),
            "independent_final_test": False,
            "human_review_completed": False,
            "method": args.method,
        },
    )


if __name__ == "__main__":
    main()
