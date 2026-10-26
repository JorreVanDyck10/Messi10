from __future__ import annotations

import math
import os
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
            if "tile_width" in spec:
                if (
                    type(spec["tile_width"]) is not int
                    or spec["tile_width"] < 128
                    or type(spec.get("tile_imgsz")) is not int
                    or spec["tile_imgsz"] < 128
                    or not 0 < float(spec.get("tile_overlap", 0)) < 0.5
                ):
                    raise PipelineError("Ongeldige overlappende detectie-uitsneden.")
            if "ball_tiles" in spec:
                from .ball_tiles import validate_ball_tile_config

                if (
                    len(mapping) != 1
                    or set(mapping.values()) != {"ball"}
                    or "tile_width" in spec
                    or next(iter(expected.values())).lower() not in {"ball", "sports ball", "in_play_ball"}
                ):
                    raise PipelineError(
                        "Ballentegels vereisen precies één echte ballenklasse en geen persoonsuitsneden."
                    )
                validate_ball_tile_config(spec["ball_tiles"])
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, PipelineError):
                raise
            raise PipelineError(f"Ongeldig modelmanifest: {exc}") from exc
    if manifest.get("appearance"):
        from .appearance import ROLE_NAMES

        spec = manifest["appearance"]
        weights = (path.parent / spec["weights"]).resolve()
        if not weights.is_file() or sha256_file(weights) != spec.get("weights_sha256"):
            raise PipelineError("Rol-/teamgewichten ontbreken of hun hash wijkt af.")
        if spec.get("role_names") != ROLE_NAMES or not spec.get("model_id"):
            raise PipelineError("Rolclassifier vereist de werkelijk getrainde klassen en een model-ID.")
        for key in ("role_confidence", "team_confidence"):
            value = spec.get(key)
            if not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 < value <= 1:
                raise PipelineError(f"Ongeldige classifierdrempel: {key}.")
        spec["weights"] = str(weights)
    return manifest


def available_roles(manifest):
    roles = {v for spec in manifest["models"] for v in spec["class_mapping"].values()}
    roles.update(manifest.get("appearance", {}).get("role_names", []))
    return roles


def merge_person_proposals(detections, overlap=0.5):
    """One human observation per overlapping proposal; keep non-human detections intact."""
    people = sorted(
        (d for d in detections if d.semantic_class in GROUND_ROLES),
        key=lambda d: (d.semantic_class != "person", d.confidence),
        reverse=True,
    )
    kept = []
    for candidate in people:
        x1, y1, x2, y2 = candidate.bbox_xyxy
        duplicate = False
        for index, other in enumerate(kept):
            a, b, c, d = other.bbox_xyxy
            intersection = max(0, min(x2, c) - max(x1, a)) * max(0, min(y2, d) - max(y1, b))
            union = (x2 - x1) * (y2 - y1) + (c - a) * (d - b) - intersection
            if union > 0 and intersection / union >= overlap:
                duplicate = True
                break
            # One detector may see the upper body while another sees the same
            # complete person. IoU alone misses that duplicate. Require distinct
            # proposal sources, almost full containment and aligned heads/axes;
            # ordinary overlapping teammates must remain separate observations.
            width, height = x2 - x1, y2 - y1
            other_width, other_height = c - a, d - b
            smaller_area = min(width * height, other_width * other_height)
            ratio = max(height, other_height) / max(1e-9, min(height, other_height))
            contained = (
                candidate.model_id != other.model_id
                and (candidate.semantic_class == "person") != (other.semantic_class == "person")
                and smaller_area > 0
                and intersection / smaller_area >= 0.9
                and 1.35 <= ratio <= 2.5
                and abs((x1 + x2) / 2 - (a + c) / 2) <= min(width, other_width) * 0.2
                and abs(y1 - b) <= max(height, other_height) * 0.15
            )
            if contained:
                # Preserve real model identity and original coordinates. A strong
                # full-body proposal provides the correct feet for projection.
                if height > other_height and candidate.confidence >= 0.5:
                    kept[index] = candidate
                duplicate = True
                break
        if not duplicate:
            kept.append(candidate)
    return kept + [d for d in detections if d.semantic_class not in GROUND_ROLES]


