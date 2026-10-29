"""Leest echte presentatietijdstippen met PyAV en kan daardoor ook variabele-frameratebronnen voor data-extractie verwerken."""

from pathlib import Path

from .core import now, read_json, sha256, write_json


def frames(path, as_image=True):
    import av
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        first = None
        previous = -1.0
        for index, frame in enumerate(container.decode(stream)):
            if frame.pts is None or frame.time_base is None:
                raise ValueError("Missing presentation timestamps. Convert source to a documented CFR MP4 first.")
            absolute = float(frame.pts * frame.time_base)
            if first is None:
                first = absolute
            stamp = absolute - first
            if stamp < previous:
                raise ValueError("Non-monotonic presentation timestamps")
            previous = stamp
            yield index, stamp, frame.to_image() if as_image else frame


def inspect_video(path, output):
    import av
    path = Path(path).resolve()
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        record = {"video_id": sha256(path), "file": str(path), "recorded_at": now(),
                  "width": stream.width, "height": stream.height,
                  "declared_fps": str(stream.average_rate) if stream.average_rate else None,
                  "container_duration_s": container.duration / av.time_base if container.duration else None,
                  "camera_approved": False, "source_approved": False}
    total, last, intervals = 0, None, set()
    for _, stamp, _ in frames(path, as_image=False):
        if last is not None:
            intervals.add(round(stamp - last, 6))
        last, total = stamp, total + 1
    if not total:
        raise ValueError("Video contains no decoded frames")
    record.update(decoded_frames=total, last_timestamp_s=last, observed_frame_intervals_s=sorted(intervals))
    write_json(output, record)
    return record


def extract(path, plan_path, output_dir):
    """Execute explicit source windows, preserving groups and held-out membership."""
    path, output_dir = Path(path).resolve(), Path(output_dir).resolve()
    plan = read_json(plan_path)
    if output_dir.exists():
        raise ValueError("Use a new output directory; never overwrite an existing dataset")
    names = plan.get("names")
    windows = plan.get("windows", [])
    if not names or not windows:
        raise ValueError("Extraction plan requires names and windows")
    groups, previous_end = set(), -1.0
    for window in sorted(windows, key=lambda w: w["start_s"]):
        if window["split"] not in ("train", "val", "test") or not window.get("group_id") or window["group_id"] in groups:
            raise ValueError("Each window requires a unique group_id and valid split")
        if not (0 <= window["start_s"] < window["end_s"] and window.get("every_s", 1) > 0) or window["start_s"] < previous_end:
            raise ValueError("Invalid or overlapping source windows")
        groups.add(window["group_id"])
        previous_end = window["end_s"]
    output_dir.mkdir(parents=True)
    (output_dir / "images").mkdir()
    video_id = sha256(path)
    selected = []
    due = {w["group_id"]: w["start_s"] for w in windows}
    for index, stamp, decoded in frames(path, as_image=False):
        for window in windows:
            group = window["group_id"]
            if window["start_s"] <= stamp < window["end_s"] and stamp + 1e-8 >= due[group]:
                image = decoded.to_image()
                fid = f"{video_id[:12]}_{index:08d}"
                image_file = f"images/{fid}.png"
                image.save(output_dir / image_file)
                selected.append({"frame_id": fid, "video_id": video_id, "frame_index": index,
                                 "timestamp_s": stamp, "width": image.width, "height": image.height,
                                 "group_id": group, "split": window["split"], "image": image_file,
                                 "label": f"labels/{fid}.txt", "label_status": "unlabelled",
                                 "annotator": "", "reviewer": "", "review_status": "open",
                                 "selection_reason": window.get("reason", "Predefined time window; difficulty to review")})
                due[group] = stamp + window.get("every_s", 1)
        if stamp >= max(w["end_s"] for w in windows):
            break
    manifest = {"schema_version": "1.0", "dataset_version": "draft-001", "names": names,
                "video": {"video_id": video_id, "file": str(path), "timing": "PTS relative to first presented frame"},
                "minimum_split_gap_s": plan.get("minimum_split_gap_s", 5), "frames": selected}
    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "extraction-plan.json", plan)
    return {"frames": len(selected), "manifest": str(output_dir / "manifest.json"), "status": "unlabelled_unreviewed"}
