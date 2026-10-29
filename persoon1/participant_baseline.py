"""Vergelijkt lokalisatie van geannoteerde deelnemers zonder COCO-personen achteraf spelersrollen te geven."""

import argparse
import json
from pathlib import Path

from .core import (dataset_path, label_pixels, load_manifest, now, read_json,
                   read_labels, require_experiment_data, sha256, write_json)
from .metrics import evaluate
from .modeling import fresh_output, yolo


def compare(manifest, attestation, baseline_weights, candidate_predictions, output, device="0"):
    require_experiment_data(manifest, attestation, True)
    data, root = load_manifest(manifest)
    candidate_predictions = Path(candidate_predictions)
    run = read_json(candidate_predictions / "run.json")
    if run["split"] != "val" or run["manifest_sha256"] != sha256(manifest):
        raise ValueError("Use matching development predictions; no test model selection")
    output = fresh_output(output)
    truth, candidate, baseline = {}, {}, {}
    frames = [f for f in data["frames"] if f["split"] == "val"]
    for frame in frames:
        truth[frame["frame_id"]] = [{"class_id": 0, "bbox_xyxy": label_pixels(b, frame["width"], frame["height"])}
            for b in read_labels(dataset_path(root, frame["label"]), len(data["names"]))]
    for line in (candidate_predictions / "detections.jsonl").read_text().splitlines():
        row = json.loads(line)
        candidate[row["frame_id"]] = [{"class_id": 0, "bbox_xyxy": b["bbox_xyxy"], "confidence": b["confidence"]}
                                      for b in row["detections"]]
    model = yolo(baseline_weights)
    person_ids = [i for i, name in model.names.items() if name == "person"]
    if len(person_ids) != 1:
        raise ValueError("This comparison requires the verified COCO person class")
    with (output / "baseline-predictions.jsonl").open("w", encoding="utf-8") as stream:
        for frame in frames:
            result = model.predict(str(dataset_path(root, frame["image"])), imgsz=run["config"]["imgsz"],
                conf=run["config"]["confidence"], iou=run["config"]["nms_iou"],
                max_det=run["config"]["max_det"], device=device, classes=person_ids, verbose=False)[0]
            boxes = [{"class_id": 0, "bbox_xyxy": list(map(float, b.xyxy[0].tolist())),
                      "confidence": float(b.conf.item())} for b in result.boxes]
            baseline[frame["frame_id"]] = boxes
            stream.write(json.dumps({"frame_id": frame["frame_id"], "source_class_name": "person",
                "purpose": "role-agnostic annotated-participant localization proxy", "detections": boxes}) + "\n")
    reports = {}
    for name, predictions in (("pretrained_person", baseline), ("finetuned_roles_collapsed", candidate)):
        report = evaluate(truth, predictions, ["annotated_participant_without_role"])
        errors = report.pop("errors")
        report.update(recorded_at=now(), subset="val", role_classification_evaluated=False,
            caveat="Only annotated participants are covered. Far-side role coverage is incomplete; unlabelled sidelines may bias this proxy. Not a player/referee classification baseline.",
            human_review_completed=False, manifest_sha256=sha256(manifest),
            weights_sha256=sha256(baseline_weights) if name == "pretrained_person" else run["weights_sha256"],
            inference_config={k: run["config"][k] for k in ("imgsz", "confidence", "nms_iou", "max_det")})
        write_json(output / f"{name}.json", report)
        write_json(output / f"{name}-errors.json", errors)
        reports[name] = {k: report[k] for k in ("mAP50", "mAP50_95")}
    write_json(output / "comparison.json", reports)
    return reports


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "attestation", "baseline-weights", "candidate-predictions", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()
    print(compare(args.manifest, args.attestation, args.baseline_weights, args.candidate_predictions,
                  args.output, args.device))
