"""Checkpoint native-frame inference and compare baseline with causal role consensus."""

import argparse
import copy
import gzip
import json
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

import cv2
import torch

from football_pipeline.automatic_calibration import project_automatic
from football_pipeline.broadcast_evaluation import reference_geometry
from football_pipeline.contracts import Detection, digest_json, read_json, sha256_file, write_json
from football_pipeline.detection import UltralyticsDetector, load_model_manifest
from football_pipeline.keeper_teams import KeeperTeamConsensus
from football_pipeline.teams import TeamAssigner, TeamSamples, load_team_settings, shirt_color
from football_pipeline.temporal_roles import TemporalOfficials
from football_pipeline.tracking import ByteTrackAdapter, load_tracker_config
from football_pipeline.tracking_evaluation import identity_metrics
from persoon1.metrics import evaluate, iou

ROOT = Path(__file__).resolve().parents[1]


def infer_clip(rows, models, settings, output, geometry_states=None):
    identity = digest_json(
        [
            rows,
            models,
            settings,
            geometry_states,
            {str(p.relative_to(ROOT)): sha256_file(p) for p in (ROOT / "src/football_pipeline").glob("*.py")},
        ]
    )
    target = output / f"{rows[0]['clip']}.json"
    if target.exists():
        cached = read_json(target)
        if cached["identity"] != identity:
            raise ValueError("Inference changed: use a new output directory")
        return cached
    started = time.perf_counter()
    detector = UltralyticsDetector(models)
    detector.set_video_identity(rows[0]["clip"])
    tracker = ByteTrackAdapter(
        load_tracker_config(ROOT / "configs/bytetrack.yaml"), rows[0]["fps"], camera_motion=True
    )
    labels = ROOT / "data/broadcast-pitch-v1/provider-labels" / f"{rows[0]['clip']}.json.gz"
    provider = json.loads(gzip.decompress(labels.read_bytes()))
    annotations = defaultdict(list)
    for a in provider["annotations"]:
        annotations[str(a["image_id"])].append(a)
    image_ids = {int(Path(i["file_name"]).stem) - 1: str(i["image_id"]) for i in provider["images"]}
    found = []
    for row in rows:
        image = cv2.imread(row["image"])
        if image is None or sha256_file(row["image"]) != row["image_sha256"]:
            raise ValueError("Continuous image changed")
        size = (row["width"], row["height"])
        geometry = (
            geometry_states[row["frame_index"]]
            if geometry_states is not None
            else reference_geometry(annotations[image_ids[row["source_frame_index"]]], *size)
        )
        detections = detector.detect(image, row["frame_index"])
        for d in detections:
            project_automatic(d, geometry, size)
        detector.classify_on_pitch(
            image, detections, projector=lambda d: project_automatic(d, geometry, size)
        )
        tracker.update(detections, row["frame_index"], size, frame=image)
        for d in detections:
            d.shirt_color_lab = shirt_color(image, d, settings)
        found.append(
            {
                "frame_index": row["frame_index"],
                "geometry_status": geometry["status"],
                "reset": tracker.motion.state["reset_tracks"],
                "detections": [asdict(d) for d in detections],
            }
        )
        if len(found) % 50 == 0:
            print(f"Inference {row['clip']}: {len(found)}/{len(rows)}", flush=True)
    result = {"identity": identity, "frames": found, "elapsed_s": time.perf_counter() - started}
    write_json(target, result)
    return result


