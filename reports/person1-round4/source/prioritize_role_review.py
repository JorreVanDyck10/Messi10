"""Prioritize existing AI-labelled role disagreements without changing truth/review status."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.video import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh review directory")
    args.output.mkdir(parents=True)
    comparison = ROOT / "reports/person1-round3/EXP-R015/crop-comparison/predictions.json"
    other = ROOT / "reports/person1-round3/EXP-R015/vs-r009/predictions.json"
    rows = read_json(comparison)["objects"]
    r009 = {r["id"]: r["R009"] for r in read_json(other)["objects"]}
    priorities = []
    for r in rows:
        versions = {"R007": r["R007"], "R009": r009[r["id"]], "R015": r["candidate"]}
        roles = [v["runtime_role"] for v in versions.values()]
        errors = [name for name, pred in versions.items() if pred["runtime_role"] != r["truth"]]
        false_player = r["truth"] != "player" and "player" in roles
        if false_player:
            priority, reason = (
                0,
                "Non-player reference predicted as player; counting risk if field gate also accepts",
            )
        elif r["truth"] in {"referee", "assistant_referee", "steward", "spectator"} and errors:
            priority, reason = 1, "Rare/official role error; inspect full source context and crop evidence"
        elif len(set(roles)) > 1:
            priority, reason = 2, "Models disagree"
        elif errors:
            priority, reason = 3, "All three models disagree with the existing AI reference"
        else:
            continue
        priorities.append(
            {
                "id": r["id"],
                "truth": r["truth"],
                "image": r["image"],
                "bbox": r["bbox"],
                "priority": priority,
                "reason": reason,
                "predictions": versions,
                "existing_ai_label_may_be_wrong": True,
                "human_reviewer": "",
                "review_status": "pending",
            }
        )
    priorities.sort(key=lambda r: (r["priority"], r["truth"], r["id"]))
    for page in range((min(len(priorities), 72) + 11) // 12):
        canvas = np.full((4 * 205, 3 * 470, 3), 245, dtype=np.uint8)
        for j, row in enumerate(priorities[page * 12 : (page + 1) * 12]):
            pixels = cv2.imread(str((ROOT / "datasets/roles-teams-v3" / row["image"]).resolve()))
            if pixels is None:
                raise ValueError("Review source is unreadable")
            x1, y1, x2, y2 = map(round, row["bbox"])
            crop = pixels[max(0, y1) : y2, max(0, x1) : x2]
            scale = min(120 / crop.shape[1], 145 / crop.shape[0])
            view = cv2.resize(
                crop, (max(1, round(crop.shape[1] * scale)), max(1, round(crop.shape[0] * scale)))
            )
            top, left = (j // 3) * 205, (j % 3) * 470
            canvas[top : top + view.shape[0], left : left + view.shape[1]] = view
            texts = [f"#{page * 12 + j + 1} P{row['priority']} AI: {row['truth']}"] + [
                f"{name}: {pred['runtime_role']} {pred['confidence']:.2f}"
                for name, pred in row["predictions"].items()
            ]
            for k, text in enumerate(texts):
                cv2.putText(
                    canvas,
                    text,
                    (left + 130, top + 25 + k * 26),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.47,
                    (20, 20, 20),
                    1,
                )
            cv2.putText(
                canvas, row["id"][:61], (left + 3, top + 180), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (20, 20, 20), 1
            )
        cv2.imwrite(str(args.output / f"review-{page + 1:02}.jpg"), canvas)
    write_json(
        args.output / "priorities.json",
        {
            "input_hashes": {str(p.relative_to(ROOT)): sha256_file(p) for p in [comparison, other]},
            "reference_crops": len(rows),
            "priorities": priorities,
            "priority_counts": dict(Counter(r["priority"] for r in priorities)),
            "false_player_reference_roles": dict(
                Counter(r["truth"] for r in priorities if r["priority"] == 0)
            ),
            "human_review_completed": False,
            "truth_labels_changed": False,
            "scope": "Conditional-crop development triage, not whole-image FP counts or proof that the existing AI truth is correct. See originals for context before relabelling.",
        },
    )
    print("Prepared", len(priorities), "review cases from", len(rows), "existing validation crops")


if __name__ == "__main__":
    main()
