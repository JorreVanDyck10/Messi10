"""Label-free track-balanced team fitting on frozen detector observations."""

import argparse
from collections import defaultdict
from pathlib import Path

from evaluate_temporal_broadcast import score, summarize

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.teams import load_team_settings
from football_pipeline.track_team_modes import fit_track_balanced

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inference", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--split", choices=("train", "val", "all"), default="train")
    parser.add_argument("--rule", choices=("balanced", "exclusive", "representative"), default="balanced")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    settings = load_team_settings(ROOT / "configs/teams-broadcast.json")
    grouped = defaultdict(list)
    for row in read_json(ROOT / "data/broadcast-temporal-v1/manifest.json")["frames"]:
        if args.split == "all" or row["split"] == args.split:
            grouped[row["clip"]].append(row)
    scores = []
    inputs = {"rule": args.rule, "inference": {}, "split": args.split}
    for clip, rows in grouped.items():
        source = args.inference / f"{clip}.json"
        cached = read_json(source)
        if [f["frame_index"] for f in cached["frames"]] != [r["frame_index"] for r in rows]:
            raise ValueError("Source timeline mismatch")
        inputs["inference"][clip] = sha256_file(source)
        model = fit_track_balanced(cached["frames"], settings, rows[0]["fps"], rule=args.rule)
        write_json(args.output / f"{clip}-teams.json", model)
        scores.append(score(rows, cached, settings, team_model=model))
        print(clip, scores[-1]["teams"]["correct_fraction_all_players"], flush=True)
    inputs["algorithm_sha256"] = sha256_file(ROOT / "src/football_pipeline/track_team_modes.py")
    inputs["dataset_sha256"] = sha256_file(ROOT / "data/broadcast-temporal-v1/manifest.json")
    write_json(args.output / "inputs.json", inputs)
    write_json(args.output / "metrics.json", {"per_clip": scores, "summary": summarize(scores)})


if __name__ == "__main__":
    main()
