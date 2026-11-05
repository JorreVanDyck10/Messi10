"""Bouwt en controleert een hervatbare broadcastdataset uit SoccerNet-providerlabels."""

from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import shutil
import struct
import threading
import time
import zipfile
import zlib
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests
import yaml
from PIL import Image

from .contracts import digest_json, read_json, sha256_file, write_json
from .course_dataset import DATASET_URL, NAMES, REVISION, archive_url, object_labels, select_games
from .research_archive import RangeArchive

ROLE_NAMES = {0: "player", 1: "goalkeeper", 2: "referee", 3: "ball", 4: "other"}
ROLE_MAP = {1: 0, 2: 1, 3: 2, 4: 3, 7: 4}


def unpack_member(payload, info):
    """Decode one checked local ZIP record; no archive paths are extracted."""
    if len(payload) < 30 or payload[:4] != b"PK\x03\x04":
        raise ValueError("Missing ZIP local header")
    fields = struct.unpack("<4s5H3I2H", payload[:30])
    flags, method, name_size, extra_size = fields[2], fields[3], fields[-2], fields[-1]
    if flags & 1 or method != info.compress_type:
        raise ValueError("Encrypted member or compression mismatch")
    encoding = "utf-8" if flags & 0x800 else "cp437"
    if payload[30 : 30 + name_size].decode(encoding) != info.filename:
        raise ValueError("ZIP local filename differs from central directory")
    start = 30 + name_size + extra_size
    compressed = payload[start : start + info.compress_size]
    if len(compressed) != info.compress_size:
        raise ValueError("Truncated ZIP member")
    if method == zipfile.ZIP_DEFLATED:
        raw = zlib.decompress(compressed, -15)
    elif method == zipfile.ZIP_STORED:
        raw = compressed
    else:
        raise ValueError(f"Unsupported ZIP compression: {method}")
    if len(raw) != info.file_size or zlib.crc32(raw) & 0xFFFFFFFF != info.CRC:
        raise ValueError("ZIP member size or CRC mismatch")
    return raw


class MemberArchive:
    """Independent bounded range requests allow concurrent reads of immutable ZIPs."""

    def __init__(self, split):
        """Bewaar de gekozen archiefsplit en maak threadlokale opslag voor onafhankelijke HTTP-sessies
        tijdens parallel downloaden.
        """
        self.url = archive_url(split)
        # Resolve once without a Range header: this grants a full-object CDN URL.
        # Resolving every image separately exhausts Hugging Face's resolver quota.
        with requests.get(self.url + "?download=true", stream=True, timeout=60) as response:
            response.raise_for_status()
            self.download_url = response.url
        with RangeArchive(self.download_url, budget_bytes=64 * 1024**2) as remote:
            with zipfile.ZipFile(remote) as archive:
                self.members = {i.filename: i for i in archive.infolist()}
            self.size = remote.size
        self.local = threading.local()

    def read(self, member):
        """Lees het exacte bereik van een gecomprimeerd archieflid via HTTP en probeer tijdelijke
        netwerkfouten opnieuw voordat het bronlid wordt teruggegeven.
        """
        info = self.members[member]
        # ZIP extra fields have a maximum length of 65535 bytes.
        start = info.header_offset
        end = min(self.size - 1, start + 30 + len(member.encode("utf-8")) + 65535 + info.compress_size - 1)
        if not hasattr(self.local, "session"):
            self.local.session = requests.Session()
        for attempt in range(5):
            try:
                with self.local.session.get(
                    self.download_url, headers={"Range": f"bytes={start}-{end}"}, timeout=60, stream=True
                ) as response:
                    response.raise_for_status()
                    expected = f"bytes {start}-{end}/{self.size}"
                    if response.status_code != 206 or response.headers.get("Content-Range") != expected:
                        raise ValueError("Server did not honor exact archive range")
                    body = response.raw.read(end - start + 2)
                if len(body) != end - start + 1:
                    raise ValueError("Truncated or oversized HTTP range")
                return unpack_member(body, info)
            except (requests.RequestException, OSError, ValueError):
                if attempt == 4:
                    raise
                time.sleep(min(2**attempt, 8))


