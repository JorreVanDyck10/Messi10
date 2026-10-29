"""Voert aanvullende trainingen voor veldrollen, shirtkenmerken en detectie uit."""

from __future__ import annotations

import argparse
import copy
import time
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
import torch

from .appearance import PITCH_ROLE_NAMES, backbone, crop_tensor
from .broadcast_training import BASE_ROLES, team_metrics, team_selection_score
from .contracts import read_json, sha256_file, write_json
from .video import ROOT


def pretrained_person_weights():
    """Pin the actual COCO checkpoint used for proposals and initialization."""
    import urllib.request

    path = ROOT / "models/yolo11s.pt"
    expected = "85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".download")
        urllib.request.urlretrieve(
            "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s.pt", temporary
        )
        if sha256_file(temporary) != expected:
            raise ValueError("COCO initialization checksum differs from the pinned source")
        temporary.replace(path)
    if sha256_file(path) != expected:
        raise ValueError("Existing COCO checkpoint differs from the pinned source")
    return path


def crop_cache(data, output):
    path, record = output / "crops.npy", output / "crops.json"
    if record.exists():
        saved = read_json(record)
        if saved["identity"] != data["identity"]:
            raise ValueError("Crop cache inputs changed")
        return np.load(path, mmap_mode="c")
    rows = data["rows"]
    pixels = np.lib.format.open_memmap(path, mode="w+", dtype=np.uint8, shape=(len(rows), 3, 192, 128))
    grouped = defaultdict(list)
    for i, row in enumerate(rows):
        grouped[row["image"]].append(i)
    mean, std = (
        torch.tensor([0.485, 0.456, 0.406])[:, None, None],
        torch.tensor([0.229, 0.224, 0.225])[:, None, None],
    )
    for number, (name, indices) in enumerate(grouped.items()):
        image = cv2.imread(name)
        if image is None or sha256_file(name) != rows[indices[0]]["image_sha256"]:
            raise ValueError("Crop source changed")
        for i in indices:
            pixels[i] = (
                ((crop_tensor(image, rows[i]["bbox"]) * std + mean) * 255)
                .round()
                .clamp(0, 255)
                .byte()
                .numpy()
            )
        if number % 100 == 0:
            print(f"Crop cache {number + 1}/{len(grouped)}", flush=True)
    pixels.flush()
    write_json(record, {"identity": data["identity"], "crops": len(rows)})
    return pixels


