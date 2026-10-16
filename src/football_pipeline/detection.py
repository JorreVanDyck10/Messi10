from __future__ import annotations

import math
from pathlib import Path

from .contracts import Detection, PipelineError, read_json, sha256_file
from .participants import GROUND_ROLES


def load_model_manifest(path: str | Path) -> dict:
    path = Path(path).resolve()
    manifest = read_json(path)
    models = manifest.get("models", [])
    if manifest.get("schema_version") != 1 or not models:
        raise PipelineError("Modelmanifest vereist schema_version 1 en minstens één model.")
    owners, identifiers = {}, set()
    for spec in models:
        try:
            identifier = spec["model_id"]
            if not identifier or identifier in identifiers:
                raise PipelineError("Model-ID's moeten uniek zijn.")
            identifiers.add(identifier)
            weights = (path.parent / spec["weights"]).resolve()
            if not weights.is_file():
                raise PipelineError(f"Modelbestand ontbreekt: {weights}. Zie download-baseline in de README.")
            mapping = {int(k): str(v) for k, v in spec["class_mapping"].items()}
            if not mapping or any(not name.strip() or key < 0 for key, name in mapping.items()):
                raise PipelineError("Ongeldige klassemapping.")
            for semantic in set(mapping.values()):
                if semantic in owners:
                    raise PipelineError(f"Dubbele leverancier voor semantische klasse {semantic}.")
                owners[semantic] = identifier
            if not 0 < float(spec["confidence"]) <= 1 or not 0 < float(spec["iou"]) <= 1:
                raise PipelineError("Confidence en NMS-IoU moeten in (0,1] liggen.")
            if not math.isfinite(float(spec["imgsz"])) or int(spec["imgsz"]) <= 0:
                raise PipelineError("imgsz moet positief zijn.")
            expected = {int(k): str(v) for k, v in spec["expected_names"].items()}
            if set(mapping) != set(expected):
                raise PipelineError("expected_names moet iedere gebruikte bronklasse beschrijven.")
            if any(
                expected[k].lower() == "person" and value in GROUND_ROLES - {"person"}
                for k, value in mapping.items()
            ):
                raise PipelineError(
                    "De klasse person mag niet stilzwijgend player, referee of een andere rol worden."
                )
            weights_hash = sha256_file(weights)
            if spec.get("weights_sha256") and spec["weights_sha256"] != weights_hash:
                raise PipelineError(f"Gewichtshash wijkt af van de overdracht voor {identifier}.")
            spec["weights"] = str(weights)
            spec["weights_sha256"] = weights_hash
            spec["class_mapping"] = {str(k): v for k, v in mapping.items()}
            spec["confidence"], spec["iou"], spec["imgsz"] = (
                float(spec["confidence"]),
                float(spec["iou"]),
                int(spec["imgsz"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, PipelineError):
                raise
            raise PipelineError(f"Ongeldig modelmanifest: {exc}") from exc
    return manifest


def validate_detection_devices(manifest: dict) -> None:
    """Fail before expensive field inference when a requested CUDA device is unavailable."""
    import torch

    for spec in manifest["models"]:
        device = str(spec.get("device", "cpu")).lower().strip()
        if device == "cuda":
            device = "0"
        elif device.startswith("cuda:"):
            device = device[5:]
        if not device.replace(",", "").isdigit():
            continue
        indices = [int(index) for index in device.split(",") if index]
        if not torch.cuda.is_available() or any(index >= torch.cuda.device_count() for index in indices):
            raise PipelineError(
                f"Model {spec['model_id']} vraagt GPU {device}, maar deze Python-omgeving "
                f"heeft geen beschikbare bijbehorende CUDA-GPU (PyTorch {torch.__version__}). "
                "Voer scripts\\Setup-Persoon1.ps1 uit voor de GPU-omgeving, of start expliciet "
                "scripts\\Start-Spelermodel.ps1 -Device cpu."
            )


class UltralyticsDetector:
    def __init__(self, manifest: dict):
        from ultralytics import YOLO

        validate_detection_devices(manifest)
        self.manifest = manifest
        self.models = []
        for spec in manifest["models"]:
            model = YOLO(spec["weights"])
            if model.task != "detect":
                raise PipelineError("Deze pipeline verwacht een bounding-boxdetector.")
            for key, name in spec["expected_names"].items():
                if model.names.get(int(key)) != name:
                    raise PipelineError(
                        f"Klasse {key} van {spec['model_id']} heet {model.names.get(int(key))}, niet {name}."
                    )
            self.models.append((spec, model))

    def detect(self, frame, frame_index: int) -> list[Detection]:
        detections = []
        for spec, model in self.models:
            result = model.predict(
                frame,
                imgsz=int(spec["imgsz"]),
                conf=float(spec["confidence"]),
                iou=float(spec["iou"]),
                device=spec.get("device", "cpu"),
                classes=[int(k) for k in spec["class_mapping"]],
                verbose=False,
            )[0]
            if tuple(result.orig_shape) != frame.shape[:2]:
                raise PipelineError("Detectorcoördinaten horen niet bij het oorspronkelijke beeldformaat.")
            for box, confidence, class_id in zip(
                result.boxes.xyxy.cpu().numpy(),
                result.boxes.conf.cpu().numpy(),
                result.boxes.cls.cpu().numpy(),
            ):
                class_id = int(class_id)
                detections.append(
                    Detection(
                        f"{frame_index}:{len(detections)}",
                        spec["model_id"],
                        class_id,
                        spec["class_mapping"][str(class_id)],
                        box.astype(float).tolist(),
                        float(confidence),
                    )
                )
        return detections
