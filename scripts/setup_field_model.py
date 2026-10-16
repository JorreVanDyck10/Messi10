"""Install only the isolated field-model runtime and official release weights."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from football_pipeline.field_model_spec import RELEASE_WEIGHTS, UPSTREAM_REVISION, UPSTREAM_URL  # noqa: E402


def checksum(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(arguments, **kwargs):
    return subprocess.check_output([str(a) for a in arguments], text=True, **kwargs).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".tools/field-runtime.json")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 11):
        parser.error("Gebruik Python 3.11 voor deze afzonderlijke omgeving.")
    repository = ROOT / ".tools/PnLCalib"
    repository.parent.mkdir(exist_ok=True)
    if not repository.exists():
        run(["git", "clone", UPSTREAM_URL + ".git", repository])
    if run(["git", "-C", repository, "status", "--porcelain"]):
        parser.error("PnLCalib bevat lokale wijzigingen; die worden niet overschreven.")
    run(["git", "-C", repository, "checkout", "--detach", UPSTREAM_REVISION])
    environment = ROOT / ".tools/pnlcalib-env"
    python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.is_file():
        venv.EnvBuilder(with_pip=True).create(environment)
    subprocess.run(
        [str(python), "-m", "pip", "install", "-r", str(ROOT / "requirements-field-model.txt")], check=True
    )
    weights = ROOT / "weights/pnlcalib"
    weights.mkdir(parents=True, exist_ok=True)
    models = {}
    for role, name in (("keypoints", "SV_kp"), ("lines", "SV_lines")):
        url = f"{UPSTREAM_URL}/releases/download/v1.0.0/{name}"
        path = weights / name
        if not path.is_file():
            temporary = path.with_suffix(".download")
            print(f"Download officiële gewichten: {name}", flush=True)
            with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            temporary.replace(path)
        actual_hash = checksum(path)
        if actual_hash != RELEASE_WEIGHTS[role]["sha256"]:
            raise ValueError(f"Onverwachte gewichtshash voor {name}; bestand wordt niet geladen: {path}")
        models[role] = {"name": name, "path": str(path), "url": url, "sha256": actual_hash}
    dependencies = run([python, "-m", "pip", "freeze"])
    (environment / "installed-requirements.txt").write_text(dependencies + "\n", encoding="utf-8")
    config = {
        "schema_version": 1,
        "python": str(python),
        "repository": str(repository),
        "device": args.device,
        "weights_keypoints": models["keypoints"]["path"],
        "weights_lines": models["lines"]["path"],
        "models": models,
        "upstream": {
            "url": UPSTREAM_URL,
            "revision": UPSTREAM_REVISION,
            "license": "GPL-2.0",
            "license_sha256": checksum(repository / "LICENSE"),
        },
        "source_sha256": {
            str(p.relative_to(repository)): checksum(p)
            for p in sorted(repository.rglob("*"))
            if p.is_file() and p.suffix in {".py", ".yaml"}
        },
        "pip_freeze": dependencies,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Veldmodelomgeving gereed: {args.output}", flush=True)


if __name__ == "__main__":
    main()
