"""Independently verify derived training pixels and original-ball coordinate matches."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.video import ROOT


def main():
    """Vergelijk afgeleide tegelpixels en terugvertaalde ballabels met de oorspronkelijke trainings- en
    validatiebeelden.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Keep previous audit; choose a new output")
    data = read_json(args.dataset / "source.json")
    source = ROOT / "assets/annotations/football-fullscene60"
    manifest = read_json(source / "manifest.json")
    annotations = {f["frame_id"]: f for f in read_json(source / "source-annotations.json")["frames"]}
    frames = {f["frame_id"]: f for f in manifest["frames"]}
    assert sha256_file(source / "manifest.json") == data["manifest_sha256"]
    assert sha256_file(source / "source-annotations.json") == data["annotations_sha256"]
    current, pixels, unique, derived_hash_splits, checked = None, None, set(), {}, []
    for row in data["rows"]:
        f = frames[row["frame_id"]]
        assert row["split"] == f["split"] and row["group"] == f["group_id"]
        if current != row["frame_id"]:
            original = source / f["image"]
            assert sha256_file(original) == f["image_sha256"]
            pixels = cv2.imread(str(original))
            current = row["frame_id"]
        image, label = args.dataset / row["image"], args.dataset / row["label"]
        digest = sha256_file(image)
        assert digest == row["image_sha256"] and sha256_file(label) == row["label_sha256"]
        assert derived_hash_splits.setdefault(digest, row["split"]) == row["split"]
        x, y, right, bottom = row["window_xyxy"]
        assert np.array_equal(cv2.imread(str(image)), pixels[y:bottom, x:right])
        objects = [(j, a) for j, a in enumerate(annotations[current]["objects"]) if a["class_id"] == 1]
        expected = [
            (j, a)
            for j, a in objects
            if min(a["xyxy"][2], right) > max(a["xyxy"][0], x)
            and min(a["xyxy"][3], bottom) > max(a["xyxy"][1], y)
        ]
        for _, a in expected:
            aa, bb, cc, dd = a["xyxy"]
            assert x <= aa < cc <= right and y <= bb < dd <= bottom
        lines = label.read_text(encoding="utf-8").splitlines()
        assert len(lines) == len(expected) == row["balls"]
        for line, (j, obj) in zip(lines, expected):
            cls, cx, cy, width, height = map(float, line.split())
            assert cls == 32 and width > 0 and height > 0
            original_box = [
                x + (cx - width / 2) * (right - x),
                y + (cy - height / 2) * (bottom - y),
                x + (cx + width / 2) * (right - x),
                y + (cy + height / 2) * (bottom - y),
            ]
            assert max(abs(a - b) for a, b in zip(original_box, obj["xyxy"])) < 0.001
            unique.add((current, j, row["split"]))
        checked.append({"image": row["image"], "split": row["split"], "balls": len(lines)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(
        args.output,
        {
            "status": "passed",
            "pixel_identical_native_tiles": len(checked),
            "splits": dict(Counter(r["split"] for r in checked)),
            "tile_ball_instances": {
                s: sum(r["balls"] for r in checked if r["split"] == s) for s in ["train", "val"]
            },
            "unique_original_ball_labels_covered": dict(Counter(s for _, _, s in unique)),
            "negative_tiles": dict(Counter(r["split"] for r in checked if r["balls"] == 0)),
            "source_coordinates_agree": True,
            "source_groups_preserved": True,
            "human_review_completed": False,
            "script_sha256": sha256_file(__file__),
        },
    )
    print("Verified", len(checked), "pixel-identical training/validation tiles")


if __name__ == "__main__":
    main()
