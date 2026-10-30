"""One fixed, training-only screen of the existing role-context rejection policy.

The .95 candidate matches the already configured positive-player threshold.
Tracking cannot be validated by masking cached tracks: any selected policy
requires fresh detector/context/tracker inference on development validation.
"""

import argparse
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

from evaluate_temporal_broadcast import score, summarize

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.detection import load_model_manifest
from football_pipeline.teams import load_team_settings

ROOT = Path(__file__).resolve().parents[1]
TARGET = 0.95


def refine_context(cached, spec):
    changed = deepcopy(cached)
    rejected = 0
    for frame in changed["frames"]:
        for detection in frame["detections"]:
            d = detection
            position = d.get("field_position")
            value = d.get("role_context_player_score")
            if (
                d["semantic_class"] == "player"
                and d["projection_status"] == "valid"
                and d["confidence"] >= 0.25
                and d.get("role_context_model_id") == spec["model_id"]
                and value is not None
                and 1 - value >= TARGET
                and not (d.get("player_kind") == "goalkeeper" and d.get("player_kind_source") == "detector")
                and position
                and spec.get("protect_end_fraction", 0.08)
                < position[0]
                < 1 - spec.get("protect_end_fraction", 0.08)
            ):
                d["semantic_class"] = "referee" if d["role_probabilities"][1] >= 0.5 else "person"
                d["role_decision"], d["track_id"] = "pitch_context_nonplayer", None
                rejected += 1
    return changed, rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    settings = load_team_settings(ROOT / "configs/teams-broadcast.json")
    models = load_model_manifest(ROOT / "configs/models-broadcast.json")
    if models["role_context"]["nonplayer_threshold"] != 0.99:
        raise ValueError("Screen expects the unchanged .99 baseline")
    sources = [
        (
            ROOT / "data/broadcast-temporal-v1/manifest.json",
            ROOT / "artifacts/broadcast-reliability-day2/motion-rank-automatic-native-v1",
        ),
        (
            ROOT / "data/broadcast-temporal-v2/manifest.json",
            ROOT / "artifacts/broadcast-reliability-20261030/extension-automatic-native-v1",
        ),
    ]
    results = {"baseline": [], "candidate": []}
    inputs = {
        "target": TARGET,
        "baseline": 0.99,
        "tracking_evaluated": False,
        "validation_used_for_selection": False,
        "rule": "One fixed .95 negative threshold; retain all existing goalkeeper/end protections",
        "files": {},
        "source_sha256": sha256_file(__file__),
    }
    total_rejected = 0
    for dataset_path, source in sources:
        dataset = read_json(dataset_path)
        saved_inputs = read_json(source / "inputs.json")
        if (
            dataset["fingerprint"] != saved_inputs["dataset_fingerprint"]
            or saved_inputs["settings"] != settings
        ):
            raise ValueError("Cached inference uses different inputs")
        grouped = defaultdict(list)
        for row in dataset["frames"]:
            if row["split"] == "train":
                grouped[row["clip"]].append(row)
        for clip, rows in grouped.items():
            path = source / f"{clip}.json"
            cached = read_json(path)
            inputs["files"][str(path)] = sha256_file(path)
            candidate, rejected = refine_context(cached, models["role_context"])
            total_rejected += rejected
            results["baseline"].append(score(rows, cached, settings, count_policy="runtime"))
            results["candidate"].append(score(rows, candidate, settings, count_policy="runtime"))
            print(clip, "additional nonplayers", rejected, flush=True)
    summaries = {name: summarize(values)["train"] for name, values in results.items()}
    for summary in summaries.values():
        for key in list(summary):
            if key.startswith(("ID", "image_ID")):
                summary.pop(key)
    for values in results.values():
        for result in values:
            result.pop("tracking")
            result.pop("image_tracking")
    before, after = summaries["baseline"], summaries["candidate"]
    passed = (
        after["precision"] >= before["precision"]
        and after["recall"] >= before["recall"] - 0.01
        and after["correct_team_fraction"] >= before["correct_team_fraction"]
        and (
            after["precision"] > before["precision"]
            or after["correct_team_fraction"] > before["correct_team_fraction"]
        )
    )
    write_json(
        args.output / "metrics.json",
        {
            "summary": summaries,
            "per_clip": results,
            "additional_nonplayers": total_rejected,
            "training_screen_passed": passed,
            "inputs": inputs,
            "human_review_completed": False,
            "independent_final_test_completed": False,
        },
    )
    candidate = deepcopy(models)
    candidate["role_context"]["nonplayer_threshold"] = TARGET
    candidate["profile_name"] = "Broadcast — fixed context-policy development candidate"
    write_json(args.output / "models.json", candidate)
    print("Training screen", passed, summaries, flush=True)


if __name__ == "__main__":
    main()
