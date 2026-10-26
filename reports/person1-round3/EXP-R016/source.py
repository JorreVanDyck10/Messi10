"""Reproducible supervised appearance heads; no reserved test frames are opened."""

import argparse
import copy
import json
import os
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import torch

from football_pipeline.appearance import ROLE_NAMES, TEAM_NAMES, backbone, crop_tensor, jersey_feature
from football_pipeline.contracts import sha256_file

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets/roles-teams-v1"


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build():
    existing = DATA / "manifest.json"
    if (DATA / "review-history.jsonl").exists() or (
        existing.is_file() and json.loads(existing.read_text(encoding="utf-8")).get("human_review_completed")
    ):
        raise ValueError(
            "Bewaar menselijke reviews; maak een nieuwe datasetversie voordat je opnieuw opbouwt."
        )
    base = ROOT / "datasets/teamtrack-players-v2"
    manifest = json.loads((base / "manifest.json").read_text())
    roles = {r["frame_id"]: r for r in json.loads((base / "role-annotations.json").read_text())["roles"]}
    rows, tables = [], {}
    for frame in manifest["frames"]:
        if frame["split"] == "test":
            continue
        group = frame["group_id"]
        if group not in tables:
            tables[group] = np.loadtxt(base / "source_annotations" / group / "gt.txt", delimiter=",")
        table = tables[group]
        selected = table[(table[:, 0] == frame["mot_frame"]) & (table[:, 1] < 22)]
        common = {
            "image": "../teamtrack-players-v2/" + frame["image"],
            "group": group,
            "split": frame["split"],
            "video_sha256": frame["video_id"],
        }
        for _, identity, x, y, w, h, *_ in selected:
            identity = int(identity)
            # Visually checked all 22 persistent source identities; red/white vs yellow/blue.
            team = "team_a" if identity <= 10 else "team_b"
            rows.append(
                {
                    **common,
                    "id": frame["frame_id"] + f":player:{identity}",
                    "bbox": [x, y, x + w, y + h],
                    "role": "player",
                    "team": team,
                    "source_track_id": identity,
                    "goalkeeper": identity in (0, 13),
                }
            )
        assistant, referee = roles[frame["frame_id"]]["referee_bboxes_xyxy"]
        for role, box in [("referee", referee), ("assistant_referee", assistant)]:
            rows.append(
                {**common, "id": frame["frame_id"] + ":" + role, "bbox": box, "role": role, "team": None}
            )
    sources = json.loads((DATA / "source-provenance.json").read_text(encoding="utf-8"))["sources"]
    annotations = json.loads((DATA / "photo-crops.json").read_text(encoding="utf-8"))["annotations"]
    for source in sources:
        image = cv2.imread(str(DATA / source["image"]))
        h, w = image.shape[:2]
        for role, boxes in annotations[source["id"]].items():
            for index, (x1, y1, x2, y2) in enumerate(boxes):
                rows.append(
                    {
                        "id": source["id"] + f":{role}:{index}",
                        "image": source["image"],
                        "group": source["id"],
                        "split": source["split"],
                        "role": role,
                        "team": None,
                        "bbox": [x1 * w, y1 * h, x2 * w, y2 * h],
                    }
                )
    original_labels = DATA / "original-labels.json"
    if original_labels.is_file():
        for frame in json.loads(original_labels.read_text())["frames"]:
            for obj in frame["objects"]:
                rows.append(
                    {
                        "id": f"original-{frame['frame_index']:06}:{obj['proposal_index']}",
                        "image": frame["image"],
                        "group": frame["group"],
                        "split": frame["split"],
                        "video_sha256": frame["video_sha256"],
                        "role": obj["role"],
                        "team": obj["team"],
                        "bbox": obj["bbox"],
                    }
                )
    # Bind every used source image; only development data, never reserved test pictures.
    for row in rows:
        row["image_sha256"] = sha256_file(DATA / row["image"])
    groups = {s: {r["group"] for r in rows if r["split"] == s} for s in ("train", "val")}
    assert not groups["train"] & groups["val"]
    result = {
        "version": "roles-teams-v1.1",
        "review_policy": "provisional_ai_visual",
        "human_review_completed": False,
        "role_names": ROLE_NAMES,
        "team_names": TEAM_NAMES,
        "team_meaning": {
            "team_a": "white outfield kit, red goalkeeper",
            "team_b": "blue outfield kit, yellow goalkeeper",
        },
        "scope": "Team head covers two explicitly labelled matches: TeamTrack and original HBTFZwMdcCw. External role photos are separate source groups; no test images opened.",
        "samples": rows,
        "counts": {s: dict(Counter(r["role"] for r in rows if r["split"] == s)) for s in ("train", "val")},
    }
    save(DATA / "manifest.json", result)
    return result


