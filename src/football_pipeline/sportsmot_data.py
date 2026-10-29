"""Voegt gelabelde voetbalsporters uit SportsMOT toe en bewaart de betekenis van de bronlabels.


Its target definition excludes referees, coaches and spectators. No SportsMOT
validation/test image is opened. SoccerNet's frozen validation matches stay fixed.
"""

from __future__ import annotations

import argparse
import configparser
import csv
import io
import os
import re
import tarfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import cv2
import numpy as np
import requests
import yaml

from .contracts import digest_json, read_json, sha256_file, write_json
from .video import ROOT

REVISION = "1b0b418ea611a8e934f1e773313e719e4fa1265e"
ARCHIVE_SHA256 = "dc8edc8126bcb66611e768679f618a14880510944dc0e07959c00c0c14722341"
SOURCE = "https://huggingface.co/datasets/MCG-NJU/SportsMOT"


def football_selection():
    base = SOURCE + "/resolve/" + REVISION + "/splits_txt/"
    lists = {}
    for name in ("train", "football"):
        response = requests.get(base + name + ".txt", timeout=60)
        response.raise_for_status()
        lists[name] = response.text.split()
    return sorted(set(lists["train"]) & set(lists["football"])), lists


def athlete_boxes(text, width, height):
    result = defaultdict(list)
    for row in csv.reader(io.StringIO(text)):
        if not row:
            continue
        numbers = np.asarray(row, float)
        if len(numbers) < 8 or not np.isfinite(numbers).all() or int(numbers[7]) != 1:
            raise ValueError("Unknown SportsMOT target class or malformed annotation")
        frame, track, x, y, w, h, marked = numbers[:7]
        if marked != 1 or w <= 0 or h <= 0:
            raise ValueError("Incomplete athlete annotations cannot silently become negatives")
        # Follow the provider's MOT-to-COCO convention; no frame or bbox offset
        # is fitted to model predictions. Only the image boundary is clipped.
        box = [max(0.0, x), max(0.0, y), min(float(width), x + w), min(float(height), y + h)]
        if box[2] > box[0] and box[3] > box[1]:
            result[int(frame)].append(
                {
                    "bbox": box,
                    "track_id": int(track),
                    "role": "player",
                    "team": None,
                    "goalkeeper": None,
                    "on_pitch": None,
                    "provider_scope": "players_on_playground",
                }
            )
    return result


def prepare_football(archive, output, step=5):
    archive, output = Path(archive).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if sha256_file(archive) != ARCHIVE_SHA256:
        raise ValueError("SportsMOT training archive checksum changed")
    selected, lists = football_selection()
    frozen = {
        "source": SOURCE,
        "revision": REVISION,
        "archive_sha256": ARCHIVE_SHA256,
        "split": "train",
        "sequences": selected,
        "source_lists": lists,
        "frame_step": step,
        "test_accessed": False,
    }
    selection = output / "selection.json"
    if selection.exists() and read_json(selection) != frozen:
        raise ValueError("SportsMOT selection changed; choose a new output")
    write_json(selection, frozen)
    if (output / "manifest.json").exists():
        saved = read_json(output / "manifest.json")
        for row in saved["frames"]:
            if row["split"] != "train" or sha256_file(row["image"]) != row["image_sha256"]:
                raise ValueError("Prepared athlete images changed or reserved split entered training")
        return saved
    by_sequence = defaultdict(dict)
    with tarfile.open(archive, "r:") as source:
        for member in source.getmembers():
            parts = PurePosixPath(member.name).parts
            if "test" in parts or "val" in parts:
                raise ValueError("The declared training archive contains a reserved split")
            matches = [p for p in parts if p in selected]
            if not matches:
                continue
            sequence = matches[0]
            at = parts.index(sequence)
            if (
                at == 0
                or parts[at - 1] != "train"
                or ".." in parts
                or "\\" in member.name
                or not member.isfile()
            ):
                if member.isdir():
                    continue
                raise ValueError("Unsafe or unverified SportsMOT member")
            suffix = "/".join(parts[at + 1 :])
            if suffix in {"seqinfo.ini", "gt/gt.txt"} or (
                re.fullmatch(r"img1/\d{6}\.jpg", suffix) and (int(Path(suffix).stem) - 1) % step == 0
            ):
                by_sequence[sequence][suffix] = member
        frames = []
        for sequence in selected:
            members = by_sequence[sequence]
            info = configparser.ConfigParser()
            info.read_string(source.extractfile(members["seqinfo.ini"]).read().decode())
            width, height = int(info["Sequence"]["imWidth"]), int(info["Sequence"]["imHeight"])
            labels = source.extractfile(members["gt/gt.txt"]).read().decode()
            people = athlete_boxes(labels, width, height)
            label_copy = output / "provider-labels" / (sequence + ".txt")
            label_copy.parent.mkdir(exist_ok=True)
            label_copy.write_text(labels, encoding="utf-8")
            for name, member in sorted(members.items()):
                if not name.startswith("img1/"):
                    continue
                frame = int(Path(name).stem)
                fid = "sportsmot_" + sequence + "_" + Path(name).stem
                image = output / "images" / (fid + ".jpg")
                image.parent.mkdir(exist_ok=True)
                if not image.exists():
                    image.write_bytes(source.extractfile(member).read())
                pixels = cv2.imread(str(image))
                if pixels is None or pixels.shape[:2] != (height, width):
                    raise ValueError("SportsMOT image dimensions disagree with the source")
                if not people.get(frame):
                    raise ValueError("Unlabelled athlete frame cannot be treated as background")
                frames.append(
                    {
                        "frame_id": fid,
                        "image": str(image),
                        "image_sha256": sha256_file(image),
                        "width": width,
                        "height": height,
                        "split": "train",
                        "clip": sequence,
                        "game_id": "sportsmot:" + sequence.rsplit("_c", 1)[0],
                        "frame_index": frame - 1,
                        "people": people[frame],
                        "provider_sha256": sha256_file(label_copy),
                    }
                )
            print("Prepared SportsMOT", sequence, len(frames), "training frames", flush=True)
    result = {
        "source": SOURCE,
        "selection": frozen,
        "frames": frames,
        "test_accessed": False,
        "license": "CC-BY-NC-4.0",
        "human_review_completed": False,
    }
    result["fingerprint"] = digest_json(result)
    write_json(output / "manifest.json", result)
    return result


