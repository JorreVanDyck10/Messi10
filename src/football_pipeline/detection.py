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
    if manifest.get("analysis_scope", "all_participants") not in {"all_participants", "on_pitch_players"}:
        raise PipelineError("Onbekend analysebereik.")
    if "person_geometry" in manifest and (
        type(manifest["person_geometry"]) is not bool or manifest.get("analysis_scope") != "on_pitch_players"
    ):
        raise PipelineError("Persoonsgeometrie vereist een expliciet veldgericht profiel.")
    if "person_box_fusion_weight" in manifest:
        weight = manifest["person_box_fusion_weight"]
        if (
            type(weight) not in {float, int}
            or not math.isfinite(weight)
            or not 0 <= weight <= 1
            or not manifest.get("person_geometry")
        ):
            raise PipelineError("Boxcombinatie vereist persoonsgeometrie en een gewicht tussen nul en één.")
    if manifest.get("schema_version") != 1 or not models:
        raise PipelineError("Modelmanifest vereist schema_version 1 en minstens één model.")
    if "field_settings" in manifest:
        from .field_motion import DEFAULT_SETTINGS, validate_settings

        if not isinstance(manifest["field_settings"], dict):
            raise PipelineError("Veldinstellingen in het modelprofiel moeten een JSON-object zijn.")
        manifest["field_settings"] = validate_settings({**DEFAULT_SETTINGS, **manifest["field_settings"]})
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
        from .appearance import PITCH_ROLE_NAMES, ROLE_NAMES

        spec = manifest["appearance"]
        if spec.get("role_policy", "classifier") not in {"classifier", "preserve_detector_players"}:
            raise PipelineError("Onbekend beleid voor rolherkenning.")
        weights = (path.parent / spec["weights"]).resolve()
        if not weights.is_file() or sha256_file(weights) != spec.get("weights_sha256"):
            raise PipelineError("Rol-/teamgewichten ontbreken of hun hash wijkt af.")
        if spec.get("role_names") not in (ROLE_NAMES, PITCH_ROLE_NAMES) or not spec.get("model_id"):
            raise PipelineError("Rolclassifier vereist de werkelijk getrainde klassen en een model-ID.")
        if spec["role_names"] == PITCH_ROLE_NAMES and manifest.get("analysis_scope") != "on_pitch_players":
            raise PipelineError("De veldgerichte rolclassifier vereist spelersanalyse binnen het veld.")
        for key in ("role_confidence", "team_confidence"):
            value = spec.get(key)
            if not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 < value <= 1:
                raise PipelineError(f"Ongeldige classifierdrempel: {key}.")
        spec["weights"] = str(weights)
    if manifest.get("kit_embedding"):
        spec = manifest["kit_embedding"]
        weights = (path.parent / spec["weights"]).resolve()
        if not weights.is_file() or sha256_file(weights) != spec.get("weights_sha256"):
            raise PipelineError("Teamgewichten ontbreken of hun hash wijkt af.")
        if manifest.get("analysis_scope") != "on_pitch_players":
            raise PipelineError("Het teammodel vereist spelersanalyse binnen het veld.")
        spec["weights"] = str(weights)
    if manifest.get("role_context"):
        spec = manifest["role_context"]
        weights = (path.parent / spec["weights"]).resolve()
        if (
            manifest.get("analysis_scope") != "on_pitch_players"
            or not manifest.get("kit_embedding")
            or manifest.get("appearance", {}).get("role_names") != ["player", "referee", "person"]
        ):
            raise PipelineError("Veldrolcontext vereist de veldgerichte rol- en shirtmodellen.")
        if (
            not weights.is_file()
            or sha256_file(weights) != spec.get("weights_sha256")
            or not spec.get("model_id")
        ):
            raise PipelineError("Gewichten of model-ID voor veldrolcontext ontbreken of wijken af.")
        for key in ("player_threshold", "nonplayer_threshold"):
            if type(spec.get(key)) not in {float, int} or not 0.5 < spec[key] < 1:
                raise PipelineError("Veldrolcontext vereist conservatieve roldrempels.")
        end = spec.get("protect_end_fraction", 0.08)
        if type(end) not in {float, int} or not 0 <= end < 0.25:
            raise PipelineError("Ongeldige doelgebiedbescherming voor veldrolcontext.")
        spec["weights"] = str(weights)
    return manifest


