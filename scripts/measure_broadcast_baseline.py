"""Freeze and measure the current broadcast development baseline, without test access."""

import argparse
import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from football_pipeline.broadcast_evaluation import evaluate_profile
from football_pipeline.contracts import read_json, sha256_file, write_json


def audit_split(manifest):
    rows = manifest["frames"]
    train = [r for r in rows if r["split"] == "train"]
    val = [r for r in rows if r["split"] == "val"]

    def games(items):
        return {str(r["game_id"]) for r in items}

    def hashes(items):
        return {r["image_sha256"] for r in items}

    overlap = sorted(games(train) & games(val))
    duplicates = sorted(hashes(train) & hashes(val))
    if not train or not val or overlap or duplicates:
        raise ValueError("Missing split or train/validation leakage")
    return {
        "frames": dict(Counter(r["split"] for r in rows)),
        "training_games": sorted(games(train)),
        "validation_games": sorted(games(val)),
        "cross_split_games": overlap,
        "cross_split_image_hashes": duplicates,
        "independent_final_test": False,
        "reason": "Validation games previously used for selection; no new test data accessed",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    dataset = Path("data/broadcast-pitch-v1")
    training_manifest = Path("data/broadcast-multisource-v1/manifest.json")
    profile = Path("configs/models-broadcast.json")
    teams = Path("configs/teams-broadcast.json")
    audit = audit_split(read_json(training_manifest))
    # Verify actual bytes rather than trusting the recorded image fingerprints.
    checked = 0
    for row in read_json(training_manifest)["frames"]:
        if sha256_file(row["image"]) != row["image_sha256"]:
            raise ValueError(f"Image changed: {row['frame_id']}")
        checked += 1
    audit["verified_image_files"] = checked
    write_json(args.output / "split-audit.json", audit)
    frozen = {
        "created_at": datetime.now(UTC).isoformat(),
        "phase": "day1",
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "files": {
            str(p): sha256_file(p) for p in (profile, teams, training_manifest, dataset / "manifest.json")
        },
        "source_hashes": {str(p): sha256_file(p) for p in Path("src/football_pipeline").glob("*.py")},
        "profile": read_json(profile),
        "team_settings": read_json(teams),
        "acceptance": {
            "precision_must_improve": True,
            "correct_team_fraction_must_improve": True,
            "max_recall_drop": 0.01,
            "max_per_game_team_fraction_drop": 0.02,
            "max_runtime_increase_fraction": 0.2,
        },
        "limitations": ["Provider labels only", "Reused development validation", "No distance ground truth"],
    }
    write_json(args.output / "frozen-inputs.json", frozen)
    results = {}
    for confidence in (0.10, 0.25):
        print(f"Measuring confidence {confidence}", flush=True)
        results[str(confidence)] = evaluate_profile(
            dataset, profile, teams, args.output / f"confidence-{confidence:.2f}", confidence=confidence
        )
    write_json(args.output / "summary.json", {"phase": "day1", "split_audit": audit, "results": results})
    print(json.dumps({k: r["player_detection_and_roles"]["per_class"][0] for k, r in results.items()}))


if __name__ == "__main__":
    main()