def load_clip(root, archive, source, member):
    """Pak één annotatielid uit, lees de clipinformatie en retourneer bronmetadata met het opgeslagen
    annotatiepad en de hash.
    """
    clip = member.split("/")[0]
    if not re.fullmatch(r"SNGS-\d+", clip):
        raise ValueError("Unsafe provider clip name")
    destination = root / "provider-labels" / f"{clip}.json.gz"
    if destination.exists():
        raw = gzip.decompress(destination.read_bytes())
    else:
        raw = archive.read(member)
        destination.write_bytes(gzip.compress(raw, mtime=0))
    expected = archive.members[member]
    if len(raw) != expected.file_size or zlib.crc32(raw) & 0xFFFFFFFF != expected.CRC:
        raise ValueError("Cached provider annotations differ from the published ZIP member")
    data = json.loads(raw)
    info = data["info"]
    if str(info["version"]) != "1.3" or info["name"] != clip or int(info["frame_rate"]) != 25:
        raise ValueError("Unexpected provider annotation version, clip or frame rate")
    categories = {c["id"]: c["name"] for c in data["categories"] if c["supercategory"] == "object"}
    if categories != {1: "player", 2: "goalkeeper", 3: "referee", 4: "ball", 7: "other"}:
        raise ValueError("Provider class mapping changed")
    return {
        "member": member,
        "archive_split": source,
        "info": info,
        "game_id": str(info["game_id"]),
        "annotation_path": str(destination),
        "annotation_sha256": sha256_file(destination),
    }


def eligible_images(data, min_gap=5):
    """Use annotated full frames, exclude ignore regions and temporally thin the pool."""
    annotations = defaultdict(list)
    for annotation in data["annotations"]:
        annotations[str(annotation["image_id"])].append(annotation)
    candidates, last = [], -min_gap
    for im in sorted(data["images"], key=lambda im: im["file_name"]):
        if not re.fullmatch(r"\d{6}\.jpg", im["file_name"]):
            raise ValueError("Unsafe provider image name")
        index = int(Path(im["file_name"]).stem) - 1
        objects = annotations[str(im["image_id"])]
        if (
            im.get("is_labeled")
            and im.get("has_labeled_person")
            and im.get("has_labeled_pitch")
            and not im.get("ignore_regions_x")
            and not im.get("ignore_regions_y")
            and any(a["supercategory"] == "pitch" and a.get("lines") for a in objects)
            and index - last >= min_gap
        ):
            candidates.append((im, objects))
            last = index
    return candidates


def choose_frames(clips, games, split, wanted):
    """Verdeel de gewenste selectie over toegestane clips en wedstrijden zonder de vooraf bepaalde
    splitgrenzen te veranderen.
    """
    pools = []
    # Alternate games, then clips; reserve every validation match from training.
    by_game = defaultdict(list)
    source = "train" if split == "train" else "valid"
    for clip in sorted(clips, key=lambda c: c["info"]["name"]):
        if clip["archive_split"] == source and clip["game_id"] in games[split]:
            # Keep only thinned candidates in memory, rather than all 86k full-frame labels.
            data = clip.get("data")
            if data is None:
                data = json.loads(gzip.decompress(Path(clip["annotation_path"]).read_bytes()))
            pool = eligible_images(data)
            if pool:
                by_game[clip["game_id"]].append((clip, pool))
    for i in range(max((len(v) for v in by_game.values()), default=0)):
        for game in sorted(by_game):
            if i < len(by_game[game]):
                pools.append(by_game[game][i])
    if sum(len(pool) for _, pool in pools) < wanted:
        raise ValueError(f"Not enough fully annotated {split} images at a five-frame minimum gap")
    quotas = [0] * len(pools)
    for _ in range(wanted):
        chosen = min(
            (i for i, (_, pool) in enumerate(pools) if quotas[i] < len(pool)), key=lambda i: (quotas[i], i)
        )
        quotas[chosen] += 1
    result = []
    for (clip, pool), quota in zip(pools, quotas):
        for index in np.linspace(0, len(pool) - 1, quota, dtype=int):
            image, objects = pool[int(index)]
            result.append({"clip": clip, "image": image, "annotations": objects, "split": split})
    return result


