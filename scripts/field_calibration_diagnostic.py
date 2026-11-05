"""Exercise real field weights with artificial camera motion of the upstream example image.

This is an engineering diagnostic, never real video accuracy or an independent football benchmark.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.field_model_spec import UPSTREAM_REVISION, UPSTREAM_URL
from football_pipeline.pipeline import process_video
from football_pipeline.video import ROOT, VideoWriter, inspect_video


def main():
    """Voer echte veldgewichten uit op gecontroleerde kunstmatige cameravariaties en schrijf de
    technische diagnose.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/automatic-field-diagnostic")
    parser.add_argument("--runtime", type=Path, default=ROOT / ".tools/field-runtime.json")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    runtime = read_json(args.runtime)
    source = Path(runtime["repository"]) / "examples/messi_sample.png"
    image = cv2.imread(str(source))
    if image is None:
        raise ValueError("Upstream example image is missing; run setup_field_model.py")
    height, width = image.shape[:2]
    video = args.output / "synthetic-pan-zoom.mp4"
    writer = VideoWriter(video, width + width % 2, height + height % 2, 10, 1)
    try:
        for index in range(50):
            phase = index / 49
            zoom = 1 + 0.2 * np.sin(phase * np.pi / 2)
            matrix = cv2.getRotationMatrix2D((width * 0.55, height * 0.5), 0, zoom)
            matrix[0, 2] += 18 * np.sin(phase * np.pi)
            frame = cv2.warpAffine(
                image, matrix, (width + width % 2, height + height % 2), borderMode=cv2.BORDER_REFLECT_101
            )
            if 20 <= index < 25:
                frame[:] = (20, 20, 20)
            cv2.putText(
                frame,
                "SYNTHETISCHE PAN/ZOOM - geen echte bewegende camera",
                (15, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            writer.write(frame)
        writer.close()
    finally:
        if not writer.closed:
            writer.close(abort=True)
    metadata = inspect_video(video)
    provenance = {
        "kind": "synthetic_camera_transform_of_upstream_still_image",
        "source": f"{UPSTREAM_URL}/blob/{UPSTREAM_REVISION}/examples/messi_sample.png",
        "source_sha256": sha256_file(source),
        "video_sha256": metadata.sha256,
        "license_context": "Image supplied with the external GPL-2.0 research checkout; local diagnostic only. "
        "No separate broadcast-footage rights or redistribution claim.",
        "changes": "Artificial pan/zoom of one still, five blank frames (20-24), diagnostic caption; no real motion.",
        "human_reviewed": False,
        "independent_accuracy_claim": False,
    }
    write_json(args.output / "provenance.json", provenance)
    result = process_video(
        video,
        None,
        ROOT / "configs/models.json",
        args.output / "runs",
        field_runtime_path=args.runtime,
        field_source=provenance["source"],
        field_usage=provenance["license_context"] + " " + provenance["changes"],
    )
    records = [
        json.loads(line) for line in (result.directory / "framegegevens.jsonl").read_text().splitlines()
    ]
    blank_safe = all(
        r["calibration"]["homography"] is None and all(d["field_position"] is None for d in r["detections"])
        for r in records[20:25]
    )
    restored = next((r["frame_index"] for r in records[25:] if r["calibration"]["status"] == "valid"), None)
    report = {
        "kind": provenance["kind"],
        "video_sha256": metadata.sha256,
        "run": str(result.directory),
        "output_video": str(result.video_path),
        "calibration": read_json(result.directory / "calibration.json")["measurements"],
        "pipeline": result.manifest["measurements"],
        "blank_frames_have_no_positions": blank_safe,
        "first_valid_frame_after_blank": restored,
        "human_evaluation": "pending",
        "independent_accuracy_claim": False,
    }
    write_json(args.output / "technical-report.json", report)
    shutil.copyfile(result.video_path, args.output / "demonstratie.mp4")
    shutil.copyfile(result.directory / "controlebeelden/frame_000000.jpg", args.output / "preview.jpg")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
