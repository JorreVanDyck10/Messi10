"""Past lokale datasets aan voor de gezamenlijke taken, met behoud van labels en bronsplits."""

from __future__ import annotations

import argparse
import hashlib
import os
from collections import Counter
from pathlib import Path

import cv2
import yaml

from .contracts import digest_json, read_json, sha256_file, write_json
from .video import ROOT

VERSION = "joint-local-v2"


def names_of(data):
    """Normaliseer een lijst of dictionary met klassenamen naar een mapping van numerieke IDs op namen."""
    names = data.get("names", {})
    return dict(enumerate(names)) if isinstance(names, list) else {int(k): v for k, v in names.items()}


def unique_rows(rows):
    """Newest annotation first. Identical source pixels must keep their split."""
    seen, selected, excluded = {}, [], []
    # A complete original image must outrank an older crop of that same source
    # frame. Annotation richness breaks ties; stable input order keeps newest
    # equally complete versions first.
    rows = sorted(
        rows, key=lambda r: (not bool(r.get("crop_xyxy_source")), len(r.get("names", []))), reverse=True
    )
    for row in rows:
        key = row.get("source_frame_rgb_sha256") or row["image_sha256"]
        if key in seen:
            if seen[key]["split"] != row["split"]:
                raise ValueError(f"Conflicting source splits: {row['image']}")
            excluded.append(
                {"image": row["image"], "reason": "duplicate source frame", "kept": seen[key]["image"]}
            )
            continue
        seen[key] = row
        selected.append(row)
    return selected, excluded


def load_boxes(image, label, names):
    """Lees YOLO-labels bij het bronbeeld en zet ze om naar gevalideerde boxen met hun expliciete
    klassebetekenis.
    """
    pixels = cv2.imread(str(image))
    if pixels is None:
        raise ValueError(f"Unreadable image {image}")
    height, width = pixels.shape[:2]
    boxes = []
    for line in label.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        c, x, y, w, h = map(float, line.split())
        if (
            c != int(c)
            or int(c) not in names
            or not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1)
        ):
            raise ValueError(f"Invalid YOLO annotation {label}")
        box = [(x - w / 2) * width, (y - h / 2) * height, (x + w / 2) * width, (y + h / 2) * height]
        if box[0] < -0.01 or box[1] < -0.01 or box[2] > width + 0.01 or box[3] > height + 0.01:
            raise ValueError(f"Box outside image {label}")
        boxes.append(
            {
                "name": names[int(c)],
                "bbox_xyxy": [max(0, box[0]), max(0, box[1]), min(width, box[2]), min(height, box[3])],
            }
        )
    return width, height, boxes


def gather_frames(root):
    """Inventariseer lokaal beschikbare bronframes met labels en herkomst voor de gezamenlijke
    trainingsselectie.
    """
    paths = sorted((root / "assets/annotations").glob("*/manifest.json"), reverse=True)
    paths += [
        root / "datasets/teamtrack-players-v2/manifest.json",
        root / "data/course-multimatch-v1/manifest.json",
    ]
    records, manifests, excluded = [], [], []
    for path in paths:
        data = read_json(path)
        names = names_of(data)
        manifests.append(
            {
                "path": str(path),
                "sha256": sha256_file(path),
                "version": data.get("dataset_version"),
                "names": names,
                "source": data.get("source"),
                "review_policy": data.get(
                    "review_policy", "provider_or_provisional_AI; human review not asserted"
                ),
            }
        )
        for frame in data["frames"]:
            if frame["split"] not in {"train", "val", "valid"}:
                excluded.append(
                    {
                        "manifest": str(path),
                        "frame": frame["frame_id"],
                        "reason": "reserved split; image and labels not opened",
                    }
                )
                continue
            image, label = (path.parent / frame["image"]).resolve(), (path.parent / frame["label"]).resolve()
            digest = sha256_file(image)
            if frame.get("image_sha256", digest) != digest:
                raise ValueError(f"Source checksum mismatch {image}")
            width, height, boxes = load_boxes(image, label, names)
            records.append(
                {
                    **frame,
                    "image": str(image),
                    "label": str(label),
                    "manifest": str(path),
                    "image_sha256": digest,
                    "label_sha256": sha256_file(label),
                    "width": width,
                    "height": height,
                    "split": "val" if frame["split"] == "valid" else frame["split"],
                    "boxes": boxes,
                    "names": list(names.values()),
                    "group": frame.get("group_id", "GSR-" + str(frame.get("game_id"))),
                    "annotation_provenance": frame.get(
                        "annotation_provenance", "Existing source labels; no new human review"
                    ),
                }
            )
    return records, manifests, excluded