def roles(data, output, minutes=30, epochs=20, color_invariant=False):
    from persoon1.role_training import scores

    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    torch.manual_seed(42)
    torch.set_num_threads(4)
    pixels = torch.from_numpy(crop_cache(data, output))
    rows = data["rows"]
    labels = torch.tensor(
        [
            0 if r["role"] == "player" else 1 if r["role"] in {"referee", "assistant_referee"} else 2
            for r in rows
        ],
        device="cuda",
    )
    tr = torch.tensor([i for i, r in enumerate(rows) if r["split"] == "train"])
    va = torch.tensor([i for i, r in enumerate(rows) if r["split"] == "val" and r["broadcast"]])
    state = torch.load(BASE_ROLES, map_location="cpu", weights_only=True)
    encoder, head = backbone().cuda().eval(), torch.nn.Linear(608, 3).cuda()
    encoder.load_state_dict(state["backbone"])
    # Adapt the last three convolution blocks; retain robust low-level features
    # and frozen running normalization statistics across different matches.
    for parameter in encoder.parameters():
        parameter.requires_grad = False
    for block in list(encoder[0].children())[-6 if color_invariant else -3 :]:
        for parameter in block.parameters():
            parameter.requires_grad = True
    raw = data["role"].cuda()
    mean, std = raw[tr].mean(0), raw[tr].std(0).clamp_min(0.1)
    colours = raw[:, 576:].clone()
    if color_invariant:
        colours.zero_()
        from torchvision.transforms import ColorJitter, RandomGrayscale

        augmentation = torch.nn.Sequential(ColorJitter(0.4, 0.4, 0.6, 0.5), RandomGrayscale(0.2))
    del raw
    rgb_mean = torch.tensor([0.485, 0.456, 0.406], device="cuda")[None, :, None, None]
    rgb_std = torch.tensor([0.229, 0.224, 0.225], device="cuda")[None, :, None, None]
    optimizer = torch.optim.AdamW(
        [
            {"params": [p for p in encoder.parameters() if p.requires_grad], "lr": 0.0001},
            {"params": head.parameters(), "lr": 0.001},
        ],
        weight_decay=0.001,
    )
    weight = torch.bincount(labels[tr], minlength=3).float().clamp_min(1).rsqrt()
    if color_invariant:
        weight = weight.clamp_max(weight[0] * 2)
    scaler = torch.amp.GradScaler("cuda")
    curve, best, best_score, best_epoch = [], None, -1.0, 0
    for epoch in range(1, epochs + 1):
        order = tr[torch.randperm(len(tr))]
        losses = []
        for start in range(0, len(order), 96):
            ids = order[start : start + 96]
            x = pixels[ids].cuda().float() / 255
            if color_invariant:
                x = augmentation(x)
            x = (x - rgb_mean) / rgb_std
            if torch.rand(()) < 0.5:
                x = x.flip(-1)
            if torch.rand(()) < 0.25:
                x = torch.nn.functional.interpolate(
                    torch.nn.functional.interpolate(x, size=(48, 32), mode="bilinear", align_corners=False),
                    size=(192, 128),
                    mode="bilinear",
                    align_corners=False,
                )
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast("cuda", dtype=torch.float16):
                features = (torch.cat([encoder(x), colours[ids]], 1) - mean) / std
                loss = torch.nn.functional.cross_entropy(
                    head(features),
                    labels[ids],
                    weight=weight,
                    label_smoothing=0.03 if color_invariant else 0.0,
                )
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(
                [p for group in optimizer.param_groups for p in group["params"]], 5.0
            )
            scaler.step(optimizer)
            scaler.update()
            losses.append(float(loss.detach()))
            if time.monotonic() - started >= minutes * 60:
                break
        with torch.inference_mode():
            predictions = []
            for start in range(0, len(va), 128):
                ids = va[start : start + 128]
                x = (pixels[ids].cuda().float() / 255 - rgb_mean) / rgb_std
                feature = (torch.cat([encoder(x), colours[ids]], 1) - mean) / std
                predictions.append(head(feature).softmax(1).cpu())
            prob = torch.cat(predictions).numpy()
        threshold = 0.5 if color_invariant else 0.65
        report = scores(
            labels[va].cpu().numpy(), np.where(prob.max(1) >= threshold, prob.argmax(1), -1), PITCH_ROLE_NAMES
        )
        player, referee = report["per_class"][:2]
        score = player["f1"] + 0.1 * referee["recall"]
        if color_invariant:
            score += float(player["precision"] >= 0.98 and player["recall"] >= 0.95)
        curve.append({"epoch": epoch, "loss": float(np.mean(losses)), "player": player, "referee": referee})
        if score > best_score:
            best_score, best_epoch = score, epoch
            best = (copy.deepcopy(encoder.state_dict()), copy.deepcopy(head.state_dict()))
            best_report = report
            np.savez_compressed(
                output / "validation-probabilities.npz",
                probabilities=prob,
                row_indices=va.numpy(),
                truth=labels[va].cpu().numpy(),
            )
        exported_head = {k: v.cpu().clone() for k, v in best[1].items()}
        if color_invariant:
            # Training's raw colour input is constant zero. Fold its normalized
            # constant into the bias so inference's zero colour block is exact.
            exported_head["bias"] += exported_head["weight"][:, 576:] @ (-mean[576:].cpu() / std[576:].cpu())
            exported_head["weight"][:, 576:] = 0
        snapshot = {
            **state,
            "backbone": {k: v.cpu() for k, v in best[0].items()},
            "role_head": exported_head,
            "mean": mean.cpu(),
            "std": std.cpu(),
            "role_colour_scale": 0.0 if color_invariant else 1.0,
            "role_names": PITCH_ROLE_NAMES,
            "team_video_hashes": [],
        }
        torch.save(snapshot, output / "roles_teams.pt")
        torch.save(
            {
                "backbone": encoder.state_dict(),
                "head": head.state_dict(),
                "optimizer": optimizer.state_dict(),
                "scaler": scaler.state_dict(),
                "epoch": epoch,
                "feature_identity": data["identity"],
            },
            output / "resume.pt",
        )
        write_json(
            output / "metrics.json",
            {
                "runtime_s": time.monotonic() - started,
                "feature_identity": data["identity"],
                "selected_epoch": best_epoch,
                "weights_sha256": sha256_file(output / "roles_teams.pt"),
                "broadcast_validation": best_report,
                "curve": curve,
                "test_accessed": False,
                "color_invariant": color_invariant,
                "validation_role_threshold": threshold,
                "constant_colour_folded": color_invariant,
                "scope": "player including goalkeeper; referee including assistant; other person",
            },
        )
        print(
            f"Fine roles {epoch}: P {player['precision']:.4f}, R {player['recall']:.4f}, referee R {referee['recall']:.4f}",
            flush=True,
        )
        if epoch - best_epoch >= 5 or time.monotonic() - started >= minutes * 60:
            break
    return output / "roles_teams.pt"


