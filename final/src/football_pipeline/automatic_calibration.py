"""Content-addressed per-frame calibration; network inference lives in a separate process."""

from __future__ import annotations

import json
import re
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .contracts import Detection, PipelineError, VideoMetadata, digest_json, read_json, sha256_file
from .field_layout import COORDINATE_SYSTEM, LINES_UV, POINTS_UV, POLICY, UPSTREAM_REVISION, UPSTREAM_URL
from .geometry import valid_box


def transform(points, matrix):
    homogeneous = np.column_stack((np.asarray(points, dtype=float), np.ones(len(points)))) @ matrix.T
    denominator = homogeneous[:, 2]
    if (
        not np.isfinite(homogeneous).all()
        or (np.abs(denominator) < 1e-10).any()
        or not ((denominator > 0).all() or (denominator < 0).all())
    ):
        raise ValueError("Projection crosses the homography horizon")
    return homogeneous[:, :2] / homogeneous[:, 2:]


def estimate_frame(observation: dict, image_size) -> dict:
    """Recompute from semantic observations, never trust a saved matrix or confidence claim.

    Line consistency is a cross-model check, NOT independent human ground truth.
    No previous-frame state or extrapolation is used, including after cuts.
    """
    result = {"status": "insufficient_points", "homography": None, "quality": {}, "points": [], "lines": []}
    try:
        width, height = image_size
        diagonal = float(np.hypot(width, height))
        xy, uv = [], []
        seen = set()
        for point in observation["points"]:
            identifier = point["id"]
            if type(identifier) is not int or identifier in seen:
                raise ValueError("Duplicate or invalid semantic point ID")
            seen.add(identifier)
            values = np.asarray([point["x"], point["y"], point["confidence"]], dtype=float)
            if not np.isfinite(values).all() or not 0 <= values[2] <= 1:
                raise ValueError("Non-finite point or confidence")
            if identifier not in POINTS_UV or values[2] < POLICY["keypoint_threshold"]:
                continue
            if not (0 <= values[0] < width and 0 <= values[1] < height):
                raise ValueError("Point outside source pixels")
            xy.append(values[:2])
            uv.append(POINTS_UV[identifier])
            result["points"].append(point)
        line_ids = set()
        for line in observation["lines"]:
            identifier = line["id"]
            if type(identifier) is not int or identifier in line_ids:
                raise ValueError("Duplicate or invalid line ID")
            line_ids.add(identifier)
            coordinates = np.asarray(line["xy"], dtype=float)
            confidence = float(line["confidence"])
            if coordinates.shape != (2, 2) or not np.isfinite(coordinates).all() or not 0 <= confidence <= 1:
                raise ValueError("Invalid line endpoints")
            if identifier not in LINES_UV or confidence < POLICY["line_threshold"]:
                continue
            if (
                (coordinates < 0).any()
                or (coordinates[:, 0] >= width).any()
                or (coordinates[:, 1] >= height).any()
            ):
                raise ValueError("Line outside source pixels")
            result["lines"].append(line)
        result["quality"]["ground_points"] = len(xy)
        if len(xy) < POLICY["minimum_points"]:
            return result
        xy, uv = np.asarray(xy), np.asarray(uv)
        result["status"] = "degenerate_geometry"
        if (
            cv2.contourArea(cv2.convexHull(xy.astype(np.float32)))
            < width * height * POLICY["minimum_image_hull_fraction"]
        ):
            return result
        # Fit field -> image so RANSAC's error threshold is in original image pixels.
        cv2.setRNGSeed(0)
        inverse, mask = cv2.findHomography(uv, xy, cv2.RANSAC, diagonal * 0.005)
        if (
            inverse is None
            or not np.isfinite(inverse).all()
            or np.linalg.matrix_rank(inverse) != 3
            or np.linalg.cond(inverse) > 1e12
        ):
            return result
        inliers = mask.ravel().astype(bool)
        result["quality"]["inliers"] = int(inliers.sum())
        if inliers.sum() < POLICY["minimum_points"] or inliers.mean() < 0.7:
            result["status"] = "inconsistent_points"
            return result
        errors = np.linalg.norm(transform(uv[inliers], inverse) - xy[inliers], axis=1)
        result["quality"].update(median_px=float(np.median(errors)), maximum_px=float(errors.max()))
        if np.median(errors) > diagonal * 0.005 or errors.max() > diagonal * 0.01:
            result["status"] = "inconsistent_points"
            return result
        center = uv[inliers].mean(axis=0)
        probes = transform([center, center + [0.001, 0], center + [0, 0.001]], inverse)
        jacobian = np.column_stack((probes[1] - probes[0], probes[2] - probes[0]))
        if jacobian[0, 0] <= 0 or jacobian[1, 1] <= 0 or np.linalg.det(jacobian) <= 0:
            result["status"] = "orientation_unknown"
            return result
        line_errors, checked_lines = [], 0
        for line in result["lines"]:
            identifier = line["id"]
            coordinates = np.asarray(line["xy"], dtype=float)
            projected = transform(LINES_UV[identifier], inverse)
            vector = projected[1] - projected[0]
            length = np.linalg.norm(vector)
            if length < 1 or np.linalg.norm(coordinates[1] - coordinates[0]) < 5:
                continue
            delta = coordinates - projected[0]
            distance = np.abs(vector[0] * delta[:, 1] - vector[1] * delta[:, 0]) / length
            line_errors.extend(distance.tolist())
            checked_lines += 1
        result["quality"]["ground_lines"] = checked_lines
        if checked_lines < POLICY["minimum_lines"]:
            result["status"] = "insufficient_lines"
            return result
        result["quality"].update(
            line_median_px=float(np.median(line_errors)), line_maximum_px=float(max(line_errors))
        )
        if np.median(line_errors) > diagonal * 0.005 or max(line_errors) > diagonal * 0.01:
            result["status"] = "inconsistent_lines"
            return result
        matrix = np.linalg.inv(inverse)
        if not np.isfinite(matrix).all() or not np.isfinite(np.linalg.norm(matrix)):
            return result
        # A horizon inside the visible pitch makes even apparently small residuals unsafe.
        hull = cv2.convexHull(xy[inliers].astype(np.float32)).reshape(-1, 2)
        denominators = np.column_stack((hull, np.ones(len(hull)))) @ matrix[2]
        if not ((denominators > 1e-10).all() or (denominators < -1e-10).all()):
            return result
        matrix /= np.linalg.norm(matrix)
        result.update(status="valid", homography=matrix.tolist())
        return result
    except (KeyError, TypeError, ValueError, OverflowError, cv2.error, np.linalg.LinAlgError):
        result.update(status="invalid_observation", homography=None)
        return result