def score(
    rows, cached, settings, temporal=False, keeper_rule=None, keeper_evidence=None,
    team_model=None, metric_transform=None,
):
    detections = [[Detection(**d) for d in r["detections"]] for r in cached["frames"]]
    fps = rows[0]["fps"]
    samples = TeamSamples(settings, fps, metric_transform=metric_transform)
    for row, ds in zip(rows, detections):
        for d in ds:
            samples.add(d, row["frame_index"])
    model = samples.fit() if team_model is None else team_model
    assigner, consensus = TeamAssigner(model, fps), TemporalOfficials(fps, model)
    truths, predictions, matches, identity_frames, image_identity_frames = {}, {}, [], [], []
    changes, missing_geometry = 0, 0
    for row, ds, saved in zip(rows, detections, cached["frames"]):
        if saved["reset"]:
            assigner.history.clear()
        assigner.update(ds, row["frame_index"])
        if temporal:
            before = sum(d.semantic_class == "player" for d in ds)
            consensus.update(ds, row["frame_index"], reset=saved["reset"])
            changes += before - sum(d.semantic_class == "player" for d in ds)
        if keeper_rule:
            if keeper_evidence:
                probabilities = keeper_evidence["frames"][row["frame_index"]]["probabilities"]
                for d in ds:
                    position = d.field_position
                    if (
                        d.semantic_class == "player"
                        and position
                        and (position[0] < 0.1 or position[0] > 0.9)
                        and 0.2 < position[1] < 0.8
                        and probabilities.get(d.detection_id, 0) >= 0.9
                    ):
                        d.player_kind = "goalkeeper"
                        d.player_kind_source = "experimental_neural_and_goal_position"
            keeper_rule.update(ds, row["frame_index"], reset=saved["reset"])
        reference = [p for p in row["people"] if p["role"] == "player" and p["on_pitch"]]
        fid = row["frame_id"]
        truths[fid] = [{"class_id": 0, "bbox_xyxy": p["bbox"]} for p in reference]
        candidates = [d for d in ds if d.semantic_class == "player" and d.projection_status == "valid"]
        predictions[fid] = [
            {"class_id": 0, "bbox_xyxy": d.bbox_xyxy, "confidence": d.confidence} for d in candidates
        ]
        used = set()
        for d in sorted((d for d in candidates if d.confidence >= 0.25), key=lambda d: -d.confidence):
            overlap, j = max(
                ((iou(d.bbox_xyxy, p["bbox"]), j) for j, p in enumerate(reference) if j not in used),
                default=(0, -1),
            )
            if overlap >= 0.5:
                used.add(j)
                matches.append((d, reference[j]))
        identity_frames.append(
            (
                [
                    {"track_id": p["track_id"], "bbox": p["bbox"]}
                    for p in reference
                    if p["track_id"] is not None
                ],
                [{"track_id": d.track_id, "bbox": d.bbox_xyxy} for d in candidates if d.track_id is not None],
            )
        )
        image_identity_frames.append(
            (
                identity_frames[-1][0],
                [
                    {"track_id": d.track_id, "bbox": d.bbox_xyxy}
                    for d in ds
                    if d.semantic_class == "player" and d.track_id is not None
                ],
            )
        )
        missing_geometry += saved["geometry_status"] != "valid"
    labelled = [(d, p) for d, p in matches if p.get("team") in {"left", "right"}]
    direct = sum(d.team_id == ("A" if p["team"] == "left" else "B") for d, p in labelled)
    swapped = sum(d.team_id == ("B" if p["team"] == "left" else "A") for d, p in labelled)
    swap = swapped > direct
    assigned = sum(d.team_id is not None for d, _ in labelled)
    correct = max(direct, swapped)
    keeper_correct = keeper_wrong = 0
    for d, p in labelled:
        expected = ("B" if p["team"] == "left" else "A") if swap else ("A" if p["team"] == "left" else "B")
        if p.get("goalkeeper") and d.team_id is not None:
            keeper_correct += d.team_id == expected
            keeper_wrong += d.team_id != expected
    metrics = evaluate(truths, predictions, ["player"], confidence=0.25)
    metrics.pop("errors")
    total = sum(len(t) for t in truths.values())
    return {
        "clip": rows[0]["clip"],
        "game_id": rows[0]["game_id"],
        "split": rows[0]["split"],
        "frames": len(rows),
        "missing_reference_geometry": missing_geometry,
        "players": metrics,
        "teams": {
            "correct": correct,
            "wrong": assigned - correct,
            "assigned": assigned,
            "matched": len(labelled),
            "total": total,
            "correct_fraction_all_players": correct / max(1, total),
            "goalkeepers_correct": keeper_correct,
            "goalkeepers_wrong": keeper_wrong,
            "single_fixed_swap": swap,
        },
        "tracking": identity_metrics(identity_frames),
        "image_tracking": identity_metrics(image_identity_frames),
        "temporal_rejections": changes,
    }