def prepare_frame(root, archives, selected):
    """Download één geselecteerd bronbeeld, zet providerobjecten om naar labels en retourneer het
    herleidbare framerecord.
    """
    clip, im, annotations, split = (selected[k] for k in ("clip", "image", "annotations", "split"))
    fid = clip["info"]["name"] + "_" + Path(im["file_name"]).stem
    paths = {
        "image": f"images/{split}/{fid}.jpg",
        "label": f"labels/{split}/{fid}.txt",
        "role_label": f"roles/labels/{split}/{fid}.txt",
        "field_label": f"field/{'train' if split == 'train' else 'valid'}/{fid}.json",
        "attributes": f"attributes/{split}/{fid}.json",
    }
    image = root / paths["image"]
    member = f"{clip['info']['name']}/img1/{im['file_name']}"
    expected = archives[clip["archive_split"]].members[member]
    if image.exists():
        raw = image.read_bytes()
        if len(raw) != expected.file_size or zlib.crc32(raw) & 0xFFFFFFFF != expected.CRC:
            raise ValueError(f"Previously downloaded image changed: {image}")
    else:
        raw = archives[clip["archive_split"]].read(member)
        temporary = image.with_suffix(".jpg.part")
        temporary.write_bytes(raw)
        temporary.replace(image)
    with Image.open(io.BytesIO(raw)) as decoded:
        if decoded.size != (im["width"], im["height"]):
            raise ValueError("Image dimensions disagree with labels")
        decoded.verify()
    labels, boxes = object_labels(annotations, im["width"], im["height"])
    (root / paths["label"]).write_text("\n".join(labels) + ("\n" if labels else ""), encoding="utf-8")
    roles = []
    clipped, dropped = 0, 0
    for annotation in annotations:
        if annotation["supercategory"] != "object" or not annotation.get("bbox_image"):
            continue
        converted, _ = object_labels([annotation], im["width"], im["height"])
        if not converted:
            dropped += 1
            continue
        roles.append(str(ROLE_MAP[annotation["category_id"]]) + " " + converted[0].split(" ", 1)[1])
        b = annotation["bbox_image"]
        clipped += int(
            b["x"] < 0 or b["y"] < 0 or b["x"] + b["w"] > im["width"] or b["y"] + b["h"] > im["height"]
        )
    (root / paths["role_label"]).write_text("\n".join(roles) + ("\n" if roles else ""), encoding="utf-8")
    pitch = next(a["lines"] for a in annotations if a["supercategory"] == "pitch" and a.get("lines"))
    # Preserve provider lines exactly; downstream field preprocessing handles boundary clipping.
    write_json(root / paths["field_label"], pitch)
    write_json(
        root / paths["attributes"],
        {
            "image": im,
            "annotations": annotations,
            "source_annotation_sha256": clip["annotation_sha256"],
            "team_semantics": "provider left/right within clip; not a universal team identity",
        },
    )
    for target in (root / "roles" / paths["image"], (root / paths["field_label"]).with_suffix(".jpg")):
        if not target.exists():
            target.hardlink_to(image)
    row = {
        "frame_id": fid,
        "split": split,
        "game_id": clip["game_id"],
        "clip": clip["info"]["name"],
        "source_archive": clip["archive_split"],
        "provider_image_id": str(im["image_id"]),
        "width": im["width"],
        "height": im["height"],
        "source_frame_index": int(Path(im["file_name"]).stem) - 1,
        "boxes": boxes,
        "annotation_provenance": "published SN-GSR-2024 v1.3; no model-generated labels",
        "project_human_review_completed": False,
        "clipped_boxes": clipped,
        "dropped_boxes": dropped,
        "provider_annotation_sha256": clip["annotation_sha256"],
        **paths,
    }
    row.update({k + "_sha256": sha256_file(root / p) for k, p in paths.items()})
    return row


