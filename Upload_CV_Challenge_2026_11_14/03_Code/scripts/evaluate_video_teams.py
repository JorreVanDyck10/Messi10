"""Development-only colour clustering benchmark on fixed, visually reviewed crops.

Ground-truth roles/boxes isolate kit assignment from detection errors. Every video
starts cold; labels are used for scoring only, never for fitting the clusters.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path

import cv2

from football_pipeline.contracts import Detection, sha256_file, write_json
from football_pipeline.teams import VideoTeams
from football_pipeline.video import ROOT


def run(output, implementation=None):
    """Meet de gekozen kleurclustering op vaste, visueel beoordeelde videospecifieke shirtcrops en
    schrijf voorspellingen en ontwikkelscores.
    """
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    implementation = Path(implementation) if implementation else ROOT / "src/football_pipeline/teams.py"
    team_type = VideoTeams
    if implementation.resolve() != (ROOT / "src/football_pipeline/teams.py").resolve():
        spec = importlib.util.spec_from_file_location(
            "football_pipeline.team_benchmark_reference", implementation
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        team_type = module.VideoTeams
    manifest = ROOT / "datasets/roles-teams-v2/manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    reference = ROOT / "reports/team-colour-v2/new-match-team-reference.json"
    extra = json.loads(reference.read_text(encoding="utf-8"))
    annotations = {r["id"]: r for r in extra["samples"]}
    groups = {}
    for row in data["samples"]:
        if row["split"] != "val" or row["role"] != "player":
            continue
        if row.get("team"):
            item = dict(row)
            item["video"] = row["video_sha256"]
        elif row["id"] in annotations:
            item = {**row, **annotations[row["id"]], "video": "football48-panorama-128057"}
        else:
            continue
        groups.setdefault(item["video"], {}).setdefault(item["image"], []).append(item)
    results = []
    for video, images in sorted(groups.items()):
        teams = team_type()
        records = []
        for image, rows in sorted(images.items()):
            path = (manifest.parent / image).resolve()
            if sha256_file(path) != rows[0]["image_sha256"]:
                raise ValueError(f"Changed source image: {path}")
            frame = cv2.imread(str(path))
            detections = [
                Detection(r["id"], "reference-boxes", 0, "player", r["bbox"], 0.9, role_confidence=0.9)
                for r in rows
            ]
            teams.update(frame, detections)
            for row, detection in zip(rows, detections):
                records.append(
                    {
                        "id": row["id"],
                        "image": image,
                        "truth": row["team"],
                        "goalkeeper": row.get("goalkeeper", False),
                        "prediction": detection.team_id,
                        "confidence": detection.team_confidence,
                        "ready": teams.centers is not None,
                    }
                )
        # Neutral A/B names are exchangeable between videos. Pick ONE permutation per video.
        scored = [r for r in records if r["truth"] and not r["goalkeeper"]]
        direct = sum(r["prediction"] == r["truth"] for r in scored)
        swapped = sum(bool(r["prediction"]) and r["prediction"] != r["truth"] for r in scored)
        swap = swapped > direct
        for row in records:
            predicted = row["prediction"]
            row["aligned_prediction"] = (
                {"team_a": "team_b", "team_b": "team_a"}[predicted] if swap and predicted else predicted
            )
        assigned = [r for r in scored if r["prediction"]]
        correct = sum(r["aligned_prediction"] == r["truth"] for r in scored)
        results.append(
            {
                "video": video,
                "images": len(images),
                "outfield_crops": len(scored),
                "correct": correct,
                "wrong": len(assigned) - correct,
                "unknown_including_warmup": len(scored) - len(assigned),
                "accuracy_including_unknown": correct / max(1, len(scored)),
                "accuracy_when_assigned": correct / max(1, len(assigned)),
                "coverage": len(assigned) / max(1, len(scored)),
                "unknown_goalkeeper_references": sum(r["goalkeeper"] and not r["truth"] for r in records),
                "assigned_unknown_goalkeepers": sum(
                    bool(r["prediction"]) for r in records if r["goalkeeper"] and not r["truth"]
                ),
                "per_video_permutation_swapped": bool(swap),
                "final_calibration": teams.info,
                "records": records,
            }
        )
    write_json(
        output / "metrics.json",
        {
            "scope": "Development GT-box conditional kit assignment; NOT detector mAP, independent test or tracking accuracy. Cold start, no label input to clusters. One scoring permutation per video.",
            "review_policy": "provisional_ai_visual",
            "human_review_completed": False,
            "manifest_sha256": sha256_file(manifest),
            "reference_sha256": sha256_file(reference),
            "implementation_sha256": sha256_file(implementation),
            "totals": dict(
                Counter(
                    {
                        key: sum(r[key] for r in results)
                        for key in ("outfield_crops", "correct", "wrong", "unknown_including_warmup")
                    }
                )
            ),
            "videos": results,
        },
    )
    print(
        json.dumps(
            [{k: v for k, v in r.items() if k not in {"records", "final_calibration"}} for r in results],
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--implementation", type=Path, help="Optional trusted local baseline implementation snapshot"
    )
    args = parser.parse_args()
    run(args.output, args.implementation)
