"""Controleert hoeveel echte labels behouden blijven na de geïnstalleerde YOLO-trainingsaugmentaties."""

from collections import Counter
import os
from pathlib import Path

from .core import now, read_json, write_json


def main():
    os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(".cache/ultralytics").resolve()))
    import torch
    from ultralytics.cfg import get_cfg
    from ultralytics.data.dataset import YOLODataset
    from ultralytics.utils import LOGGER

    torch.set_num_threads(4)
    config = read_json("configs/train-players-reference.json")
    report = {"recorded_at": now(), "scope": "training transformations only, no model scores", "resolutions": {}}
    LOGGER.setLevel("WARNING")
    for size in (640, 960, 1920):
        hypothesis = get_cfg(overrides={**config, "imgsz": size})
        dataset = YOLODataset(img_path=str(Path("runs/EXP-P003-teamtrack-players/dataset/images/train").resolve()),
            imgsz=size, batch_size=4, augment=True, hyp=hypothesis, rect=True, stride=32,
            data={"names": {0: "player", 1: "referee"}, "nc": 2})
        original, retained, shapes = Counter(), Counter(), set()
        for i, labels in enumerate(dataset.labels):
            original.update(int(c) for c in labels["cls"].reshape(-1))
            sample = dataset[i]
            retained.update(int(c) for c in sample["cls"].reshape(-1))
            shapes.add(tuple(sample["img"].shape))
        report["resolutions"][str(size)] = {"original_by_class": dict(original),
            "retained_by_class": dict(retained), "batch_image_shapes_CHW": sorted(shapes)}
    write_json("reports/players-experiments/preprocessing-audit.json", report)
    print(report)


if __name__ == "__main__":
    main()
