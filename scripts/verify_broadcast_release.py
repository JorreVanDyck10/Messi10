"""Reproduce the historical rank-bridge trial; it is no longer the default policy."""

import json
import statistics
import time
from pathlib import Path

import cv2
import torch

from football_pipeline.automatic_calibration import AutomaticCalibration, load_automatic_calibration
from football_pipeline.contracts import read_json, write_json
from football_pipeline.detection import UltralyticsDetector, load_model_manifest
from football_pipeline.distances import estimate_distances
from football_pipeline.field_motion import DEFAULT_SETTINGS, MOTION_RANK_SETTINGS
from football_pipeline.pipeline import process_video, validate_completed

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/broadcast-reliability-release-20261028"
DEMO = ROOT / "runs/d3cff1b2360bb235635d9e2dcd99870a462d153a6b253913c73afb2f07b61664"
FULL = ROOT / "runs/0b2006b23d066695e0c35ebe1d282748e2d083217f3a33ee638783db251c4167"


def process(source, label, policy, profile):
    original = validate_completed(source)
    bundle = load_automatic_calibration(source / "calibration.json")
    calibration = AutomaticCalibration(bundle.manifest, bundle.observations_path, policy)
    started = time.perf_counter()
    result = process_video(
        original["video"]["path"],
        calibration,
        profile,
        OUTPUT / label,
        tracker_config_path=ROOT / "configs/bytetrack.yaml",
        team_config_path=ROOT / "configs/teams-broadcast.json",
        progress=lambda n, total, elapsed: (
            print(f"Integration {label}: {n}/{total}", flush=True) if n % 150 == 0 else None
        ),
    )
    elapsed = time.perf_counter() - started
    directory = Path(result.directory)
    manifest = validate_completed(directory)
    with (directory / "framegegevens.jsonl").open(encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream]
    tracks, intervals = estimate_distances(records, manifest["video"]["duration_s"])
    write_json(
        directory / "observed-distance-check.json",
        {
            "tracks": tracks,
            "intervals": intervals,
            "independent_accuracy_measured": False,
            "field_dimensions_assumed": [105, 68],
        },
    )
    check = {
        "label": label,
        "run": str(directory),
        "elapsed_s": elapsed,
        "frames": len(records),
        "source": "native detector, roles, tracking, team assignment and video/CSV render",
        "calibration_settings": manifest.get("field_settings"),
        "cached_field_network_observations": True,
        "field_valid_frames": sum(r["calibration"]["status"] == "valid" for r in records),
        "tracks_with_distance_intervals": sum(r["measured_s"] > 0 for r in tracks),
    }
    print(check, flush=True)
    return check


def main():
    torch.set_num_threads(4)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / "integration.json"
    reports = read_json(target)["runs"] if target.exists() else []
    done = {r["label"] for r in reports}
    # Warm the GPU once; every measured run still creates its own native detector.
    source = read_json(DEMO / "runmanifest.json")
    detector = UltralyticsDetector(load_model_manifest(ROOT / "configs/models-broadcast.json"))
    capture = cv2.VideoCapture(source["video"]["path"])
    ok, frame = capture.read()
    capture.release()
    if not ok:
        raise ValueError("Missing demonstration frame")
    detector.detect(frame, 0)
    torch.cuda.synchronize()
    del detector
    torch.cuda.empty_cache()
    baseline = ROOT / "artifacts/broadcast-reliability-day2/baseline-before-field-profile.json"
    candidate = ROOT / "configs/models-broadcast.json"
    cases = [
        (DEMO, "baseline-a", DEFAULT_SETTINGS, baseline),
        (DEMO, "candidate-a", MOTION_RANK_SETTINGS, candidate),
        (DEMO, "candidate-b", MOTION_RANK_SETTINGS, candidate),
        (DEMO, "baseline-b", DEFAULT_SETTINGS, baseline),
        (FULL, "full-broadcast", MOTION_RANK_SETTINGS, candidate),
    ]
    for args in cases:
        if args[1] in done:
            continue
        reports.append(process(*args))
        write_json(
            target, {"runs": reports, "independent_final_test": False, "human_review_completed": False}
        )
    old = statistics.median(r["elapsed_s"] for r in reports if r["label"].startswith("baseline"))
    new = statistics.median(r["elapsed_s"] for r in reports if r["label"].startswith("candidate"))
    write_json(
        OUTPUT / "timing.json",
        {
            "baseline_median_s": old,
            "candidate_median_s": new,
            "ratio": new / old,
            "max_ratio": 1.2,
            "passed": new <= old * 1.2,
            "scope": "paired 150-frame native pipeline incl model init, projection, tracking, team fit, video and CSV; unchanged field network excluded via shared observations",
        },
    )


if __name__ == "__main__":
    main()
