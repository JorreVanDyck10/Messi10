"""Zet broadcastproviderlabels om naar ontwikkeldata en behoudt rollen, teams en brontracks.


The frozen match split is inherited from course-multimatch-v1. Neither the
official test archive nor the project's reserved TeamTrack frames is accessed.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import threading
import time
import zipfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import yaml

from .contracts import digest_json, read_json, sha256_file, write_json
from .course_dataset import DATASET_URL, REVISION, archive_url, object_labels
from .research_archive import RangeArchive
from .video import ROOT


def labelled_people(annotations, width, height):
    """Join attributes to the *same* provider box; never align by list index."""
    people = []
    for annotation in annotations:
        if annotation.get("supercategory") != "object" or annotation["category_id"] not in {1, 2, 3, 7}:
            continue
        _, boxes = object_labels([annotation], width, height)
        if not boxes:
            continue
        attributes = annotation.get("attributes", {})
        role = {1: "player", 2: "player", 3: "referee", 7: "person"}[annotation["category_id"]]
        position = annotation.get("bbox_pitch") or {}
        x, y = position.get("x_bottom_middle"), position.get("y_bottom_middle")
        on_pitch = x is not None and y is not None and -52.5 <= x <= 52.5 and -34 <= y <= 34
        people.append(
            {
                "bbox": boxes[0]["bbox_xyxy"],
                "role": role,
                "goalkeeper": annotation["category_id"] == 2,
                "team": attributes.get("team") if role == "player" else None,
                "track_id": annotation.get("track_id"),
                "on_pitch": bool(on_pitch),
                "provider_annotation_id": str(annotation["id"]),
            }
        )
    return people


def prepare(output, *, source=ROOT / "data/course-multimatch-v1", train_step=25, val_step=125):
    """Selecteer broadcastframes, download bronbeelden en exporteer labels met hun oorspronkelijke
    rollen, teams en tracks naar de ontwikkelset.
    """
    output, source = Path(output).resolve(), Path(source).resolve()
    output.mkdir(parents=True, exist_ok=True)
    selection = read_json(source / "selection.json")
    if selection["revision"] != REVISION:
        raise ValueError("Prepared source dataset uses a different provider revision")
    games = selection["games"]
    if set(games["train"]) & set(games["val"]):
        raise ValueError("Broadcast match split overlaps")
    frozen = {
        "revision": REVISION,
        "games": games,
        "train_step": train_step,
        "val_step": val_step,
        "rule": "provider frame number 1 modulo step; complete person labels; no ignore regions",
        "test_accessed": False,
    }
    if (output / "selection.json").exists() and read_json(output / "selection.json") != frozen:
        raise ValueError("Selection changed; use a new dataset directory")
    write_json(output / "selection.json", frozen)
    if (output / "manifest.json").exists():
        saved = read_json(output / "manifest.json")
        if any(row["split"] not in {"train", "val"} for row in saved["frames"]):
            raise ValueError("Reserved images must not be opened during broadcast preparation")
        for row in saved["frames"]:
            if (
                sha256_file(row["image"]) != row["image_sha256"]
                or sha256_file(row["label"]) != row["label_sha256"]
            ):
                raise ValueError("Prepared broadcast data changed")
        return saved
    existing = {r["frame_id"]: source / r["image"] for r in read_json(source / "manifest.json")["frames"]}
    frames, excluded, hashes = [], [], {}
    for split, archive_split, step in (("train", "train", train_step), ("val", "valid", val_step)):
        clips = [
            c
            for c in read_json(source / f"catalog-{archive_split}.json")["clips"]
            if c["game_id"] in games[split]
        ]
        remote = archive = None
        thread_state, worker_archives = threading.local(), []
        pool = ThreadPoolExecutor(max_workers=8)

        def open_archive():
            """Open voor de huidige downloadthread een eigen archiefverbinding en bewaar die threadlokaal
            voor hergebruik.
            """
            nonlocal remote, archive
            if archive is None:
                remote = RangeArchive(archive_url(archive_split), budget_bytes=4 * 1024**3)
                archive = zipfile.ZipFile(remote)
            return archive

        def ensure_image(task):
            """Haal het gevraagde bronbeeld uit het archief als de lokale kopie nog ontbreekt; probeer
            tijdelijke leesfouten opnieuw.
            """
            fid, image, member = task
            if image.exists():
                return
            if fid in existing:
                os.link(existing[fid], image)
                return
            if not hasattr(thread_state, "archive"):
                worker_remote = RangeArchive(
                    archive_url(archive_split), budget_bytes=512 * 1024**2, block_size=65536
                )
                thread_state.archive = zipfile.ZipFile(worker_remote)
                worker_archives.append((thread_state.archive, worker_remote))
            for attempt in range(3):
                try:
                    payload = thread_state.archive.read(member)
                    image.write_bytes(payload)
                    return
                except (OSError, TimeoutError):
                    if attempt == 2:
                        raise
                    time.sleep(1)

        try:
            for clip_index, clip in enumerate(clips):
                name = clip["info"]["name"]
                cached = output / "provider-labels" / (name + ".json.gz")
                previous = source / "provider-labels" / cached.name
                cached.parent.mkdir(exist_ok=True)
                if not cached.exists():
                    raw = (
                        previous.read_bytes()
                        if previous.exists()
                        else gzip.compress(open_archive().read(clip["member"]), mtime=0)
                    )
                    cached.write_bytes(raw)
                data = json.loads(gzip.decompress(cached.read_bytes()))
                if float(data["info"]["version"]) < 1.3 or str(data["info"]["game_id"]) != clip["game_id"]:
                    raise ValueError("Provider annotation version or game changed")
                by_image = defaultdict(list)
                for annotation in data["annotations"]:
                    by_image[str(annotation["image_id"])].append(annotation)
                tasks = []
                for im in data["images"]:
                    if (
                        (int(Path(im["file_name"]).stem) - 1) % step
                        or not im.get("has_labeled_person")
                        or im.get("ignore_regions_x")
                        or im.get("ignore_regions_y")
                    ):
                        continue
                    if Path(im["file_name"]).name != im["file_name"] or not im["file_name"].endswith(".jpg"):
                        raise ValueError("Unsafe provider image name")
                    fid = name + "_" + Path(im["file_name"]).stem
                    target = output / "images" / split / (fid + ".jpg")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    tasks.append((fid, target, clip["member"].rsplit("/", 1)[0] + "/img1/" + im["file_name"]))
                list(pool.map(ensure_image, tasks))
                for im in data["images"]:
                    if (int(Path(im["file_name"]).stem) - 1) % step:
                        continue
                    if (
                        not im.get("has_labeled_person")
                        or im.get("ignore_regions_x")
                        or im.get("ignore_regions_y")
                    ):
                        excluded.append(
                            {"clip": name, "image": im["image_id"], "reason": "incomplete or ignored labels"}
                        )
                        continue
                    fid = name + "_" + Path(im["file_name"]).stem
                    if Path(im["file_name"]).name != im["file_name"] or not im["file_name"].endswith(".jpg"):
                        raise ValueError("Unsafe provider image name")
                    image = output / "images" / split / (fid + ".jpg")
                    image.parent.mkdir(parents=True, exist_ok=True)
                    if not image.exists():
                        if fid in existing:
                            os.link(existing[fid], image)
                        else:
                            member = clip["member"].rsplit("/", 1)[0] + "/img1/" + im["file_name"]
                            for attempt in range(3):
                                try:
                                    payload = open_archive().read(member)
                                    image.write_bytes(payload)
                                    break
                                except (OSError, TimeoutError):
                                    if attempt == 2:
                                        raise
                                    time.sleep(1)
                    pixels = cv2.imread(str(image))
                    if pixels is None or pixels.shape[:2] != (im["height"], im["width"]):
                        raise ValueError(f"Image dimensions differ: {image}")
                    digest = sha256_file(image)
                    if digest in hashes:
                        if hashes[digest] != split:
                            raise ValueError("Identical broadcast image crosses splits")
                        continue
                    hashes[digest] = split
                    annotations = by_image[str(im["image_id"])]
                    people = labelled_people(annotations, im["width"], im["height"])
                    labels, boxes = object_labels(annotations, im["width"], im["height"])
                    # The dedicated detector retains two real classes. Other people
                    # remain documented negatives; team/role crops are never full labels.
                    label = output / "labels" / split / (fid + ".txt")
                    label.parent.mkdir(parents=True, exist_ok=True)
                    label.write_text(
                        "\n".join(s for s in labels if s.startswith(("0 ", "1 "))) + "\n", encoding="utf-8"
                    )
                    frames.append(
                        {
                            "frame_id": fid,
                            "image": str(image),
                            "image_sha256": digest,
                            "label": str(label),
                            "label_sha256": sha256_file(label),
                            "width": im["width"],
                            "height": im["height"],
                            "split": split,
                            "game_id": clip["game_id"],
                            "clip": name,
                            "frame_index": int(Path(im["file_name"]).stem) - 1,
                            "boxes": [b for b in boxes if b["class_id"] in {0, 1}],
                            "people": people,
                            "provider_sha256": sha256_file(cached),
                        }
                    )
                write_json(
                    output / "progress.json",
                    {
                        "stage": "prepare",
                        "split": split,
                        "clips": clip_index + 1,
                        "total_clips": len(clips),
                        "frames": len(frames),
                        "downloaded_bytes": (remote.downloaded if remote else 0)
                        + sum(r.downloaded for _, r in worker_archives),
                    },
                )
                print(f"{split}: clip {clip_index + 1}/{len(clips)}, {len(frames)} frames", flush=True)
        finally:
            pool.shutdown(wait=True)
            for worker_archive, worker_remote in worker_archives:
                worker_archive.close()
                worker_remote.close()
            if archive:
                archive.close()
            if remote:
                remote.close()
    result = {
        "schema_version": 1,
        "dataset_version": "broadcast-pitch-v1",
        "source": DATASET_URL,
        "source_revision": REVISION,
        "selection": frozen,
        "frames": frames,
        "counts": dict(Counter(r["split"] for r in frames)),
        "excluded": excluded,
        "names": {0: "player", 1: "referee"},
        "test_accessed": False,
        "human_review_completed": False,
        "annotation_provenance": "SN-GSR v1.3 provider labels",
    }
    result["fingerprint"] = digest_json(result)
    (output / "data.yaml").write_text(
        yaml.safe_dump(
            {
                "path": output.as_posix(),
                "train": "images/train",
                "val": "images/val",
                "names": result["names"],
            }
        ),
        encoding="utf-8",
    )
    write_json(output / "manifest.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(prepare(args.output)["counts"])
