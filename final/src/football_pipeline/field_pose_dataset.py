"""Build a match-separated field-pose dataset from published SoccerNet line annotations."""

from __future__ import annotations

import argparse
import copy
import os
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import yaml

from .contracts import digest_json, read_json, sha256_file, write_json
from .field_layout import POINTS_UV
from .field_learning import upstream_runtime, validate_labels

IDS = sorted(POINTS_UV)


def flip_indices():
    uv = np.array([POINTS_UV[i] for i in IDS])
    reflected = uv * [-1, 1] + [1, 0]
    distances = np.linalg.norm(reflected[:, None] - uv[None], axis=2)
    result = distances.argmin(axis=1).tolist()
    # Upstream rounds one central-circle landmark by 0.15 m; retain its pinned semantics.
    if max(distances[np.arange(len(IDS)), result]) > 0.002 or any(
        result[result[i]] != i for i in range(len(IDS))
    ):
        raise ValueError("Field semantics do not have a consistent left/right flip")
    return result


def worker_initialize(runtime):
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    upstream_runtime(Path(runtime))
    import torch

    torch.set_num_threads(1)
    cv2.setNumThreads(1)


def targets(row):
    import torch
    from utils.utils_keypoints import KeypointsDB

    try:
        labels = validate_labels(read_json(row["source_label"]))
        if "Goal left post left" in labels:
            labels["Goal left post left "] = labels.pop("Goal left post left")
        np.random.seed(int(sha256_file(row["source_label"])[:8], 16))
        db = KeypointsDB(copy.deepcopy(labels), torch.zeros(3, 540, 960))
        # No network predictions or dense heatmaps: geometric conversion of provider labels.
        db.get_full_keypoints()
        keypoints, visible = [], []
        for identifier in IDS:
            point = db.keypoints_final.get(identifier, {})
            x, y = float(point.get("x", -1)) / 960, float(point.get("y", -1)) / 540
            valid = (
                np.isfinite([x, y]).all()
                and 0 <= x < 1
                and 0 <= y < 1
                and db.mask_array[identifier - 1] > 0
                and point.get("proj_err", 0) <= db.proj_err_th
            )
            keypoints.append([x, y, 2] if valid else [0.0, 0.0, 0])
            if valid:
                visible.append((identifier, x, y))
        xy = np.array([[x, y] for _, x, y in visible], np.float32)
        uv = np.array([POINTS_UV[i] for i, _, _ in visible], np.float32)
        if (
            len(xy) < 6
            or cv2.contourArea(cv2.convexHull(xy)) < 0.001
            or cv2.contourArea(cv2.convexHull(uv)) < 0.0001
        ):
            return {**row, "excluded": "insufficient_noncollinear_provider_support"}
        planar = [p for name, pts in labels.items() if "Goal" not in name for p in pts]
        bounds = np.array([[p["x"], p["y"]] for p in planar])
        lower, upper = np.maximum(0, bounds.min(axis=0) - 0.025), np.minimum(1, bounds.max(axis=0) + 0.025)
        # Include all labeled keypoints; the box describes the visible field instance.
        lower, upper = np.minimum(lower, xy.min(axis=0)), np.maximum(upper, xy.max(axis=0))
        bbox = [*((lower + upper) / 2), *(upper - lower)]
        line = "0 " + " ".join(f"{float(n):.9f}" for n in [*bbox, *np.array(keypoints).ravel()]) + "\n"
        return {**row, "pose_label": line, "keypoints": keypoints, "visible_keypoints": len(visible)}
    except (ValueError, TypeError, KeyError, IndexError, np.linalg.LinAlgError, cv2.error) as exc:
        return {**row, "excluded": type(exc).__name__ + ": " + str(exc)}


def match_key(info):
    values = [str(info.get(k, "")).strip() for k in ("league", "season", "date", "match")]
    if not all(values):
        raise ValueError("A verified provider match identity is required")
    return digest_json(values)


