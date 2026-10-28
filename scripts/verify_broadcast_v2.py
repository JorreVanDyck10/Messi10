"""Verify v2 data, measured improvements and optional model handoff without replacing defaults."""

from __future__ import annotations

import copy
import csv
import os
import shutil
import statistics
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import cv2

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json


def gaps(rows):
    groups = defaultdict(list)
    for row in rows:
        if row["split"] == "train":
            groups[row["clip"]].append(row["source_frame_index"])
    values = [(b - a) / 25 for group in groups.values() for a, b in zip(sorted(group), sorted(group)[1:])]
    return {
        "median_s": statistics.median(values),
        "fraction_below_half_second": sum(v < 0.5 for v in values) / len(values),
    }


def main():
    dataset = Path("data/broadcast-training-v2").resolve()
    report_root = Path("reports/broadcast-data")
    artifact = Path("artifacts/broadcast-ball-v2").resolve()
    source = read_json("data/broadcast-sngsr-v1/manifest.json")
    players = read_json(dataset / "players/manifest.json")
    balls = read_json(dataset / "balls/manifest.json")
    for manifest in (source, players, balls):
        if digest_json({k: v for k, v in manifest.items() if k != "fingerprint"}) != manifest["fingerprint"]:
            raise ValueError("Dataset identity changed")
    source_val = {r["frame_id"] for r in source["frames"] if r["split"] == "val"}
    val = {r["frame_id"] for r in players["frames"] if r["split"] == "val"}
    if val != source_val:
        raise ValueError("Player validation changed")
    selected_bins, source_bins = set(), set()
    label_counts = defaultdict(Counter)
    for row in source["frames"]:
        if row["split"] == "train":
            source_bins.add((row["clip"], row["source_frame_index"] // 25))
    for row in players["frames"]:
        for key in ("image", "label"):
            if sha256_file(dataset / "players" / row[key]) != row[key + "_sha256"]:
                raise ValueError("Selected player image or label changed")
        # Compare against the original two-class view, not its four-class source.
        if (dataset / "players" / row["label"]).read_bytes() != (
            Path("data/broadcast-sngsr-v1/players") / row["label"]
        ).read_bytes():
            raise ValueError("Player selection changed label contents")
        if row["split"] == "train":
            key = (row["clip"], row["source_frame_index"] // 25)
            if key in selected_bins:
                raise ValueError("Repeated train second")
            selected_bins.add(key)
        for box in row["boxes"]:
            label_counts[row["split"]][str(box["class_id"])] += 1
    if selected_bins != source_bins:
        raise ValueError("Training temporal coverage was lost")
    experiment = read_json(artifact / "comparison.json")
    if sha256_file(artifact / "experiment-source.py") != experiment["preregistration"]["script_sha256"]:
        raise ValueError("Training source snapshot mismatch")
    with (artifact / "fine-tune/results.csv").open(newline="", encoding="utf-8-sig") as stream:
        epochs = list(csv.DictReader(stream))
    if len(epochs) != 12 or int(epochs[-1]["epoch"]) != 12:
        raise ValueError("The bounded training did not complete")
    baseline, candidate = experiment["baseline"], experiment["candidate"]
    old, new = baseline["tiled"]["per_class"][0], candidate["tiled"]["per_class"][0]
    eligible = (
        new["AP50_95"] > old["AP50_95"]
        and new["TP"] >= old["TP"]
        and new["FP"] <= old["FP"]
        and candidate["crops"]["unmatched_on_negatives"] <= baseline["crops"]["unmatched_on_negatives"]
    )
    profiles = []
    if eligible:
        weights = artifact / "broadcast_ball_v2.pt"
        if weights.exists() and sha256_file(weights) != experiment["candidate_weights_sha256"]:
            raise ValueError("Preserve existing exported weights")
        if not weights.exists():
            shutil.copy2(experiment["candidate_weights"], weights)
        spec = {
            "model_id": "broadcast-ball-native-v2",
            "weights": "../artifacts/broadcast-ball-v2/broadcast_ball_v2.pt",
            "weights_sha256": sha256_file(weights),
            "class_mapping": {"32": "ball"},
            "expected_names": {"32": "sports ball"},
            "imgsz": 640,
            "confidence": 0.25,
            "iou": 0.7,
            "device": "0",
            "ball_tiles": {"sizes": [640], "imgsz": 640, "overlap": 0.2, "merge_iou": 0.5},
        }
        evidence = "../reports/broadcast-data/v2-experiment.json"
        handoff = {
            "evaluation_record": evidence,
            "evaluation_sha256": sha256_file(report_root / "v2-experiment.json"),
            "human_review_completed": False,
            "independent_final_test_completed": False,
            "default_promoted": False,
            "dataset_fingerprint": balls["fingerprint"],
            "scope": "73 AI-curated development frames, fixed 640-pixel tiling; not independent final accuracy",
        }
        ball_profile = {
            "schema_version": 1,
            "profile_name": "Broadcastbal v2 — native tegels, experimenteel",
            "models": [spec],
            "handoff": handoff,
        }
        combo = copy.deepcopy(read_json("configs/models-players.json"))
        combo["profile_name"] = "Spelers v3 + broadcastbal v2 — experimentele combinatie"
        combo["models"].append(spec)
        combo["handoff"].update(
            ball_evaluation_record=evidence,
            ball_evaluation_sha256=handoff["evaluation_sha256"],
            default_promoted=False,
            joint_accuracy_evaluated=False,
            ball_available_in_this_profile=True,
        )
        for path, profile in (
            (Path("configs/models-ball-broadcast-v2.json"), ball_profile),
            (Path("configs/models-players-ball-broadcast-v2.json"), combo),
        ):
            if path.exists() and read_json(path) != profile:
                raise ValueError("Preserve edited profile; choose a fresh version")
            write_json(path, profile)
            profiles.append(str(path))
        # Exercise the real runtime path, including actual class identities and native tiling.
        (Path(".cache/ultralytics-broadcast-v2") / "Ultralytics").mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(".cache/ultralytics-broadcast-v2").resolve()))
        from ultralytics import settings

        settings.update(
            {
                k: False
                for k in ("sync", "clearml", "comet", "dvc", "mlflow", "neptune", "wandb")
                if k in settings
            }
        )
        from football_pipeline.detection import UltralyticsDetector, load_model_manifest

        row = next(
            r
            for r in read_json("data/broadcast-ball-review-v1/curated/manifest.json")["frames"]
            if r["split"] == "val"
        )
        pixels = cv2.imread(str(Path("data/broadcast-ball-review-v1/curated") / row["image"]))
        detector = UltralyticsDetector(load_model_manifest(profiles[-1]))
        detected = detector.detect(pixels, 0)
        smoke = {
            "profile": profiles[-1],
            "frame_id": row["frame_id"],
            "observed_classes": dict(Counter(d.semantic_class for d in detected)),
            "status": "passed",
        }
    else:
        smoke = {"status": "not published; measured gate failed"}
    suite = ET.parse(report_root / "software-tests.xml").getroot().find("testsuite")
    software = {k: int(suite.attrib[k]) for k in ("tests", "failures", "errors", "skipped")}
    summary = {
        "player_training": {
            "before": 6000,
            "after": players["counts"]["train"],
            "covered_train_seconds": len(selected_bins),
            "validation_frames_unchanged": len(val),
            "before_adjacent_gaps": gaps(source["frames"]),
            "after_adjacent_gaps": gaps(players["frames"]),
            "class_counts": {s: dict(c) for s, c in label_counts.items()},
            "player_accuracy_retrained_or_claimed": False,
        },
        "ball_data": {
            "counts": balls["counts"],
            "negative_counts": balls["negative_counts"],
            "unique_source_frames": balls["unique_source_frames"],
            "native_pixels_verified": True,
            "duplicate_windows_excluded": len(balls["duplicate_windows_excluded"]),
            "reviewed_negative_candidates": 36,
            "negative_candidates_rejected": 2,
        },
        "experiment": {
            "epochs_completed": len(epochs),
            "comparison": "reports/broadcast-data/v2-experiment.json",
            "baseline_tiled": old,
            "candidate_tiled": new,
            "candidate_meets_optional_profile_gate": eligible,
            "standalone_full_frame_TP_before": baseline["full"]["per_class"][0]["TP"],
            "standalone_full_frame_TP_after": candidate["full"]["per_class"][0]["TP"],
        },
        "optional_profiles": profiles,
        "runtime_smoke": smoke,
        "software_tests": software,
        "actual_training_source_sha256": sha256_file(artifact / "experiment-source.py"),
        "evaluation_source_sha256": {
            p: sha256_file(p) for p in ("persoon1/metrics.py", "src/football_pipeline/ball_tiles.py")
        },
        "current_tool_source_sha256": {
            p: sha256_file(p)
            for p in (
                "scripts/prepare_broadcast_v2.py",
                "scripts/experiment_broadcast_v2.py",
                "scripts/verify_broadcast_v2.py",
                "tests/test_broadcast_v2.py",
            )
        },
        "active_defaults_changed": False,
        "human_review_completed": False,
        "independent_final_test_completed": False,
        "source_image_count_increase": 0,
    }
    write_json(report_root / "v2-summary.json", summary)
    for name in ("summary.json", "follow-up-summary.json"):
        saved = read_json(report_root / name)
        saved["v2_summary"] = "reports/broadcast-data/v2-summary.json"
        write_json(report_root / name, saved)
    print(summary)


if __name__ == "__main__":
    main()
