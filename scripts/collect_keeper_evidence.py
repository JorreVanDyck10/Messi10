"""Evaluate the retained neural keeper head without replacing selected kit embeddings."""

import copy
from collections import defaultdict
from pathlib import Path

import cv2
import torch

from football_pipeline.contracts import Detection, read_json, sha256_file, write_json
from football_pipeline.kit_embedding import KitEmbedding

ROOT = Path(__file__).resolve().parents[1]


def main():
    torch.set_num_threads(2)
    output = ROOT / "artifacts/broadcast-reliability-day2/keeper-evidence-v2"
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = ROOT / "artifacts/broadcast-pitch-v1/teams/kit_embedding.pt"
    kit = KitEmbedding({"weights": str(checkpoint), "device": "cpu"})
    probabilities = []

    def capture_probabilities(module, inputs, logits):
        probabilities.extend(logits.detach().softmax(1)[:, 1].cpu().tolist())

    kit.keeper.register_forward_hook(capture_probabilities)
    dataset = read_json(ROOT / "data/broadcast-temporal-v1/manifest.json")
    grouped = defaultdict(list)
    for row in dataset["frames"]:
        grouped[row["clip"]].append(row)
    for clip, rows in grouped.items():
        target = output / f"{clip}.json"
        source = ROOT / "artifacts/broadcast-reliability-day2/temporal-native-v1" / f"{clip}.json"
        identity = {
            "keeper_weights_sha256": sha256_file(checkpoint),
            "detections_sha256": sha256_file(source),
            "dataset_fingerprint": dataset["fingerprint"],
        }
        if target.exists():
            if read_json(target)["identity"] != identity:
                raise ValueError("Keeper evidence inputs changed")
            continue
        cached = read_json(source)
        found = []
        for row, frame in zip(rows, cached["frames"], strict=True):
            detections = [Detection(**copy.deepcopy(d)) for d in frame["detections"]]
            image = cv2.imread(row["image"])
            if image is None or sha256_file(row["image"]) != row["image_sha256"]:
                raise ValueError("Keeper image changed")
            probabilities.clear()
            eligible = [
                d
                for d in detections
                if d.semantic_class == "player"
                and d.projection_status == "valid"
                and d.bbox_xyxy[2] - d.bbox_xyxy[0] >= 4
                and d.bbox_xyxy[3] - d.bbox_xyxy[1] >= 12
            ]
            kit.update(image, detections)
            found.append(
                {
                    "frame_index": row["frame_index"],
                    "kinds": {d.detection_id: d.player_kind for d in detections if d.player_kind is not None},
                    "probabilities": dict(
                        zip((d.detection_id for d in eligible), probabilities, strict=True)
                    ),
                }
            )
            if len(found) % 50 == 0:
                print(f"Keeper evidence {clip}: {len(found)}/{len(rows)}", flush=True)
        write_json(target, {"identity": identity, "frames": found})
    write_json(output / "complete.json", {"status": "complete"})


if __name__ == "__main__":
    main()
