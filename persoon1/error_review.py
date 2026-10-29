"""Maakt detailbeelden van geselecteerde false positives en false negatives voor foutenanalyse."""

from pathlib import Path

from .core import dataset_path, label_pixels, load_manifest, read_json, read_labels, write_json


def main():
    from PIL import Image, ImageDraw
    root = Path("reports/players-experiments")
    errors = read_json(root / "EXP-P004/validation-metrics/errors.json")
    data, images = load_manifest("datasets/teamtrack-players-v2/manifest.json")
    frames = {f["frame_id"]: f for f in data["frames"]}
    players_fn = [e for e in errors if e["type"] == "FN" and e["class_id"] == 0]
    players_fp = [e for e in errors if e["type"] == "FP" and e["class_id"] == 0]
    officials_fn = [e for e in errors if e["type"] == "FN" and e["class_id"] == 1]

    def area(error):
        b = error.get("annotation", error.get("prediction"))["bbox_xyxy"]
        return (b[2]-b[0])*(b[3]-b[1])

    selected = sorted(players_fn, key=area)[:2] + sorted(players_fn, key=area, reverse=True)[:2]
    selected += sorted(players_fp, key=lambda e: e["prediction"]["confidence"], reverse=True)[:2]
    selected += sorted(officials_fn, key=area)[:1] + sorted(officials_fn, key=area, reverse=True)[:1]
    sheet = Image.new("RGB", (1600, 900), "#15202b")
    records = []
    for i, error in enumerate(selected):
        frame = frames[error["frame_id"]]
        box = error.get("annotation", error.get("prediction"))["bbox_xyxy"]
        x1, y1, x2, y2 = box
        cx, cy = (x1+x2)/2, (y1+y2)/2
        width, height = max(100, (x2-x1)*3), max(100, (y2-y1)*2)
        left, top = max(0, int(cx-width/2)), max(0, int(cy-height/2))
        right, bottom = min(frame["width"], int(cx+width/2)), min(frame["height"], int(cy+height/2))
        image = Image.open(dataset_path(images, frame["image"])).convert("RGB")
        draw = ImageDraw.Draw(image)
        for label in read_labels(dataset_path(images, frame["label"]), len(data["names"])):
            draw.rectangle(label_pixels(label, frame["width"], frame["height"]), outline="#22ff88", width=1)
        draw.rectangle(box, outline="#ff4444", width=1)
        crop = image.crop((left, top, right, bottom))
        scale = min(390/crop.width, 390/crop.height)
        crop = crop.resize((round(crop.width*scale), round(crop.height*scale)))
        px, py = i % 4 * 400, i // 4 * 450
        sheet.paste(crop, (px, py+45))
        identity = f"ERR-P{i+1:03}"
        ImageDraw.Draw(sheet).text((px+5, py+5), f"{identity}: {error['type']} {data['names'][error['class_id']]}", fill="white")
        ImageDraw.Draw(sheet).text((px+5, py+22), frame["frame_id"][-6:] + " / val", fill="white")
        records.append({"error_id": identity, **error, "source_crop_xyxy": [left, top, right, bottom],
                        "evidence": "error-examples.jpg", "cause": "Hypothesis requires interpretation; see the report"})
    sheet.save(root / "error-examples.jpg", quality=95)
    write_json(root / "reviewed-error-examples.json", records)
    print(len(records))


if __name__ == "__main__":
    main()
