from dataclasses import asdict
from types import SimpleNamespace

import streamlit as st
from streamlit.testing.v1 import AppTest

from football_pipeline.video import ROOT


def test_app_initial_screen_and_rerun():
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=20).run()
    assert not app.exception
    assert app.title[0].value == "Van voetbalbeeld naar veldpositie"
    app.run()
    assert not app.exception
    assert "result" not in app.session_state


def test_preloaded_calibration_processes_once_on_explicit_click(demo_fixture, tmp_path, monkeypatch):
    import json
    from unittest.mock import Mock

    from football_pipeline import pipeline
    from football_pipeline.demo import SyntheticDetector

    # Real renderer/encoder/processing, synthetic detector explicitly marked in its runmanifest.
    real_process = pipeline.process_video
    calls = Mock(side_effect=lambda *a, **kw: real_process(*a, **kw, detector=SyntheticDetector()))
    monkeypatch.setattr(pipeline, "process_video", calls)
    monkeypatch.setenv("FOOTBALL_MODELS", str(demo_fixture["models"]))
    monkeypatch.setenv("FOOTBALL_RUNS", str(tmp_path / "runs"))
    video_bytes = demo_fixture["video"].read_bytes()
    calibration_bytes = json.dumps(asdict(demo_fixture["calibration"])).encode()
    video_upload = SimpleNamespace(file_id="demo-video", getbuffer=lambda: video_bytes)
    calibration_upload = SimpleNamespace(getvalue=lambda: calibration_bytes)

    def upload(label, **kwargs):
        return {"video_upload": video_upload, "calibration_upload": calibration_upload}.get(kwargs["key"])

    monkeypatch.setattr(st, "file_uploader", upload)
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    assert calls.call_count == 0
    app.button(key="process").click().run()
    assert not app.exception
    assert calls.call_count == 1
    assert app.session_state["result"].manifest["status"] == "completed"
    app.run()
    assert not app.exception
    assert calls.call_count == 1
    app.checkbox(key="tracking").check().run()
    assert not app.exception
    assert "result" not in app.session_state
    assert calls.call_count == 1


def test_point_table_calculation_review_and_invalidation(demo_fixture, monkeypatch):
    from copy import deepcopy
    from unittest.mock import Mock

    import pandas as pd

    from football_pipeline import pipeline

    calls = Mock()
    monkeypatch.setattr(pipeline, "process_video", calls)
    monkeypatch.setenv("FOOTBALL_MODELS", str(demo_fixture["models"]))
    content = demo_fixture["video"].read_bytes()
    upload = SimpleNamespace(file_id="calibration-workflow", getbuffer=lambda: content)
    monkeypatch.setattr(st, "file_uploader", lambda *a, **kw: upload if kw["key"] == "video_upload" else None)
    points = deepcopy(demo_fixture["calibration"].points)
    monkeypatch.setattr(st, "data_editor", lambda *a, **kw: pd.DataFrame(points))
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=20).run()
    assert not app.exception
    app.button(key="calculate").click().run()
    assert not app.exception
    app.text_input[0].set_value("Reviewer")
    app.text_input[1].set_value("Generated test frames")
    app.text_input[2].set_value("Engineering test")
    app.checkbox[0].check()
    next(b for b in app.button if b.label == "Kalibratie goedkeuren").click().run()
    assert not app.exception
    assert app.session_state["calibration"].review["reviewer"] == "Reviewer"
    assert calls.call_count == 0
    points[0]["x"] += 10
    app.run()
    assert not app.exception
    assert "calibration" not in app.session_state
    assert calls.call_count == 0
