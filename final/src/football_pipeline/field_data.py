"""Bounded, resumable field-training corpus; downloaded highlights are never ground truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

from .contracts import sha256_file, write_json

GIB = 1024**3
DATASET = "https://huggingface.co/datasets/SoccerNet/SN-Calibration-2023"
CHANNELS = [
    "https://www.youtube.com/@fifa",
    "https://www.youtube.com/@seriea",
    "https://www.youtube.com/@bundesliga",
    "https://www.youtube.com/@UEFA",
    "https://www.youtube.com/@LaLiga",
    "https://www.youtube.com/@BarclaysWSL",
]


class CorpusBudget:
    def __init__(self, root, limit=20 * GIB):
        self.root, self.limit = Path(root).resolve(), limit
        self.root.mkdir(parents=True, exist_ok=True)
        self._cached_used = None

    def used(self):
        if self._cached_used is not None:
            return self._cached_used
        return sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file())

    def start_tracking(self):
        self._cached_used = None
        self._cached_used = self.used()

    def account(self, change):
        if self._cached_used is not None:
            self._cached_used += change

    def require(self, additional):
        if additional < 0 or self.used() + additional > self.limit:
            raise ValueError("Corpus storage budget exceeded; reduce the selection or increase --limit-gib")
        if shutil.disk_usage(self.root).free < additional + GIB:
            raise ValueError("Insufficient free disk space (1 GiB reserve required)")

    def write_json(self, path, value):
        if not Path(path).resolve().is_relative_to(self.root):
            raise ValueError("Corpus metadata must remain inside its root")
        content = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)
        size = len(content.replace("\n", os.linesep).encode("utf-8"))
        previous = Path(path).stat().st_size if Path(path).exists() else 0
        self.require(size)
        write_json(path, value)
        self.account(Path(path).stat().st_size - previous)


def download(url, destination, budget, expected_size=None, expected_sha256=None):
    """Resume only the same URL/ETag, verify completed content before skipping it."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    record = destination.with_suffix(destination.suffix + ".download.json")
    old = json.loads(record.read_text(encoding="utf-8")) if record.exists() else {}
    if destination.exists():
        if old.get("url") == url and old.get("sha256") == sha256_file(destination):
            if expected_sha256 and old["sha256"] != expected_sha256:
                raise ValueError("Downloaded bytes do not match the source checksum")
            return old
        raise ValueError(f"Existing download failed provenance/hash validation: {destination}")
    partial = destination.with_suffix(destination.suffix + ".part")
    offset = partial.stat().st_size if partial.exists() else 0
    if offset and old.get("url") != url:
        raise ValueError("Partial download belongs to another URL")
    if expected_size and offset == expected_size:
        actual_hash = sha256_file(partial)
        if expected_sha256 and actual_hash != expected_sha256:
            raise ValueError("Complete partial file does not match the source checksum")
        partial.replace(destination)
        old.update(status="complete", bytes=offset, sha256=actual_hash)
        budget.write_json(record, old)
        return old
    if expected_size and offset > expected_size:
        raise ValueError("Partial download exceeds source length; preserve it and use a fresh destination")
    headers = {"User-Agent": "Messi10-field-research/1.0"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
        if old.get("etag"):
            headers["If-Range"] = old["etag"]
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
        resumed = offset and response.status == 206
        if resumed and not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
            raise ValueError("Server resumed at an unexpected byte offset")
        remaining = int(response.headers.get("Content-Length", "0"))
        budget.require(max(0, remaining - (offset if offset and not resumed else 0)))
        previous_partial = offset
        if not resumed:
            offset = 0
        info = {"url": url, "etag": response.headers.get("ETag"), "status": "downloading"}
        budget.write_json(record, info)
        tick = time.monotonic()
        with partial.open("ab" if resumed else "wb") as stream:
            if not resumed:
                budget.account(-previous_partial)
            while chunk := response.read(4 * 1024**2):
                # A known Content-Length was already reserved before writing.
                if not remaining:
                    budget.require(len(chunk) + 4096)
                stream.write(chunk)
                budget.account(len(chunk))
                offset += len(chunk)
                if time.monotonic() - tick > 10:
                    print(f"{destination.name}: {offset / GIB:.2f} GiB", flush=True)
                    tick = time.monotonic()
        if expected_size is not None and offset != expected_size:
            raise ValueError(f"Incomplete download: {offset} != {expected_size}")
    info.update(status="complete", bytes=offset, sha256=sha256_file(partial))
    if expected_sha256 and info["sha256"] != expected_sha256:
        raise ValueError("Downloaded bytes do not match the source checksum")
    partial.replace(destination)
    budget.write_json(record, info)
    return info


def extract_archive(archive, output, budget):
    """Verify ZIP CRCs and reject traversal; retain archives for verified resumption."""
    output = Path(output).resolve()
    marker = output / (Path(archive).stem + ".extracted.json")
    archive_hash = sha256_file(archive)
    if marker.exists():
        saved = json.loads(marker.read_text(encoding="utf-8"))
        if saved["archive_sha256"] == archive_hash and all(
            (output / p).is_file() and sha256_file(output / p) == h for p, h in saved["files"].items()
        ):
            return saved
        raise ValueError("Previously extracted dataset changed")
    with zipfile.ZipFile(archive) as bundle:
        members = [m for m in bundle.infolist() if not m.is_dir()]
        files = {}
        for member in members:
            target = (output / member.filename).resolve()
            if not target.is_relative_to(output) or (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Unsafe archive path")
        budget.require(
            sum(
                max(
                    0,
                    m.file_size
                    - ((output / m.filename).stat().st_size if (output / m.filename).exists() else 0),
                )
                for m in members
            )
        )
        for member in members:
            target = output / member.filename
            # Reading every member checks CRC even after an interrupted extraction.
            data = bundle.read(member)
            files[member.filename] = hashlib.sha256(data).hexdigest()
            if target.exists() and target.read_bytes() == data:
                continue
            old_size = target.stat().st_size if target.exists() else 0
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            budget.account(len(data) - old_size)
    saved = {
        "archive_sha256": archive_hash,
        "files": files,
    }
    budget.write_json(marker, saved)
    return saved


def collect_dataset(root, budget, splits=("train", "valid")):
    listing = json.load(
        urllib.request.urlopen(
            "https://huggingface.co/api/datasets/SoccerNet/SN-Calibration-2023/tree/main", timeout=60
        )
    )
    inventory = {
        "source": DATASET,
        "splits": {},
        "official_split_policy": True,
        "pretraining_overlap": True,
        "independent_accuracy_claim": False,
    }
    if (root / "dataset-inventory.json").exists():
        inventory = json.loads((root / "dataset-inventory.json").read_text(encoding="utf-8"))
    for split in splits:
        spec = next(item for item in listing if item["path"] == split + ".zip")
        path = root / "archives" / spec["path"]
        for attempt in range(12):
            try:
                result = download(
                    f"{DATASET}/resolve/main/{spec['path']}?download=true",
                    path,
                    budget,
                    spec["size"],
                    spec.get("lfs", {}).get("oid"),
                )
                break
            except (OSError, ValueError) as exc:
                if "budget" in str(exc).lower() or attempt == 11:
                    raise
                print(f"Resuming {split}: {exc}", flush=True)
        extract_archive(path, root / "soccernet", budget)
        inventory["splits"][split] = result
        budget.write_json(root / "dataset-inventory.json", inventory)
    return inventory


def match_split(match_id):
    bucket = int(hashlib.sha256(match_id.encode()).hexdigest()[:8], 16) % 10
    return "train" if bucket < 7 else "valid" if bucket < 9 else "test"


def identify_match(title):
    """Conservative candidate ID. A title alone never certifies training eligibility."""
    title = title.lower().replace("–", "-").replace("—", "-")
    if not re.search(r"\b(v|vs|versus)\b|\w\s*-\s*\w", title):
        return None
    if re.search(r"compilation|all goals|best goals|top \d|every goal", title):
        return None
    return re.sub(r"[^a-z0-9]+", "-", title).strip("-")


def discover_highlights(root, per_channel=25, budget=None):
    import yt_dlp

    destination = root / "highlight-inventory.json"
    inventory = (
        json.loads(destination.read_text(encoding="utf-8"))
        if destination.exists()
        else {"videos": [], "searches": []}
    )
    known = {v["id"] for v in inventory["videos"]}
    for channel in CHANNELS:
        query = channel + "/search?query=extended%20highlights"
        try:
            with yt_dlp.YoutubeDL(
                {
                    "extract_flat": True,
                    "skip_download": True,
                    "quiet": True,
                    "playlistend": per_channel,
                    "socket_timeout": 25,
                    "retries": 1,
                }
            ) as client:
                result = client.extract_info(query, download=False)
            entries = list(result.get("entries", []))
            inventory["searches"].append({"url": query, "status": "complete", "found": len(entries)})
            for entry in entries:
                if not entry or entry.get("id") in known:
                    continue
                title = entry.get("title", "")
                duration = entry.get("duration")
                if "highlight" not in title.lower() or (duration and not 90 <= duration <= 1800):
                    continue
                identifier = identify_match(title)
                inventory["videos"].append(
                    {
                        "id": entry["id"],
                        "url": f"https://www.youtube.com/watch?v={entry['id']}",
                        "title": title,
                        "channel_source": channel,
                        "duration_s": duration,
                        "match_id": identifier,
                        "match_identity_verified": False,
                        "split": match_split(identifier) if identifier else "unassigned",
                        "status": "candidate",
                        "training_eligible": False,
                        "usage": "Local research collection; training rights not independently confirmed",
                        "terms_url": "https://www.youtube.com/static?template=terms",
                    }
                )
                known.add(entry["id"])
        except Exception as exc:
            inventory["searches"].append({"url": query, "status": "failed", "error": str(exc)})
        (budget.write_json if budget else write_json)(destination, inventory)
    return inventory


def collect_highlights(root, budget, ffmpeg, count=30):
    import yt_dlp

    path = root / "highlight-inventory.json"
    inventory = json.loads(path.read_text(encoding="utf-8"))
    completed, matches = 0, set()
    # Round-robin channels so one league does not consume the collection.
    candidates = sorted(
        inventory["videos"],
        key=lambda v: (
            [x["id"] for x in inventory["videos"] if x["channel_source"] == v["channel_source"]].index(
                v["id"]
            ),
            CHANNELS.index(v["channel_source"]),
        ),
    )
    for item in candidates:
        if completed >= count:
            break
        if not item.get("match_id") or item["match_id"] in matches:
            continue
        file = root / "highlights" / (item["id"] + ".mp4")
        if item["status"] == "complete":
            if not file.exists() or sha256_file(file) != item["sha256"]:
                raise ValueError(f"Highlight changed: {file}")
            completed += 1
            matches.add(item["match_id"])
            continue

        def hook(progress):
            if progress["status"] == "downloading":
                if progress.get("downloaded_bytes", 0) > 192 * 1024**2:
                    raise ValueError("Media stream exceeds the per-file storage reservation")

        try:
            # Two <=192 MiB streams plus merge temporaries fit within a 1 GiB reservation.
            budget.require(GIB)
            options = {
                "format": "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]",
                "js_runtimes": {"node": {}},
                "outtmpl": str(file),
                "merge_output_format": "mp4",
                "noplaylist": True,
                "ffmpeg_location": str(ffmpeg),
                "progress_hooks": [hook],
                "quiet": True,
                "noprogress": True,
                "socket_timeout": 25,
                "retries": 1,
                "fragment_retries": 1,
                "max_filesize": 192 * 1024**2,
                "overwrites": False,
            }
            with yt_dlp.YoutubeDL(options) as client:
                metadata = client.extract_info(item["url"], download=True)
            if not file.exists():
                raise ValueError("Downloader did not produce a complete MP4")
            item.update(
                status="complete",
                file=str(file.relative_to(root)),
                sha256=sha256_file(file),
                bytes=file.stat().st_size,
                license=metadata.get("license"),
                channel=metadata.get("channel"),
                channel_id=metadata.get("channel_id"),
                upload_date=metadata.get("upload_date"),
                duration_s=metadata.get("duration"),
            )
            completed += 1
            matches.add(item["match_id"])
            print(f"Highlights: {completed}/{count}: {item['title']}", flush=True)
        except Exception as exc:
            item.update(status="failed", error=str(exc))
            print(f"Highlight unavailable: {item['id']}: {exc}", flush=True)
        # yt-dlp owns stream/merge temporaries; reconcile its actual writes after each bounded transfer.
        budget.start_tracking()
        budget.require(0)
        budget.write_json(path, inventory)
    inventory.update(
        completed=sum(v["status"] == "complete" for v in inventory["videos"]),
        target=count,
        corpus_bytes=budget.used(),
        limit_bytes=budget.limit,
    )
    budget.write_json(path, inventory)
    return inventory


def frame_signature(image):
    import cv2

    small = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (9, 8))
    return (small[:, 1:] > small[:, :-1]).flatten()


def near_duplicate(signature, previous, maximum=5):
    import numpy as np

    return any(np.count_nonzero(signature != other) <= maximum for other in previous)


def sampled_frames(video, fps, size, ffmpeg):
    """Decode at most five analysis frames/s; selected source frame indices remain exact for CFR video."""
    import numpy as np

    stride = max(1, int(np.ceil(fps / 5)))
    width, height = size
    step = 0
    for gpu in (True, False):
        select = f"select=not(mod(n\\,{stride}))"
        filters = (
            f"{select},scale_cuda={width}:{height}:format=nv12,hwdownload,format=nv12"
            if gpu
            else f"{select},scale={width}:{height}"
        )
        command = [str(ffmpeg), "-v", "error", "-threads", "4"]
        if gpu:
            command += ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
        command += [
            "-noautorotate",
            "-i",
            str(video),
            "-an",
            "-vf",
            filters,
            "-fps_mode",
            "vfr",
            "-pix_fmt",
            "bgr24",
            "-f",
            "rawvideo",
            "pipe:1",
        ]
        with tempfile.TemporaryFile() as error_log:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=error_log)
            try:
                while True:
                    data = process.stdout.read(width * height * 3)
                    if not data:
                        break
                    if len(data) != width * height * 3:
                        raise ValueError("Truncated decoded analysis frame")
                    yield step * stride, np.frombuffer(data, np.uint8).reshape(height, width, 3)
                    step += 1
                process.wait()
                if not process.returncode:
                    return
                if step:
                    raise ValueError("Video decoding failed after partial output")
                if not gpu:
                    error_log.seek(0)
                    raise ValueError(error_log.read().decode(errors="replace")[-2000:])
                print("Hardware frame sampling unavailable; retrying with CPU FFmpeg", flush=True)
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=30)
                process.stdout.close()