def summarize(rows):
    result = {}
    for split in ("train", "val"):
        selected = [r for r in rows if r["split"] == split]
        tp = sum(r["players"]["per_class"][0]["TP"] for r in selected)
        fp = sum(r["players"]["per_class"][0]["FP"] for r in selected)
        fn = sum(r["players"]["per_class"][0]["FN"] for r in selected)
        idtp, idfp, idfn = (sum(r["tracking"][k] for r in selected) for k in ("IDTP", "IDFP", "IDFN"))
        result[split] = {
            "precision": tp / max(1, tp + fp),
            "recall": tp / max(1, tp + fn),
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "correct_team_fraction": sum(r["teams"]["correct"] for r in selected) / max(1, tp + fn),
            "IDF1": 2 * idtp / max(1, 2 * idtp + idfp + idfn),
            "ID_switches": sum(r["tracking"]["ID_switches"] for r in selected),
            "temporal_rejections": sum(r["temporal_rejections"] for r in selected),
        }
        itp, ifp, ifn = (sum(r["image_tracking"][k] for r in selected) for k in ("IDTP", "IDFP", "IDFN"))
        result[split]["image_IDF1"] = 2 * itp / max(1, 2 * itp + ifp + ifn)
        result[split]["image_ID_switches"] = sum(r["image_tracking"]["ID_switches"] for r in selected)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--score-only", action="store_true")
    parser.add_argument("--score-output", type=Path)
    parser.add_argument("--keeper-evidence", type=Path)
    parser.add_argument("--geometry", choices=("provider", "automatic"), default="provider")
    parser.add_argument("--profile", type=Path, default=ROOT / "configs/models-broadcast.json")
    parser.add_argument(
        "--field-root", type=Path, default=ROOT / "artifacts/broadcast-reliability-day2/field-native-v1"
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    dataset = read_json(ROOT / "data/broadcast-temporal-v1/manifest.json")
    models = load_model_manifest(args.profile)
    settings = load_team_settings(ROOT / "configs/teams-broadcast.json")
    grouped = defaultdict(list)
    for row in dataset["frames"]:
        grouped[row["clip"]].append(row)
    all_scores = {name: [] for name in ("baseline", "temporal", "keepers", "combined")}
    inputs = {
        "dataset_fingerprint": dataset["fingerprint"],
        "models": models,
        "settings": settings,
        "independent_final_test": False,
        "human_review_completed": False,
        "geometry": (
            "provider correspondences; not automatic calibration accuracy"
            if args.geometry == "provider"
            else "automatic calibration; provider labels used for scoring only"
        ),
    }
    if args.score_only:
        if read_json(args.output / "inputs.json") != inputs:
            raise ValueError("Scoring requires the exact inference inputs")
    else:
        write_json(args.output / "inputs.json", inputs)
    score_output = args.score_output or args.output
    score_output.mkdir(parents=True, exist_ok=True)
    for clip, rows in grouped.items():
        geometry_states = None
        if args.geometry == "automatic":
            field_directory = args.field_root / clip
            field_metrics = read_json(field_directory / "projection-metrics.json")
            if field_metrics["dataset_manifest_sha256"] != sha256_file(
                ROOT / "data/broadcast-temporal-v1/manifest.json"
            ):
                raise ValueError("Automatic field states use different source frames")
            geometry_states = read_json(field_directory / "states.json")["frames"]
            if len(geometry_states) != len(rows):
                raise ValueError("Automatic calibration frame count differs")
        cached = (
            read_json(args.output / f"{clip}.json")
            if args.score_only
            else infer_clip(rows, models, settings, args.output, geometry_states=geometry_states)
        )
        if [r["frame_index"] for r in cached["frames"]] != [r["frame_index"] for r in rows]:
            raise ValueError("Cached frames differ from the frozen sequence")
        keeper_evidence = read_json(args.keeper_evidence / f"{clip}.json") if args.keeper_evidence else None
        if keeper_evidence and (
            keeper_evidence["identity"]["detections_sha256"] != sha256_file(args.output / f"{clip}.json")
            or keeper_evidence["identity"]["dataset_fingerprint"] != dataset["fingerprint"]
        ):
            raise ValueError("Keeper evidence does not match inference")
        for name in all_scores:
            result = score(
                rows,
                copy.deepcopy(cached),
                settings,
                temporal=name in {"temporal", "combined"},
                keeper_rule=KeeperTeamConsensus(rows[0]["fps"]) if name in {"keepers", "combined"} else None,
                keeper_evidence=keeper_evidence,
            )
            all_scores[name].append(result)
            write_json(
                score_output / f"{name}-metrics.json",
                {"per_clip": all_scores[name], "summary": summarize(all_scores[name])},
            )
        print(f"Scored {clip}", flush=True)
    write_json(score_output / "complete.json", {"status": "complete", "dataset": dataset["fingerprint"]})


if __name__ == "__main__":
    main()
