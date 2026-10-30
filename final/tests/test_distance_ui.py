"""Distance inspection runs solely on saved positions and existing IDs."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

from streamlit.testing.v1 import AppTest

pytest_plugins = ["test_team_pipeline", "test_result_inspection"]


def result_app(result):
    app = AppTest.from_string(
        "import streamlit as st\nfrom football_pipeline.app_results import show_result\n"
        "show_result(st.session_state.saved)\n",
        default_timeout=30,
    )
    app.session_state["saved"] = result
    app.session_state["result_view"] = "Spelers en afstanden"
    return app.run()


def test_existing_tracks_show_distances_without_new_processing(team_run, monkeypatch):
    from football_pipeline import pipeline

    result, _ = team_run
    processing = Mock(side_effect=AssertionError("Distance inspection must not process video"))
    monkeypatch.setattr(pipeline, "process_video", processing)
    app = result_app(result)
    token = result.directory.name[:16]
    assert not app.exception
    before = app.dataframe[0].value
    assert "Geschatte afstand (m)" in before.columns
    assert set(before["Geschatte afstand (m)"]) <= {"0.0", "Niet beschikbaar"}
    assert not processing.called
    app.number_input(key=f"distance_length_{token}").set_value(100)
    next(b for b in app.button if b.label == "Afstanden bijwerken").click().run()
    assert not app.exception
    assert not processing.called


def test_an_analysis_without_tracking_does_not_get_made_up_player_distances(saved_run):
    app = result_app(saved_run)
    assert not app.exception
    assert any("geen tijdelijke speler-ID" in element.value for element in app.info)
    assert not app.dataframe


def test_field_dimensions_change_the_distance_but_not_the_saved_data(tmp_path):
    from football_pipeline.contracts import Detection, FrameRecord, sha256_file, write_json

    directory = tmp_path / ("a" * 64)
    directory.mkdir()
    records = []
    for i, position in enumerate(([0.1, 0.2], [0.13, 0.28])):
        records.append(
            FrameRecord(
                i,
                float(i),
                (100, 100),
                [
                    Detection(
                        f"{i}:0",
                        "test",
                        0,
                        "player",
                        [10, 10, 20, 40],
                        0.9,
                        track_id=7,
                        field_position=position,
                        projection_status="valid",
                    )
                ],
            ).to_dict()
        )
    path = directory / "framegegevens.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")
    write_json(
        directory / "calibration.json", {"review": {"field_dimensions_m": {"length": 100, "width": 50}}}
    )
    original = sha256_file(path)
    result = SimpleNamespace(
        directory=directory,
        manifest={
            "video": {"duration_s": 2, "fps_num": 1, "fps_den": 1},
            "artifacts": {"framegegevens.jsonl": original},
        },
    )
    app = AppTest.from_string(
        "import streamlit as st\nfrom football_pipeline.distance_ui import show_distances\n"
        "show_distances(st.session_state.saved)\n",
        default_timeout=20,
    )
    app.session_state["saved"] = result
    app.run()
    token = directory.name[:16]
    assert not app.exception
    assert app.number_input(key=f"distance_length_{token}").value == 100
    assert app.number_input(key=f"distance_width_{token}").value == 50
    assert float(app.dataframe[0].value.iloc[0]["Geschatte afstand (m)"]) == 5
    app.number_input(key=f"distance_length_{token}").set_value(120)
    app.number_input(key=f"distance_width_{token}").set_value(60)
    next(b for b in app.button if b.label == "Afstanden bijwerken").click().run()
    assert not app.exception
    assert float(app.dataframe[0].value.iloc[0]["Geschatte afstand (m)"]) == 6
    app.number_input(key=f"distance_speed_{token}").set_value(1)
    next(b for b in app.button if b.label == "Afstanden bijwerken").click().run()
    assert not app.exception
    assert set(app.dataframe[0].value["Geschatte afstand (m)"]) == {"Niet beschikbaar"}
    assert sha256_file(path) == original
