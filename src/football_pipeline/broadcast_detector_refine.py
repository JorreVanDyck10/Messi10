"""High-detail supervised player/referee training; field models are never used."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

import torch

from .contracts import read_json, sha256_file, write_json
from .training_budget import train_yolo
from .video import ROOT


def initialize_two_roles(source, output):
    """Transfer COCO appearance and localization, then train two actual roles.

    This initialization is deliberately not an application checkpoint. Its two
    output rows both start from person evidence and require the supervised run.
    """
    from ultralytics import YOLO
    from ultralytics.nn.tasks import DetectionModel

    original = YOLO(str(source))
    if original.names.get(0) != "person":
        raise ValueError("Initialization requires the actual COCO person source class")
    model = DetectionModel(copy.deepcopy(original.model.yaml), ch=3, nc=2, verbose=False)
    model.load(original.model, verbose=False)
    with torch.no_grad():
        for target, old in zip(model.model[-1].cv3, original.model.model[-1].cv3):
            for role in range(2):
                target[-1].weight[role].copy_(old[-1].weight[0])
                target[-1].bias[role].copy_(old[-1].bias[0] - (2 if role == 1 else 0))
    model.names = {0: "player", 1: "referee"}
    path = output / "initialization_only.pt"
    torch.save({"model": model.half(), "train_args": {"task": "detect"}, "optimizer": None}, path)
    write_json(
        output / "initialization.json",
        {
            "source_sha256": sha256_file(source),
            "initialization_sha256": sha256_file(path),
            "source_names": original.names,
            "target_names": model.names,
            "application_use_allowed": False,
            "meaning": "Untrained role rows; supervised training on player/referee labels is mandatory",
        },
    )
    return path


def train(dataset, output, epochs=40, resolution=1920, minutes=None):
    dataset, output = Path(dataset).resolve(), Path(output).resolve()
    manifest = read_json(dataset / "manifest.json")
    if any(r["split"] not in {"train", "val"} for r in manifest["frames"]):
        raise ValueError("Reserved images must not enter detector training")
    for row in manifest["frames"]:
        if (
            sha256_file(row["image"]) != row["image_sha256"]
            or sha256_file(row["label"]) != row["label_sha256"]
        ):
            raise ValueError("Broadcast training bytes changed")
    output.mkdir(parents=True, exist_ok=False)
    source = ROOT / "models/yolo11m.pt"
    if sha256_file(source) != "d5ffc1a674953a08e11a8d21e022781b1b23a19b730afc309290bd9fb5305b95":
        raise ValueError("COCO medium initialization changed")
    initial = initialize_two_roles(source, output)
    write_json(
        output / "inputs.json",
        {
            "dataset_fingerprint": manifest["fingerprint"],
            "source": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11m.pt",
            "source_sha256": sha256_file(source),
            "test_accessed": False,
            "target_names": {0: "player", 1: "referee"},
            "field_models_changed": False,
        },
    )
    config = {
        "imgsz": resolution,
        "epochs": epochs,
        "patience": 8,
        "batch": 1,
        "workers": 4,
        "optimizer": "AdamW",
        "lr0": 0.0003,
        "lrf": 0.1,
        "cos_lr": True,
        "warmup_epochs": 3.0,
        "warmup_bias_lr": 0.0,
        "weight_decay": 0.0005,
        "freeze": 0,
        "amp": True,
        "seed": 42,
        "deterministic": True,
        "rect": True,
        "fliplr": 0.5,
        "flipud": 0.0,
        "degrees": 2.0,
        "translate": 0.05,
        "scale": 0.15,
        "hsv_h": 0.05,
        "hsv_s": 0.5,
        "hsv_v": 0.35,
        "mosaic": 0.0,
        "close_mosaic": 0,
        "mixup": 0.0,
        "plots": True,
        "val": True,
        "save": True,
    }
    return train_yolo(initial, dataset, output / "training", config, minutes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/broadcast-pitch-v1")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/broadcast-detector-v4")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--resolution", type=int, default=1920)
    parser.add_argument("--minutes", type=float)
    args = parser.parse_args()
    torch.set_num_threads(4)
    print(train(args.dataset, args.output, args.epochs, args.resolution, args.minutes), flush=True)
