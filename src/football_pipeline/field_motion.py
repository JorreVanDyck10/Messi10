"""Controleert veldgeometrie en overbrugt korte uitval met gemeten camerabeweging en begrensde geldigheid.


Model hold-outs are a self-consistency check, never human accuracy evidence.
The field network, player detector and manual/static-camera workflow stay separate.
"""

from __future__ import annotations

import cv2
import numpy as np

from .automatic_calibration import transform
from .contracts import PipelineError
from .field_layout import LINES_UV, POINTS_UV

DEFAULT_SETTINGS = {
    "version": 2,
    "keypoint_threshold": 0.3434,
    "line_threshold": 0.7867,
    "motion": True,
    "tracking_width": 960,
    "forward_backward_px": 1.5,
    "minimum_motion_inliers": 20,
    "minimum_motion_ratio": 0.6,
    "maximum_age_s": 2.0,
    "ransac_px": 3.0,
    "median_diagonal_fraction": 0.005,
    "maximum_diagonal_fraction": 0.01,
    "minimum_image_hull_fraction": 0.001,
    "minimum_motion_hull_fraction": 0.01,
    "cut_mean_difference": 45.0,
    "cut_histogram_distance": 0.55,
    "holdout_rule": "two_semantic_tertiles_no_refit",
}

# Candidate only: DEFAULT_SETTINGS and the installed runtime keep their v2 policy
# until the reviewed comparison passes the release gate.
RELIABLE_SETTINGS = {**DEFAULT_SETTINGS, "version": 3}


def validate_settings(settings):
    if (
        set(settings) != set(DEFAULT_SETTINGS)
        or type(settings["version"]) is not int
        or settings["version"] not in (2, 3)
    ):
        raise PipelineError("Onbekende instellingen voor automatische kalibratie.")
    if type(settings["motion"]) is not bool or settings["holdout_rule"] != DEFAULT_SETTINGS["holdout_rule"]:
        raise PipelineError("Ongeldig kalibratieprofiel.")
    for name, default in DEFAULT_SETTINGS.items():
        if type(default) in (int, float):
            value = settings[name]
            if type(value) not in (int, float) or not np.isfinite(value) or value <= 0:
                raise PipelineError(f"Ongeldige kalibratie-instelling: {name}")
    if (
        settings["tracking_width"] > 960
        or settings["maximum_age_s"] > 2
        or settings["minimum_motion_inliers"] < 20
        or not 0.6 <= settings["minimum_motion_ratio"] <= 1
        or settings["forward_backward_px"] > 1.5
        or settings["median_diagonal_fraction"] > 0.005
        or settings["maximum_diagonal_fraction"] > 0.01
        or not 0 < settings["keypoint_threshold"] <= 1
        or not 0 < settings["line_threshold"] <= 1
    ):
        raise PipelineError("Het profiel overschrijdt de afgesproken veiligheidsgrenzen.")
    return dict(settings)


def _spread(xy, size, minimum):
    return cv2.contourArea(cv2.convexHull(np.asarray(xy, np.float32))) >= np.prod(size) * minimum


def checked_matrix(inverse, xy, uv):
    """Return image -> field only for finite, oriented, nondegenerate visible support."""
    if inverse is None or not np.isfinite(inverse).all() or np.linalg.cond(inverse) > 1e12:
        raise ValueError("degenerate_geometry")
    center = np.mean(uv, axis=0)
    probes = transform([center, center + [0.001, 0], center + [0, 0.001]], inverse)
    jacobian = np.column_stack((probes[1] - probes[0], probes[2] - probes[0]))
    if jacobian[0, 0] <= 0 or jacobian[1, 1] <= 0 or np.linalg.det(jacobian) <= 0:
        raise ValueError("orientation_unknown")
    matrix = np.linalg.inv(inverse)
    transform(xy, matrix)  # Includes the projective horizon check on visible support.
    return matrix / np.linalg.norm(matrix)


def line_checks(lines, inverse):
    errors, identifiers = [], []
    for line in lines:
        # Validate the observed line in homogeneous coordinates. Its virtual full-pitch
        # endpoints can straddle the horizon while the visible segment is perfectly valid.
        field = np.column_stack((np.asarray(LINES_UV[line["id"]]), np.ones(2)))
        projected = field @ np.asarray(inverse).T
        coefficients = np.cross(projected[0], projected[1])
        length = np.hypot(*coefficients[:2])
        coordinates = np.asarray(line["xy"])
        if (
            not np.isfinite(coefficients).all()
            or length < 1e-10
            or np.linalg.norm(coordinates[1] - coordinates[0]) < 5
        ):
            continue
        errors.extend((np.abs(np.column_stack((coordinates, np.ones(2))) @ coefficients) / length).tolist())
        identifiers.append(line["id"])
    return errors, identifiers