def audit(root, manifest):
    """Independently parse the exported labels and compare them to manifest boxes."""
    from persoon1.core import label_pixels, read_labels

    counts, role_counts = defaultdict(Counter), defaultdict(Counter)
    if (
        "fingerprint" in manifest
        and digest_json({k: v for k, v in manifest.items() if k != "fingerprint"}) != manifest["fingerprint"]
    ):
        raise ValueError("Dataset manifest fingerprint changed")
    hashes, ids, match_splits = {}, set(), defaultdict(set)
    source_hashes = {}
    for row in manifest["frames"]:
        fid = row["frame_id"]
        if fid in ids:
            raise ValueError("Duplicate frame identity")
        ids.add(fid)
        clip = row["clip"]
        if clip not in source_hashes:
            source_hashes[clip] = sha256_file(root / "provider-labels" / f"{clip}.json.gz")
        if source_hashes[clip] != row["provider_annotation_sha256"]:
            raise ValueError("Original provider annotation checksum changed")
        for key in ("image", "label", "role_label", "field_label", "attributes"):
            if sha256_file(root / row[key]) != row[key + "_sha256"]:
                raise ValueError(f"Dataset checksum mismatch: {row[key]}")
        image_hash = row["image_sha256"]
        if image_hash in hashes:
            raise ValueError(f"Duplicate image: {fid} and {hashes[image_hash]}")
        hashes[image_hash] = fid
        match_splits[row["game_id"]].add(row["split"])
        parsed = read_labels(root / row["label"], len(NAMES))
        if len(parsed) != len(row["boxes"]):
            raise ValueError("YOLO box count mismatch")
        for exported, original in zip(parsed, row["boxes"]):
            if exported["class_id"] != original["class_id"] or not np.allclose(
                label_pixels(exported, row["width"], row["height"]), original["bbox_xyxy"], atol=0.00001
            ):
                raise ValueError("YOLO conversion differs from source pixel box")
            counts[row["split"]][NAMES[exported["class_id"]]] += 1
        for label in read_labels(root / row["role_label"], len(ROLE_NAMES)):
            role_counts[row["split"]][ROLE_NAMES[label["class_id"]]] += 1
        with Image.open(root / row["image"]) as image:
            if image.size != (row["width"], row["height"]):
                raise ValueError("Image size changed")
            image.load()
    if any(len(splits) != 1 for splits in match_splits.values()):
        raise ValueError("A match occurs in multiple splits")
    result = {
        "status": "passed",
        "frames": len(ids),
        "counts": dict(Counter(r["split"] for r in manifest["frames"])),
        "object_counts": {s: dict(c) for s, c in counts.items()},
        "role_counts": {s: dict(c) for s, c in role_counts.items()},
        "match_ids": {
            s: sorted(g for g, splits in match_splits.items() if s in splits) for s in ("train", "val")
        },
        "duplicate_images": 0,
        "match_split_overlap": 0,
        "clip_count": len(source_hashes),
        "fully_decoded_images": len(ids),
        "clipped_boxes": sum(r["clipped_boxes"] for r in manifest["frames"]),
        "dropped_boxes": sum(r["dropped_boxes"] for r in manifest["frames"]),
        "project_human_review_completed": False,
        "test_accessed": False,
    }
    write_json(root / "quality-report.json", result)
    return result


def prepare(root, train_count=6000, valid_count=2000, workers=8):
    """Beveilig datasetbouw met een exclusieve lock en geef die ook bij fouten vrij voordat een andere
    schrijver verder kan.
    """
    root = Path(root).resolve()
    if min(train_count, valid_count) < 1 or not 1 <= workers <= 16:
        raise ValueError("Positive split counts and 1-16 workers required")
    root.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root).free < (train_count + valid_count) * 700000 + 2 * 1024**3:
        raise ValueError("Insufficient free disk space for the requested dataset")
    lock_path = root / ".writer.lock"
    lock = lock_path.open("x")
    try:
        return _prepare(root, train_count, valid_count, workers)
    finally:
        lock.close()
        lock_path.unlink()


