"""Bouwt aanvullende scheidsrechterdata met expliciete negatieve voorbeelden en gescheiden clips."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import re
import threading
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
import yaml
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .contracts import digest_json, read_json, sha256_file, write_json

REPOSITORY = "infactory-ai/referee-tracking"
REVISION = "094370666a599016e2e0646525b148046a023498"
SOURCE = f"https://huggingface.co/datasets/{REPOSITORY}"
LOCAL = threading.local()


def source_bytes(path, files):
    entry = files[path]
    if not isinstance(path, str) or path.startswith("/") or ".." in Path(path).parts:
        raise ValueError("Provider paths must be safe relative strings")
    if not hasattr(LOCAL, "session"):
        LOCAL.session = requests.Session()
        LOCAL.session.mount(
            "https://",
            HTTPAdapter(
                max_retries=Retry(
                    total=4,
                    backoff_factor=2,
                    status_forcelist=(429, 500, 502, 503, 504),
                    respect_retry_after_header=True,
                )
            ),
        )
    with LOCAL.session.get(f"{SOURCE}/resolve/{REVISION}/{path}", timeout=60) as response:
        response.raise_for_status()
        raw = response.content
    if len(raw) != entry["size"]:
        raise ValueError("Provider file size changed")
    if entry.get("lfs"):
        if hashlib.sha256(raw).hexdigest() != entry["lfs"]["sha256"]:
            raise ValueError("Provider SHA-256 mismatch")
    elif hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != entry["blobId"]:
        raise ValueError("Provider Git blob mismatch")
    return raw


def clip_split(rows):
    groups = defaultdict(Counter)
    for row in rows:
        groups[row["video_source"]][row["visibility"]] += 1
    if len(groups) < 4:
        raise ValueError("Need at least four distinct source clips")
    totals = Counter(row["visibility"] for row in rows)
    candidates = []
    for subset in itertools.combinations(sorted(groups), max(2, round(len(groups) * 0.25))):
        counts = sum((groups[g] for g in subset), Counter())
        if any(not 0 < counts[k] < totals[k] for k in ("visible", "not_visible")):
            continue
        score = sum(abs(counts[k] / totals[k] - 0.25) for k in totals)
        candidates.append((score, digest_json(["referee-broadcast-v1", subset]), subset))
    if not candidates:
        raise ValueError("Cannot construct both positive and negative clip-separated development splits")
    valid = set(min(candidates)[2])
    return {g: "val" if g in valid else "train" for g in groups}


def download_row(root, files, row, split, forbidden_hashes):
    from persoon1.core import read_labels

    path = row["file_path"]
    if not re.fullmatch(r"data/(visible|not_visible)/[0-9a-f-]+_\d+\.jpg", path):
        raise ValueError("Unsafe image path in provider metadata")
    stem = Path(path).stem
    if stem.rsplit("_", 1)[0] != row["video_source"] or Path(path).parts[1] != row["visibility"]:
        raise ValueError("Metadata source/visibility does not match image path")
    raw_image = root / "provider" / path
    raw_image.parent.mkdir(parents=True, exist_ok=True)
    if not raw_image.exists():
        raw_image.write_bytes(source_bytes(path, files))
    raw = raw_image.read_bytes()
    entry = files[path]
    expected_hash = (entry.get("lfs") or {}).get("sha256")
    if (
        len(raw) != entry["size"]
        or (expected_hash and hashlib.sha256(raw).hexdigest() != expected_hash)
        or (
            not expected_hash
            and hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != entry["blobId"]
        )
    ):
        raise ValueError("Existing provider image changed")
    image_hash = hashlib.sha256(raw).hexdigest()
    if image_hash in forbidden_hashes:
        return {"excluded": path, "reason": "exact overlap with existing SoccerNet corpus"}
    with Image.open(io.BytesIO(raw)) as decoded:
        width, height = decoded.size
        decoded.load()
    image = root / "images" / split / (stem + ".jpg")
    label = root / "labels" / split / (stem + ".txt")
    if row["visibility"] == "visible":
        label_member = str(Path(path).with_suffix(".txt")).replace("\\", "/")
        raw_label = root / "provider" / label_member
        if not raw_label.exists():
            raw_label.write_bytes(source_bytes(label_member, files))
        expected = files[label_member]
        label_bytes = raw_label.read_bytes()
        if (
            hashlib.sha1(b"blob " + str(len(label_bytes)).encode() + b"\0" + label_bytes).hexdigest()
            != expected["blobId"]
        ):
            raise ValueError("Provider label checksum mismatch")
        parsed = read_labels(raw_label, 1)
        if len(parsed) != int(row["bboxes_count"]) or not parsed:
            raise ValueError("Visible-frame label count differs from provider metadata")
        content = raw_label.read_text(encoding="utf-8-sig")
    elif row["visibility"] == "not_visible" and int(row["bboxes_count"]) == 0:
        parsed, content = [], ""
    else:
        raise ValueError("Negative frame is not explicitly confirmed by provider metadata")
    for folder in (image.parent, label.parent):
        folder.mkdir(parents=True, exist_ok=True)
    if not image.exists():
        image.hardlink_to(raw_image)
    if label.exists() and label.read_text(encoding="utf-8") != content:
        raise ValueError("Existing exported labels changed; preserve corrections in a new version")
    label.write_text(content, encoding="utf-8")
    return {
        "frame_id": stem,
        "source_clip_id": row["video_source"],
        "split": split,
        "image": image.relative_to(root).as_posix(),
        "label": label.relative_to(root).as_posix(),
        "width": width,
        "height": height,
        "image_sha256": image_hash,
        "label_sha256": sha256_file(label),
        "box_count": len(parsed),
        "visibility": row["visibility"],
        "frame_index": int(row["frame_index"]),
        "source_provenance": "Infactory published annotations; provider reports manual verification",
        "project_human_review_completed": False,
    }


def prepare(root, workers=8):
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        f"https://huggingface.co/api/datasets/{REPOSITORY}/revision/{REVISION}?blobs=true", timeout=60
    )
    response.raise_for_status()
    inventory = response.json()
    if inventory["sha"] != REVISION:
        raise ValueError("Provider repository revision changed")
    files = {f["rfilename"]: f for f in inventory["siblings"]}
    for name in ("README.md", "metadata.csv", "dataset_info.json"):
        (root / name).write_bytes(source_bytes(name, files))
    rows = list(csv.DictReader(io.StringIO((root / "metadata.csv").read_text(encoding="utf-8-sig"))))
    if len(rows) != 1450 or len({r["file_path"] for r in rows}) != len(rows):
        raise ValueError("Unexpected provider sample count or duplicate metadata")
    assignment = clip_split(rows)
    selection = {
        "revision": REVISION,
        "split_unit": "source_clip_UUID",
        "assignment": assignment,
        "match_identity_verified": False,
        "source": SOURCE,
    }
    frozen = root / "selection.json"
    if frozen.exists() and read_json(frozen) != selection:
        raise ValueError("Frozen clip split changed")
    write_json(frozen, selection)
    existing = Path("data/broadcast-sngsr-v1/manifest.json")
    hashes = {r["image_sha256"] for r in read_json(existing)["frames"]} if existing.exists() else set()
    frames, excluded = [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(
            lambda r: download_row(root, files, r, assignment[r["video_source"]], hashes), rows
        ):
            if "excluded" in result:
                excluded.append(result)
            else:
                frames.append(result)
            if (len(frames) + len(excluded)) % 100 == 0:
                print(f"Referee frames {len(frames) + len(excluded)}/{len(rows)}", flush=True)
    seen, unique = {}, []
    for row in frames:
        if row["image_sha256"] in seen:
            excluded.append(
                {
                    "frame_id": row["frame_id"],
                    "reason": "exact duplicate",
                    "duplicate_of": seen[row["image_sha256"]],
                }
            )
            (root / row["image"]).unlink()
            (root / row["label"]).unlink()
        else:
            seen[row["image_sha256"]] = row["frame_id"]
            unique.append(row)
    manifest = {
        "source": SOURCE,
        "source_revision": REVISION,
        "license": "CC-BY-NC-4.0",
        "credit": "Infactory: Valentino Constantinou, Mehdi Iranmanesh, John Kanalakis",
        "names": {0: "referee"},
        "frames": unique,
        "excluded": excluded,
        "counts": dict(Counter(r["split"] for r in unique)),
        "visibility_counts": dict(Counter(r["visibility"] for r in unique)),
        "box_count": sum(r["box_count"] for r in unique),
        "selection": selection,
        "match_independence_verified": False,
        "purpose": "Separate auxiliary referee task; never merged automatically with player training",
        "project_human_review_completed": False,
    }
    manifest["fingerprint"] = digest_json(manifest)
    write_json(root / "manifest.json", manifest)
    (root / "data.yaml").write_text(
        yaml.safe_dump(
            {"path": str(root), "train": "images/train", "val": "images/val", "names": {0: "referee"}},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return {k: manifest[k] for k in ("counts", "visibility_counts", "box_count", "fingerprint")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/referee-broadcast-v1"))
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    print(prepare(args.root, args.workers))
