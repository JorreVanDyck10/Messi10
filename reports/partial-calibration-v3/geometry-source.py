from __future__ import annotations

from dataclasses import asdict, dataclass

import cv2
import numpy as np

from .contracts import Detection, PipelineError, VideoMetadata, digest_json

class CalibrationControlError(PipelineError):
    """Rejected calibration with independent checks available for visual diagnosis."""

    def __init__(self, checks, projected, errors, diagonal):
        super().__init__(f"Onafhankelijke controle faalt: fouten {errors.round(2).tolist()} pixels.")
        self.diagnostics = [
            {
                "name": point["name"],
                "u": point["u"],
                "v": point["v"],
                "clicked": [point["x"], point["y"]],
                "predicted": xy.tolist(),
                "error_px": float(error),
            }
            for point, xy, error in zip(checks, projected, errors)
        ]
        self.median_px = float(np.median(errors))
        self.maximum_px = float(max(errors))
        self.median_limit_px = float(0.005 * diagonal)
        self.maximum_limit_px = float(0.01 * diagonal)


def point_coordinate_issues(points: list[dict]) -> list[str]:
    """Name missing/non-finite cells without silently replacing them with zero."""
    issues = []
    for index, point in enumerate(points):
        invalid = []
        for field in ("x", "y", "u", "v"):
            value = point.get(field)
            try:
                valid = value is not None and not isinstance(value, bool) and np.isfinite(float(value))
            except (ValueError, TypeError, OverflowError):
                valid = False
            if not valid:
                invalid.append(field)
        if invalid:
            issues.append(f"{point.get('name', f'punt {index + 1}')} ({', '.join(invalid)})")
    return issues


