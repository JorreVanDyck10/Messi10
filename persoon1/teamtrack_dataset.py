"""Zet MOT-persoonsboxen en expliciete rolboxen om naar speler-/scheidsrechterlabels."""

from pathlib import Path

from .core import now, read_json, sha256, validate_dataset, write_json


def build(root="datasets/teamtrack-players-v2"):
    import numpy as np
    import yaml
    from PIL import Image, ImageDraw

    root = Path(root)
    existing = root / "manifest.json"
    if existing.exists():
        saved = read_json(existing)
        if (root / "review-history.jsonl").exists() or any(
            f.get("annotator") != "Codex AI" or f.get("reviewer") or f.get("review_status") == "approved"
            for f in saved.get("frames", [])
        ):
            raise ValueError("Preserve actual annotation/review edits; create a new dataset version instead of rebuilding over them")
    selection = read_json(root / "selection.json")
    roles = read_json(root / "role-annotations.json")
    proposals = read_json(root / "automatic-role-proposals.json")["frames"]
    role_by_id = {r["frame_id"]: r for r in roles["roles"]}
    frames, tables, source_records = [], {}, []
    for sequence in sorted({r["sequence"] for r in selection["frames"]}):
        source = root / "source_annotations" / sequence / "gt.txt"
        tables[sequence] = np.loadtxt(source, delimiter=",")
        source_records.append({"sequence": sequence, "sha256": sha256(source),
            "provider": "TeamTrack authors; public MOT geometry, role column is -1",
            "dataset_url": "https://www.kaggle.com/datasets/atomscott/teamtrack",
            "provider_path": f"teamtrack-mot/teamtrack-mot/soccer_side/train/{sequence}/gt/gt.txt"})
    # Contact sheets contain the final referee boxes, including the rejected white-player proposal.
    for page in range(5):
        sheet = Image.new("RGB", (1000, 855), "#dddddd")
        draw = ImageDraw.Draw(sheet)
        for j, row in enumerate(proposals[page * 12:(page + 1) * 12]):
            x1, y1, x2, y2 = role_by_id[row["frame_id"]]["referee_bbox_xyxy"]
            with Image.open(root / row["image"]) as image:
                left, top = x1 - 30, y1 - 20
                crop = image.crop((left, top, x2 + 30, min(1000, y2 + 20)))
            scale = min(245 / crop.width, 250 / crop.height)
            crop = crop.resize((round(crop.width * scale), round(crop.height * scale)))
            ImageDraw.Draw(crop).rectangle(((x1-left)*scale, (y1-top)*scale,
                (x2-left)*scale, (y2-top)*scale), outline="red", width=1)
            px, py = j % 4 * 250, j // 4 * 285
            sheet.paste(crop, (px, py + 30))
            draw.text((px, py), f"{row['split']} frame {row['frame_index']} | AI checked", fill="black")
        sheet.save(root / "review" / f"final-roles-{page}.jpg", quality=92)
    for i, row in enumerate(proposals):
        fid, split = row["frame_id"], row["split"]
        image_path = root / row["image"]
        if sha256(image_path) != row["image_sha256"]:
            raise ValueError("Delivered source image changed")
        with Image.open(image_path) as image:
            width, height = image.size
        if (width, height) != (6500, 1000):
            raise ValueError("Do not silently resize the TeamTrack dataset")
        table = tables[row["sequence"]]
        selected = table[table[:, 0] == row["mot_frame"]]
        players = selected[np.isin(selected[:, 1], roles["official_geometry_ids_as_player"])]
        if len(players) != 22 or set(players[:, 1].astype(int)) != set(range(22)):
            raise ValueError("Expected the 22 explicitly identified player tracks")
        boxes = [(0, [float(x), float(y), float(x+w), float(y+h)])
                 for _, _, x, y, w, h, *_ in players]
        role = role_by_id[fid]
        boxes.extend((1, box) for box in role["referee_bboxes_xyxy"])
        if len(role["referee_bboxes_xyxy"]) != 2:
            raise ValueError("Review must cover both reliably identified officials")
        labels = []
        for cls, (x1, y1, x2, y2) in boxes:
            if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
                raise ValueError(f"Box outside source image: {fid}")
            labels.append(f"{cls} {(x1+x2)/2/width:.10f} {(y1+y2)/2/height:.10f} {(x2-x1)/width:.10f} {(y2-y1)/height:.10f}")
        label = Path("labels") / split / f"{fid}.txt"
        (root / label).parent.mkdir(parents=True, exist_ok=True)
        (root / label).write_text("\n".join(labels) + "\n", encoding="utf-8", newline="\n")
        evidence = f"review/final-roles-{i // 12}.jpg"
        frames.append({"frame_id": fid, "video_id": row["video_sha256"],
            "frame_index": row["frame_index"], "timestamp_s": row["timestamp_s"],
            "original_match_id": "F_20200220_1", "original_match_frame_index": row["source_frame_index"],
            "original_match_timestamp_s": row["original_timestamp_s"], "mot_frame": row["mot_frame"],
            "width": width, "height": height, "group_id": row["sequence"], "split": split,
            "image": row["image"], "label": label.as_posix(), "label_status": "positive",
            "annotator": "Codex AI", "reviewer": "", "review_status": "ai_visual_checked",
            "geometry_provider": "TeamTrack human-authored MOT for player IDs 0..21; referee geometry assisted and AI checked",
            "visual_evidence": evidence, "visual_evidence_sha256": sha256(root / evidence),
            "selection_reason": "Preselected temporal clip; fixed sampling, not selected using model errors"})
    manifest = root / "manifest.json"
    manifest_data = {"schema_version": "1.0", "dataset_version": selection["dataset_version"],
        "names": ["player", "referee"], "minimum_split_gap_s": 6,
        "review_policy": "provisional_ai_visual", "human_review_completed": False,
        "referee_coverage": roles["referee_coverage"],
        "source_geometry": source_records, "role_annotations_sha256": sha256(root / "role-annotations.json"),
        "scope": "New moments in one TeamTrack match; project split of the public train partition. Human team role review pending.",
        "frames": frames}
    write_json(manifest, manifest_data)
    from .review_sheets import create_sheets
    create_sheets(manifest, root / "review" / "all-boxes")
    for i, frame in enumerate(frames):
        evidence = f"review/all-boxes/referees-{i // 6:02}.jpg"
        frame.update(visual_evidence=evidence, visual_evidence_sha256=sha256(root / evidence))
    write_json(manifest, manifest_data)
    (root / "data.yaml").write_text(yaml.safe_dump({"train": "images/train", "val": "images/val",
        "test": "images/test", "names": {0: "player", 1: "referee"}}, sort_keys=False), encoding="utf-8", newline="\n")
    report = validate_dataset(manifest)
    write_json(root / "validation.json", report)
    if report["errors"]:
        raise ValueError(str(report["errors"]))
    write_json(root / "ai-attestation.json", {"recorded_at": now(), "dataset_fingerprint": report["dataset_fingerprint"],
        "review_policy": "provisional_ai_visual", "human_review_completed": False,
        "note": "Published TeamTrack body geometry plus explicit AI role assignment and referee correction; no invented human review."})
    return report


if __name__ == "__main__":
    result = build()
    print({"counts": result["counts"], "errors": result["errors"]})
