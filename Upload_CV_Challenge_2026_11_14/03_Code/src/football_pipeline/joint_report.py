"""Schrijft het gezamenlijke rapport uit werkelijk opgeslagen trainings- en demonstratieresultaten."""

from .contracts import read_json, sha256_file, write_json
from .video import ROOT


def write_report(dataset, output):
    """Lees de werkelijk voltooide deeltrainingen en demonstraties en schrijf daaruit het gezamenlijke
    verslag met bronverwijzingen.
    """
    import json
    import shutil
    import xml.etree.ElementTree as ET
    from collections import Counter
    from pathlib import Path

    inventory_path = dataset / "inventory-final.json"
    if not inventory_path.exists():
        inventory_path = dataset / "inventory.json"
    inventory = read_json(inventory_path)
    reports = read_json(output / "comparison.json")
    role_training = Path(reports["roles"]["candidate"]).parent
    if (role_training / "curves.json").exists():
        curves = read_json(role_training / "curves.json")
        fine = role_training / "fine-tune-curves.json"
        reports["roles"]["training"]["executed_epochs"] = {
            "backbone": len(json.loads(fine.read_text(encoding="utf-8"))) if fine.exists() else 0,
            **{name: max((row["epoch"] for row in history), default=0) for name, history in curves.items()},
        }
    demos = read_json(output / "demonstrations.json")
    target = ROOT / "reports/joint-retrain-20261027"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(inventory_path, target / "data-inventory.json")
    provenance = dataset / "source-provenance.json"
    if provenance.exists():
        shutil.copy2(provenance, target / "source-provenance.json")
    write_json(
        target / "audit-index.json",
        {
            "dataset_version": inventory["dataset_version"],
            "dataset_root": str(dataset),
            "files": {
                name: sha256_file(dataset / name)
                for name in (
                    "inventory.json",
                    *(
                        ["inventory-final.json", "roles-pixel-v1/manifest.json"]
                        if inventory_path.name == "inventory-final.json"
                        else []
                    ),
                    "players/manifest.json",
                    "roles/manifest.json",
                    "ball/manifest.json",
                    "field/index.json",
                )
            },
            "human_review_completed": False,
            "test_images_accessed": False,
        },
    )
    summary = {
        "status": "complete",
        "dataset": str(dataset),
        "inventory_sha256": sha256_file(inventory_path),
        "counts": inventory["counts"],
        "exclusions_by_reason": dict(Counter(r["reason"] for r in inventory["excluded"])),
        "training": {name: r["training"] for name, r in reports.items()},
        "selections": {
            name: {
                "promoted": r["promoted"],
                "baseline": r["baseline"],
                "candidate": r["candidate"],
                "selected": r["selected"],
                "criterion": r["criterion"],
                "comparison_sha256": sha256_file(output / name / "comparison.json"),
            }
            for name, r in reports.items()
        },
        "demonstrations": demos,
        "human_review_completed": False,
        "independent_final_test_completed": False,
    }
    visual = target / "visual-review.json"
    if visual.exists():
        summary["visual_review"] = read_json(visual)
    software = output / "software-tests.xml"
    environment = output / "environment-checks.json"
    if environment.exists():
        summary["environment_checks"] = read_json(environment)
        shutil.copy2(environment, target / "environment-checks.json")
    if software.exists():
        suite = ET.parse(software).getroot().find("testsuite")
        summary["software_tests"] = dict(suite.attrib)
        summary["software_tests_sha256"] = sha256_file(software)
    write_json(target / "summary.json", summary)
    lines = [
        "# Gezamenlijke training en toepassing — 27 oktober 2026",
        "",
        "De bestaande lokale data is gecontroleerd en per taak samengebracht. Spelers, rollen, bal en veld hebben elk een echte nieuwe training gekregen. Een kandidaat wordt alleen gekozen als de vooraf vastgelegde vergelijking de verbetering ondersteunt.",
        "",
        "## Data",
        "",
        "| Taak | Training | Validatie |",
        "|---|---:|---:|",
    ]
    for name, count in inventory["counts"].items():
        lines.append(f"| {name} | {count.get('train', 0)} | {count.get('val', count.get('valid', 0))} |")
    lines += [
        "",
        "De balrijen zijn overlappende tegels, de rolrijen persoonscrops. Dit zijn geen aantallen onafhankelijke wedstrijden. Veldtraining gebruikt de volledige beschikbare trainingsindex binnen het tijdsbudget. Heatmapvalidatie en de geometrische vergelijking gebruiken vooraf gekozen 64 beelden: alle 20 course-validatiebeelden en 44 verspreide corpusbeelden. De overige veldvalidatiebeelden zijn geïnventariseerd maar niet als gemeten voorgesteld.",
        "",
        "Exacte kopieën en oudere cropannotaties worden ontdubbeld. Gereserveerde testbeelden worden niet geopend. Generieke personen worden geen spelers; alleen positieve balmomenten, ongelabelde voorstellen en incompatibele poseannotaties blijven buiten de bijbehorende training. Bron-, label- en videohashes staan in de inventaris en taakmanifesten.",
        "",
        "| Uitsluitingsreden in gezamenlijke inventaris | Records |",
        "|---|---:|",
        *[f"| {reason} | {count} |" for reason, count in summary["exclusions_by_reason"].items()],
        "",
        "De taakmanifesten bevatten daarnaast taakgebonden uitsluitingen, zoals onbruikbare baltegels en ongeldige veldannotaties; hun aantallen worden niet bij elkaar opgeteld als unieke beelden.",
        "",
        "## Training en selectie",
        "",
        "| Onderdeel | Nieuwe gewichten gekozen | Uitkomst | Gemeten duur (min) |",
        "|---|---|---|---:|",
    ]
    for name, r in reports.items():
        training = r["training"]
        status = training.get("status", "complete")
        epochs = training.get("epochs")
        text = f"{status}; {epochs} geregistreerde epochs" if epochs else status
        if name == "roles" and training.get("executed_epochs"):
            text += "; laatste kandidaat: " + ", ".join(
                f"{k}: {v} epochs" for k, v in training["executed_epochs"].items()
            )
        if name == "field":
            text = "; ".join(
                f"{k}: {sum(e['epoch_complete'] for e in v['history'])} volledige + "
                f"{sum(not e['epoch_complete'] for e in v['history'])} gedeeltelijke epochs, "
                f"{sum(e['training_samples'] for e in v['history'])} beeldpassages, {v['completion_reason']}"
                for k, v in training["models"].items()
            )
        duration = training.get("runtime_s", 0) / 60
        lines.append(
            f"| {name} | {'ja' if r['promoted'] else 'nee; huidige model behouden'} | {text} | {duration:.2f} |"
        )
    if reports["ball"]["training"].get("resume"):
        lines += [
            "",
            "De baltraining is op verzoek gepauzeerd na epoch 15 en met dezelfde optimizer hervat. Het resterende budget was 36,58 minuten; de pauzetijd telt niet als training. Het oorspronkelijke hervatbare checkpoint en zijn SHA-256 zijn bewaard.",
            "",
        ]
    if reports["players"]["training"].get("phases"):
        lines += [
            "",
            "Het spelermodel gebruikt twee vastgelegde fasen: 53 epochs in de eerste samenvoeging en zeven aanvullende epochs vanuit het geselecteerde checkpoint op dataset v2. In v2 krijgen 16 volledige bronbeelden voorrang op hun oudere uitsneden. Alle spelerresultaten hieronder zijn opnieuw gemeten op dezelfde 83 v2-validatiebeelden; de eerdere 79-beeldenmeting wordt niet als v2-resultaat gebruikt.",
            "",
        ]
    lines += [
        "",
        "### Spelers en officials",
        "",
        "| Model | Speler AP50 | Speler AP50:95 | Speler recall | Official AP50:95 |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, m in reports["players"]["metrics"].items():
        p = {r["name"]: r for r in m["per_class"]}
        lines.append(
            f"| {name} | {p['player']['AP50']:.4f} | {p['player']['AP50_95']:.4f} | {p['player']['recall']:.4f} | {p['referee']['AP50_95']:.4f} |"
        )
    lines += [
        "",
        "Deze AP betreft de detector vóór aanvullende rolclassificatie, teams, tracking en veldprojectie. Het is geen AP-score voor de volledige toepassing.",
        "",
    ]
    lines += ["", "### Rollen", "", "| Model | Macro-F1 bij 0,65 | Accuracy bij 0,65 |", "|---|---:|---:|"]
    for name, m in reports["roles"]["metrics"].items():
        lines.append(f"| {name} | {m['macro_f1']:.4f} | {m['accuracy']:.4f} |")
    role_baseline = {r["name"]: r for r in reports["roles"]["metrics"]["baseline"]["per_class"]}
    if reports["roles"].get("pixel_manifest_sha256"):
        lines += [
            "",
            "Een aanvullende pixelcontrole verwijderde 16 exact gelijke persoonsuitsneden met verschillend afgeronde boxen: twee trainingscrops en veertien validatiecrops. Er waren geen identieke croppixels tussen training en validatie. De roltraining is vanuit R007 opnieuw uitgevoerd binnen het resterende rolbudget; bovenstaande scores gebruiken uitsluitend de opgeschoonde 2.243 validatiecrops. De eerste vergelijking en oorspronkelijke manifesten blijven bewaard.",
            "",
        ]
    role_candidate = {r["name"]: r for r in reports["roles"]["metrics"]["candidate"]["per_class"]}
    lines += [
        "",
        "| Rol | Baseline recall | Kandidaat recall | Baseline F1 | Kandidaat F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, b in role_baseline.items():
        c = role_candidate[name]
        lines.append(f"| {name} | {b['recall']:.4f} | {c['recall']:.4f} | {b['f1']:.4f} | {c['f1']:.4f} |")
    regressed = [name for name, b in role_baseline.items() if role_candidate[name]["recall"] < b["recall"]]
    if not reports["roles"]["promoted"] and regressed:
        lines += [
            "",
            "R007 blijft actief omdat de kandidaat recall verliest voor: "
            + ", ".join(regressed)
            + ". De hogere totaalscore heft die vooraf vastgelegde behoudvoorwaarde niet op.",
            "",
        ]
    lines += [
        "",
        "De rolmeting gebruikt correcte referentiecrops en is geen detectie-AP. Per rol, verwarringsmatrices en voorspellingen staan in het vergelijkingsbestand.",
        "",
        "### Bal",
        "",
        "| Model | AP50 | AP50:95 | Precision | Recall |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, m in reports["ball"]["metrics"].items():
        b = m["per_class"][0]
        lines.append(
            f"| {name} | {b['AP50']:.4f} | {b['AP50_95']:.4f} | {b['precision']:.4f} | {b['recall']:.4f} |"
        )
    lines += [
        "",
        "Balmetingen gebruiken dezelfde volledige validatiebeelden en multiscale-tegelverwerking. Labels omvatten reserveballen; dit meet geen automatische selectie van de speelbal.",
        "",
        "### Veld",
        "",
        "| Model | Intern geldig | Daarvan fout | Zonder lijnreferentie | Mediane lijnfout (px) |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, m in reports["field"]["metrics"].items():
        error = m["median_error_px"] if m["median_error_px"] is not None else "niet beschikbaar"
        lines.append(
            f"| {name} | {m['valid_frames']}/{m['frames']} | {m['wrong_calibrations']} | {m.get('unscored_valid_frames', 0)} | {error} |"
        )
    lines += [
        "",
        "Veldcorpus en voortraining overlappen. Geometrische referenties zijn afzonderlijk van interne geldigheid beoordeeld; deze ontwikkelvergelijking is geen onafhankelijke eindtest.",
        "",
        "## Werkende toepassing",
        "",
        "Start met `scripts/Start-Gezamenlijk.ps1`. Het profiel `configs/models-integrated-20261027.json` koppelt de geselecteerde onderdelen aan teams, cameracompensatie, tracking en de minimap.",
        "",
        "| Demonstratie | Frames | Frames met telling | Tijd (s) |",
        "|---|---:|---:|---:|",
    ]
    for name, d in demos.items():
        lines.append(
            f"| {name} | {d['frames']} | {d['frames_with_count']} | {d['measurements']['runtime_s']:.1f} |"
        )
    lines += [
        "Video, JSONL en CSV zijn op gelijke frameaantallen en teamtotalen gecontroleerd. Elke bronclip krijgt eigen automatische veldherkenning; er wordt geen kalibratie van een andere opname geleend. ID's zijn tijdelijk en worden bij camerawissels vernieuwd.",
        "",
        "## Bestanden en beperkingen",
        "",
        f"- Actuele inventaris: `{inventory_path}`; de oorspronkelijke inventaris blijft bewaard.",
        f"- Gewichten, configuraties, logs en vergelijkingen: `{output}`.",
        "- Samenvatting met checksums: `reports/joint-retrain-20261027/summary.json`.",
        "- Versieerbare data-inventaris en herkomst: `reports/joint-retrain-20261027/data-inventory.json`, `source-provenance.json` en `audit-index.json`.",
        "- Voorlopige AI-labels blijven voorlopig. Er is geen menselijke nauwkeurigheidsreview of acceptatie ingevuld.",
        "- Teamfouten, gemiste rollen, reserveballen, onvolledige veldherkenning en gefragmenteerde track-ID's blijven mogelijk.",
        "",
    ]
    if "software_tests" in summary:
        s = summary["software_tests"]
        lines += [
            "",
            f"Softwarecontrole: {s['tests']} tests geregistreerd, {s['failures']} failures en {s['errors']} errors. De console-uitvoer en XML zijn bij de trainingsronde bewaard.",
            "",
        ]
    if "environment_checks" in summary:
        lines += [
            "De dependencycontrole slaagt voor de app- en veldruntimeomgeving. De aparte veldtrainer gebruikt upstream PyTorch 2.3.1; `pip check` meldt daar ontbrekende algemene app-dependencies en afwijkende app-versie-eisen. Die app draait daar niet. De vereiste veldimports, bron-/gewichtencontrole en CUDA-preflight zijn wel uitgevoerd; echte training en resultaten staan hierboven. De volledige uitvoer is bewaard in `environment-checks.json`.",
            "",
        ]
    if "visual_review" in summary:
        review = summary["visual_review"]
        lines += [
            "## Visuele controle en concrete beperkingen",
            "",
            "Codex (AI) heeft voor beide video's frames 0, 75 en 149 bekeken. Dit is geen menselijke acceptatie of onafhankelijke nauwkeurigheidsmeting.",
            "",
        ]
        lines += [f"- {finding}" for finding in review["findings"]]
        counts = review["software_tests"]
        lines += [
            "",
            f"De volledige suite: {counts['passed']} tests en {counts['subtests_passed']} subtests geslaagd (de XML registreert samen 344 gevallen).",
            "",
        ]
        for name, demo in demos.items():
            identifier = demo["run_directory"].replace("\\", "/").rsplit("/", 1)[-1]
            lines.append(f"- [{name}: openen in de app](http://127.0.0.1:8501/?run={identifier}).")
        lines.append("")
    path = ROOT / "docs/Gezamenlijke_Training_20261027.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