def link_file(source, destination):
    """Hergebruik bronpixels via een hardlink wanneer dat kan en val anders terug op een gewone
    bestandskopie.
    """
    import shutil

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def detector_dataset(rows, output):
    """Bouw de gezamenlijke detectorweergave met speler-/officiallabels en behoud de oorspronkelijke
    bronsplits.
    """
    names = {0: "player", 1: "referee"}
    kept = []
    for row in rows:
        stem = row["image_sha256"]
        image = output / "images" / row["split"] / (stem + Path(row["image"]).suffix)
        label = output / "labels" / row["split"] / (stem + ".txt")
        link_file(row["image"], image)
        label.parent.mkdir(parents=True, exist_ok=True)
        mapped = []
        for box in row["boxes"]:
            if box["name"] not in names.values():
                continue
            a, b, c, d = box["bbox_xyxy"]
            mapped.append(
                [
                    0 if box["name"] == "player" else 1,
                    (a + c) / 2 / row["width"],
                    (b + d) / 2 / row["height"],
                    (c - a) / row["width"],
                    (d - b) / row["height"],
                ]
            )
        label.write_text("".join(" ".join(map(str, b)) + "\n" for b in mapped), encoding="utf-8")
        kept.append(
            {
                **row,
                "image": str(image),
                "label": str(label),
                "label_sha256": sha256_file(label),
                "frame_id": stem,
                "boxes": [
                    {"class_id": 0 if b["name"] == "player" else 1, "bbox_xyxy": b["bbox_xyxy"]}
                    for b in row["boxes"]
                    if b["name"] in names.values()
                ],
            }
        )
    write_yaml(output, names)
    manifest = {
        "dataset_version": VERSION,
        "names": names,
        "frames": kept,
        "fingerprint": digest_json(kept),
        "human_review_completed": False,
        "test_accessed": False,
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def write_yaml(output, names):
    """Schrijf de relatieve trainings- en validatiepaden en klassenamen in een Ultralytics-
    datasetconfiguratie.
    """
    output.mkdir(parents=True, exist_ok=True)
    (output / "data.yaml").write_text(
        yaml.safe_dump(
            {"path": output.as_posix(), "train": "images/train", "val": "images/val", "names": names}
        ),
        encoding="utf-8",
    )


def ball_dataset(rows, output, names):
    """Bouw de gezamenlijke balweergave met de passende klassemapping en gecontroleerde afgeleide
    beelden.
    """
    from .ball_tiles import tile_windows

    records, skipped = [], []
    for row in rows:
        pixels = cv2.imread(row["image"])
        balls = [b["bbox_xyxy"] for b in row["boxes"] if b["name"] == "ball"]
        for index, window in enumerate(tile_windows(row["width"], row["height"], 1280)):
            x, y, r, b = window

            def intersects(q):
                """Bepaal of de kandidaatbox het huidige tegelgebied werkelijk overlapt voordat het
                object in de tegelweergave wordt meegenomen.
                """
                return min(q[2], r) > max(q[0], x) and min(q[3], b) > max(q[1], y)

            partial = any(
                intersects(q) and not (x <= q[0] < q[2] <= r and y <= q[1] < q[3] <= b) for q in balls
            )
            uncertain = any(intersects(region["xyxy"]) for region in row.get("unresolved_regions", []))
            if partial or uncertain:
                skipped.append(
                    {"image": row["image"], "window": window, "reason": "partial ball or unresolved region"}
                )
                continue
            objects = [q for q in balls if intersects(q)]
            stem = row["image_sha256"] + f"-t{index}"
            image = output / "images" / row["split"] / (stem + ".png")
            label = output / "labels" / row["split"] / (stem + ".txt")
            image.parent.mkdir(parents=True, exist_ok=True)
            label.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(image), pixels[y:b, x:r], [cv2.IMWRITE_PNG_COMPRESSION, 2]):
                raise ValueError("Could not write ball tile")
            labels = [
                [
                    32,
                    (a + c - 2 * x) / 2 / (r - x),
                    (d + e - 2 * y) / 2 / (b - y),
                    (c - a) / (r - x),
                    (e - d) / (b - y),
                ]
                for a, d, c, e in objects
            ]
            label.write_text("".join(" ".join(map(str, q)) + "\n" for q in labels), encoding="utf-8")
            records.append(
                {
                    "image": str(image),
                    "label": str(label),
                    "split": row["split"],
                    "source_image_sha256": row["image_sha256"],
                    "window": window,
                    "balls": len(objects),
                    "image_sha256": sha256_file(image),
                    "label_sha256": sha256_file(label),
                }
            )
    write_yaml(output, names)
    data = {
        "dataset_version": VERSION,
        "rows": records,
        "full_frames": rows,
        "skipped": skipped,
        "fingerprint": digest_json(records),
        "target": "All annotated balls including reserves",
        "human_review_completed": False,
    }
    write_json(output / "manifest.json", data)
    return data


