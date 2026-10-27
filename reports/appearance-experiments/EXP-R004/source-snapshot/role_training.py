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
    # Bind every used source image; only development data, never reserved test pictures.
    for row in rows:
        row["image_sha256"] = sha256_file(DATA / row["image"])
    groups = {s: {r["group"] for r in rows if r["split"] == s} for s in ("train", "val")}
    assert not groups["train"] & groups["val"]
    result = {
        "version": "roles-teams-v1",
        "review_policy": "provisional_ai_visual",
        "human_review_completed": False,
        "role_names": ROLE_NAMES,
        "team_names": TEAM_NAMES,
        "team_meaning": {
            "team_a": "white outfield kit, red goalkeeper",
            "team_b": "blue outfield kit, yellow goalkeeper",
        },
        "scope": "Team head is specific to TeamTrack match F_20200220_1; external role photos are separate source groups.",
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


def train(output, fine_tune=False):
    torch.manual_seed(42)
    np.random.seed(42)
    torch.set_num_threads(4)
    os.environ.setdefault("TORCH_HOME", str(ROOT / ".cache/torch"))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    data = build()
    rows = data["samples"]
    # Label-preserving photo augmentation stays within each source's original training group.
    extra = []
    for r in rows:
        if r["split"] == "train" and r["image"].startswith("sources/"):
            extra.extend({**r, "id": r["id"] + f":aug{a}", "augmentation": a} for a in range(1, 6))
    rows = rows + extra
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    encoder = backbone(pretrained=True).eval().to(device)
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
                    images[r["image"]] = cv2.imread(str(DATA / r["image"]))
                im = images[r["image"]]
                tensor = crop_tensor(im, r["bbox"])
                augmentation = r.get("augmentation", 0)
                if augmentation % 2:
                    tensor = tensor.flip(2)
                if augmentation >= 2:
                    size = (32, 24) if augmentation < 4 else (64, 48)
                    tensor = torch.nn.functional.interpolate(
                        tensor[None], size=size, mode="bilinear", align_corners=False
                    )
                    tensor = torch.nn.functional.interpolate(
                        tensor, size=(192, 128), mode="bilinear", align_corners=False
                    )[0]
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
    x = (x - mean) / std
    role_y = torch.tensor([ROLE_NAMES.index(r["role"]) for r in rows], device=device)
    team_y = torch.tensor([TEAM_NAMES.index(r["team"]) if r["team"] else -1 for r in rows], device=device)
    if fine_tune:
        # Adapt only the last three feature blocks; retain batch-normalization running statistics.
        for parameter in encoder.parameters():
            parameter.requires_grad = False
        for block in list(encoder[0].children())[-3:]:
            for parameter in block.parameters():
                parameter.requires_grad = True
        warm = torch.load(
            ROOT / "runs/appearance/EXP-R003/roles_teams.pt", map_location=device, weights_only=True
        )
        head = torch.nn.Linear(608, len(ROLE_NAMES)).to(device)
        head.load_state_dict(warm["role_head"])
        opt = torch.optim.Adam(
            [
                {"params": [p for p in encoder.parameters() if p.requires_grad], "lr": 0.0001},
                {"params": head.parameters(), "lr": 0.0005},
            ],
            weight_decay=0.001,
        )
        raw_pixels = []
        raw_colours = []
        for r in rows:
            im = images[r["image"]]
            tensor = crop_tensor(im, r["bbox"])
            if r.get("augmentation", 0) % 2:
                tensor = tensor.flip(2)
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
                features = torch.cat([features[:, :576], features[:, 576:] * 8], 1)
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
                role_features = torch.cat([normal[:, :576], normal[:, 576:] * 8], 1)
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
        # Refit both heads on the adapted representation with training-only normalization.
        raw = raw.clone()
        mean = raw[train_mask].mean(0)
        std = raw[train_mask].std(0).clamp_min(0.1)
        x = (raw - mean) / std
        save(output / "fine-tune-curves.json", fine_curve)
    heads = {}
    reports = {}
    curves = {}
    for task, y, names in [("role", role_y, ROLE_NAMES), ("team", team_y, TEAM_NAMES)]:
        task_x = x.clone()
        if task == "role":
            task_x[:, 576:] *= 8
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
        "role_colour_scale": 8.0,
        "role_names": ROLE_NAMES,
        "team_names": TEAM_NAMES,
        "team_video_hashes": sorted({r["video_id"] for r in base["frames"]}),
    }
    path = output / "roles_teams.pt"
    torch.save(state, path)
    save(
        output / "metrics.json",
        {
            "kind": "conditional ground-truth crop classification, not detection mAP",
            "dataset_sha256": sha256_file(DATA / "manifest.json"),
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
    args = parser.parse_args()
    train(args.output, args.fine_tune)
