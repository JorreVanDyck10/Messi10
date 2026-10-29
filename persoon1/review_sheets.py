"""Maakt overzichtsbladen en detailcrops voor visuele labelreview zonder labels te veranderen."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from .core import dataset_path, load_manifest, read_labels


def create_sheets(manifest, output):
    """Maak reproduceerbare volledige-frame- en boxdetailoverzichten uit het manifest zonder de
    onderliggende labels te wijzigen.
    """
    data, root = load_manifest(manifest)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(data["frames"]), 6):
        frames = data["frames"][start:start + 6]
        crops = Image.new("RGB", (25 * 84, len(frames) * 180), "#15202b")
        full = Image.new("RGB", (2000, len(frames) * 336), "#15202b")
        officials = Image.new("RGB", (900, len(frames) * 240), "#15202b")
        for row, frame in enumerate(frames):
            image = Image.open(dataset_path(root, frame["image"])).convert("RGB")
            labels = read_labels(dataset_path(root, frame["label"]), len(data["names"]))
            overlay = image.copy()
            draw = ImageDraw.Draw(overlay)
            for col, box in enumerate(labels):
                x, y, w, h = box["xywh"]
                x, w = x * image.width, w * image.width
                y, h = y * image.height, h * image.height
                color = "#00ff80" if box["class_id"] == 0 else "#ff40ff"
                draw.rectangle((x-w/2, y-h/2, x+w/2, y+h/2), outline=color, width=3)
                draw.text((x-w/2, y-h/2-14), str(col+1), fill=color)
                crop = image.crop((max(0, int(x-w*.7)), max(0, int(y-h*.65)),
                                   min(image.width, int(x+w*.7)), min(image.height, int(y+h*.65))))
                crop.thumbnail((80, 140))
                crops.paste(crop, (col*84+(84-crop.width)//2, row*180+30))
                ImageDraw.Draw(crops).text((col*84+3, row*180+15),
                                          f"{col+1} {'P' if box['class_id'] == 0 else 'R'}", fill=color)
                if box["class_id"] == 1:
                    role = col - 22
                    padding = 8
                    left, top = int(x-w/2)-padding, int(y-h/2)-padding
                    official = image.crop((left, top, int(x+w/2)+padding, int(y+h/2)+padding))
                    ImageDraw.Draw(official).rectangle((x-w/2-left, y-h/2-top,
                        x+w/2-left, y+h/2-top), outline="#ff40ff", width=1)
                    scale = min(280 / official.width, 210 / official.height)
                    official = official.resize((round(official.width*scale), round(official.height*scale)))
                    officials.paste(official, (role*300, row*240+25))
                    ImageDraw.Draw(officials).text((role*300, row*240+5),
                        f"{start+row+1} / box {col+1}: {frame['frame_index']}", fill="white")
            title = f"{start+row+1}/60 {frame['frame_id']} [{frame['split']}]"
            ImageDraw.Draw(crops).text((3, row*180), title, fill="white")
            overlay.thumbnail((2000, 308))
            full.paste(overlay, (0, row*336+24))
            ImageDraw.Draw(full).text((5, row*336+5), title, fill="white")
        crops.save(output / f"boxes-{start//6:02}.jpg", quality=93)
        full.save(output / f"frames-{start//6:02}.jpg", quality=93)
        officials.save(output / f"referees-{start//6:02}.jpg", quality=94)
    return {"frames": len(data["frames"]), "output": str(output)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(create_sheets(args.manifest, args.output))
