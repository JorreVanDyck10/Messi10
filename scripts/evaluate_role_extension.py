"""Compare two real classifiers on identical conditional crops, never report this as detection AP."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.appearance import ROLE_NAMES, TEAM_NAMES, AppearanceClassifier
from football_pipeline.contracts import Detection, sha256_file, write_json
from football_pipeline.video import ROOT
from persoon1.role_training import load_training_manifest, scores


def infer(weights, root, rows):
    classifier = AppearanceClassifier(
        {
            "weights": str(weights),
            "weights_sha256": sha256_file(weights),
            "model_id": weights.stem,
            "role_confidence": 0.65,
            "team_confidence": 0.65,
            "device": "0",
        }
    )
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["image"]].append(row)
    predictions = {}
    for image, objects in grouped.items():
        pixels = cv2.imread(str(root / image))
        detections = [
            Detection(row["id"], "ground_truth_crop", 0, "person", row["bbox"], 1.0) for row in objects
        ]
        video_hash = objects[0].get("video_sha256", "role_only_no_verified_supervised_teams")
        classifier.classify(pixels, detections, video_hash)
        for row, d in zip(objects, detections):
            predictions[row["id"]] = {
                "role_id": d.role_class_id,
                "confidence": d.role_confidence,
                "runtime_role": d.semantic_class,
                "team_id": d.team_id,
                "team_method": d.team_method,
            }
    return predictions


def summarize(rows, predictions):
    truth = np.array([ROLE_NAMES.index(r["role"]) for r in rows])
    chosen = np.array(
        [
            ROLE_NAMES.index(predictions[r["id"]]["runtime_role"])
            if predictions[r["id"]]["confidence"] >= 0.65
            else -1
            for r in rows
        ]
    )
    result = scores(truth, chosen, ROLE_NAMES)
    teams = [r for r in rows if r.get("team")]
    result["teams"] = {
        "labelled_crops": len(teams),
        "correct": sum(predictions[r["id"]]["team_id"] == r["team"] for r in teams),
        "wrong": sum(predictions[r["id"]]["team_id"] not in (None, r["team"]) for r in teams),
        "unknown": sum(predictions[r["id"]]["team_id"] is None for r in teams),
    }
    result["crops"] = len(rows)
    return result


def cohorts(rows):
    """Keep new rare-photo references distinct from the earlier added match."""
    return {
        name: subset
        for name, subset in {
            "all_val": rows,
            "retained_val": [r for r in rows if r.get("origin") == "retained_v1"],
            "new_match_val": [r for r in rows if r.get("origin") == "new_masked_match_val"],
            "new_rare_roles_val": [r for r in rows if r.get("origin") == "new_rare_role_photo"],
        }.items()
        if subset
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, default=ROOT / "datasets/roles-teams-v2/manifest.json")
    p.add_argument("--baseline", type=Path, default=ROOT / "artifacts/appearance-v1/roles_teams.pt")
    p.add_argument("--baseline-label", default="R007")
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.baseline_label == "candidate":
        p.error("Baseline label must differ from candidate")
    args.output.mkdir(parents=True, exist_ok=False)
    data = load_training_manifest(args.manifest)
    rows = [r for r in data["samples"] if r["split"] == "val"]
    predictions = {
        name: infer(weights, args.manifest.parent, rows)
        for name, weights in ((args.baseline_label, args.baseline), ("candidate", args.candidate))
    }
    groups = cohorts(rows)
    report = {
        "scope": "Conditional crop classification, not detection AP; development data with AI labels.",
        "dataset_sha256": sha256_file(args.manifest),
        "weights_sha256": {
            args.baseline_label: sha256_file(args.baseline),
            "candidate": sha256_file(args.candidate),
        },
        "role_names": ROLE_NAMES,
        "team_names": TEAM_NAMES,
        "threshold": 0.65,
        "subsets": {
            name: {model: summarize(subset, preds) for model, preds in predictions.items()}
            for name, subset in groups.items()
        },
        "human_review_completed": False,
        "independent_final_test": False,
    }
    write_json(args.output / "comparison.json", report)
    write_json(
        args.output / "predictions.json",
        {
            "objects": [
                {
                    "id": r["id"],
                    "truth": r["role"],
                    "image": r["image"],
                    "bbox": r["bbox"],
                    "origin": r.get("origin"),
                    **{name: preds[r["id"]] for name, preds in predictions.items()},
                }
                for r in rows
            ]
        },
    )
    print(
        {
            k: {m: (v["accuracy"], v["macro_f1"]) for m, v in subset.items()}
            for k, subset in report["subsets"].items()
        }
    )


if __name__ == "__main__":
    main()
