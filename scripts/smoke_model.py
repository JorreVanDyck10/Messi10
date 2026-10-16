"""Exercise actual YOLO inference on a local reference image; this is not a detection evaluation."""

import argparse
import time
from collections import Counter
from pathlib import Path

import cv2

from football_pipeline.contracts import sha256_file, write_json
from football_pipeline.detection import UltralyticsDetector, load_model_manifest
from football_pipeline.geometry import valid_box
from football_pipeline.video import ROOT

parser = argparse.ArgumentParser()
parser.add_argument("image", type=Path)
parser.add_argument("--output", type=Path, default=ROOT / "artifacts/model-smoke.json")
args = parser.parse_args()
frame = cv2.imread(str(args.image))
if frame is None:
    parser.error("Afbeelding kan niet gelezen worden.")
models = load_model_manifest(ROOT / "configs/models.json")
detector = UltralyticsDetector(models)
started = time.perf_counter()
detections = detector.detect(frame, 0)
elapsed = time.perf_counter() - started
assert all(valid_box(d, (frame.shape[1], frame.shape[0])) for d in detections)
assert all(d.semantic_class != "player" for d in detections)
args.output.parent.mkdir(parents=True, exist_ok=True)
write_json(
    args.output,
    {
        "kind": "inference_smoke_not_map",
        "image_sha256": sha256_file(args.image),
        "image_size": [frame.shape[1], frame.shape[0]],
        "models": models,
        "class_counts": dict(Counter(d.semantic_class for d in detections)),
        "runtime_s": elapsed,
        "original_coordinate_bounds_valid": True,
    },
)
print(args.output)
