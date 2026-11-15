"""Controleer vaste spelertracking op ontwikkelclips en toon het effect van uitsluitend weergavedrempels."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

import cv2
import torch

from football_pipeline.contracts import FrameRecord, read_json, sha256_file, write_json
from football_pipeline.detection import load_model_manifest
from football_pipeline.participants import player_display_policy, player_summary, visible_in_record
from football_pipeline.pipeline import validate_completed
from football_pipeline.render import render_frame
from football_pipeline.teams import load_team_settings
from football_pipeline.tracking import Trajectories, load_tracker_config
from football_pipeline.video import ROOT, VideoWriter
from scripts.evaluate_temporal_broadcast import infer_clip, score, summarize


def observation_summary(records):
    """Meet waargenomen ID-continuïteit en velddekking zonder ongekende echte identiteiten te veronderstellen."""
    frames_by_id, resets, states = defaultdict(list), [], Counter()
    players = with_id = projected = field_frames = 0
    events, previous = [], set()
    for record in records:
        ds = [d for d in record.detections if d.semantic_class == "player"]
        current = {d.track_id for d in ds if d.track_id is not None}
        players += len(ds)
        with_id += sum(d.track_id is not None for d in ds)
        projected += sum(d.projection_status == "valid" for d in ds)
        field_frames += (record.calibration or {}).get("status") == "valid"
        motion = record.tracking or {}
        states[motion.get("status", "not_recorded")] += 1
        if motion.get("reset_tracks"):
            resets.append({"frame": record.frame_index, "reason": motion.get("status")})
            events.append(
                {"frame": record.frame_index, "kind": "camera_reset", "detail": motion.get("status")}
            )
        if record.frame_index > 25 and len(current - previous) >= 2:
            events.append(
                {"frame": record.frame_index, "kind": "new_ids", "detail": sorted(current - previous)}
            )
        if any(d.track_id is not None and d.confidence < 0.25 for d in ds):
            events.append(
                {
                    "frame": record.frame_index,
                    "kind": "tracked_low_confidence",
                    "detail": "intern gekoppeld, onder 0.25",
                }
            )
        for d in ds:
            if d.track_id is not None:
                frames_by_id[d.track_id].append(record.frame_index)
        previous = current
    gaps = [b - a - 1 for frames in frames_by_id.values() for a, b in zip(frames, frames[1:]) if b > a + 1]
    return {
        "frames": len(records),
        "player_observations": players,
        "observations_with_id": with_id,
        "id_coverage": with_id / max(1, players),
        "projected_player_observations": projected,
        "frames_with_valid_field": field_frames,
        "distinct_temporary_ids": len(frames_by_id),
        "same_id_reappearances_after_gap": len(gaps),
        "largest_gap_frames": max(gaps, default=0),
        "camera_resets": resets,
        "camera_motion_states": dict(states),
        "events": events,
        "ground_truth_available": False,
        "id_switch_accuracy_measured": False,
    }


def render_display_replay(run, records, output, confidence):
    """Render dezelfde detecties en ID's opnieuw; alleen het opgeslagen spelersweergavebeleid verschilt."""
    manifest = validate_completed(run)
    video = manifest["video"]
    source = Path(video["path"])
    if sha256_file(source) != video["sha256"]:
        raise ValueError("Upload changed")
    output.mkdir(exist_ok=True, parents=True)
    capture = cv2.VideoCapture(str(source))
    writer = VideoWriter(output / "vergelijking.mp4", 1920, 720, video["fps_num"], video["fps_den"])
    histories = Trajectories(video["fps_num"] / video["fps_den"])
    policy = player_display_policy(confidence)
    counts = []
    try:
        with (output / "framegegevens.jsonl").open("w", encoding="utf-8") as stream:
            for record in records:
                ok, frame = capture.read()
                if not ok:
                    raise ValueError("Incomplete source video")
                current = replace(record, player_policy=policy)
                histories.update(
                    [d for d in current.detections if visible_in_record(current, d)], current.frame_index
                )
                writer.write(render_frame(frame, current, histories))
                stream.write(json.dumps(current.to_dict(), allow_nan=False) + "\n")
                counts.append(player_summary(current)["on_field"])
        writer.close()
    except BaseException:
        writer.close(abort=True)
        raise
    finally:
        capture.release()
    with (output / "telling.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        table = csv.writer(stream)
        table.writerow(["frame_index", "players_on_field"])
        table.writerows(enumerate(counts))
    write_json(
        output / "settings.json",
        {
            "player_policy": policy,
            "source_run": str(run),
            "same_detections_and_ids": True,
            "frames": len(counts),
        },
    )
    return {
        "policy": policy,
        "sum_on_field_observations": sum(c for c in counts if c is not None),
        "video": str(output / "vergelijking.mp4"),
    }


def event_examples(run, events, output, fps):
    """Bewaar korte fragmenten rond verschillende soorten trackinggebeurtenissen voor visuele beoordeling."""
    chosen = []
    for kind in ("camera_reset", "new_ids", "tracked_low_confidence"):
        event = next((e for e in events if e["kind"] == kind), None)
        if event:
            chosen.append(event)
    capture = cv2.VideoCapture(str(run / "samengestelde_video.mp4"))
    try:
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        for event in chosen:
            start, end = max(0, event["frame"] - round(fps)), min(total, event["frame"] + round(fps) + 1)
            capture.set(cv2.CAP_PROP_POS_FRAMES, start)
            target = output / f"event-{event['kind']}.mp4"
            writer = VideoWriter(target, 1920, 720, round(fps * 1000), 1000)
            try:
                for index in range(start, end):
                    ok, frame = capture.read()
                    if not ok:
                        raise ValueError("Event clip truncated")
                    writer.write(frame)
                    if index == event["frame"]:
                        cv2.imwrite(str(output / f"event-{event['kind']}.jpg"), frame)
                writer.close()
            except BaseException:
                writer.close(abort=True)
                raise
            event.update(video=str(target), start_frame=start, end_frame_exclusive=end)
    finally:
        capture.release()
    return chosen


def main():
    """Audit uitsluitend de temporele validatiesplit en de vaste laatste upload; schrijf hervatbare tussenresultaten."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/player-threshold-tracking-20261113")
    parser.add_argument("--upload-run", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    models = load_model_manifest(ROOT / "configs/models-broadcast.json")
    settings = load_team_settings(ROOT / "configs/teams-broadcast.json")
    dataset_path = ROOT / "data/broadcast-temporal-v1/manifest.json"
    dataset = read_json(dataset_path)
    groups = defaultdict(list)
    for row in dataset["frames"]:
        if row["split"] == "val":
            groups[row["clip"]].append(row)
    native = args.output / "validation-native"
    native.mkdir(exist_ok=True)
    results = []
    write_json(
        args.output / "audit-inputs.json",
        {
            "models": models,
            "tracker": load_tracker_config(ROOT / "configs/bytetrack.yaml"),
            "dataset_sha256": sha256_file(dataset_path),
            "clips": list(groups),
            "independent_final_test": False,
            "geometry": "provider reference; not automatic field accuracy",
        },
    )
    for clip, rows in groups.items():
        print(f"Validating {clip} ({len(rows)} frames)", flush=True)
        cached = infer_clip(rows, models, settings, native)
        results.append(score(rows, cached, settings, count_policy="runtime"))
        write_json(
            args.output / "tracking-validation.json",
            {
                "per_clip": results,
                "summary": summarize(results),
                "count_policy": "runtime_original",
                "geometry": "provider",
                "test_accessed": False,
            },
        )
    manifest = validate_completed(args.upload_run)
    if manifest["models"] != models:
        raise ValueError("Upload uses a different player profile")
    records = [
        FrameRecord.from_dict(json.loads(line))
        for line in (args.upload_run / "framegegevens.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    before = [[(d.detection_id, d.track_id, d.confidence) for d in r.detections] for r in records]
    observed = observation_summary(records)
    write_json(args.output / "upload-observations.json", observed)
    displays = {}
    for name, threshold in (("original", None), ("strict-025", 0.25), ("strict-065", 0.65)):
        print(f"Display replay {name}", flush=True)
        displays[name] = render_display_replay(args.upload_run, records, args.output / name, threshold)
    assert before == [[(d.detection_id, d.track_id, d.confidence) for d in r.detections] for r in records]
    examples = event_examples(
        args.upload_run,
        observed["events"],
        args.output,
        manifest["video"]["fps_num"] / manifest["video"]["fps_den"],
    )
    write_json(
        args.output / "display-verification.json",
        {
            "same_detections_ids_confidences": True,
            "ball_settings_unchanged": True,
            "variants": displays,
            "examples": examples,
            "source_run": str(args.upload_run),
            "records_sha256": sha256_file(args.upload_run / "framegegevens.jsonl"),
        },
    )
    print("Audit complete", flush=True)


if __name__ == "__main__":
    main()