@dataclass
class Calibration:
    video_sha256: str
    image_size: list[int]
    reference_frame: int
    points: list[dict]
    homography: list[list[float]]
    check_errors_px: list[float]
    review: dict
    coordinate_system: str = "normalized_u_length_v_width_v1"
    schema_version: int = 1

    @property
    def identity(self) -> str:
        return digest_json(asdict(self))

    @property
    def polygon(self) -> np.ndarray:
        """The four clicked fit points; a partial view need not cover the whole field."""
        return np.array([[p["x"], p["y"]] for p in self.points if p["role"] == "fit"], np.float32)

    def validate_for(self, video: VideoMetadata, approved: bool = True) -> None:
        if not isinstance(self.review, dict) or not isinstance(self.points, list):
            raise PipelineError("Kalibratie vereist een puntentabel en een reviewrecord.")
        if not isinstance(self.image_size, (list, tuple)) or len(self.image_size) != 2:
            raise PipelineError("Kalibratie vereist oorspronkelijke beeldafmetingen.")
        if not isinstance(self.reference_frame, int) or isinstance(self.reference_frame, bool):
            raise PipelineError("Referentieframe moet een gehele frame-index zijn.")
        if self.video_sha256 != video.sha256 or tuple(self.image_size) != video.size:
            raise PipelineError("Kalibratie hoort bij een andere clip of ander beeldformaat.")
        if self.coordinate_system != "normalized_u_length_v_width_v1" or self.schema_version != 1:
            raise PipelineError("Niet-ondersteund kalibratieformaat.")
        if not 0 <= self.reference_frame < video.frame_count:
            raise PipelineError("Ongeldig kalibratiereferentieframe.")
        # Never trust a loaded matrix or claimed error: recompute from the source correspondences.
        rebuilt = create_calibration(video, self.points, self.reference_frame)
        if np.shape(self.homography) != (3, 3) or not np.allclose(
            rebuilt.homography, self.homography, atol=1e-8
        ):
            raise PipelineError("Opgeslagen matrix komt niet overeen met de puntparen.")
        if np.shape(self.check_errors_px) != np.shape(rebuilt.check_errors_px) or not np.allclose(
            rebuilt.check_errors_px, self.check_errors_px, atol=1e-6
        ):
            raise PipelineError("Opgeslagen controlefouten komen niet overeen met de puntparen.")
        if approved and not (
            self.review.get("approved") is True
            and str(self.review.get("reviewer", "")).strip()
            and self.review.get("static_camera_confirmed") is True
            and self.review.get("temporal_frames") == [0, video.frame_count // 2, video.frame_count - 1]
            and str(self.review.get("source", "")).strip()
            and str(self.review.get("usage", "")).strip()
        ):
            raise PipelineError(
                "Bevestig reviewer, brongebruik en camerastabiliteit op begin, midden en einde."
            )


def create_calibration(video: VideoMetadata, points: list[dict], reference_frame: int = 0) -> Calibration:
    try:
        if not isinstance(reference_frame, int) or not 0 <= reference_frame < video.frame_count:
            raise PipelineError("Ongeldig kalibratiereferentieframe.")
        fit = [p for p in points if p["role"] == "fit"]
        check = [p for p in points if p["role"] == "check"]
        if len(fit) != 4 or len(check) < 2 or len(points) != len(fit) + len(check):
            raise PipelineError(
                "Gebruik precies vier fitpunten en minstens twee onafhankelijke controlepunten."
            )
        issues = point_coordinate_issues(points)
        if issues:
            raise PipelineError(
                "Vul geldige coördinaten in voor: "
                + "; ".join(issues)
                + ". Lege velden, NaN en oneindig zijn niet toegestaan."
            )
        src = np.array([[p["x"], p["y"]] for p in fit], dtype=np.float64)
        dst = np.array([[p["u"], p["v"]] for p in fit], dtype=np.float64)
        all_xy = np.array([[p["x"], p["y"]] for p in points], dtype=np.float64)
        all_uv = np.array([[p["u"], p["v"]] for p in points], dtype=np.float64)
        if not np.isfinite(all_xy).all() or not np.isfinite(all_uv).all():
            raise PipelineError("Kalibratiepunten moeten eindige getallen bevatten.")
        if len(np.unique(all_xy, axis=0)) != len(points) or len(np.unique(all_uv, axis=0)) != len(points):
            raise PipelineError("Fit- en controlepunten moeten onderling verschillend en onafhankelijk zijn.")
        if (all_xy < 0).any() or (all_xy[:, 0] >= video.width).any() or (all_xy[:, 1] >= video.height).any():
            raise PipelineError("Kalibratiepunten liggen buiten het oorspronkelijke beeld.")
        if (all_uv < 0).any() or (all_uv > 1).any():
            raise PipelineError("Veldcoördinaten moeten tussen 0 en 1 liggen.")
        target_polygon = dst.astype(np.float32)
        if not cv2.isContourConvex(target_polygon) or cv2.contourArea(target_polygon) < 0.001:
            raise PipelineError("Kies vier verspreide veldpunten in een niet-gekruiste volgorde.")
        polygon = src.astype(np.float32)
        if not cv2.isContourConvex(polygon) or cv2.contourArea(polygon) < video.width * video.height * 0.001:
            raise PipelineError(
                "Veldpolygon is te klein, gekruist of degeneratief; controleer de puntvolgorde."
            )
        matrix, _ = cv2.findHomography(src, dst, method=0)
        if matrix is None or not np.isfinite(matrix).all() or np.linalg.matrix_rank(matrix) != 3:
            raise PipelineError("Geen geldige homography berekend.")
        inverse = np.linalg.inv(matrix)
        # The clicked region must stay on one visible side of the perspective horizon.
        # Unseen parts of a panned-to field can legitimately lie behind the camera.
        denominators = (matrix @ np.column_stack([src, np.ones(4)]).T)[2]
        if (not np.isfinite(denominators).all() or np.min(np.abs(denominators)) < 1e-9
                or np.min(denominators) * np.max(denominators) <= 0):
            raise PipelineError("De fitpunten lopen over de perspectiefhorizon. Kies beter verspreide veldpunten.")
        check_uv = np.array([[p["u"], p["v"]] for p in check], dtype=np.float64)
        check_xy = np.array([[p["x"], p["y"]] for p in check], dtype=np.float64)
        projected = cv2.perspectiveTransform(check_uv.reshape(-1, 1, 2), inverse).reshape(-1, 2)
        errors = np.linalg.norm(projected - check_xy, axis=1)
        diagonal = np.hypot(video.width, video.height)
        if (
            not np.isfinite(errors).all()
            or np.median(errors) > 0.005 * diagonal
            or max(errors) > 0.01 * diagonal
        ):
            raise CalibrationControlError(check, projected, errors, diagonal)
        return Calibration(
            video.sha256,
            list(video.size),
            reference_frame,
            points,
            matrix.tolist(),
            errors.tolist(),
            {"approved": False},
        )
    except (KeyError, TypeError, ValueError, cv2.error, np.linalg.LinAlgError) as exc:
        if isinstance(exc, PipelineError):
            raise
        raise PipelineError(f"Ongeldige puntentabel: {exc}") from exc


def valid_box(detection: Detection, image_size: tuple[int, int]) -> bool:
    box = np.asarray(detection.bbox_xyxy, dtype=float)
    if box.shape != (4,) or not np.isfinite(box).all() or not np.isfinite(detection.confidence):
        return False
    x1, y1, x2, y2 = box
    width, height = image_size
    return bool(0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height and 0 <= detection.confidence <= 1)


def project_detection(detection: Detection, calibration: Calibration) -> None:
    detection.field_position = None
    if not valid_box(detection, tuple(calibration.image_size)):
        detection.projection_status = "invalid_box"
        return
    x1, _, x2, y2 = detection.bbox_xyxy
    point = ((x1 + x2) / 2, y2)
    if y2 >= calibration.image_size[1] - 1:
        detection.projection_status = "truncated_bottom"
    else:
        transformed = np.asarray(calibration.homography) @ [*point, 1]
        if not np.isfinite(transformed).all() or abs(transformed[2]) < 1e-12:
            detection.projection_status = "invalid_transform"
            return
        anchor = next(p for p in calibration.points if p["role"] == "fit")
        reference = np.asarray(calibration.homography)[2] @ [anchor["x"], anchor["y"], 1]
        if transformed[2] * reference <= 0:
            detection.projection_status = "outside_field"
            return
        uv = transformed[:2] / transformed[2]
        if not np.isfinite(uv).all():
            detection.projection_status = "invalid_transform"
        elif (uv < -1e-9).any() or (uv > 1 + 1e-9).any():
            detection.projection_status = "outside_field"
        else:
            detection.field_position = uv.tolist()
            detection.projection_status = "valid"