def prepare_frames(root, budget, maximum_per_video=180, ffmpeg=None):
    import cv2
    import numpy as np

    from .video import find_tool

    ffmpeg = ffmpeg or find_tool("ffmpeg")

    inventory = json.loads((root / "highlight-inventory.json").read_text(encoding="utf-8"))
    for item in inventory["videos"]:
        if item["status"] != "complete":
            continue
        output = root / "frames" / item["id"]
        manifest = output / "manifest.json"
        if manifest.exists():
            saved = json.loads(manifest.read_text(encoding="utf-8"))
            if saved["video_sha256"] != item["sha256"] or not all(
                (output / f["image"]).exists() and sha256_file(output / f["image"]) == f["sha256"]
                for f in saved["frames"]
            ):
                raise ValueError("Prepared frame cache changed")
            continue
        video = root / item["file"]
        if sha256_file(video) != item["sha256"]:
            raise ValueError("Video hash changed")
        output.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(str(video))
        fps = cap.get(cv2.CAP_PROP_FPS)
        source_size = [int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))]
        cap.release()
        if not np.isfinite(fps) or fps <= 0:
            raise ValueError("Invalid video framerate")
        previous, histogram, signatures, rows = None, None, [], []
        scale = min(1.0, 1280 / source_size[0])
        analysis_size = [max(2, round(value * scale / 2) * 2) for value in source_size]
        shot, last_selected = 0, -2 * fps
        iterator = sampled_frames(video, fps, analysis_size, ffmpeg)
        try:
            for index, frame in iterator:
                if len(rows) >= maximum_per_video:
                    break
                small = cv2.resize(frame, (160, 90))
                hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
                hist = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256])
                cv2.normalize(hist, hist)
                cut = previous is not None and (
                    np.abs(small.astype(float) - previous).mean() > 45
                    or cv2.compareHist(hist, histogram, cv2.HISTCMP_BHATTACHARYYA) > 0.55
                )
                if cut:
                    shot += 1
                if index - last_selected >= 2 * fps and not cut:
                    signature = frame_signature(small)
                    if not near_duplicate(signature, signatures):
                        grass = cv2.inRange(hsv, (25, 40, 30), (95, 255, 255)).mean() / 255
                        # Routing heuristic only: reviewers must decide actual calibratability.
                        category = "overview_candidates" if grass >= 0.35 else "closeup_candidates"
                        name = f"{category}/{index:08d}.jpg"
                        height, width = frame.shape[:2]
                        resized = cv2.resize(
                            frame, (min(width, 1280), round(height * min(width, 1280) / width))
                        )
                        ok, encoded = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, 88])
                        if not ok:
                            raise ValueError("JPEG encoding failed")
                        budget.require(encoded.nbytes + 4096)
                        target = output / name
                        target.parent.mkdir(exist_ok=True)
                        previous_bytes = target.stat().st_size if target.exists() else 0
                        target.write_bytes(encoded.tobytes())
                        budget.account(encoded.nbytes - previous_bytes)
                        rows.append(
                            {
                                "frame_index": index,
                                "timestamp_s": index / fps,
                                "shot": shot,
                                "image": name,
                                "sha256": sha256_file(target),
                                "grass_fraction": grass,
                                "source_size": source_size,
                                "image_size": list(resized.shape[1::-1]),
                                "label_status": "unlabelled",
                                "training_eligible": False,
                            }
                        )
                        signatures.append(signature)
                        last_selected = index
                previous, histogram = small, hist
        finally:
            iterator.close()
        budget.write_json(
            manifest,
            {
                "schema_version": 1,
                "video_sha256": item["sha256"],
                "source": item["url"],
                "match_id": item["match_id"],
                "match_identity_verified": False,
                "split": item["split"],
                "frames": rows,
                "minimum_spacing_s": 2,
                "category_is_heuristic": True,
                "analysis_fps_maximum": 5,
                "timestamp_basis": "source_frame_index_divided_by_declared_fps_CFR_assumption",
                "training_eligible": False,
            },
        )
        print(f"Prepared {item['id']}: {len(rows)} frames", flush=True)