def role_dataset(root, frames, output):
    """Verzamel persoonscrops en rollen uit de beschikbare bronmanifesten voor de gezamenlijke
    roltraining.
    """
    from .appearance import ROLE_NAMES, TEAM_NAMES

    rows, excluded, seen = [], [], {}
    for p in sorted((root / "datasets").glob("roles-teams-v*/manifest.json"), reverse=True):
        for r in read_json(p)["samples"]:
            if r["split"] not in {"train", "val"}:
                continue
            image = (p.parent / r["image"]).resolve()
            digest = sha256_file(image)
            if r.get("image_sha256", digest) != digest:
                raise ValueError(f"Role source checksum mismatch {image}")
            rows.append({**r, "image": str(image), "image_sha256": digest})
    for f in frames:
        for i, box in enumerate(f["boxes"]):
            role = {"other_person": "person"}.get(box["name"], box["name"])
            if role not in ROLE_NAMES:
                continue
            rows.append(
                {
                    "image": f["image"],
                    "image_sha256": f["image_sha256"],
                    "bbox": box["bbox_xyxy"],
                    "role": role,
                    "team": None,
                    "split": f["split"],
                    "group": f["group"],
                    "id": f"joint-{f['image_sha256']}-{i}",
                    "origin": "joint_full_frame_labels",
                }
            )
    kept = []
    for r in rows:
        key = digest_json([r["image_sha256"], [round(float(v), 2) for v in r["bbox"]]])
        if key in seen:
            previous = seen[key]
            if previous["split"] != r["split"]:
                raise ValueError("Role crop crosses splits")
            excluded.append({"id": r["id"], "reason": "superseded crop annotation", "kept": previous["id"]})
            continue
        seen[key] = r
        # Same semantic geometry can have different original identifiers.
        r = {**r, "id": "crop-" + key}
        kept.append(r)
    kept, pixel_excluded = unique_role_pixels(kept)
    excluded.extend(pixel_excluded)
    output.mkdir(parents=True)
    data = {
        "version": VERSION,
        "role_names": ROLE_NAMES,
        "team_names": TEAM_NAMES,
        "review_policy": "provisional_ai_visual",
        "human_review_completed": False,
        "samples": kept,
        "excluded": excluded,
    }
    write_json(output / "manifest.json", data)
    return data


