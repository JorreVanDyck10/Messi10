"""Registreert modelprofielen met expliciete bronklassen en herkomst voor overdracht naar de toepassing."""

import os
import tempfile
from pathlib import Path

from .contracts import PipelineError, digest_json, read_json, sha256_file, write_json
from .detection import load_model_manifest


def available_model_profiles(default: Path, directory: Path) -> dict[Path, str]:
    """Zoek de beschikbare modelprofielen en combineer hun metadata voor de modelkeuzelijst zonder
    inferentie uit te voeren.
    """
    profiles = {}
    seen = set()
    for path in dict.fromkeys(
        [default.resolve(), *(p.resolve() for p in sorted(directory.glob("models*.json")))]
    ):
        try:
            manifest = read_json(path)
            if manifest.get("schema_version") != 1 or not manifest.get("models"):
                continue
            normalized = []
            for model in manifest["models"]:
                spec = dict(model)
                if "weights" in spec:
                    spec["weights"] = str((path.parent / spec["weights"]).resolve())
                normalized.append(spec)
            heads = {}
            for name in ("appearance", "kit_embedding", "role_context"):
                if manifest.get(name):
                    heads[name] = dict(manifest[name])
                    heads[name]["weights"] = str((path.parent / heads[name]["weights"]).resolve())
            # A checkout may contain profiles made on a different computer.
            # Keep an explicitly requested default so its loader can explain errors.
            if path != default.resolve() and any(
                not spec.get("weights") or not Path(spec["weights"]).is_file()
                for spec in [*normalized, *heads.values()]
            ):
                continue
            identity = digest_json(
                {
                    "models": normalized,
                    "heads": heads,
                    "analysis_scope": manifest.get("analysis_scope", "all_participants"),
                    "person_geometry": manifest.get("person_geometry", False),
                    "person_box_fusion_weight": manifest.get("person_box_fusion_weight"),
                }
            )
            if identity in seen:
                continue
            seen.add(identity)
            profiles[path] = str(manifest.get("profile_name", path.stem))
        except (PipelineError, KeyError, TypeError, ValueError):
            if path == default.resolve():
                profiles[path] = path.stem
    return profiles


def register_player_model(
    weights: Path,
    mapping_path: Path,
    output: Path,
    *,
    model_id="players_v1",
    imgsz=1920,
    confidence=0.10,
    iou=0.70,
    device="cpu",
    evaluation_record: Path | None = None,
) -> dict:
    """Controleer checkpoint en expliciete bronklassemapping en schrijf een draagbaar modelmanifest met
    herkomst en gewichtshash.
    """
    from ultralytics import YOLO

    weights, output = weights.resolve(), output.resolve()
    if not weights.is_file():
        raise PipelineError(f"Getrainde gewichten ontbreken: {weights}.")
    if output.exists():
        raise PipelineError(
            "Dit modelprofiel bestaat al. Kies een nieuwe uitvoernaam om de vorige versie te bewaren."
        )
    mapping = read_json(mapping_path)
    if "player" not in mapping.values():
        raise PipelineError("Lever een expliciete klassemapping met player aan; losse labels volstaan niet.")
    if not 0 < confidence <= 0.10:
        raise PipelineError("Gebruik confidence maximaal 0.10 om lage ByteTrack-kandidaten te behouden.")
    try:
        model = YOLO(str(weights))
        if model.task != "detect":
            raise PipelineError("Spelertracking vereist een bounding-boxdetector.")
        names = {str(key): value for key, value in model.names.items()}
        if not set(mapping).issubset(names):
            raise PipelineError("De opgegeven klasse-ID's komen niet voor in het gewichtenbestand.")
    except PipelineError:
        raise
    except Exception as exc:
        raise PipelineError(f"Gewichten konden niet worden geladen: {exc}") from exc
    candidate = {
        "schema_version": 1,
        "profile_name": f"Spelermodel {model_id} — geschikt voor ByteTrack na MVP-review",
        "models": [
            {
                "model_id": model_id,
                "weights": Path(os.path.relpath(weights, output.parent)).as_posix(),
                "weights_sha256": sha256_file(weights),
                "class_mapping": mapping,
                "expected_names": {key: names[key] for key in mapping},
                "imgsz": imgsz,
                "confidence": confidence,
                "iou": iou,
                "device": device,
            }
        ],
    }
    if evaluation_record is not None:
        evaluation_record = evaluation_record.resolve()
        if not evaluation_record.is_file():
            raise PipelineError("Het opgegeven evaluatierecord ontbreekt.")
        candidate["handoff"] = {
            "evaluation_record": Path(os.path.relpath(evaluation_record, output.parent)).as_posix(),
            "evaluation_sha256": sha256_file(evaluation_record),
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    # The regular loader enforces every contract, including the person→player ban.
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".json", delete=False) as stream:
        temporary = Path(stream.name)
    try:
        write_json(temporary, candidate)
        load_model_manifest(temporary)
        with output.open("x", encoding="utf-8") as target:
            target.write(temporary.read_text(encoding="utf-8"))
    finally:
        temporary.unlink(missing_ok=True)
    return candidate
