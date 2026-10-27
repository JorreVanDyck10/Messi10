import json

import pandas as pd
from streamlit.testing.v1 import AppTest

from football_pipeline.contracts import read_json
from football_pipeline.video import ROOT

pytest_plugins = ["test_team_pipeline"]


def result_app(result):
    app = AppTest.from_string(
        "import streamlit as st\n"
        "from football_pipeline.app_results import show_result\n"
        "show_result(st.session_state.result)\n",
        default_timeout=30,
    )
    app.session_state["result"] = result
    return app.run()


def test_frame_counts_and_corrections_only_apply_on_submit(team_run):
    result, _ = team_run
    app = result_app(result)
    token = result.manifest["cache_key"][:16]
    assert not app.exception
    app.slider(key=f"team_frame_{token}").set_value(7).run()
    assert not app.exception
    values = {metric.label: metric.value for metric in app.metric}
    assert values["Totaal"] == "7" and values["Onbekend"] == "1"
    assert sorted([values["Team A"], values["Team B"]]) == ["3", "3"]
    app.text_input(key=f"team_name_A_{token}").set_value("Thuis").run()
    assert not app.exception
    assert app.session_state["result"].directory == result.directory
    assert read_json(result.directory / "teaminstellingen.json")["teams"]["A"]["name"] == "Team A"
    goal_id = json.loads((result.directory / "framegegevens.jsonl").read_text().splitlines()[7])[
        "detections"
    ][6]["track_id"]
    app.selectbox(key=f"team_track_{token}").select(str(goal_id))
    app.selectbox(key=f"team_override_{token}").select("A")
    next(button for button in app.button if button.label == "Correcties toepassen").click().run()
    assert not app.exception
    corrected = app.session_state["result"]
    assert corrected.directory != result.directory
    assert read_json(corrected.directory / "teaminstellingen.json")["teams"]["A"]["name"] == "Thuis"
    assert read_json(corrected.directory / "teamcorrecties.json")["track_overrides"] == {str(goal_id): "A"}
    app.run()
    assert not app.exception
    assert app.session_state["result"].directory == corrected.directory


def test_app_can_open_saved_result_without_upload_and_keeps_original_visible(team_run, monkeypatch):
    result, _ = team_run
    monkeypatch.setenv("FOOTBALL_RUNS", str(result.directory.parent))
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    app.checkbox(key="open_team_result").check().run()
    assert not app.exception
    assert app.session_state["result"].directory == result.directory
    token = result.manifest["cache_key"][:16]
    app.text_input(key=f"team_name_A_{token}").set_value("Nieuwe naam")
    next(button for button in app.button if button.label == "Correcties toepassen").click().run()
    assert not app.exception
    corrected = app.session_state["result"]
    assert corrected.directory != result.directory
    # The saved-run selection can explicitly reopen its original even though the
    # correction shares the same origin key.
    app.selectbox(key="saved_team_run").select_index(1).run()
    assert not app.exception
    assert app.session_state["result"].directory == result.directory


def test_chart_has_separate_segments_across_field_dropout(team_run, monkeypatch):
    from football_pipeline import team_ui

    result, _ = team_run
    captured = []
    monkeypatch.setattr(team_ui.st, "altair_chart", lambda chart: captured.append(chart))
    table = pd.DataFrame(
        [
            {"timestamp_s": 0, "total": 2, "A": 1, "B": 1, "unknown": 0},
            {"timestamp_s": 1, "total": None, "A": None, "B": None, "unknown": None},
            {"timestamp_s": 2, "total": 2, "A": 1, "B": 1, "unknown": 0},
        ]
    )
    team_ui.count_chart(table, read_json(result.directory / "teaminstellingen.json"))
    rows = captured[0].data.to_dict("records")
    assert {row["Segment"] for row in rows if row["Tijd (s)"] == 0} == {"A:0", "B:0", "unknown:0"}
    assert {row["Segment"] for row in rows if row["Tijd (s)"] == 2} == {"A:1", "B:1", "unknown:1"}


def test_old_result_still_uses_shared_downloads_without_team_controls(demo_fixture, tmp_path):
    from football_pipeline.demo import SyntheticDetector
    from football_pipeline.pipeline import process_video

    result = process_video(
        demo_fixture["video"],
        demo_fixture["calibration"],
        demo_fixture["models"],
        tmp_path / "runs",
        detector=SyntheticDetector(),
    )
    app = result_app(result)
    assert not app.exception
    assert not app.slider
    assert not app.text_input