def _prepare(root, train_count, valid_count, workers):
    """Bouw of hervat beelden, labels en metadata voor de aangevraagde broadcasttrainings- en
    validatieset en controleer de resulterende inventaris.
    """
    settings = {
        "revision": REVISION,
        "train_count": train_count,
        "valid_count": valid_count,
        "minimum_frame_gap": 5,
        "source": DATASET_URL,
    }
    settings_path = root / "settings.json"
    if settings_path.exists() and read_json(settings_path) != settings:
        raise ValueError("Settings changed; choose a new output directory")
    write_json(settings_path, settings)
    existing = root / "manifest.json"
    if existing.exists():
        return audit(root, read_json(existing))
    (root / "provider-labels").mkdir(exist_ok=True)
    archives = {s: MemberArchive(s) for s in ("train", "valid")}
    tasks = [
        (s, member)
        for s, a in archives.items()
        for member in sorted(a.members)
        if member.endswith("/Labels-GameState.json")
    ]
    clips = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for clip in pool.map(lambda t: load_clip(root, archives[t[0]], *t), tasks):
            clips.append(clip)
            print(
                f"Labels {len(clips)}/{len(tasks)}: {clip['info']['name']} game {clip['game_id']}", flush=True
            )
    catalogs = {s: [c for c in clips if c["archive_split"] == s] for s in archives}
    games, strategy = select_games(catalogs)
    if not strategy.startswith("official_valid"):
        raise ValueError("Need official validation matches excluded from training for this corpus")
    selected = choose_frames(clips, games, "train", train_count) + choose_frames(
        clips, games, "val", valid_count
    )
    selection = {
        **settings,
        "games": games,
        "strategy": strategy,
        "rule": "round-robin clips, fixed evenly spaced fully labeled frames before model inference",
        "frames": [
            {
                "frame_id": s["clip"]["info"]["name"] + "_" + Path(s["image"]["file_name"]).stem,
                "split": s["split"],
                "game_id": s["clip"]["game_id"],
            }
            for s in selected
        ],
    }
    selection_path = root / "selection.json"
    if selection_path.exists() and read_json(selection_path) != selection:
        raise ValueError("Frozen frame selection changed")
    write_json(selection_path, selection)
    for split in ("train", "val"):
        for directory in (
            f"images/{split}",
            f"labels/{split}",
            f"roles/images/{split}",
            f"roles/labels/{split}",
            f"field/{'train' if split == 'train' else 'valid'}",
            f"attributes/{split}",
        ):
            (root / directory).mkdir(parents=True, exist_ok=True)
    frames = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for row in pool.map(lambda s: prepare_frame(root, archives, s), selected):
            frames.append(row)
            if len(frames) % 50 == 0 or len(frames) == len(selected):
                print(f"Images {len(frames)}/{len(selected)}: {row['frame_id']}", flush=True)
                write_json(root / "progress.json", {"completed": len(frames), "total": len(selected)})
    for split, field_split in (("train", "train"), ("val", "valid")):
        match_info = {}
        clip_info = {c["info"]["name"]: c["info"] for c in clips}
        for row in frames:
            if row["split"] == split:
                moment = int(clip_info[row["clip"]]["clip_start"]) + row["source_frame_index"] * 40
                match_info[Path(row["image"]).name] = {
                    "league": "SN-GSR-2024",
                    "season": "v1.3",
                    "date": "provider",
                    "match": "game-" + row["game_id"],
                    "ms_time": moment,
                    "replay_time": moment,
                }
        write_json(root / "field" / field_split / "match_info.json", match_info)
    for filename, base, names in (
        ("data.yaml", root, NAMES),
        ("data-roles.yaml", root / "roles", ROLE_NAMES),
    ):
        (root / filename).write_text(
            yaml.safe_dump(
                {"path": str(base), "train": "images/train", "val": "images/val", "names": names},
                sort_keys=False,
            ),
            encoding="utf-8",
        )
    manifest = {
        "schema_version": 1,
        "dataset_version": root.name,
        "source": DATASET_URL,
        "source_revision": REVISION,
        "license_metadata": "GPL-3.0 on provider repository; no independent broadcast rights claim",
        "selection": {k: v for k, v in selection.items() if k != "frames"},
        "names": NAMES,
        "role_names": ROLE_NAMES,
        "frames": frames,
        "counts": dict(Counter(r["split"] for r in frames)),
        "match_counts": {s: len({r["game_id"] for r in frames if r["split"] == s}) for s in ("train", "val")},
        "project_human_review_completed": False,
        "test_accessed": False,
        "pretraining_overlap_with_field_model": "not excluded",
    }
    manifest["fingerprint"] = digest_json(manifest)
    result = audit(root, manifest)
    write_json(existing, manifest)
    return result


def main():
    """Lees de datasetbouw- of auditopdracht en voer de gevraagde corpusstap met de gekozen aantallen en
    workers uit.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/broadcast-sngsr-v1"))
    parser.add_argument("--train", type=int, default=6000)
    parser.add_argument("--val", type=int, default=2000)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.audit_only:
        result = audit(root, read_json(root / "manifest.json"))
    else:
        result = prepare(root, args.train, args.val, args.workers)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
