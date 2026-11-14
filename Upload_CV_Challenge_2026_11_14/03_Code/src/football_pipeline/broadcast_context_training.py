"""Traint aanvullende rolcontext op vooraf vastgelegde broadcasttrainingsbeelden.


Teacher errors are simulated per kit so the classifier learns to preserve common
player uniforms even when their individual crop role is wrong. PCA and scaling
are fitted on training images only. Validation is for development selection.
"""

import gzip
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

from football_pipeline.appearance import AppearanceClassifier
from football_pipeline.broadcast_refine import crop_cache
from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.role_context import context_features
from football_pipeline.video import ROOT


def features(prob, kit, cnn, positions, boxes):
    """Zet rolkansen, shirt- en beeldkenmerken, veldposities en boxen om naar de contextvectoren voor het
    vaste broadcastbeeldformaat.
    """
    return context_features(prob, kit, cnn, positions, boxes, (1920, 1080))


def train(output):
    """Verzamel bevroren broadcastkenmerken, train het kleine rolcontextnetwerk en selecteer een
    checkpoint met de vastgelegde ontwikkelvergelijking.
    """
    torch.set_num_threads(4)
    torch.manual_seed(42)
    started = time.monotonic()
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    data = torch.load(
        ROOT / "artifacts/broadcast-pitch-v1/appearance/features.pt", map_location="cpu", weights_only=True
    )
    if any(r["split"] not in {"train", "val"} for r in data["rows"]):
        raise ValueError("Reserved split in context training")
    ids = [i for i, r in enumerate(data["rows"]) if r["broadcast"]]
    rows = [data["rows"][i] for i in ids]
    for path, digest in {(r["image"], r["image_sha256"]) for r in rows}:
        if sha256_file(path) != digest:
            raise ValueError("Context training image changed")
    teacher = ROOT / "artifacts/broadcast-refine-v2/roles/roles_teams.pt"
    inputs = {
        "feature_identity": data["identity"],
        "teacher_sha256": sha256_file(teacher),
        "rows_digest": digest_json([r["id"] for r in rows]),
    }
    cache = root / "teacher-features.npz"
    cache_record = root / "teacher-features.json"
    if cache.exists():
        record = read_json(cache_record)
        if record["inputs"] != inputs or record["sha256"] != sha256_file(cache):
            raise ValueError("Teacher cache inputs changed")
    if not cache.exists():
        classifier = AppearanceClassifier(
            {
                "weights": str(teacher),
                "weights_sha256": sha256_file(teacher),
                "model_id": "teacher",
                "device": "0",
                "role_confidence": 0.5,
                "team_confidence": 0.65,
            }
        )
        pixels = torch.from_numpy(crop_cache(data, ROOT / "artifacts/broadcast-refine-v2/roles"))
        rawcols = data["role"][ids, 576:].cuda()
        mean = torch.tensor([0.485, 0.456, 0.406], device="cuda")[None, :, None, None]
        std = torch.tensor([0.229, 0.224, 0.225], device="cuda")[None, :, None, None]
        raw = np.zeros((len(ids), 576), np.float32)
        prob = np.zeros((len(ids), 3), np.float32)
        with torch.inference_mode():
            for start in range(0, len(ids), 96):
                ix = ids[start : start + 96]
                x = pixels[ix].cuda().float() / 255
                h = classifier.backbone((x - mean) / std)
                z = (torch.cat([h, rawcols[start : start + 96]], 1) - classifier.mean) / classifier.std
                p = classifier.role_head(z).softmax(1)
                raw[start : start + 96] = h.cpu().numpy()
                prob[start : start + 96] = p.cpu().numpy()
                if start % 4800 == 0:
                    print("Teacher", start, "/", len(ids), flush=True)
        np.savez_compressed(cache, raw=raw, prob=prob)
        write_json(cache_record, {"inputs": inputs, "sha256": sha256_file(cache)})
        del classifier, pixels, rawcols
        torch.cuda.empty_cache()
    saved = np.load(root / "teacher-features.npz")
    raw, prob = saved["raw"], saved["prob"]
    kit_path = ROOT / "artifacts/broadcast-refine-v2/teams/kit_embedding.pt"
    kit_state = torch.load(kit_path, map_location="cpu", weights_only=True)
    kit = data["kit"][ids, 576:].numpy() * kit_state["metric_weights"].numpy()
    train = np.array([r["split"] == "train" for r in rows])
    center = raw[train].mean(0)
    z = raw[train] - center
    cov = z.T @ z / max(1, len(z) - 1)
    eig, vec = np.linalg.eigh(cov)
    order = np.argsort(eig)[-32:][::-1]
    projection = vec[:, order] / np.maximum(eig[order], 1e-5)[None, :] ** 0.25
    cnn = (raw - center) @ projection
    cnn /= np.maximum(np.linalg.norm(cnn, axis=1, keepdims=True), 1e-8)
    grouped = defaultdict(list)
    for i, r in enumerate(rows):
        grouped[r["image"]].append(i)
    positions = {}
    for clip in {r["group"].split("/")[-1] for r in rows}:
        provider = json.loads(
            gzip.decompress(
                (ROOT / "data/broadcast-pitch-v1/provider-labels" / f"{clip}.json.gz").read_bytes()
            )
        )
        for a in provider["annotations"]:
            if a.get("supercategory") == "object" and a.get("bbox_pitch"):
                p = a["bbox_pitch"]
                positions[str(a["id"])] = [
                    (p["x_bottom_middle"] + 52.5) / 105,
                    (p["y_bottom_middle"] + 34) / 68,
                ]
    Xtr = []
    Ytr = []
    Xv = []
    Yv = []
    val_ids = []
    for image, ix in grouped.items():
        if len(ix) < 4:
            continue
        group = [rows[i] for i in ix]
        p = prob[ix]
        k = kit[ix]
        e = cnn[ix]
        pos = [positions[r["provider_annotation_id"]] for r in group]
        boxes = [r["bbox"] for r in group]
        truth = np.array([r["role"] != "player" for r in group], np.float32)
        if group[0]["split"] == "val":
            Xv.append(features(p, k, e, pos, boxes))
            Yv.append(truth)
            val_ids.extend(ix)
            continue
        variants = [p]
        for side in ["left", "right"]:
            changed = p.copy()
            for j, r in enumerate(group):
                if r["team"] == side and r["role"] == "player" and not r["goalkeeper"]:
                    changed[j] = [0.02, 0.96, 0.02]
            variants.append(changed)
        changed = p.copy()
        for j, r in enumerate(group):
            if r["role"] != "player":
                changed[j] = [0.98, 0.01, 0.01]
        variants.append(changed)
        for changed in variants:
            Xtr.append(features(changed, k, e, pos, boxes))
            Ytr.append(truth)
    Xtr = np.concatenate(Xtr)
    Ytr = np.concatenate(Ytr)
    Xv = np.concatenate(Xv)
    Yv = np.concatenate(Yv)
    m = Xtr.mean(0)
    s = Xtr.std(0).clip(0.05)
    x = torch.from_numpy((Xtr - m) / s).cuda()
    y = torch.from_numpy(Ytr).cuda()
    xv = torch.from_numpy((Xv - m) / s).cuda()
    torch.manual_seed(42)
    model = torch.nn.Sequential(
        torch.nn.Linear(x.shape[1], 64),
        torch.nn.SiLU(),
        torch.nn.Linear(64, 32),
        torch.nn.SiLU(),
        torch.nn.Linear(32, 1),
    ).cuda()
    opt = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    best = None
    curve = []
    for epoch in range(1, 41):
        model.train()
        order = torch.randperm(len(x), device="cuda")
        for start in range(0, len(x), 1024):
            ix = order[start : start + 1024]
            pred = model(x[ix] + 0.02 * torch.randn_like(x[ix])).squeeze(1)
            loss = torch.nn.functional.binary_cross_entropy_with_logits(
                pred, y[ix], pos_weight=torch.tensor(3.0, device="cuda")
            )
            opt.zero_grad()
            loss.backward()
            opt.step()
        model.eval()
        with torch.inference_mode():
            q = model(xv).sigmoid().cpu().numpy().ravel()
        threshold = max(0.8, float(np.quantile(q[Yv == 0], 0.995)) + 1e-6)
        neg = q >= threshold
        removed_players = int((neg & (Yv == 0)).sum())
        removed_refs = int((neg & (Yv == 1)).sum())
        recovery = max(0.9, float(np.quantile(1 - q[Yv == 1], 0.995)) + 1e-6)
        recovered = (1 - q) >= recovery
        item = {
            "epoch": epoch,
            "reject_threshold": threshold,
            "false_rejected_players": removed_players,
            "correct_rejected_nonplayers": removed_refs,
            "nonplayers": int(Yv.sum()),
            "players": int((Yv == 0).sum()),
            "recover_threshold": recovery,
            "positive_players": int((recovered & (Yv == 0)).sum()),
            "false_positive_nonplayers": int((recovered & (Yv == 1)).sum()),
        }
        curve.append(item)
        score = removed_refs - 3 * removed_players + 0.05 * item["positive_players"]
        if best is None or score > best[0]:
            best = (
                score,
                {k: v.detach().cpu().clone() for k, v in model.state_dict().items()},
                item,
                q.copy(),
            )
        if epoch % 5 == 0:
            print(item, flush=True)
    selected = best[2]
    torch.save(
        {
            "format": "pitch-role-context-v1",
            "state_dict": best[1],
            "mean": torch.from_numpy(m),
            "std": torch.from_numpy(s),
            "cnn_center": torch.from_numpy(center),
            "cnn_projection": torch.from_numpy(projection),
            "input_dimension": x.shape[1],
            "teacher_sha256": sha256_file(teacher),
            "kit_weights_sha256": sha256_file(kit_path),
            "feature_identity": data["identity"],
            "selection": selected,
        },
        root / "role_context.pt",
    )
    np.savez_compressed(
        root / "validation-context.npz",
        probability_nonplayer=best[3],
        truth=Yv,
        row_indices=np.array(val_ids),
    )
    write_json(
        root / "metrics.json",
        {
            "runtime_s": time.monotonic() - started,
            "selected": selected,
            "curve": curve,
            "test_accessed": False,
            "augmentation": "Teacher-role mistakes simulated consistently per labelled kit; referee mistaken for player also simulated",
            "feature_identity": data["identity"],
            "teacher_sha256": sha256_file(teacher),
            "weights_sha256": sha256_file(root / "role_context.pt"),
            "independent_final_test": False,
        },
    )
    print("Selected", selected, flush=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/broadcast-role-context-v6")
    args = parser.parse_args()
    train(args.output)
