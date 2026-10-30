"""Provider-supervised multi-match development set; project test images stay unopened."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from .contracts import digest_json, read_json, sha256_file, write_json
from .research_archive import RangeArchive

REVISION = "3cc710eb6d53a23350a3d2863311c1c0a2e645d7"
DATASET_URL = "https://huggingface.co/datasets/SoccerNet/SN-GSR-2024"
NAMES = {0: "player", 1: "referee", 2: "ball", 3: "person"}
CATEGORY_MAP = {1: 0, 2: 0, 3: 1, 4: 2, 7: 3}


def archive_url(split):
    if split not in {"train", "valid"}:
        raise ValueError("Only public train and validation archives may be opened for development")
    return f"{DATASET_URL}/resolve/{REVISION}/{split}.zip"


def catalog(archive):
    clips = []
    for member in sorted(n for n in archive.namelist() if n.endswith("/Labels-GameState.json")):
        with archive.open(member) as stream:
            prefix = stream.read(16384).decode("utf-8-sig")
        position = prefix.index('"info"')
        info = json.JSONDecoder().raw_decode(prefix[prefix.index(":", position) + 1 :].lstrip())[0]
        if float(info["version"]) < 1.3:
            raise ValueError("Need the corrected v1.3 GameState labels")
        if not re.fullmatch(r"SNGS-\d+", info["name"]):
            raise ValueError("Unsafe provider clip name")
        clips.append({"member": member, "info": info, "game_id": str(info["game_id"])})
    return clips


def select_games(catalogs):
    train = {r["game_id"] for r in catalogs["train"]}
    valid = {r["game_id"] for r in catalogs["valid"]}
    # Retain the official validation games and remove all overlapping games from training.
    train_only = train - valid
    if len(train_only) >= 2 and len(valid) >= 2:
        return {"train": sorted(train_only), "val": sorted(valid)}, "official_valid_games_excluded_from_train"
    # Some releases split clips of the same match. A frozen game split is stronger than that split.
    games = sorted(train, key=lambda game: digest_json(["course-multimatch-v1", game]))
    if len(games) < 4:
        raise ValueError("Too few independently identified matches for a multi-match experiment")
    holdout = max(2, round(len(games) * 0.25))
    return {"train": games[holdout:], "val": games[:holdout]}, "frozen_game_holdout_from_official_train"


def selected_clips(catalogs, games, strategy, split):
    source = "valid" if split == "val" and strategy.startswith("official_valid") else "train"
    pool = [dict(row, archive_split=source) for row in catalogs[source] if row["game_id"] in games[split]]
    # Round-robin matches before selecting more clips of one match.
    grouped = defaultdict(list)
    for row in pool:
        grouped[row["game_id"]].append(row)
    result = []
    for i in range(max(map(len, grouped.values()))):
        for game in sorted(grouped):
            if i < len(grouped[game]):
                result.append(grouped[game][i])
    return result


def object_labels(annotations, width, height):
    labels, boxes = [], []
    for annotation in annotations:
        if annotation["supercategory"] != "object":
            continue
        category = annotation["category_id"]
        if category not in CATEGORY_MAP:
            raise ValueError(f"Unmapped provider object category: {category}")
        box = annotation.get("bbox_image")
        if not box:
            continue
        values = np.array([box[k] for k in ("x", "y", "w", "h")], float)
        if not np.isfinite(values).all() or (values[2:] <= 0).any():
            raise ValueError("Invalid provider bounding box")
        x, y, w, h = values
        x1, y1, x2, y2 = max(0, x), max(0, y), min(width, x + w), min(height, y + h)
        if x2 <= x1 or y2 <= y1:
            continue
        cls = CATEGORY_MAP[category]
        labels.append(
            f"{cls} {(x1 + x2) / 2 / width:.9f} {(y1 + y2) / 2 / height:.9f} {(x2 - x1) / width:.9f} {(y2 - y1) / height:.9f}"
        )
        boxes.append({"class_id": cls, "bbox_xyxy": [x1, y1, x2, y2]})
    return labels, boxes


def prepare(root, train_count=60, valid_count=20):
    root = Path(root).resolve()
    if train_count < 1 or valid_count < 1 or train_count + valid_count > 80:
        raise ValueError("This curated experiment uses at most 80 source frames")
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        for row in manifest["frames"]:
            for key in ("image", "label", "field_label"):
                if sha256_file(root / row[key]) != row[key + "_sha256"]:
                    raise ValueError("Prepared dataset was modified; preserve edits and create a new version")
        return manifest
    root.mkdir(parents=True, exist_ok=True)
    archives, remotes, catalogs = {}, {}, {}
    try:
        for source in ("train", "valid"):
            remote = RangeArchive(archive_url(source))
            remotes[source] = remote
            archives[source] = zipfile.ZipFile(remote)
            cached = root / f"catalog-{source}.json"
            catalogs[source] = read_json(cached)["clips"] if cached.exists() else catalog(archives[source])
            write_json(cached, {"revision": REVISION, "clips": catalogs[source]})
            print(
                f"Catalog {source}: {len(catalogs[source])} clips, {remote.downloaded / 1024**2:.1f} MiB fetched",
                flush=True,
            )
        games, strategy = select_games(catalogs)
        if set(games["train"]) & set(games["val"]):
            raise ValueError("Match leakage")
        selection = {
            "games": games,
            "strategy": strategy,
            "counts": {"train": train_count, "val": valid_count},
            "revision": REVISION,
            "selection_rule": "round_robin_matches_then_clips; fixed temporal samples before inference",
            "test_access": "official test and challenge archives never opened",
        }
        frozen = root / "selection.json"
        if frozen.exists() and read_json(frozen) != selection:
            raise ValueError("Selection changed; use a fresh dataset version")
        write_json(frozen, selection)
        frames, counts = [], Counter()
        for split, wanted in (("train", train_count), ("val", valid_count)):
            clips = selected_clips(catalogs, games, strategy, split)
            if not clips:
                raise ValueError("No clips in the frozen match split")
            quota = max(1, int(np.ceil(wanted / min(len(clips), wanted))))
            match_info = {}
            field_split = "train" if split == "train" else "valid"
            for row in clips:
                if counts[split] >= wanted:
                    break
                archive = archives[row["archive_split"]]
                compressed = root / "provider-labels" / (row["info"]["name"] + ".json.gz")
                compressed.parent.mkdir(exist_ok=True)
                if compressed.exists():
                    raw = gzip.decompress(compressed.read_bytes())
                else:
                    raw = archive.read(row["member"])
                    compressed.write_bytes(gzip.compress(raw, mtime=0))
                data = json.loads(raw)
                grouped = defaultdict(list)
                for annotation in data["annotations"]:
                    grouped[str(annotation["image_id"])].append(annotation)
                available = [
                    im
                    for im in data["images"]
                    if im.get("has_labeled_person")
                    and im.get("has_labeled_pitch")
                    and not im.get("ignore_regions_x")
                    and not im.get("ignore_regions_y")
                ]
                if not available:
                    continue
                indices = np.linspace(
                    int(len(available) * 0.15), max(0, int(len(available) * 0.85) - 1), quota, dtype=int
                )
                for i in indices:
                    if counts[split] >= wanted:
                        break
                    im = available[int(i)]
                    if not re.fullmatch(r"\d{6}\.jpg", im["file_name"]):
                        raise ValueError("Unsafe provider frame name")
                    annotations = grouped[str(im["image_id"])]
                    pitch = next((a["lines"] for a in annotations if a["supercategory"] == "pitch"), None)
                    if not pitch:
                        continue
                    fid = row["info"]["name"] + "_" + Path(im["file_name"]).stem
                    image = Path("images") / split / (fid + ".jpg")
                    label = Path("labels") / split / (fid + ".txt")
                    field_split = "train" if split == "train" else "valid"
                    field_image = Path("field") / field_split / (fid + ".jpg")
                    field_label = field_image.with_suffix(".json")
                    for path in (image, label, field_label):
                        (root / path).parent.mkdir(parents=True, exist_ok=True)
                    member = str(Path(row["member"]).parent.as_posix()) + "/img1/" + im["file_name"]
                    if not (root / image).exists():
                        (root / image).write_bytes(archive.read(member))
                    with Image.open(root / image) as decoded:
                        if decoded.size != (im["width"], im["height"]):
                            raise ValueError("Provider image dimensions disagree with annotations")
                        decoded.verify()
                    labels, boxes = object_labels(annotations, im["width"], im["height"])
                    (root / label).write_text("\n".join(labels) + "\n", encoding="utf-8")
                    write_json(root / field_label, pitch)
                    if not (root / field_image).exists():
                        os.link(root / image, root / field_image)
                    moment = int(row["info"]["clip_start"]) + round(
                        (int(Path(im["file_name"]).stem) - 1) / 25 * 1000
                    )
                    match_info[field_image.name] = {
                        "league": "SN-GSR-2024",
                        "season": "v1.3",
                        "date": "provider",
                        "match": "game-" + row["game_id"],
                        "ms_time": moment,
                        "replay_time": moment,
                    }
                    frames.append(
                        {
                            "frame_id": fid,
                            "split": split,
                            "game_id": row["game_id"],
                            "clip": row["info"]["name"],
                            "source_archive": row["archive_split"],
                            "provider_image_id": str(im["image_id"]),
                            "width": im["width"],
                            "height": im["height"],
                            "image": image.as_posix(),
                            "label": label.as_posix(),
                            "field_label": field_label.as_posix(),
                            "image_sha256": sha256_file(root / image),
                            "label_sha256": sha256_file(root / label),
                            "field_label_sha256": sha256_file(root / field_label),
                            "boxes": boxes,
                            "annotation_provenance": "published SN-GSR-2024 v1.3; not model-generated labels",
                            "project_human_review_completed": False,
                        }
                    )
                    counts[split] += 1
                    print(
                        f"Prepared {split} {counts[split]}/{wanted}: {fid} game {row['game_id']}", flush=True
                    )
            write_json(root / "field" / field_split / "match_info.json", match_info)
            if counts[split] != wanted:
                raise ValueError("Not enough fully labeled source frames for the frozen selection")
        if len({r["image_sha256"] for r in frames}) != len(frames):
            raise ValueError("Duplicate source images")
        config = {"path": str(root), "train": "images/train", "val": "images/val", "names": NAMES}
        (root / "data.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        manifest = {
            "schema_version": 1,
            "dataset_version": "course-multimatch-v1",
            "source": DATASET_URL,
            "source_revision": REVISION,
            "selection": selection,
            "frames": frames,
            "counts": dict(counts),
            "match_counts": {
                s: len({r["game_id"] for r in frames if r["split"] == s}) for s in ("train", "val")
            },
            "names": NAMES,
            "project_human_review_completed": False,
            "test_accessed": False,
            "pretraining_overlap_with_field_model": "not excluded",
            "downloaded_bytes": sum(r.downloaded for r in remotes.values()),
        }
        manifest["fingerprint"] = digest_json(manifest)
        write_json(manifest_path, manifest)
        return manifest
    finally:
        for archive in archives.values():
            archive.close()
        for remote in remotes.values():
            remote.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    result = prepare(args.root)
    print({key: result[key] for key in ("counts", "match_counts", "fingerprint", "downloaded_bytes")})
