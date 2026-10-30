"""Reserve existing test-only source videos and export original pixels without predictions.

Match identity and manual references remain unapproved until a real reviewer
checks them. Merely reserving three sources is not a completed independent test.
"""

import argparse
from datetime import UTC, datetime
from pathlib import Path

import cv2

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.field_layout import POINTS_UV


def prepare(root, output):
    inventory = read_json(root / "highlight-inventory.json")
    candidates = sorted(
        [v for v in inventory["videos"] if v.get("split") == "test" and v.get("status") == "complete"],
        key=lambda v: v["id"],
    )
    if len(candidates) < 3 or len({v["match_id"] for v in candidates}) < 3:
        raise ValueError("At least three separately reserved test-source groups required")
    output.mkdir(parents=True, exist_ok=True)
    frozen_path = output / "selection.json"
    selection = [
        {k: v[k] for k in ("id", "match_id", "sha256", "file", "url", "title")} for v in candidates[:3]
    ]
    if frozen_path.exists() and read_json(frozen_path)["sources"] != selection:
        raise ValueError("Final review selection changed")
    write_json(
        frozen_path,
        {
            "sources": selection,
            "selection_policy": "first_three_sorted_test_source_ids",
            "human_review_completed": False,
            "independent_final_test_completed": False,
            "match_identity_verified": False,
            "pretraining_overlap": "unknown; requires provenance review",
        },
    )
    for source in selection:
        directory = output / source["id"]
        if (directory / "reference-template.json").exists():
            continue
        path = root / source["file"]
        if sha256_file(path) != source["sha256"]:
            raise ValueError("Reserved original video changed")
        # Routing uses only the existing image-category heuristic, never predictions or errors.
        frames_manifest = root / "frames" / source["id"] / "manifest.json"
        overview = []
        if frames_manifest.exists():
            overview = [
                r
                for r in read_json(frames_manifest)["frames"]
                if r["image"].startswith("overview_candidates/")
            ]
        capture = cv2.VideoCapture(str(path))
        fps, count = capture.get(cv2.CAP_PROP_FPS), int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if fps <= 0 or count < round(fps * 30):
            capture.release()
            raise ValueError("Reserved source requires at least 30 seconds of video")
        start = round(overview[0]["timestamp_s"] * fps) if overview else round(10 * fps)
        start = min(start, count - round(30 * fps))
        indices = [start + round(i * fps) for i in range(30)]
        directory.mkdir(exist_ok=True)
        references = []
        try:
            for i in indices:
                capture.set(cv2.CAP_PROP_POS_FRAMES, i)
                ok, frame = capture.read()
                if not ok:
                    raise ValueError("Cannot decode reserved original frame")
                target = directory / f"frame-{i:06d}.png"
                if not cv2.imwrite(str(target), frame):
                    raise ValueError("Cannot write final review frame")
                references.append(
                    {
                        "frame_index": i,
                        "timestamp_s": i / fps,
                        "image": target.name,
                        "image_sha256": sha256_file(target),
                        "calibratable": None,
                        "points": [],
                        "players": [],
                        "human_reviewed": False,
                    }
                )
        finally:
            capture.release()
        write_json(
            directory / "reference-template.json",
            {
                "video_sha256": source["sha256"],
                "video_path": str(path.resolve()),
                "source": source["url"],
                "claimed_match": source["title"],
                "match_identity_verified": False,
                "split": "test",
                "used_for_tuning": False,
                "human_reviewed": False,
                "reviewer": "",
                "settings_frozen_at": None,
                "selection_frozen_at": datetime.now(UTC).isoformat(),
                "selected_frame_indices": indices,
                "selection_fingerprint": digest_json([source["sha256"], indices]),
                "image_size": list(frame.shape[1::-1]),
                "frames": references,
                "known_field_points": [{"id": i, "uv": list(uv)} for i, uv in POINTS_UV.items()],
                "instructions": "Confirm match identity and separation from training/development. "
                "Freeze the chosen weights before reviewing references. Label original pixels; "
                "mark non-calibratable closeups. This is a sparse accuracy review, not a "
                "continuous-frame dropout-duration benchmark.",
            },
        )
        print(f"Reserved {source['id']}: {len(references)} original frames", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/field-corpus"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.root, args.output)


if __name__ == "__main__":
    main()
