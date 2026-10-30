"""Learn role context from genuine detector crops matched to provider annotations.

Unmatched predictions participate in scene context but never become invented
role labels. The fixed SoccerNet validation matches remain development-only.
"""

from __future__ import annotations

import argparse
import gzip
import json
import time
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
import torch
from scipy.optimize import linear_sum_assignment

from .automatic_calibration import project_automatic
from .broadcast_evaluation import reference_geometry
from .contracts import digest_json, read_json, sha256_file, write_json
from .detection import UltralyticsDetector, load_model_manifest
from .role_context import context_features, context_head
from .video import ROOT


def matched_targets(detections, people, minimum_iou=0.5):
    """One-to-one source labels; unmatched boxes receive no supervision."""
    targets = np.full(len(detections), -1, np.int64)
    teams = np.full(len(detections), "", dtype="<U5")
    if not detections or not people:
        return targets, teams
    a, b = np.array([d.bbox_xyxy for d in detections]), np.array([p["bbox"] for p in people])
    intersection = np.maximum(
        0, np.minimum(a[:, None, 2:], b[None, :, 2:]) - np.maximum(a[:, None, :2], b[None, :, :2])
    ).prod(2)
    union = (a[:, 2:] - a[:, :2]).prod(1)[:, None] + (b[:, 2:] - b[:, :2]).prod(1) - intersection
    overlap = np.divide(intersection, union, out=np.zeros_like(intersection), where=union > 0)
    for i, j in zip(*linear_sum_assignment(-overlap)):
        if overlap[i, j] >= minimum_iou:
            targets[i] = int(people[j]["role"] != "player")
            teams[i] = (people[j].get("team") or "") if not people[j].get("goalkeeper") else ""
    return targets, teams


def scene_features(detections, size):
    return context_features(
        [d.role_probabilities for d in detections],
        [d.team_embedding for d in detections],
        [d.context_embedding for d in detections],
        [d.field_position for d in detections],
        [d.bbox_xyxy for d in detections],
        size,
    )


def collect(dataset, profile, output):
    torch.set_num_threads(4)
    # Leave room for the independent detector fine-tuning process on this GPU.
    torch.cuda.set_per_process_memory_fraction(0.45)
    dataset, output = Path(dataset).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest, models = read_json(dataset / "manifest.json"), load_model_manifest(profile)
    if any(r["split"] not in {"train", "val"} for r in manifest["frames"]):
        raise ValueError("Reserved images cannot enter observed context training")
    context = torch.load(models["role_context"]["weights"], map_location="cpu", weights_only=True)
    code = {
        name: sha256_file(Path(__file__).with_name(name + ".py"))
        for name in (
            "broadcast_observed_context",
            "broadcast_evaluation",
            "detection",
            "appearance",
            "kit_embedding",
            "role_context",
            "video_teams",
            "automatic_calibration",
            "participants",
        )
    }
    identity = digest_json([manifest["fingerprint"], models, code])
    record_path = output / "inputs.json"
    if record_path.exists() and read_json(record_path)["identity"] != identity:
        raise ValueError("Observed context inputs changed; choose another output")
    write_json(
        record_path,
        {
            "identity": identity,
            "dataset_fingerprint": manifest["fingerprint"],
            "profile": models,
            "test_accessed": False,
            "independent_final_test": False,
            "labels": "One-to-one provider box IoU >= .5; unmatched predictions ignored for supervision",
        },
    )
    detector = UltralyticsDetector(models)
    grouped = defaultdict(list)
    for row in manifest["frames"]:
        grouped[row["clip"]].append(row)
    files = {}
    for clip, rows in grouped.items():
        path = output / (clip + ".npz")
        if path.exists():
            if str(np.load(path)["identity"]) != identity:
                raise ValueError("Observed clip cache changed")
            files[path.name] = sha256_file(path)
            continue
        detector.set_video_identity(clip)
        provider = json.loads(
            gzip.decompress((dataset / "provider-labels" / (clip + ".json.gz")).read_bytes())
        )
        image_ids = {Path(im["file_name"]).stem: str(im["image_id"]) for im in provider["images"]}
        annotations = defaultdict(list)
        for a in provider["annotations"]:
            annotations[str(a["image_id"])].append(a)
        features, targets = [], []
        for row in rows:
            image = cv2.imread(row["image"])
            if image is None or sha256_file(row["image"]) != row["image_sha256"]:
                raise ValueError("Observed context source image changed")
            geometry = reference_geometry(
                annotations[image_ids[row["frame_id"].rsplit("_", 1)[1]]], row["width"], row["height"]
            )
            if geometry["status"] != "valid":
                continue
            found = detector.detect(image, row["frame_index"])

            def project(d):
                project_automatic(d, geometry, (row["width"], row["height"]))

            for d in found:
                project(d)
            detector.classify_on_pitch(image, found, projector=project)
            found = [
                d
                for d in found
                if d.projection_status == "valid"
                and d.confidence >= 0.25
                and d.role_probabilities is not None
                and d.team_embedding is not None
                and d.context_embedding is not None
            ]
            if len(found) < 4:
                continue
            y, teams = matched_targets(found, row["people"])
            mask = y >= 0
            features.append(scene_features(found, (row["width"], row["height"]))[mask])
            targets.append(y[mask])
            if row["split"] == "train":
                original = np.array([d.role_probabilities for d in found])
                for side in ("left", "right", "official"):
                    for i, d in enumerate(found):
                        d.role_probabilities = original[i].tolist()
                        if side == "official" and y[i] == 1:
                            d.role_probabilities = [0.98, 0.01, 0.01]
                        elif teams[i] == side and y[i] == 0:
                            d.role_probabilities = [0.02, 0.96, 0.02]
                    features.append(scene_features(found, (row["width"], row["height"]))[mask])
                    targets.append(y[mask])
        if not targets:
            raise ValueError("Clip has no labelled observed context")
        np.savez_compressed(
            path,
            x=np.concatenate(features),
            y=np.concatenate(targets),
            split=rows[0]["split"],
            identity=identity,
        )
        files[path.name] = sha256_file(path)
        print(
            "Observed context",
            clip,
            rows[0]["split"],
            sum(map(len, targets)),
            "labelled predictions",
            flush=True,
        )
    torch.save(
        {
            "cnn_center": context["cnn_center"],
            "cnn_projection": context["cnn_projection"],
            "teacher_sha256": context["teacher_sha256"],
            "kit_weights_sha256": context["kit_weights_sha256"],
        },
        output / "projection.pt",
    )
    write_json(
        output / "complete.json",
        {"identity": identity, "files": files, "projection_sha256": sha256_file(output / "projection.pt")},
    )
    return output


