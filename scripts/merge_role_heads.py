"""Measured head interpolation for identical frozen encoders; never average incompatible features.

This is model selection on development validation, not another fine-tuning run or
an independent test. The base team head and all team/video semantics stay intact.
"""

from __future__ import annotations

import argparse
import copy
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np
import torch

from football_pipeline.appearance import ROLE_NAMES, TEAM_NAMES, backbone, crop_tensor, jersey_feature
from football_pipeline.contracts import sha256_file, write_json
from persoon1.role_training import load_training_manifest, scores
from scripts.evaluate_role_extension import cohorts


def blend_role_states(base, candidate, alpha):
    """Meng alleen gelijkvormige rolkopgewichten van compatibele bevroren encoders met het opgegeven
    alfagewicht.
    """
    if not np.isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError("Interpolation weight must be in [0,1]")
    for key, expected in (("role_names", ROLE_NAMES), ("team_names", TEAM_NAMES)):
        if base[key] != expected or candidate[key] != expected:
            raise ValueError("Incompatible output semantics")
    if base["role_colour_scale"] != candidate["role_colour_scale"]:
        raise ValueError("Incompatible colour feature scale")
    for key in ("mean", "std"):
        if not torch.equal(base[key], candidate[key]):
            raise ValueError("Incompatible feature normalization")
    if base["backbone"].keys() != candidate["backbone"].keys() or any(
        not torch.equal(value, candidate["backbone"][key]) for key, value in base["backbone"].items()
    ):
        raise ValueError("Incompatible backbone: head interpolation requires EXACTLY the same encoder")
    result = copy.deepcopy(base)
    for key, value in base["role_head"].items():
        other = candidate["role_head"][key]
        if value.shape != other.shape:
            raise ValueError("Incompatible role head dimensions")
        result["role_head"][key] = value * (1 - alpha) + other * alpha
    return result


def main():
    """Interpoleer alleen compatibele lineaire rolkoppen, meet de toegestane menggewichten en bewaar de
    ontwikkelkeuze.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    base = torch.load(args.base, map_location="cpu", weights_only=True)
    candidate = torch.load(args.candidate, map_location="cpu", weights_only=True)
    blend_role_states(base, candidate, 0.5)
    grid = [0, 0.25, 0.5, 0.75, 1]
    write_json(
        args.output / "preregistration.json",
        {
            "recorded_at": datetime.now(UTC).isoformat(),
            "alpha_grid": grid,
            "base_sha256": sha256_file(args.base),
            "candidate_sha256": sha256_file(args.candidate),
            "dataset_sha256": sha256_file(args.manifest),
            "script_sha256": sha256_file(__file__),
            "selection": "Highest all-val six-class macro F1 at .65; ties prefer retained-val F1, then less change from base.",
            "hypothesis": "Averaging compatible linear heads may retain previous steward decisions while keeping useful new spectator decisions. No incompatible backbone, normalization or colour scale may be averaged.",
            "human_review_completed": False,
            "independent_final_test": False,
        },
    )
    data = load_training_manifest(args.manifest)
    rows = [r for r in data["samples"] if r["split"] == "val"]
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch.set_num_threads(4)
    encoder = backbone().to(device).eval()
    encoder.load_state_dict(base["backbone"])
    images, features = {}, []
    with torch.inference_mode():
        for start in range(0, len(rows), 32):
            pixels, colours = [], []
            for row in rows[start : start + 32]:
                image = row["image"]
                if image not in images:
                    images[image] = cv2.imread(str(args.manifest.parent / image))
                pixels.append(crop_tensor(images[image], row["bbox"]))
                colours.append(jersey_feature(images[image], row["bbox"]))
            features.append(
                torch.cat(
                    [encoder(torch.stack(pixels).to(device)), torch.from_numpy(np.stack(colours)).to(device)],
                    1,
                )
            )
        x = (torch.cat(features).cpu() - base["mean"]) / base["std"]
        x[:, 576:] *= base["role_colour_scale"]
    truth = np.array([ROLE_NAMES.index(r["role"]) for r in rows])
    row_indices = {r["id"]: i for i, r in enumerate(rows)}
    comparisons, best, chosen = [], None, None
    for alpha in grid:
        state = blend_role_states(base, candidate, alpha)
        probabilities = (
            torch.nn.functional.linear(x, state["role_head"]["weight"], state["role_head"]["bias"])
            .softmax(1)
            .numpy()
        )
        predicted = np.where(probabilities.max(1) >= 0.65, probabilities.argmax(1), -1)
        subsets = {}
        for name, subset in cohorts(rows).items():
            selected = [row_indices[r["id"]] for r in subset]
            subsets[name] = scores(truth[selected], predicted[selected], ROLE_NAMES)
        comparisons.append(
            {
                "alpha": alpha,
                "subsets": subsets,
                "predictions": [
                    {"id": r["id"], "role_id": int(p), "confidence": float(v.max())}
                    for r, p, v in zip(rows, predicted, probabilities)
                ],
            }
        )
        ordering = (subsets["all_val"]["macro_f1"], subsets["retained_val"]["macro_f1"], -alpha)
        if best is None or ordering > best:
            best, chosen = ordering, alpha
        print(alpha, {k: round(v["macro_f1"], 4) for k, v in subsets.items()}, flush=True)
    state = blend_role_states(base, candidate, chosen)
    state["role_head_interpolation"] = {
        "alpha": chosen,
        "base_sha256": sha256_file(args.base),
        "candidate_sha256": sha256_file(args.candidate),
    }
    weights = args.output / "roles_teams.pt"
    torch.save(state, weights)
    write_json(
        args.output / "comparison.json",
        {
            "kind": "Development selection of compatible linear role heads; not another training run or independent test",
            "selected_alpha": chosen,
            "weights_sha256": sha256_file(weights),
            "base_team_head_preserved": True,
            "backbone_and_normalization_identical": True,
            "comparisons": comparisons,
            "human_review_completed": False,
        },
    )


if __name__ == "__main__":
    main()
