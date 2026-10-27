"""Shared wall-clock budgets checked between optimizer steps, never mid-write."""

import math
import time


class TrainingBudget:
    def __init__(self, minutes=None, *, clock=time.monotonic):
        if minutes is not None and (not math.isfinite(minutes) or minutes <= 0):
            raise ValueError("Training minutes must be positive and finite")
        self.clock = clock
        self.started = clock()
        self.deadline = self.started + minutes * 60 if minutes is not None else math.inf

    @property
    def expired(self):
        return self.clock() >= self.deadline

    def stop_trainer(self, trainer):
        """Ultralytics checks stop at epoch boundary; retain a mid-epoch checkpoint too."""
        if self.expired:
            trainer.stop = True


def train_yolo(weights, dataset, output, config, minutes):
    """Fine-tune with native per-optimizer-step stopping and fixed resolution."""
    import csv
    import gc
    from pathlib import Path

    import torch
    from ultralytics import YOLO

    from .contracts import sha256_file, write_json

    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    budget = TrainingBudget(minutes)
    config = dict(config)
    config.pop("workers", None)
    requested_batch = config.pop("batch", 4)
    maximum_epochs = config["epochs"]
    record = {
        "status": "running",
        "base_weights": str(weights),
        "base_sha256": sha256_file(weights),
        "config": {**config, "batch": requested_batch},
        "minutes": minutes,
        "attempts": [],
        "training_source_sha256": sha256_file(__file__),
    }
    write_json(output / "status.json", record)
    for batch in dict.fromkeys([requested_batch, 2, 1] if requested_batch >= 2 else [1]):
        if budget.expired:
            break
        model = YOLO(str(weights))

        def limit_epochs(trainer):
            if trainer.epoch + 1 >= maximum_epochs:
                trainer.stop = True

        model.add_callback("on_fit_epoch_end", limit_epochs)

        def save_progress(trainer):
            write_json(output / "progress.json", {
                "epoch": trainer.epoch + 1, "maximum_epochs": maximum_epochs,
                "elapsed_s": budget.clock() - budget.started, "batch_size": batch,
                "loss": [float(v) for v in trainer.tloss.detach().cpu().flatten()]
                if getattr(trainer, "tloss", None) is not None else None,
            })

        model.add_callback("on_train_epoch_end", save_progress)
        try:
            model.train(
                data=str(Path(dataset) / "data.yaml"),
                project=str(output),
                name=f"batch-{batch}",
                device=0,
                workers=0,
                batch=batch,
                time=max(0.0001, (budget.deadline - budget.clock()) / 3600),
                **config,
            )
            best = output / f"batch-{batch}/weights/best.pt"
            with (output / f"batch-{batch}/results.csv").open() as stream:
                history = list(csv.DictReader(stream))
            record["attempts"].append({"batch": batch, "status": "complete", "epochs": len(history)})
            record.update(
                status="time_limited" if budget.expired else "complete",
                last_epoch_may_be_partial=budget.expired,
                best=str(best.resolve()),
                best_sha256=sha256_file(best),
                epochs=len(history),
                runtime_s=budget.clock() - budget.started,
            )
            return best
        except torch.cuda.OutOfMemoryError as exc:
            record["attempts"].append({"batch": batch, "status": "cuda_out_of_memory", "error": str(exc)})
        except BaseException as exc:
            record.update(status="failed", error=str(exc), runtime_s=budget.clock() - budget.started)
            raise
        finally:
            write_json(output / "status.json", record)
            del model
            gc.collect()
            torch.cuda.empty_cache()
    record.update(status="no_candidate", runtime_s=budget.clock() - budget.started)
    write_json(output / "status.json", record)
    raise ValueError("No trained checkpoint within the training budget")


def resume_yolo(dataset, output, pause):
    """Continue a verified native checkpoint, charging only the remaining budget."""
    import csv
    from pathlib import Path

    import torch
    from ultralytics import YOLO

    from .contracts import read_json, sha256_file, write_json

    checkpoint = Path(pause["resume_checkpoint"])
    if sha256_file(checkpoint) != pause["sha256"]:
        raise ValueError("Paused checkpoint changed")
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    if state.get("optimizer") is None or state["epoch"] + 1 != pause["last_completed_epoch"]:
        raise ValueError("Paused checkpoint lacks the expected optimizer or epoch")
    expected_data = (Path(dataset) / "data.yaml").resolve()
    if Path(state["train_args"]["data"]).resolve() != expected_data:
        raise ValueError("Paused training dataset changed")
    save_dir = Path(state["train_args"]["save_dir"])
    if save_dir.resolve().parent != Path(output).resolve():
        raise ValueError("Paused training output changed")
    del state
    budget = TrainingBudget(pause["remaining_training_minutes"])
    maximum = pause["maximum_epochs_total"]
    record = read_json(Path(output) / "status.json")
    write_json(Path(output) / "status-before-resume.json", record)
    record.update(status="running", resume=pause, resume_source_sha256=sha256_file(__file__))
    write_json(Path(output) / "status.json", record)
    model = YOLO(str(checkpoint))

    def remaining_time(trainer):
        # Native check_resume restores old arguments and ignores time overrides.
        trainer.args.time = max(0.0001, (budget.deadline - budget.clock()) / 3600)
        trainer.args.epochs = trainer.epochs = maximum

    def fixed_epoch_ceiling(trainer):
        # Timed native training recalculates epochs without adding start_epoch.
        # Restore the original ceiling and scheduler after every timed update.
        trainer.args.epochs = trainer.epochs = maximum
        trainer._setup_scheduler()
        trainer.scheduler.last_epoch = trainer.epoch
        trainer.stop = (
            budget.expired
            or trainer.epoch + 1 >= maximum
            or trainer.epoch + 1 - trainer.stopper.best_epoch >= trainer.stopper.patience
        )

    model.add_callback("on_pretrain_routine_start", remaining_time)
    model.add_callback("on_fit_epoch_end", fixed_epoch_ceiling)
    try:
        try:
            model.train(resume=True, device=0, workers=0)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            model = YOLO(str(checkpoint))
            model.add_callback("on_pretrain_routine_start", remaining_time)
            model.add_callback("on_fit_epoch_end", fixed_epoch_ceiling)
            model.train(resume=True, device=0, workers=0, batch=1)
        best = save_dir / "weights/best.pt"
        with (save_dir / "results.csv").open() as stream:
            history = list(csv.DictReader(stream))
        record.update(
            status="time_limited" if budget.expired else "complete",
            best=str(best.resolve()),
            best_sha256=sha256_file(best),
            epochs=len(history),
            runtime_s=pause["elapsed_stage_wall_seconds"] + budget.clock() - budget.started,
            resumed_runtime_s=budget.clock() - budget.started,
            last_epoch_may_be_partial=budget.expired,
        )
        return best
    except BaseException as exc:
        record.update(status="failed", error=str(exc))
        raise
    finally:
        write_json(Path(output) / "status.json", record)
