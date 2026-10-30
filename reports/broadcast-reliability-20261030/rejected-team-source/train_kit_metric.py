"""Fit a small histogram metric using existing training matches only.

The fixed SoccerNet development validation games never enter fitting or
checkpoint selection. Every fifth clip within each training match is an
internal holdout; these are not independent matches or an independent test.
"""

import argparse
import copy
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

from football_pipeline.contracts import read_json, sha256_file, write_json

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "artifacts/broadcast-pitch-v1/appearance/features.pt"
FEATURE_SHA256 = "7282ed16fce0a3df427e230209c27792872ef1eaa472bf5d3b77bda8a42f920b"


def pair_loss(raw, labels, transform):
    vector = torch.nn.functional.normalize(raw @ transform.T, dim=1)
    similarity = vector @ vector.T
    same = labels[:, None] == labels[None, :]
    positive = same & ~torch.eye(len(labels), dtype=torch.bool, device=raw.device)
    negative = ~same
    return (1 - similarity[positive]).square().mean() + torch.relu(
        similarity[negative] - 0.45
    ).square().mean()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=1000)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if sha256_file(FEATURES) != FEATURE_SHA256:
        raise ValueError("Frozen feature cache changed")
    if not torch.cuda.is_available():
        raise ValueError("Configured local CUDA training is unavailable")
    torch.set_num_threads(4)
    torch.manual_seed(42)
    torch.use_deterministic_algorithms(True)
    rng = np.random.default_rng(42)
    data = torch.load(FEATURES, map_location="cpu", weights_only=True)
    rows, pools = data["rows"], defaultdict(lambda: [[], []])
    for i, row in enumerate(rows):
        if (
            row["split"] == "train"
            and row["broadcast"]
            and row["role"] == "player"
            and not row.get("goalkeeper")
            and row.get("team") in {"left", "right"}
        ):
            pools[row["group"]][int(row["team"] == "right")].append(i)
    games = defaultdict(list)
    for group, teams in sorted(pools.items()):
        if min(map(len, teams)) >= 2:
            games[group.split("/")[0]].append(group)
    holdout = [group for groups in games.values() for j, group in enumerate(groups) if j % 5 == 0]
    training = [group for groups in games.values() for group in groups if group not in holdout]
    selected_ids = {i for group in training + holdout for team in pools[group] for i in team}
    # These assertions make accidental inclusion of a validation crop fail early.
    if not selected_ids or any(rows[i]["split"] != "train" for i in selected_ids):
        raise ValueError("Only existing training crops may enter this experiment")
    transform = torch.nn.Parameter(torch.eye(32, device="cuda"))
    identity = torch.eye(32, device="cuda")
    raw = data["kit"][:, 576:].cuda()
    labels = torch.tensor([int(row.get("team") == "right") for row in rows], device="cuda")
    optimizer = torch.optim.Adam([transform], lr=0.003)
    inputs = {
        "features_sha256": FEATURE_SHA256,
        "feature_identity": data["identity"],
        "source_sha256": sha256_file(__file__),
        "steps": args.steps,
        "training_clips": training,
        "internal_holdout_clips": holdout,
        "reserved_validation_games": ["2", "3", "5"],
        "validation_used_for_fitting_or_selection": False,
        "test_accessed": False,
        "human_review_completed": False,
        "selection": "Lowest fixed-pair loss on internal training-clip holdout, including identity baseline",
    }
    record = args.output / "inputs.json"
    if record.exists() and read_json(record) != inputs:
        raise ValueError("Training inputs changed; use a fresh output")
    write_json(record, inputs)
    holdout_rng = np.random.default_rng(812)
    fixed = [
        [i for team in pools[group] for i in holdout_rng.choice(team, min(48, len(team)), replace=False)]
        for group in holdout
    ]
    first, curve, best_loss, best, best_step = 0, [], float("inf"), None, 0
    resume = args.output / "resume.pt"
    if resume.exists():
        saved = torch.load(resume, map_location="cuda", weights_only=True)
        transform.data.copy_(saved["transform"])
        optimizer.load_state_dict(saved["optimizer"])
        rng.bit_generator.state = saved["rng_state"]
        first, curve = saved["step"] + 1, saved["curve"]
        best_loss, best, best_step = saved["best_loss"], saved["best"], saved["best_step"]
    started = time.perf_counter()
    for step in range(first, args.steps + 1):
        if step:
            group = training[int(rng.integers(len(training)))]
            ids = [i for team in pools[group] for i in rng.choice(team, min(48, len(team)), replace=False)]
            loss = pair_loss(raw[ids], labels[ids], transform) + 0.02 * (transform - identity).square().mean()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        if step % 50 == 0 or step == args.steps:
            with torch.inference_mode():
                held_loss = float(torch.stack([pair_loss(raw[ids], labels[ids], transform) for ids in fixed]).mean())
            if held_loss < best_loss:
                best_loss, best_step = held_loss, step
                best = transform.detach().cpu().clone()
            curve.append({"step": step, "internal_holdout_pair_loss": held_loss})
            torch.save(
                {
                    "step": step,
                    "transform": transform.detach(),
                    "optimizer": optimizer.state_dict(),
                    "rng_state": copy.deepcopy(rng.bit_generator.state),
                    "curve": curve,
                    "best_loss": best_loss,
                    "best": best,
                    "best_step": best_step,
                },
                resume,
            )
            write_json(args.output / "progress.json", {"step": step, "best_step": best_step, "curve": curve})
            print(step, held_loss, "best", best_step, flush=True)
    torch.save({"format": "post_context_kit_linear_v1", "transform": best}, args.output / "metric.pt")
    write_json(
        args.output / "metrics.json",
        {
            "selected_step": best_step,
            "internal_holdout_pair_loss": best_loss,
            "curve": curve,
            "elapsed_s": time.perf_counter() - started,
            "weights_sha256": sha256_file(args.output / "metric.pt"),
            "limitations": "Holdout clips share training matches; development results only",
        },
    )


if __name__ == "__main__":
    main()