def scores(target, predicted, names):
    confusion = np.zeros((len(names), len(names) + 1), int)
    for t, p in zip(target, predicted):
        confusion[t, p if p >= 0 else len(names)] += 1
    per = []
    for i, name in enumerate(names):
        tp = int(confusion[i, i])
        total = int(confusion[i].sum())
        emitted = int(confusion[:, i].sum())
        precision = tp / emitted if emitted else 0
        recall = tp / total if total else 0
        per.append(
            {
                "name": name,
                "n": total,
                "correct": tp,
                "precision": precision,
                "recall": recall,
                "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0,
            }
        )
    return {
        "accuracy": float(sum(t == p for t, p in zip(target, predicted)) / len(target)),
        "macro_f1": float(np.mean([r["f1"] for r in per])),
        "per_class": per,
        "confusion": confusion.tolist(),
        "confusion_columns": [*names, "unknown"],
    }


def load_training_manifest(path):
    """Explicit extension data must preserve its own train/val groups and source bytes."""
    path = Path(path).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    if (data.get("human_review_completed") is not False
            or data.get("review_policy") != "provisional_ai_visual"
            or data.get("role_names") != ROLE_NAMES or data.get("team_names") != TEAM_NAMES):
        raise ValueError("Extension manifest must disclose provisional AI labels and actual class names")
    groups, images, image_hash_splits, identifiers, dimensions = {}, {}, {}, set(), {}
    for row in data["samples"]:
        if row["split"] not in {"train", "val"}:
            raise ValueError("Role development training must never open reserved test images")
        if row["id"] in identifiers or row["role"] not in ROLE_NAMES:
            raise ValueError("Duplicate crop identity or invalid role")
        identifiers.add(row["id"])
        if row.get("team") is not None and (row["role"] != "player" or row["team"] not in TEAM_NAMES):
            raise ValueError("Only verified player crops may have a supervised team label")
        if groups.setdefault(row["group"], row["split"]) != row["split"]:
            raise ValueError("Source group crosses training/validation")
        image = (path.parent / row["image"]).resolve()
        if not image.is_relative_to(ROOT) or sha256_file(image) != row["image_sha256"]:
            raise ValueError("Source image identity changed or points outside the project")
        if images.setdefault(str(image), row["split"]) != row["split"]:
            raise ValueError("Source image crosses training/validation")
        if image_hash_splits.setdefault(row["image_sha256"], row["split"]) != row["split"]:
            raise ValueError("Duplicate image bytes cross training/validation under different file names")
        if len(row["bbox"]) != 4 or not np.isfinite(row["bbox"]).all():
            raise ValueError("Invalid crop box")
        if str(image) not in dimensions:
            pixels = cv2.imread(str(image))
            if pixels is None:
                raise ValueError("Unreadable source image")
            dimensions[str(image)] = pixels.shape[:2]
        height, width = dimensions[str(image)]
        x1, y1, x2, y2 = row["bbox"]
        if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
            raise ValueError("Crop box outside its source image")
    return data


def supervised_team_videos(rows, base):
    # Role-only additions never make a new match eligible for a trained team head.
    return sorted({r["video_id"] for r in base["frames"]}
                  | {r["video_sha256"] for r in rows if r.get("video_sha256") and r.get("team") is not None})


def augment_role_tensor(tensor, augmentation):
    """One deterministic transform shared by initial features AND later training pixels."""
    if augmentation not in range(6):
        raise ValueError("Unknown role crop augmentation")
    if augmentation % 2:
        tensor = tensor.flip(2)
    if augmentation >= 2:
        size = (32, 24) if augmentation < 4 else (64, 48)
        tensor = torch.nn.functional.interpolate(tensor[None], size=size, mode="bilinear", align_corners=False)
        tensor = torch.nn.functional.interpolate(tensor, size=(192, 128), mode="bilinear", align_corners=False)[0]
    return tensor


