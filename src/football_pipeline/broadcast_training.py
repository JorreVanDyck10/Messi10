"""Bounded, resumable broadcast player/role/team experiments on frozen matches."""

from __future__ import annotations

import argparse
import copy
import time
from collections import defaultdict
from inspect import getsource
from pathlib import Path

import cv2
import numpy as np
import torch

from .appearance import ROLE_NAMES, TEAM_NAMES, backbone, crop_tensor, jersey_feature
from .contracts import digest_json, read_json, sha256_file, write_json
from .kit_embedding import dominant_teams, projection_head
from .training_budget import TrainingBudget
from .video import ROOT
from .video_teams import kit_feature

BASE_PLAYERS = ROOT / "artifacts/joint-retrain-20261027-v2/players/training/batch-4/weights/best.pt"
BASE_ROLES = ROOT / "artifacts/joint-retrain-20261027-v2/roles/pixel-training/roles_teams.pt"
OLD_ROLES = ROOT / "data/joint-local-20261027-v2/roles/manifest.json"


def sample_rows(dataset):
    rows, seen, splits = [], set(), {}
    for f in read_json(Path(dataset) / "manifest.json")["frames"]:
        for p in f["people"]:
            if not p["on_pitch"]:
                continue
            rows.append({**p, "image": f["image"], "image_sha256": f["image_sha256"],
                         "split": f["split"], "group": f["game_id"] + "/" + f["clip"],
                         "frame_index": f["frame_index"], "broadcast": True,
                         "id": f["frame_id"] + ":" + p["provider_annotation_id"]})
    for p in read_json(OLD_ROLES)["samples"]:
        rows.append({**p, "image": str((OLD_ROLES.parent / p["image"]).resolve()),
                     "broadcast": False, "goalkeeper": p.get("goalkeeper", False)})
    kept = []
    for r in rows:
        if r["bbox"][2] - r["bbox"][0] < 4 or r["bbox"][3] - r["bbox"][1] < 12:
            continue
        key = digest_json([r["image_sha256"], [round(float(v), 2) for v in r["bbox"]]])
        if key in seen:
            continue
        seen.add(key)
        if splits.setdefault(r["image_sha256"], r["split"]) != r["split"]:
            raise ValueError("Appearance image crosses splits")
        kept.append(r)
    return kept


def features(dataset, output):
    output.mkdir(parents=True, exist_ok=True)
    path = output / "features.pt"
    identity = digest_json(["broadcast-features-v1", sha256_file(Path(dataset) / "manifest.json"),
                            sha256_file(OLD_ROLES), sha256_file(BASE_ROLES),
                            getsource(sample_rows), getsource(features),
                            sha256_file(ROOT / "src/football_pipeline/appearance.py"),
                            sha256_file(ROOT / "src/football_pipeline/video_teams.py")])
    if path.exists():
        data = torch.load(path, map_location="cpu", weights_only=True)
        if data["identity"] != identity:
            raise ValueError("Feature inputs changed; preserve cache and use a fresh output")
        return data
    torch.set_num_threads(4)
    state = torch.load(BASE_ROLES, map_location="cpu", weights_only=True)
    encoder = backbone().cuda().eval()
    encoder.load_state_dict(state["backbone"])
    rows = sample_rows(dataset)
    grouped = defaultdict(list)
    for i, row in enumerate(rows):
        grouped[row["image"]].append(i)
    role, kit = torch.empty(len(rows), 608), torch.empty(len(rows), 608)
    started = time.monotonic()
    with torch.inference_mode():
        for number, (image_path, indices) in enumerate(grouped.items()):
            frame = cv2.imread(image_path)
            if frame is None or sha256_file(image_path) != rows[indices[0]]["image_sha256"]:
                raise ValueError("Appearance image changed")
            for start in range(0, len(indices), 32):
                ids = indices[start:start + 32]
                batch = [rows[i] for i in ids]
                pixel = torch.stack([crop_tensor(frame, r["bbox"]) for r in batch]).cuda()
                encoded = encoder(pixel).cpu()
                colours = torch.from_numpy(np.stack([jersey_feature(frame, r["bbox"]) for r in batch]))
                kits = torch.from_numpy(np.stack([kit_feature(frame, r["bbox"]) for r in batch]))
                role[ids] = torch.cat([encoded, colours], 1)
                kit[ids] = torch.cat([encoded, kits], 1)
            if number % 25 == 0:
                write_json(output / "progress.json", {"phase": "features", "images": number + 1,
                           "total_images": len(grouped), "elapsed_s": time.monotonic() - started})
                print(f"Features {number + 1}/{len(grouped)} images", flush=True)
    data = {"identity": identity, "rows": rows, "role": role, "kit": kit,
            "backbone": state["backbone"], "runtime_s": time.monotonic() - started}
    torch.save(data, path)
    write_json(output / "metrics.json", {"identity": identity, "runtime_s": data["runtime_s"],
               "images": len(grouped), "crops": len(rows), "encoder_sha256": sha256_file(BASE_ROLES),
               "crop_selection": "on-pitch provider people plus retained role crops; minimum 4x12 pixels"})
    del encoder
    torch.cuda.empty_cache()
    return data


