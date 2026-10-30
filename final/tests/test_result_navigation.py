"""Exercise leaving an old result before returning to an active upload or link."""

from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from football_pipeline.contracts import write_json
from football_pipeline.video import ROOT


def test_reopening_a_link_does_not_show_the_last_uploaded_result(tmp_path, monkeypatch):
    from football_pipeline import app_results

    identifier = "a" * 64
    expected = SimpleNamespace(directory=tmp_path / identifier)
    displayed, loaded = [], []

    def load(root, name):
        loaded.append(name)
        return expected

    monkeypatch.setattr(app_results, "linked_result", load)
    monkeypatch.setattr(app_results, "show_result", displayed.append)
    monkeypatch.setenv("FOOTBALL_SCHOOL_MODE", "1")
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    app.query_params["run"] = identifier
    app.run()
    assert not app.exception
    assert displayed[-1] is expected
    app.query_params.clear()
    app.session_state["result_request_signature"] = "previous-request"
    app.run()
    assert not app.exception
    assert "result" not in app.session_state
    assert "result_request_signature" not in app.session_state
    app.session_state["result"] = SimpleNamespace(directory=tmp_path / ("b" * 64))
    app.query_params["run"] = identifier
    app.run()
    assert not app.exception
    assert displayed[-1] is expected
    assert loaded == [identifier, identifier]


def test_reopening_team_history_does_not_show_a_different_active_result(tmp_path, monkeypatch):
    from football_pipeline import app_results, pipeline, training_status_ui

    directory = tmp_path / ("a" * 64)
    directory.mkdir()
    manifest = {
        "status": "completed",
        "completed_at": "2026-10-28T08:00:00+00:00",
        "team_settings": {},
        "video": {"path": "fixture.mp4"},
    }
    write_json(directory / "runmanifest.json", manifest)
    monkeypatch.setattr(pipeline, "validate_completed", lambda path: manifest)
    monkeypatch.setattr(training_status_ui, "show_training_status", lambda *args, **kwargs: None)
    displayed = []
    monkeypatch.setattr(app_results, "show_result", displayed.append)
    monkeypatch.setenv("FOOTBALL_SCHOOL_MODE", "0")
    monkeypatch.setenv("FOOTBALL_RUNS", str(tmp_path))
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    app.run()
    app.radio(key="workspace_view").set_value("Opgeslagen analyses").run()
    assert not app.exception
    assert displayed[-1].directory == directory
    app.session_state["result_request_signature"] = "previous-request"
    app.radio(key="workspace_view").set_value("Nieuwe analyse").run()
    assert not app.exception
    assert "result" not in app.session_state
    assert "result_request_signature" not in app.session_state
    app.session_state["result"] = SimpleNamespace(directory=tmp_path / ("b" * 64))
    app.radio(key="workspace_view").set_value("Opgeslagen analyses").run()
    assert not app.exception
    assert displayed[-1].directory == directory
