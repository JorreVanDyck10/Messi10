from __future__ import annotations

import contextlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import time
import uuid
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import cv2
import psutil

from .automatic_calibration import AutomaticCalibration, prepare_automatic_calibration, project_automatic
from .contracts import FrameRecord, PipelineError, RunResult, digest_json, read_json, sha256_file, write_json
from .detection import UltralyticsDetector, load_model_manifest
from .geometry import Calibration, project_detection, valid_box
from .render import render_frame
from .tracking import ByteTrackAdapter, Trajectories, load_tracker_config
from .video import ROOT, VideoWriter, inspect_video, tool_versions


def code_identity() -> dict:
    paths = sorted((ROOT / "src" / "football_pipeline").glob("*.py"))
    paths += [ROOT / "streamlit_app.py", ROOT / "pyproject.toml"]
    hashes = {str(p.relative_to(ROOT)): sha256_file(p) for p in paths if p.is_file()}
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    return {"git_commit": commit, "source_sha256": digest_json(hashes), "files": hashes}


def dependencies() -> dict:
    names = ("streamlit", "ultralytics", "torch", "torchvision", "opencv-python", "numpy", "psutil", "lap")
    return {name: importlib.metadata.version(name) for name in names}


@contextlib.contextmanager
def processing_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    lock = (root / ".processing.lock").open("a+b")
    locked = False
    try:
        lock.seek(0, 2)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except OSError as exc:
            raise PipelineError(
                "Er draait al een verwerking in deze uitvoermap. Wacht tot die klaar is."
            ) from exc
        yield
    finally:
        if locked:
            lock.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()


def validate_completed(directory: Path) -> dict:
    manifest = read_json(directory / "runmanifest.json")
    if manifest.get("status") != "completed":
        raise PipelineError("Uitvoering is niet volledig geslaagd.")
    required = {"samengestelde_video.mp4", "framegegevens.jsonl", "calibration.json"}
    if manifest.get("calibration_mode") == "automatic":
        required.add("observations.jsonl")
    artifacts = manifest.get("artifacts", {})
    if not required.issubset(artifacts):
        raise PipelineError("Runmanifest mist verplichte uitvoerbestanden.")
    for name, expected in artifacts.items():
        path = directory / name
        if Path(name).is_absolute() or ".." in Path(name).parts or not path.is_file():
            raise PipelineError("Ongeldige of ontbrekende uitvoer in runmanifest.")
        if sha256_file(path) != expected:
            raise PipelineError(f"Uitvoer gewijzigd of beschadigd: {name}.")
    return manifest


def accept_mvp(directory: Path, reviewer: str, confirmed: bool) -> Path:
    manifest = validate_completed(directory)
    if not confirmed or not reviewer.strip() or manifest.get("tracker_config") is not None:
        raise PipelineError(
            "Accepteer een MVP zonder tracking met reviewer en expliciete controlebevestiging."
        )
    if manifest.get("evidence_kind") != "ultralytics" or (
        manifest.get("calibration_mode") == "automatic" and manifest.get("field_evidence_kind") != "pnlcalib"
    ):
        raise PipelineError(
            "Synthetische, aangepaste of technische pilotuitvoer is geen echte MVP-acceptatie."
        )
    record = {
        "schema_version": 1,
        "human_accepted": True,
        "reviewer": reviewer.strip(),
        "accepted_at": datetime.now(UTC).isoformat(),
        "run_directory": str(directory.resolve()),
        "cache_key": manifest["cache_key"],
        "checks": ["geometry", "synchronization_start_middle_end", "playback", "empty_frames", "runtime"],
    }
    destination = directory / "mvp_acceptance.json"
    write_json(destination, record)
    return destination


def check_mvp_acceptance(
    path: Path | None,
    video_hash: str,
    calibration: Calibration | AutomaticCalibration,
    model_manifest: dict,
    code: dict,
    versions: dict,
) -> dict:
    if path is None:
        raise PipelineError("Tracking vereist eerst een gecontroleerde MVP-run; zie accept-mvp.")
    acceptance = read_json(path)
    if acceptance.get("human_accepted") is not True or not str(acceptance.get("reviewer", "")).strip():
        raise PipelineError("Geen geldige menselijke MVP-acceptatie.")
    manifest = validate_completed(Path(acceptance["run_directory"]))
    if (
        manifest.get("tracker_config") is not None
        or manifest.get("evidence_kind") != "ultralytics"
        or manifest.get("cache_key") != acceptance.get("cache_key")
        or manifest["video"]["sha256"] != video_hash
        or manifest["calibration_id"] != calibration.identity
        or manifest["models"] != model_manifest
        or manifest["code"] != code
        or manifest["dependencies"] != versions
    ):
        raise PipelineError(
            "MVP-acceptatie hoort niet bij deze video, kalibratie, modellen, code of omgeving."
        )
    return acceptance