def teams(data, output, minutes=15):
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    torch.manual_seed(42)
    rng = np.random.default_rng(42)
    rows = data["rows"]
    raw = data["kit"][:, 576:].cuda()
    log_weights = torch.nn.Parameter(torch.zeros(32, device="cuda"))
    optimizer = torch.optim.Adam([log_weights], lr=0.01)
    grouped = defaultdict(list)
    for i, r in enumerate(rows):
        if (
            r["split"] == "train"
            and r["broadcast"]
            and r["role"] == "player"
            and not r["goalkeeper"]
            and r.get("team") in {"left", "right"}
        ):
            grouped[r["group"]].append(i)
    pools = [v for v in grouped.values() if len({rows[i]["team"] for i in v}) == 2]
    candidates, curve = [], []
    for step in range(1001):
        if step and time.monotonic() - started >= minutes * 60:
            break
        if step:
            pool = pools[int(rng.integers(len(pools)))]
            ids = rng.choice(pool, min(128, len(pool)), replace=False).tolist()
            vector = torch.nn.functional.normalize(raw[ids] * log_weights.exp().clamp(0.2, 5), dim=1)
            similarity = vector @ vector.T
            labels = torch.tensor([int(rows[i]["team"] == "right") for i in ids], device="cuda")
            same = labels[:, None] == labels[None, :]
            mask = ~torch.eye(len(ids), dtype=torch.bool, device="cuda")
            positive, negative = same & mask, ~same & mask
            loss = (
                (1 - similarity[positive]).square().mean()
                + torch.relu(similarity[negative] - 0.45).square().mean()
                + 0.02 * log_weights.square().mean()
            )
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        if step % 100 == 0:
            weights = log_weights.detach().exp().clamp(0.2, 5)
            vectors = torch.nn.functional.normalize(raw * weights, dim=1).cpu().numpy()
            metrics = team_metrics(
                rows,
                vectors,
                np.zeros(len(rows)),
                {
                    "embedding_radius": 0.12,
                    "embedding_separation": 0.35,
                    "embedding_max_distance": 0.5,
                    "embedding_margin": 0.1,
                },
            )
            score = team_selection_score(metrics)
            candidates.append((score, step, weights.cpu().clone()))
            curve.append({"step": step, **{k: v for k, v in metrics.items() if k != "per_clip"}})
    candidates.sort(key=lambda v: v[0], reverse=True)
    best = None
    for _, step, weights in candidates[:3]:
        vectors = torch.nn.functional.normalize(raw * weights.cuda(), dim=1).cpu().numpy()
        for radius in (0.08, 0.12, 0.18):
            for separation in (0.2, 0.35):
                for maximum in (0.2, 0.35, 0.5):
                    for margin in (0.02, 0.05, 0.1):
                        if best is not None and time.monotonic() - started >= minutes * 60:
                            break
                        settings = {
                            "embedding_radius": radius,
                            "embedding_separation": separation,
                            "embedding_max_distance": maximum,
                            "embedding_margin": margin,
                        }
                        metrics = team_metrics(rows, vectors, np.zeros(len(rows)), settings)
                        score = team_selection_score(metrics)
                        if best is None or score > best[0]:
                            best = score, step, weights, settings, metrics
    _, step, weights, settings, metrics = best
    path = output / "kit_embedding.pt"
    torch.save(
        {
            "format": "broadcast-kit-hist-v2",
            "metric_weights": weights,
            "feature": "saturation_weighted_hsv_v2",
        },
        path,
    )
    write_json(
        output / "metrics.json",
        {
            "runtime_s": time.monotonic() - started,
            "selected_step": step,
            "weights_sha256": sha256_file(path),
            "feature_identity": data["identity"],
            "settings": settings,
            "validation": metrics,
            "curve": curve,
            "test_accessed": False,
            "selection": "Within-clip same/different-team pairs; fixed raw-color baseline retained if training does not improve validation",
        },
    )
    print("Color metric", {k: v for k, v in metrics.items() if k != "per_clip"}, flush=True)
    return path