def estimate_checked(observation, image_size, settings=None):
    settings = validate_settings(settings or DEFAULT_SETTINGS)
    result = {
        "schema_version": 2,
        "status": "insufficient_points",
        "homography": None,
        "source": "unavailable",
        "quality": {},
        "points": [],
        "lines": [],
        "reference_frame": None,
        "age_s": None,
        "motion_quality": {},
        "tracked_points": [],
    }
    if settings["version"] == 3:
        result.update(schema_version=3, visible_field_polygon_xy=None)
    try:
        width, height = image_size
        for kind, canonical in (("points", POINTS_UV), ("lines", LINES_UV)):
            seen = set()
            for item in observation[kind]:
                identifier = item["id"]
                if type(identifier) is not int or identifier in seen:
                    raise ValueError("invalid_observation")
                seen.add(identifier)
                score = float(item["confidence"])
                xy = np.asarray([[item["x"], item["y"]]] if kind == "points" else item["xy"], float)
                if (
                    not np.isfinite(xy).all()
                    or not np.isfinite(score)
                    or not 0 <= score <= 1
                    or xy.shape != ((1, 2) if kind == "points" else (2, 2))
                    or (xy < 0).any()
                    or (xy[:, 0] >= width).any()
                    or (xy[:, 1] >= height).any()
                ):
                    raise ValueError("invalid_observation")
                threshold = settings["keypoint_threshold" if kind == "points" else "line_threshold"]
                if identifier in canonical and score >= threshold:
                    result[kind].append(item)
        points = sorted(result["points"], key=lambda p: p["id"])
        n = len(points)
        result["quality"]["ground_points"] = n
        if n < 4:
            return result
        xy = np.asarray([[p["x"], p["y"]] for p in points], float)
        uv = np.asarray([POINTS_UV[p["id"]] for p in points], float)
        # Semantic, deterministic split BEFORE fitting or examining errors. Never refit the controls.
        holdout = [n // 3, 2 * n // 3] if n >= 6 else []
        fit = [i for i in range(n) if i not in holdout]
        result["quality"].update(
            fit_ids=[points[i]["id"] for i in fit],
            control_ids=[points[i]["id"] for i in holdout],
            independent_human_controls=False,
        )
        if not _spread(xy[fit], image_size, settings["minimum_image_hull_fraction"]) or not _spread(
            uv[fit], (1, 1), 0.0001
        ):
            raise ValueError("degenerate_geometry")
        diagonal = float(np.hypot(width, height))
        cv2.setRNGSeed(0)
        inverse, mask = cv2.findHomography(uv[fit], xy[fit], cv2.RANSAC, diagonal * 0.005)
        matrix = checked_matrix(inverse, xy, uv)
        inliers = mask.ravel().astype(bool)
        result["quality"]["inliers"] = int(inliers.sum())
        if inliers.sum() < 4 or inliers.mean() < 0.7:
            raise ValueError("inconsistent_points")
        fit_errors = np.linalg.norm(transform(uv[fit][inliers], inverse) - xy[fit][inliers], axis=1)
        errors = (
            np.linalg.norm(transform(uv[holdout], inverse) - xy[holdout], axis=1) if holdout else np.array([])
        )
        line_errors, checked_lines = line_checks(result["lines"], inverse)
        # Two different line directions provide extra checks for the four/five-point case.
        diverse_lines = False
        for a in checked_lines:
            va = np.diff(np.asarray(LINES_UV[a]), axis=0)[0]
            for b in checked_lines:
                vb = np.diff(np.asarray(LINES_UV[b]), axis=0)[0]
                diverse_lines |= abs(va[0] * vb[1] - va[1] * vb[0]) > 0.001
        result["quality"].update(
            ground_lines=len(checked_lines), control_errors_px=errors.tolist(), line_errors_px=line_errors
        )
        if not holdout and not diverse_lines:
            raise ValueError("insufficient_controls")
        for values, reason in (
            (fit_errors, "inconsistent_points"),
            (errors, "inconsistent_controls"),
            (line_errors, "inconsistent_lines"),
        ):
            if len(values) and (
                np.median(values) > diagonal * settings["median_diagonal_fraction"]
                or max(values) > diagonal * settings["maximum_diagonal_fraction"]
            ):
                raise ValueError(reason)
        result.update(status="valid", source="detected", homography=matrix.tolist())
        result["quality"].update(
            control_median_px=float(np.median(errors)) if len(errors) else None,
            control_maximum_px=float(max(errors)) if len(errors) else None,
        )
    except (KeyError, TypeError, ValueError, OverflowError, cv2.error, np.linalg.LinAlgError) as exc:
        reason = str(exc)
        result.update(
            status=reason
            if reason
            in {
                "degenerate_geometry",
                "orientation_unknown",
                "inconsistent_points",
                "insufficient_controls",
                "inconsistent_controls",
                "inconsistent_lines",
            }
            else "invalid_observation",
            homography=None,
            source="unavailable",
        )
    if settings["version"] == 3:
        from .field_bounds import attach_visible_field

        result = attach_visible_field(result, image_size)
        result["schema_version"] = 3
    return result


class LegacyCameraCalibration:
    """One sequential stream; reference age is never refreshed by a propagated result."""

    def __init__(self, fps, settings=None):
        self.settings = validate_settings(settings or DEFAULT_SETTINGS)
        self.fps = fps
        self.previous = None
        self.state = None
        self.anchor = None
        self.last_recognition = None
        self.last_index = None

    def update(self, frame, direct, index):
        s = self.settings
        height, width = frame.shape[:2]
        scale = min(1.0, s["tracking_width"] / width)
        small = cv2.resize(frame, (round(width * scale), round(height * scale)))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        result = dict(direct)
        result.update(
            frame_index=index,
            reference_frame=self.last_recognition,
            age_s=(index - self.last_recognition) / self.fps if self.last_recognition is not None else None,
            motion_quality={},
            tracked_points=[],
        )
        if self.last_index is not None and index != self.last_index + 1:
            self.state, self.anchor = None, None
        self.last_index = index
        # Direct recognition always supersedes a propagated estimate, including after a cut.
        if direct["status"] == "valid":
            self.anchor = index
            self.last_recognition = index
            result.update(reference_frame=index, age_s=0.0, source="detected")
        elif (
            s["motion"]
            and self.previous is not None
            and self.state is not None
            and direct["status"] not in {"invalid_observation", "degenerate_geometry", "orientation_unknown"}
        ):
            age = (index - self.anchor) / self.fps
            result.update(reference_frame=self.anchor, age_s=age)
            try:
                if age > s["maximum_age_s"]:
                    raise ValueError("bridge_expired")
                old, old_gray = self.previous
                difference = float(np.mean(cv2.absdiff(old_gray, gray)))
                histograms = [
                    cv2.normalize(
                        cv2.calcHist([im], [0, 1], None, [24, 16], [0, 180, 0, 256]), None
                    ).flatten()
                    for im in (cv2.cvtColor(old, cv2.COLOR_BGR2HSV), cv2.cvtColor(small, cv2.COLOR_BGR2HSV))
                ]
                distance = float(cv2.compareHist(histograms[0], histograms[1], cv2.HISTCMP_BHATTACHARYYA))
                result["motion_quality"].update(mean_difference=difference, histogram_distance=distance)
                if difference > s["cut_mean_difference"] or distance > s["cut_histogram_distance"]:
                    raise ValueError("camera_cut")
                mask = cv2.inRange(
                    cv2.cvtColor(old, cv2.COLOR_BGR2HSV), np.array([25, 30, 25]), np.array([95, 255, 255])
                )
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
                # Intersect grass with the previously visible, projected pitch.
                yy, xx = np.indices(mask.shape)
                source_xy = np.column_stack((xx.ravel(), yy.ravel())) / scale
                mapped = (
                    np.column_stack((source_xy, np.ones(len(source_xy))))
                    @ np.asarray(self.state["homography"]).T
                )
                with np.errstate(divide="ignore", invalid="ignore"):
                    uv = mapped[:, :2] / mapped[:, 2:]
                inside = np.isfinite(uv).all(axis=1) & (uv >= 0).all(axis=1) & (uv <= 1).all(axis=1)
                mask[~inside.reshape(mask.shape)] = 0
                p0 = cv2.goodFeaturesToTrack(
                    old_gray, maxCorners=600, qualityLevel=0.01, minDistance=8, mask=mask
                )
                if p0 is None or len(p0) < s["minimum_motion_inliers"]:
                    raise ValueError("insufficient_motion_matches")
                lk = dict(
                    winSize=(21, 21),
                    maxLevel=3,
                    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
                )
                p1, forward, _ = cv2.calcOpticalFlowPyrLK(old_gray, gray, p0, None, **lk)
                if p1 is None or forward is None:
                    raise ValueError("insufficient_motion_matches")
                back, backward, _ = cv2.calcOpticalFlowPyrLK(gray, old_gray, p1, None, **lk)
                if back is None or backward is None:
                    raise ValueError("insufficient_motion_matches")
                fb = np.linalg.norm(p0 - back, axis=2).ravel()
                good = (
                    forward.ravel().astype(bool)
                    & backward.ravel().astype(bool)
                    & np.isfinite(fb)
                    & (fb <= s["forward_backward_px"])
                )
                a, b = p0.reshape(-1, 2)[good], p1.reshape(-1, 2)[good]
                good_bounds = (
                    np.isfinite(b).all(axis=1)
                    & (b >= 0).all(axis=1)
                    & (b[:, 0] < gray.shape[1])
                    & (b[:, 1] < gray.shape[0])
                )
                a, b = a[good_bounds], b[good_bounds]
                if len(a) < s["minimum_motion_inliers"]:
                    raise ValueError("insufficient_motion_matches")
                cv2.setRNGSeed(0)
                movement, inliers = cv2.findHomography(a, b, cv2.RANSAC, s["ransac_px"])
                if movement is None or inliers is None:
                    raise ValueError("invalid_motion")
                inliers = inliers.ravel().astype(bool)
                count, ratio = int(inliers.sum()), float(inliers.mean())
                result["motion_quality"].update(
                    matches=len(a),
                    inliers=count,
                    inlier_ratio=ratio,
                    forward_backward_max_px=float(fb[good].max()),
                )
                if count < s["minimum_motion_inliers"] or ratio < s["minimum_motion_ratio"]:
                    raise ValueError("inconsistent_motion")
                residuals = np.linalg.norm(transform(a[inliers], movement) - b[inliers], axis=1)
                result["motion_quality"].update(
                    reprojection_median_px=float(np.median(residuals)),
                    reprojection_maximum_px=float(max(residuals)),
                )
                if np.median(residuals) > s["forward_backward_px"]:
                    raise ValueError("inconsistent_motion")
                if not _spread(a[inliers], gray.shape[::-1], s["minimum_motion_hull_fraction"]):
                    raise ValueError("localized_motion")
                # Convert measured small-image movement into original pixel coordinates.
                scaling = np.diag([scale, scale, 1.0])
                movement = np.linalg.inv(scaling) @ movement @ scaling
                inverse = movement @ np.linalg.inv(np.asarray(self.state["homography"]))
                support = b[inliers] / scale
                support_uv = transform(a[inliers] / scale, np.asarray(self.state["homography"]))
                matrix = checked_matrix(inverse, support, support_uv)
                # Reject disagreement with visible model points, also while bridging dropout.
                points = direct.get("points", [])
                if points:
                    uv = [POINTS_UV[p["id"]] for p in points]
                    pixels = [[p["x"], p["y"]] for p in points]
                    errors = np.linalg.norm(transform(uv, inverse) - pixels, axis=1)
                    result["motion_quality"]["semantic_errors_px"] = errors.tolist()
                    if (
                        np.median(errors) > np.hypot(width, height) * 0.005
                        or max(errors) > np.hypot(width, height) * 0.01
                    ):
                        raise ValueError("motion_semantic_disagreement")
                line_errors, line_ids = line_checks(direct.get("lines", []), inverse)
                result["motion_quality"].update(line_errors_px=line_errors, checked_line_ids=line_ids)
                if line_errors and (
                    np.median(line_errors) > np.hypot(width, height) * 0.005
                    or max(line_errors) > np.hypot(width, height) * 0.01
                ):
                    raise ValueError("motion_line_disagreement")
                result.update(
                    status="valid",
                    source="tracked",
                    homography=matrix.tolist(),
                    recognition_status=direct["status"],
                    tracked_points=support.tolist(),
                    recognition_quality=direct.get("quality", {}),
                    quality={
                        "ground_points": len(points),
                        "motion_support": count,
                        "independent_human_controls": False,
                    },
                )
            except (ValueError, TypeError, cv2.error, np.linalg.LinAlgError) as exc:
                result.update(
                    status=str(exc) if isinstance(exc, ValueError) else "invalid_motion",
                    source="unavailable",
                    homography=None,
                )
        if result["status"] != "valid":
            self.state, self.anchor = None, None
        else:
            self.state = result
        self.previous = (small, gray)
        return result


class CameraCalibration(LegacyCameraCalibration):
    """V3 checks direct recognition against measured motion; v2 retains its policy."""

    def _reset(self):
        self.state = self.anchor = self.last_recognition = self.previous = None

    def update(self, frame, direct, index):
        if self.settings["version"] == 2:
            return super().update(frame, direct, index)

        from .field_bounds import attach_visible_field

        height, width = frame.shape[:2]
        s = self.settings
        temporal = {"status": "no_previous_calibration", "camera_reset": False}
        consecutive = self.last_index is None or index == self.last_index + 1
        if not consecutive:
            self._reset()
            temporal.update(status="frame_gap", camera_reset=True)
        elif self.previous is not None:
            scale = min(1.0, s["tracking_width"] / width)
            small = cv2.resize(frame, (round(width * scale), round(height * scale)))
            old, old_gray = self.previous
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            difference = float(np.mean(cv2.absdiff(old_gray, gray)))
            histograms = [
                cv2.normalize(cv2.calcHist([im], [0, 1], None, [24, 16], [0, 180, 0, 256]), None).flatten()
                for im in (cv2.cvtColor(old, cv2.COLOR_BGR2HSV), cv2.cvtColor(small, cv2.COLOR_BGR2HSV))
            ]
            distance = float(cv2.compareHist(histograms[0], histograms[1], cv2.HISTCMP_BHATTACHARYYA))
            temporal.update(mean_difference=difference, histogram_distance=distance)
            if difference > s["cut_mean_difference"] or distance > s["cut_histogram_distance"]:
                self._reset()
                temporal.update(status="camera_cut", camera_reset=True)

        if direct["status"] == "valid":
            previous_state = self.state
            if previous_state is not None and s["motion"]:
                # Ask the preserved motion implementation for a prediction WITHOUT
                # allowing the new semantic observations to influence its motion fit.
                probe = dict(direct, status="insufficient_points", points=[], lines=[])
                predicted = super().update(frame, probe, index)
                if predicted["status"] == "valid":
                    support = np.asarray(predicted["tracked_points"])
                    try:
                        uv = transform(support, np.asarray(predicted["homography"]))
                        pixels = transform(uv, np.linalg.inv(np.asarray(direct["homography"])))
                        errors = np.linalg.norm(pixels - support, axis=1)
                        median, maximum = float(np.median(errors)), float(max(errors))
                        temporal.update(
                            status="consistent",
                            median_error_px=median,
                            maximum_error_px=maximum,
                            support_points=len(support),
                            motion_quality=predicted["motion_quality"],
                        )
                        if (
                            median > np.hypot(width, height) * s["median_diagonal_fraction"]
                            or maximum > np.hypot(width, height) * s["maximum_diagonal_fraction"]
                        ):
                            raise ValueError("temporal_disagreement")
                    except (ValueError, np.linalg.LinAlgError):
                        self._reset()
                        temporal.update(status="temporal_disagreement", camera_reset=True)
                        direct = dict(
                            direct, status="temporal_disagreement", homography=None, source="unavailable"
                        )
                else:
                    temporal.update(
                        status="motion_unavailable",
                        reason=predicted["status"],
                        motion_quality=predicted.get("motion_quality", {}),
                    )
                # The probe already consumed this image. A fresh direct recognition
                # is an anchor, never run a second flow update on the same frame.
                if direct["status"] == "valid":
                    result = dict(
                        direct,
                        frame_index=index,
                        reference_frame=index,
                        age_s=0.0,
                        source="detected",
                        tracked_points=[],
                        motion_quality={},
                    )
                    self.anchor = self.last_recognition = index
                else:
                    result = dict(
                        direct,
                        frame_index=index,
                        reference_frame=None,
                        age_s=None,
                        tracked_points=[],
                        motion_quality={},
                    )
            else:
                result = super().update(frame, direct, index)
                if previous_state is not None:
                    temporal["status"] = "motion_disabled"
        else:
            result = super().update(frame, direct, index)
            if temporal["status"] not in {"camera_cut", "frame_gap"}:
                temporal.update(
                    status="propagated" if result["status"] == "valid" else "unavailable",
                    reason=result["status"],
                )

        result = attach_visible_field(result, (width, height))
        result.update(schema_version=3, temporal_quality=temporal)
        if result["status"] != "valid":
            self._reset()
            result.update(reference_frame=None, age_s=None, homography=None, source="unavailable")
        else:
            self.state = result
        self.last_index = index
        return result


def status_label(state):
    if state.get("status") != "valid":
        return "Veldpositie onbekend"
    return "Gevolgd met camerabeweging" if state.get("source") == "tracked" else "Opnieuw herkend"
