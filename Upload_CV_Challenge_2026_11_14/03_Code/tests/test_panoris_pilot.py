from copy import deepcopy

import cv2
import numpy as np
import pytest

from football_pipeline.contracts import PipelineError, read_json
from scripts import panoris_pilot


def pilot_config(video_metadata, calibration):
    return {
        "image_size": list(video_metadata.size),
        "points": deepcopy(calibration.points),
        "reference_frame": 0,
        "camera_patch_min_ncc": 0.8,
        "camera_patch_max_shift_px": 2,
        "temporal_anchor_names": [p["name"] for p in calibration.points],
        "point_selection": "synthetic test fixture",
    }


def pitch_frame():
    frame = np.zeros((360, 640, 3), np.uint8)
    cv2.rectangle(frame, (40, 40), (600, 320), (240, 240, 240), 2)
    cv2.line(frame, (320, 40), (320, 320), (240, 240, 240), 2)
    return frame


def test_static_geometry_passes_without_human_approval(video_metadata, calibration, tmp_path, monkeypatch):
    monkeypatch.setattr(panoris_pilot, "read_frame", lambda *args: pitch_frame())
    result, report = panoris_pilot.assess_geometry(
        video_metadata, pilot_config(video_metadata, calibration), tmp_path
    )
    assert report["technical_passed"] is True
    assert result.review["human_reviewed"] is False
    assert result.review["approved"] is False
    assert len(report["per_frame"]) == 3


def test_failed_geometry_is_recorded_without_correcting_points(video_metadata, calibration, tmp_path):
    config = pilot_config(video_metadata, calibration)
    config["points"][4]["x"] += 30
    with pytest.raises(PipelineError, match="controle faalt"):
        panoris_pilot.assess_geometry(video_metadata, config, tmp_path)
    report = read_json(tmp_path / "geometry-report.json")
    assert report["technical_passed"] is False
    assert report["points"] == config["points"]
    assert not (tmp_path / "calibration-technical.json").exists()


def test_camera_shift_stops_pilot(video_metadata, calibration, tmp_path, monkeypatch):
    frame = pitch_frame()
    monkeypatch.setattr(
        panoris_pilot, "read_frame", lambda video, index: frame if index == 0 else np.roll(frame, 3, axis=1)
    )
    with pytest.raises(PipelineError, match="cameracontrole faalt"):
        panoris_pilot.assess_geometry(video_metadata, pilot_config(video_metadata, calibration), tmp_path)
    assert read_json(tmp_path / "geometry-report.json")["camera_anchor_check_passed"] is False
