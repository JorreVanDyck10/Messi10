"""Prepare fixed continuous windows from already selected development games."""

import gzip
import json
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from football_pipeline.broadcast_data import labelled_people
from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.course_dataset import REVISION, archive_url
from football_pipeline.research_archive import RangeArchive

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/broadcast-temporal-v1"


def prepare_clip(task):
    split, catalog = task
    clip = catalog["info"]["name"]
    directory = OUTPUT / clip
    directory.mkdir(parents=True, exist_ok=True)
    record = directory / "manifest.json"
    if record.exists():
        saved = read_json(record)
        for row in saved["frames"]:
            if sha256_file(row["image"]) != row["image_sha256"]:
                raise ValueError("Cached continuous frame changed")
        return saved["frames"]
    labels = ROOT / "data/broadcast-pitch-v1/provider-labels" / f"{clip}.json.gz"
    provider = json.loads(gzip.decompress(labels.read_bytes()))
    annotations = defaultdict(list)
    for annotation in provider["annotations"]:
        annotations[str(annotation["image_id"])].append(annotation)
    images = sorted(provider["images"], key=lambda r: int(Path(r["file_name"]).stem))
    window = []
    for image in images:
        number = int(Path(image["file_name"]).stem)
        valid = (
            image.get("has_labeled_person")
            and not image.get("ignore_regions_x")
            and not image.get("ignore_regions_y")
        )
        if not valid:
            window = []
            continue
        if window and number != int(Path(window[-1]["file_name"]).stem) + 1:
            window = []
        window.append(image)
        if len(window) == 150:
            break
    if len(window) != 150:
        raise ValueError(f"No complete continuous window in {clip}")
    archive_split = "train" if split == "train" else "valid"
    rows = []
    # Separate streams per clip: ZipFile seeks are never shared between threads.
    with RangeArchive(archive_url(archive_split), budget_bytes=256 * 1024**2) as remote:
        with zipfile.ZipFile(remote) as archive:
            for index, image in enumerate(window):
                name = image["file_name"]
                if Path(name).name != name:
                    raise ValueError("Unsafe image name")
                target = directory / name
                member = catalog["member"].rsplit("/", 1)[0] + "/img1/" + name
                if not target.exists():
                    target.write_bytes(archive.read(member))
                rows.append(
                    {
                        "frame_id": clip + "_" + Path(name).stem,
                        "clip": clip,
                        "game_id": catalog["game_id"],
                        "split": split,
                        "frame_index": index,
                        "source_frame_index": int(Path(name).stem) - 1,
                        "fps": int(catalog["info"]["frame_rate"]),
                        "image": str(target),
                        "image_sha256": sha256_file(target),
                        "width": image["width"],
                        "height": image["height"],
                        "people": labelled_people(
                            annotations[str(image["image_id"])], image["width"], image["height"]
                        ),
                        "provider_sha256": sha256_file(labels),
                    }
                )
        print(f"Prepared {clip}: {len(rows)} frames, {remote.downloaded} downloaded bytes", flush=True)
    write_json(record, {"frames": rows})
    return rows


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    tasks = []
    games = read_json(ROOT / "data/broadcast-pitch-v1/selection.json")["games"]
    for split, archive in (("train", "train"), ("val", "valid")):
        catalog = read_json(ROOT / f"data/course-multimatch-v1/catalog-{archive}.json")["clips"]
        for game in games[split]:
            chosen = sorted((c for c in catalog if c["game_id"] == game), key=lambda c: c["info"]["name"])[0]
            tasks.append((split, chosen))
    selection = {
        "revision": REVISION,
        "clips": [c["info"]["name"] for _, c in tasks],
        "rule": "first clip per previously selected game; first 150 continuous fully labelled frames",
        "test_accessed": False,
        "independent_final_test": False,
    }
    if (OUTPUT / "selection.json").exists() and read_json(OUTPUT / "selection.json") != selection:
        raise ValueError("Selection changed")
    write_json(OUTPUT / "selection.json", selection)
    with ThreadPoolExecutor(max_workers=6) as pool:
        frames = [row for rows in pool.map(prepare_clip, tasks) for row in rows]
    result = {"selection": selection, "frames": frames, "fingerprint": digest_json(frames)}
    write_json(OUTPUT / "manifest.json", result)
    print({"frames": len(frames), "fingerprint": result["fingerprint"]}, flush=True)


if __name__ == "__main__":
    main()