@dataclass
class AutomaticCalibration:
    manifest: dict
    observations_path: str
    profile: dict | None = None

    @property
    def settings(self):
        from .field_motion import DEFAULT_SETTINGS, validate_settings

        if self.profile is None and self.manifest.get("schema_version") == 1:
            return None
        settings = validate_settings({**DEFAULT_SETTINGS, **(self.profile or {})})
        if self.manifest.get("schema_version") == 1 and any(
            settings[name] < POLICY[name] for name in ("keypoint_threshold", "line_threshold")
        ):
            raise PipelineError(
                "Deze oude bundel bevat gefilterde scores; voer het veldmodel opnieuw uit voor een lagere confidence."
            )
        return settings

    @property
    def identity(self):
        identity = {"manifest": self.manifest, "policy": POLICY}
        if self.settings is not None:
            identity["settings"] = self.settings
            identity["implementation_sha256"] = {
                name: sha256_file(Path(__file__).with_name(name))
                for name in ("automatic_calibration.py", "field_motion.py")
            }
            if self.settings["version"] == 3:
                identity["implementation_sha256"]["field_bounds.py"] = sha256_file(
                    Path(__file__).with_name("field_bounds.py")
                )
        return digest_json(identity)

    def validate_for(self, video: VideoMetadata, approved=True):
        m = self.manifest
        upstream = m.get("upstream")
        if (
            m.get("schema_version") not in (1, 2)
            or m.get("kind") != "automatic_field_observations"
            or m.get("coordinate_system") != COORDINATE_SYSTEM
            or m.get("policy") != POLICY
            or not isinstance(upstream, dict)
            or upstream.get("revision") != UPSTREAM_REVISION
            or upstream.get("url") != UPSTREAM_URL
        ):
            raise PipelineError("Niet-ondersteund automatisch kalibratieformaat of modelversie.")
        if m["schema_version"] == 2 and m.get("score_storage") != "all_ground_peaks_before_threshold":
            raise PipelineError("Ruwe veldscores ontbreken in de nieuwe kalibratiebundel.")
        self.settings
        expected = {
            "sha256": video.sha256,
            "image_size": list(video.size),
            "frame_count": video.frame_count,
            "fps_num": video.fps_num,
            "fps_den": video.fps_den,
        }
        if m.get("video") != expected:
            raise PipelineError("Automatische kalibratie hoort bij een andere clip of tijdlijn.")
        if any(not isinstance(m.get(k), str) or not m[k].strip() for k in ("source", "usage")):
            raise PipelineError("Automatische kalibratie mist videobron en toegelaten gebruik.")
        if sha256_file(self.observations_path) != m.get("observations_sha256"):
            raise PipelineError("Automatische kalibratiegegevens gewijzigd of beschadigd.")
        models = m.get("models", {})
        if (
            not isinstance(models, dict)
            or set(models) != {"keypoints", "lines"}
            or any(
                not isinstance(spec, dict) or not re.fullmatch(r"[a-f0-9]{64}", str(spec.get("sha256", "")))
                for spec in models.values()
            )
        ):
            raise PipelineError("Automatische kalibratie mist modelidentiteit.")
        if (
            not re.fullmatch(r"[a-f0-9]{64}", str(m.get("worker_sha256", "")))
            or not isinstance(m.get("dependencies"), dict)
            or not m["dependencies"]
        ):
            raise PipelineError("Automatische kalibratie mist software-identiteit.")

    def frames(self, video):
        with Path(self.observations_path).open(encoding="utf-8") as stream:
            for index in range(video.frame_count):
                try:
                    row = json.loads(stream.readline())
                    if (
                        type(row["frame_index"]) is not int
                        or row["frame_index"] != index
                        or row["image_size"] != list(video.size)
                        or not np.isfinite(row["timestamp_s"])
                        or abs(row["timestamp_s"] - index / video.fps) > 1e-6
                    ):
                        raise ValueError("Afwijkende tijdlijn")
                    if self.manifest["schema_version"] == 2:
                        if {p["id"] for p in row["points"]} != set(POINTS_UV) or {
                            p["id"] for p in row["lines"]
                        } != set(LINES_UV):
                            raise ValueError("Ruwe bundel mist semantische punt- of lijnscores")
                        for point in row["points"]:
                            raw = float(point["raw_score"])
                            if not np.isfinite(raw) or point["confidence"] != min(1.0, max(0.0, raw)):
                                raise ValueError("Ruwe puntscore wijkt af van confidence")
                        for line in row["lines"]:
                            raw = np.asarray(line["raw_scores"], float)
                            if (
                                raw.shape != (2,)
                                or not np.isfinite(raw).all()
                                or line["confidence"] != min(1.0, max(0.0, float(raw.min())))
                            ):
                                raise ValueError("Ruwe lijnscores ontbreken of wijken af van confidence")
                    if self.settings is None:
                        state = estimate_frame(row, video.size)
                    else:
                        from .field_motion import estimate_checked

                        state = estimate_checked(row, video.size, self.settings)
                    state.update(frame_index=index, model_identity=self.identity)
                    yield state
                except (ValueError, TypeError, KeyError) as exc:
                    raise PipelineError(f"Ongeldig automatisch kalibratieframe {index}: {exc}") from exc
            if stream.readline():
                raise PipelineError("Automatische kalibratie bevat meer frames dan de video.")


