"""Copy 80 ball frames for student review; never overwrite previous labels or reviews."""

import argparse
import copy
import shutil
from pathlib import Path

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json


def prepare(source: Path, metadata: Path, output: Path):
    """Kopieer de vastgelegde 80 balbeelden en labels naar een nieuwe reviewmap met behouden splits en
    weiger bestaande reviewgegevens te overschrijven.
    """
    source, output = source.resolve(), output.resolve()
    if output.exists():
        raise ValueError("Choose a new output directory; an existing review must be preserved.")
    curated = read_json(source / "manifest.json")
    if digest_json({k: v for k, v in curated.items() if k != "fingerprint"}) != curated["fingerprint"]:
        raise ValueError("Curated source fingerprint changed.")
    if curated["names"] != {"0": "ball"}:
        raise ValueError("This exercise requires the explicitly curated ball-only source.")
    original = {row["frame_id"]: row for row in read_json(metadata)["frames"]}
    selected = []
    for split, count in (("train", 48), ("val", 32)):
        rows = sorted(
            (r for r in curated["frames"] if r["split"] == split),
            key=lambda r: (r["game_id"], r["clip"], r["frame_id"]),
        )
        if len(rows) < count:
            raise ValueError(f"Not enough {split} frames.")
        selected.extend(rows[round(i * (len(rows) - 1) / (count - 1))] for i in range(count))
    games = {s: {r["game_id"] for r in selected if r["split"] == s} for s in ("train", "val")}
    if games["train"] & games["val"]:
        raise ValueError("Training and validation must contain different games.")
    # Check every input before creating the editable copies.
    for row in selected:
        if original[row["frame_id"]]["split"] != row["split"]:
            raise ValueError("Source split and review metadata disagree.")
        for kind in ("image", "label"):
            if sha256_file(source / row[kind]) != row[kind + "_sha256"]:
                raise ValueError(f"Changed source {kind}: {row['frame_id']}")

    frames = []
    output.mkdir(parents=True)
    for row in selected:
        frame = copy.deepcopy(original[row["frame_id"]])
        for kind in ("image", "label"):
            destination = output / row[kind]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / row[kind], destination)
            frame[kind] = row[kind]
        frame.update(
            label_status="positive",
            annotator="Codex (AI)",
            reviewer="",
            review_status="open",
            annotation_source="AI-curated provider ball proposals; student review pending",
            initial_image_sha256=row["image_sha256"],
            initial_label_sha256=row["label_sha256"],
        )
        for key in ("reviewed_at", "annotated_at"):
            frame.pop(key, None)
        frames.append(frame)
    manifest = {
        "schema_version": "1.0",
        "dataset_version": "school-ball80-review-v1",
        "names": ["ball"],
        "frames": frames,
        "human_review_completed": False,
        "source_fingerprint": curated["fingerprint"],
        "metadata_sha256": sha256_file(metadata),
        "selection": "48 train and 32 val; evenly spaced sorted game/clip/frame IDs; original match split",
        "match_ids": {s: sorted(v) for s, v in games.items()},
        "limitations": "Existing development images, all positive; not new data or an independent test. "
        "Check the whole image for missing balls; do not treat uncertain images as negative.",
    }
    write_json(output / "manifest.json", manifest)
    (output / "data.yaml").write_text(
        f"path: {output.as_posix()}\ntrain: images/train\nval: images/val\nnames:\n  0: ball\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/broadcast-ball-review-v1/curated"))
    parser.add_argument(
        "--metadata", type=Path, default=Path("data/broadcast-sngsr-v1/review-workspace/manifest.json")
    )
    parser.add_argument("--output", type=Path, default=Path("data/school-ball80-review-v1"))
    args = parser.parse_args()
    result = prepare(args.source, args.metadata, args.output)
    print(f"Prepared {len(result['frames'])} editable frames at {args.output}; human review is open.")