def unique_role_pixels(rows):
    """Deduplicate the actual padded crop, including differently rounded boxes."""
    from collections import defaultdict

    import numpy as np

    grouped = defaultdict(list)
    for row in rows:
        grouped[row["image"]].append(row)
    seen, kept, excluded = {}, {}, []
    for path, items in grouped.items():
        image = cv2.imread(str(path))
        if image is None:
            raise ValueError(f"Unreadable role source {path}")
        height, width = image.shape[:2]
        for row in items:
            x1, y1, x2, y2 = row["bbox"]
            dx, dy = (x2 - x1) * 0.08, (y2 - y1) * 0.04
            crop = image[
                max(0, int(y1 - dy)) : min(height, int(np.ceil(y2 + dy))),
                max(0, int(x1 - dx)) : min(width, int(np.ceil(x2 + dx))),
            ]
            if not crop.size:
                raise ValueError("Empty role crop")
            key = hashlib.sha256(str(crop.shape).encode() + crop.tobytes()).hexdigest()
            if key in seen:
                prior = seen[key]
                if prior["split"] != row["split"]:
                    raise ValueError("Identical role crop pixels cross splits")
                if prior["role"] != row["role"] or (
                    prior.get("team") and row.get("team") and prior["team"] != row["team"]
                ):
                    raise ValueError("Identical role crop pixels have conflicting labels")
                excluded.append(
                    {
                        "id": row["id"],
                        "kept": prior["id"],
                        "reason": "identical padded crop pixels",
                        "split": row["split"],
                    }
                )
                continue
            seen[key] = row
            kept[row["id"]] = {**row, "crop_pixel_sha256": key}
    return [kept[row["id"]] for row in rows if row["id"] in kept], excluded


def prepare_role_pixel_overlay(dataset):
    """Add an immutable role-only revision while retaining original round inputs."""
    destination = dataset / "roles-pixel-v1/manifest.json"
    original = dataset / "roles/manifest.json"
    if destination.exists():
        data = read_json(destination)
        if data["parent_manifest"]["sha256"] != sha256_file(original):
            raise ValueError("Role overlay parent changed")
        rows = data["samples"]
        excluded = [r for r in data["excluded"] if r["reason"] == "identical padded crop pixels"]
    else:
        data = read_json(original)
        rows, excluded = unique_role_pixels(data["samples"])
        data.update(
            version="joint-local-v2-role-pixel-v1",
            samples=rows,
            excluded=data["excluded"] + excluded,
            parent_manifest={"path": str(original), "sha256": sha256_file(original)},
        )
        destination.parent.mkdir(parents=True)
        write_json(destination, data)
    inventory = read_json(dataset / "inventory.json")
    inventory["dataset_version"] = "joint-local-v2.1-role-pixels"
    inventory["counts"]["roles"] = dict(Counter(row["split"] for row in rows))
    inventory["fingerprints"]["roles"] = sha256_file(destination)
    inventory["task_overrides"] = {
        "roles": {"path": str(destination), "sha256": sha256_file(destination), "removed_crops": excluded}
    }
    inventory["parent_inventory_sha256"] = sha256_file(dataset / "inventory.json")
    inventory["fingerprint"] = digest_json({k: v for k, v in inventory.items() if k != "fingerprint"})
    write_json(dataset / "inventory-final.json", inventory)
    return destination


def check_split_leakage(frames, roles):
    """Vergelijk bronidentiteiten van frames en rolcrops over splits en weiger geconstateerde overlap."""
    images, sources = {}, {}
    for row in [*frames, *roles]:
        for mapping, key in [(images, row["image_sha256"]), (sources, row.get("source_frame_rgb_sha256"))]:
            if key and mapping.setdefault(key, row["split"]) != row["split"]:
                raise ValueError(f"Image crosses task splits: {row['image']}")


def field_dataset(root, output):
    """Verzamel de gecontroleerde lokale veldtrainingsvoorbeelden en schrijf hun gezamenlijke index met
    behouden herkomst.
    """
    from .field_learning import dataset_index

    output.mkdir(parents=True, exist_ok=True)
    combined, excluded, manifests = [], [], []
    for source in [root / "data/course-multimatch-v1/field", root / "data/field-corpus/soccernet"]:
        index = dataset_index(source)
        combined.extend(index["frames"])
        excluded.extend(index["excluded"])
        manifests.append({"source": str(source), "fingerprint": index["fingerprint"]})
    combined, duplicates = unique_rows(combined)
    excluded.extend(duplicates)
    # Bound expensive heatmap validation before observing model outputs. Keep all
    # course references and an evenly spread sample of the much larger corpus.
    valid = [r for r in combined if r["split"] == "valid"]
    course = [r for r in valid if "course-multimatch" in r["image"]]
    remaining = [r for r in valid if r not in course]
    import numpy as np

    validation = course + [
        remaining[i] for i in np.linspace(0, len(remaining) - 1, min(44, len(remaining)), dtype=int)
    ]
    data = {
        "schema_version": 1,
        "dataset_version": VERSION,
        "frames": combined,
        "excluded": excluded,
        "sources": manifests,
        "fingerprint": digest_json(combined),
        "validation_images": [r["image"] for r in validation],
        "validation_policy": "all course validation plus 44 evenly spaced corpus frames, selected before training",
        "pretraining_overlap": True,
        "independent_accuracy_claim": False,
    }
    write_json(output / "index.json", data)
    return data


