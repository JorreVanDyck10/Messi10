"""Train-side selection of one association threshold on frozen native detections."""

from collections import defaultdict
from pathlib import Path

import cv2
import torch

from football_pipeline.contracts import Detection, digest_json, read_json, sha256_file, write_json
from football_pipeline.teams import load_team_settings
from football_pipeline.tracking import ByteTrackAdapter, load_tracker_config
from scripts.evaluate_temporal_broadcast import score, summarize

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/broadcast-reliability-day2/tracker-association-v1"


def run_clip(rows, source, config, output, settings):
    target = output / f"{rows[0]['clip']}.json"
    identity = digest_json([sha256_file(source), config, rows])
    if target.exists():
        saved = read_json(target)
        if saved["identity"] != identity:
            raise ValueError("Tracking replay inputs changed")
        return saved["score"]
    cached = read_json(source)
    tracker = ByteTrackAdapter(config, rows[0]["fps"], camera_motion=True)
    for row, frame in zip(rows, cached["frames"], strict=True):
        image = cv2.imread(row["image"])
        if image is None or sha256_file(row["image"]) != row["image_sha256"]:
            raise ValueError("Tracking source changed")
        detections = [Detection(**d) for d in frame["detections"]]
        tracker.update(detections, row["frame_index"], (row["width"], row["height"]), frame=image)
        for d, serialized in zip(detections, frame["detections"], strict=True):
            serialized["track_id"] = d.track_id
        frame["reset"] = tracker.motion.state["reset_tracks"]
    result = score(rows, cached, settings)
    write_json(target, {"identity": identity, "score": result, "config": config})
    print(f"Tracker {output.name} {rows[0]['clip']}: {result['tracking']}", flush=True)
    return result


def main():
    torch.set_num_threads(2)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    base = load_tracker_config(ROOT / "configs/bytetrack.yaml")
    settings = load_team_settings(ROOT / "configs/teams-broadcast.json")
    groups = defaultdict(list)
    for row in read_json(ROOT / "data/broadcast-temporal-v1/manifest.json")["frames"]:
        groups[row["clip"]].append(row)
    thresholds = [0.8, 0.7, 0.85, 0.9]
    preregistration = {
        "match_thresholds": thresholds,
        "base_config": base,
        "selection": "training IDF1 improves at least 0.002, no extra ID switches; then validate once",
        "frozen_detection_root": "temporal-native-v1",
        "test_accessed": False,
    }
    target = OUTPUT / "selection-inputs.json"
    if target.exists() and read_json(target) != preregistration:
        raise ValueError("Tracking selection changed")
    write_json(target, preregistration)
    train_results = {}
    for threshold in thresholds:
        directory = OUTPUT / f"threshold-{threshold}"
        directory.mkdir(exist_ok=True)
        config = {**base, "match_thresh": threshold}
        results = [
            run_clip(
                rows,
                ROOT / "artifacts/broadcast-reliability-day2/temporal-native-v1" / f"{clip}.json",
                config,
                directory,
                settings,
            )
            for clip, rows in groups.items()
            if rows[0]["split"] == "train"
        ]
        train_results[str(threshold)] = {"summary": summarize(results)["train"], "per_clip": results}
        write_json(OUTPUT / "training-results.json", train_results)
    baseline = train_results["0.8"]["summary"]
    candidates = [
        k
        for k, v in train_results.items()
        if k != "0.8"
        and v["summary"]["IDF1"] >= baseline["IDF1"] + 0.002
        and v["summary"]["ID_switches"] <= baseline["ID_switches"]
        and v["summary"]["image_IDF1"] >= baseline["image_IDF1"]
    ]
    selected = max(candidates, key=lambda k: train_results[k]["summary"]["IDF1"]) if candidates else None
    write_json(
        OUTPUT / "training-selection.json",
        {
            "selected": selected,
            "baseline": baseline,
            "eligible": candidates,
            "validation_accessed_for_selection": False,
        },
    )
    if selected is None:
        print("No tracking candidate passed training gates", flush=True)
        return
    validation = {}
    for route in ("temporal-native-v1", "automatic-native-v1"):
        validation[route] = {}
        for threshold in ("0.8", selected):
            directory = OUTPUT / f"{route}-threshold-{threshold}"
            directory.mkdir(exist_ok=True)
            config = {**base, "match_thresh": float(threshold)}
            results = [
                run_clip(
                    rows,
                    ROOT / "artifacts/broadcast-reliability-day2" / route / f"{clip}.json",
                    config,
                    directory,
                    settings,
                )
                for clip, rows in groups.items()
                if rows[0]["split"] == "val"
            ]
            validation[route][threshold] = {"summary": summarize(results)["val"], "per_clip": results}
            write_json(OUTPUT / "validation-results.json", validation)
    print({"selected_on_training": selected, "validation": validation}, flush=True)


if __name__ == "__main__":
    main()
