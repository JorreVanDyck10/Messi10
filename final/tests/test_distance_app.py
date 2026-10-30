"""The distance view reads existing records and never runs video inference."""

import json

import pytest
from streamlit.testing.v1 import AppTest
from test_distances import frame

from football_pipeline.contracts import RunResult, sha256_file, write_json
from football_pipeline.distance_ui import distance_tables
from football_pipeline.video import ROOT


@pytest.fixture
def observed_run(tmp_path):
    directory = tmp_path / ("a" * 64)
    directory.mkdir()
    records = directory / "framegegevens.jsonl"
    records.write_text(
        "\n".join(json.dumps(frame(i, 0.1 + i * 0.001).to_dict()) for i in range(11)), encoding="utf-8"
    )
    manifest = {
        "video": {"duration_s": 1.1, "frame_count": 11, "fps_num": 10, "fps_den": 1},
        "measurements": {},
        "artifacts": {"framegegevens.jsonl": sha256_file(records)},
    }
    return RunResult(directory, manifest, reused=True)


def result_view(result, view="Spelers en afstanden"):
    app = AppTest.from_string(
        "import streamlit as st\nfrom football_pipeline.app_results import show_result\n"
        "show_result(st.session_state.result)",
        default_timeout=30,
    )
    app.session_state.result = result
    app.session_state.result_view = view
    return app.run()


def test_distance_settings_filters_downloads_and_cache_do_not_modify_records(observed_run):
    original_hash = sha256_file(observed_run.directory / "framegegevens.jsonl")
    app = result_view(observed_run)
    assert not app.exception and not app.error
    assert app.dataframe[0].value.iloc[0]["Geschatte afstand (m)"] == "1.1"
    assert any(button.label == "Afstanden downloaden (CSV)" for button in app.get("download_button"))
    token = observed_run.directory.name[:16]
    app.number_input(key=f"distance_length_{token}").set_value(120.0)
    next(button for button in app.button if button.label == "Afstanden bijwerken").click().run()
    assert not app.exception and not app.error
    assert app.dataframe[0].value.iloc[0]["Geschatte afstand (m)"] == "1.2"
    assert app.session_state[f"distance_settings_{token}"]["length_m"] == 120
    app.selectbox(key=f"distance_team_{token}").set_value("B").run()
    assert not app.exception and app.dataframe[0].value.empty
    assert sha256_file(observed_run.directory / "framegegevens.jsonl") == original_hash
    settings = {"length_m": 105.0, "width_m": 68.0, "max_speed_m_s": 12.0, "step_s": 0.2}
    table, _ = distance_tables(str(observed_run.directory), original_hash, 1.1, settings)
    assert table.iloc[0].distance_m == pytest.approx(1.05)
    settings["length_m"] = 120.0
    table, _ = distance_tables(str(observed_run.directory), original_hash, 1.1, settings)
    assert table.iloc[0].distance_m == pytest.approx(1.2)


def test_missing_tracking_is_unavailable_and_empty_saved_list_is_actionable(
    observed_run, monkeypatch, tmp_path
):
    path = observed_run.directory / "framegegevens.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:
        row["detections"][0]["track_id"] = None
    path.write_text("\n".join(json.dumps(row) for row in rows))
    observed_run.manifest["artifacts"][path.name] = sha256_file(path)
    app = result_view(observed_run)
    assert not app.exception and not app.error
    assert any("geen tijdelijke speler-ID" in message.value for message in app.info)
    monkeypatch.setenv("FOOTBALL_RUNS", str(tmp_path / "empty"))
    app = AppTest.from_file(str(ROOT / "streamlit_app.py")).run()
    app.radio(key="workspace_view").set_value("Opgeslagen analyses").run()
    assert not app.exception
    assert any("Nog geen voltooide analyse" in message.value for message in app.info)


def test_recorded_dimensions_are_reused(observed_run):
    write_json(
        observed_run.directory / "calibration.json",
        {
            "review": {"field_dimensions_m": {"length": 120, "width": 80}},
        },
    )
    app = result_view(observed_run)
    assert not app.exception and not app.error
    assert app.dataframe[0].value.iloc[0]["Geschatte afstand (m)"] == "1.2"
    assert any("Vastgelegd bij de kalibratie" in caption.value for caption in app.caption)