def detector(output, minutes=90, dataset_path=None):
    import os

    import yaml

    from .training_budget import train_yolo

    source = read_json(Path(dataset_path or ROOT / "data/broadcast-pitch-v1") / "manifest.json")
    dataset = output / "player-only-data"
    dataset.mkdir(parents=True, exist_ok=True)
    for row in source["frames"]:
        target = dataset / "images" / row["split"] / Path(row["image"]).name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            os.link(row["image"], target)
        label = dataset / "labels" / row["split"] / (target.stem + ".txt")
        label.parent.mkdir(parents=True, exist_ok=True)
        lines = Path(row["label"]).read_text().splitlines()
        label.write_text("\n".join(line for line in lines if line.startswith("0 ")) + "\n")
    (dataset / "data.yaml").write_text(
        yaml.safe_dump(
            {"path": dataset.as_posix(), "train": "images/train", "val": "images/val", "names": {0: "player"}}
        ),
        encoding="utf-8",
    )
    write_json(
        dataset / "provenance.json",
        {
            "source_fingerprint": source["fingerprint"],
            "names": {0: "player"},
            "referees": "known negatives; not relabelled as players",
            "test_accessed": False,
        },
    )
    config = {
        "imgsz": 1280,
        "epochs": 25,
        "patience": 7,
        "batch": 2,
        "optimizer": "AdamW",
        "lr0": 0.0001,
        "lrf": 0.1,
        "cos_lr": True,
        "warmup_epochs": 2,
        "warmup_bias_lr": 0.0,
        "weight_decay": 0.0005,
        "freeze": 0,
        "amp": True,
        "seed": 42,
        "deterministic": True,
        "rect": False,
        "fliplr": 0.5,
        "flipud": 0.0,
        "degrees": 3.0,
        "translate": 0.1,
        "scale": 0.25,
        "hsv_h": 0.015,
        "hsv_s": 0.4,
        "hsv_v": 0.25,
        "mosaic": 0.1,
        "close_mosaic": 5,
        "mixup": 0.0,
        "plots": True,
        "val": True,
        "save": True,
    }
    return train_yolo(pretrained_person_weights(), dataset, output / "detector", config, minutes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("roles", "teams", "detector"))
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/broadcast-refine-v2")
    parser.add_argument("--base-output", type=Path, default=ROOT / "artifacts/broadcast-pitch-v1")
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/broadcast-pitch-v1")
    parser.add_argument("--minutes", type=float)
    parser.add_argument("--color-invariant", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    data = None
    if args.stage != "detector":
        data = torch.load(args.base_output / "appearance/features.pt", map_location="cpu", weights_only=True)
    record = args.output / (
        "detector/status.json" if args.stage == "detector" else args.stage + "/metrics.json"
    )
    if record.exists():
        saved = read_json(record)
        weight = (
            Path(saved["best"])
            if args.stage == "detector" and saved.get("best")
            else args.output
            / args.stage
            / ("roles_teams.pt" if args.stage == "roles" else "kit_embedding.pt")
        )
        checksum = saved.get("best_sha256") if args.stage == "detector" else saved.get("weights_sha256")
        if args.stage == "detector":
            prepared = read_json(args.output / "player-only-data/provenance.json")
            if prepared["source_fingerprint"] != read_json(args.dataset / "manifest.json")["fingerprint"]:
                raise ValueError("Refined detector dataset changed")
        elif saved.get("feature_identity") != data["identity"]:
            raise ValueError("Refined appearance training inputs changed")
        if weight.is_file() and checksum and sha256_file(weight) == checksum:
            print("Reusing completed verified stage", weight, flush=True)
            raise SystemExit(0)
        raise ValueError("Incomplete or changed refined stage; preserve it and choose a fresh output")
    if args.stage == "detector":
        print(detector(args.output.resolve(), args.minutes or 90, args.dataset), flush=True)
    else:
        if args.stage == "roles":
            roles(
                data,
                args.output / "roles",
                minutes=args.minutes or 30,
                epochs=40 if args.color_invariant else 20,
                color_invariant=args.color_invariant,
            )
        else:
            teams(data, args.output / "teams", minutes=args.minutes or 15)