def main():
    from filelock import FileLock

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["dataset", "discover", "highlights", "frames", "status"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--limit-gib", type=float, default=20)
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--ffmpeg", type=Path)
    parser.add_argument("--split", choices=["train", "valid"], action="append")
    args = parser.parse_args()
    if args.limit_gib <= 0 or args.count < 1:
        parser.error("--limit-gib and --count must be positive")
    root = args.root.resolve()
    budget = CorpusBudget(root, int(args.limit_gib * GIB))
    if args.command == "status":
        print(json.dumps({"root": str(root), "used_bytes": budget.used(), "limit_bytes": budget.limit}))
        return
    # One writer per corpus prevents competing downloads/extraction from spending the same free budget.
    with FileLock(str(root / ".writer.lock")):
        budget.start_tracking()
        if args.command == "dataset":
            collect_dataset(root, budget, args.split or ("train", "valid"))
        elif args.command == "discover":
            discover_highlights(root, budget=budget)
        elif args.command == "highlights":
            if not args.ffmpeg or not args.ffmpeg.is_file():
                parser.error("--ffmpeg must point to ffmpeg.exe")
            collect_highlights(root, budget, args.ffmpeg, args.count)
        elif args.command == "frames":
            prepare_frames(root, budget, ffmpeg=args.ffmpeg)
    print(json.dumps({"root": str(root), "used_bytes": budget.used(), "limit_bytes": budget.limit}))


if __name__ == "__main__":
    main()
