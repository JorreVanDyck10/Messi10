import pytest

from football_pipeline import video
from football_pipeline.contracts import PipelineError


def payload(timestamps):
    return {
        "streams": [
            {"width": 640, "height": 360, "r_frame_rate": "25/1", "time_base": "1/1000", "codec_name": "h264"}
        ],
        "frames": [{"width": 640, "height": 360, "best_effort_timestamp": t} for t in timestamps],
    }


def test_variable_framerate_rejected_even_if_nominal_rate_is_25(tmp_path, monkeypatch):
    path = tmp_path / "vfr.mp4"
    path.write_bytes(b"metadata fixture")
    monkeypatch.setattr(video, "probe_json", lambda *a, **k: payload([0, 40, 110, 150]))
    with pytest.raises(PipelineError, match="Variabele framerate"):
        video.inspect_video(path)


def test_frame_size_change_rejected(tmp_path, monkeypatch):
    path = tmp_path / "changed.mp4"
    path.write_bytes(b"metadata fixture")
    metadata = payload([0, 40, 80])
    metadata["frames"][1]["width"] = 1280
    monkeypatch.setattr(video, "probe_json", lambda *a, **k: metadata)
    with pytest.raises(PipelineError, match="Beeldformaat verandert"):
        video.inspect_video(path)
