"""Check that the application path reproduces the measured tiled boxes on real frames."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.detection import UltralyticsDetector, load_model_manifest


def main():
    """Vergelijk de tegeldetecties van de echte applicatieadapter met de eerder gemeten bronpixelboxen."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Preserve existing runtime proof")
    config = load_model_manifest(args.models)
    if len(config["models"]) != 1 or "ball_tiles" not in config["models"][0]:
        raise ValueError("Use the ball-only profile for coordinate equality")
    reference = read_json(args.reference)
    detector = UltralyticsDetector(config)
    keys = sorted(reference["predictions"])
    checks = []
    for n, key in enumerate([keys[0], keys[len(keys) // 2], keys[-1]]):
        frame = cv2.imread(reference["identities"][key]["image"])
        actual = sorted(detector.detect(frame, n), key=lambda d: (-d.confidence, *d.bbox_xyxy))
        expected = sorted(
            [b for b in reference["predictions"][key] if b["confidence"] >= 0.25],
            key=lambda b: (-b["confidence"], *b["bbox_xyxy"]),
        )
        assert len(actual) == len(expected), (key, len(actual), len(expected))
        for a, b in zip(actual, expected):
            assert a.source_class_id == 32 and a.semantic_class == "ball"
            assert abs(a.confidence - b["confidence"]) < 1e-6
            assert max(abs(x - y) for x, y in zip(a.bbox_xyxy, b["bbox_xyxy"])) < 0.001
        checks.append({"frame_id": key, "detections": len(actual), "source_pixels_match": True})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(
        args.output,
        {
            "status": "passed",
            "frames": checks,
            "model_profile_sha256": sha256_file(args.models),
            "reference_sha256": sha256_file(args.reference),
            "coordinate_tolerance_pixels": 0.001,
            "confidence_tolerance": 1e-6,
            "scope": "Application/evaluation path equality, not a new accuracy measurement.",
        },
    )
    print("Runtime and measured tiled coordinates agree on three real frames")


if __name__ == "__main__":
    main()
