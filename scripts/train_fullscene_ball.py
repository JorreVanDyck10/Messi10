"""Train a ball specialist on native tiles from the delivered fullscene60 source."""

from __future__ import annotations

import argparse
import contextlib
import gc
import logging
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import cv2
import torch
import yaml

from football_pipeline.ball_tiles import tile_windows
from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.pipeline import code_identity, dependencies
from football_pipeline.video import ROOT
from persoon1.modeling import yolo


def tile_ball_labels(objects, window):
    """Exclude tiles cutting through labelled balls or unresolved source regions."""
    x, y, right, bottom = window
    labels = []
    for obj in objects:
        if obj["class_id"] != 1:
            continue
        a, b, c, d = obj["xyxy"]
        intersects = min(c, right) > max(a, x) and min(d, bottom) > max(b, y)
        if not intersects:
            continue
        if a < x or b < y or c > right or d > bottom:
            return None
        width, height = right - x, bottom - y
        labels.append(
            [32, ((a + c) / 2 - x) / width, ((b + d) / 2 - y) / height, (c - a) / width, (d - b) / height]
        )
    return labels


def build_dataset(source, output, names):
    """Maak de native tegels en terugvertaalde ballabels uit de volledige-scèneset en bewaar
    bronvensters, splits en beeldidentiteiten.
    """
    if output.exists():
        raise ValueError("Choose a new derived dataset directory")
    spec = read_json(source / "source-annotations.json")
    manifest = read_json(source / "manifest.json")
    if manifest["names"][1] != "ball" or names.get(32) != "sports ball":
        raise ValueError("Invalid semantic class mapping")
    groups = {}
    for f in manifest["frames"]:
        if f["split"] not in {"train", "val"}:
            raise ValueError("Reserved test frames cannot be used")
        if groups.setdefault(f["group_id"], f["split"]) != f["split"]:
            raise ValueError("Source group crosses train/val")
    output.mkdir(parents=True)
    rows, skipped, source_hashes, seen_hashes = [], [], {}, {}
    by_id = {f["frame_id"]: f for f in spec["frames"]}
    for f in manifest["frames"]:
        path = source / f["image"]
        digest = sha256_file(path)
        if digest != f["image_sha256"]:
            raise ValueError("Source image checksum mismatch")
        if seen_hashes.setdefault(digest, f["split"]) != f["split"]:
            raise ValueError("Copied source image crosses split")
        source_hashes[f["image"]] = digest
        pixels = cv2.imread(str(path))
        if pixels is None or pixels.shape[:2] != (f["height"], f["width"]):
            raise ValueError("Source dimensions mismatch")
        objects = by_id[f["frame_id"]]["objects"]
        for index, window in enumerate(tile_windows(f["width"], f["height"], 1280)):
            x, y, right, bottom = window
            labels = tile_ball_labels(objects, window)
            regions = f.get("unresolved_regions", [])
            uncertain = any(
                min(r["xyxy"][2], right) > max(r["xyxy"][0], x)
                and min(r["xyxy"][3], bottom) > max(r["xyxy"][1], y)
                for r in regions
            )
            if labels is None or uncertain:
                skipped.append(
                    {
                        "frame": f["frame_id"],
                        "tile": window,
                        "reason": "partial ball or unresolved source region",
                    }
                )
                continue
            stem = f"{f['frame_id']}-tile{index}"
            image = output / "images" / f["split"] / (stem + ".png")
            label = output / "labels" / f["split"] / (stem + ".txt")
            image.parent.mkdir(parents=True, exist_ok=True)
            label.parent.mkdir(parents=True, exist_ok=True)
            assert cv2.imwrite(str(image), pixels[y:bottom, x:right], [cv2.IMWRITE_PNG_COMPRESSION, 3])
            label.write_text("".join(" ".join(map(str, row)) + "\n" for row in labels), encoding="utf-8")
            rows.append(
                {
                    "image": image.relative_to(output).as_posix(),
                    "label": label.relative_to(output).as_posix(),
                    "split": f["split"],
                    "group": f["group_id"],
                    "frame_id": f["frame_id"],
                    "window_xyxy": window,
                    "balls": len(labels),
                    "image_sha256": sha256_file(image),
                    "label_sha256": sha256_file(label),
                }
            )
    (output / "data.yaml").write_text(
        yaml.safe_dump(
            {
                "path": output.as_posix(),
                "train": "images/train",
                "val": "images/val",
                "names": names,
            }
        ),
        encoding="utf-8",
    )
    record = {
        "source_dataset": manifest["dataset_version"],
        "manifest_sha256": sha256_file(source / "manifest.json"),
        "annotations_sha256": sha256_file(source / "source-annotations.json"),
        "source_hashes": source_hashes,
        "rows": rows,
        "skipped": skipped,
        "counts": dict(Counter(r["split"] for r in rows)),
        "negative_tiles": dict(Counter(r["split"] for r in rows if r["balls"] == 0)),
        "mapping": {"source_ball_1": "COCO sports ball 32"},
        "human_review_completed": False,
        "target": "All labelled visible footballs including reserves; other COCO classes intentionally unsupervised",
        "scope": "Derived tiles share source groups; overlapping tiles are not independent images.",
    }
    write_json(output / "source.json", record)
    return record