def load_automatic_calibration(path):
    path = Path(path).resolve()
    manifest = read_json(path)
    profile = None
    # A saved processing run records its derived policy separately from the raw
    # observations. Restore that policy rather than silently replaying the default.
    run_path = path.with_name("runmanifest.json")
    if path.name == "calibration.json" and run_path.is_file():
        run = read_json(run_path)
        if run.get("calibration_mode") != "automatic" or run.get("video", {}).get("sha256") != manifest.get(
            "video", {}
        ).get("sha256"):
            raise PipelineError("Opgeslagen veldinstellingen horen bij een andere kalibratie.")
        profile = run.get("field_settings")
    return AutomaticCalibration(manifest, str(path.with_name("observations.jsonl")), profile)


def project_automatic(detection: Detection, state: dict, image_size):
    detection.field_position = None
    if not valid_box(detection, image_size):
        detection.projection_status = "invalid_box"
        return
    if state["status"] != "valid":
        detection.projection_status = "calibration_unavailable"
        return
    if detection.bbox_xyxy[3] >= image_size[1] - 1:
        detection.projection_status = "truncated_bottom"
        return
    x1, _, x2, y2 = detection.bbox_xyxy
    try:
        if "visible_field_polygon_xy" in state:
            from .field_bounds import contains_footpoint

            if not contains_footpoint(state["visible_field_polygon_xy"], ((x1 + x2) / 2, y2)):
                detection.projection_status = "outside_field"
                return
        uv = transform([[(x1 + x2) / 2, y2]], np.asarray(state["homography"]))[0]
    except (ValueError, TypeError, np.linalg.LinAlgError):
        detection.projection_status = "invalid_transform"
        return
    if (uv < 0).any() or (uv > 1).any():
        detection.projection_status = "outside_field"
        return
    detection.field_position, detection.projection_status = uv.tolist(), "valid"


