"""Frozen hard-example field fine-tuning and three controlled geometry comparisons.

Run prepare/compare in the existing PnLCalib environment. Human final acceptance
is separate from provider development metrics; this module never changes defaults.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

from .contracts import digest_json, read_json, sha256_file, write_json
from .field_learning import (
    dataset_index,
    image_observation,
    labels_for_row,
    load_model,
    load_training_index,
    reprojection_metrics,
    upstream_runtime,
)
from .field_motion import DEFAULT_SETTINGS, estimate_checked


def diverse_rows(rows, count):
    """Round-robin matches; selection never looks at validation errors."""
    groups = defaultdict(list)
    for row in sorted(rows, key=lambda r: digest_json([42, r["image_sha256"]])):
        if not row.get("match_id"):
            continue
        groups[row["match_id"]].append(row)
    result = []
    while groups and len(result) < count:
        for match in sorted(list(groups)):
            result.append(groups[match].pop())
            if not groups[match]:
                del groups[match]
            if len(result) == count:
                break
    return result


def field_score(observation, labels, size):
    """Bereken correcte velddekking en de verdeling van projectiefouten op vaste referenties."""
    state = estimate_checked(observation, size, DEFAULT_SETTINGS)
    scored = reprojection_metrics(observation, labels, DEFAULT_SETTINGS, state=state)
    errors = scored.get("errors_px", [])
    median = float(np.median(errors)) if errors else None
    maximum = max(errors) if errors else None
    diagonal = np.hypot(*size)
    correct = bool(errors and median <= 0.005 * diagonal and maximum <= 0.01 * diagonal)
    return {
        "status": state["status"],
        "available": state["status"] == "valid",
        "correct": correct,
        "wrong": state["status"] == "valid" and bool(errors) and not correct,
        "median_line_error_px": median,
        "maximum_line_error_px": maximum,
        "errors_px": errors,
    }


def cached_observation(models, row, output, runtime):
    """Hergebruik een bij dezelfde beeld- en modelhash horende veldwaarneming of bereken haar opnieuw."""
    identity = digest_json(
        [
            row["image_sha256"],
            runtime["models"],
            sha256_file(Path(__file__).with_name("field_coordinates.py")),
            sha256_file(Path(__file__).with_name("field_learning.py")),
        ]
    )
    target = output / f"{identity}.json"
    if target.exists():
        saved = read_json(target)
        if saved["identity"] != identity:
            raise ValueError("Observation cache identity changed")
        return saved["observation"]
    if sha256_file(row["image"]) != row["image_sha256"] or sha256_file(row["label"]) != row["label_sha256"]:
        raise ValueError("Frozen source image/label changed")
    image = cv2.imread(row["image"])
    if image is None:
        raise ValueError("Cannot decode field source")
    obs = image_observation(models, image, "cuda:0")
    write_json(target, {"identity": identity, "observation": obs})
    return obs


def prepare(args):
    """Selecteer moeilijke en goede vergelijkingsbeelden met gescheiden trainings- en validatiewedstrijden."""
    import torch

    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / "training-index.json"
    if target.exists():
        load_training_index(target)
        print("Frozen selection already verified", flush=True)
        return
    runtime = upstream_runtime(args.runtime)
    index = dataset_index(args.dataset)
    pool = diverse_rows([r for r in index["frames"] if r["split"] == "train"], args.pool)
    valid = diverse_rows([r for r in index["frames"] if r["split"] == "valid"], args.valid_frames)
    selection_path = args.output / "pool-selection.json"
    selection = {
        "pool": pool,
        "valid": valid,
        "seed": 42,
        "mined_on": "train_only",
        "source_index_fingerprint": index["fingerprint"],
        "train_frames": args.train_frames,
    }
    if selection_path.exists() and read_json(selection_path) != selection:
        raise ValueError("Frozen pool/configuration changed; use a new output")
    write_json(selection_path, selection)
    cache = args.output / "observations"
    cache.mkdir(exist_ok=True)
    torch.set_num_threads(4)
    models = [load_model(runtime, role, "cuda:0").eval() for role in ("keypoints", "lines")]
    mined, good = [], []
    for i, row in enumerate(pool):
        obs = cached_observation(models, row, cache, runtime)
        score = field_score(obs, labels_for_row(row), obs["image_size"])
        (good if score["correct"] else mined).append({**row, "mining_score": score})
        if i % 16 == 0:
            print(f"Hard-example pool {i + 1}/{len(pool)}", flush=True)
    # Equal-weight recovery and preservation examples; fill only from unused pool rows.
    chosen = diverse_rows(mined, args.train_frames // 2) + diverse_rows(good, args.train_frames // 2)
    used = {r["image_sha256"] for r in chosen}
    chosen += diverse_rows(
        [r for r in mined + good if r["image_sha256"] not in used], args.train_frames - len(chosen)
    )
    frames = chosen + valid
    frozen = {
        "schema_version": 1,
        "frames": frames,
        "fingerprint": digest_json(frames),
        "dataset_version": "field-recovery-hard-examples-v1",
        "pretraining_overlap": True,
        "independent_accuracy_claim": False,
        "human_review_completed": False,
        "training_source": "Provider field annotations, never model-predicted labels",
        "mining": {
            "pool": len(pool),
            "correct": len(good),
            "failed_or_wrong": len(mined),
            "selected_train": len(chosen),
            "selected_valid": len(valid),
        },
        "cross_split_match_overlap": 0,
    }
    write_json(target, frozen)
    load_training_index(target)
    write_json(
        args.output / "experiment.json",
        {
            "training_index_sha256": sha256_file(target),
            "variants": ["keypoints_only", "lines_only", "both"],
            "train": {"epochs": 3, "lr": 0.00001, "patience": 3, "weight_decay": 0.0001, "head_only": False},
            "settings": DEFAULT_SETTINGS,
            "selection_metric": "correct_field_coverage_with_error_nonregression",
            "no_automatic_promotion": True,
            "human_final_test_required": True,
        },
    )
    print(f"Prepared {len(chosen)} train / {len(valid)} validation frames", flush=True)


def summarize(scores):
    """Vat geometrische dekking, foutprojecties en projectieafwijkingen van een variant samen."""
    errors = [e for s in scores for e in s["errors_px"]]
    return {
        "frames": len(scores),
        "available": sum(s["available"] for s in scores),
        "correct": sum(s["correct"] for s in scores),
        "wrong": sum(s["wrong"] for s in scores),
        "unscored_available": sum(s["available"] and not s["errors_px"] for s in scores),
        "correct_coverage": sum(s["correct"] for s in scores) / len(scores),
        "median_line_error_px": float(np.median(errors)) if errors else None,
        "p95_line_error_px": float(np.quantile(errors, 0.95)) if errors else None,
    }


def development_gate(baseline, candidate):
    """Accepteer een variant alleen bij betere dekking zonder meer foutprojecties of hogere mediane en p95-fout."""
    return (
        baseline["frames"] == candidate["frames"]
        and candidate["correct"] > baseline["correct"]
        and candidate["wrong"] <= baseline["wrong"]
        and candidate["unscored_available"] <= baseline["unscored_available"]
        and all(
            baseline[k] is not None and candidate[k] is not None and candidate[k] <= baseline[k]
            for k in ("median_line_error_px", "p95_line_error_px")
        )
    )


def compare(args):
    """Vergelijk de vaste veldvarianten op dezelfde bevroren ontwikkelreferenties."""
    import torch

    index = load_training_index(args.output / "training-index.json")
    base, trained = upstream_runtime(args.runtime), upstream_runtime(args.candidate)
    rows = [r for r in index["frames"] if r["split"] == "valid"]
    cache = args.output / "observations"
    stats, details = {}, {}
    torch.set_num_threads(4)
    for name, roles in (
        ("baseline", ()),
        ("keypoints_only", ("keypoints",)),
        ("lines_only", ("lines",)),
        ("both", ("keypoints", "lines")),
    ):
        runtime = {**base, "models": dict(base["models"])}
        for role in roles:
            runtime["models"][role] = trained["models"][role]
            runtime["weights_" + role] = trained["weights_" + role]
        models = [load_model(runtime, role, "cuda:0").eval() for role in ("keypoints", "lines")]
        scores = []
        for row in rows:
            obs = cached_observation(models, row, cache, runtime)
            scores.append(
                {
                    "image_sha256": row["image_sha256"],
                    "match_id": row["match_id"],
                    **field_score(obs, labels_for_row(row), obs["image_size"]),
                }
            )
        details[name], stats[name] = scores, summarize(scores)
        print(name, stats[name], flush=True)
        write_json(args.output / f"runtime-{name}.json", runtime)
        del models
        torch.cuda.empty_cache()
    gates = {k: development_gate(stats["baseline"], v) for k, v in stats.items() if k != "baseline"}
    passing = [k for k, v in gates.items() if v]
    selected = max(passing, key=lambda k: stats[k]["correct"]) if passing else "baseline"
    write_json(
        args.output / "comparison.json",
        {
            "models": stats,
            "development_gates": gates,
            "development_selection": selected,
            "records": details,
            "frozen_index_sha256": sha256_file(args.output / "training-index.json"),
            "promoted": False,
            "human_review_completed": False,
            "independent_final_test_completed": False,
            "pretraining_overlap": True,
            "remaining_release_checks": [
                "continuous temporal benchmark",
                "original development clip",
                "three unused matches with human references",
            ],
        },
    )


def main():
    """Verwerk de opdrachten voor veldselectie, training en geometrische modelvergelijking."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "compare"))
    parser.add_argument("--runtime", type=Path, default=Path(".tools/field-runtime.json"))
    parser.add_argument("--dataset", type=Path, default=Path("data/field-corpus/soccernet"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--pool", type=int, default=256)
    parser.add_argument("--train-frames", type=int, default=128)
    parser.add_argument("--valid-frames", type=int, default=48)
    args = parser.parse_args()
    if min(args.pool, args.train_frames, args.valid_frames) < 1 or args.train_frames > args.pool:
        parser.error("Positive sample sizes required; training cannot exceed its pool")
    if args.command == "compare" and not args.candidate:
        parser.error("--candidate required for compare")
    prepare(args) if args.command == "prepare" else compare(args)


if __name__ == "__main__":
    main()
