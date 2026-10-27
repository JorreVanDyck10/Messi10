"""Fetch the published P1 models/data into a NEW LFS storage and verify actual loads."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import cv2

from football_pipeline.appearance import ROLE_NAMES, AppearanceClassifier
from football_pipeline.contracts import sha256_file, write_json
from football_pipeline.video import ROOT
from persoon1.modeling import yolo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cache = args.cache.resolve()
    if cache.exists() or args.output.exists():
        raise ValueError("Use a new LFS cache and report; previous verification is preserved")
    cache.mkdir(parents=True)
    includes = (
        "artifacts/appearance-v3/*.pt,artifacts/football48-ball-v2/*.pt,datasets/roles-teams-v3/sources/*"
    )
    command = [
        "git",
        "-c",
        f"lfs.storage={cache}",
        "lfs",
        "fetch",
        "origin",
        args.revision,
        f"--include={includes}",
        "--exclude=",
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    files = [
        *sorted((ROOT / "artifacts/appearance-v3").glob("*.pt")),
        *sorted((ROOT / "artifacts/football48-ball-v2").glob("*.pt")),
        *sorted((ROOT / "datasets/roles-teams-v3/sources").glob("*")),
    ]
    checked = cache / "checked"
    checked.mkdir()
    results = []
    yolo(ROOT / "models/yolo11n.pt")
    for path in files:
        digest = sha256_file(path)
        fetched = cache / "objects" / digest[:2] / digest[2:4] / digest
        if (
            not fetched.is_file()
            or sha256_file(fetched) != digest
            or fetched.stat().st_size != path.stat().st_size
        ):
            raise ValueError(f"Remote LFS object missing or changed: {path}")
        target = checked / path.name
        shutil.copy2(fetched, target)
        item = {"path": path.relative_to(ROOT).as_posix(), "sha256": digest, "bytes": fetched.stat().st_size}
        if path.suffix == ".pt" and path.parent.name == "appearance-v3":
            classifier = AppearanceClassifier(
                {"weights": str(target), "weights_sha256": digest, "model_id": path.stem, "device": "cpu"}
            )
            assert classifier.role_head.out_features == len(ROLE_NAMES)
            item.update(
                kind="crop_role_classifier",
                actual_role_names=ROLE_NAMES,
                role_colour_scale=classifier.colour_scale,
            )
            del classifier
        elif path.suffix == ".pt":
            model = yolo(target)
            assert len(model.names) == 80 and model.names[0] == "person" and model.names[32] == "sports ball"
            item.update(kind="yolo_detector", actual_names=model.names)
            del model
        else:
            image = cv2.imread(str(target))
            if image is None:
                raise ValueError("Downloaded source image cannot be decoded")
            item.update(kind="source_image", decoded_size=[image.shape[1], image.shape[0]])
        results.append(item)
    write_json(
        args.output,
        {
            "recorded_at": datetime.now(UTC).isoformat(),
            "published_asset_revision": args.revision,
            "new_lfs_storage": str(cache),
            "files": results,
            "count": len(results),
            "all_remote_bytes_and_loads_verified": True,
            "human_accuracy_review": False,
        },
    )
    print(f"Verified {len(results)} freshly fetched model/image objects")


if __name__ == "__main__":
    main()
