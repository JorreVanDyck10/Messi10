"""Bouw een leeskaart van alle gevolgde code zonder modules te importeren of uit te voeren.

AST leest functies en docstrings als tekst. Daardoor starten datasetbouwers,
trainingen en Streamlit niet tijdens het documenteren. Bronkopieën in reports
worden alleen beschreven; historische meetcode blijft ongewijzigd.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = {".py", ".ps1", ".js", ".jsx", ".ts", ".tsx", ".html", ".css"}
GROUPS = {
    "src": ("Toepassing en uitbreidingen", "De bibliotheek die interface en CLI aanroepen."),
    "persoon1": ("Data, training en evaluatie", "De afzonderlijke datatools en hun commandoregelinterface."),
    "scripts": (
        "Start-, trainings- en controlescripts",
        "Voer alleen het script voor de bedoelde werkstap uit.",
    ),
    "assets": (
        "Datasetbouwers en labelcontroles",
        "Deze bestanden horen bij de specifieke datasetversie in hun pad.",
    ),
    "tests": ("Softwaretests", "Fixtures en assertions controleren gedrag; ze zijn geen voetbalbenchmark."),
    "reports": (
        "Historische bronkopieën",
        "Meetbewijs van eerdere experimenten. Dit zijn geen actuele runtimebestanden.",
    ),
    "entry": ("Interface", "Het toegangspunt van de lokale Streamlit-toepassing."),
}
POWERSHELL_PURPOSES = {
    "Start-School": "Start de schoolbasis met handmatige kalibratie; optioneel een tegelprofiel.",
    "Start-Gezamenlijk": "Start het geselecteerde gezamenlijke modelprofiel.",
    "Start-Spelermodel": "Start de toepassing met een expliciete herkenningskeuze.",
    "Start-Wedstrijd": "Start de gezamenlijke wedstrijdworkflow met rollen en uitbreidingen.",
    "Start-Persoon1": "Start de commandoregelworkflow voor data, training of evaluatie.",
    "Setup-Persoon1": "Bereidt de lokale omgeving van persoon 1 voor.",
    "setup_tools": "Installeert lokale FFmpeg- en ffprobe-tools.",
    "Run-BallExperiment": "Voert de afzonderlijke balexperimentworkflow uit.",
    "Run-BroadcastSpelersTraining": "Start begrensde broadcastspelertraining.",
    "Run-CourseImprovement": "Start de cursusgerichte modelvergelijking.",
    "Run-GezamenlijkeTraining": "Start training en vergelijking van de gezamenlijke deelsystemen.",
    "Train-RollenTeams": "Start aanvullende rol- en teamtraining.",
    "Collect-BroadcastData": "Verzamelt en controleert de broadcastdataset.",
    "Resume-Broadcast": "Toont status of hervat een bestaande broadcastwerkstap.",
}


def followed_files() -> list[Path]:
    """Lees Git-paden, inclusief nieuwe niet-genegeerde code op deze branch."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return sorted({Path(p) for p in result.stdout.decode("utf-8").split("\0") if p})


def first_sentence(text: str) -> str:
    return text.strip().splitlines()[0].replace("|", "\\|") if text.strip() else ""


def describe(path: Path) -> tuple[str, list[str], list[str]]:
    """Haal de modulebedoeling, topniveausymbolen en lokale imports uit brontekst."""
    text = (ROOT / path).read_text(encoding="utf-8-sig")
    if path.suffix == ".py":
        tree = ast.parse(text, filename=str(path))
        purpose = first_sentence(ast.get_docstring(tree) or "")
        symbols = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]
        dependencies = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
                if node.level or module.startswith(("football_pipeline", "persoon1")):
                    dependencies.add("." * node.level + module)
            elif isinstance(node, ast.Import):
                dependencies.update(
                    item.name
                    for item in node.names
                    if item.name.startswith(("football_pipeline", "persoon1"))
                )
        if not purpose:
            if path.parts[0] == "tests":
                purpose = "Controleert gedrag via de onderstaande testfuncties en fixtures."
            elif path.name.startswith("__"):
                purpose = "Pakkettoegangspunt of pakketinitialisatie; zie de genoemde imports."
            else:
                purpose = fallback_purpose(path)
        return purpose, symbols, sorted(dependencies)
    if path.suffix == ".ps1":
        params = re.findall(r"\[(?:string|int|switch)\]\$(\w+)", text, flags=re.IGNORECASE)
        return POWERSHELL_PURPOSES.get(path.stem, "PowerShell-startprocedure."), params, []
    return (
        "Browsercomponent of presentatielaag; lees de inhoud samen met de aanroepende Python-module.",
        [],
        [],
    )


