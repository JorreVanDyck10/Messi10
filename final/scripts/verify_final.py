"""Check the packaged files and dataset with only the Python standard library."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    errors = []
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        if not path.is_file() or sha256(path) != entry["sha256"]:
            errors.append(f"Missing or changed file: {entry['path']}")
    dataset = ROOT / "datasets/school-ball80-review-v1"
    frames = json.loads((dataset / "manifest.json").read_text(encoding="utf-8"))["frames"]
    splits = {split: [row for row in frames if row["split"] == split] for split in ("train", "val")}
    if len(frames) != 80 or len(splits["train"]) != 48 or len(splits["val"]) != 32:
        errors.append("Expected 80 review frames: 48 train and 32 validation")
    if {r["group_id"] for r in splits["train"]} & {r["group_id"] for r in splits["val"]}:
        errors.append("Training and validation groups overlap")
    for row in frames:
        for kind in ("image", "label"):
            path = dataset / row[kind]
            if not path.is_file() or sha256(path) != row[f"initial_{kind}_sha256"]:
                errors.append(f"Changed initial {kind}: {row['frame_id']}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"OK: {len(manifest['files'])} files verified; 80 image/label pairs; no train/val group overlap.")
    print("Dataset reviews remain open; software checks do not establish model accuracy.")


if __name__ == "__main__":
    main()