def prepare(root, output, runtime, counts, workers=2):
    if (output / "manifest.json").exists():
        manifest = read_json(output / "manifest.json")
        for row in manifest["frames"]:
            for key in ("image", "label"):
                if sha256_file(output / row[key]) != row[key + "_sha256"]:
                    raise ValueError("Frozen pose dataset changed")
        return manifest
    output.mkdir(parents=True, exist_ok=True)
    pools, matches = {}, {}
    for split in ("train", "valid"):
        info = read_json(root / split / "match_info.json")
        groups = defaultdict(list)
        for filename, row in info.items():
            if int(row["ms_time"]) != int(row["replay_time"]):
                continue
            source = root / split / filename
            if source.is_file() and source.with_suffix(".json").is_file():
                groups[match_key(row)].append(
                    {
                        "source_image": str(source.resolve()),
                        "source_label": str(source.with_suffix(".json").resolve()),
                        "match_id": match_key(row),
                        "split": "val" if split == "valid" else "train",
                    }
                )
        matches[split] = set(groups)
        rng = np.random.default_rng(42)
        names = sorted(groups)
        rng.shuffle(names)
        for values in groups.values():
            rng.shuffle(values)
        # Equal match participation before sampling more frames from the same camera.
        pools[split] = [
            groups[name][i]
            for i in range(max(map(len, groups.values())))
            for name in names
            if i < len(groups[name])
        ]
    if matches["train"] & matches["valid"]:
        raise ValueError("Official match splits overlap")
    selected, exclusions = [], []
    with ProcessPoolExecutor(
        max_workers=workers, initializer=worker_initialize, initargs=(str(runtime),)
    ) as executor:
        for split, count in counts.items():
            image_dir, label_dir = output / "images" / split, output / "labels" / split
            image_dir.mkdir(parents=True, exist_ok=True)
            label_dir.mkdir(parents=True, exist_ok=True)
            accepted = 0
            pool = pools["valid" if split == "val" else "train"]
            for offset in range(0, len(pool), 64):
                if accepted >= count:
                    break
                for row in executor.map(targets, pool[offset : offset + 64]):
                    if "excluded" in row:
                        exclusions.append(row)
                        continue
                    if accepted >= count:
                        break
                    stem = split + "_" + Path(row["source_image"]).stem
                    image, label = image_dir / (stem + ".jpg"), label_dir / (stem + ".txt")
                    if not image.exists():
                        os.link(row["source_image"], image)
                    label.write_text(row.pop("pose_label"), encoding="utf-8")
                    row.update(
                        image=image.relative_to(output).as_posix(),
                        label=label.relative_to(output).as_posix(),
                        image_sha256=sha256_file(image),
                        label_sha256=sha256_file(label),
                        source_label_sha256=sha256_file(row["source_label"]),
                        annotation_provenance="Published SoccerNet lines; pinned upstream geometric keypoint derivation",
                        project_human_review_completed=False,
                    )
                    selected.append(row)
                    accepted += 1
                    if accepted % 64 == 0:
                        print(f"Pose data {split}: {accepted}/{count}", flush=True)
            if accepted != count:
                raise ValueError("Not enough eligible labeled frames")
    config = {
        "path": str(output.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {0: "football_field"},
        "kpt_shape": [len(IDS), 3],
        "flip_idx": flip_indices(),
        "kpt_names": {0: [str(i) for i in IDS]},
    }
    (output / "data.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "dataset_version": "field-pose-multicamera-v1",
        "frames": selected,
        "counts": counts,
        "source": "SoccerNet/SN-Calibration-2023",
        "provider_archive_inventory": read_json(root.parent / "dataset-inventory.json"),
        "ground_point_ids": IDS,
        "flip_idx": flip_indices(),
        "exclusions": exclusions,
        "cross_split_match_overlap": 0,
        "test_accessed": False,
        "project_human_review_completed": False,
        "pretraining_overlap_with_pnlcalib": True,
        "selection_seed": 42,
        "match_counts": {s: len({r["match_id"] for r in selected if r["split"] == s}) for s in counts},
    }
    manifest["fingerprint"] = digest_json(manifest)
    write_json(output / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/field-corpus/soccernet"))
    parser.add_argument("--output", type=Path, default=Path("data/field-pose-multicamera-v1"))
    parser.add_argument("--runtime", type=Path, default=Path(".tools/field-runtime.json"))
    parser.add_argument("--train", type=int, default=1024)
    parser.add_argument("--val", type=int, default=192)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    result = prepare(
        args.root, args.output, args.runtime, {"train": args.train, "val": args.val}, args.workers
    )
    print({k: result[k] for k in ("counts", "match_counts", "fingerprint")})
