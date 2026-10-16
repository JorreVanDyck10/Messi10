from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

import cv2
import numpy as np

from .contracts import PipelineError, VideoMetadata, sha256_file

ROOT = Path(__file__).resolve().parents[2]


def find_tool(name: str) -> str:
    explicit = os.environ.get(f"FOOTBALL_{name.upper()}")
    if explicit and Path(explicit).is_file():
        return explicit
    resolved = shutil.which(name)
    if resolved:
        return resolved
    candidates = sorted((ROOT / ".tools").glob(f"**/{name}.exe"))
    if candidates:
        return str(candidates[0])
    raise PipelineError(f"{name} ontbreekt. Installeer FFmpeg/ffprobe of voer scripts/setup_tools.ps1 uit.")


def probe_json(path: Path, *, frames: bool = False) -> dict:
    entries = (
        "stream=width,height,r_frame_rate,codec_name,time_base:stream_tags=rotate:stream_side_data=rotation"
    )
    if frames:
        entries += ":frame=best_effort_timestamp,width,height"
    cmd = [find_tool("ffprobe"), "-v", "error", "-select_streams", "v:0"]
    if frames:
        cmd += ["-show_frames"]
    cmd += ["-show_entries", entries, "-of", "json", str(path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=180)
        if result.returncode or result.stderr.strip():
            raise PipelineError(f"Video kan niet betrouwbaar gelezen worden: {result.stderr[-1500:]}")
        return json.loads(result.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        raise PipelineError(f"Videocontrole mislukt: {exc}") from exc


def inspect_video(path: str | Path) -> VideoMetadata:
    path = Path(path).resolve()
    if path.suffix.lower() != ".mp4" or not path.is_file():
        raise PipelineError("Kies een bestaand .mp4-bestand.")
    payload = probe_json(path, frames=True)
    streams = payload.get("streams", [])
    frames = payload.get("frames", [])
    if not streams or len(frames) < 2:
        raise PipelineError("Video moet minstens twee leesbare frames bevatten.")
    stream = streams[0]
    try:
        width, height = int(stream["width"]), int(stream["height"])
        fps = Fraction(stream["r_frame_rate"])
        time_base = Fraction(stream["time_base"])
        if fps <= 0 or fps > 240 or width <= 0 or height <= 0:
            raise PipelineError("Ongeldige resolutie of framerate.")
        rotation = float(stream.get("tags", {}).get("rotate", 0))
        rotation += sum(float(x.get("rotation", 0)) for x in stream.get("side_data_list", []))
        if rotation % 360:
            raise PipelineError(
                "Video met rotatiemetadata niet ondersteund; normaliseer eerst de oriëntatie."
            )
        expected = 1 / fps
        previous = None
        tolerance = max(float(time_base) * 1.1, float(expected) * 0.001)
        if tolerance >= float(expected) * 0.1:
            raise PipelineError("Tijdsbasis is te grof om constante framerate te verifiëren.")
        for frame in frames:
            if (int(frame["width"]), int(frame["height"])) != (width, height):
                raise PipelineError("Beeldformaat verandert binnen de clip.")
            timestamp = int(frame["best_effort_timestamp"]) * time_base
            if previous is not None and abs(float(timestamp - previous - expected)) > tolerance:
                raise PipelineError("Variabele framerate of ontbrekende frames: kies een CFR-clip.")
            previous = timestamp
    except (KeyError, ValueError, ZeroDivisionError, TypeError) as exc:
        raise PipelineError(f"Onvolledige of ongeldige videometadata: {exc}") from exc
    return VideoMetadata(
        str(path),
        sha256_file(path),
        width,
        height,
        fps.numerator,
        fps.denominator,
        len(frames),
        stream["codec_name"],
        float(len(frames) / fps),
    )


def read_frame(video: VideoMetadata, frame_index: int) -> np.ndarray:
    if not 0 <= frame_index < video.frame_count:
        raise PipelineError("Frame-index ligt buiten de clip.")
    cap = cv2.VideoCapture(video.path)
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()
        if not ok or frame.shape[:2] != (video.height, video.width):
            raise PipelineError(f"Frame {frame_index} kan niet gelezen worden.")
        return frame
    finally:
        cap.release()


def tool_versions() -> dict:
    return {
        name: subprocess.check_output([find_tool(name), "-version"], text=True).splitlines()[0]
        for name in ("ffmpeg", "ffprobe")
    }


class VideoWriter:
    """Stream BGR frames to FFmpeg; stderr goes to disk to avoid pipe deadlocks."""

    def __init__(self, path: Path, width: int, height: int, fps_num: int, fps_den: int):
        self.path, self.size = path, (width, height)
        self.error_log = tempfile.TemporaryFile()
        self.closed = False
        self.count = 0
        command = [
            find_tool("ffmpeg"),
            "-v",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{width}x{height}",
            "-r",
            f"{fps_num}/{fps_den}",
            "-i",
            "pipe:0",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(path),
        ]
        try:
            self.process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=self.error_log
            )
        except OSError as exc:
            self.error_log.close()
            raise PipelineError(f"FFmpeg kan niet starten: {exc}") from exc

    def write(self, frame: np.ndarray) -> None:
        if frame.shape != (self.size[1], self.size[0], 3) or frame.dtype != np.uint8:
            raise PipelineError("Verkeerd uitvoerframeformaat.")
        try:
            self.process.stdin.write(np.ascontiguousarray(frame).tobytes())
            self.count += 1
        except (BrokenPipeError, OSError) as exc:
            raise PipelineError(
                "FFmpeg stopte tijdens schrijven; controleer encoder en schijfruimte."
            ) from exc

    def close(self, abort: bool = False) -> None:
        if self.closed:
            return
        self.closed = True
        try:
            try:
                self.process.stdin.close()
            except OSError:
                pass
            if abort:
                self.process.kill()
            try:
                code = self.process.wait(timeout=60)
            except subprocess.TimeoutExpired as exc:
                self.process.kill()
                self.process.wait()
                raise PipelineError("FFmpeg reageert niet bij afsluiten.") from exc
            self.error_log.seek(0)
            error = self.error_log.read().decode(errors="replace")
            if not abort and (code or not self.path.is_file() or not self.path.stat().st_size):
                raise PipelineError(f"H.264-uitvoer mislukt: {error[-2000:]}")
        finally:
            self.error_log.close()