def available_roles(manifest):
    roles = {v for spec in manifest["models"] for v in spec["class_mapping"].values()}
    roles.update(manifest.get("appearance", {}).get("role_names", []))
    return roles


def player_detection_sources(manifest):
    actual = [s for s in manifest["models"] if "player" in s["class_mapping"].values()]
    if actual:
        return actual
    if "player" in manifest.get("appearance", {}).get("role_names", []):
        # Person remains the detector's real source class. The verified trained
        # crop classifier must emit a positive player label before counting.
        return [s for s in manifest["models"] if "person" in s["class_mapping"].values()]
    return []


def merge_person_proposals(detections, overlap=0.5, *, preserve_same_source=False):
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
                smaller = min((x2 - x1) * (y2 - y1), (c - a) * (d - b))
                aligned_partial = (
                    preserve_same_source
                    and candidate.model_id == other.model_id
                    and candidate.semantic_class == other.semantic_class
                    and smaller > 0
                    and intersection / smaller >= 0.95
                    and min(y2 - y1, d - b) < 0.85 * max(y2 - y1, d - b)
                    and abs((x1 + x2) / 2 - (a + c) / 2) <= min(x2 - x1, c - a) * 0.1
                    and abs(y2 - d) <= max(y2 - y1, d - b) * 0.08
                )
                if aligned_partial:
                    # Two boxes share the same feet/axis, with one nearly inside
                    # the other. Prefer the complete original source box. This
                    # also removes partial duplicates at an image boundary.
                    if y2 - y1 > d - b and candidate.confidence >= 0.25:
                        kept[index] = candidate
                    duplicate = True
                    break
                distinct_same_source = (
                    preserve_same_source
                    and candidate.model_id == other.model_id
                    and candidate.semantic_class == other.semantic_class
                    and intersection / union < 0.8
                    and (
                        abs((x1 + x2) / 2 - (a + c) / 2) > min(x2 - x1, c - a) * 0.15
                        or abs(y1 - b) > min(y2 - y1, d - b) * 0.08
                    )
                )
                if distinct_same_source:
                    # The detector already ran same-class NMS at its configured
                    # threshold. Distinct heads in a crowd must not be erased by
                    # a second, more aggressive cross-detector proposal merge.
                    continue
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


def prefer_person_geometry(people, fusion_weight=0):
    """One-to-one specialist role evidence on a general detector's person box.

    Preserve the person model's real source identity and coordinates. A positive
    specialist class is separate evidence, never a person->player class mapping.
    """
    import numpy as np
    from scipy.optimize import linear_sum_assignment

    persons = merge_person_proposals(
        [d for d in people if d.semantic_class == "person"], preserve_same_source=True
    )
    specialists = [d for d in people if d.semantic_class in {"player", "referee"}]
    if not persons:
        return [d for d in specialists if d.semantic_class == "player" and d.confidence >= 0.75]
    if not specialists:
        return persons
    a = np.asarray([d.bbox_xyxy for d in persons], float)
    b = np.asarray([d.bbox_xyxy for d in specialists], float)
    intersection = np.maximum(
        0, np.minimum(a[:, None, 2:], b[None, :, 2:]) - np.maximum(a[:, None, :2], b[None, :, :2])
    ).prod(2)
    union = (a[:, 2:] - a[:, :2]).prod(1)[:, None] + (b[:, 2:] - b[:, :2]).prod(1) - intersection
    scores = np.divide(intersection, union, out=np.zeros_like(intersection), where=union > 0)
    used = set()
    for a, b in zip(*linear_sum_assignment(-scores)):
        if scores[a, b] < 0.35:
            continue
        source = specialists[b]
        persons[a].role_evidence = {
            "model_id": source.model_id,
            "source_class_id": source.source_class_id,
            "semantic_class": source.semantic_class,
            "confidence": source.confidence,
            "bbox_xyxy": list(source.bbox_xyxy),
            "overlap": float(scores[a, b]),
        }
        if fusion_weight and scores[a, b] >= 0.5 and source.confidence >= 0.25:
            person = persons[a]
            original = list(person.bbox_xyxy)
            person.box_geometry_evidence = {
                "method": "weighted_person_specialist",
                "person_model_id": person.model_id,
                "person_source_bbox": original,
                "specialist_model_id": source.model_id,
                "specialist_source_bbox": list(source.bbox_xyxy),
                "specialist_weight": fusion_weight,
            }
            person.bbox_xyxy = (
                (1 - fusion_weight) * np.asarray(original) + fusion_weight * np.asarray(source.bbox_xyxy)
            ).tolist()
        used.add(b)
    fallback = [
        d
        for i, d in enumerate(specialists)
        if i not in used
        and d.semantic_class == "player"
        and d.confidence >= 0.75
        and scores[:, i].max() < 0.2
    ]
    return persons + fallback


