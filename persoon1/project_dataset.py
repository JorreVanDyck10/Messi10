"""Reconstrueert de voorlopige baldataset uit de exacte bronvideo en expliciete annotaties."""

import argparse
from pathlib import Path

from .core import now, read_json, sha256, validate_dataset, write_json


def prepare(video, selection, output):
    import av
    from PIL import ImageDraw
    video, output = Path(video), Path(output)
    specification = read_json(selection)
    if sha256(video) != specification["video_sha256"]:
        raise ValueError("Source video does not match the recorded annotation source")
    if output.exists():
        raise ValueError("Use a new output directory to preserve dataset versions")
    for sub in ("images", "labels", "evidence"):
        (output / sub).mkdir(parents=True, exist_ok=True)
    wanted = {r["frame_index"]: r for r in specification["frames"]}
    frames = []
    with av.open(str(video)) as container:
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        for index, source in enumerate(container.decode(stream)):
            if index not in wanted:
                continue
            row = wanted[index]
            image = source.to_image()
            width, height = image.size
            fid = specification["video_sha256"][:12] + f"_{index:08d}"
            image.save(output / "images" / f"{fid}.png")
            x, y, w, h = row["bbox_xywh"]
            (output / "labels" / f"{fid}.txt").write_text(
                f"0 {(x+w/2)/width:.10f} {(y+h/2)/height:.10f} {w/width:.10f} {h/height:.10f}\n", encoding="utf-8")
            # Native context and a magnified view let a teammate challenge each box.
            crop = image.crop((x-32, y-32, x+64, y+64)).resize((576, 576))
            ImageDraw.Draw(crop).rectangle((192, 192, (32+w)*6, (32+h)*6), outline="red", width=2)
            evidence = output / "evidence" / f"{fid}.png"
            crop.save(evidence)
            stamp = float(source.pts * stream.time_base)
            if abs(stamp - row["timestamp_s"]) > 0.001:
                raise ValueError("Source timing differs from the recorded annotation")
            frames.append({"frame_id": fid, "video_id": specification["video_sha256"],
                "frame_index": index, "timestamp_s": stamp, "width": width, "height": height,
                "group_id": row["group_id"], "split": row["split"],
                "image": f"images/{fid}.png", "label": f"labels/{fid}.txt",
                "label_status": "positive", "annotator": "Codex AI", "reviewer": "",
                "review_status": "ai_visual_checked", "visual_evidence": f"evidence/{fid}.png",
                "visual_evidence_sha256": sha256(evidence), "selection_reason": row["selection_reason"]})
            if len(frames) == len(wanted):
                break
    if len(frames) != len(wanted):
        raise ValueError("Not all recorded source frames were decoded")
    manifest = output / "manifest.json"
    write_json(manifest, {"schema_version": "1.0", "dataset_version": specification["dataset_version"],
        "names": ["ball"], "video": {"video_id": specification["video_sha256"], "file": str(video.resolve())},
        "minimum_split_gap_s": 6.0, "review_policy": "provisional_ai_visual", "human_review_completed": False,
        "scope": specification["scope"], "selection_sha256": sha256(selection), "frames": frames})
    report = validate_dataset(manifest)
    write_json(output / "validation.json", report)
    if report["errors"]:
        raise ValueError(str(report["errors"]))
    write_json(output / "ai-attestation.json", {"recorded_at": now(), "dataset_fingerprint": report["dataset_fingerprint"],
        "review_policy": "provisional_ai_visual", "human_review_completed": False,
        "limitations": "AI visual annotation only. Both teammates must review before formal final evaluation."})
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True)
    parser.add_argument("--selection", default="datasets/panoris-ball-ai-v1/selection.json")
    parser.add_argument("--output", default="data/panoris-ball-ai-v1")
    args = parser.parse_args()
    result = prepare(args.video, args.selection, args.output)
    print({"counts": result["counts"], "errors": result["errors"]})