def prepare(output, root=ROOT, field_index=None):
    """Maak de taakgebonden gezamenlijke datasets, controleer splitoverlap en schrijf de complete lokale
    gegevensinventaris.
    """
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    frames, sources, excluded = gather_frames(root)
    frames, duplicates = unique_rows(frames)
    excluded.extend(duplicates)
    players = [r for r in frames if "player" in r["names"] and "referee" in r["names"]]
    for r in frames:
        if r not in players:
            excluded.append(
                {
                    "image": r["image"],
                    "task": "players",
                    "reason": "No complete explicit player/referee labels; person is not player",
                }
            )
    roles = role_dataset(root, players, output / "roles")
    check_split_leakage(frames, roles["samples"])
    detector = detector_dataset(players, output / "players")
    from persoon1.modeling import yolo

    model = yolo(root / "artifacts/fullscene-ball-v1/fullscene_ball_f005.pt")
    ball = ball_dataset([r for r in frames if "ball" in r["names"]], output / "ball", model.names)
    del model
    if field_index is not None:
        field = read_json(field_index)
        field["dataset_version"] = VERSION
        field["reused_unchanged_field_audit"] = {
            "path": str(Path(field_index).resolve()),
            "sha256": sha256_file(field_index),
        }
        (output / "field").mkdir()
        write_json(output / "field/index.json", field)
    else:
        field = field_dataset(root, output / "field")
    check_split_leakage(
        frames,
        roles["samples"]
        + [{**r, "split": "val" if r["split"] == "valid" else r["split"]} for r in field["frames"]],
    )
    for p in [
        root / "datasets/panoris-ball-ai-v1/selection.json",
        root / "datasets/development-candidates-v1/manifest.json",
        root / "data/field-pose-multicamera-v1/manifest.json",
    ]:
        sources.append(
            {
                "path": str(p),
                "sha256": sha256_file(p),
                "reason": "positive-only ball moments, unlabelled candidates, or incompatible pose labels; retained, not false negative images",
            }
        )
    videos = []
    for folder in [root / "data/uploads", root / "assets"]:
        for p in sorted(folder.rglob("*.mp4")):
            videos.append(
                {
                    "path": str(p),
                    "bytes": p.stat().st_size,
                    "sha256": sha256_file(p),
                    "purpose": "Source identity; no new annotations inferred",
                }
            )
    inventory = {
        "schema_version": 1,
        "dataset_version": VERSION,
        "source_manifests": sources,
        "frames": frames,
        "videos": videos,
        "excluded": excluded,
        "counts": {
            "players": dict(Counter(r["split"] for r in detector["frames"])),
            "roles": dict(Counter(r["split"] for r in roles["samples"])),
            "ball_tiles": dict(Counter(r["split"] for r in ball["rows"])),
            "field": dict(Counter(r["split"] for r in field["frames"])),
        },
        "field_validation_selection": len(field["validation_images"]),
        "human_review_completed": False,
        "test_images_accessed": False,
        "fingerprints": {
            "players": detector["fingerprint"],
            "ball": ball["fingerprint"],
            "field": field["fingerprint"],
            "roles": sha256_file(output / "roles/manifest.json"),
        },
    }
    inventory["fingerprint"] = digest_json(inventory)
    write_json(output / "inventory.json", inventory)
    print(inventory["counts"], flush=True)
    return inventory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--field-index", type=Path, help="Reuse a frozen field audit when only detector annotations change"
    )
    args = parser.parse_args()
    prepare(args.output, field_index=args.field_index)
