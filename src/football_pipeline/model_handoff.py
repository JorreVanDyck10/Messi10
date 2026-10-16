"""Register an explicitly mapped player model without changing baseline semantics."""

import os
import tempfile
from pathlib import Path

from .contracts import PipelineError, read_json, sha256_file, write_json
from .detection import load_model_manifest


def available_model_profiles(default: Path, directory: Path) -> dict[Path, str]:
    profiles = {}
    for path in dict.fromkeys(
        [default.resolve(), *(p.resolve() for p in sorted(directory.glob("models*.json")))]
    ):
        try:
            manifest = read_json(path)
            if manifest.get("schema_version") != 1 or not manifest.get("models"):
                continue
            profiles[path] = str(manifest.get("profile_name", path.stem))
        except PipelineError:
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
