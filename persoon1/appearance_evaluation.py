"""Evaluate the actual two-stage detector, keeping photo crops distinct from detection AP."""

import copy
import json
import time
from collections import Counter
from pathlib import Path

import cv2

from football_pipeline.contracts import FrameRecord, sha256_file
from football_pipeline.detection import UltralyticsDetector, load_model_manifest
from football_pipeline.render import render_frame

from .metrics import evaluate, iou
from .modeling import yolo
from .role_training import DATA, ROOT, save


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    # Set the repo-local Ultralytics settings before the pipeline imports its detector.
    yolo(ROOT / "models/yolo11n.pt")
    config = load_model_manifest(ROOT / "configs/models-players.json")
    detector = UltralyticsDetector(config)
    old = copy.deepcopy(config)
    old.pop("appearance")
    old["models"] = old["models"][:1]
    baseline = UltralyticsDetector(old)
    frames = {
        r["frame_id"]: r
        for r in json.loads((ROOT / "datasets/teamtrack-players-v2/manifest.json").read_text())["frames"]
    }
    data = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    rows = [r for r in data["samples"] if r["split"] == "val" and r["image"].startswith("../")]
    grouped = {}
    for row in rows:
        grouped.setdefault(row["image"], []).append(row)
    names = ["player", "referee", "assistant_referee"]
    gt, predictions, old_predictions, merged_gt, merged_new = {}, {}, {}, {}, {}
    team_matches = []
    records = []
    started = time.perf_counter()
    for index, (image, objects) in enumerate(grouped.items()):
        frame = cv2.imread(str(DATA / image))
        detector.set_video_identity(objects[0]["video_sha256"])
        key = Path(image).stem
        source = frames[key]
        new = detector.detect(frame, source["frame_index"])
        prior = baseline.detect(frame, source["frame_index"])
        gt[key] = [{"class_id": names.index(r["role"]), "bbox_xyxy": r["bbox"]} for r in objects]
        merged_gt[key] = [{**r, "class_id": min(1, r["class_id"])} for r in gt[key]]
        predictions[key] = [
            {"class_id": names.index(d.semantic_class), "bbox_xyxy": d.bbox_xyxy, "confidence": d.confidence}
            for d in new
            if d.semantic_class in names
        ]
        merged_new[key] = [{**r, "class_id": min(1, r["class_id"])} for r in predictions[key]]
        old_predictions[key] = [
            {
                "class_id": 0 if d.semantic_class == "player" else 1,
                "bbox_xyxy": d.bbox_xyxy,
                "confidence": d.confidence,
            }
            for d in prior
        ]
        record = FrameRecord(
            source["frame_index"],
            source["timestamp_s"],
            (frame.shape[1], frame.shape[0]),
            new,
            {"status": "calibration_unavailable", "points": []},
        )
        records.append({"source_frame_id": key, "video_sha256": source["video_id"], **record.to_dict()})
        used = set()
        for d in sorted(new, key=lambda d: -d.confidence):
            if d.semantic_class != "player" or d.confidence < 0.25:
                continue
            options = [
                (iou(d.bbox_xyxy, r["bbox"]), j, r)
                for j, r in enumerate(objects)
                if r["role"] == "player" and j not in used
            ]
            overlap, j, r = max(options, key=lambda t: t[0], default=(0, -1, None))
            if overlap >= 0.5:
                used.add(j)
                team_matches.append(
                    {
                        "source_frame_id": key,
                        "id": r["id"],
                        "truth": r["team"],
                        "prediction": d.team_id,
                        "correct": r["team"] == d.team_id,
                        "confidence": d.team_confidence,
                    }
                )
        if index in (0, 6):
            cv2.imwrite(str(output / f"video-roles-teams-{index}.jpg"), render_frame(frame, record))
    new_metrics = evaluate(merged_gt, merged_new, ["player", "official"])
    old_metrics = evaluate(merged_gt, old_predictions, ["player", "official"])
    subtype = evaluate(gt, predictions, names)
    for name, value in [
        ("baseline-detection", old_metrics),
        ("new-detection", new_metrics),
        ("official-subtypes", subtype),
    ]:
        save(output / (name + ".json"), value)
    (output / "detections.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    save(
        output / "matched-player-teams.json",
        {
            "scope": "Team accuracy conditional on matched player detections at proposal confidence .25 and box IoU .50",
            "matched_players": len(team_matches),
            "correct": sum(r["correct"] for r in team_matches),
            "unknown": sum(r["prediction"] is None for r in team_matches),
            "records": team_matches,
        },
    )
    # Source photos have selected person crops, not exhaustive box GT: evaluate proposal coverage only.
    photos = [r for r in data["samples"] if r["split"] == "val" and r["image"].startswith("sources/")]
    photo_groups = {}
    for r in photos:
        photo_groups.setdefault(r["image"], []).append(r)
    coverage = []
    for index, (image, objects) in enumerate(photo_groups.items()):
        frame = cv2.imread(str(DATA / image))
        detector.set_video_identity(sha256_file(DATA / image))
        detections = detector.detect(frame, index)
        for r in objects:
            matches = [(iou(d.bbox_xyxy, r["bbox"]), d) for d in detections if d.confidence >= 0.25]
            overlap, d = max(matches, key=lambda t: t[0], default=(0, None))
            coverage.append(
                {
                    "id": r["id"],
                    "truth": r["role"],
                    "proposal_iou": overlap,
                    "proposal_found": overlap >= 0.5,
                    "predicted_role": d.semantic_class if overlap >= 0.5 else None,
                    "role_correct": overlap >= 0.5 and d.semantic_class == r["role"],
                }
            )
        record = FrameRecord(
            index,
            0,
            (frame.shape[1], frame.shape[0]),
            detections,
            {"status": "calibration_unavailable", "points": []},
        )
        cv2.imwrite(str(output / (Path(image).stem + "-predictions.jpg")), render_frame(frame, record))
    save(
        output / "photo-proposal-coverage.json",
        {
            "scope": "Selected annotated people only; unlabelled predictions are not scored as FP. Not mAP.",
            "records": coverage,
        },
    )
    save(
        output / "run.json",
        {
            "models": config,
            "runtime_s": time.perf_counter() - started,
            "video_frames": len(grouped),
            "val_photo_sources": len(photo_groups),
            "test_frames": 0,
            "AP_inference_confidence_floor": 0.1,
            "workpoint_proposal_confidence": 0.25,
            "role_confidence": 0.65,
            "human_review_completed": False,
            "role_counts": dict(Counter(d["semantic_class"] for r in records for d in r["detections"])),
        },
    )
    print(
        "old",
        [(c["name"], c["AP50"], c["AP50_95"], c["TP"], c["FP"], c["FN"]) for c in old_metrics["per_class"]],
    )
    print(
        "new",
        [(c["name"], c["AP50"], c["AP50_95"], c["TP"], c["FP"], c["FN"]) for c in new_metrics["per_class"]],
    )
    print("matched team", len(team_matches), sum(r["correct"] for r in team_matches))
    print(
        "partial crop proposal coverage",
        {
            role: {
                "crops": sum(r["truth"] == role for r in coverage),
                "proposal_found": sum(r["truth"] == role and r["proposal_found"] for r in coverage),
                "role_correct": sum(r["truth"] == role and r["role_correct"] for r in coverage),
            }
            for role in sorted({r["truth"] for r in coverage})
        },
    )


if __name__ == "__main__":
    run("reports/appearance-experiments/EXP-R004/end-to-end")