def main():
    """Bouw de native baltegelset, voer de ingestelde specialisttraining uit en registreer het echte
    beste checkpoint.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--device", default="0")
    parser.add_argument("--dataset", type=Path, help="Existing audited tile dataset with data.yaml")
    parser.add_argument("--weights", type=Path)
    parser.add_argument("--max-minutes", type=float)
    args = parser.parse_args()
    if args.dataset:
        from football_pipeline.training_budget import train_yolo

        train_yolo(
            args.weights or ROOT / "artifacts/fullscene-ball-v1/fullscene_ball_f005.pt",
            args.dataset,
            args.run.resolve(),
            read_json(args.config),
            args.max_minutes if args.max_minutes is not None else 60,
        )
        return
    if args.max_minutes is not None:
        parser.error("--max-minutes requires an audited --dataset")
    run = args.run.resolve()
    if run.exists():
        raise ValueError("Choose a new training directory")
    run.mkdir(parents=True)
    source = ROOT / "assets/annotations/football-fullscene60"
    config = read_json(args.config)
    weights = args.weights or ROOT / "artifacts/appearance-v1/person_proposals.pt"
    initial = yolo(weights)
    write_json(
        run / "preregistration.json",
        {
            "recorded_before_dataset_and_training": datetime.now(UTC).isoformat(),
            "hypothesis": "Native full-scene tiles add unmasked small balls and real negative background context.",
            "initial_weights_sha256": sha256_file(weights),
            "config": config,
            "script_sha256": sha256_file(__file__),
            "code": code_identity(),
            "software": dependencies(),
            "gpu": torch.cuda.get_device_name(0),
            "gpu_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
            "source_manifest_sha256": sha256_file(source / "manifest.json"),
            "selection": "Checkpoint by tile-validation framework AP fitness; final candidate compared on the same original full frames and inference modes as frozen baselines.",
            "guard": "No person/role model replacement, no new team identities, no end-test claim or label-review approval.",
        },
    )
    dataset = build_dataset(source, run / "dataset", initial.names)
    write_json(run / "dataset-identity.json", dataset)
    del initial
    attempts = []
    for batch in [config["batch"], 1]:
        if any(a["batch"] == batch for a in attempts):
            continue
        model = yolo(weights)
        try:
            used = {
                **config,
                "batch": batch,
                "data": str(run / "dataset/data.yaml"),
                "device": args.device,
                "workers": 0,
                "project": str(run),
                "name": f"batch-{batch}",
                "exist_ok": False,
            }
            write_json(run / f"requested-batch-{batch}.json", used)
            with (run / f"train-batch-{batch}.log").open("w", encoding="utf-8") as log:
                from ultralytics.utils import LOGGER

                handler = logging.StreamHandler(log)
                LOGGER.addHandler(handler)
                try:
                    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                        model.train(**used)
                finally:
                    LOGGER.removeHandler(handler)
            best = run / f"batch-{batch}/weights/best.pt"
            attempts.append({"batch": batch, "status": "completed", "weights_sha256": sha256_file(best)})
            break
        except torch.cuda.OutOfMemoryError:
            attempts.append({"batch": batch, "status": "out_of_memory"})
        finally:
            del model
            gc.collect()
            torch.cuda.empty_cache()
            write_json(run / "attempts.json", {"attempts": attempts})
    else:
        raise RuntimeError("No successful training batch")
    if sha256_file(source / "manifest.json") != dataset["manifest_sha256"]:
        raise ValueError("Source manifest changed during training")
    print("Training completed:", best, flush=True)


if __name__ == "__main__":
    main()