def train(output, fine_tune=False, encoder_checkpoint=None, manifest_path=None, fine_tune_blocks=3,
          role_colour_scale=8.0):
    if not np.isfinite(role_colour_scale) or role_colour_scale <= 0:
        raise ValueError("Role colour scale must be positive and finite")
    torch.manual_seed(42)
    np.random.seed(42)
    torch.set_num_threads(4)
    os.environ.setdefault("TORCH_HOME", str(ROOT / ".cache/torch"))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    explicit_manifest = manifest_path is not None
    manifest_path = Path(manifest_path).resolve() if explicit_manifest else DATA / "manifest.json"
    data = load_training_manifest(manifest_path) if explicit_manifest else build()
    data_root = manifest_path.parent
    rows = data["samples"]
    save(output / "configuration.json", {
        "seed": 42, "dataset_sha256": sha256_file(manifest_path),
        "warm_start_sha256": sha256_file(encoder_checkpoint) if encoder_checkpoint else None,
        "fine_tune": fine_tune, "fine_tune_blocks": fine_tune_blocks,
        "role_colour_scale": role_colour_scale, "fine_epochs": 20, "steps_per_epoch": 10,
        "samples_per_class_step": 12, "fine_head_lr": .0005, "fine_backbone_lr": .00005,
        "head_refit_epochs": 400, "head_refit_lr": .005, "role_threshold": .65,
        "selection": "Validation macro F1 at role confidence .65", "human_review_completed": False,
        "training_source_sha256": sha256_file(__file__),
        "photo_augmentation_applied_in_both_feature_stages": True,
        "photo_augmentation": {"0":"original", "1":"horizontal mirror", "2":"32x24 then restore", "3":"mirror and 32x24 then restore", "4":"64x48 then restore", "5":"mirror and 64x48 then restore"},
        "colour_histogram_source": "Original torso histogram, retained across crop-only visual transforms",
    })
    # Label-preserving photo augmentation stays within each source's original training group.
    extra = []
    for r in rows:
        if r["split"] == "train" and r.get("augment_training_crops", r["image"].startswith("sources/")):
            extra.extend({**r, "id": r["id"] + f":aug{a}", "augmentation": a} for a in range(1, 6))
    rows = rows + extra
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    encoder = backbone(pretrained=not bool(encoder_checkpoint)).eval().to(device)
    if encoder_checkpoint:
        encoder.load_state_dict(
            torch.load(encoder_checkpoint, map_location=device, weights_only=True)["backbone"]
        )
    features = []
    started = time.perf_counter()
    images = {}
    with torch.inference_mode():
        for start in range(0, len(rows), 32):
            batch = rows[start : start + 32]
            pixels = []
            colours = []
            for r in batch:
                if r["image"] not in images:
                    images[r["image"]] = cv2.imread(str(data_root / r["image"]))
                im = images[r["image"]]
                tensor = crop_tensor(im, r["bbox"])
                tensor = augment_role_tensor(tensor, r.get("augmentation", 0))
                pixels.append(tensor)
                colours.append(jersey_feature(im, r["bbox"]))
            features.append(
                torch.cat(
                    [encoder(torch.stack(pixels).to(device)), torch.from_numpy(np.stack(colours)).to(device)],
                    1,
                ).cpu()
            )
    x = torch.cat(features).float().to(device)
    train_mask = torch.tensor([r["split"] == "train" for r in rows], device=device)
    val_mask = ~train_mask
    mean = x[train_mask].mean(0)
    std = x[train_mask].std(0).clamp_min(0.1)
    if fine_tune and encoder_checkpoint:
        initial = torch.load(encoder_checkpoint, map_location=device, weights_only=True)
        mean, std = initial["mean"], initial["std"]
    x = (x - mean) / std
    role_y = torch.tensor([ROLE_NAMES.index(r["role"]) for r in rows], device=device)
    team_y = torch.tensor([TEAM_NAMES.index(r["team"]) if r["team"] else -1 for r in rows], device=device)
    if fine_tune:
        # Adapt only the last three feature blocks; retain batch-normalization running statistics.
        for parameter in encoder.parameters():
            parameter.requires_grad = False
        if fine_tune_blocks not in (0, 1, 3):
            raise ValueError("Choose 0, 1 or 3 trainable backbone blocks")
        blocks = list(encoder[0].children())[-fine_tune_blocks:] if fine_tune_blocks else []
        for block in blocks:
            for parameter in block.parameters():
                parameter.requires_grad = True
        warm = torch.load(
            encoder_checkpoint or ROOT / "runs/appearance/EXP-R003/roles_teams.pt",
            map_location=device,
            weights_only=True,
        )
        head = torch.nn.Linear(608, len(ROLE_NAMES)).to(device)
        with torch.no_grad():
            head.weight.zero_()
            head.bias.zero_()
            count = warm["role_head"]["weight"].shape[0]
            head.weight[:count].copy_(warm["role_head"]["weight"])
            head.bias[:count].copy_(warm["role_head"]["bias"])
        opt = torch.optim.Adam(
            [
                {"params": [p for p in encoder.parameters() if p.requires_grad], "lr": 0.00005},
                {"params": head.parameters(), "lr": 0.0005},
            ],
            weight_decay=0.001,
        )
        raw_pixels = []
        raw_colours = []
        for r in rows:
            im = images[r["image"]]
            tensor = crop_tensor(im, r["bbox"])
            tensor = augment_role_tensor(tensor, r.get("augmentation", 0))
            raw_pixels.append(tensor)
            raw_colours.append(jersey_feature(im, r["bbox"]))
        pixels = torch.stack(raw_pixels)
        colours = torch.from_numpy(np.stack(raw_colours)).to(device)
        class_indices = [torch.where(train_mask & (role_y == i))[0] for i in range(len(ROLE_NAMES))]
        best = -1
        fine_curve = []
        for epoch in range(1, 21):
            encoder.eval()
            head.train()
            for step in range(10):
                chosen = torch.cat(
                    [indices[torch.randint(len(indices), (12,), device=device)] for indices in class_indices]
                )
                embedding = encoder(pixels[chosen.cpu()].to(device))
                features = (torch.cat([embedding, colours[chosen]], 1) - mean) / std
                features = torch.cat([features[:, :576], features[:, 576:] * role_colour_scale], 1)
                opt.zero_grad()
                loss = torch.nn.functional.cross_entropy(head(features), role_y[chosen])
                loss.backward()
                opt.step()
            with torch.inference_mode():
                current = []
                for start in range(0, len(rows), 32):
                    current.append(
                        torch.cat(
                            [encoder(pixels[start : start + 32].to(device)), colours[start : start + 32]], 1
                        )
                    )
                raw = torch.cat(current)
                normal = (raw - mean) / std
                role_features = torch.cat([normal[:, :576], normal[:, 576:] * role_colour_scale], 1)
                probs = head(role_features[val_mask]).softmax(1).cpu().numpy()
                report = scores(
                    role_y[val_mask].cpu().numpy(),
                    np.where(probs.max(1) >= 0.65, probs.argmax(1), -1),
                    ROLE_NAMES,
                )
            fine_curve.append(
                {"epoch": epoch, "val_macro_f1_at_0_65": report["macro_f1"], "per_class": report["per_class"]}
            )
            if report["macro_f1"] > best:
                best = report["macro_f1"]
                best_encoder = copy.deepcopy(encoder.state_dict())
                fine_role_head = copy.deepcopy(head.state_dict())
                fine_role_score = report["macro_f1"]
                fine_role_epoch = epoch
            print("fine", epoch, report["macro_f1"], flush=True)
        encoder.load_state_dict(best_encoder)
        with torch.inference_mode():
            raw = torch.cat(
                [
                    torch.cat(
                        [encoder(pixels[start : start + 32].to(device)), colours[start : start + 32]], 1
                    )
                    for start in range(0, len(rows), 32)
                ]
            )
        # Retain the normalization bound to the warm-start head; compare its selected head to a refit.
        raw = raw.clone()
        x = (raw - mean) / std
        save(output / "fine-tune-curves.json", fine_curve)
    heads = {}
    reports = {}
    curves = {}
    for task, y, names in [("role", role_y, ROLE_NAMES), ("team", team_y, TEAM_NAMES)]:
        task_x = x.clone()
        if task == "role":
            task_x[:, 576:] *= role_colour_scale
        tr = train_mask & (y >= 0)
        va = val_mask & (y >= 0)
        head = torch.nn.Linear(608, len(names)).to(device)
        opt = torch.optim.Adam(head.parameters(), lr=0.005, weight_decay=0.01)
        weight = torch.bincount(y[tr], minlength=len(names)).float().clamp_min(1).reciprocal()
        criterion = torch.nn.CrossEntropyLoss(weight=weight)
        best_score = -1
        best = None
        curve = []
        for epoch in range(1, 401):
            head.train()
            opt.zero_grad()
            loss = criterion(head(task_x[tr]), y[tr])
            loss.backward()
            opt.step()
            if epoch % 5 == 0:
                with torch.inference_mode():
                    probs = head(task_x[va]).softmax(1).cpu().numpy()
                    truth = y[va].cpu().numpy()
                report = scores(truth, np.where(probs.max(1) >= 0.65, probs.argmax(1), -1), names)
                curve.append(
                    {"epoch": epoch, "train_loss": float(loss.detach()), "val_macro_f1": report["macro_f1"]}
                )
                if report["macro_f1"] > best_score:
                    best_score = report["macro_f1"]
                    best = copy.deepcopy(head.state_dict())
                    selected = epoch
        head.load_state_dict(best)
        if fine_tune and task == "role" and fine_role_score > best_score:
            best = fine_role_head
            selected = f"fine_epoch_{fine_role_epoch}"
            head.load_state_dict(best)
        heads[task] = best
        with torch.inference_mode():
            probs = head(task_x[va]).softmax(1).cpu().numpy()
            truth = y[va].cpu().numpy()
        predicted = probs.argmax(1)
        thresholded = np.where(probs.max(1) >= 0.65, predicted, -1)
        reports[task] = {
            "selected_epoch": selected,
            "argmax": scores(truth, predicted, names),
            "threshold_0_65": scores(truth, thresholded, names),
            "predictions": [
                {
                    "id": r["id"],
                    "truth": names[int(t)],
                    "prediction": names[int(p)],
                    "confidence": float(prob.max()),
                }
                for r, t, p, prob in zip(
                    [r for r, mask in zip(rows, va.cpu().numpy()) if mask], truth, predicted, probs
                )
            ],
        }
        curves[task] = curve
        print(task, reports[task]["argmax"], flush=True)
    # All clips in this same match share team identities, but not their geometric calibration.
    base = json.loads((ROOT / "datasets/teamtrack-players-v2/manifest.json").read_text())
    state = {
        "backbone": {k: v.cpu() for k, v in encoder.state_dict().items()},
        "role_head": {k: v.cpu() for k, v in heads["role"].items()},
        "team_head": {k: v.cpu() for k, v in heads["team"].items()},
        "mean": mean.cpu(),
        "std": std.cpu(),
        "role_colour_scale": float(role_colour_scale),
        "role_names": ROLE_NAMES,
        "team_names": TEAM_NAMES,
        "team_video_hashes": supervised_team_videos(rows, base),
    }
    path = output / "roles_teams.pt"
    torch.save(state, path)
    save(
        output / "metrics.json",
        {
            "kind": "conditional ground-truth crop classification, not detection mAP",
            "dataset_sha256": sha256_file(manifest_path),
            "device": device,
            "gpu": torch.cuda.get_device_name() if device != "cpu" else None,
            "runtime_s": time.perf_counter() - started,
            "weights_sha256": sha256_file(path),
            "roles": reports["role"],
            "teams": reports["team"],
            "human_review_completed": False,
            "independent_final_test": False,
        },
    )
    save(output / "curves.json", curves)
    return reports


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="runs/appearance/EXP-R001")
    parser.add_argument("--fine-tune", action="store_true")
    parser.add_argument("--encoder-checkpoint")
    parser.add_argument("--manifest", help="Separate reviewed AI development manifest; preserves the base dataset")
    parser.add_argument("--fine-tune-blocks", type=int, choices=(0, 1, 3), default=3)
    parser.add_argument("--role-colour-scale", type=float, default=8.0)
    args = parser.parse_args()
    train(args.output, args.fine_tune, args.encoder_checkpoint, args.manifest, args.fine_tune_blocks,
          args.role_colour_scale)
