"""Run both networks and then compare, keeping durable status and subprocess logs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from football_pipeline.contracts import write_json  # noqa: E402


def main():
    """Start de afzonderlijke veldtrainingen en vergelijking als subprocessen en bewaar duurzame status
    en uitvoerlogs.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/field-corpus/soccernet")
    parser.add_argument("--runtime", type=Path, default=ROOT / ".tools/field-runtime.json")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--comparison-frames", type=int, default=200)
    parser.add_argument("--wait-for-pid", type=int, action="append", default=[])
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    status = {
        "pid": os.getpid(),
        "started_at": datetime.now(UTC).isoformat(),
        "status": "running",
        "output": str(output),
        "smoke": args.smoke,
        "automatic_promotion": False,
    }
    if args.wait_for_pid:
        import psutil

        pending = []
        for pid in args.wait_for_pid:
            try:
                pending.append(psutil.Process(pid))
            except psutil.NoSuchProcess:
                pass
        while pending:
            status.update(
                phase="waiting_for_gpu_jobs",
                waiting_for=[p.pid for p in pending],
                updated_at=datetime.now(UTC).isoformat(),
            )
            write_json(output / "job.json", status)
            _, pending = psutil.wait_procs(pending, timeout=10)
        status.pop("waiting_for", None)
    commands = [
        (
            "train",
            [
                "train",
                "--runtime",
                str(args.runtime.resolve()),
                "--dataset",
                str(args.dataset.resolve()),
                "--output",
                str(output),
                "--epochs",
                str(args.epochs),
            ]
            + (["--smoke"] if args.smoke else []),
        ),
        (
            "compare",
            [
                "compare",
                "--runtime",
                str(args.runtime.resolve()),
                "--dataset",
                str(args.dataset.resolve()),
                "--candidate",
                str(output / "field-runtime.json"),
                "--video",
                str(args.video.resolve()),
                "--output",
                str(output / "comparison"),
                "--limit-valid",
                str(args.comparison_frames),
            ],
        ),
    ]
    if not args.smoke:
        preflight = [
            "train",
            "--runtime",
            str(args.runtime.resolve()),
            "--dataset",
            str(args.dataset.resolve()),
            "--output",
            str(output / "preflight"),
            "--smoke",
        ]
        commands.insert(0, ("preflight", preflight))
    for phase, arguments in commands:
        status.update(phase=phase, updated_at=datetime.now(UTC).isoformat())
        write_json(output / "job.json", status)
        env = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
        with (output / (phase + ".log")).open("a", encoding="utf-8") as log:
            command = [sys.executable, "-m", "football_pipeline.field_learning", *arguments]
            log.write("\n" + json.dumps(command) + "\n")
            log.flush()
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            status.update(
                status="failed", returncode=result.returncode, updated_at=datetime.now(UTC).isoformat()
            )
            write_json(output / "job.json", status)
            raise SystemExit(result.returncode)
    status.update(status="complete", updated_at=datetime.now(UTC).isoformat())
    write_json(output / "job.json", status)


if __name__ == "__main__":
    main()
