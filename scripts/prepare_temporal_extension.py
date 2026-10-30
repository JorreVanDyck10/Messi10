"""Preregister middle/last six-second windows in the six existing development clips."""

import gzip
import json
import zipfile
import zlib
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.broadcast_data import labelled_people
from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.course_dataset import REVISION, archive_url
from football_pipeline.research_archive import RangeArchive

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/broadcast-temporal-v2"
WINDOWS = {"middle": (301, 450), "last": (601, 750)}


def prepare_clip(task):
    split, catalog, selection = task
    clip = catalog["info"]["name"]
    source = ROOT / "data/broadcast-pitch-v1/provider-labels" / f"{clip}.json.gz"
    provider = json.loads(gzip.decompress(source.read_bytes()))
    annotations = defaultdict(list)
    for annotation in provider["annotations"]:
        annotations[str(annotation["image_id"])].append(annotation)
    images = {int(Path(im["file_name"]).stem): im for im in provider["images"]}
    frames, pending = [], []
    for position, (first, last) in WINDOWS.items():
        name = clip + "-" + position
        directory = OUTPUT / name
        directory.mkdir(parents=True, exist_ok=True)
        record = directory / "manifest.json"
        if record.exists():
            saved = read_json(record)
            if saved["selection_digest"] != digest_json(selection):
                raise ValueError("Window selection changed")
            for row in saved["frames"]:
                if sha256_file(row["image"]) != row["image_sha256"] or (
                    row["field_label"] and sha256_file(row["field_label"]) != row["field_label_sha256"]
                ):
                    raise ValueError("Saved extension frame or field label changed")
            frames.extend(saved["frames"])
        else:
            pending.append((position, first, last, directory, record))
    if not pending:
        return frames
    with RangeArchive(
        archive_url("train" if split == "train" else "valid"), budget_bytes=256 * 1024**2
    ) as remote:
        with zipfile.ZipFile(remote) as archive:
            for position, first, last, directory, record in pending:
                window = []
                for number in range(first, last + 1):
                    image = images[number]
                    name = image["file_name"]
                    if (
                        Path(name).name != name
                        or not image.get("has_labeled_person")
                        or image.get("ignore_regions_x")
                        or image.get("ignore_regions_y")
                    ):
                        raise ValueError("Fixed window is not fully person-labelled or has unsafe filenames")
                    member = catalog["member"].rsplit("/", 1)[0] + "/img1/" + name
                    info = archive.getinfo(member)
                    target = directory / name
                    valid = target.exists() and zlib.crc32(target.read_bytes()) == info.CRC
                    if not valid:
                        raw = archive.read(member)
                        decoded = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
                        if decoded is None or decoded.shape[:2] != (image["height"], image["width"]):
                            raise ValueError("Downloaded pixels disagree with provider dimensions")
                        temporary = target.with_suffix(".jpg.partial")
                        temporary.write_bytes(raw)
                        temporary.replace(target)
                    people = annotations[str(image["image_id"])]
                    pitch = next((a["lines"] for a in people if a.get("supercategory") == "pitch"), None)
                    field_label = directory / (Path(name).stem + ".field.json")
                    if pitch:
                        write_json(field_label, pitch)
                    window.append(
                        {
                            "frame_id": clip + "_" + Path(name).stem,
                            "clip": clip + "-" + position,
                            "provider_clip": clip,
                            "window": position,
                            "game_id": catalog["game_id"],
                            "split": split,
                            "frame_index": number - first,
                            "source_frame_index": number - 1,
                            "fps": int(catalog["info"]["frame_rate"]),
                            "image": str(target),
                            "image_sha256": sha256_file(target),
                            "width": image["width"],
                            "height": image["height"],
                            "people": labelled_people(people, image["width"], image["height"]),
                            "provider_sha256": sha256_file(source),
                            "field_label": str(field_label) if pitch else None,
                            "field_label_sha256": sha256_file(field_label) if pitch else None,
                            "label_policy": "provider_visible_polylines_v1",
                            "archive_member": member,
                            "archive_crc32": f"{info.CRC:08x}",
                        }
                    )
                    if len(window) % 50 == 0:
                        print(clip, position, len(window), "/150", flush=True)
                write_json(record, {"selection_digest": digest_json(selection), "frames": window})
                frames.extend(window)
    return frames


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    old = read_json(ROOT / "data/broadcast-temporal-v1/manifest.json")
    games = read_json(ROOT / "data/broadcast-pitch-v1/selection.json")["games"]
    selection = {
        "revision": REVISION,
        "source_clips": old["selection"]["clips"],
        "source_manifest_sha256": sha256_file(ROOT / "data/broadcast-temporal-v1/manifest.json"),
        "windows": {k: list(v) for k, v in WINDOWS.items()},
        "rule": "Fixed frames301–450 and601–750; same first clip per previously selected game; no outcome-based window selection",
        "test_accessed": False,
        "independent_final_test": False,
        "human_review_completed": False,
        "training_performed": False,
    }
    path = OUTPUT / "selection.json"
    if path.exists() and read_json(path) != selection:
        raise ValueError("Preregistered windows changed")
    write_json(path, selection)
    write_json(ROOT / "reports/broadcast-reliability-20261030/temporal-extension-selection.json", selection)
    tasks = []
    for split, archive in (("train", "train"), ("val", "valid")):
        catalog = read_json(ROOT / f"data/course-multimatch-v1/catalog-{archive}.json")["clips"]
        for game in games[split]:
            chosen = sorted((c for c in catalog if c["game_id"] == game), key=lambda c: c["info"]["name"])[0]
            if chosen["info"]["name"] not in selection["source_clips"]:
                raise ValueError("Extension must use exactly the existing source clips")
            tasks.append((split, chosen, selection))
    with ThreadPoolExecutor(max_workers=3) as pool:
        frames = [r for group in pool.map(prepare_clip, tasks) for r in group]
    frames.sort(key=lambda r: (r["split"], r["clip"], r["frame_index"]))
    old_ids = {r["frame_id"] for r in old["frames"]}
    if len(frames) != 1800 or any(r["frame_id"] in old_ids for r in frames):
        raise ValueError("Extension overlaps the first windows or is incomplete")
    train = {r["image_sha256"] for r in frames if r["split"] == "train"}
    val = {r["image_sha256"] for r in frames if r["split"] == "val"}
    if train & val:
        raise ValueError("Identical pixels cross training/validation split")
    result = {"selection": selection, "frames": frames, "fingerprint": digest_json(frames)}
    write_json(OUTPUT / "manifest.json", result)
    print(
        {
            "frames": len(frames),
            "fingerprint": result["fingerprint"],
            "field_labels": sum(bool(r["field_label"]) for r in frames),
        },
        flush=True,
    )


if __name__ == "__main__":
    main()
