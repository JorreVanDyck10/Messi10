"""Afzonderlijke YOLO11/26-profielen met controleerbare import en herstelbare startinstellingen."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
from pathlib import Path

from .contracts import PipelineError, read_json, sha256_file, write_json
from .detection import load_model_manifest, validate_detection_devices
from .video import ROOT

MODEL_SLOTS = ("appearance", "kit_embedding", "role_context")


def rebase_profile(profile: dict, origin: Path, destination: Path) -> dict:
    """Behoud alle instellingen en herschrijf alleen relatieve bestandsverwijzingen naar de nieuwe profielmap."""
    result = copy.deepcopy(profile)
    specs = result["models"] + [result[key] for key in MODEL_SLOTS if result.get(key)]
    for spec in specs:
        path = (origin / spec["weights"]).resolve()
        spec["weights"] = Path(os.path.relpath(path, destination)).as_posix()
    for key, value in result.get("handoff", {}).items():
        if key.endswith("_record") and isinstance(value, str):
            result["handoff"][key] = Path(os.path.relpath((origin / value).resolve(), destination)).as_posix()
    return result


def select_profile(model: str, root: Path = ROOT, experiment: Path | None = None) -> Path:
    """Kies een apart profiel; geef bij ontbrekende getrainde YOLO26-gewichten expliciete importinstructies."""
    if model == "yolo11":
        snapshot = root / "configs/models-broadcast-yolo11.json"
        return snapshot if snapshot.is_file() else root / "configs/models-broadcast.json"
    if model != "yolo26":
        raise PipelineError("Kies yolo11 of yolo26.")
    installed = root / "configs/models-broadcast-yolo26.json"
    if installed.is_file():
        return installed
    previous = (experiment or root / "artifacts/yolo26-players-20261113-v1") / "yolo26s-profile.json"
    if previous.is_file():
        return previous
    raise PipelineError(
        "Het gefinetunede YOLO26-spelerscheckpoint ontbreekt. "
        "Importeer Raouls best.pt met scripts/Import-Yolo26.ps1 -Weights <pad>. "
        "Een algemeen COCO-checkpoint vervangt dit voetbalmodel niet. "
        "De oorspronkelijke route blijft beschikbaar via scripts/Start-Yolo11.ps1."
    )


def register_yolo26(weights: Path, root: Path = ROOT) -> Path:
    """Controleer een echt voetbalcheckpoint en maak een onafhankelijke modelkopie zonder YOLO11 te wijzigen."""
    from ultralytics import YOLO

    weights = weights.resolve()
    if not weights.is_file():
        raise PipelineError(f"Checkpoint ontbreekt: {weights}.")
    with weights.open("rb") as stream:
        if stream.read(128).startswith(b"version https://git-lfs.github.com/spec/v1"):
            raise PipelineError("Dit is een Git LFS-pointer; haal eerst het echte gewichtsbestand op.")
    model = YOLO(str(weights))
    if model.task != "detect" or model.names != {0: "player"}:
        raise PipelineError("Verwacht Raouls getrainde spelercheckpoint met uitsluitend klasse 0 = player.")
    architecture = str(getattr(model.model, "yaml", {}).get("yaml_file", "")).lower()
    if "yolo26" not in architecture:
        raise PipelineError("Dit checkpoint is geen herkenbare YOLO26-architectuur.")
    del model
    baseline_path = select_profile("yolo11", root)
    baseline = load_model_manifest(baseline_path)
    suppliers = [s for s in baseline["models"] if "player" in s["class_mapping"].values()]
    if len(suppliers) != 1:
        raise PipelineError("De oorspronkelijke pipeline moet precies één spelersdetector bevatten.")
    digest = sha256_file(weights)
    output = root / "configs/models-broadcast-yolo26.json"
    if output.exists():
        existing = read_json(output)
        player = next(s for s in existing["models"] if "player" in s["class_mapping"].values())
        if player.get("weights_sha256") != digest:
            raise PipelineError(
                "Er bestaat al een ander YOLO26-profiel. Bewaar die versie vóór een nieuwe import."
            )
        load_model_manifest(output)
        return output
    stored = root / "artifacts/yolo26-players-v1" / digest[:12] / "players_best.pt"
    stored.parent.mkdir(parents=True, exist_ok=True)
    if stored.exists() and sha256_file(stored) != digest:
        raise PipelineError("De doelmap bevat afwijkende gewichten; import wordt gestopt.")
    if not stored.exists():
        temporary = stored.with_suffix(".importing")
        shutil.copy2(weights, temporary)
        if sha256_file(temporary) != digest:
            raise PipelineError("De gekopieerde modelbytes wijken af van de bron.")
        temporary.replace(stored)
    candidate = rebase_profile(baseline, baseline_path.parent, output.parent)
    player = next(s for s in candidate["models"] if "player" in s["class_mapping"].values())
    player.update(
        model_id="yolo26s-football-imported",
        weights=Path(os.path.relpath(stored, output.parent)).as_posix(),
        weights_sha256=digest,
        class_mapping={"0": "player"},
        expected_names={"0": "player"},
        nms=True,
    )
    candidate["profile_name"] = "YOLO26 voetbal — oorspronkelijke bal, teams, veld en tracking"
    candidate["handoff"] = {
        "source_checkpoint_sha256": digest,
        "original_profile_sha256": sha256_file(baseline_path),
        "human_review_completed": False,
        "independent_final_test_completed": False,
        "scope": "Alleen spelersdetector vervangen; nieuwe integratiecontrole vereist.",
    }
    staged = output.with_name(output.stem + ".importing.json")
    try:
        write_json(staged, candidate)
        load_model_manifest(staged)
        staged.replace(output)
    finally:
        staged.unlink(missing_ok=True)
    write_json(
        stored.parent / "provenance.json",
        {
            "weights_sha256": digest,
            "architecture": architecture,
            "original_profile_sha256": sha256_file(baseline_path),
            "trained_here": False,
        },
    )
    return output


def local_profile(model: str, device: str, root: Path = ROOT, experiment: Path | None = None) -> Path:
    """Maak een apparaatgebonden werkkopie van het gekozen profiel en controleer bestanden en device."""
    if not re.fullmatch(r"cpu|\d+", device):
        raise PipelineError("Device moet cpu of een numerieke CUDA-index zijn.")
    source = select_profile(model, root, experiment)
    output = root / f".cache/model-switch/{model}-{device}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = rebase_profile(read_json(source), source.parent, output.parent)
    for spec in manifest["models"] + [manifest[k] for k in MODEL_SLOTS if manifest.get(k)]:
        spec["device"] = device
    if model == "yolo26":
        import ultralytics

        version = tuple(int(p) for p in ultralytics.__version__.split(".")[:2])
        if version < (8, 4):
            raise PipelineError("YOLO26 vereist de aparte Ultralytics 8.4-omgeving; start Setup-Yolo26.ps1.")
        player = next(s for s in manifest["models"] if "player" in s["class_mapping"].values())
        player["nms"] = True
    write_json(output, manifest)
    checked = load_model_manifest(output)
    validate_detection_devices(checked)
    return output


def main() -> None:
    """Importeer een voetbalcheckpoint of controleer en print het lokale startprofiel voor een modelversie."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    install = commands.add_parser("import")
    install.add_argument("weights", type=Path)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--model", choices=("yolo11", "yolo26"), required=True)
    prepare.add_argument("--device", default="cpu")
    prepare.add_argument("--experiment", type=Path)
    args = parser.parse_args()
    try:
        path = (
            register_yolo26(args.weights)
            if args.command == "import"
            else local_profile(args.model, args.device, experiment=args.experiment)
        )
        print(json.dumps({"profile": str(path)}, ensure_ascii=False))
    except (PipelineError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
