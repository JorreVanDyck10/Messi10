"""Controleer uitleg bij iedere Python-functie in de actuele projectcode.

De controle omvat src, persoon1, scripts, datasethelpers en streamlit_app.py,
inclusief methoden en geneste functies. Tests en historische bronkopieën onder
reports zijn afzonderlijk meetbewijs en vallen buiten deze productiedekking.
Alleen Git-gevolgde of nieuwe niet-genegeerde bronbestanden worden gelezen.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source_files() -> list[Path]:
    """Selecteer actuele Python-bronnen uit Git zonder omgevingen of rapportkopieën mee te tellen."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = {Path(p) for p in result.stdout.decode("utf-8").split("\0") if p}
    return sorted(
        p
        for p in paths
        if p.suffix == ".py"
        and (
            p.parts[0] in {"src", "persoon1", "scripts"}
            or p.parts[:2] == ("assets", "annotations")
            or p == Path("streamlit_app.py")
        )
    )


def functions(tree: ast.AST, prefix: str = ""):
    """Lever ook klassenmethoden, callbacks en functies binnen if/try-blokken met hun volledige naam."""
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = prefix + node.name
            if not isinstance(node, ast.ClassDef):
                yield name, node
            yield from functions(node, name + ".")
        else:
            yield from functions(node, prefix)


def audit() -> dict:
    """Tel documentatiedekking en geef iedere ontbrekende of lege docstring met bronlocatie terug."""
    counts = Counter()
    missing = []
    files = source_files()
    for path in files:
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8-sig"), filename=str(path))
        for name, node in functions(tree):
            counts[path.parts[0]] += 1
            if not (ast.get_docstring(node) or "").strip():
                missing.append({"file": path.as_posix(), "function": name, "line": node.lineno})
    return {
        "files": len(files),
        "functions": sum(counts.values()),
        "by_group": dict(counts),
        "missing": missing,
        "excluded": ["tests", "reports historical source snapshots"],
    }


def main() -> None:
    """Print de actuele dekking, schrijf optioneel een JSON-rapport en faal als een functie uitleg mist."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = audit()
    content = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(content, encoding="utf-8")
    print(content, end="")
    if result["missing"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
