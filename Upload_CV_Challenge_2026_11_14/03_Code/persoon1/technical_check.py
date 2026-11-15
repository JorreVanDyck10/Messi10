"""Controleert GPU-training met synthetische rechthoeken; resultaten zijn geen voetbalmodelscore."""

import contextlib
import gc
import logging
from pathlib import Path

from .core import environment, now, read_json, sha256, write_json
from .modeling import yolo


def main():
    """Probeer één epoch training op synthetische rechthoeken met de toegestane batches om de GPU-
    softwareketen te controleren, zonder dit als voetbalresultaat te rapporteren.
    """
    import torch
    import yaml
    from PIL import Image, ImageDraw
    if not torch.cuda.is_available():
        raise RuntimeError("This check requires a CUDA GPU")
    stamp = now().replace(":", "").replace(".", "").replace("+", "_")
    root = Path("output") / f"synthetic-software-check-{stamp}"
    root = root.resolve()
    for split, count in (("train", 8), ("val", 8)):
        for part in ("images", "labels"):
            (root / "dataset" / part / split).mkdir(parents=True)
        for index in range(count):
            image = Image.new("RGB", (640, 384), (35 + index * 3, 75, 45))
            x1, y1, x2, y2 = 70 + index * 10, 80, 150 + index * 10, 240
            ImageDraw.Draw(image).rectangle((x1, y1, x2, y2), fill=(220, 30, 30))
            image.save(root / "dataset/images" / split / f"{index}.png")
            (root / "dataset/labels" / split / f"{index}.txt").write_text(
                f"0 {(x1+x2)/1280} {(y1+y2)/768} {(x2-x1)/640} {(y2-y1)/384}\n")
    data = root / "dataset/data.yaml"
    data.write_text(yaml.safe_dump({"path": str(root / "dataset"), "train": "images/train", "val": "images/val",
                                   "names": {0: "synthetic_rectangle_not_a_player_or_ball"}}), encoding="utf-8")
    config = read_json("configs/train-reference.json")
    config.update(epochs=1, patience=1, workers=0, plots=False)
    report = {"kind": "synthetic_software_check_only", "counts_as_project_training": False,
              "recorded_at": now(), "environment": environment(), "generated_images": 16, "attempts": []}
    for batch in (4, 2, 1):
        model = yolo("models/yolo11n.pt")
        from ultralytics.utils import LOGGER
        try:
            with (root / f"batch-{batch}.log").open("w", encoding="utf-8") as log:
                handler = logging.StreamHandler(log)
                LOGGER.addHandler(handler)
                try:
                    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                        model.train(**{**config, "batch": batch, "data": str(data), "device": 0,
                                       "project": str(root), "name": f"batch-{batch}", "exist_ok": False})
                finally:
                    LOGGER.removeHandler(handler)
            checkpoint = root / f"batch-{batch}/weights/best.pt"
            if not checkpoint.is_file():
                raise RuntimeError("Synthetic training failed to save best.pt")
            report["attempts"].append({"batch": batch, "status": "completed", "checkpoint_sha256": sha256(checkpoint)})
            report.update(status="completed", output=str(root), project_mAP=None)
            write_json("reports/training-software-check.json", report)
            print("Synthetic one-epoch software check completed; this is not a project model.")
            return
        except torch.cuda.OutOfMemoryError:
            report["attempts"].append({"batch": batch, "status": "CUDA_out_of_memory"})
            del model
            gc.collect()
            torch.cuda.empty_cache()
        except Exception as exc:
            report.update(status="failed", error=str(exc), output=str(root))
            write_json("reports/training-software-check.json", report)
            raise
    report.update(status="failed_all_batches_OOM", output=str(root))
    write_json("reports/training-software-check.json", report)
    raise RuntimeError("Synthetic software check failed at all configured batches")


if __name__ == "__main__":
    main()
