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
from .contracts import digest_json, read_json, sha256_file, write_json
from .teams import load_team_settings
from .video import ROOT

OLD_RUN = ROOT / "runs/63d6a606d9cda9ade4c1719aecc03e50f573ec97469e7d5b3904a0d1f72425cb"


def build_profile(weights, roles=None, kit=None, *, protected=True, proposal_only=False):
    from ultralytics import YOLO

    profile = copy.deepcopy(read_json(ROOT / "configs/models-integrated-20261027.json"))
    profile["analysis_scope"] = "on_pitch_players"
    profile["profile_name"] = "Broadcast — spelers op het veld en Team A/B"
    profile["models"] = [s for s in profile["models"] if set(s["class_mapping"].values()) != {"ball"}]
    names = YOLO(str(weights)).names
    mapping = {str(k): v for k, v in names.items() if v in ({"person"} if proposal_only else {"player", "referee"})}
    if not mapping or (not proposal_only and "player" not in mapping.values()):
        raise ValueError("Checkpoint does not provide the declared trained source classes")
    profile["models"][0].update(weights=str(Path(weights).resolve()), weights_sha256=sha256_file(weights),
                                class_mapping=mapping, expected_names=mapping)
    profile["models"][1]["weights"] = str(ROOT / "artifacts/appearance-v1/person_proposals.pt")
    if proposal_only:
        profile["models"] = [profile["models"][0]]
        profile["models"][0]["model_id"] = "broadcast-person-proposals"
    if roles:
        import torch

        profile["appearance"].update(weights=str(Path(roles).resolve()), weights_sha256=sha256_file(roles),
                                     role_policy="preserve_detector_players" if protected else "classifier",
                                     role_names=torch.load(roles, map_location="cpu", weights_only=True)["role_names"])
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


def evaluation_directory(refined):
    code = digest_json({p.name: sha256_file(p) for p in Path(__file__).parent.glob("*.py")})[:12]
    return Path(refined) / ("final-evaluation-" + code)