def prepare_automatic_calibration(video_path, runtime_path, output_root, *, source, usage, progress=None):
    """Run the isolated worker with an argument array; only publish completed bundles."""
    from .pipeline import processing_lock
    from .video import ROOT, inspect_video

    video = inspect_video(video_path)
    if not source.strip() or not usage.strip():
        raise PipelineError("Vul videobron en toegelaten gebruik in voor automatische kalibratie.")
    runtime_path = Path(runtime_path).resolve()
    runtime = read_json(runtime_path)
    worker = ROOT / "scripts/field_calibration_worker.py"
    runtime_identity = {
        "config": runtime,
        "worker_sha256": sha256_file(worker),
        "adapter_files": {
            name: sha256_file(Path(__file__).with_name(name))
            for name in ("automatic_calibration.py", "field_layout.py", "field_model_spec.py")
        },
    }
    # Rehash executable, model weights and source tree before cache lookup.
    for name in ("python", "weights_keypoints", "weights_lines"):
        runtime_identity[name] = sha256_file(runtime[name])
    repo = Path(runtime["repository"])
    runtime_identity["upstream_files"] = {
        str(p.relative_to(repo)): sha256_file(p)
        for p in sorted(repo.rglob("*"))
        if p.is_file() and p.suffix in {".py", ".yaml"}
    }
    key = digest_json(
        {
            "runtime": runtime_identity,
            "video": video.sha256,
            "source": source,
            "usage": usage,
            "policy": POLICY,
        }
    )
    root = Path(output_root).resolve()
    with processing_lock(root):
        destination = root / key
        for candidate in sorted(root.glob(key + "*")):
            if not candidate.is_dir() or not (candidate / "automatic_calibration.json").is_file():
                continue
            try:
                existing = load_automatic_calibration(candidate / "automatic_calibration.json")
                existing.validate_for(video)
                return existing
            except (PipelineError, OSError):
                continue
        # Preserve failed/partial/damaged attempts, including their logs.
        if destination.exists():
            destination = root / f"{key}-{uuid.uuid4().hex[:8]}"
        destination.mkdir()
        arguments = [
            runtime["python"],
            str(worker),
            "--video",
            str(Path(video_path).resolve()),
            "--runtime",
            str(runtime_path),
            "--output",
            str(destination),
            "--source",
            source,
            "--usage",
            usage,
            "--fps-num",
            str(video.fps_num),
            "--fps-den",
            str(video.fps_den),
            "--frames",
            str(video.frame_count),
        ]
        started = time.perf_counter()
        log_path = destination / "worker.log"
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(arguments, stdout=log, stderr=subprocess.STDOUT, cwd=repo)
            last_reported = -1
            try:
                while process.poll() is None:
                    if progress:
                        matches = re.findall(rb"(\d+)/(\d+) frames", log_path.read_bytes())
                        completed = min(int(matches[-1][0]), video.frame_count) if matches else 0
                        if completed != last_reported:
                            progress(completed, video.frame_count, time.perf_counter() - started)
                            last_reported = completed
                    time.sleep(0.5)
            except BaseException:
                process.terminate()
                process.wait(timeout=30)
                raise
        if process.returncode:
            tail = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
            raise PipelineError(f"Veldmodel kon niet verwerken. Zie {log_path}\n{tail}")
        bundle = load_automatic_calibration(destination / "automatic_calibration.json")
        bundle.validate_for(video)
        if bundle.manifest["worker_sha256"] != runtime_identity["worker_sha256"]:
            raise PipelineError("Veldmodeladapter gewijzigd tijdens verwerking; voer opnieuw uit.")
        if progress:
            progress(video.frame_count, video.frame_count, time.perf_counter() - started)
        return bundle
