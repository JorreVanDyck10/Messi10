"""Resumable output-layer adaptation from existing, match-separated field labels.

Cache features at provided landmarks, known-channel hard peaks and fixed grid
locations. Unannotated semantic channels retain teacher probabilities. No new
image labels are invented, and the original validation split selects no weights.
"""

import argparse
import copy
import time
from pathlib import Path

import cv2
import numpy as np
import torch
import torchvision.transforms.functional as tf

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.field_layout import POINTS_UV
from football_pipeline.field_learning import atomic_torch_save, load_model, upstream_runtime
from football_pipeline.field_model_spec import RELEASE_WEIGHTS

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/field-pose-multicamera-v1"
RUNTIME = ROOT / "artifacts/joint-retrain-20261027-v2/selected-field-runtime.json"


def sparse_targets(output, keypoints):
    """Return unique sampled pixels and soft targets with unknown channels retained."""
    channels, height, width = output.shape
    if channels != 58 or len(keypoints) != len(POINTS_UV):
        raise ValueError("Unexpected field landmark channels")
    visible = [
        (identifier - 1, float(x) * width, float(y) * height)
        for identifier, (x, y, vis) in zip(sorted(POINTS_UV), keypoints, strict=True)
        if vis == 2
    ]
    indices = set()
    for y in np.linspace(0, height - 1, 6, dtype=int):
        for x in np.linspace(0, width - 1, 8, dtype=int):
            indices.add(int(y * width + x))
    for channel, x, y in visible:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                px, py = int(np.clip(round(x) + dx, 0, width - 1)), int(np.clip(round(y) + dy, 0, height - 1))
                indices.add(py * width + px)
        indices.add(int(output[channel].argmax()))
    indices = torch.tensor(sorted(indices), device=output.device)
    teacher = output.flatten(1)[:, indices].T.float()
    target = teacher.clone()
    ids = [c for c, _, _ in visible]
    if ids:
        coordinates = torch.stack((indices % width, indices // width), 1).float()
        locations = torch.tensor([[x, y] for _, x, y in visible], device=output.device)
        squared = (coordinates[:, None] - locations[None]).square().sum(2)
        positives = 0.9 * torch.exp(-squared / 8.0)
        mass = positives.sum(1, keepdim=True)
        positives *= torch.minimum(torch.ones_like(mass), 0.9 / mass.clamp_min(1e-9))
        other = torch.ones(channels, dtype=torch.bool, device=output.device)
        other[ids] = False
        remainder = teacher[:, other]
        remainder = remainder / remainder.sum(1, keepdim=True).clamp_min(1e-9)
        target[:, other] = remainder * (1 - positives.sum(1, keepdim=True))
        target[:, ids] = positives
        # Retain half the original distribution to limit catastrophic forgetting.
        target = 0.5 * target + 0.5 * teacher
    if not torch.isfinite(target).all() or not torch.allclose(
        target.sum(1), torch.ones(len(target), device=target.device), atol=1e-5
    ):
        raise ValueError("Invalid sparse supervision distribution")
    return indices, target


def collect(args, runtime, manifest, identity):
    directory = args.output / "features"
    directory.mkdir(exist_ok=True)
    model, captured = None, []
    for number, row in enumerate(r for r in manifest["frames"] if r["split"] == "train"):
        image = DATASET / row["image"]
        if (
            sha256_file(image) != row["image_sha256"]
            or sha256_file(DATASET / row["label"]) != row["label_sha256"]
            or sha256_file(row["source_label"]) != row["source_label_sha256"]
        ):
            raise ValueError("Training image or existing annotation changed")
        key = digest_json([identity, row])
        target = directory / f"{key}.pt"
        if target.exists():
            continue
        if model is None:
            model = load_model(runtime, "keypoints", "cuda:0").eval()
            model.head[0][3].register_forward_pre_hook(lambda _, inputs: captured.append(inputs[0]))
        frame = cv2.imread(str(image))
        tensor = tf.resize(tf.to_tensor(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), [540, 960], antialias=True)
        with torch.inference_mode():
            output = model(tensor[None].cuda())[0]
            indices, targets = sparse_targets(output, row["keypoints"])
            features = captured.pop()[0].flatten(1)[:, indices].T
            atomic_torch_save(
                {
                    "identity": key,
                    "features": features.cpu().half(),
                    "targets": targets.cpu().half(),
                    "match_id": row["match_id"],
                    "image_sha256": row["image_sha256"],
                },
                target,
            )
        if (number + 1) % 25 == 0:
            write_json(
                args.output / "progress.json", {"phase": "features", "frames": number + 1, "total": 1024}
            )
            print(f"Features {number + 1}/1024", flush=True)
    if model is not None:
        del model, captured
        torch.cuda.empty_cache()


def train(args, runtime, manifest, identity):
    matches = sorted({r["match_id"] for r in manifest["frames"] if r["split"] == "train"})
    holdout = set(matches[::5])
    train_x, train_y, valid_x, valid_y = [], [], [], []
    for row in (r for r in manifest["frames"] if r["split"] == "train"):
        key = digest_json([identity, row])
        data = torch.load(args.output / "features" / f"{key}.pt", map_location="cpu", weights_only=True)
        if data["identity"] != key or data["image_sha256"] != row["image_sha256"]:
            raise ValueError("Sparse feature cache changed")
        xs, ys = (valid_x, valid_y) if row["match_id"] in holdout else (train_x, train_y)
        xs.append(data["features"])
        ys.append(data["targets"])
    x, y, vx, vy = [torch.cat(values).cuda() for values in (train_x, train_y, valid_x, valid_y)]
    base = torch.load(runtime["weights_keypoints"], map_location="cpu", weights_only=True)
    layer = torch.nn.Linear(x.shape[1], 58).cuda()
    if base["head.0.3.weight"].shape[2:] != (1, 1):
        raise ValueError("Sparse adaptation requires the pinned 1x1 output layer")
    layer.weight.data.copy_(base["head.0.3.weight"][:, :, 0, 0])
    layer.bias.data.copy_(base["head.0.3.bias"])
    optimizer = torch.optim.Adam(layer.parameters(), lr=0.00001, weight_decay=0.0001)
    rng = np.random.default_rng(42)
    curve, best_loss, best, best_step, first = [], float("inf"), None, 0, 0
    resume = args.output / "resume.pt"
    if resume.exists():
        saved = torch.load(resume, map_location="cuda", weights_only=True)
        if saved["identity"] != identity:
            raise ValueError("Sparse training resume inputs differ")
        layer.load_state_dict(saved["layer"])
        optimizer.load_state_dict(saved["optimizer"])
        rng.bit_generator.state = saved["rng_state"]
        first, curve, best_loss, best, best_step = (
            saved["step"] + 1,
            saved["curve"],
            saved["best_loss"],
            saved["best"],
            saved["best_step"],
        )
    started = time.perf_counter()
    for step in range(first, args.steps + 1):
        if step:
            indices = rng.integers(len(x), size=1024)
            logits = layer(x[indices].float())
            targets = y[indices].float()
            targets /= targets.sum(1, keepdim=True)
            loss = torch.nn.functional.kl_div(logits.log_softmax(1), targets, reduction="batchmean")
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        if step % 50 == 0 or step == args.steps:
            total = 0.0
            with torch.inference_mode():
                for start in range(0, len(vx), 2048):
                    targets = vy[start : start + 2048].float()
                    targets /= targets.sum(1, keepdim=True)
                    total += float(
                        torch.nn.functional.kl_div(
                            layer(vx[start : start + 2048].float()).log_softmax(1), targets, reduction="sum"
                        )
                    )
            measured = total / len(vx)
            if measured < best_loss:
                best_loss, best_step, best = measured, step, copy.deepcopy(layer.state_dict())
            curve.append({"step": step, "internal_training_match_holdout_KL": measured})
            atomic_torch_save(
                {
                    "identity": identity,
                    "step": step,
                    "layer": layer.state_dict(),
                    "optimizer": optimizer.state_dict(),
                    "rng_state": copy.deepcopy(rng.bit_generator.state),
                    "curve": curve,
                    "best_loss": best_loss,
                    "best": best,
                    "best_step": best_step,
                },
                resume,
            )
            write_json(
                args.output / "progress.json",
                {"phase": "head_training", "step": step, "best_step": best_step, "holdout_KL": measured},
            )
            print(f"Head {step}: holdout KL {measured:.6f}, best {best_step}", flush=True)
    base["head.0.3.weight"] = best["weight"].detach().cpu()[:, :, None, None]
    base["head.0.3.bias"] = best["bias"].detach().cpu()
    destination = args.output / "keypoints.pt"
    atomic_torch_save(base, destination)
    fingerprint = digest_json([manifest["fingerprint"], sorted(holdout), "sparse_teacher_blend_half_v1"])
    report = {
        "status": "complete",
        "dataset_fingerprint": fingerprint,
        "is_smoke_test": False,
        "selected_step": best_step,
        "curve": curve,
        "head_training_elapsed_s": time.perf_counter() - started,
        "internal_holdout_matches": sorted(holdout),
        "training_matches": len(matches) - len(holdout),
        "validation_used_for_selection": False,
        "test_accessed": False,
        "human_review_completed": False,
        "independent_final_test_completed": False,
        "models": {
            "keypoints": {
                "status": "complete",
                "sha256": sha256_file(destination),
                "path": str(destination.resolve()),
            }
        },
        "identity": identity,
    }
    report_path = args.output / "training-report.json"
    write_json(report_path, report)
    candidate = copy.deepcopy(runtime)
    candidate["weights_keypoints"] = str(destination.resolve())
    candidate["models"]["keypoints"] = {
        "name": "SV_kp_sparse_head_development",
        "path": str(destination.resolve()),
        "sha256": sha256_file(destination),
        "kind": "finetuned",
        "base_model": RELEASE_WEIGHTS["keypoints"],
        "dataset_fingerprint": fingerprint,
        "training_report": str(report_path.resolve()),
        "training_report_sha256": sha256_file(report_path),
        "is_smoke_test": False,
    }
    write_json(args.output / "field-runtime.json", candidate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--stage", choices=("collect", "train", "all"), default="all")
    parser.add_argument("--steps", type=int, default=1000)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    torch.manual_seed(42)
    runtime = upstream_runtime(RUNTIME)
    manifest = read_json(DATASET / "manifest.json")
    if manifest["cross_split_match_overlap"] or manifest["test_accessed"]:
        raise ValueError("Existing training/validation matches must remain separate")
    identity = digest_json(
        [sha256_file(__file__), sha256_file(DATASET / "manifest.json"), sha256_file(RUNTIME), args.steps]
    )
    path = args.output / "inputs.json"
    inputs = {
        "identity": identity,
        "source_sha256": sha256_file(__file__),
        "dataset_manifest_sha256": sha256_file(DATASET / "manifest.json"),
        "runtime_sha256": sha256_file(RUNTIME),
        "steps": args.steps,
        "method": "sparse provided landmarks and known-channel hard peaks; half teacher preservation; frozen backbone and batch norms",
        "validation_used_for_selection": False,
    }
    if path.exists() and read_json(path) != inputs:
        raise ValueError("Sparse experiment inputs changed; use a new output")
    write_json(path, inputs)
    if args.stage in {"collect", "all"}:
        collect(args, runtime, manifest, identity)
    if args.stage in {"train", "all"}:
        train(args, runtime, manifest, identity)


if __name__ == "__main__":
    main()