def train(cache, output, epochs=50):
    torch.set_num_threads(4)
    torch.manual_seed(42)
    cache, output = Path(cache).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    inputs = read_json(cache / "inputs.json")
    complete = read_json(cache / "complete.json")
    if complete["identity"] != inputs["identity"] or complete["projection_sha256"] != sha256_file(
        cache / "projection.pt"
    ):
        raise ValueError("Observed context collection is incomplete or projection changed")
    groups = {key: [[], []] for key in ("train", "val")}
    for name, checksum in sorted(complete["files"].items()):
        path = cache / name
        if sha256_file(path) != checksum:
            raise ValueError("Observed clip cache changed")
        source = np.load(path)
        if str(source["identity"]) != inputs["identity"]:
            raise ValueError("Observed feature cache changed")
        split = str(source["split"])
        if split not in groups:
            raise ValueError("Reserved split in observed context features")
        groups[split][0].append(source["x"])
        groups[split][1].append(source["y"])
    x, y = (np.concatenate(v) for v in groups["train"])
    xv, yv = (np.concatenate(v) for v in groups["val"])
    mean, std = x.mean(0), x.std(0).clip(0.05)
    x, y, xv = (
        torch.from_numpy((x - mean) / std),
        torch.from_numpy(y).float(),
        torch.from_numpy((xv - mean) / std),
    )
    model = context_head()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    best, curve, started = None, [], time.monotonic()
    for epoch in range(1, epochs + 1):
        model.train()
        order = torch.randperm(len(x))
        for start in range(0, len(x), 1024):
            indices = order[start : start + 1024]
            logits = model(x[indices] + 0.02 * torch.randn_like(x[indices])).squeeze(1)
            loss = torch.nn.functional.binary_cross_entropy_with_logits(
                logits, y[indices], pos_weight=torch.tensor(3.0)
            )
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.inference_mode():
            q = model(xv).sigmoid().numpy().ravel()
        row = {
            "epoch": epoch,
            "rejected_players": int(((q >= 0.99) & (yv == 0)).sum()),
            "rejected_nonplayers": int(((q >= 0.99) & (yv == 1)).sum()),
            "positive_players": int(((q <= 0.05) & (yv == 0)).sum()),
            "positive_nonplayers": int(((q <= 0.05) & (yv == 1)).sum()),
        }
        score = (
            row["rejected_nonplayers"]
            - 3 * row["rejected_players"]
            + 0.05 * row["positive_players"]
            - 3 * row["positive_nonplayers"]
        )
        curve.append(row)
        if best is None or score > best[0]:
            best = score, {k: v.detach().clone() for k, v in model.state_dict().items()}, row
        if epoch % 5 == 0:
            print(row, flush=True)
    projection = torch.load(cache / "projection.pt", map_location="cpu", weights_only=True)
    torch.save(
        {
            **projection,
            "format": "pitch-role-context-v1",
            "input_dimension": 46,
            "state_dict": best[1],
            "mean": torch.from_numpy(mean),
            "std": torch.from_numpy(std),
            "selection": best[2],
        },
        output / "role_context.pt",
    )
    write_json(
        output / "metrics.json",
        {
            "selected": best[2],
            "curve": curve,
            "inputs": inputs,
            "train_rows": len(x),
            "val_rows": len(xv),
            "runtime_s": time.monotonic() - started,
            "weights_sha256": sha256_file(output / "role_context.pt"),
            "test_accessed": False,
            "independent_final_test": False,
            "selection": "Fixed .99 nonplayer / .95 player; validation development only",
        },
    )
    return output / "role_context.pt"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("collect", "train"))
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/broadcast-pitch-v1")
    parser.add_argument(
        "--profile",
        type=Path,
        default=ROOT / "artifacts/broadcast-role-context-v5/evaluation/context-fused-s/profile.json",
    )
    parser.add_argument("--cache", type=Path, default=ROOT / "artifacts/broadcast-observed-v8/cache")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/broadcast-observed-v8/training")
    args = parser.parse_args()
    print(
        collect(args.dataset, args.profile, args.cache)
        if args.action == "collect"
        else train(args.cache, args.output),
        flush=True,
    )
