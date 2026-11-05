"""Expose an actual trained last epoch for geometric validation, without altering its loss selection."""

import argparse
import copy
import shutil
from pathlib import Path

import torch

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.field_learning import atomic_torch_save, make_runtime


def extract(training, baseline_runtime, output):
    """Verpak het werkelijk opgeslagen laatste veldcheckpoint als traceerbare kandidaat-runtime zonder
    het historische beste-losscheckpoint te vervangen.
    """
    source_path = training / "training-report.json"
    original = read_json(source_path)
    if original["status"] != "complete":
        raise ValueError("Training must finish before exposing its actual last epochs")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(training / "dataset-index.json", output / "dataset-index.json")
    report = copy.deepcopy(original)
    report["selection_purpose"] = (
        "Last trained epoch candidate for projection validation; not selected by heatmap loss"
    )
    report["parent_training_report"] = str(source_path.resolve())
    report["parent_training_report_sha256"] = sha256_file(source_path)
    for role in ("keypoints", "lines"):
        saved = original["models"][role]
        checkpoint = Path(saved["last_path"])
        if sha256_file(checkpoint) != saved["last_sha256"]:
            raise ValueError("The actual training checkpoint changed")
        state = torch.load(checkpoint, map_location="cpu", weights_only=False)
        if state["identity"] != original["identity"]:
            raise ValueError("Checkpoint belongs to a different experiment")
        destination = output / (role + "-last-trained.pt")
        atomic_torch_save(state["model"], destination)
        report["models"][role].update(
            path=str(destination.resolve()),
            sha256=sha256_file(destination),
            selected_epoch=int(state["epoch"]) + 1,
            selected_valid_loss=saved["history"][-1]["valid_loss"],
            selection="actual_last_epoch_for_geometry_comparison",
        )
        del state
    write_json(output / "training-report.json", report)
    make_runtime(baseline_runtime, output)
    return output / "field-runtime.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(extract(args.training, args.baseline, args.output))