def mixed_player_dataset(sports, output, base=ROOT / "data/broadcast-pitch-v1"):
    output, base = Path(output).resolve(), Path(base).resolve()
    original = read_json(base / "manifest.json")
    output.mkdir(parents=True, exist_ok=True)
    rows, hashes = [], {}
    for provider, items in (("soccernet", original["frames"]), ("sportsmot", sports["frames"])):
        for row in items:
            split = row["split"]
            if split not in {"train", "val"} or (provider == "sportsmot" and split != "train"):
                raise ValueError("Reserved data cannot enter mixed training")
            checksum = sha256_file(row["image"])
            if checksum != row["image_sha256"] or (checksum in hashes and hashes[checksum] != split):
                raise ValueError("Image bytes changed or duplicate image crosses splits")
            hashes[checksum] = split
            # Rectangular training cannot shuffle by aspect. Random aliases mix
            # matches deterministically even when the loader sorts filenames.
            alias = digest_json([42, provider, row["frame_id"]])[:24]
            image = output / "images" / split / (alias + ".jpg")
            image.parent.mkdir(parents=True, exist_ok=True)
            if not image.exists():
                os.link(row["image"], image)
            elif sha256_file(image) != checksum:
                raise ValueError("Mixed training alias changed")
            label = output / "labels" / split / (alias + ".txt")
            label.parent.mkdir(parents=True, exist_ok=True)
            lines = []
            width, height = row["width"], row["height"]
            for person in row["people"]:
                if person["role"] != "player":
                    continue
                x1, y1, x2, y2 = person["bbox"]
                lines.append(
                    f"0 {(x1 + x2) / 2 / width:.9f} {(y1 + y2) / 2 / height:.9f} {(x2 - x1) / width:.9f} {(y2 - y1) / height:.9f}"
                )
            label.write_text("\n".join(lines) + "\n", encoding="utf-8")
            rows.append(
                {
                    **row,
                    "provider": provider,
                    "image": str(image),
                    "label": str(label),
                    "label_sha256": sha256_file(label),
                    "original_image": row["image"],
                }
            )
    result = {
        "schema_version": 1,
        "names": {0: "player"},
        "frames": rows,
        "source_fingerprints": {"soccernet": original["fingerprint"], "sportsmot": sports["fingerprint"]},
        "selection": sports["selection"],
        "counts": dict(Counter((r["provider"] + ":" + r["split"]) for r in rows)),
        "test_accessed": False,
        "referees": "Known non-target humans, not relabelled as players",
        "split_rule": "Original SoccerNet validation matches; SportsMOT official football train only",
        "ordering": "Seed-42 hashed aliases mix matches before aspect sorting",
    }
    result["fingerprint"] = digest_json(result)
    (output / "data.yaml").write_text(
        yaml.safe_dump(
            {"path": output.as_posix(), "train": "images/train", "val": "images/val", "names": {0: "player"}}
        ),
        encoding="utf-8",
    )
    write_json(output / "manifest.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / ".cache/sportsmot/train.tar")
    parser.add_argument("--sports-output", type=Path, default=ROOT / "data/sportsmot-football-train-v1")
    parser.add_argument("--output", type=Path, default=ROOT / "data/broadcast-multisource-v1")
    args = parser.parse_args()
    print(mixed_player_dataset(prepare_football(args.archive, args.sports_output), args.output)["counts"])
