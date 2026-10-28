"""Exercise the school workflow through rendering, even with stale advanced settings."""

import json
from dataclasses import asdict
from types import SimpleNamespace
from unittest.mock import Mock

import streamlit as st
from streamlit.testing.v1 import AppTest

from football_pipeline.video import ROOT


def test_school_run_uses_manual_calibration_without_tracking_or_teams(demo_fixture, tmp_path, monkeypatch):
    from football_pipeline import pipeline, training_status_ui
    from football_pipeline.demo import SyntheticDetector

    real_process = pipeline.process_video
    process = Mock(side_effect=lambda *a, **kw: real_process(*a, **kw, detector=SyntheticDetector()))
    dashboard = Mock(side_effect=AssertionError("School mode must not open the training dashboard"))
    monkeypatch.setattr(pipeline, "process_video", process)
    monkeypatch.setattr(training_status_ui, "show_training_status", dashboard)
    monkeypatch.setenv("FOOTBALL_SCHOOL_MODE", "1")
    monkeypatch.setenv("FOOTBALL_MODELS", str(demo_fixture["models"]))
    monkeypatch.setenv("FOOTBALL_CALIBRATION_MODE", "automatic")
    monkeypatch.setenv("FOOTBALL_RUNS", str(tmp_path / "runs"))
    video_bytes = demo_fixture["video"].read_bytes()
    calibration_bytes = json.dumps(asdict(demo_fixture["calibration"])).encode()
    uploads = {
        "video_upload": SimpleNamespace(file_id="school", getbuffer=lambda: video_bytes),
        "calibration_upload": SimpleNamespace(getvalue=lambda: calibration_bytes),
    }
    monkeypatch.setattr(st, "file_uploader", lambda *a, **kw: uploads.get(kw["key"]))
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    for key in ("automatic_analysis", "open_team_result", "open_field_review", "tracking", "teams_enabled"):
        app.session_state[key] = True
    app.session_state["calibration_mode"] = "Automatische veldkalibratie"
    app.run()
    assert not app.exception
    assert process.call_count == 0
    assert not dashboard.called
    assert not any(item.key in {"tracking", "teams_enabled", "open_team_result", "open_field_review"}
                   for item in app.checkbox)
    assert len(app.selectbox(key="model_profile").options) == 1
    app.button(key="process").click().run()
    assert not app.exception
    assert process.call_count == 1
    kwargs = process.call_args.kwargs
    assert kwargs["tracker_config_path"] is None
    assert kwargs["team_config_path"] is None
    assert kwargs["field_runtime_path"] is None
    assert app.session_state["result"].manifest["status"] == "completed"
    app.run()
    assert not app.exception
    assert process.call_count == 1


def test_switching_the_visible_field_region_discards_the_previous_calibration(demo_fixture, monkeypatch):
    from football_pipeline.video import inspect_video

    monkeypatch.setenv("FOOTBALL_SCHOOL_MODE", "1")
    monkeypatch.setenv("FOOTBALL_MODELS", str(demo_fixture["models"]))
    video_bytes = demo_fixture["video"].read_bytes()
    monkeypatch.setattr(st, "file_uploader", lambda *a, **kw: (
        SimpleNamespace(file_id="partial-field", getbuffer=lambda: video_bytes)
        if kw["key"] == "video_upload" else None
    ))

    def populate_points(frame, **kwargs):
        return frame.assign(x=40 + frame.u * 560, y=40 + frame.v * 280)

    monkeypatch.setattr(st, "data_editor", populate_points)
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    app.run()
    assert not app.exception
    video = inspect_video(demo_fixture["video"])
    radio_key = f"point_layout_{video.sha256}"
    app.radio(key=radio_key).set_value("Strafschopgebied links").run()
    assert not app.exception
    app.button(key="calculate").click().run()
    assert not app.exception
    fit = [p for p in app.session_state["draft_calibration"].points if p["role"] == "fit"]
    assert max(p["u"] for p in fit) < 0.2
    app.radio(key=radio_key).set_value("Strafschopgebied rechts").run()
    assert not app.exception
    assert "draft_calibration" not in app.session_state
    assert "calibration" not in app.session_state
    assert "result" not in app.session_state
    latest = app.session_state[f"point_latest_{video.sha256}"]
    assert min(p["u"] for p in latest[:4]) > 0.8
