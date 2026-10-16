"""Extend the pinned inference runtime read-only in an isolated Windows training venv."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    runtime = json.loads((ROOT / ".tools/field-runtime.json").read_text(encoding="utf-8"))
    base = Path(runtime["python"])
    environment = ROOT / ".tools/field-training-env"
    python = environment / "Scripts/python.exe"
    if not python.exists():
        subprocess.run([str(base), "-m", "venv", str(environment)], check=True)
    packages = base.parent.parent / "Lib/site-packages"
    # Imported dependencies are not copied or modified; additional packages live in the training venv.
    site = environment / "Lib/site-packages"
    (site / "field_runtime_bootstrap.py").write_text(
        "import os\n"
        f"_dll_paths = [{str(base.parent.parent / 'Library/bin')!r}]\n"
        "_dll_handles = [os.add_dll_directory(p) for p in _dll_paths if os.path.isdir(p)]\n",
        encoding="utf-8",
    )
    bootstrap = str(packages.resolve()) + "\nimport field_runtime_bootstrap\n"
    project_path = site / "field-runtime.pth"
    project_path.write_text(bootstrap, encoding="utf-8")
    try:
        subprocess.run(
            [str(python), "-m", "pip", "install", "-r", str(ROOT / "requirements-field-training.txt")],
            check=True,
        )
    finally:
        project_path.write_text(bootstrap + str(ROOT / "src") + "\n", encoding="utf-8")
    frozen = subprocess.check_output([str(python), "-m", "pip", "freeze"], text=True)
    (environment / "installed-requirements.txt").write_text(frozen, encoding="utf-8")
    print(python)


if __name__ == "__main__":
    main()