def fallback_purpose(path: Path) -> str:
    """Beschrijf bekende datasetbestandsrollen zonder gedrag uit de naam te verzinnen."""
    if path.parts[0] == "reports":
        return "Vastgelegde broncode van het experiment in deze rapportmap; geen nieuw startcommando."
    if path.parts[0] == "assets":
        if "validate" in path.stem or "check" in path.stem:
            return "Controleert beelden, labels of uitlijning van deze datasetversie."
        if path.stem.startswith("make_"):
            return "Maakt een afgeleide labeltaak van deze dataset; controleer de klassemapping."
        if "clip" in path.stem:
            return "Reconstrueert of knipt bronvideo voor deze datasetversie."
        return "Bouwt of past de expliciete annotaties van deze datasetversie toe."
    return "Lees de onderstaande functies en de bijbehorende werkstap in de hoofdleesgids."


def render() -> str:
    paths = followed_files()
    code = [p for p in paths if p.suffix in SUFFIXES]
    grouped = {name: [] for name in GROUPS}
    for path in code:
        grouped[path.parts[0] if path.parts[0] in GROUPS else "entry"].append(path)
    lines = [
        "# Codekaart: alle codebestanden",
        "",
        "Lees eerst [Code begrijpen en verdedigen](Code_en_Verdediging.md). Deze kaart legt per bestand",
        "de rol vast en noemt de daadwerkelijk aanwezige functies/klassen en lokale afhankelijkheden.",
        "Bij scripts met een oorspronkelijke Engelse moduleuitleg blijft die technische samenvatting zichtbaar.",
        "Functienamen zijn navigatiehulp; een lijst met namen vervangt het lezen van de implementatie niet.",
        "",
        f"Dekking: **{len(code)} codebestanden**, inclusief tests, datasethelpers en historische bronkopieën.",
        "Niet-gevolgde virtuele omgevingen, externe modelrepositories en gegenereerde uitvoer horen hier niet bij.",
        "Inline JavaScript van de puntenkiezer staat in `point_picker.py` en schaalt klikposities terug naar bronpixels.",
        "",
        "Werk bij met `python scripts/build_code_guide.py`. `--check` controleert of de kaart actueel is.",
        "",
        "## Leesroute voor de demonstratie",
        "",
        "`Start-School.ps1` → `streamlit_app.py` → `pipeline.process_video` → `detection` + `geometry`",
        "→ optioneel `tracking`/`teams` → `render` + `video.VideoWriter`.",
        "`contracts.py` beschrijft de gegevens die tussen deze stappen worden uitgewisseld.",
        "",
    ]
    for key, (title, explanation) in GROUPS.items():
        lines += [f"## {title}", "", explanation, ""]
        for path in grouped[key]:
            purpose, symbols, dependencies = describe(path)
            lines += [f"### [{path.as_posix()}](../{path.as_posix()})", "", purpose, ""]
            if symbols:
                label = "Parameters" if path.suffix == ".ps1" else "Topniveaufuncties en klassen"
                lines += [label + ": " + ", ".join(f"`{s}`" for s in symbols) + ".", ""]
            if dependencies:
                lines += ["Lokale koppelingen: " + ", ".join(f"`{s}`" for s in dependencies) + ".", ""]
    lines += [
        "## Modelconfiguraties",
        "",
        "Dit zijn instelbare profielen, geen verschillende implementaties van de hele pipeline.",
        "Een profielnaam alleen bewijst niet dat zijn gewichten aanwezig, actief of onafhankelijk geëvalueerd zijn.",
        "De loader controleert bestanden en mappings; de run bewaart wat daadwerkelijk is gebruikt.",
        "",
        "| Profiel | Model-ID's | Aanvullende instellingen |",
        "| --- | --- | --- |",
    ]
    for path in paths:
        if path.parent != Path("configs") or not path.name.startswith("models") or path.suffix != ".json":
            continue
        config = json.loads((ROOT / path).read_text(encoding="utf-8-sig"))
        ids = ", ".join(str(m.get("model_id", "?")) for m in config.get("models", []))
        extras = [k for k in ("appearance", "kit_embedding", "role_context", "analysis_scope") if k in config]
        if any("ball_tiles" in m for m in config.get("models", [])):
            extras.append("ball_tiles")
        lines.append(f"| [{path.name}](../{path.as_posix()}) | {ids} | {', '.join(extras) or 'geen'} |")
    counts = Counter(p.suffix for p in code)
    lines += [
        "",
        "Bestandstypen: " + ", ".join(f"{suffix}: {count}" for suffix, count in sorted(counts.items())) + ".",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "docs" / "Codekaart.md"
    content = render()
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            raise SystemExit("Codekaart is verouderd; voer python scripts/build_code_guide.py uit.")
        print("Codekaart dekt alle gevolgde codebestanden en is actueel.")
    else:
        target.write_text(content, encoding="utf-8", newline="\n")
        print(f"Geschreven: {target}")


if __name__ == "__main__":
    main()