def train_roles(data, output, minutes):
    from persoon1.role_training import scores

    output.mkdir(parents=True, exist_ok=True)
    if (output / "roles_teams.pt").exists():
        record = read_json(output / "metrics.json")
        if record["feature_identity"] != data["identity"] or record["weights_sha256"] != sha256_file(output / "roles_teams.pt"):
            raise ValueError("Completed role model inputs or weights changed")
        return output / "roles_teams.pt"
    budget, started = TrainingBudget(minutes), time.monotonic()
    torch.manual_seed(42)
    rows = data["rows"]
    train = torch.tensor([r["split"] == "train" for r in rows], device="cuda")
    val = torch.tensor([r["split"] == "val" and r["broadcast"] for r in rows], device="cuda")
    raw = data["role"].cuda()
    mean, std = raw[train].mean(0), raw[train].std(0).clamp_min(0.1)
    x = (raw - mean) / std
    y = torch.tensor([ROLE_NAMES.index(r["role"]) for r in rows], device="cuda")
    head = torch.nn.Linear(608, len(ROLE_NAMES)).cuda()
    optimizer = torch.optim.AdamW(head.parameters(), lr=.003, weight_decay=.01)
    weight = torch.bincount(y[train], minlength=len(ROLE_NAMES)).float().clamp_min(1).rsqrt()
    curve, best, best_score, first_epoch, previous_time = [], None, -float("inf"), 1, 0.
    resume_path = output / "resume.pt"
    if resume_path.exists():
        saved = torch.load(resume_path, map_location="cuda", weights_only=True)
        if saved["feature_identity"] != data["identity"]:
            raise ValueError("Interrupted role training inputs changed")
        head.load_state_dict(saved["current"])
        optimizer.load_state_dict(saved["optimizer"])
        curve, best, best_score = saved["curve"], saved["best"], saved["best_score"]
        best_report, best_epoch = saved["best_report"], saved["best_epoch"]
        first_epoch, previous_time = saved["epoch"] + 1, saved["runtime_s"]
        budget = TrainingBudget(max(.001, minutes - previous_time / 60))
    for epoch in range(first_epoch, 601):
        optimizer.zero_grad()
        loss = torch.nn.functional.cross_entropy(head(x[train]), y[train], weight=weight)
        loss.backward()
        optimizer.step()
        if epoch % 10 == 0:
            with torch.inference_mode():
                probabilities = head(x[val]).softmax(1).cpu().numpy()
            pred = np.where(probabilities.max(1) >= .65, probabilities.argmax(1), -1)
            report = scores(y[val].cpu().numpy(), pred, ROLE_NAMES)
            # This scope prioritizes players, while penalising false player labels
            # on real referees. Spectator/steward recall cannot veto the winner.
            player = report["per_class"][0]
            referee = report["per_class"][1]
            score = player["f1"] + .1 * referee["recall"]
            curve.append({"epoch": epoch, "loss": float(loss.detach()), "selection_score": score,
                          "player": player, "referee": referee})
            if score > best_score:
                best_score, best = score, copy.deepcopy(head.state_dict())
                best_report, best_epoch = report, epoch
            if epoch % 100 == 0:
                print(f"Roles epoch {epoch}, player F1 {player['f1']:.4f}", flush=True)
            torch.save({"feature_identity": data["identity"], "current": head.state_dict(),
                        "optimizer": optimizer.state_dict(), "curve": curve, "best": best,
                        "best_score": best_score, "best_report": best_report, "best_epoch": best_epoch,
                        "epoch": epoch, "runtime_s": previous_time + time.monotonic() - started}, resume_path)
            if budget.expired:
                break
    state = torch.load(BASE_ROLES, map_location="cpu", weights_only=True)
    state.update(backbone=data["backbone"], role_head={k: v.cpu() for k, v in best.items()},
                 mean=mean.cpu(), std=std.cpu(), role_colour_scale=1., team_video_hashes=[],
                 role_names=ROLE_NAMES, team_names=TEAM_NAMES)
    path = output / "roles_teams.pt"
    torch.save(state, path)
    write_json(output / "metrics.json", {"status": "time_limited" if budget.expired else "complete",
               "runtime_s": previous_time + time.monotonic() - started, "selected_epoch": best_epoch,
               "weights_sha256": sha256_file(path), "feature_identity": data["identity"],
               "broadcast_validation": best_report, "curve": curve, "test_accessed": False})
    return path


