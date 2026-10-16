"""Dataset provenance and review gates. Heavy ML dependencies are loaded lazily."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def environment():
    result = {"recorded_at": now(), "python": sys.version, "platform": platform.platform(), "packages": {}}
    code_root = Path(__file__).resolve().parent
    result["source_code_sha256"] = {str(p.relative_to(code_root)): sha256(p) for p in sorted(code_root.glob("*.py"))}
    for name in ("torch", "torchvision", "ultralytics", "numpy", "opencv-python", "Pillow", "PyYAML", "av"):
        try:
            result["packages"][name] = version(name)
        except PackageNotFoundError:
            result["packages"][name] = None
    try:
        result["nvidia_smi"] = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv,noheader"],
            text=True, stderr=subprocess.STDOUT, timeout=15,
        ).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        result["nvidia_smi"] = str(exc)
    try:
        result["git_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
        result["git_dirty"] = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True))
    except (OSError, subprocess.SubprocessError):
        result["git_commit"] = None
    try:
        import torch
        result["cuda_available"] = torch.cuda.is_available()
        result["torch_cuda"] = torch.version.cuda
        if result["cuda_available"]:
            result["gpu"] = torch.cuda.get_device_name(0)
            result["gpu_total_bytes"] = torch.cuda.get_device_properties(0).total_memory
    except (ImportError, OSError) as exc:
        result["cuda_available"] = False
        result["torch_error"] = str(exc)
    return result


def load_manifest(path):
    path = Path(path).resolve()
    data = read_json(path)
    if data.get("schema_version") != "1.0":
        raise ValueError("Manifest requires schema_version 1.0")
    names = data.get("names")
    if not isinstance(names, list) or not names or any(not isinstance(n, str) or not n.strip() for n in names) or len(set(names)) != len(names):
        raise ValueError("names must contain unique nonempty class names")
    if not isinstance(data.get("frames"), list):
        raise ValueError("frames must be a list")
    for frame in data["frames"]:
        if not isinstance(frame, dict):
            raise ValueError("Each frame must be an object")
        fid = frame.get("frame_id")
        if not isinstance(fid, str) or not fid or Path(fid).name != fid or any(c in fid for c in '/\\:'):
            raise ValueError("frame_id must be a safe nonempty filename component")
    return data, path.parent


def dataset_path(root, relative):
    if not isinstance(relative, str) or not relative:
        raise ValueError("Missing dataset-relative path")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Dataset path escapes manifest directory: {relative}")
    return path


def read_labels(path, class_count):
    labels = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        pieces = line.split()
        if len(pieces) != 5:
            raise ValueError(f"{path}:{number}: expected class xc yc w h")
        try:
            cls = int(pieces[0])
            xc, yc, w, h = map(float, pieces[1:])
        except ValueError as exc:
            raise ValueError(f"{path}:{number}: invalid numeric values") from exc
        if not 0 <= cls < class_count or not all(map(math.isfinite, (xc, yc, w, h))):
            raise ValueError(f"{path}:{number}: invalid class or non-finite coordinate")
        if not (0 < w <= 1 and 0 < h <= 1 and xc - w / 2 >= -1e-6 and yc - h / 2 >= -1e-6 and xc + w / 2 <= 1 + 1e-6 and yc + h / 2 <= 1 + 1e-6):
            raise ValueError(f"{path}:{number}: box lies outside image or has no area")
        labels.append({"class_id": cls, "xywh": [xc, yc, w, h]})
    return labels


def label_pixels(label, width, height):
    x, y, w, h = label["xywh"]
    return [(x - w / 2) * width, (y - h / 2) * height, (x + w / 2) * width, (y + h / 2) * height]


def validate_dataset(manifest_path, require_review=False, min_frames=40, max_frames=80):
    """Return errors instead of silently treating absent labels as negative samples."""
    from PIL import Image, ImageOps
    data, root = load_manifest(manifest_path)
    errors, warnings = [], []
    seen_ids, seen_source = set(), set()
    groups, exact, perceptual = defaultdict(set), {}, []
    near_counts, near_examples = Counter(), []
    counts = defaultdict(Counter)
    fingerprint_files = []
    if not min_frames <= len(data["frames"]) <= max_frames:
        errors.append(f"Expected {min_frames}–{max_frames} frames, found {len(data['frames'])}")
    for frame in data["frames"]:
        fid = frame.get("frame_id", "<missing>")
        try:
            if not isinstance(fid, str) or not fid or fid in seen_ids:
                raise ValueError("missing or duplicate frame_id")
            seen_ids.add(fid)
            split = frame.get("split")
            if split not in ("train", "val", "test"):
                raise ValueError("split must be train, val or test")
            if not frame.get("video_id") or not frame.get("group_id"):
                raise ValueError("video_id and group_id are required")
            idx, stamp = frame.get("frame_index"), frame.get("timestamp_s")
            if type(idx) is not int or idx < 0 or type(stamp) not in (int, float) or not math.isfinite(stamp) or stamp < 0:
                raise ValueError("invalid source frame index or presentation timestamp")
            key = (frame["video_id"], idx)
            if key in seen_source:
                raise ValueError("source frame appears more than once")
            seen_source.add(key)
            groups[(frame["video_id"], frame["group_id"])].add(split)
            counts[split]["frames"] += 1
            image_path = dataset_path(root, frame["image"])
            label_path = dataset_path(root, frame["label"])
            with Image.open(image_path) as image:
                image.load()
                if image.size != (frame.get("width"), frame.get("height")):
                    raise ValueError("manifest image dimensions differ from actual image")
                decoded = hashlib.sha256(image.convert("RGB").tobytes() + str(image.size).encode()).hexdigest()
                small = list(ImageOps.grayscale(image).resize((9, 8)).getdata())
                dhash = sum((small[y * 9 + x] > small[y * 9 + x + 1]) << (y * 8 + x) for y in range(8) for x in range(8))
            if decoded in exact:
                errors.append(f"{fid}: duplicate pixels of {exact[decoded]}")
            exact[decoded] = fid
            perceptual.append((fid, split, dhash))
            fingerprint_files.append([fid, sha256(image_path), sha256(label_path) if label_path.is_file() else None])
            labels = read_labels(label_path, len(data["names"]))
            if not labels and frame.get("label_status") != "negative":
                raise ValueError("empty labels require explicit label_status=negative")
            if labels and frame.get("label_status") != "positive":
                raise ValueError("nonempty labels require label_status=positive")
            if require_review:
                author, reviewer = frame.get("annotator", "").strip(), frame.get("reviewer", "").strip()
                if not author or not reviewer or author.casefold() == reviewer.casefold() or frame.get("review_status") != "approved":
                    raise ValueError("requires actual independent annotation review")
            counts[split]["labelled_frames"] += 1
            counts[split]["reviewed_frames"] += frame.get("review_status") == "approved"
            counts[split]["negative_frames"] += not labels
            for label in labels:
                counts[split][f"class_{label['class_id']}_objects"] += 1
        except (ValueError, KeyError, OSError, TypeError) as exc:
            errors.append(f"{fid}: {exc}")
    for group, splits in groups.items():
        if len(splits) != 1:
            errors.append(f"Group {group} crosses subsets: {sorted(splits)}")
    for i, (fid, split, dhash) in enumerate(perceptual):
        for other, other_split, other_hash in perceptual[:i]:
            if split != other_split and (dhash ^ other_hash).bit_count() <= 4:
                near_counts["/".join(sorted((split, other_split)))] += 1
                if len(near_examples) < 10:
                    near_examples.append([fid, other])
    for pair, count in sorted(near_counts.items()):
        warnings.append(f"Global-image similarity screen: {count} near-duplicate pairs across {pair}; static backgrounds can trigger this. Manual action/group review required.")
    # A minimum time gap is a screening aid, never a claim of statistical independence.
    frames = [f for f in data["frames"] if type(f.get("timestamp_s")) in (int, float) and math.isfinite(f["timestamp_s"])]
    frames = sorted(frames, key=lambda f: (str(f.get("video_id")), f["timestamp_s"]))
    gap = data.get("minimum_split_gap_s", 5.0)
    if type(gap) not in (int, float) or not math.isfinite(gap) or gap < 0:
        raise ValueError("minimum_split_gap_s must be a finite nonnegative number")
    for i, frame in enumerate(frames):
        for other in frames[:i]:
            if frame.get("video_id") == other.get("video_id") and frame.get("split") != other.get("split"):
                if abs(frame.get("timestamp_s", 0) - other.get("timestamp_s", 0)) < gap:
                    errors.append(f"Cross-subset source moments too close: {frame.get('frame_id')} / {other.get('frame_id')}")
    for split in ("train", "val", "test"):
        if not counts[split]["frames"]:
            errors.append(f"No frames in {split}; independent end evaluation is required for this tooling route")
        for cls in range(len(data["names"])):
            if not counts[split][f"class_{cls}_objects"]:
                errors.append(f"No objects of class {data['names'][cls]} in {split}")
    return {"recorded_at": now(), "errors": errors, "warnings": warnings,
            "counts": dict(counts), "near_duplicate_pair_counts": dict(near_counts), "near_duplicate_examples": near_examples,
            "dataset_fingerprint": canonical_hash([data, sorted(fingerprint_files)])}


def require_approval(manifest_path, approval_path):
    report = validate_dataset(manifest_path, require_review=True)
    if report["errors"]:
        raise ValueError("Dataset not ready: " + "; ".join(report["errors"][:8]))
    approval = read_json(approval_path)
    if approval.get("dataset_fingerprint") != report["dataset_fingerprint"]:
        raise ValueError("Approval does not match the current dataset contents")
    reviewers = approval.get("reviewers", [])
    if len(reviewers) != 2 or any(not isinstance(r, str) or not r.strip() for r in reviewers) or reviewers[0].strip().casefold() == reviewers[1].strip().casefold():
        raise ValueError("Record both distinct actual team reviewers")
    for key in ("source_approved", "label_rules_approved", "split_approved", "class_coverage_approved", "model_roles_approved", "near_duplicates_reviewed"):
        if approval.get(key) is not True:
            raise ValueError(f"Missing actual team decision: {key}")
    return report
