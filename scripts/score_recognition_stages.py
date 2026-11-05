"""Score cached retained players with and without the field filter on the raw-detector sample."""

import argparse
from collections import defaultdict
from pathlib import Path

from football_pipeline.contracts import read_json, sha256_file, write_json
from persoon1.metrics import evaluate


def score_stages(datasets, inference_dirs, raw, output):
    """Vergelijk detectie, rolfilter en veldfilter op dezelfde opgeslagen ruwe spelerwaarnemingen."""
    if len(datasets) != len(inference_dirs):
        raise ValueError("Provide one native inference directory per dataset")
    raw_predictions = read_json(raw / "raw-detections.json")["predictions"]
    grouped, truths, metrics, provenance = defaultdict(list), defaultdict(dict), defaultdict(dict), []
    for dataset, directory in zip(datasets, inference_dirs, strict=True):
        for row in read_json(dataset)["frames"]:
            if row["frame_id"] in raw_predictions:
                grouped[(str(directory), row["clip"])].append(row)
    for (directory, clip), rows in grouped.items():
        path = Path(directory) / f"{clip}.json"
        cached = read_json(path)
        provenance.append({"path": str(path), "sha256": sha256_file(path)})
        by_index = {f["frame_index"]: f for f in cached["frames"]}
        for row in rows:
            fid, split = row["frame_id"], row["split"]
            truths[split][fid] = [
                {"class_id": 0, "bbox_xyxy": p["bbox"]}
                for p in row["people"]
                if p["role"] == "player" and p["on_pitch"]
            ]
            for stage in ("retained_players_without_field_filter", "retained_players_with_field_filter"):
                metrics[split].setdefault(stage, {})[fid] = [
                    {"class_id": 0, "bbox_xyxy": d["bbox_xyxy"], "confidence": d["confidence"]}
                    for d in by_index[row["frame_index"]]["detections"]
                    if d["semantic_class"] == "player"
                    and (
                        stage == "retained_players_without_field_filter" or d["projection_status"] == "valid"
                    )
                ]
    if set().union(*(set(v) for v in truths.values())) != set(raw_predictions):
        raise ValueError("Retained outputs must cover exactly the fresh raw-detector sample")
    results = {}
    for split, stages in metrics.items():
        results[split] = {}
        for name, predictions in stages.items():
            result = evaluate(truths[split], predictions, ["player"])
            result.pop("errors")
            results[split][name] = result
    write_json(
        output,
        {
            "reference": "Same 108 source frames as fresh raw inference; existing provider labels",
            "raw_inference_metrics_sha256": sha256_file(raw / "metrics.json"),
            "cached_inferences": provenance,
            "scoring_source_sha256": sha256_file(__file__),
            "results": results,
            "fresh_detector_inference_for_retained_stages": False,
            "new_tracking_evaluated": False,
            "independent_final_test_completed": False,
        },
    )


def main():
    """Meet waar opgeslagen spelerwaarnemingen door rol- en veldfilters verloren gaan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, action="append", required=True)
    parser.add_argument("--inference", type=Path, action="append", required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    score_stages(args.dataset, args.inference, args.raw, args.output)


if __name__ == "__main__":
    main()
