"""Checked future-anchor backfill on frozen development observations; no new network inference."""

import argparse
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.automatic_calibration import transform
from football_pipeline.bidirectional_field import backward_backfill
from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.field_motion import MOTION_RANK_SETTINGS, estimate_checked

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/broadcast-reliability-20261030/backward-field-v1"


def reverse_video(path, count, block=16):
    capture = cv2.VideoCapture(str(path))
    try:
        stop = count
        while stop:
            start = max(0, stop - block)
            capture.set(cv2.CAP_PROP_POS_FRAMES, start)
            frames = []
            for _ in range(start, stop):
                ok, frame = capture.read()
                if not ok:
                    raise ValueError("Incomplete reverse video block")
                frames.append(frame)
            for index in range(stop - 1, start - 1, -1):
                yield index, frames[index - start]
            stop = start
    finally:
        capture.release()


def point_errors(rows, states, clip):
    clip = rows[0].get("provider_clip", clip)
    provider = json.loads(
        gzip.decompress((ROOT / "data/broadcast-pitch-v1/provider-labels" / (clip + ".json.gz")).read_bytes())
    )
    ids = {int(Path(i["file_name"]).stem) - 1: str(i["image_id"]) for i in provider["images"]}
    annotations = defaultdict(list)
    for annotation in provider["annotations"]:
        annotations[str(annotation["image_id"])].append(annotation)
    errors = {}
    for row, state in zip(rows, states, strict=True):
        if state["status"] != "valid":
            continue
        for a in annotations[ids[row["source_frame_index"]]]:
            box, pitch = a.get("bbox_image"), a.get("bbox_pitch")
            if a.get("category_id") not in {1, 2} or not box or not pitch:
                continue
            x, y = pitch.get("x_bottom_middle"), pitch.get("y_bottom_middle")
            if x is None or y is None or not -52.5 <= x <= 52.5 or not -34 <= y <= 34:
                continue
            try:
                uv = transform(
                    [[box["x"] + box["w"] / 2, box["y"] + box["h"]]], np.asarray(state["homography"])
                )[0]
            except ValueError:
                continue
            key = f"{row['frame_index']}:{a['id']}"
            errors[key] = float(np.linalg.norm((uv - [(x + 52.5) / 105, (y + 34) / 68]) * [105, 68]))
    return errors


def evaluate(name, observations, forward, reverse_frames, rows=None):
    directory = OUTPUT / name
    directory.mkdir(parents=True, exist_ok=True)
    identity = digest_json(
        [
            observations,
            forward,
            MOTION_RANK_SETTINGS,
            sha256_file(ROOT / "src/football_pipeline/bidirectional_field.py"),
        ]
    )
    path = directory / "metrics.json"
    if path.exists():
        saved = read_json(path)
        if saved["identity"] != identity:
            raise ValueError("Backfill inputs changed; preserve result and select new output")
        return saved
    direct = [estimate_checked(o, o["image_size"], MOTION_RANK_SETTINGS) for o in observations]
    backward = backward_backfill(direct, forward, reverse_frames, 25, MOTION_RANK_SETTINGS)
    gained = [
        i
        for i, (a, b) in enumerate(zip(forward, backward))
        if a["status"] != "valid" and b["status"] == "valid"
    ]
    report = {
        "identity": identity,
        "frames": len(direct),
        "baseline_valid": sum(x["status"] == "valid" for x in forward),
        "candidate_valid": sum(x["status"] == "valid" for x in backward),
        "gained_frames": gained,
        "lost_frames": sum(
            a["status"] == "valid" and b["status"] != "valid" for a, b in zip(forward, backward)
        ),
        "status_counts": dict(Counter(x["status"] for x in backward)),
        "independent_final_test": False,
        "human_review_completed": False,
        "maximum_anchor_age_s": 2.0,
    }
    if rows is not None:
        before, after = point_errors(rows, forward, name), point_errors(rows, backward, name)
        added = [error for key, error in after.items() if key not in before]
        report.update(
            split=rows[0]["split"],
            game_id=rows[0]["game_id"],
            added_points=len(added),
            added_median_m=float(np.median(added)) if added else None,
            added_p90_m=float(np.quantile(added, 0.9)) if added else None,
            common_point_errors_unchanged=all(abs(before[k] - after[k]) < 1e-10 for k in before),
            added_point_errors_m=added,
        )
    write_json(directory / "states.json", {"frames": backward})
    write_json(path, report)
    print({k: v for k, v in report.items() if k not in {"added_point_errors_m", "gained_frames"}}, flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--own-clip", action="store_true")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if args.own_clip:
        original = ROOT / "runs/0b2006b23d066695e0c35ebe1d282748e2d083217f3a33ee638783db251c4167"
        manifest = read_json(original / "runmanifest.json")
        observations = [
            json.loads(line)
            for line in (original / "observations.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        states = [
            json.loads(line)["calibration"]
            for line in (
                ROOT
                / "runs/316e0824bc9fbb019691a294474bbc008c9701072b5309b6ee3939e759e6c386/framegegevens.jsonl"
            )
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        assert sha256_file(manifest["video"]["path"]) == manifest["video"]["sha256"]
        evaluate("own-broadcast", observations, states, reverse_video(manifest["video"]["path"], len(states)))
        return
    groups = defaultdict(list)
    for row in read_json(ROOT / "data/broadcast-temporal-v1/manifest.json")["frames"]:
        groups[row["clip"]].append(row)
    results = []
    for clip, rows in groups.items():
        baseline = read_json(
            ROOT / "artifacts/broadcast-reliability-day2/field-native-v1" / clip / "projection-metrics.json"
        )
        observations = [
            json.loads(line)
            for line in Path(baseline["calibration_bundle"]).read_text(encoding="utf-8").splitlines()
        ]
        states = read_json(
            ROOT / "artifacts/broadcast-reliability-day2/field-motion-rank-v2" / clip / "states.json"
        )["frames"]

        def images():
            for row in reversed(rows):
                frame = cv2.imread(row["image"])
                if frame is None or sha256_file(row["image"]) != row["image_sha256"]:
                    raise ValueError("Frozen reverse image changed")
                yield row["frame_index"], frame

        results.append(evaluate(clip, observations, states, images(), rows))
        write_json(OUTPUT / "summary.json", {"per_clip": results, "independent_final_test": False})


if __name__ == "__main__":
    main()