def team_metrics(rows, vectors, keeper_probabilities, settings=None):
    from .contracts import Detection
    from .kit_embedding import embedding_candidate

    settings = settings or {"embedding_radius": .32, "embedding_separation": .4,
                           "embedding_max_distance": .45, "embedding_margin": .18}
    clips = defaultdict(list)
    for i, r in enumerate(rows):
        if r["split"] == "val" and r["broadcast"] and r["role"] == "player" and r.get("team") in {"left", "right"}:
            clips[r["group"]].append(i)
    total = correct = wrong = unknown = keepers = keeper_assigned = 0
    per_clip = []
    for clip, indices in clips.items():
        cluster_indices = [i for i in indices if keeper_probabilities[i] < .8]
        fitted = dominant_teams([vectors[i] for i in cluster_indices], radius=settings["embedding_radius"],
                               separation=settings["embedding_separation"])
        predictions = []
        for i in indices:
            candidate = None
            if fitted:
                model = {"status": "available", "settings": settings,
                         "teams": {key: {"prototype_embedding": c.tolist()} for key, c in zip(("A", "B"), fitted[0])}}
                d = Detection(str(i), "validation", 0, "player", [0, 0, 1, 1], 1.,
                              projection_status="valid", team_embedding=vectors[i].tolist(),
                              player_kind="goalkeeper" if keeper_probabilities[i] >= .8 else "outfield")
                candidate, _ = embedding_candidate(d, model)
            predictions.append(candidate)
        direct = sum(p == ("A" if rows[i]["team"] == "left" else "B") for p, i in zip(predictions, indices))
        swapped = sum(p == ("B" if rows[i]["team"] == "left" else "A") for p, i in zip(predictions, indices))
        hit, assigned = max(direct, swapped), sum(p is not None for p in predictions)
        total += len(indices)
        correct += hit
        wrong += assigned - hit
        unknown += len(indices) - assigned
        keepers += sum(rows[i].get("goalkeeper", False) for i in indices)
        keeper_assigned += sum(rows[i].get("goalkeeper", False) and p is not None for i, p in zip(indices, predictions))
        per_clip.append({"clip": clip, "total": len(indices), "correct": hit, "wrong": assigned - hit,
                         "unknown": len(indices) - assigned, "single_fixed_swap": swapped > direct})
    return {"total": total, "correct": correct, "wrong": wrong, "unknown": unknown,
            "accuracy_assigned": correct / max(1, correct + wrong), "coverage": (correct + wrong) / max(1, total),
            "correct_fraction": correct / max(1, total), "goalkeepers": keepers,
            "goalkeepers_assigned": keeper_assigned, "per_clip": per_clip,
            "meaning": "reference crops, one A/B mapping per whole clip; not end-to-end detector accuracy"}


def team_selection_score(metrics):
    qualified = metrics["accuracy_assigned"] >= .95 and metrics["coverage"] >= .9
    return float(qualified) + (metrics["correct"] - 2 * metrics["wrong"]) / max(1, metrics["total"])


