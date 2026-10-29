"""Combineert aanvullende voetbalbronnen voor fine-tuning en controleert de dataset vóór training."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import torch

from .contracts import read_json, sha256_file, write_json
from .sportsmot_data import ARCHIVE_SHA256, REVISION
from .training_budget import train_yolo
from .video import ROOT

BASE = ROOT / "artifacts/broadcast-refine-v2/detector/batch-2/weights/best.pt"
BASE_SHA256 = "e36cf616da81d07a900a74c90580565f5e8b89e6bffb5668979bf1f9355cf0da"


def validate_dataset(dataset):
    dataset = Path(dataset).resolve()
    manifest = read_json(dataset / "manifest.json")
    selection = manifest["selection"]
    if (
        manifest["names"] != {"0": "player"}
        or manifest["test_accessed"]
        or selection["revision"] != REVISION
        or selection["archive_sha256"] != ARCHIVE_SHA256
        or selection["split"] != "train"
        or selection["test_accessed"]
    ):
        raise ValueError("Mixed training requires the pinned, player-only official training selection")
    original = read_json(ROOT / "data/broadcast-pitch-v1/manifest.json")
    if manifest["source_fingerprints"]["soccernet"] != original["fingerprint"]:
        raise ValueError("Frozen SoccerNet split changed")
    expected_validation = {
        (r["frame_id"], r["image_sha256"]) for r in original["frames"] if r["split"] == "val"
    }
    validation, hashes, games = set(), {}, Counter()
    for row in manifest["frames"]:
        if row["split"] not in {"train", "val"} or row["provider"] not in {"soccernet", "sportsmot"}:
            raise ValueError("Reserved or unknown source in mixed training")
        if row["provider"] == "sportsmot" and (
            row["split"] != "train" or row["clip"] not in selection["sequences"]
        ):
            raise ValueError("SportsMOT validation/test cannot enter training")
        if (
            sha256_file(row["image"]) != row["image_sha256"]
            or sha256_file(row["label"]) != row["label_sha256"]
        ):
            raise ValueError("Mixed training image or target changed")
        if row["image_sha256"] in hashes and hashes[row["image_sha256"]] != row["split"]:
            raise ValueError("Duplicate image crosses the training/validation split")
        hashes[row["image_sha256"]] = row["split"]
        for line in Path(row["label"]).read_text().splitlines():
            if line.strip() and line.split()[0] != "0":
                raise ValueError("Only genuine labelled player targets are supported")
        if row["split"] == "val":
            validation.add((row["frame_id"], row["image_sha256"]))
        else:
            games[row["game_id"]] += 1
    if validation != expected_validation:
        raise ValueError("The original complete validation selection must remain unchanged")
    if not any(str(g).startswith("sportsmot:") for g in games):
        raise ValueError("Additional official football matches are missing")
    return manifest, dict(games)


def train(dataset, output, epochs=40, resolution=1536):
    from ultralytics import YOLO

    dataset, output = Path(dataset).resolve(), Path(output).resolve()
    manifest, games = validate_dataset(dataset)
    if sha256_file(BASE) != BASE_SHA256 or YOLO(str(BASE)).names != {0: "player"}:
        raise ValueError("Warm start must be the verified, supervised player checkpoint")
    output.mkdir(parents=True, exist_ok=False)
    write_json(
        output / "inputs.json",
        {
            "dataset_fingerprint": manifest["fingerprint"],
            "base_sha256": BASE_SHA256,
            "source_fingerprints": manifest["source_fingerprints"],
            "training_games": games,
            "target_names": {0: "player"},
            "test_accessed": False,
            "field_models_changed": False,
            "selection": "Fixed original validation; extra official football training matches only",
            "training_source_sha256": sha256_file(__file__),
        },
    )
    config = {
        "imgsz": resolution,
        "epochs": epochs,
        "patience": 8,
        "batch": 2,
        "workers": 4,
        "optimizer": "AdamW",
        "lr0": 0.00005,
        "lrf": 0.1,
        "cos_lr": True,
        "warmup_epochs": 1.0,
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
    return train_yolo(BASE, dataset, output / "detector", config, minutes=None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/broadcast-multisource-v1")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/broadcast-multisource-v7")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--resolution", type=int, default=1536)
    args = parser.parse_args()
    torch.set_num_threads(4)
    print(train(args.dataset, args.output, args.epochs, args.resolution), flush=True)