def compare_and_package(dataset, output, refined=None, candidate_file=None):
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
    refine_record = None
    if refined:
        refined = Path(refined).resolve()
        refine_record = read_json(refined / "detector/status.json")
        if refine_record["status"] not in {"complete", "time_limited"}:
            raise ValueError("Refined detector training has not completed")
        larger = Path(refine_record["best"])
        if sha256_file(larger) != refine_record["best_sha256"]:
            raise ValueError("Refined checkpoint changed")
        roles, kit = refined / "roles/roles_teams.pt", refined / "teams/kit_embedding.pt"
        new_settings = load_team_settings({"method": "torso_embedding_dominant_modes_v1", "confirmation_samples": 1,
                                           **read_json(refined / "teams/metrics.json")["settings"]})
        # Re-evaluate the historical baseline using exactly this final evaluator.
        candidates = {"r007-baseline": candidates["r007-baseline"]}
        for label, weights in (("previous", BASE_PLAYERS), ("larger-player", larger)):
            profile = build_profile(weights, roles, kit)
            profile["appearance"]["role_confidence"] = .5
            if label == "larger-player":
                candidates[label + "-1280"] = copy.deepcopy(profile), new_settings
                single = copy.deepcopy(profile)
                single["models"] = single["models"][:1]
                single.pop("appearance")
                candidates[label + "-only-1280"] = single, new_settings
                profile["models"][0]["imgsz"] = 1920
                candidates[label + "-1920"] = copy.deepcopy(profile), new_settings
                single = copy.deepcopy(single)
                single["models"][0]["imgsz"] = 1920
                candidates[label + "-only-1920"] = single, new_settings
                tighter = copy.deepcopy(single)
                tighter["models"][0]["iou"] = .5
                candidates[label + "-only-1920-nms05"] = tighter, new_settings
            profile["models"][1].update(weights=str(ROOT / "models/yolo11s.pt"),
                weights_sha256=sha256_file(ROOT / "models/yolo11s.pt"), imgsz=1920)
            profile["person_geometry"] = True
            candidates[label + "-person-geometry"] = copy.deepcopy(profile), new_settings
            candidates[label + "-kit-recovery"] = copy.deepcopy(profile), {**new_settings, "kit_player_recovery": True}
            tighter = copy.deepcopy(profile)
            tighter["models"][1]["iou"] = .5
            candidates[label + "-kit-recovery-nms05"] = tighter, {**new_settings, "kit_player_recovery": True}
    additional_training = {}
    if candidate_file:
        import re

        candidate_file = Path(candidate_file).resolve()
        declared = read_json(candidate_file)
        candidates = {"r007-baseline": candidates["r007-baseline"]}
        for item in declared["candidates"]:
            name = item["name"]
            if not re.fullmatch(r"[a-z0-9-]+", name) or name in candidates:
                raise ValueError("Candidate names must be unique simple identifiers")
            candidates[name] = (read_json((candidate_file.parent / item["profile"]).resolve()),
                                load_team_settings((candidate_file.parent / item["teams"]).resolve()))
        for item in declared.get("training_records", []):
            additional_training[item["name"]] = read_json((candidate_file.parent / item["path"]).resolve())
    reports = {}
    for name, (profile, settings) in candidates.items():
        directory = (evaluation_directory(refined) if refined else output / "evaluation") / name
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
    write_json((refined or output) / "comparison.json", summary)
    if not improved:
        raise ValueError("No improvement over baseline; existing application profile preserved")
    package = ROOT / "artifacts/broadcast-players-v1"
    package.mkdir(parents=True, exist_ok=True)
    profile, settings = copy.deepcopy(candidates[selected])
    specs = [(spec, "players_best.pt" if "player" in spec["class_mapping"].values() else "person_proposals.pt")
             for spec in profile["models"]]
    specs += ([(profile["appearance"], "roles_teams.pt")] if profile.get("appearance") else [])
    specs += ([(profile["role_context"], "role_context.pt")] if profile.get("role_context") else [])
    specs += [(profile["kit_embedding"], "kit_embedding.pt")]
    for spec, filename in specs:
        target = package / filename
        if sha256_file(spec["weights"]) != spec["weights_sha256"]:
            raise ValueError("Selected source weight checksum changed")
        shutil.copy2(spec["weights"], target)
        spec.update(weights="../artifacts/broadcast-players-v1/" + filename, weights_sha256=sha256_file(target))
    profile["profile_name"] = "Broadcast — spelers en teams" + (" (ontwikkelprofiel)" if not summary["targets_met"] else "")
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
    if refined:
        compact["training"]["refinement"] = {"detector": refine_record,
            "roles": read_json(refined / "roles/metrics.json"), "teams": read_json(refined / "teams/metrics.json")}
        compact["training"]["gpu_stage_wall_seconds"] += sum(
            v["runtime_s"] for v in compact["training"]["refinement"].values())
    compact["training"]["additional_stages"] = additional_training
    compact["training"]["gpu_stage_wall_seconds"] += sum(v.get("runtime_s", 0) for v in additional_training.values())
    compact["training"]["time_limit_lifted_by_user"] = True
    write_json(report_root / "summary.json", compact)
    for filename in ("players_best.pt", "person_proposals.pt", "roles_teams.pt", "kit_embedding.pt", "role_context.pt"):
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
    teams = Counter(d["team_id"] or "unknown" for frame in after for d in frame["detections"]
                    if d["counted_as_player"])
    summary = {"engineering": engineering, "field_calibrations_identical": identical,
               "on_pitch_roles": dict(roles), "original_run": str(OLD_RUN),
               "on_pitch_player_teams": dict(teams),
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
        "splits, hashes, kandidaatsvergelijking en werkelijk trainingsbudget.\n\n"
        f"Alle streefgrenzen gehaald: **{summary['targets_met']}**. De validatieset is gebruikt voor checkpoint- "
        "en drempelselectie; deze cijfers zijn geen onafhankelijke generalisatietest.\n\n"
        "Bronnen: [SoccerNet-GSR](https://www.soccer-net.org/tasks/game-state-reconstruction), "
        "[SN-GSR-2024](https://huggingface.co/datasets/SoccerNet/SN-GSR-2024), "
        "[Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/). "
        "De oorspronkelijke gebruiksvoorwaarden blijven van toepassing.\n", encoding="utf-8")


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
              "De validatieset is herhaald gebruikt om checkpoints, drempels en combinaties te kiezen. "
              "Daarom zijn deze ontwikkelcijfers geen onafhankelijke eindtest. De aangeleerde shirtprojectie "
              "presteerde slechter dan de verzadigingsgewogen kleurhistogrammen; die eenvoudigere referentie "
              "is behouden. De speler- en rolmodellen zijn wel werkelijk bijgetraind.", "",
              "## Toepassing", "",
              f"Nieuwe uitvoer: `{demo['new_run']}`. De veldkalibraties zijn op alle frames identiek aan de oorspronkelijke analyse.",
              f"Open: [broadcastanalyse](http://127.0.0.1:8501/?run={Path(demo['new_run']).name}).", "",
              "Video, minimap en CSV gebruiken dezelfde teamindeling. Bij ontbrekende veldkalibratie blijven veldposities en telling onbekend.", "",
              "## Grenzen", "",
              "Keepers met afwijkende kleding worden niet in een veldspelerskleur gedwongen; zonder betrouwbare koppeling blijft hun team onbekend. "
              "Team- en keeperresultaten, gemiste spelers en foutpositieven staan afzonderlijk in het JSON-rapport. "
              "De getoonde bronclip is ontwikkeldata; visuele AI-controle is geen menselijke acceptatie of onafhankelijke eindtest. "
              "Tracking-ID's blijven tijdelijk.", "",
              f"Voor het geselecteerde profiel zijn {summary['candidates'][summary['selected']]['teams']['goalkeepers_matched']} "
              f"van {summary['candidates'][summary['selected']]['teams']['goalkeepers_total']} keepers gematcht; "
              f"{summary['candidates'][summary['selected']]['teams']['goalkeepers_correct_team']} krijgen het correcte team. "
              "Dit onderdeel blijft dus een beperking.", "",
              "Reproduceren: `scripts/Run-BroadcastSpelersTraining.ps1`. Starten: `scripts/Start-Gezamenlijk.ps1`."]
    (ROOT / "docs/Broadcast_Spelers_en_Teams.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/broadcast-pitch-v1")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/broadcast-pitch-v1")
    parser.add_argument("--demonstrate-only", action="store_true")
    parser.add_argument("--refined", type=Path)
    parser.add_argument("--candidates", type=Path)
    args = parser.parse_args()
    if not args.demonstrate_only:
        compare_and_package(args.dataset, args.output, args.refined, args.candidates)
    print(demonstrate(args.output))