def train_teams(data, output, minutes):
    output.mkdir(parents=True, exist_ok=True)
    path = output / "kit_embedding.pt"
    if path.exists():
        record = read_json(output / "metrics.json")
        if record["feature_identity"] != data["identity"] or record["weights_sha256"] != sha256_file(path):
            raise ValueError("Completed team model inputs or weights changed")
        return path
    budget, started = TrainingBudget(minutes), time.monotonic()
    torch.manual_seed(42)
    rng = np.random.default_rng(42)
    rows = data["rows"]
    train_indices = [i for i, r in enumerate(rows) if r["split"] == "train" and r["broadcast"] and r["role"] == "player"]
    raw = data["kit"].cuda()
    mean, std = raw[train_indices].mean(0), raw[train_indices].std(0).clamp_min(.1)
    x = (raw - mean) / std
    grouped = defaultdict(list)
    for i in train_indices:
        r = rows[i]
        if r.get("team") in {"left", "right"} and not r["goalkeeper"]:
            grouped[r["group"]].append(i)
    pools = [indices for indices in grouped.values() if len({rows[i]["team"] for i in indices}) == 2]
    if not pools:
        raise ValueError("No same/different-team pairs in training clips")
    head, keeper = projection_head().cuda(), torch.nn.Linear(608, 2).cuda()
    optimizer = torch.optim.AdamW([*head.parameters(), *keeper.parameters()], lr=.001, weight_decay=.001)
    keeper_y = torch.tensor([int(r.get("goalkeeper", False)) for r in rows], device="cuda")
    keeper_weights = torch.bincount(keeper_y[train_indices], minlength=2).float().clamp_min(1).rsqrt()
    curve, best_score, best, first_step, previous_time = [], -float("inf"), None, 1, 0.
    resume_path = output / "resume.pt"
    if resume_path.exists():
        saved = torch.load(resume_path, map_location="cuda", weights_only=True)
        if saved["feature_identity"] != data["identity"]:
            raise ValueError("Interrupted team training inputs changed")
        head.load_state_dict(saved["current_projection"])
        keeper.load_state_dict(saved["current_keeper"])
        optimizer.load_state_dict(saved["optimizer"])
        curve, best_score, best = saved["curve"], saved["best_score"], saved["best"]
        best_step, first_step, previous_time = saved["best_step"], saved["step"] + 1, saved["runtime_s"]
        # The deterministic draw stream is restored rather than repeating pairs.
        rng.bit_generator.state = saved["rng_state"]
        budget = TrainingBudget(max(.001, minutes - previous_time / 60))
    for step in range(first_step, 3001):
        pool = pools[int(rng.integers(len(pools)))]
        indices = rng.choice(pool, min(128, len(pool)), replace=False).tolist()
        z = torch.nn.functional.normalize(head(x[indices]), dim=1)
        teams = torch.tensor([int(rows[i]["team"] == "right") for i in indices], device="cuda")
        same = teams[:, None] == teams[None, :]
        mask = ~torch.eye(len(indices), dtype=torch.bool, device="cuda")
        similarity = z @ z.T
        positives, negatives = same & mask, ~same & mask
        if not positives.any() or not negatives.any():
            continue
        pair_loss = (1 - similarity[positives]).square().mean() + torch.relu(similarity[negatives] + .3).square().mean()
        keeper_indices = rng.choice(train_indices, min(512, len(train_indices)), replace=False).tolist()
        keeper_loss = torch.nn.functional.cross_entropy(keeper(x[keeper_indices]), keeper_y[keeper_indices], weight=keeper_weights)
        loss = pair_loss + .2 * keeper_loss
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if step % 100 == 0:
            with torch.inference_mode():
                vectors = torch.nn.functional.normalize(head(x), dim=1).cpu().numpy()
                probabilities = keeper(x).softmax(1)[:, 1].cpu().numpy()
            metrics = team_metrics(rows, vectors, probabilities)
            score = team_selection_score(metrics)
            curve.append({"step": step, "loss": float(loss.detach()), "score": score,
                          **{k: v for k, v in metrics.items() if k != "per_clip"}})
            if score > best_score:
                best_score = score
                best = (copy.deepcopy(head.state_dict()), copy.deepcopy(keeper.state_dict()))
                best_step = step
            print(f"Teams step {step}: accuracy {metrics['accuracy_assigned']:.4f}, coverage {metrics['coverage']:.4f}", flush=True)
            write_json(output / "progress.json", {"phase": "train", "step": step, "elapsed_s": time.monotonic() - started,
                       "accuracy": metrics["accuracy_assigned"], "coverage": metrics["coverage"]})
            torch.save({"feature_identity": data["identity"], "current_projection": head.state_dict(),
                        "current_keeper": keeper.state_dict(), "optimizer": optimizer.state_dict(),
                        "best": best, "best_score": best_score, "best_step": best_step, "curve": curve,
                        "rng_state": rng.bit_generator.state, "step": step,
                        "runtime_s": previous_time + time.monotonic() - started}, resume_path)
            if budget.expired:
                break
    head.load_state_dict(best[0])
    keeper.load_state_dict(best[1])
    with torch.inference_mode():
        vectors = torch.nn.functional.normalize(head(x), dim=1).cpu().numpy()
        probabilities = keeper(x).softmax(1)[:, 1].cpu().numpy()
    selected, score = None, -float("inf")
    for radius in (.2, .32, .45):
        for separation in (.4, .6):
            for maximum in (.3, .45, .6):
                for margin in (.12, .18, .25):
                    settings = {"embedding_radius": radius, "embedding_separation": separation,
                                "embedding_max_distance": maximum, "embedding_margin": margin}
                    metrics = team_metrics(rows, vectors, probabilities, settings)
                    current = team_selection_score(metrics)
                    if current > score:
                        score, selected, selected_metrics = current, settings, metrics
    torch.save({"format": "broadcast-kit-v1", "backbone": data["backbone"],
                "projection": {k: v.cpu() for k, v in best[0].items()},
                "keeper": {k: v.cpu() for k, v in best[1].items()}, "mean": mean.cpu(), "std": std.cpu()}, path)
    write_json(output / "metrics.json", {"status": "time_limited" if budget.expired else "complete",
               "runtime_s": previous_time + time.monotonic() - started, "selected_step": best_step,
               "weights_sha256": sha256_file(path), "feature_identity": data["identity"],
               "selection": "First meet .95 assigned accuracy and .90 coverage on reference crops; then maximize (correct - 2*wrong)/total",
               "settings": selected, "validation": selected_metrics, "curve": curve, "test_accessed": False})
    return path


