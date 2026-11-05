"""Recheck the earlier selected field policy against all2700provider-line frames."""

import gzip
import json
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
from evaluate_temporal_extension_field import reference_metrics

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.field_learning import upstream_runtime
from football_pipeline.field_motion import DEFAULT_SETTINGS, CameraCalibration, estimate_checked

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts/broadcast-reliability-20261030"


def references(rows, directory):
    provider_clip = rows[0].get("provider_clip", rows[0]["clip"])
    path = ROOT / "data/broadcast-pitch-v1/provider-labels" / f"{provider_clip}.json.gz"
    provider = json.loads(gzip.decompress(path.read_bytes()))
    if any(row["provider_sha256"] != sha256_file(path) for row in rows):
        raise ValueError("Original provider annotations changed")
    ids = {int(Path(im["file_name"]).stem) - 1: str(im["image_id"]) for im in provider["images"]}
    pitch = {
        str(a["image_id"]): a["lines"] for a in provider["annotations"] if a.get("supercategory") == "pitch"
    }
    result = []
    directory.mkdir(parents=True, exist_ok=True)
    for row in rows:
        copy = dict(row)
        if not row.get("field_label"):
            lines = pitch.get(ids[row["source_frame_index"]])
            target = directory / f"{row['frame_id']}.json"
            if lines:
                write_json(target, lines)
            copy.update(
                field_label=str(target) if lines else None, label_policy="provider_visible_polylines_v1"
            )
        result.append(copy)
    return result


def signature(state):
    return {
        "valid": state["status"] == "valid",
        "homography": state.get("homography") if state["status"] == "valid" else None,
        "polygon": state.get("visible_field_polygon_xy") if state["status"] == "valid" else None,
        "polygon_present": "visible_field_polygon_xy" in state if state["status"] == "valid" else False,
    }


def main():
    output = ARTIFACTS / "release-rank-audit-v1"
    output.mkdir(parents=True, exist_ok=True)
    upstream_runtime(ROOT / "artifacts/joint-retrain-20261027-v2/selected-field-runtime.json")
    results = []
    for version in (1, 2):
        dataset_path = ROOT / f"data/broadcast-temporal-v{version}/manifest.json"
        dataset = read_json(dataset_path)
        grouped = defaultdict(list)
        for row in dataset["frames"]:
            grouped[row["clip"]].append(row)
        for clip, rows in grouped.items():
            rows = references(rows, output / "references" / clip)
            if version == 1:
                original = ROOT / "artifacts/broadcast-reliability-day2/field-native-v1" / clip
                before = read_json(original / "states.json")["frames"]
                after = read_json(
                    ROOT / "artifacts/broadcast-reliability-day2/field-motion-rank-v2" / clip / "states.json"
                )["frames"]
                observation_path = Path(read_json(original / "projection-metrics.json")["calibration_bundle"])
                observations = [json.loads(line) for line in observation_path.read_text().splitlines()]
            else:
                after = read_json(ARTIFACTS / "extension-field-v2/baseline" / clip / "states.json")["frames"]
                observations = [
                    read_json(ARTIFACTS / "extension-field-raw-v1" / clip / f"{i:06d}.json")["observation"]
                    for i in range(len(rows))
                ]
                camera = CameraCalibration(rows[0]["fps"], DEFAULT_SETTINGS)
                before = []
                for row, observation in zip(rows, observations, strict=True):
                    if sha256_file(row["image"]) != row["image_sha256"]:
                        raise ValueError("Original source pixels changed")
                    direct = estimate_checked(observation, observation["image_size"], DEFAULT_SETTINGS)
                    before.append(camera.update(cv2.imread(row["image"]), direct, row["frame_index"]))
            old_reference = reference_metrics(rows, observations, before)
            new_reference = reference_metrics(rows, observations, after)
            old_by_id = {r["frame_index"]: r for r in old_reference["per_frame"]}
            new_by_id = {r["frame_index"]: r for r in new_reference["per_frame"]}
            changes = []
            for i, (a, b) in enumerate(zip(before, after, strict=True)):
                if signature(a) != signature(b):
                    changes.append(
                        {
                            "frame_index": i,
                            "source_frame_index": rows[i]["source_frame_index"],
                            "before": old_by_id.get(i, {}).get("status", "no_field_reference"),
                            "motion_rank": new_by_id.get(i, {}).get("status", "no_field_reference"),
                            "before_available": a["status"] == "valid",
                            "motion_rank_available": b["status"] == "valid",
                        }
                    )
            result = {
                "clip": clip,
                "game_id": rows[0]["game_id"],
                "split": rows[0]["split"],
                "window": rows[0].get("window", "first"),
                "frames": len(rows),
                "before": old_reference,
                "motion_rank": new_reference,
                "projection_changes": changes,
                "dataset_sha256": sha256_file(dataset_path),
            }
            directory = output / clip
            directory.mkdir(exist_ok=True)
            write_json(directory / "default-states.json", {"frames": before})
            write_json(directory / "metrics.json", result)
            results.append(result)
            write_json(
                output / "metrics.json",
                {
                    "per_clip": results,
                    "source_sha256": sha256_file(__file__),
                    "human_review_completed": False,
                    "independent_final_test_completed": False,
                },
            )
            print(
                clip,
                "before",
                (old_reference["correct"], old_reference["wrong"]),
                "motion_rank",
                (new_reference["correct"], new_reference["wrong"]),
                "changed",
                len(changes),
                flush=True,
            )
    compact = []
    for item in results:
        compact.append(
            {
                **{k: v for k, v in item.items() if k not in {"before", "motion_rank"}},
                "before": {k: v for k, v in item["before"].items() if k != "per_frame"},
                "motion_rank": {k: v for k, v in item["motion_rank"].items() if k != "per_frame"},
            }
        )
    write_json(
        ROOT / "reports/broadcast-reliability-20261030/motion-rank-release-audit.json",
        {
            "per_clip": compact,
            "source_sha256": sha256_file(__file__),
            "meaning": "Provider-line tolerances; unsupported references counted separately; every person frame retained",
            "human_review_completed": False,
            "independent_final_test_completed": False,
        },
    )


if __name__ == "__main__":
    main()
