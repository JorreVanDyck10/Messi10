"""Select confidence policies on training matches, then measure held-out match geometry."""

from __future__ import annotations

import argparse
import ast
import copy
import json
from pathlib import Path

import cv2
import numpy as np
import torch

from .contracts import digest_json, read_json, sha256_file, write_json
from .field_learning import (
    image_observation,
    labels_for_row,
    load_model,
    reprojection_metrics,
    upstream_runtime,
)
from .field_motion import DEFAULT_SETTINGS


def score(observations, rows, settings, *, line_fallback=False):
    measured = []
    for obs, row in zip(observations, rows):
        extra = {}
        if line_fallback:
            from .field_line_geometry import estimate_from_lines
            from .field_motion import estimate_checked

            state = estimate_checked(obs, obs["image_size"], settings)
            extra["state"] = estimate_from_lines(state, obs["image_size"], settings)
        measured.append(reprojection_metrics(obs, labels_for_row(row), settings, **extra))
    correct = wrong = unscored = 0
    errors = []
    for item, observation in zip(measured, observations):
        if not item["valid"]:
            continue
        residuals = item["errors_px"]
        if not residuals:
            unscored += 1
            continue
        diagonal = np.hypot(*observation["image_size"])
        accurate = np.median(residuals) <= diagonal * 0.005 and max(residuals) <= diagonal * 0.01
        correct += bool(accurate)
        wrong += not bool(accurate)
        errors.extend(residuals)
    return {
        "frames": len(rows),
        "valid": sum(m["valid"] for m in measured),
        "correct": correct,
        "wrong": wrong,
        "unscored_valid": unscored,
        "median_line_error_px": float(np.median(errors)) if errors else None,
        "p95_line_error_px": float(np.percentile(errors, 95)) if errors else None,
        "correct_fraction": correct / len(rows),
        "independent_final_test": False,
    }


def observations_for(runtime_path, rows, output, inference_source=None):
    runtime = upstream_runtime(runtime_path)
    source = Path(__file__).with_name("field_learning.py")
    if inference_source:
        # A metric-only repair must not require running unchanged neural inference again.
        # Reuse is allowed only when every local inference function has an identical AST.
        def functions(path):
            return {
                node.name: ast.dump(node, include_attributes=False)
                for node in ast.parse(path.read_text(encoding="utf-8")).body
                if isinstance(node, ast.FunctionDef)
            }

        before, after = functions(inference_source), functions(source)
        for name in ("image_observation", "load_model", "read_yaml", "upstream_runtime"):
            if before[name] != after[name]:
                raise ValueError("Cached neural inference implementation changed")
        source = inference_source
    identity = digest_json(
        {
            "models": {k: v["sha256"] for k, v in runtime["models"].items()},
            "images": [r["image_sha256"] for r in rows],
            "inference_implementation": sha256_file(source),
        }
    )
    path = output / f"observations-{identity}.json"
    if path.exists():
        return read_json(path)["observations"], runtime
    models = [load_model(runtime, role, "cuda:0").eval() for role in ("keypoints", "lines")]
    result = []
    try:
        for i, row in enumerate(rows):
            image = cv2.imread(row["image"])
            if image is None:
                raise ValueError("Cannot read the frozen evaluation frame")
            result.append(image_observation(models, image, "cuda:0"))
            if i % 10 == 0:
                print(f"Field inference {i + 1}/{len(rows)}: {Path(runtime_path).parent.name}", flush=True)
    finally:
        del models
        torch.cuda.empty_cache()
    write_json(path, {"identity": identity, "observations": result})
    return result, runtime


def improves_geometry(measured, baseline, *, allow_error_reduction=False):
    """Never trade correct coverage for fewer errors, or allow extra false calibrations."""
    if measured["wrong"] > baseline["wrong"] or measured["correct"] < baseline["correct"]:
        return False
    return measured["correct"] > baseline["correct"] or (
        allow_error_reduction and measured["wrong"] < baseline["wrong"]
    )


