"""Download an attributed development clip, freeze a review selection, and run real field inference.

This creates no human labels or approvals. The selected frames remain an unfinished review template.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.automatic_calibration import prepare_automatic_calibration
from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.pipeline import process_video
from football_pipeline.video import ROOT, find_tool, inspect_video, read_frame

SOURCES = {
    "nz-canada": {
        "page": "https://commons.wikimedia.org/wiki/File:2018_FIFA_U-17_Women%27s_World_Cup_-_New_Zealand_vs_Canada_-_24.webm",
        "url": "https://upload.wikimedia.org/wikipedia/commons/9/95/2018_FIFA_U-17_Women%27s_World_Cup_-_New_Zealand_vs_Canada_-_24.webm",
        "author": "NaBUru38",
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "original_sha1": "c90cbbf2da1dc837cebed0cbf6047365d9f21b57",
    },
    "latvia": {
        "page": "https://commons.wikimedia.org/wiki/File:Latvia-Gibraltar_football_2026-03-31.webm",
        "url": "https://upload.wikimedia.org/wikipedia/commons/0/06/Latvia-Gibraltar_football_2026-03-31.webm",
        "author": "Martins Brunenieks / Papuass",
        "license": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "original_sha1": "5e9f987bdfef00090c6c57f6728f1459842ffe3a",
    },
}


def main():
    """Download de toegeschreven ontwikkelclip, leg de reviewselectie vast en voer de echte
    veldinferentie voor de pilot uit.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=SOURCES, default="nz-canada")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/automatic-field-pilot")
    parser.add_argument("--runtime", type=Path, default=ROOT / ".tools/field-runtime.json")
    parser.add_argument("--models", type=Path, default=ROOT / "configs/models.json")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    directory = args.output / args.source
    directory.mkdir(parents=True, exist_ok=True)
    source = SOURCES[args.source]
    original = directory / "source.webm"
    if not original.is_file():
        request = urllib.request.Request(
            source["url"], headers={"User-Agent": "Messi10-field-pilot/0.1 (research)"}
        )
        partial = original.with_suffix(".download")
        with urllib.request.urlopen(request, timeout=90) as response, partial.open("wb") as stream:
            while chunk := response.read(1024 * 1024):
                stream.write(chunk)
        partial.replace(original)
    import hashlib

    with original.open("rb") as stream:
        if hashlib.file_digest(stream, "sha1").hexdigest() != source["original_sha1"]:
            raise ValueError("Source differs from the Commons file revision selected before inference")
    video_path = directory / "development.mp4"
    if not video_path.is_file():
        subprocess.run(
            [
                find_tool("ffmpeg"),
                "-v",
                "error",
                "-i",
                str(original),
                "-t",
                "12",
                "-an",
                "-vf",
                "fps=10",
                "-c:v",
                "libx264",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                str(video_path),
            ],
            check=True,
        )
    video = inspect_video(video_path)
    usage = (
        f"{source['license']} {source['license_url']}; credit {source['author']} / Wikimedia Commons. "
        "Changes: first 12 seconds, silent H.264 CFR 10 fps, detection and field overlay with minimap. "
        f"Annotated video available under {source['license']}; no endorsement."
    )
    provenance_path = directory / "provenance.json"
    if not provenance_path.exists():
        write_json(
            provenance_path,
            {
                "source": source,
                "usage": usage,
                "original_sha256": sha256_file(original),
                "video": asdict(video),
                "role": "field-calibration development, separate from person-1 splits",
                "selected_frame_indices": np.linspace(0, video.frame_count - 1, 30, dtype=int).tolist(),
                "selection_frozen_at": datetime.now(UTC).isoformat(),
                "human_reviewed": False,
            },
        )
    provenance = read_json(provenance_path)
    if provenance["video"]["sha256"] != video.sha256:
        raise ValueError("Frozen selection belongs to a different clip")
    reference_path = directory / "reference-to-review.json"
    if not reference_path.exists():
        write_json(
            reference_path,
            {
                "schema_version": 1,
                "video_sha256": video.sha256,
                "human_reviewed": False,
                "reviewer": "",
                "used_for_tuning": False,
                "selection_frozen_at": provenance["selection_frozen_at"],
                "selected_frame_indices": provenance["selected_frame_indices"],
                "source": source["page"],
                "usage": usage,
                "frames": [
                    {"frame_index": i, "calibratable": None, "points": []}
                    for i in provenance["selected_frame_indices"]
                ],
            },
        )
    images = directory / "review-frames"
    images.mkdir(exist_ok=True)
    for index in provenance["selected_frame_indices"]:
        target = images / f"frame_{index:06d}.jpg"
        if not target.is_file() and not cv2.imwrite(str(target), read_frame(video, index)):
            raise ValueError("Cannot save review frame")
    if args.prepare_only:
        print(video_path)
        return
    bundle = prepare_automatic_calibration(
        video_path, args.runtime, directory / "calibrations", source=source["page"], usage=usage
    )
    result = process_video(video_path, bundle, args.models, directory / "runs")
    calibration_manifest = bundle.manifest
    report = {
        "kind": "real_pretrained_model_technical_pilot",
        "source": source,
        "usage": usage,
        "video_sha256": video.sha256,
        "run": str(result.directory),
        "output_video": str(result.video_path),
        "calibration": calibration_manifest["measurements"],
        "pipeline": result.manifest["measurements"],
        "models": calibration_manifest["models"],
        "human_evaluation": "pending",
        "review_template": str(reference_path),
        "independent_accuracy_claim": False,
        "limitations": [
            "Development clip, no generalization benchmark",
            "No player-specific trained weights yet",
            "No global player identity or team-side identity across camera cuts",
        ],
    }
    write_json(directory / "technical-report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
