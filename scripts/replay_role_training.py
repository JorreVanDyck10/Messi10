"""Replay a historical role training with its recorded source and unchanged dataset version."""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
from pathlib import Path

from football_pipeline.contracts import read_json, sha256_file
from football_pipeline.video import ROOT


def specification(run):
    reports = ROOT / "reports/person1-round3"
    old = reports / "source-snapshot/role_training.py"
    specs = {
        "R011": (old, "manifest-v3.0.json", 3, 8),
        "R012": (old, "manifest-v3.0.json", 0, 8),
        "R013": (reports / "EXP-R013/training-source.py", "manifest.json", 0, 1),
        "R014": (reports / "EXP-R014/training-source.py", "manifest.json", 0, 8),
        "R016": (reports / "EXP-R016/source.py", "manifest.json", 0, 8),
    }
    source, manifest, blocks, scale = specs[run]
    manifest = ROOT / "datasets/roles-teams-v3" / manifest
    if run in {"R011", "R012"}:
        plan = read_json(reports / "role-experiment-plan.json")
        expected_source = plan["training_source_sha256"]
        expected_data = plan["dataset_sha256"]
    else:
        config = read_json(reports / f"EXP-{run}/configuration.json")
        expected_source = config["training_source_sha256"]
        expected_data = config["dataset_sha256"]
    if sha256_file(source) != expected_source or sha256_file(manifest) != expected_data:
        raise ValueError("Historical source/dataset changed; do not silently replay a different experiment")
    return {"source": source, "manifest": manifest, "blocks": blocks, "scale": scale}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", choices=["R011", "R012", "R013", "R014", "R016"], required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--describe", action="store_true")
    args = parser.parse_args()
    spec = specification(args.run)
    if args.describe:
        print(json.dumps({k: str(v) if isinstance(v, Path) else v for k, v in spec.items()}, indent=2))
        return
    if args.output is None:
        parser.error("Choose a fresh --output directory")
    module_spec = importlib.util.spec_from_file_location("persoon1.historical_role_training", spec["source"])
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    # Historical __file__ is inside reports; bind data paths to this checkout explicitly.
    module.ROOT = ROOT
    module.DATA = ROOT / "datasets/roles-teams-v1"
    kwargs = {
        "fine_tune": True,
        "encoder_checkpoint": ROOT / "artifacts/appearance-v1/roles_teams.pt",
        "manifest_path": spec["manifest"],
        "fine_tune_blocks": spec["blocks"],
    }
    if "role_colour_scale" in inspect.signature(module.train).parameters:
        kwargs["role_colour_scale"] = spec["scale"]
    module.train(args.output, **kwargs)


if __name__ == "__main__":
    main()
