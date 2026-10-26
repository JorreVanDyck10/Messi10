"""Pool full-frame references correctly and separate in-play recall from all-ball AP."""

from __future__ import annotations

import argparse
from pathlib import Path

from football_pipeline.ball_tiles import merge_ball_predictions
from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.video import ROOT
from persoon1.metrics import evaluate, iou


def summarize(source, output):
    if output.exists():
        raise ValueError("Use a fresh summary directory")
    output.mkdir(parents=True)
    plan = read_json(source / "plan.json")
    summaries = []
    for model in plan["weights"]:
        for mode in [*plan["modes"], "multiscale"]:
            truth, predictions, identities, in_play = {}, {}, {}, []
            for dataset in plan["datasets"]:
                file_mode = "tiles1280" if mode == "multiscale" else mode
                first = read_json(source / f"{model}-{file_mode}-{dataset}.json")
                truth.update(first["truth"])
                identities.update(first["identities"])
                if mode == "multiscale":
                    second = read_json(source / f"{model}-tiles640x2-{dataset}.json")
                    predictions.update(
                        {
                            key: merge_ball_predictions(boxes + second["predictions"][key])
                            for key, boxes in first["predictions"].items()
                        }
                    )
                else:
                    predictions.update(first["predictions"])
                annotations = read_json(ROOT / "assets/annotations" / dataset / "source-annotations.json")
                for f in annotations["frames"]:
                    if f["frame_id"] not in first["predictions"]:
                        continue
                    for obj in f["objects"]:
                        if obj["kind"] != "in_play_ball":
                            continue
                        boxes = predictions[f["frame_id"]]
                        hit = any(
                            b["confidence"] >= 0.25 and iou(b["bbox_xyxy"], obj["xyxy"]) >= 0.5 for b in boxes
                        )
                        in_play.append({"frame_id": f["frame_id"], "bbox_xyxy": obj["xyxy"], "matched": hit})
            metrics = evaluate(truth, predictions, ["ball"], confidence=0.25)
            row = {
                "model": model,
                "mode": mode,
                "frames": len(truth),
                **metrics["per_class"][0],
                "in_play_visible_references": len(in_play),
                "in_play_matched": sum(r["matched"] for r in in_play),
            }
            summaries.append(row)
            write_json(
                output / f"{model}-{mode}.json",
                {
                    "summary": row,
                    "metrics": metrics,
                    "predictions": predictions,
                    "truth": truth,
                    "identities": identities,
                    "in_play_references": in_play,
                    "selection_scope": "Development comparison. Multiscale is a post-hoc fusion motivated by the single-scale results; no independent-test claim.",
                },
            )
    write_json(
        output / "summary.json",
        {
            "input_plan_sha256": sha256_file(source / "plan.json"),
            "rows": summaries,
            "all_ball_target_includes_reserves": True,
            "in_play_measure": "Recall of visible annotated in-play balls at confidence .25 and IoU .50; reserve detections are not scored as FP for this recall.",
            "human_review_completed": False,
            "independent_final_test": False,
        },
    )
    for row in summaries:
        print(row, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summarize(args.source, args.output)
