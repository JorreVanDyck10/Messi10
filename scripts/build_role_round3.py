"""Explicit AI visual decisions for rare-role development; preserves all earlier labels."""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

import cv2

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.video import ROOT
from persoon1.role_training import load_training_manifest

# These are reviewed subject proposals, not an automatic mapping from file title to role.
DECISIONS = {
    "portugal-stewards": {"steward": [0, 1, 2, 3, 5, 8], "spectator": [9, 15, 16, 17], "person": [4]},
    "sosnowiec-night": {"spectator": [3, 4, 8]},
    "grand-rapids": {"spectator": [0, 3, 16, 17, 27, 32, 37]},
    "us-venezuela-fans": {"spectator": [22, 24, 26, 28, 29, 31, 34], "person": [1, 2, 3, 5]},
    "seattle-portland": {"spectator": [4, 5, 7, 11, 13, 16, 30], "person": [0, 2]},
    "sweden-u21-fans": {"spectator": [0, 1, 2, 3, 4, 9, 18]},
    "shimizu-fans": {"spectator": [0, 1, 2, 4, 7, 9, 22]},
    "bohemians-fans": {"spectator": [0, 2, 4, 5, 10], "person": [1]},
    "japan-audience": {"spectator": [2, 7, 8, 15, 18, 29]},
    "faroe-fans": {"spectator": [0, 1, 8, 10, 14, 18, 23, 29]},
    "leverkusen-fans": {"spectator": [0, 1, 2, 6, 10, 23, 24, 25, 28, 35, 44, 59]},
    "event-stewards-2012": {"steward": [1, 2, 3]},
}


def main():
    """Voeg de vastgelegde zeldzame-rolvoorbeelden en correcties toe zonder bestaande datasetlabels te
    overschrijven.
    """
    output = ROOT / "datasets/roles-teams-v3"
    if (output / "manifest.json").exists():
        raise ValueError("Preserve dataset/review history; choose a new version")
    prior_path = ROOT / "datasets/roles-teams-v2/manifest.json"
    prior = load_training_manifest(prior_path)
    rows = []
    for row in prior["samples"]:
        item = dict(row)
        item["image"] = Path(os.path.relpath(prior_path.parent / row["image"], output)).as_posix()
        rows.append(item)
    index = read_json(ROOT / "reports/person1-round3/proposals/index.json")
    decisions = []
    for source in index["sources"]:
        for role, selected in DECISIONS.get(source["id"], {}).items():
            for number in selected:
                proposal = next(p for p in source["proposals"] if p["proposal_index"] == number)
                box = proposal["bbox"]
                if source["id"] == "sweden-u21-fans" and number == 2:
                    box = [1218, 314, box[2], box[3]]  # Exclude the adjacent blue-shirt spectator.
                item = {
                    "id": f"round3:{source['id']}:{number}",
                    "image": source["image"],
                    "image_sha256": source["sha256"],
                    "group": source["group"],
                    "split": source["split"],
                    "bbox": box,
                    "role": role,
                    "team": None,
                    "origin": "new_rare_role_photo",
                    "annotator": "Codex AI",
                    "reviewer": "",
                    "review_status": "ai_visual_checked",
                    "human_review_completed": False,
                    "augment_training_crops": source["split"] == "train",
                    "note": "Selected conditional single-subject crop, not exhaustive image detection labels. Original context was inspected; generic staff/ambiguous job remains person.",
                }
                if source["id"] == "event-stewards-2012":
                    item["note"] += (
                        " Auxiliary non-football event-steward source; no stadium-specific identity claim."
                    )
                rows.append(item)
                decisions.append(
                    {"id": item["id"], "proposal": proposal, "corrected_bbox": box, "role": role}
                )
    # One in-domain development frame gives a clear orange-vest stadium steward;
    # white-capped ball/event assistants are NOT labelled as referees or players.
    video = ROOT / "artifacts/joint-automatic-roles/nz-canada/development.mp4"
    capture = cv2.VideoCapture(str(video))
    ok, frame = capture.read()
    capture.release()
    if not ok or frame.shape[:2] != (720, 1280):
        raise ValueError("Existing Commons development clip unavailable or changed")
    image = output / "sources/nz-canada-frame0.jpg"
    if image.exists():
        raise ValueError("Unregistered extracted frame exists; do not overwrite")
    if not cv2.imwrite(str(image), frame):
        raise ValueError("Failed to save development frame")
    video_labels = [
        ("steward", [900, 9, 945, 127]),
        ("person", [274, 385, 344, 579]),
        ("person", [790, 510, 934, 720]),
    ]
    for i, (role, box) in enumerate(video_labels):
        rows.append(
            {
                "id": f"round3:nz-canada:0:{i}",
                "image": image.relative_to(output).as_posix(),
                "image_sha256": sha256_file(image),
                "group": "nz-canada-2018-u17-commons-24",
                "split": "train",
                "bbox": box,
                "role": role,
                "team": None,
                "origin": "new_rare_role_video",
                "annotator": "Codex AI",
                "reviewer": "",
                "review_status": "ai_visual_checked",
                "human_review_completed": False,
                "augment_training_crops": True,
                "note": "Stadium orange-vest steward and generic white-capped event/ball assistants. The technical integration clip is now role training development data, never an unseen accuracy test.",
            }
        )
    write_json(
        output / "extracted-video-source.json",
        {
            "video_sha256": sha256_file(video),
            "frame_index": 0,
            "image_sha256": sha256_file(image),
            "source": "https://commons.wikimedia.org/wiki/File:2018_FIFA_U-17_Women%27s_World_Cup_-_New_Zealand_vs_Canada_-_24.webm",
            "author": "NaBUru38",
            "license": "CC BY-SA 4.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "changes": "First frame from the existing silent 10-fps development derivative, JPEG encoding and selected role crops/overlays; no endorsement.",
            "source_image_size": [1280, 720],
            "split": "train",
            "group": "nz-canada-2018-u17-commons-24",
        },
    )
    manifest = {
        "version": "roles-teams-v3.1",
        "role_names": prior["role_names"],
        "team_names": prior["team_names"],
        "review_policy": "provisional_ai_visual",
        "human_review_completed": False,
        "base_manifest_sha256": sha256_file(prior_path),
        "samples": rows,
        "scope": "Retained V2 development crops plus event-group-split rare-role sources. Extra sources have no team supervision. No reserved test pictures opened.",
        "annotation_scope": "Selected person crops, never exhaustive whole-image detector ground truth.",
    }
    write_json(output / "manifest.json", manifest)
    write_json(
        output / "ai-label-decisions.json",
        {
            "decisions": decisions,
            "excluded_source": {
                "event-stewards-2010": "Different ceremony context and attire; no reliable football-role transfer assumed. Source retained as an unused candidate."
            },
            "excluded_proposals": "Unlisted suggestions are deliberately not supervision: duplicates, combined subjects, chairs, tiny fragments and unresolved roles. Negative proposals are not training negatives for a detector.",
            "human_review_completed": False,
        },
    )
    load_training_manifest(output / "manifest.json")
    print(dict(Counter((r["split"], r["role"]) for r in rows if r["id"].startswith("round3:"))))


if __name__ == "__main__":
    main()
