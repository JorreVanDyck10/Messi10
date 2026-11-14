"""Assisted-label suggestions for fixed source groups; no prediction is a role label."""

from __future__ import annotations

import cv2
import numpy as np

from football_pipeline.contracts import read_json, write_json
from football_pipeline.video import ROOT
from persoon1.modeling import yolo


def main():
    """Maak COCO-persoonsvoorstellen voor de vaste rolbronnen en bewaar ze als voorstellen, niet als
    definitieve rollabels.
    """
    root = ROOT / "datasets/roles-teams-v3"
    output = ROOT / "reports/person1-round3/proposals"
    output.mkdir(parents=True, exist_ok=True)
    model = yolo(ROOT / "models/yolo11n.pt")
    index_path = output / "index.json"
    previous = read_json(index_path)["sources"] if index_path.is_file() else []
    saved = {r["id"]: r for r in previous}
    records = []
    for source in read_json(root / "source-provenance.json")["sources"]:
        if source["id"] in saved:
            if source["sha256"] != saved[source["id"]]["sha256"]:
                raise ValueError("Source changed since proposal generation")
            records.append(saved[source["id"]])
            continue
        frame = cv2.imread(str(root / source["image"]))
        result = model.predict(
            frame, imgsz=1600, conf=0.15, classes=[0], iou=0.7, max_det=300, device="0", verbose=False
        )[0]
        proposed = []
        overlay = frame.copy()
        for index, (box, confidence) in enumerate(
            zip(result.boxes.xyxy.cpu().tolist(), result.boxes.conf.cpu().tolist())
        ):
            proposed.append(
                {
                    "proposal_index": index,
                    "bbox": box,
                    "confidence": confidence,
                    "class_id": 0,
                    "class_name": "person",
                }
            )
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 1)
            cv2.putText(overlay, str(index), (x1, max(10, y1)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        cv2.imwrite(str(output / (source["id"] + "-proposals.jpg")), overlay)
        # Large-body suggestions first; every final selection still requires visual review.
        chosen = sorted(
            proposed, key=lambda r: -(r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1])
        )[:24]
        for start in range(0, len(chosen), 12):
            canvas = np.full((2 * 210, 6 * 180, 3), 235, np.uint8)
            for j, proposal in enumerate(chosen[start : start + 12]):
                x1, y1, x2, y2 = map(int, proposal["bbox"])
                crop = frame[max(0, y1) : y2, max(0, x1) : x2]
                h, w = crop.shape[:2]
                scale = min(170 / w, 180 / h)
                crop = cv2.resize(crop, (max(1, int(w * scale)), max(1, int(h * scale))))
                y, x = divmod(j, 6)
                canvas[y * 210 + 25 : y * 210 + 25 + crop.shape[0], x * 180 : x * 180 + crop.shape[1]] = crop
                cv2.putText(
                    canvas,
                    str(proposal["proposal_index"]),
                    (x * 180 + 3, y * 210 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 0, 0),
                    1,
                )
            cv2.imwrite(str(output / f"{source['id']}-crops-{start:02}.jpg"), canvas)
        records.append({**source, "proposals": proposed})
        print(source["id"], len(proposed), flush=True)
    write_json(
        output / "index.json",
        {"model": "Pretrained YOLO11n COCO person proposals, NOT role ground truth", "sources": records},
    )


if __name__ == "__main__":
    main()
