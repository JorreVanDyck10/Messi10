"""Team exports and immutable corrected runs, reusing exact observed geometry and IDs."""

from __future__ import annotations

import copy
import csv
import json
import shutil
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import cv2
import psutil

from .contracts import FrameRecord, PipelineError, RunResult, digest_json, read_json, sha256_file, write_json
from .participants import player_summary
from .render import render_frame
from .teams import (
    TEAM_IDS,
    TeamAssigner,
    TeamSamples,
    hex_rgb,
    load_team_settings,
    rgb_to_lab,
    team_context,
    validate_team_model,
)
from .tracking import Trajectories
from .video import VideoWriter, inspect_video


def fit_team_file(path: Path, settings: dict, fps: float) -> dict:
    samples = TeamSamples(settings, fps)
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            record = FrameRecord.from_dict(json.loads(line))
            for detection in record.detections:
                samples.add(detection, record.frame_index)
    return samples.fit()


def render_team_file(
    source: Path,
    directory: Path,
    manifest: dict,
    model: dict,
    overrides: dict | None = None,
    progress=None,
) -> dict:
    """Only decode, assign teams and render; never run detection, projection or tracking."""
    video = manifest["video"]
    path = Path(video["path"])
    if not path.is_file() or sha256_file(path) != video["sha256"]:
        raise PipelineError("De oorspronkelijke, ongewijzigde video is nodig voor teamweergave.")
    fps = video["fps_num"] / video["fps_den"]
    assigner = TeamAssigner(model, fps, overrides)
    histories = Trajectories(fps)
    capture = cv2.VideoCapture(str(path))
    writer = None
    count = 0
    peak_ram = psutil.Process().memory_info().rss
    started = time.perf_counter()
    counts = {"assigned": 0, "unknown": 0}
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "controlebeelden").mkdir(exist_ok=True)
    temporary_records = directory / "frames.team.partial.jsonl"
    try:
        writer = VideoWriter(directory / "video.partial.mp4", 1920, 720, video["fps_num"], video["fps_den"])
        with (
            source.open(encoding="utf-8") as stream,
            temporary_records.open("w", encoding="utf-8") as output,
            (directory / "teamtelling.csv").open("w", encoding="utf-8-sig", newline="") as csv_stream,
        ):
            table = csv.writer(csv_stream)
            table.writerow(
                ["frame_index", "timestamp_s", "status", "on_field", "team_A", "team_B", "unknown"]
            )
            for index, line in enumerate(stream):
                record = FrameRecord.from_dict(json.loads(line))
                if (
                    record.frame_index != index
                    or index >= video["frame_count"]
                    or record.image_size != (video["width"], video["height"])
                    or abs(record.timestamp_s - index / fps) > 1e-6
                ):
                    raise PipelineError("Teamuitvoer vereist de oorspronkelijke framevolgorde en tijdlijn.")
                ok, frame = capture.read()
                if not ok or frame.shape[:2] != (video["height"], video["width"]):
                    raise PipelineError(f"Decodeerfout bij teamweergave op frame {index}.")
                if record.tracking and record.tracking.get("reset_tracks"):
                    assigner.history.clear()
                assigner.update(record.detections, index)
                record.team_context = team_context(model)
                histories.update(record.detections, index)
                rendered = render_frame(
                    frame, record, histories, technical_pilot=manifest.get("technical_pilot", False)
                )
                writer.write(rendered)
                output.write(json.dumps(record.to_dict(), allow_nan=False) + "\n")
                summary = player_summary(record)
                table.writerow(
                    [
                        index,
                        record.timestamp_s,
                        summary["status"],
                        summary["on_field"],
                        *[summary["by_team"][k] for k in (*TEAM_IDS, "unknown")],
                    ]
                )
                for detection in record.detections:
                    if detection.semantic_class == "player":
                        counts["assigned" if detection.team_id else "unknown"] += 1
                if index in {0, video["frame_count"] // 2, video["frame_count"] - 1}:
                    if not cv2.imwrite(
                        str(directory / "controlebeelden" / f"frame_{index:06d}.jpg"), rendered
                    ):
                        raise PipelineError("Controlebeeld voor teams kan niet worden opgeslagen.")
                count += 1
                peak_ram = max(peak_ram, psutil.Process().memory_info().rss)
                if progress and (count % max(1, round(fps / 4)) == 0 or count == video["frame_count"]):
                    progress(count, video["frame_count"], time.perf_counter() - started)
            if count != video["frame_count"] or capture.read()[0]:
                raise PipelineError("Teamuitvoer heeft een afwijkend frameaantal.")
        writer.close()
        encoded = inspect_video(directory / "video.partial.mp4")
        if (
            encoded.frame_count != count
            or encoded.size != (1920, 720)
            or encoded.codec != "h264"
            or abs(encoded.fps - fps) > 1e-8
        ):
            raise PipelineError("Teamvideo heeft een afwijkend uitvoerformaat of tijdlijn.")
        temporary_records.replace(directory / "framegegevens.jsonl")
        (directory / "video.partial.mp4").replace(directory / "samengestelde_video.mp4")
        return {
            "runtime_s": time.perf_counter() - started,
            "observations": counts,
            "peak_process_ram_bytes_sampled": peak_ram,
            "model_status": model["status"],
        }
    finally:
        capture.release()
        if writer and not writer.closed:
            writer.close(abort=True)


def finish_teams(directory: Path, manifest: dict, progress=None) -> dict:
    started = time.perf_counter()
    settings = load_team_settings(manifest["team_settings"])
    source = directory / "framegegevens.jsonl"
    fps = manifest["video"]["fps_num"] / manifest["video"]["fps_den"]
    model = fit_team_file(source, settings, fps)
    write_json(directory / "teaminstellingen.json", model)
    write_json(
        directory / "teamcorrecties.json",
        {
            "schema_version": 1,
            "source_run_key": manifest["cache_key"],
            "video_sha256": manifest["video"]["sha256"],
            "teams": {},
            "track_overrides": {},
        },
    )
    measurement = render_team_file(source, directory, manifest, model, progress=progress)
    measurement["runtime_s"] = time.perf_counter() - started
    manifest["team_model_status"] = model["status"]
    manifest["team_origin"] = {"directory": str(directory.resolve()), "cache_key": manifest["cache_key"]}
    return measurement


def correction_origin(run_directory: Path) -> tuple[Path, dict]:
    from .pipeline import validate_completed

    current = validate_completed(run_directory)
    if current.get("team_settings") is None:
        raise PipelineError("Deze analyse bevat nog geen teamherkenning.")
    origin = current.get("team_origin", {"directory": str(run_directory), "cache_key": current["cache_key"]})
    directory = Path(origin["directory"])
    manifest = current if directory.resolve() == run_directory.resolve() else validate_completed(directory)
    if (
        manifest["cache_key"] != origin["cache_key"]
        or manifest["video"]["sha256"] != current["video"]["sha256"]
    ):
        raise PipelineError("Teamcorrecties horen bij een andere oorspronkelijke analyse.")
    return directory, manifest


def validate_corrections(
    corrections: dict, origin: dict, model: dict, track_ids: set[str]
) -> tuple[dict, dict]:
    if (
        corrections.get("schema_version") != 1
        or corrections.get("source_run_key") != origin["cache_key"]
        or corrections.get("video_sha256") != origin["video"]["sha256"]
        or set(corrections) - {"schema_version", "source_run_key", "video_sha256", "teams", "track_overrides"}
    ):
        raise PipelineError("Teamcorrecties horen niet bij deze oorspronkelijke analyse.")
    edits, overrides = corrections.get("teams", {}), corrections.get("track_overrides", {})
    if not isinstance(edits, dict) or not isinstance(overrides, dict) or set(edits) - set(TEAM_IDS):
        raise PipelineError("Ongeldige teamcorrecties.")
    if any(key not in track_ids or value not in (*TEAM_IDS, None) for key, value in overrides.items()):
        raise PipelineError("Teamcorrectie bevat een onbekende speler-ID of teamkoppeling.")
    updated = copy.deepcopy(model)
    for key, edit in edits.items():
        if not isinstance(edit, dict) or set(edit) - {"name", "shirt_color", "display_color"}:
            raise PipelineError("Ongeldige teaminstellingen in correctie.")
        updated["teams"][key].update(edit)
        if "shirt_color" in edit:
            updated["teams"][key]["prototype_lab"] = rgb_to_lab(hex_rgb(edit["shirt_color"]))
            # An explicit shirt-colour correction uses the supplied colour
            # prototypes, rather than silently retaining a different embedding.
            updated["settings"]["method"] = "torso_lab_dominant_modes_v1"
    validate_team_model(updated)
    prototypes = [team["prototype_lab"] for team in updated["teams"].values()]
    if updated["settings"]["method"] == "torso_lab_dominant_modes_v1" and all(p is not None for p in prototypes):
        import numpy as np

        separation = np.linalg.norm(np.array(prototypes[0]) - prototypes[1])
        updated["status"] = (
            "available" if separation >= updated["settings"]["min_separation"] else "ambiguous_colors"
        )
    return updated, overrides


def apply_team_corrections(
    run_directory: Path, corrections: dict, output_root: Path, progress=None
) -> RunResult:
    from .pipeline import code_identity, dependencies, processing_lock, validate_completed

    output_root = Path(output_root).resolve()
    with processing_lock(output_root):
        origin_directory, origin = correction_origin(Path(run_directory))
        model = read_json(origin_directory / "teaminstellingen.json")
        track_ids = set()
        with (origin_directory / "framegegevens.jsonl").open(encoding="utf-8") as stream:
            for line in stream:
                track_ids.update(
                    str(d["track_id"])
                    for d in json.loads(line)["detections"]
                    if d["semantic_class"] == "player" and d.get("track_id") is not None
                )
        model, overrides = validate_corrections(corrections, origin, model, track_ids)
        code, versions = code_identity(), dependencies()
        identity = {
            "kind": "team_correction_v1",
            "source_run_key": origin["cache_key"],
            "source_artifacts": origin["artifacts"],
            "corrections": corrections,
            "code": code,
            "dependencies": versions,
        }
        key = digest_json(identity)
        for candidate in sorted(output_root.glob(key + "*")):
            try:
                cached = validate_completed(candidate)
                if cached["cache_key"] == key:
                    return RunResult(candidate, cached, reused=True)
            except PipelineError:
                continue
        directory = output_root / key
        if directory.exists():
            directory = output_root / f"{key}-{uuid.uuid4().hex[:8]}"
        directory.mkdir()
        started = time.perf_counter()
        manifest = copy.deepcopy(origin)
        manifest.update(
            cache_key=key,
            status="running",
            code=code,
            dependencies=versions,
            started_at=datetime.now(UTC).isoformat(),
            team_origin={"directory": str(origin_directory.resolve()), "cache_key": origin["cache_key"]},
            derivation={
                "kind": "teams_only",
                "source_run_key": origin["cache_key"],
                "source_artifacts": origin["artifacts"],
                "corrections": corrections,
            },
        )
        manifest.pop("artifacts", None)
        manifest.pop("completed_at", None)
        manifest.pop("mvp_acceptance", None)
        write_json(directory / "runmanifest.json", manifest)
        try:
            for name in ("calibration.json", "observations.jsonl"):
                if (origin_directory / name).is_file():
                    shutil.copyfile(origin_directory / name, directory / name)
            write_json(directory / "teaminstellingen.json", model)
            write_json(directory / "teamcorrecties.json", corrections)
            measurement = render_team_file(
                origin_directory / "framegegevens.jsonl", directory, manifest, model, overrides, progress
            )
            elapsed = time.perf_counter() - started
            manifest["team_model_status"] = model["status"]
            manifest["measurements"] = {
                **origin["measurements"],
                "runtime_s": elapsed,
                "processing_fps": origin["video"]["frame_count"] / elapsed,
                "inference_or_replay_s": 0.0,
                "tracking_s": 0.0,
                "calibration_preparation_s": 0.0,
                "peak_process_ram_bytes_sampled": measurement["peak_process_ram_bytes_sampled"],
                "peak_gpu_allocated_bytes": None,
                "teams": measurement,
                "runtime_kind": "team_render_only",
            }
            manifest.update(
                status="completed",
                completed_at=datetime.now(UTC).isoformat(),
                artifacts={
                    str(p.relative_to(directory)): sha256_file(p)
                    for p in directory.rglob("*")
                    if p.is_file() and p.name != "runmanifest.json"
                },
            )
            write_json(directory / "runmanifest.json", manifest)
            return RunResult(directory, manifest)
        except Exception as exc:
            manifest.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            write_json(directory / "runmanifest.json", manifest)
            raise PipelineError(f"Teamcorrectie mislukt: {exc}. Details: {directory}") from exc
