"""Create editable review labels and deterministic visual samples of the broadcast corpus."""

from __future__ import annotations

import argparse
import shutil
from collections import defaultdict
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json
from football_pipeline.field_learning import clip_provider_lines

COLORS = {0: "#33ed83", 1: "#ff9f43", 2: "#ff4565", 3: "#52baff"}


def font(size):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def audit_field_labels(root, source):
    path = root / "field-quality-report.json"
    if path.exists() and read_json(path).get("dataset_fingerprint") == source["fingerprint"]:
        return path
    valid, excluded = {"train": 0, "valid": 0}, []
    for row in source["frames"]:
        try:
            clip_provider_lines(read_json(root / row["field_label"]))
            valid["train" if row["split"] == "train" else "valid"] += 1
        except (ValueError, TypeError, KeyError) as exc:
            excluded.append({"label": row["field_label"], "reason": str(exc)})
    write_json(
        path,
        {
            "dataset_fingerprint": source["fingerprint"],
            "valid_field_labels": valid,
            "excluded": excluded,
            "policy": "provider_visible_polylines_v1",
        },
    )
    return path


def export_participants(root, source):
    """Export explicit participant-only tasks so questionable ball boxes cannot supervise them."""
    profiles = (
        ("players", "label", {0: "player", 1: "referee"}),
        ("participants", "role_label", {0: "player", 1: "goalkeeper", 2: "referee"}),
    )
    outputs = []
    for profile, source_key, names in profiles:
        base = root / profile
        frames, counts = [], defaultdict(lambda: defaultdict(int))
        for split in ("train", "val"):
            (base / "images" / split).mkdir(parents=True, exist_ok=True)
            (base / "labels" / split).mkdir(parents=True, exist_ok=True)
        for row in source["frames"]:
            split, fid = row["split"], row["frame_id"]
            lines = []
            for line in (root / row[source_key]).read_text(encoding="utf-8").splitlines():
                if line.strip() and int(line.split()[0]) in names:
                    lines.append(line)
                    counts[split][names[int(line.split()[0])]] += 1
            image = base / "images" / split / f"{fid}.jpg"
            label = base / "labels" / split / f"{fid}.txt"
            if not image.exists():
                image.hardlink_to(root / row["image"])
            expected = "\n".join(lines) + ("\n" if lines else "")
            if label.exists() and label.read_text(encoding="utf-8") != expected:
                raise ValueError(f"Preserve modified labels and create a new version: {label}")
            if not label.exists():
                label.write_text(expected, encoding="utf-8")
            frames.append({"frame_id": fid, "split": split, "label_sha256": sha256_file(label)})
        write_json(
            base / "manifest.json",
            {
                "source_dataset_fingerprint": source["fingerprint"],
                "names": names,
                "frames": frames,
                "object_counts": {s: dict(v) for s, v in counts.items()},
                "task": "participants only; ball is outside this task",
                "human_review_completed": False,
            },
        )
        config = root / f"data-{profile}.yaml"
        config.write_text(
            yaml.safe_dump(
                {"path": str(base), "train": "images/train", "val": "images/val", "names": names},
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        outputs.append(str(config))
    return outputs


def prepare_review(root, source):
    destination = root / "review-workspace"
    manifest_path = destination / "manifest.json"
    if manifest_path.exists():
        return manifest_path  # Existing corrections and review history always take precedence.
    frames = []
    for row in source["frames"]:
        image = f"images/{row['frame_id']}.jpg"
        label = f"labels/{row['frame_id']}.txt"
        for relative in (image, label):
            (destination / relative).parent.mkdir(parents=True, exist_ok=True)
        if not (destination / image).exists():
            (destination / image).hardlink_to(root / row["image"])
        if not (destination / label).exists():
            shutil.copy2(root / row["label"], destination / label)
        frames.append(
            {
                "frame_id": row["frame_id"],
                "video_id": digest_json([source["source"], row["clip"]]),
                "video_id_basis": "provider clip identifier",
                "frame_index": row["source_frame_index"],
                "timestamp_s": row["source_frame_index"] / 25,
                "width": row["width"],
                "height": row["height"],
                "group_id": row["game_id"],
                "split": row["split"],
                "image": image,
                "label": label,
                "label_status": "positive" if row["boxes"] else "negative",
                "annotator": "",
                "reviewer": "",
                "review_status": "open",
                "annotation_source": "published SN-GSR-2024 v1.3, copied for correction",
                "frozen_source_fingerprint": source["fingerprint"],
            }
        )
    write_json(
        manifest_path,
        {
            "schema_version": "1.0",
            "dataset_version": source["dataset_version"] + "-review",
            "names": list(source["names"].values()),
            "frames": frames,
            "human_review_completed": False,
            "purpose": "Editable label copies; original corpus and existing measurements remain frozen",
        },
    )
    return manifest_path


def preview(root, source):
    output = root / "visual-review"
    output.mkdir(exist_ok=True)
    grouped = defaultdict(list)
    for row in source["frames"]:
        grouped[row["game_id"]].append(row)
    selected = []
    # Four clips per match, sampled before viewing any model outputs.
    for game in sorted(grouped):
        clips = defaultdict(list)
        for row in grouped[game]:
            clips[row["clip"]].append(row)
        keys = sorted(clips)
        for index in sorted({round(i * (len(keys) - 1) / 3) for i in range(4)}):
            rows = clips[keys[index]]
            selected.append(rows[len(rows) // 2])
    sample = []
    for page in range((len(selected) + 5) // 6):
        canvas = Image.new("RGB", (1920, 3 * 590), "#111827")
        for position, row in enumerate(selected[page * 6 : page * 6 + 6]):
            with Image.open(root / row["image"]) as original:
                image = original.convert("RGB").resize((960, 540))
            draw = ImageDraw.Draw(image)
            sx, sy = 960 / row["width"], 540 / row["height"]
            for box in row["boxes"]:
                x1, y1, x2, y2 = box["bbox_xyxy"]
                coordinates = (x1 * sx, y1 * sy, x2 * sx, y2 * sy)
                cls = box["class_id"]
                draw.rectangle(coordinates, outline=COLORS[cls], width=2)
                if cls != 0:
                    draw.text(
                        (coordinates[0], max(0, coordinates[1] - 16)),
                        source["names"][str(cls)],
                        fill=COLORS[cls],
                        font=font(15),
                        stroke_width=1,
                        stroke_fill="black",
                    )
            x, y = (position % 2) * 960, (position // 2) * 590
            canvas.paste(image, (x, y + 40))
            ImageDraw.Draw(canvas).text(
                (x + 12, y + 8),
                f"{row['frame_id']} | game {row['game_id']} | {row['split']} | {len(row['boxes'])} boxes",
                fill="white",
                font=font(22),
            )
            sample.append(
                {
                    "frame_id": row["frame_id"],
                    "image_sha256": row["image_sha256"],
                    "page": f"contact-{page + 1:02d}.jpg",
                }
            )
        canvas.save(output / f"contact-{page + 1:02d}.jpg", quality=92)
    # Ball boxes receive native-resolution crops because they are tiny in full-frame sheets.
    balls = Image.new("RGB", (6 * 220, 4 * 250), "#111827")
    for i, row in enumerate(selected):
        candidates = [b for b in row["boxes"] if b["class_id"] == 2]
        if not candidates:
            continue
        x1, y1, x2, y2 = candidates[0]["bbox_xyxy"]
        cx, cy = round((x1 + x2) / 2), round((y1 + y2) / 2)
        with Image.open(root / row["image"]) as original:
            crop = original.crop((cx - 55, cy - 55, cx + 55, cy + 55)).resize((220, 220))
        draw = ImageDraw.Draw(crop)
        draw.rectangle(
            ((x1 - cx + 55) * 2, (y1 - cy + 55) * 2, (x2 - cx + 55) * 2, (y2 - cy + 55) * 2),
            outline=COLORS[2],
            width=2,
        )
        x, y = (i % 6) * 220, (i // 6) * 250
        balls.paste(crop, (x, y + 25))
        ImageDraw.Draw(balls).text((x + 5, y + 3), row["frame_id"], fill="white", font=font(13))
    balls.save(output / "ball-crops.jpg", quality=94)
    write_json(
        output / "sample.json",
        {
            "selection": "four evenly distributed clips per match, temporal midpoint",
            "frames": sample,
            "human_review_completed": False,
        },
    )
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/broadcast-sngsr-v1"))
    args = parser.parse_args()
    root = args.root.resolve()
    source = read_json(root / "manifest.json")
    print(audit_field_labels(root, source))
    print(export_participants(root, source))
    print(prepare_review(root, source))
    print(preview(root, source))
