"""Compare broadcast candidates, package portable weights and preserve field geometry."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
from collections import Counter
from pathlib import Path

from .broadcast_evaluation import evaluate_profile
from .broadcast_training import BASE_PLAYERS, BASE_ROLES
from .contracts import read_json, sha256_file, write_json
from .teams import load_team_settings
from .video import ROOT

OLD_RUN = ROOT / "runs/63d6a606d9cda9ade4c1719aecc03e50f573ec97469e7d5b3904a0d1f72425cb"


def build_profile(weights, roles=None, kit=None, *, protected=True):
    profile = copy.deepcopy(read_json(ROOT / "configs/models-integrated-20261027.json"))
    profile["analysis_scope"] = "on_pitch_players"
    profile["profile_name"] = "Broadcast — spelers op het veld en Team A/B"
    profile["models"] = [s for s in profile["models"] if set(s["class_mapping"].values()) != {"ball"}]
    profile["models"][0].update(weights=str(Path(weights).resolve()), weights_sha256=sha256_file(weights))
    profile["models"][1]["weights"] = str(ROOT / "artifacts/appearance-v1/person_proposals.pt")
    if roles:
        profile["appearance"].update(weights=str(Path(roles).resolve()), weights_sha256=sha256_file(roles),
                                     role_policy="preserve_detector_players" if protected else "classifier")
    else:
        profile.pop("appearance", None)
    if kit:
        profile["kit_embedding"] = {"model_id": "broadcast-kit-v1", "weights": str(Path(kit).resolve()),
                                    "weights_sha256": sha256_file(kit), "device": "0"}
    profile.pop("handoff", None)
    return profile


def candidate_score(report):
    p, t = report["player_detection_and_roles"]["per_class"][0], report["teams"]
    f1 = 2 * p["precision"] * p["recall"] / max(1e-9, p["precision"] + p["recall"])
    return (bool(report["targets_met"]), t["correct_fraction_all_players"] -
            2 * (t["wrong"] + t["false_positive_players"]) / max(1, t["matched_players"] + t["missed_players"]), f1)


def compare_and_package(dataset, output):
    dataset, output = Path(dataset).resolve(), Path(output).resolve()
    detector = read_json(output / "detector/status.json")
    trained = Path(detector["best"])
    if sha256_file(trained) != detector["best_sha256"]:
        raise ValueError("Trained detector checksum changed")
    new_roles, kit = output / "roles/roles_teams.pt", output / "teams/kit_embedding.pt"
    kit_report = read_json(output / "teams/metrics.json")
    embedding_settings = load_team_settings({"method": "torso_embedding_dominant_modes_v1",
                                             "confirmation_samples": 1, **kit_report["settings"]})
    lab_settings = load_team_settings(ROOT / "configs/teams.json")
    candidates = {
        "r007-baseline": (build_profile(BASE_PLAYERS, ROOT / "artifacts/appearance-v1/roles_teams.pt", protected=False), lab_settings),
        "previous-role-candidate": (build_profile(BASE_PLAYERS, BASE_ROLES, kit, protected=False), embedding_settings),
        "protected-previous-candidate": (build_profile(BASE_PLAYERS, BASE_ROLES, kit), embedding_settings),
        "new-roles-existing-detector": (build_profile(BASE_PLAYERS, new_roles, kit), embedding_settings),
        "new-detector-protected": (build_profile(trained, new_roles, kit), embedding_settings),
        "new-detector-classifier": (build_profile(trained, new_roles, kit, protected=False), embedding_settings),
        "new-detector-only": (build_profile(trained, kit=kit), embedding_settings),
    }
    # Test whether extra source detail recovers small players. The model's actual
    # class identities and source-pixel boxes remain identical in meaning.
    for name in ("new-detector-protected", "new-detector-classifier", "new-detector-only"):
        profile, settings = copy.deepcopy(candidates[name])
        profile["models"][0]["imgsz"] = 1920
        candidates[name + "-1920"] = profile, settings
    reports = {}
    for name, (profile, settings) in candidates.items():
        directory = output / "evaluation" / name
        directory.mkdir(parents=True, exist_ok=True)
        write_json(directory / "profile.json", profile)
        write_json(directory / "teams.json", settings)
        reports[name] = evaluate_profile(dataset, directory / "profile.json", directory / "teams.json", directory)
    baseline = reports["r007-baseline"]
    eligible = [name for name, (profile, _) in candidates.items() if name != "r007-baseline"
                and (not profile.get("appearance")
                     or profile["appearance"].get("role_policy") == "preserve_detector_players")]
    selected = max(eligible, key=lambda name: candidate_score(reports[name]))
    before, after = baseline["player_detection_and_roles"]["per_class"][0], reports[selected]["player_detection_and_roles"]["per_class"][0]
    f1_before = 2 * before["precision"] * before["recall"] / max(1e-9, before["precision"] + before["recall"])
    f1_after = 2 * after["precision"] * after["recall"] / max(1e-9, after["precision"] + after["recall"])
    improved = (f1_after > f1_before and reports[selected]["teams"]["correct_fraction_all_players"]
                > baseline["teams"]["correct_fraction_all_players"])
    summary = {"selected": selected, "improved_over_baseline": improved,
               "eligible_candidates": eligible,
               "selection_rule": "Protect specialist player labels; prefer all targets met, then correct teams with false players penalized",
               "targets_met": reports[selected]["targets_met"], "independent_final_test": False,
               "human_review_completed": False, "candidates": reports,
               "geometry_kind": baseline["geometry_kind"]}
    write_json(output / "comparison.json", summary)
    if not improved:
        raise ValueError("No improvement over baseline; existing application profile preserved")
    package = ROOT / "artifacts/broadcast-players-v1"
    package.mkdir(parents=True, exist_ok=True)
    profile, settings = copy.deepcopy(candidates[selected])
    for spec, filename in [(profile["models"][0], "players_best.pt"),
                           *([(profile["appearance"], "roles_teams.pt")] if profile.get("appearance") else []),
                           (profile["kit_embedding"], "kit_embedding.pt")]:
        target = package / filename
        shutil.copy2(spec["weights"], target)
        spec.update(weights="../artifacts/broadcast-players-v1/" + filename, weights_sha256=sha256_file(target))
    # Generic person proposals are a previously shipped COCO checkpoint.
    generic = profile["models"][1]
    generic["weights"] = "../artifacts/appearance-v1/person_proposals.pt"
    profile["handoff"] = {"evaluation_record": "../reports/broadcast-pitch-v1/summary.json",
                           "human_review_completed": False, "independent_final_test_completed": False,
                           "targets_met": summary["targets_met"],
                           "scope": "Broadcast development validation; players inside current field only"}
    write_json(ROOT / "configs/models-broadcast.json", profile)
    write_json(ROOT / "configs/teams-broadcast.json", settings)
    report_root = ROOT / "reports/broadcast-pitch-v1"
    report_root.mkdir(parents=True, exist_ok=True)
    compact = copy.deepcopy(summary)
    for report in compact["candidates"].values():
        report["profile"] = {"models": [{"model_id": s["model_id"], "weights_sha256": s["weights_sha256"]}
                                        for s in report["profile"]["models"]],
                             "appearance": report["profile"].get("appearance"),
                             "kit_embedding": report["profile"].get("kit_embedding")}
    source = read_json(dataset / "manifest.json")
    compact["data"] = {k: source[k] for k in ("source", "source_revision", "selection", "counts", "fingerprint")}
    compact["training"] = {"detector": detector, "roles": read_json(output / "roles/metrics.json"),
                            "teams": kit_report, "features_runtime_s":
                            read_json(output / "appearance/metrics.json")["runtime_s"]}
    compact["training"]["gpu_stage_wall_seconds"] = (detector["runtime_s"]
        + compact["training"]["roles"]["runtime_s"] + kit_report["runtime_s"] + compact["training"]["features_runtime_s"])
    write_json(report_root / "summary.json", compact)
    for filename in ("players_best.pt", "roles_teams.pt", "kit_embedding.pt"):
        if (package / filename).exists():
            print(filename, sha256_file(package / filename), flush=True)
    write_card(package, compact)
    return compact


def demonstrate(output):
    from scripts.check_team_integration import check_result

    from .automatic_calibration import load_automatic_calibration
    from .pipeline import process_video

    original = read_json(OLD_RUN / "runmanifest.json")
    result = process_video(original["video"]["path"], load_automatic_calibration(OLD_RUN / "calibration.json"),
                           ROOT / "configs/models-broadcast.json", ROOT / "runs",
                           tracker_config_path=ROOT / "configs/bytetrack.yaml",
                           team_config_path=ROOT / "configs/teams-broadcast.json")
    engineering = check_result(result)
    before = [json.loads(s) for s in (OLD_RUN / "framegegevens.jsonl").read_text().splitlines()]
    after = [json.loads(s) for s in (result.directory / "framegegevens.jsonl").read_text().splitlines()]
    identical = len(before) == len(after) and all(a.get("calibration") == b.get("calibration") for a, b in zip(before, after))
    if not identical:
        raise ValueError("Field calibrations changed during player-only improvement")
    roles = Counter(d["semantic_class"] for frame in after for d in frame["detections"]
                    if d["projection_status"] == "valid")
    summary = {"engineering": engineering, "field_calibrations_identical": identical,
               "on_pitch_roles": dict(roles), "original_run": str(OLD_RUN),
               "new_run": str(result.directory), "human_review_completed": False,
               "demonstration_is_accuracy_test": False}
    write_json(Path(output) / "demonstration.json", summary)
    report_root = ROOT / "reports/broadcast-pitch-v1"
    write_json(report_root / "demonstration.json", summary)
    for index in (0, 75, 149):
        shutil.copy2(result.directory / "controlebeelden" / f"frame_{index:06d}.jpg", report_root / f"frame_{index:06d}.jpg")
    compact = read_json(report_root / "summary.json")
    write_report(compact, summary)
    return summary


def write_card(package, summary):
    name = summary["selected"]
    report = summary["candidates"][name]
    player, team = report["player_detection_and_roles"]["per_class"][0], report["teams"]
    (package / "README.md").write_text(
        "# Broadcastspelers v1\n\n"
        f"Geselecteerd: `{name}`. Spelerprecision {player['precision']:.2%}, recall {player['recall']:.2%}; "
        f"teamaccuracy onder toegewezen gematchte spelers {team['accuracy_assigned']:.2%}, "
        f"teamdekking onder gematchte spelers {team['coverage_matched']:.2%}.\n\n"
        "Dit zijn ontwikkelmetingen op aparte SoccerNet-GSR-wedstrijden met referentiegeometrie; "
        "geen onafhankelijke eindtest en geen score voor automatische veldherkenning. "
        "Keepers blijven speler, maar een onzekere teamkoppeling blijft onbekend. "
        "Personen buiten het geldige veld worden niet als speler geanalyseerd of getoond.\n\n"
        "Start met `scripts/Start-Gezamenlijk.ps1` of `scripts/Start-Spelermodel.ps1 -Recognition broadcast`. "
        "Modelgewichten worden via Git LFS geleverd. Zie `reports/broadcast-pitch-v1/summary.json` voor "
        "splits, hashes, kandidaatsvergelijking en werkelijk trainingsbudget.\n", encoding="utf-8")


def write_report(summary, demo):
    lines = ["# Broadcastspelers en teams — 27 oktober 2026", "",
             "Spelers worden binnen het bestaande veld geselecteerd. De rolclassifier kan betrouwbare "
             "spelerlabels beschermen; officials blijven afzonderlijke rollen. Buitenveldse personen zijn uitgesteld.", "",
             "## Vergelijking", "",
             "Deze ontwikkelmeting gebruikt vaste validatiewedstrijden en referentiegeometrie uit providerannotaties. "
             "Ze meet detectie, rollen en teamgroepering samen, maar geen automatische veldnauwkeurigheid. "
             "Per clip is slechts één vaste A/B-omwisseling toegestaan.", "",
             "| Kandidaat | Spelerprecision | Recall | Team correct/toegewezen | Teamdekking gematcht | Correct team/alle spelers |",
             "|---|---:|---:|---:|---:|---:|"]
    for name, r in summary["candidates"].items():
        p, t = r["player_detection_and_roles"]["per_class"][0], r["teams"]
        lines.append(f"| {name} | {p['precision']:.2%} | {p['recall']:.2%} | {t['accuracy_assigned']:.2%} | "
                     f"{t['coverage_matched']:.2%} | {t['correct_fraction_all_players']:.2%} |")
    lines += ["", f"Geselecteerd: **{summary['selected']}**. Alle streefgrenzen gehaald: **{summary['targets_met']}**.", "",
              "## Data en training", "",
              f"Broadcastbeelden: {summary['data']['counts']}. Wedstrijden: {summary['data']['selection']['games']}.",
              f"Werkelijke GPU-fasetijd inclusief feature-extractie: {summary['training']['gpu_stage_wall_seconds'] / 60:.2f} minuten.",
              "Oorspronkelijke team-, keeper- en tracklabels blijven bewaard. Geen officiële test- of challengebeelden gebruikt.", "",
              "## Toepassing", "",
              f"Nieuwe uitvoer: `{demo['new_run']}`. De veldkalibraties zijn op alle frames identiek aan de oorspronkelijke analyse.",
              f"Open: [broadcastanalyse](http://127.0.0.1:8501/?run={Path(demo['new_run']).name}).", "",
              "Video, minimap en CSV gebruiken dezelfde teamindeling. Bij ontbrekende veldkalibratie blijven veldposities en telling onbekend.", "",
              "## Grenzen", "",
              "Keepers met afwijkende kleding worden niet in een veldspelerskleur gedwongen; zonder betrouwbare koppeling blijft hun team onbekend. "
              "Team- en keeperresultaten, gemiste spelers en foutpositieven staan afzonderlijk in het JSON-rapport. "
              "De getoonde bronclip is ontwikkeldata; visuele AI-controle is geen menselijke acceptatie of onafhankelijke eindtest. "
              "Tracking-ID's blijven tijdelijk.", "",
              "Reproduceren: `scripts/Run-BroadcastSpelersTraining.ps1`. Starten: `scripts/Start-Gezamenlijk.ps1`."]
    (ROOT / "docs/Broadcast_Spelers_en_Teams.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/broadcast-pitch-v1")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/broadcast-pitch-v1")
    parser.add_argument("--demonstrate-only", action="store_true")
    args = parser.parse_args()
    if not args.demonstrate_only:
        compare_and_package(args.dataset, args.output)
    print(demonstrate(args.output))