def validate_detection_devices(manifest: dict) -> None:
    """Fail before expensive field inference when a requested CUDA device is unavailable."""
    import torch

    for spec in [
        *manifest["models"],
        *(manifest[k] for k in ("appearance", "kit_embedding") if manifest.get(k)),
    ]:
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
        self.kit_embedding = None
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
        if manifest.get("kit_embedding"):
            from .kit_embedding import KitEmbedding

            self.kit_embedding = KitEmbedding(manifest["kit_embedding"])
        self.role_context = None
        if manifest.get("role_context"):
            from .role_context import RoleContext

            self.role_context = RoleContext(
                manifest["role_context"],
                manifest["appearance"]["weights_sha256"],
                manifest["kit_embedding"]["weights_sha256"],
            )
            self.appearance.context_projection = (
                self.role_context.cnn_center.to(self.appearance.device),
                self.role_context.cnn_projection.to(self.appearance.device),
            )

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
                            player_kind="goalkeeper"
                            if str(spec.get("expected_names", {}).get(str(class_id), "")).lower()
                            == "goalkeeper"
                            else None,
                            player_kind_source="detector"
                            if str(spec.get("expected_names", {}).get(str(class_id), "")).lower()
                            == "goalkeeper"
                            else None,
                        )
                    )
        if self.appearance and getattr(self, "manifest", {}).get("analysis_scope") != "on_pitch_players":
            detections = merge_person_proposals(detections)
        if self.appearance and getattr(self, "manifest", {}).get("analysis_scope") != "on_pitch_players":
            self.appearance.classify(frame, detections, self.video_hash)
        return detections

    def classify_on_pitch(self, frame, detections, *, projector=None):
        """Refine only geometrically eligible people, after current-frame projection."""
        from .participants import field_exclusion_reason

        size = (frame.shape[1], frame.shape[0])
        people = [
            d
            for d in detections
            if d.semantic_class in GROUND_ROLES and field_exclusion_reason(d, size) is None
        ]
        merged = (
            prefer_person_geometry(people, getattr(self, "manifest", {}).get("person_box_fusion_weight", 0))
            if getattr(self, "manifest", {}).get("person_geometry")
            else merge_person_proposals(people, preserve_same_source=True)
        )
        eligible_ids = {id(d) for d in people}
        # An outside-field proposal cannot suppress an inside-field athlete.
        # Keep excluded raw observations for audit, without role/team inference.
        detections[:] = merged + [d for d in detections if id(d) not in eligible_ids]
        if projector is not None:
            for d in merged:
                if d.box_geometry_evidence:
                    projector(d)
        people = [d for d in merged if field_exclusion_reason(d, size) is None]
        if self.appearance:
            self.appearance.classify(frame, people, self.video_hash)
        if self.kit_embedding:
            self.kit_embedding.update(frame, people)
        if getattr(self, "role_context", None):
            self.role_context.update(people, size)
