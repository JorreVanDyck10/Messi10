"""One controlled comparison: frozen backbone versus all-layer ball fine-tuning."""

from __future__ import annotations

import argparse
import gc
import os
from pathlib import Path

import torch

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from scripts.experiment_broadcast_v2 import measured


def run(output: Path):
    from ultralytics import YOLO, settings

    if output.exists():
        raise ValueError("Use a fresh output directory to preserve earlier experiments.")
    if not torch.cuda.is_available():
        raise ValueError("The bounded experiment requires CUDA.")
    weights = Path("artifacts/broadcast-ball-v2/broadcast_ball_v2.pt").resolve()
    dataset = Path("data/broadcast-training-v2").resolve()
    full_root = Path("data/broadcast-ball-review-v1/curated").resolve()
    crops = read_json(dataset / "balls/manifest.json")
    full = read_json(full_root / "manifest.json")
    for manifest in (crops, full):
        if digest_json({k: v for k, v in manifest.items() if k != "fingerprint"}) != manifest["fingerprint"]:
            raise ValueError("Input dataset identity changed.")
    training = dict(epochs=16, imgsz=640, batch=4, optimizer="Adam", lr0=0.0001,
                    lrf=0.1, cos_lr=True, warmup_epochs=1.0, warmup_bias_lr=0.0,
                    weight_decay=0.0005, patience=8, amp=True, workers=0,
                    seed=42, deterministic=True, cache=False, mosaic=0.0, mixup=0.0,
                    copy_paste=0.0, degrees=0.0, scale=0.0, translate=0.0,
                    fliplr=0.5, flipud=0.0, hsv_h=0.01, hsv_s=0.2, hsv_v=0.15, plots=False)
    protocol = {
        "hypothesis": "Updating all layers improves small-ball transfer compared with freezing the first ten.",
        "single_changed_factor_between_candidates": "freeze: 10 versus 0",
        "initial_weights": str(weights), "initial_weights_sha256": sha256_file(weights),
        "crop_dataset_fingerprint": crops["fingerprint"], "full_dataset_fingerprint": full["fingerprint"],
        "script_sha256": sha256_file(__file__), "training": training,
        "checkpoint_selection": "Ultralytics best checkpoint on the same development crop validation",
        "candidate_selection": "Tiled AP50:95 improves, TP >= baseline, FP <= baseline, no extra negative-crop detections at 0.25",
        "human_review_completed": False, "independent_final_test": False,
        "scope": "Further development on previously used AI-curated validation; not an independent test.",
        "default_models_changed": False,
    }
    output.mkdir(parents=True)
    write_json(output / "protocol.json", protocol)
    (output / "experiment-source.py").write_bytes(Path(__file__).read_bytes())
    settings.update({k: False for k in ("sync", "clearml", "comet", "dvc", "mlflow", "neptune", "wandb") if k in settings})
    crop_rows = [r for r in crops["frames"] if r["split"] == "val"]
    full_rows = [r for r in full["frames"] if r["split"] == "val"]

    def evaluate(path, name):
        return {mode: measured(path, rows, root, output / name / mode, mode=mode)
                for mode, rows, root in (("crops", crop_rows, dataset / "balls"),
                                         ("full", full_rows, full_root), ("tiled", full_rows, full_root))}

    baseline = evaluate(weights, "baseline")
    candidates = {}
    for freeze in (10, 0):
        name = f"freeze-{freeze}"
        print(f"Training {name}, maximum 16 epochs", flush=True)
        model = YOLO(str(weights))
        model.train(data=str(dataset / "ball-coco/data.yaml"), device=0, project=str(output),
                    name=name, exist_ok=False, freeze=freeze, **training)
        del model
        gc.collect()
        torch.cuda.empty_cache()
        best = output / name / "weights/best.pt"
        candidates[name] = {"weights": str(best), "weights_sha256": sha256_file(best),
                            "measurements": evaluate(best, name + "-evaluation")}
        write_json(output / "progress.json", {"baseline": baseline, "candidates": candidates})
    old = baseline["tiled"]["per_class"][0]
    eligible = []
    for name, candidate in candidates.items():
        new = candidate["measurements"]["tiled"]["per_class"][0]
        candidate["eligible"] = (new["AP50_95"] > old["AP50_95"] and new["TP"] >= old["TP"]
                                 and new["FP"] <= old["FP"] and
                                 candidate["measurements"]["crops"]["unmatched_on_negatives"]
                                 <= baseline["crops"]["unmatched_on_negatives"])
        if candidate["eligible"]:
            eligible.append(name)
    selected = max(eligible, key=lambda n: candidates[n]["measurements"]["tiled"]["mAP50_95"]) if eligible else None
    result = {"protocol": protocol, "baseline": baseline, "candidates": candidates,
              "selected_candidate": selected, "default_models_changed": False}
    write_json(output / "comparison.json", result)
    print(f"Completed. Selected optional candidate: {selected}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/broadcast-ball-v3"))
    args = parser.parse_args()
    os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(".cache/ultralytics-broadcast-v3").resolve()))
    os.environ.setdefault("WANDB_MODE", "disabled")
    run(args.output.resolve())