def validate_detection_devices(manifest: dict) -> None:
    """Fail before expensive field inference when a requested CUDA device is unavailable."""
    import torch

    for spec in [*manifest["models"], *([manifest["appearance"]] if manifest.get("appearance") else [])]:
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
        # Keep the local app usable without write access to the Windows user profile.
        root = Path(__file__).resolve().parents[2]
        os.environ.setdefault("YOLO_CONFIG_DIR", str(root / ".cache/ultralytics"))
        (Path(os.environ["YOLO_CONFIG_DIR"]) / "Ultralytics").mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", str(root / ".cache/matplotlib"))
        Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
        from ultralytics import YOLO

        validate_detection_devices(manifest)
        self.manifest = manifest
        self.models = []
        self.video_hash = ""
        self.appearance = None
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
        if manifest.get("appearance"):
            from .appearance import AppearanceClassifier

            self.appearance = AppearanceClassifier(manifest["appearance"])

    def set_video_identity(self, video_hash):
        if video_hash != self.video_hash and self.appearance:
            from .teams import VideoTeams

            self.appearance.video_teams = VideoTeams()
        self.video_hash = video_hash

    def detect(self, frame, frame_index: int) -> list[Detection]:
        detections = []
        for spec, model in self.models:
            if "ball_tiles" in spec:
                from .ball_tiles import predict_multiscale_ball

                source_class = int(next(iter(spec["class_mapping"])))
                boxes = predict_multiscale_ball(
                    model,
                    frame,
                    spec["ball_tiles"],
                    confidence=spec["confidence"],
                    local_iou=spec["iou"],
                    device=spec.get("device", "cpu"),
                    source_class=source_class,
                )
                for box in boxes:
                    detections.append(
                        Detection(
                            f"{frame_index}:{len(detections)}",
                            spec["model_id"],
                            source_class,
                            "ball",
                            box["bbox_xyxy"],
                            box["confidence"],
                        )
                    )
                continue
            inputs = [(frame, 0, int(spec["imgsz"]), False)]
            tile_width = spec.get("tile_width", frame.shape[1])
            if frame.shape[1] > tile_width:
                step = max(1, round(tile_width * (1 - spec["tile_overlap"])))
                starts = sorted(
                    set([*range(0, frame.shape[1] - tile_width + 1, step), frame.shape[1] - tile_width])
                )
                inputs.extend((frame[:, x : x + tile_width], x, spec["tile_imgsz"], True) for x in starts)
            for pixels, offset, imgsz, is_tile in inputs:
                result = model.predict(
                    pixels,
                    imgsz=imgsz,
                    conf=float(spec["confidence"]),
                    iou=float(spec["iou"]),
                    device=spec.get("device", "cpu"),
                    classes=[int(k) for k in spec["class_mapping"]],
                    verbose=False,
                )[0]
                if tuple(result.orig_shape) != pixels.shape[:2]:
                    raise PipelineError("Detectorcoördinaten horen niet bij het oorspronkelijke invoerbeeld.")
                for box, confidence, class_id in zip(
                    result.boxes.xyxy.cpu().numpy(),
                    result.boxes.conf.cpu().numpy(),
                    result.boxes.cls.cpu().numpy(),
                ):
                    if is_tile and (
                        (offset > 0 and box[0] <= 2)
                        or (offset + pixels.shape[1] < frame.shape[1] and box[2] >= pixels.shape[1] - 2)
                    ):
                        continue
                    box = box.astype(float).copy()
                    box[[0, 2]] += offset
                    class_id = int(class_id)
                    detections.append(
                        Detection(
                            f"{frame_index}:{len(detections)}",
                            spec["model_id"],
                            class_id,
                            spec["class_mapping"][str(class_id)],
                            box.tolist(),
                            float(confidence),
                        )
                    )
        if self.appearance:
            detections = merge_person_proposals(detections)
            self.appearance.classify(frame, detections, self.video_hash)
        return detections
