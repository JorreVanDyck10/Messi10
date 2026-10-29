"""Create an editable review copy without changing any frozen experimental labels."""

import shutil
from pathlib import Path

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.video import ROOT


def prepare_review(dataset):
    """Maak een afzonderlijke bewerkbare reviewkopie zodat menselijke correcties de bevroren
    experimentele labels niet veranderen.
    """
    source = read_json(dataset / "manifest.json")
    destination = dataset / "review-workspace"
    output = destination / "manifest.json"
    if output.exists():
        return output  # Never overwrite actual team edits or review history.
    frames = []
    for row in source["frames"]:
        image = Path("images") / (row["frame_id"] + ".jpg")
        label = Path("labels") / (row["frame_id"] + ".txt")
        for key, relative in (("image", image), ("label", label)):
            (destination / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dataset / row[key], destination / relative)
            assert sha256_file(destination / relative) == row[key + "_sha256"]
        frames.append(
            {
                "frame_id": row["frame_id"],
                "video_id": digest_json([source["source"], source["source_revision"], row["clip"]]),
                "video_id_basis": "provider clip identifier; source video bytes were not downloaded",
                "frame_index": int(row["frame_id"].rsplit("_", 1)[-1]) - 1,
                "timestamp_s": (int(row["frame_id"].rsplit("_", 1)[-1]) - 1) / 25,
                "width": row["width"],
                "height": row["height"],
                "group_id": row["game_id"],
                "split": row["split"],
                "image": image.as_posix(),
                "label": label.as_posix(),
                "label_status": "positive",
                "annotator": "",
                "reviewer": "",
                "review_status": "open",
                "annotation_source": "provider proposals copied for actual team verification/correction",
                "frozen_source_fingerprint": source["fingerprint"],
            }
        )
    write_json(
        output,
        {
            "schema_version": "1.0",
            "dataset_version": "course-multimatch-v1-team-review-copy",
            "names": list(source["names"].values()),
            "frames": frames,
            "purpose": "Team review workspace; edits do not change completed experimental scores",
            "human_review_completed": False,
        },
    )
    return output


if __name__ == "__main__":
    print(prepare_review(ROOT / "data/course-multimatch-v1"))
