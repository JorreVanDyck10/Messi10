"""Replay both field policies on the user's longer broadcast development clip."""

from collections import Counter
from pathlib import Path

import cv2

from football_pipeline.automatic_calibration import AutomaticCalibration, load_automatic_calibration
from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.field_motion import DEFAULT_SETTINGS, MOTION_RANK_SETTINGS, CameraCalibration
from football_pipeline.video import inspect_video

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "runs/0b2006b23d066695e0c35ebe1d282748e2d083217f3a33ee638783db251c4167"
    manifest = read_json(source / "runmanifest.json")
    video = inspect_video(manifest["video"]["path"])
    if video.sha256 != manifest["video"]["sha256"]:
        raise ValueError("Original broadcast clip changed")
    bundle = load_automatic_calibration(source / "calibration.json")
    bundle.validate_for(video)
    output = ROOT / "artifacts/broadcast-reliability-day2/user-clip-motion-rank-v1"
    output.mkdir(parents=True, exist_ok=False)
    profiles = {"baseline": DEFAULT_SETTINGS, "motion_rank": MOTION_RANK_SETTINGS}
    streams = {
        n: AutomaticCalibration(bundle.manifest, bundle.observations_path, s).frames(video)
        for n, s in profiles.items()
    }
    cameras = {n: CameraCalibration(video.fps, s) for n, s in profiles.items()}
    states = {n: [] for n in profiles}
    capture = cv2.VideoCapture(video.path)
    try:
        for index in range(video.frame_count):
            ok, frame = capture.read()
            if not ok:
                raise ValueError("Incomplete broadcast timeline")
            for name in profiles:
                state = cameras[name].update(frame, next(streams[name]), index)
                states[name].append(state)
                if state["status"] == "valid" and state.get("source") == "tracked":
                    if state["age_s"] > profiles[name]["maximum_age_s"]:
                        raise ValueError("Propagation exceeded the fixed age bound")
            if (index + 1) % 150 == 0:
                print(f"Broadcast field replay {index + 1}/{video.frame_count}", flush=True)
    finally:
        capture.release()
    summary = {}
    for name, values in states.items():
        write_json(output / f"{name}-states.json", {"frames": values})
        count = Counter(v["status"] for v in values)
        summary[name] = {"frames": len(values), "valid": count["valid"], "status_counts": dict(count)}
    summary.update(
        gained=sum(b["status"] != "valid" and c["status"] == "valid" for b, c in zip(*states.values())),
        lost=sum(b["status"] == "valid" and c["status"] != "valid" for b, c in zip(*states.values())),
        independent_final_test=False,
        human_review_completed=False,
        accuracy_measured=False,
        observations_sha256=sha256_file(bundle.observations_path),
    )
    write_json(output / "summary.json", summary)
    print(summary, flush=True)


if __name__ == "__main__":
    main()
