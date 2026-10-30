"""Build a Windows starter archive from the working source and a verified data bundle."""

import argparse
import json
import zipfile
from pathlib import Path

from football_pipeline.contracts import sha256_file
from football_pipeline.video import ROOT


def build(data, output):
    if not data.is_file() or output.exists():
        raise ValueError("Datapakket moet bestaan en het startpakket moet een nieuwe naam krijgen")
    with zipfile.ZipFile(data) as archive:
        manifest = json.loads(archive.read("training-transfer.json"))
        if manifest.get("schema_version") != 1 or manifest.get("kind") == "models":
            raise ValueError("Een trainingsdatapakket is vereist")
    allowed = {".py", ".ps1", ".json", ".yaml", ".yml", ".html", ".js", ".css", ".svg", ".toml"}
    files = []
    for name in ("src", "persoon1", "scripts", "configs"):
        files += [
            p
            for p in (ROOT / name).rglob("*")
            if p.is_file()
            and p.suffix in allowed
            and "__pycache__" not in p.parts
            and "node_modules" not in p.parts
        ]
    files += [ROOT / "streamlit_app.py", ROOT / "pyproject.toml", ROOT / "README.md"]
    files += list(ROOT.glob("requirements*.txt")) + list(ROOT.glob("requirements*.lock"))
    files += [
        ROOT / ".streamlit/config.toml",
        ROOT / "docs/Trainen_op_Andere_Laptop.md",
        ROOT / "docs/Spelers_en_Veld_Betrouwbaarheid_20261030.md",
    ]
    files = sorted({p for p in files if p.is_file()})
    hashes = {p.relative_to(ROOT).as_posix(): sha256_file(p) for p in files}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".partial.zip")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for path in files:
            archive.write(path, "Messi10/" + path.relative_to(ROOT).as_posix())
        archive.write(data, "Messi10/trainingsdata.zip")
        archive.writestr(
            "Messi10/laptop-source-manifest.json",
            json.dumps(
                {
                    "source_files": hashes,
                    "data_files": len(manifest["files"]),
                    "data_bundle_bytes": data.stat().st_size,
                    "environments_included": False,
                    "secret_files_included": False,
                },
                indent=2,
            ),
        )
        archive.writestr(
            "Messi10/START-HIER.txt",
            (
                "SPORTS VISION - TRAINEN OP JE EIGEN LAPTOP\n\n"
                "1. Pak de volledige Messi10-map uit. Kopieer geen .venv van een andere laptop.\n"
                "2. Installeer Python 3.11, Git voor Windows en een recente NVIDIA-driver.\n"
                "3. Open PowerShell in deze map: powershell -ExecutionPolicy Bypass -File scripts/Setup-Laptop.ps1\n"
                "4. Start: powershell -ExecutionPolicy Bypass -File scripts/Start-Laptop.ps1 en open Modellen trainen.\n"
                "5. Importeer trainingsdata.zip en controleer de GPU. Kies je model of Alles trainen.\n\n"
                "Elke laptop gebruikt de eigen GPU. Nieuwe modellen blijven proefmodellen tot evaluatie.\n"
                "Zie docs/Trainen_op_Andere_Laptop.md voor verdeling, gewichten delen en modelcombinaties.\n"
            ),
        )
    temporary.replace(output)
    print(f"Startpakket: {output} ({output.stat().st_size / 1024**3:.2f} GiB)", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.data, args.output)