def run(dataset, output, stage):
    output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    if not torch.cuda.is_available():
        raise ValueError("This training run requires the configured CUDA GPU")
    if stage == "detector":
        from .course_experiments import train_candidate

        status_path = output / "detector/status.json"
        inputs = {"dataset": sha256_file(Path(dataset) / "manifest.json"), "base": sha256_file(BASE_PLAYERS)}
        frozen = output / "detector-inputs.json"
        if frozen.exists() and read_json(frozen) != inputs:
            raise ValueError("Detector training inputs changed")
        write_json(frozen, inputs)
        if status_path.exists():
            status = read_json(status_path)
            if status["status"] in {"complete", "time_limited"} and sha256_file(status["best"]) == status["best_sha256"]:
                print("Reusing completed detector", status["best"], flush=True)
                return
            from .training_budget import resume_yolo

            checkpoints = sorted((output / "detector").glob("batch-*/weights/last.pt"), key=lambda p: p.stat().st_mtime)
            if not checkpoints:
                raise ValueError("Interrupted detector has no native checkpoint; preserve run and choose fresh output")
            last = checkpoints[-1]
            state = torch.load(last, map_location="cpu", weights_only=False)
            if state.get("optimizer") is None or state["epoch"] < 0:
                raise ValueError("Detector checkpoint has no resumable optimizer")
            progress = output / "detector/progress.json"
            elapsed = max(status.get("runtime_s", 0), read_json(progress).get("elapsed_s", 0) if progress.exists() else 0)
            remaining = 120 - elapsed / 60
            if remaining <= 0:
                raise ValueError("Detector training budget already consumed")
            pause = {"resume_checkpoint": str(last), "sha256": sha256_file(last),
                     "last_completed_epoch": state["epoch"] + 1, "maximum_epochs_total": 40,
                     "elapsed_stage_wall_seconds": elapsed, "remaining_training_minutes": remaining}
            del state
            print("Resuming detector", resume_yolo(dataset, output / "detector", pause), flush=True)
            return
        trained = train_candidate(dataset, output / "detector", augment=True, epochs=40,
                                  weights=BASE_PLAYERS, max_minutes=120)
        print("Detector checkpoint", trained, flush=True)
    elif stage == "appearance":
        started = time.monotonic()
        data = features(dataset, output / "appearance")
        train_roles(data, output / "roles", max(.1, 60 - (time.monotonic() - started) / 60))
        train_teams(data, output / "teams", 60)
    else:
        raise ValueError("Unknown training stage")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("detector", "appearance"))
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/broadcast-pitch-v1")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/broadcast-pitch-v1")
    args = parser.parse_args()
    run(args.dataset.resolve(), args.output.resolve(), args.stage)