def compare(
    dataset, baseline_path, candidate_path, output, inference_source=None, allow_error_reduction=False
):
    output.mkdir(parents=True, exist_ok=True)
    index = read_json(candidate_path.parent / "dataset-index.json")
    if Path(index["root"]).resolve() != dataset.resolve():
        raise ValueError("Candidate training index belongs to a different field dataset")
    rows = index["frames"]
    for row in rows:
        if (
            sha256_file(row["image"]) != row["image_sha256"]
            or sha256_file(row["label"]) != row["label_sha256"]
        ):
            raise ValueError("Frozen field evaluation inputs changed")
    if {r["split"] for r in rows} != {"train", "valid"}:
        raise ValueError("Need frozen training and held-out validation matches")
    train_games = {r["match_id"] for r in rows if r["split"] == "train"}
    val_games = {r["match_id"] for r in rows if r["split"] == "valid"}
    if train_games & val_games:
        raise ValueError("Match overlap")
    prereg = {
        "geometry_sha256": sha256_file(Path(__file__).with_name("field_motion.py")),
        "metrics_sha256": sha256_file(Path(__file__).with_name("field_learning.py")),
        "keypoint_thresholds": [0.2, 0.35, 0.5],
        "line_thresholds": [0.3, 0.5, 0.75],
        "geometry_limits": {
            k: DEFAULT_SETTINGS[k] for k in ("median_diagonal_fraction", "maximum_diagonal_fraction")
        },
        "selection": "top three policies by correct training-frame count with no more wrong calibrations than baseline; validation is model selection, not final test",
        "held_out_test_accessed": False,
        "allow_error_reduction_at_equal_correct_coverage": allow_error_reduction,
        "selection_refinement": (
            "Secondary development analysis after initial coverage-gain experiments; fewer wrong projections at unchanged correct coverage. Not an independent confirmatory test."
            if allow_error_reduction
            else None
        ),
        "dataset_fingerprint": index["fingerprint"],
    }
    policy_path = output / "policy-preregistration.json"
    if policy_path.exists() and read_json(policy_path) != prereg:
        raise ValueError("Frozen field policy grid changed")
    write_json(policy_path, prereg)
    torch.set_num_threads(4)
    baseline, base_runtime = observations_for(baseline_path, rows, output, inference_source)
    candidate, candidate_runtime = observations_for(candidate_path, rows, output, inference_source)
    masks = {s: [i for i, r in enumerate(rows) if r["split"] == s] for s in ("train", "valid")}

    def subset_score(obs, settings, split):
        ids = masks[split]
        return score([obs[i] for i in ids], [rows[i] for i in ids], settings)

    base_train = subset_score(baseline, DEFAULT_SETTINGS, "train")
    base_valid = subset_score(baseline, DEFAULT_SETTINGS, "valid")
    variants = {
        "baseline": baseline,
        "finetuned": candidate,
        "finetuned_points": [{**b, "points": c["points"]} for b, c in zip(baseline, candidate)],
        "finetuned_lines": [{**b, "lines": c["lines"]} for b, c in zip(baseline, candidate)],
    }
    candidates = []
    for name, obs in variants.items():
        settings = [DEFAULT_SETTINGS] + [
            {**DEFAULT_SETTINGS, "keypoint_threshold": kp, "line_threshold": ln}
            for kp in prereg["keypoint_thresholds"]
            for ln in prereg["line_thresholds"]
        ]
        ranked = []
        for setting in settings:
            measurement = subset_score(obs, setting, "train")
            ranked.append({"variant": name, "settings": setting, "train": measurement})
        eligible = [r for r in ranked if r["train"]["wrong"] <= base_train["wrong"]]
        eligible.sort(key=lambda r: (r["train"]["correct"], -r["train"]["wrong"]), reverse=True)
        for record in eligible[:3]:
            record["validation"] = subset_score(obs, record["settings"], "valid")
            candidates.append(record)
    acceptable = [
        r
        for r in candidates
        if improves_geometry(r["validation"], base_valid, allow_error_reduction=allow_error_reduction)
    ]
    acceptable.sort(key=lambda r: (r["validation"]["correct"], -r["validation"]["wrong"]), reverse=True)
    selected = acceptable[0] if acceptable else None
    report = {
        "status": "complete",
        "baseline": {"settings": DEFAULT_SETTINGS, "train": base_train, "validation": base_valid},
        "candidates": candidates,
        "selected": selected,
        "test_accessed": False,
        "pretraining_overlap": "not excluded; these are held out from this fine-tuning, not a new independent final test",
        "project_human_review_completed": False,
        "source": "SN-GSR-2024 v1.3 provider line annotations",
        "selection_policy": prereg,
    }
    if selected:
        runtime = copy.deepcopy(base_runtime)
        roles = {
            "finetuned": ("keypoints", "lines"),
            "finetuned_points": ("keypoints",),
            "finetuned_lines": ("lines",),
            "baseline": (),
        }[selected["variant"]]
        for role in roles:
            key = "weights_keypoints" if role == "keypoints" else "weights_lines"
            runtime[key] = candidate_runtime[key]
            runtime["models"][role] = candidate_runtime["models"][role]
        runtime["calibration_settings"] = selected["settings"]
        runtime["development_validation"] = str((output / "comparison.json").resolve())
        runtime["automatic_promotion"] = False
        write_json(output / "selected-field-runtime.json", runtime)
    write_json(output / "comparison.json", report)
    print(json.dumps({"baseline": base_valid, "selected": selected}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inference-source", type=Path)
    parser.add_argument("--allow-error-reduction", action="store_true")
    args = parser.parse_args()
    compare(
        args.dataset,
        args.baseline,
        args.candidate,
        args.output,
        args.inference_source,
        args.allow_error_reduction,
    )
