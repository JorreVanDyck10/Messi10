"""Inspecteert of hervat bestaande broadcastwerkstappen zonder voltooide resultaten opnieuw te trainen."""

from __future__ import annotations

import argparse
import csv
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

from .contracts import read_json, sha256_file, write_json
from .sportsmot_data import ARCHIVE_SHA256, REVISION, SOURCE
from .video import ROOT

STAGE = ROOT / "artifacts/broadcast-detector-v4"
CACHE = ROOT / ".cache/sportsmot"
ARCHIVE_BYTES = 6703191552


def status():
    paused = read_json(STAGE / "paused/checkpoint.json")
    part = CACHE / "train.tar.part"
    final = CACHE / "train.tar"
    current = ROOT / "artifacts/broadcast-multisource-v7/detector/status.json"
    return {
        "training": read_json(STAGE / "training/status.json")["status"],
        "completed_checkpoint_epoch": paused["last_completed_epoch"],
        "checkpoint_verified": sha256_file(paused["resume_checkpoint"]) == paused["sha256"],
        "download_bytes": final.stat().st_size
        if final.exists()
        else part.stat().st_size
        if part.exists()
        else 0,
        "download_total_bytes": ARCHIVE_BYTES,
        "archive_complete": final.exists(),
        "multisource_training": read_json(current) if current.exists() else None,
        "handover": str(ROOT / "docs/Broadcast_Hervatten.md"),
    }


def download():
    CACHE.mkdir(parents=True, exist_ok=True)
    final, partial = CACHE / "train.tar", CACHE / "train.tar.part"
    if final.exists():
        if sha256_file(final) != ARCHIVE_SHA256:
            raise ValueError("Existing SportsMOT training archive changed")
        return final
    if partial.exists():
        progress = read_json(CACHE / "progress.json")
        if progress["source_revision"] != REVISION or progress["total_bytes"] != ARCHIVE_BYTES:
            raise ValueError("Partial archive belongs to another source")
    started, last = time.monotonic(), 0
    for attempt in range(8):
        offset = partial.stat().st_size if partial.exists() else 0
        if offset == ARCHIVE_BYTES:
            break
        url = SOURCE + "/resolve/" + REVISION + "/dataset/train.tar?download=true"
        try:
            with requests.get(
                url, headers={"Range": f"bytes={offset}-"} if offset else {}, stream=True, timeout=(30, 120)
            ) as response:
                response.raise_for_status()
                if offset and (
                    response.status_code != 206
                    or not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-")
                ):
                    raise ValueError("Source refused the exact resume range; partial bytes preserved")
                with partial.open("ab" if offset else "wb") as output:
                    for block in response.iter_content(4 * 1024 * 1024):
                        output.write(block)
                        offset += len(block)
                        if offset - last >= 128 * 1024**2:
                            last = offset
                            write_json(
                                CACHE / "progress.json",
                                {
                                    "source_revision": REVISION,
                                    "downloaded_bytes": offset,
                                    "total_bytes": ARCHIVE_BYTES,
                                    "test_accessed": False,
                                },
                            )
                            print(f"SportsMOT train: {offset / ARCHIVE_BYTES:.1%}", flush=True)
            break
        except (requests.RequestException, OSError) as error:
            print("Download retry:", type(error).__name__, flush=True)
            if attempt == 7:
                raise RuntimeError("Training archive download failed; partial bytes preserved") from None
    if partial.stat().st_size != ARCHIVE_BYTES or sha256_file(partial) != ARCHIVE_SHA256:
        raise ValueError("SportsMOT training archive checksum mismatch; bytes preserved")
    partial.replace(final)
    write_json(
        CACHE / "archive.json",
        {
            "source": SOURCE,
            "revision": REVISION,
            "path": "dataset/train.tar",
            "bytes": ARCHIVE_BYTES,
            "sha256": ARCHIVE_SHA256,
            "resumed_runtime_s": time.monotonic() - started,
            "test_accessed": False,
        },
    )
    return final


def training():
    import torch
    from ultralytics import YOLO

    paused = read_json(STAGE / "paused/checkpoint.json")
    record_path = STAGE / "training/status.json"
    record = read_json(record_path)
    if record["status"] not in {"paused_by_user", "interrupted"}:
        raise ValueError("Training is already running or complete; inspect status before resuming")
    path = paused["resume_checkpoint"]
    if sha256_file(path) != paused["sha256"]:
        raise ValueError("Paused optimizer checkpoint changed")
    dataset = read_json(ROOT / "data/broadcast-pitch-v1/manifest.json")
    if dataset["fingerprint"] != paused["dataset_fingerprint"]:
        raise ValueError("Paused training dataset changed")
    if any(r["split"] not in {"train", "val"} for r in dataset["frames"]):
        raise ValueError("Reserved split in resumed training")
    for row in dataset["frames"]:
        if (
            sha256_file(row["image"]) != row["image_sha256"]
            or sha256_file(row["label"]) != row["label_sha256"]
        ):
            raise ValueError("Paused training image or label changed")
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if checkpoint["optimizer"] is None or checkpoint["epoch"] + 1 != paused["last_completed_epoch"]:
        raise ValueError("Paused checkpoint is not resumable at the recorded epoch")
    if Path(checkpoint["train_args"]["data"]).resolve() != ROOT / "data/broadcast-pitch-v1/data.yaml":
        raise ValueError("Native checkpoint refers to another dataset")
    if Path(checkpoint["train_args"]["save_dir"]).resolve() != STAGE / "training/batch-1":
        raise ValueError("Native checkpoint refers to another output")
    del checkpoint
    record.update(status="running", resumed_at=datetime.now(UTC).isoformat(), resume=paused)
    write_json(record_path, record)
    started = time.monotonic()
    previous = record.get("runtime_s", 0)
    model = YOLO(path)

    def progress(trainer):
        write_json(
            STAGE / "training/progress.json",
            {
                "epoch": trainer.epoch + 1,
                "maximum_epochs": paused["maximum_epochs_total"],
                "elapsed_s": previous + time.monotonic() - started,
                "batch_size": trainer.batch_size,
            },
        )

    model.add_callback("on_train_epoch_end", progress)
    try:
        model.train(resume=True, device=0, workers=4)
        best = STAGE / "training/batch-1/weights/best.pt"
        with (STAGE / "training/batch-1/results.csv").open() as stream:
            epochs = len(list(csv.DictReader(stream)))
        record.update(
            status="complete",
            best=str(best),
            best_sha256=sha256_file(best),
            epochs=epochs,
            runtime_s=previous + time.monotonic() - started,
        )
        return best
    except BaseException as error:
        record.update(
            status="interrupted", error=type(error).__name__, runtime_s=previous + time.monotonic() - started
        )
        raise
    finally:
        write_json(record_path, record)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("status", "training", "download", "prepare-data"), default="status", nargs="?"
    )
    args = parser.parse_args()
    if args.action == "status":
        print(status())
    elif args.action == "training":
        print(training())
    elif args.action == "download":
        print(download())
    else:
        from .sportsmot_data import mixed_player_dataset, prepare_football

        print(
            mixed_player_dataset(
                prepare_football(CACHE / "train.tar", ROOT / "data/sportsmot-football-train-v1"),
                ROOT / "data/broadcast-multisource-v1",
            )["counts"]
        )