def process_video(
    video_path: str | Path,
    calibration: Calibration | AutomaticCalibration | None,
    model_manifest_path: str | Path,
    output_root: str | Path,
    *,
    tracker_config_path: str | Path | None = None,
    mvp_acceptance_path: str | Path | None = None,
    progress: Callable | None = None,
    field_progress: Callable | None = None,
    detector=None,
    replay_run: str | Path | None = None,
    technical_pilot: bool = False,
    field_runtime_path: str | Path | None = None,
    field_source: str = "",
    field_usage: str = "",
    field_settings: dict | None = None,
    recalibrate_replay: bool = False,
) -> RunResult:
    """Process sequentially; injected detectors are explicitly marked as non-model evidence."""
    output_root = Path(output_root).resolve()
    with processing_lock(output_root):
        video = inspect_video(video_path)
        preparation_started = time.perf_counter()
        if calibration is None:
            if field_runtime_path is None:
                raise PipelineError("Kies handmatige kalibratie of configureer het automatische veldmodel.")
            if tracker_config_path or technical_pilot:
                raise PipelineError(
                    "Automatische kalibratie ondersteunt geen tracking of statische technische pilot."
                )
            calibration = prepare_automatic_calibration(
                video_path,
                field_runtime_path,
                output_root / "field-calibration",
                source=field_source,
                usage=field_usage,
                progress=field_progress,
            )
        elif field_runtime_path is not None:
            raise PipelineError(
                "Kies één kalibratiebron; combineer geen kalibratie met een veldmodelruntime."
            )
        automatic = isinstance(calibration, AutomaticCalibration)
        if field_settings is not None:
            if not automatic:
                raise PipelineError("Veldinstellingen vereisen automatische kalibratie.")
            calibration = AutomaticCalibration(
                calibration.manifest, calibration.observations_path, field_settings
            )
        if recalibrate_replay and (not replay_run or not automatic):
            raise PipelineError("Herkalibratie vereist een detectiereplay en automatische kalibratie.")
        if automatic and (tracker_config_path or technical_pilot):
            raise PipelineError(
                "Automatische kalibratie ondersteunt geen tracking of statische technische pilot."
            )
        preparation_s = time.perf_counter() - preparation_started
        if technical_pilot and (tracker_config_path or replay_run):
            raise PipelineError("Een technische pilot gebruikt nieuwe detecties zonder tracking of replay.")
        calibration.validate_for(video, approved=not technical_pilot)
        if technical_pilot and not (
            calibration.review.get("kind") == "agent_technical"
            and calibration.review.get("technical_passed") is True
            and calibration.review.get("approved") is False
            and calibration.review.get("human_reviewed") is False
            and calibration.review.get("static_camera_technical_check") is True
            and calibration.review.get("temporal_frames")
            == [0, video.frame_count // 2, video.frame_count - 1]
        ):
            raise PipelineError(
                "Technische pilot vereist een expliciete technische kalibratiecontrole zonder menselijke goedkeuring."
            )
        models = load_model_manifest(model_manifest_path)
        versions, code, tools = dependencies(), code_identity(), tool_versions()
        config = load_tracker_config(tracker_config_path) if tracker_config_path else None
        acceptance = None
        if config:
            player_models = [s for s in models["models"] if "player" in s["class_mapping"].values()]
            if not player_models:
                raise PipelineError("Spelertracking vereist expliciete player-klassen; person volstaat niet.")
            if any(s["confidence"] > min(0.10, config["track_low_thresh"]) for s in player_models):
                raise PipelineError("Detectorconfidence verwijdert lage kandidaten vóór ByteTrack.")
            acceptance = check_mvp_acceptance(
                Path(mvp_acceptance_path) if mvp_acceptance_path else None,
                video.sha256,
                calibration,
                models,
                code,
                versions,
            )
        replay_manifest = None
        if replay_run:
            replay_manifest = validate_completed(Path(replay_run))
            if (
                replay_manifest["video"]["sha256"] != video.sha256
                or replay_manifest["models"] != models
                or replay_manifest.get("evidence_kind") != "ultralytics"
            ):
                raise PipelineError("Replay vereist echte detecties van dezelfde video en modelinstellingen.")
            if (
                not recalibrate_replay
                and (automatic or replay_manifest.get("calibration_mode") == "automatic")
                and (replay_manifest.get("calibration_id") != calibration.identity)
            ):
                raise PipelineError("Automatische replay vereist dezelfde framekalibraties.")
            if detector is not None:
                raise PipelineError("Replay en aangepaste detector kunnen niet tegelijk.")
        evidence = "ultralytics" if detector is None else getattr(detector, "evidence_kind", "custom")
        if technical_pilot:
            evidence += "_technical_pilot"
        provenance = getattr(detector, "provenance", {}) if detector else {}
        identity = {
            "video_sha256": video.sha256,
            "calibration_id": calibration.identity,
            "models": models,
            "tracker_config": config,
            "code": code,
            "dependencies": versions,
            "tools": tools,
            "evidence_kind": evidence,
            "technical_pilot": technical_pilot,
            "field_evidence_kind": calibration.manifest.get("evidence_kind", "unverified")
            if automatic
            else None,
            "custom_provenance": provenance,
            "acceptance": acceptance,
            "replay_hash": (replay_manifest or {}).get("artifacts", {}).get("framegegevens.jsonl"),
            "recalibrate_replay": recalibrate_replay,
        }
        key = digest_json(identity)
        for candidate in sorted(output_root.glob(key + "*")):
            if not candidate.is_dir():
                continue
            try:
                previous = validate_completed(candidate)
                if previous.get("cache_key") == key:
                    return RunResult(candidate, previous, reused=True)
            except PipelineError:
                continue
        directory = output_root / key
        if directory.exists():
            directory = output_root / f"{key}-{uuid.uuid4().hex[:8]}"
        directory.mkdir()
        (directory / "controlebeelden").mkdir()
        manifest = {
            "schema_version": 3 if automatic and calibration.settings is not None else 2 if automatic else 1,
            "field_settings": calibration.settings if automatic else None,
            "recalibrate_replay": recalibrate_replay,
            "calibration_mode": "automatic" if automatic else "manual",
            "cache_key": key,
            "status": "running",
            "started_at": datetime.now(UTC).isoformat(),
            "video": asdict(video),
            "calibration_id": calibration.identity,
            "models": models,
            "code": code,
            "dependencies": versions,
            "tools": tools,
            "tracker_config": config,
            "mvp_acceptance": acceptance,
            "evidence_kind": evidence,
            "technical_pilot": technical_pilot,
            "custom_provenance": provenance,
            "replayed_from": str(replay_run) if replay_run else None,
            "field_evidence_kind": calibration.manifest.get("evidence_kind", "unverified")
            if automatic
            else None,
        }
        write_json(directory / "runmanifest.json", manifest)
        write_json(directory / "calibration.json", calibration.manifest if automatic else asdict(calibration))
        if automatic:
            shutil.copyfile(calibration.observations_path, directory / "observations.jsonl")
        capture, writer, replay_stream = None, None, None
        count, rejected = 0, Counter()
        calibration_counts = Counter()
        started, inference_time, tracking_time = time.perf_counter(), 0.0, 0.0
        process = psutil.Process()
        peak_ram = process.memory_info().rss
        gpu_peak = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
            if not replay_run and detector is None:
                detector = UltralyticsDetector(models)
            if replay_run:
                replay_stream = (Path(replay_run) / "framegegevens.jsonl").open(encoding="utf-8")
            tracker = ByteTrackAdapter(config, video.fps) if config else None
            histories = Trajectories(video.fps) if tracker else None
            if tracker:
                manifest["tracker_effective"] = tracker.info
            writer = VideoWriter(directory / "video.partial.mp4", 1920, 720, video.fps_num, video.fps_den)
            capture = cv2.VideoCapture(video.path)
            frame_calibrations = calibration.frames(video) if automatic else None
            from .field_motion import CameraCalibration

            camera = (
                CameraCalibration(video.fps, calibration.settings)
                if automatic and calibration.settings
                else None
            )
            with (directory / "framegegevens.jsonl").open("w", encoding="utf-8") as records:
                for index in range(video.frame_count):
                    ok, frame = capture.read()
                    if not ok or frame.shape[:2] != (video.height, video.width):
                        raise PipelineError(f"Decodeerfout bij bronframe {index}; uitvoer onvolledig.")
                    tick = time.perf_counter()
                    if replay_stream:
                        from .replay import replay_detections

                        detections = replay_detections(replay_stream, index, video)
                    else:
                        detections = detector.detect(frame, index)
                    inference_time += time.perf_counter() - tick
                    frame_calibration = next(frame_calibrations) if automatic else None
                    if camera:
                        frame_calibration = camera.update(frame, frame_calibration, index)
                    if automatic:
                        calibration_counts[frame_calibration["status"]] += 1
                    if tracker:
                        tick = time.perf_counter()
                        tracker.update(detections, index, video.size)
                        tracking_time += time.perf_counter() - tick
                    for detection in detections:
                        if not valid_box(detection, video.size):
                            detection.bbox_xyxy = []  # JSON has no NaN/Infinity; preserve rejection, not invalid numbers.
                            detection.confidence = 0.0
                        if detection.semantic_class in {"player", "referee", "person"}:
                            if automatic:
                                project_automatic(detection, frame_calibration, video.size)
                            else:
                                project_detection(detection, calibration)
                        else:
                            detection.field_position = None
                            detection.projection_status = "not_ground_projected"
                        rejected[detection.projection_status] += 1
                    record = FrameRecord(index, index / video.fps, video.size, detections, frame_calibration)
                    if histories:
                        histories.update(detections, index)
                    rendered = render_frame(frame, record, histories, technical_pilot=technical_pilot)
                    writer.write(rendered)
                    records.write(json.dumps(record.to_dict(), allow_nan=False) + "\n")
                    if index in {0, video.frame_count // 2, video.frame_count - 1}:
                        target = directory / "controlebeelden" / f"frame_{index:06d}.jpg"
                        if not cv2.imwrite(str(target), rendered):
                            raise PipelineError("Controlebeeld kan niet worden opgeslagen.")
                    count += 1
                    peak_ram = max(peak_ram, process.memory_info().rss)
                    if progress and (index % max(1, round(video.fps / 4)) == 0 or count == video.frame_count):
                        progress(count, video.frame_count, time.perf_counter() - started + preparation_s)
                if capture.read()[0]:
                    raise PipelineError("Decoder leverde meer frames dan de gecontroleerde tijdlijn.")
                if replay_stream and replay_stream.readline():
                    raise PipelineError("Replay bevat meer frames dan de bronvideo.")
                if automatic:
                    # Exhaust the generator so trailing calibration records cannot pass validation.
                    if next(frame_calibrations, None) is not None:
                        raise PipelineError("Automatische kalibratie bevat extra frames.")
            writer.close()
            encoded = inspect_video(directory / "video.partial.mp4")
            if (
                encoded.frame_count != video.frame_count
                or encoded.size != (1920, 720)
                or encoded.codec != "h264"
                or abs(encoded.fps - video.fps) > 1e-8
            ):
                raise PipelineError("Uitvoer voldoet niet aan frameaantal, resolutie, codec of framerate.")
            (directory / "video.partial.mp4").replace(directory / "samengestelde_video.mp4")
            if torch.cuda.is_available():
                gpu_peak = torch.cuda.max_memory_allocated()
            artifacts = [p for p in directory.rglob("*") if p.is_file() and p.name != "runmanifest.json"]
            manifest.update(
                status="completed",
                completed_at=datetime.now(UTC).isoformat(),
                artifacts={str(p.relative_to(directory)): sha256_file(p) for p in artifacts},
            )
        except Exception as exc:
            manifest.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            raise PipelineError(
                f"Verwerking mislukt: {exc}. Details: {directory / 'runmanifest.json'}"
            ) from exc
        finally:
            if capture:
                capture.release()
            if replay_stream:
                replay_stream.close()
            if automatic and "frame_calibrations" in locals() and frame_calibrations is not None:
                frame_calibrations.close()
            if writer and not writer.closed:
                writer.close(abort=True)
            elapsed = time.perf_counter() - started
            manifest["measurements"] = {
                "processed_frames": count,
                "runtime_s": elapsed + preparation_s,
                "processing_fps": count / (elapsed + preparation_s) if elapsed + preparation_s else 0,
                "inference_or_replay_s": inference_time,
                "tracking_s": tracking_time,
                "peak_process_ram_bytes_sampled": peak_ram,
                "peak_gpu_allocated_bytes": gpu_peak,
                "projection_counts": dict(rejected),
                "calibration_preparation_s": preparation_s,
                "calibration_status_counts": dict(calibration_counts),
                "calibration_usable_fraction": calibration_counts["valid"] / count
                if automatic and count
                else None,
            }
            write_json(directory / "runmanifest.json", manifest)
        return RunResult(directory, manifest)
