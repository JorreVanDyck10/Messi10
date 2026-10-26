"""Assemble immutable per-frame measurements into one equal-population comparison."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from football_pipeline.contracts import read_json, sha256_file, write_json
from scripts.summarize_ball_resolution import summarize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.summary.exists():
        raise ValueError("Preserve previous comparisons; choose fresh outputs")
    weights, datasets, measurements = {}, {}, {}
    modes = None
    for source in args.sources:
        plan = read_json(source / "plan.json")
        assert plan["confidence_floor"] == 0.001 and plan["workpoint"] == 0.25
        assert plan["tile_overlap"] == 0.2 and plan["global_nms_iou"] == 0.5
        assert plan["source_class"] == 32
        if modes is None:
            modes = plan["modes"]
        assert modes == plan["modes"]
        for model, identity in plan["weights"].items():
            if model == "F004":
                continue  # Retained in the initial comparison; no new winner claim for it.
            if model in weights:
                assert weights[model]["sha256"] == identity["sha256"]
            weights[model] = identity
            for dataset, digest in plan["datasets"].items():
                if dataset in datasets:
                    assert datasets[dataset] == digest
                datasets[dataset] = digest
                for mode in modes:
                    path = source / f"{model}-{mode}-{dataset}.json"
                    assert (model, mode, dataset) not in measurements
                    measurements[model, mode, dataset] = path
    assert set(weights) == {"pretrained", "F003", "F005"}
    for dataset in datasets:
        truth, identities = None, None
        for model in weights:
            for mode in modes:
                path = measurements[model, mode, dataset]
                record = read_json(path)
                if truth is None:
                    truth, identities = record["truth"], record["identities"]
                assert record["truth"] == truth and record["identities"] == identities
    args.output.mkdir(parents=True)
    for (model, mode, dataset), path in measurements.items():
        shutil.copy2(path, args.output / f"{model}-{mode}-{dataset}.json")
    write_json(
        args.output / "plan.json",
        {
            "weights": weights,
            "datasets": datasets,
            "modes": modes,
            "input_plans": {str(s): sha256_file(s / "plan.json") for s in args.sources},
            "scope": "Development comparison on the same pooled original full-frame validation labels; no independent match or final test.",
        },
    )
    summarize(args.output, args.summary)


if __name__ == "__main__":
    main()
