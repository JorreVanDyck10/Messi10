"""Versioned AI crop corrections after explicit visual inspection; no synthetic human review."""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

from football_pipeline.appearance import ROLE_NAMES, TEAM_NAMES
from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.video import ROOT
from persoon1.role_training import load_training_manifest


def main():
    """Pas de expliciete visuele AI-beslissingen toe op nieuwe rolcrops en bewaar de uitbreiding als
    nieuwe datasetversie.
    """
    output = ROOT / "datasets/roles-teams-v2"
    if output.exists():
        raise ValueError("Preserve the existing version; choose a new version before changing crop labels")
    output.mkdir()
    old_root = ROOT / "datasets/roles-teams-v1"
    old = read_json(old_root / "manifest.json")
    rows = []
    for original in old["samples"]:
        row = dict(original)
        row["image"] = Path(os.path.relpath(old_root / original["image"], output)).as_posix()
        row["augment_training_crops"] = original["image"].startswith("sources/")
        row["origin"] = "retained_v1"
        rows.append(row)
    review = ROOT / "reports/football48-ball-experiments/role-review"
    train_index = read_json(review / "index.json")["objects"]
    val_index = read_json(review / "new-val-index.json")["objects"]
    candidates = read_json(ROOT / "datasets/development-candidates-v1/manifest.json")
    # Explicitly inspected jersey/body crops. Overlapping or ambiguous subjects are omitted.
    player_ids = {
        0,
        1,
        5,
        8,
        9,
        11,
        14,
        15,
        20,
        21,
        24,
        25,
        26,
        27,
        31,
        33,
        35,
        36,
        37,
        38,
        39,
        41,
        42,
        45,
        46,
        47,
        48,
        49,
        50,
        51,
        55,
        58,
        60,
        62,
        63,
        64,
        66,
        68,
        69,
        70,
        72,
        75,
        76,
        77,
        78,
        79,
        80,
        81,
        82,
        83,
        84,
        85,
        90,
        91,
        92,
        93,
        94,
        95,
        96,
        97,
        98,
        99,
        100,
        101,
        103,
        104,
        105,
        106,
        107,
        109,
        110,
        113,
        114,
        115,
        117,
        118,
        119,
        120,
        121,
        122,
        124,
    }
    referee_ids = {13, 17, 29, 44, 67, 73, 86, 102, 111}
    assistant_ids = {3, 28, 43, 52, 71, 74, 108, 116}
    decisions = []

    def add(item, image, group, split, role, origin):
        """Voeg één expliciet gekozen rolcrop met bron, split en herkomst toe en registreer welke visuele
        beslissing de toevoeging verklaart.
        """
        row = {
            "id": f"extension:{split}:{item['frame_id']}:{item['index']}",
            "image": Path(os.path.relpath(image, output)).as_posix(),
            "image_sha256": sha256_file(image),
            "group": group,
            "split": split,
            "bbox": item["bbox"],
            "role": role,
            "team": None,
            "origin": origin,
            "annotator": "Codex AI",
            "reviewer": "",
            "review_status": "ai_visual_checked",
            "human_review_completed": False,
            "augment_training_crops": split == "train",
            "note": "Partial conditional role crop; not complete detection ground truth or a team annotation.",
        }
        rows.append(row)
        decisions.append(
            {
                "id": row["id"],
                "review_index": item["index"],
                "role": role,
                "previous_prediction": item.get("predicted_role"),
                "split": split,
            }
        )

    for frame in candidates["frames"]:
        objects = [r for r in train_index if r["frame_id"] == frame["frame_id"]]
        players = sorted(
            (r for r in objects if r["index"] in player_ids and not r["outside_approximate_polygon"]),
            key=lambda r: (
                r["predicted_role"] not in {"steward", "spectator", "assistant_referee", "referee"},
                r["index"],
            ),
        )[:3]
        selected = players + [r for r in objects if r["index"] in referee_ids | assistant_ids]
        image = ROOT / "datasets/development-candidates-v1" / frame["image"]
        for item in selected:
            role = (
                "referee"
                if item["index"] in referee_ids
                else "assistant_referee"
                if item["index"] in assistant_ids
                else "player"
            )
            add(item, image, frame["group_id"], "train", role, "new_unmasked_match_train")
    # Crop fragments containing only feet, masked bench people or undecidable context are excluded.
    excluded_val = {3, 4, 5, 6, 11, 12, 18, 37, 46, 47, 48, 53, 54, 58, 61, 62, 63, 74, 75, 76}
    val_referees = {10, 24, 77, 78}
    for item in val_index:
        if item["index"] in excluded_val:
            continue
        add(
            item,
            ROOT / "assets/annotations/football48" / item["image"],
            item["group_id"],
            "val",
            "referee" if item["index"] in val_referees else "player",
            "new_masked_match_val",
        )
    manifest = {
        "version": "roles-teams-v2.0",
        "role_names": ROLE_NAMES,
        "team_names": TEAM_NAMES,
        "review_policy": "provisional_ai_visual",
        "human_review_completed": False,
        "base_manifest_sha256": sha256_file(old_root / "manifest.json"),
        "samples": rows,
        "scope": "Conditional crop classification on three matches. New match has role labels only, no team-head supervision. Reserved tests unopened.",
        "new_frame_scope": "12 new unmasked train moments and 12 already-existing masked football48 val moments; development scores only.",
    }
    write_json(output / "manifest.json", manifest)
    write_json(
        output / "ai-label-decisions.json",
        {
            "decisions": decisions,
            "excluded_validation_crop_indices": sorted(excluded_val),
            "evidence_source": "reports/football48-ball-experiments/role-review/*",
            "human_review_completed": False,
            "non_exhaustive_crop_labels": True,
        },
    )
    load_training_manifest(output / "manifest.json")
    counts = Counter((r["split"], r["role"]) for r in rows if r.get("origin") != "retained_v1")
    print(counts)


if __name__ == "__main__":
    main()
