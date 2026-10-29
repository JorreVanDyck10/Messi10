"""Meet afzonderlijke detectie-, rol- en teamstappen en registreert waar de referentiegeometrie vandaan komt."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np
import torch

from persoon1.metrics import evaluate, iou

from .automatic_calibration import project_automatic
from .contracts import Detection, digest_json, read_json, sha256_file, write_json
from .detection import UltralyticsDetector, load_model_manifest
from .teams import TeamAssigner, TeamSamples, load_team_settings


def reference_geometry(annotations, width, height):
    """Conditional geometry from provider correspondences, not our field network.

    Kept separate from the unchanged automatic-field demonstration. This lets
    player/role errors be measured without attributing field failures to them.
    """
    xy, uv = [], []
    for a in annotations:
        b, p = a.get("bbox_image"), a.get("bbox_pitch")
        if a.get("supercategory") != "object" or not b or not p:
            continue
        x, y = p.get("x_bottom_middle"), p.get("y_bottom_middle")
        if x is None or y is None or not -52.5 <= x <= 52.5 or not -34 <= y <= 34:
            continue
        xy.append([b["x"] + b["w"] / 2, b["y"] + b["h"]])
        uv.append([(x + 52.5) / 105, (y + 34) / 68])
    if len(xy) < 4:
        return {"status": "insufficient_reference_geometry"}
    matrix, mask = cv2.findHomography(np.asarray(xy, float), np.asarray(uv, float), cv2.RANSAC, 0.015)
    if matrix is None or int(mask.sum()) < 4 or not np.isfinite(matrix).all():
        return {"status": "insufficient_reference_geometry"}
    return {"status": "valid", "homography": matrix.tolist(), "reference_correspondences": len(xy)}


def evaluate_profile(dataset, profile, team_settings, output, *, replay=None):
    dataset, output = Path(dataset), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = read_json(dataset / "manifest.json")
    models, settings = load_model_manifest(profile), load_team_settings(team_settings)
    rows = [r for r in manifest["frames"] if r["split"] == "val"]
    replay_frames = None
    replay_identity = None
    if replay:
        replay = Path(replay)
        previous = read_json(replay / "metrics.json")

        def inference_spec(value):
            if isinstance(value, dict):
                return {k: inference_spec(v) for k, v in value.items() if k != "device"}
            return [inference_spec(v) for v in value] if isinstance(value, list) else value

        if previous["dataset_fingerprint"] != manifest["fingerprint"] or inference_spec(
            previous["profile"]
        ) != inference_spec(models):
            raise ValueError("Replay must use the same detector, roles, kit weights, boxes and dataset")
        replay_identity = {
            "metrics_sha256": sha256_file(replay / "metrics.json"),
            "detections_sha256": sha256_file(replay / "detections.json"),
        }
        replay_frames = {
            r["frame_id"]: [Detection(**d) for d in r["detections"]]
            for r in read_json(replay / "detections.json")["frames"]
        }
    identity = digest_json(
        [
            manifest["fingerprint"],
            models,
            settings,
            replay_identity,
            sha256_file(__file__),
            {p.name: sha256_file(p) for p in Path(__file__).parent.glob("*.py")},
        ]
    )
    if (output / "metrics.json").exists():
        saved = read_json(output / "metrics.json")
        if saved["identity"] != identity:
            raise ValueError("Evaluation inputs changed; use a new output")
        return saved
    torch.set_num_threads(4)
    detector = UltralyticsDetector(models) if replay_frames is None else None
    if replay_frames is not None:
        from .kit_embedding import KitEmbedding

        kit = KitEmbedding(models["kit_embedding"])
    truths, predictions, detections, references, frame_rows = {}, {}, {}, {}, {}
    geometry_missing, raw_counts, final_counts, transitions = 0, Counter(), Counter(), Counter()
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["clip"]].append(row)
    for clip, clip_rows in grouped.items():
        if detector:
            detector.set_video_identity(clip)
        annotations = json.loads(
            gzip.decompress((dataset / "provider-labels" / (clip + ".json.gz")).read_bytes())
        )
        by_image = defaultdict(list)
        for a in annotations["annotations"]:
            by_image[str(a["image_id"])].append(a)
        image_ids = {Path(im["file_name"]).stem: str(im["image_id"]) for im in annotations["images"]}
        for row in clip_rows:
            frame = cv2.imread(row["image"])
            if frame is None or sha256_file(row["image"]) != row["image_sha256"]:
                raise ValueError("Evaluation image changed")
            fid = row["frame_id"]
            reference = reference_geometry(
                by_image[image_ids[fid.rsplit("_", 1)[1]]], row["width"], row["height"]
            )
            # A missing reference is reported and never becomes an empty ground truth.
            if reference["status"] != "valid":
                geometry_missing += 1
                continue
            found = detector.detect(frame, row["frame_index"]) if detector else replay_frames[fid]
            raw_counts.update(d.semantic_class for d in found)
            for d in found:
                project_automatic(d, reference, (row["width"], row["height"]))
            if detector and models.get("analysis_scope") == "on_pitch_players":
                if models.get("person_box_fusion_weight"):
                    detector.classify_on_pitch(
                        frame,
                        found,
                        projector=lambda d: project_automatic(d, reference, (row["width"], row["height"])),
                    )
                else:
                    detector.classify_on_pitch(frame, found)
            elif not detector:
                kit.update(frame, found)
            from .teams import shirt_color

            for d in found:
                d.shirt_color_lab = shirt_color(frame, d, settings)
            eligible = [d for d in found if d.projection_status == "valid" and d.confidence >= 0.25]
            final_counts.update(d.semantic_class for d in eligible)
            transitions.update(
                (d.detector_semantic_class or d.semantic_class) + " -> " + d.semantic_class for d in eligible
            )
            detections[fid], frame_rows[fid] = found, row
            references[fid] = [p for p in row["people"] if p["on_pitch"] and p["role"] == "player"]
            truths[fid] = [{"class_id": 0, "bbox_xyxy": p["bbox"]} for p in references[fid]]
            predictions[fid] = [
                {"class_id": 0, "bbox_xyxy": d.bbox_xyxy, "confidence": d.confidence}
                for d in found
                if d.semantic_class == "player" and d.projection_status == "valid"
            ]
        print(f"Evaluated {clip}: {len(detections)}/{len(rows)} frames", flush=True)
    if not truths:
        raise ValueError("No evaluable reference geometry")
    team_total = team_correct = team_wrong = team_unknown = missed = false_positive = keepers = keeper_hit = 0
    per_clip, all_serialized = [], []
    for clip, clip_rows in grouped.items():
        samples = TeamSamples(settings, 25)
        for r in clip_rows:
            for d in detections.get(r["frame_id"], []):
                samples.add(d, r["frame_index"])
        model = samples.fit()
        assigner = TeamAssigner(model, 25)
        matches, unmatched = [], 0
        for row in clip_rows:
            fid = row["frame_id"]
            if fid not in detections:
                continue
            found = detections[fid]
            assigner.update(found, row["frame_index"])
            # Team context may refine a proposal's role. Measure the final output,
            # including those recoveries/rejections, against the same truth.
            predictions[fid] = [
                {"class_id": 0, "bbox_xyxy": d.bbox_xyxy, "confidence": d.confidence}
                for d in found
                if d.semantic_class == "player" and d.projection_status == "valid"
            ]
            candidates = sorted(
                [
                    d
                    for d in found
                    if d.semantic_class == "player"
                    and d.projection_status == "valid"
                    and d.confidence >= 0.25
                ],
                key=lambda d: -d.confidence,
            )
            used = set()
            for d in candidates:
                overlap, index = max(
                    (
                        (iou(d.bbox_xyxy, p["bbox"]), j)
                        for j, p in enumerate(references[fid])
                        if j not in used
                    ),
                    default=(0.0, -1),
                )
                if overlap >= 0.5:
                    used.add(index)
                    matches.append((d, references[fid][index]))
                else:
                    false_positive += 1
            missed += len(references[fid]) - len(used)
            unmatched += len(references[fid]) - len(used)
            all_serialized.append(
                {
                    "frame_id": fid,
                    "clip": clip,
                    "frame_index": row["frame_index"],
                    "detections": [asdict(d) for d in found],
                }
            )
        labelled = [(d, p) for d, p in matches if p.get("team") in {"left", "right"}]
        direct = sum(d.team_id == ("A" if p["team"] == "left" else "B") for d, p in labelled)
        swapped = sum(d.team_id == ("B" if p["team"] == "left" else "A") for d, p in labelled)
        assigned = sum(d.team_id is not None for d, _ in labelled)
        correct = max(direct, swapped)
        team_total += len(labelled)
        team_correct += correct
        team_wrong += assigned - correct
        team_unknown += len(labelled) - assigned
        keepers += sum(p.get("goalkeeper", False) for _, p in labelled)
        keeper_hit += sum(
            p.get("goalkeeper", False)
            and d.team_id
            == (
                ("B" if p["team"] == "left" else "A")
                if swapped > direct
                else ("A" if p["team"] == "left" else "B")
            )
            for d, p in labelled
        )
        per_clip.append(
            {
                "clip": clip,
                "team_status": model["status"],
                "matched": len(labelled),
                "correct": correct,
                "wrong": assigned - correct,
                "unknown": len(labelled) - assigned,
                "missed_players": unmatched,
                "single_fixed_swap": swapped > direct,
            }
        )
    write_json(output / "detections.json", {"frames": all_serialized})
    metrics = evaluate(truths, predictions, ["player"])
    errors = metrics.pop("errors")
    write_json(output / "player-errors.json", {"errors": errors})
    player = metrics["per_class"][0]
    result = {
        "identity": identity,
        "frames": len(truths),
        "reference_geometry_unavailable": geometry_missing,
        "dataset_fingerprint": manifest["fingerprint"],
        "profile": models,
        "player_detection_and_roles": metrics,
        "teams": {
            "matched_players": team_total,
            "correct": team_correct,
            "wrong": team_wrong,
            "unknown": team_unknown,
            "missed_players": missed,
            "false_positive_players": false_positive,
            "accuracy_assigned": team_correct / max(1, team_correct + team_wrong),
            "coverage_matched": (team_correct + team_wrong) / max(1, team_total),
            "correct_fraction_all_players": team_correct / max(1, team_total + missed),
            "goalkeepers_total": sum(p.get("goalkeeper", False) for v in references.values() for p in v),
            "goalkeepers_matched": keepers,
            "goalkeepers_correct_team": keeper_hit,
            "per_clip": per_clip,
        },
        "raw_roles": dict(raw_counts),
        "final_roles": dict(final_counts),
        "transitions": dict(transitions),
        "test_accessed": False,
        "independent_final_test": False,
        "inference_replay": replay_identity,
        "geometry_kind": "conditional provider object correspondences; not automatic-field accuracy",
    }
    result["targets_met"] = (
        player["precision"] >= 0.95
        and player["recall"] >= 0.9
        and result["teams"]["accuracy_assigned"] >= 0.95
        and result["teams"]["coverage_matched"] >= 0.9
    )
    write_json(output / "metrics.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--teams", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args()
    report = evaluate_profile(args.dataset, args.profile, args.teams, args.output, replay=args.replay)
    print(
        {
            "frames": report["frames"],
            "targets_met": report["targets_met"],
            "players": report["player_detection_and_roles"]["per_class"][0],
            "team_accuracy": report["teams"]["accuracy_assigned"],
        }
    )
