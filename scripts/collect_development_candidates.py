"""Collect unlabelled, model-assisted candidates from existing TRAIN groups only."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.detection import UltralyticsDetector, load_model_manifest
from football_pipeline.video import ROOT


def main():
    """Selecteer ongelabelde modelondersteunde ontwikkelkandidaten uitsluitend uit de toegestane
    trainingsgroepen.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "datasets/development-candidates-v1")
    parser.add_argument("--models", type=Path, default=ROOT / "configs/models-players.json")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error("Choose a new output directory; existing evidence is never overwritten.")
    clip_root = ROOT / "assets/clips20/panorama128057-training48"
    clip_manifest = read_json(clip_root / "manifest.json")
    dataset = read_json(ROOT / "assets/annotations/football48/manifest.json")
    assert clip_manifest["source"]["sha256"] == dataset["video"]["sha256"]
    groups = {f["group_id"]: f["split"] for f in dataset["frames"]}
    forbidden = {f["group_id"] for f in dataset["frames"] if f["split"] != "train"}
    contour = np.asarray(dataset["field_polygon_source"], np.float32)
    model_spec = load_model_manifest(args.models)
    detector = UltralyticsDetector(model_spec)
    output.mkdir(parents=True)
    (output / "images").mkdir()
    frames, pool_log, previews, pixel_hashes = [], [], [], set()
    for clip in clip_manifest["clips"]:
        if clip["split"] != "train":
            continue
        group = clip["group_id"]
        assert groups[group] == "train" and group not in forbidden
        path = clip_root / clip["file"]
        assert sha256_file(path) == clip["sha256"]
        detector.set_video_identity(clip["sha256"])
        fps = float(clip["fps"])
        old_times = [f["clip_time_s"] for f in clip["selected_frames"]]
        capture = cv2.VideoCapture(str(path))
        pool = []
        try:
            for index in range(25, clip["frame_count"], 75):
                if min(abs(index / fps - t) for t in old_times) < 1.0:
                    continue
                capture.set(cv2.CAP_PROP_POS_FRAMES, index)
                ok, pixels = capture.read()
                if not ok or list(pixels.shape[1::-1]) != clip["size"]:
                    raise ValueError(f"Cannot decode {path.name} frame {index}")
                detections = detector.detect(pixels, index)
                visible = [d for d in detections if d.confidence >= 0.25]
                ambiguous = sum(0.45 <= (d.role_confidence or 0) <= 0.8 for d in visible)
                outside = sum(
                    d.semantic_class == "player"
                    and cv2.pointPolygonTest(
                        contour,
                        ((d.bbox_xyxy[0] + d.bbox_xyxy[2]) / 2, d.bbox_xyxy[3]),
                        False,
                    )
                    < 0
                    for d in visible
                )
                scores = {
                    "ambiguous_role_proposals": ambiguous,
                    "player_proposals_outside_approximate_region": outside,
                    "predicted_roles": dict(Counter(d.semantic_class for d in visible)),
                }
                # Hypotheses for annotation, never claims of true errors or roles.
                priority = 2 * outside + ambiguous
                pool.append((priority, index, pixels, detections, scores))
                pool_log.append(
                    {"group_id": group, "clip_frame_index": index, "priority": priority, **scores}
                )
        finally:
            capture.release()
        selected = sorted(pool, key=lambda row: (-row[0], row[1]))[:2]
        if len(selected) != 2:
            raise ValueError(f"Insufficient independent candidates within training group {group}")
        for _, index, pixels, detections, scores in sorted(selected, key=lambda row: row[1]):
            import hashlib

            raw_hash = hashlib.sha256(pixels.tobytes()).hexdigest()
            assert raw_hash not in pixel_hashes
            pixel_hashes.add(raw_hash)
            frame_id = f"{group}_{index:06d}"
            image = output / "images" / (frame_id + ".jpg")
            if not cv2.imwrite(str(image), pixels, [cv2.IMWRITE_JPEG_QUALITY, 95]):
                raise OSError(f"Cannot save {image}")
            frames.append(
                {
                    "frame_id": frame_id,
                    "image": image.relative_to(output).as_posix(),
                    "image_sha256": sha256_file(image),
                    "decoded_bgr_sha256": raw_hash,
                    "image_size": list(pixels.shape[1::-1]),
                    "group_id": group,
                    "source_clip": path.relative_to(ROOT).as_posix(),
                    "source_clip_sha256": clip["sha256"],
                    "clip_frame_index": index,
                    "clip_timestamp_s": index / fps,
                    "original_timestamp_s_approximate": clip["source_start_s"] + index / fps,
                    "original_frame_index_approximate": round(clip["source_start_s"] * fps) + index,
                    "source_time_caveat": "Re-encoded reference clips align within one frame; exact identity is clip hash/index.",
                    "nearest_existing_annotation_s": min(abs(index / fps - t) for t in old_times),
                    "split": "train_candidate",
                    "annotation_status": "unlabelled",
                    "human_review_completed": False,
                    "training_eligible": False,
                    "selection_signals": scores,
                    "proposals_are_ground_truth": False,
                    "proposals": [asdict(d) for d in detections],
                }
            )
            tile = np.full((220, 640, 3), 245, np.uint8)
            tile[:169] = cv2.resize(pixels, (640, 169), interpolation=cv2.INTER_AREA)
            cv2.putText(
                tile, f"{frame_id} | UNLABELLED", (8, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1
            )
            cv2.putText(
                tile,
                f"uncertain={scores['ambiguous_role_proposals']} outside?={scores['player_proposals_outside_approximate_region']}",
                (8, 212),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (20, 20, 20),
                1,
            )
            previews.append(tile)
        print(group, "2 candidates saved", flush=True)
    assert len(frames) == 12 and len({f["group_id"] for f in frames}) == 6
    write_json(
        output / "manifest.json",
        {
            "schema_version": 1,
            "kind": "unlabelled_training_candidates_not_dataset_labels",
            "source": clip_manifest["source"],
            "models": model_spec,
            "frames": frames,
            "selection": "Two per existing training group, from a 3-second grid, >=1s from current annotations; ranked by model role uncertainty and approximate region disagreements.",
            "test_or_validation_groups_opened": [],
            "independent_matches_added": 0,
            "new_annotated_frames": 0,
            "training_performed": False,
            "limitations": [
                "Same existing match; no new camera or kit generalization evidence.",
                "AI polygon only prioritizes review and is not a calibration or role reference.",
                "Candidate selection cannot discover every missed object; proposals need full visual review.",
            ],
        },
    )
    write_json(output / "selection-pool.json", {"candidates": pool_log})
    sheet = np.vstack([np.hstack(previews[i : i + 2]) for i in range(0, len(previews), 2)])
    assert cv2.imwrite(str(output / "contactsheet.jpg"), sheet)
    print(output)


if __name__ == "__main__":
    main()
