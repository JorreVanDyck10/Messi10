"""Saved results remain useful without source footage or model weights."""

import json

import pytest
from streamlit.testing.v1 import AppTest

from football_pipeline.app_results import linked_result, saved_analyses
from football_pipeline.contracts import PipelineError, RunResult, write_json
from football_pipeline.demo import SyntheticDetector
from football_pipeline.pipeline import process_video
from football_pipeline.result_inspection import position_table, record_offsets, saved_record
from football_pipeline.video import ROOT


@pytest.fixture
def saved_run(demo_fixture, tmp_path):
    return process_video(
        demo_fixture["video"],
        demo_fixture["calibration"],
        demo_fixture["models"],
        tmp_path / "runs",
        detector=SyntheticDetector(),
    )


def test_completed_results_are_listed_and_collision_suffix_links_open(saved_run):
    original = saved_run.directory
    renamed = original.with_name(original.name + "-a12bc345")
    original.rename(renamed)
    root = renamed.parent
    incomplete = root / ("b" * 64)
    incomplete.mkdir()
    write_json(incomplete / "runmanifest.json", {"status": "running"})
    broken = root / ("c" * 64)
    broken.mkdir()
    (broken / "runmanifest.json").write_text("broken")
    items = saved_analyses(root)
    assert [item["directory"] for item in items] == [renamed]
    assert "Handmatig" in items[0]["label"]
    result = linked_result(root, renamed.name)
    assert result.reused and result.directory == renamed
    (renamed / "framegegevens.jsonl").write_text("tampered")
    with pytest.raises(PipelineError, match="gewijzigd of beschadigd"):
        linked_result(root, renamed.name)


@pytest.mark.parametrize(
    "identifier", ["a" * 64 + "-../file", "a" * 64 + "-123456789", "a" * 64 + "-ZZZZZZZZ"]
)
def test_collision_suffix_does_not_allow_arbitrary_paths(tmp_path, identifier):
    with pytest.raises(PipelineError, match="analyselink"):
        linked_result(tmp_path, identifier)


def test_indexed_records_keep_empty_frames_and_reject_wrong_order(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text(
        "\n".join(json.dumps({"frame_index": i, "detections": [], "timestamp_s": i / 25}) for i in range(3))
        + "\n",
        encoding="utf-8",
    )
    stat = path.stat()
    offsets = record_offsets(str(path), stat.st_size, stat.st_mtime_ns)
    assert saved_record(path, 2, offsets)["timestamp_s"] == 0.08
    assert position_table(saved_record(path, 1, offsets)).empty
    with pytest.raises(PipelineError):
        saved_record(path, -1, offsets)
    path.write_text('{"frame_index":99,"detections":[]}\n', encoding="utf-8")
    with pytest.raises(PipelineError, match="Framevolgorde"):
        saved_record(path, 0, [0])


def test_unavailable_positions_stay_empty_in_the_export():
    row = {
        "frame_index": 4,
        "timestamp_s": 0.16,
        "detections": [
            {
                "detection_id": "4:0",
                "semantic_class": "player",
                "confidence": 0.8,
                "field_position": [0.3, 0.4],
                "projection_status": "field_unknown",
                "counted_as_player": False,
            },
            {
                "detection_id": "4:1",
                "semantic_class": "player",
                "confidence": 0.9,
                "field_position": [0.7, 0.8],
                "projection_status": "valid",
                "counted_as_player": True,
            },
        ],
    }
    table = position_table(row)
    assert table.loc[0, ["u", "v"]].isna().all()
    assert table.loc[1, "u"] == 0.7
    assert list(table["Telt als speler"]) == ["Nee", "Ja"]
    assert list(table["Frame"]) == [4, 4]


def test_frame_view_uses_saved_video_after_the_source_has_been_removed(saved_run, tmp_path):
    # Read-only viewing must not depend on a usable model or on the original footage.
    manifest = dict(saved_run.manifest)
    manifest["video"] = {**manifest["video"], "path": str(tmp_path / "missing.mp4")}
    app = AppTest.from_string(
        "from football_pipeline.app_results import show_result\n"
        "import streamlit as st\nshow_result(st.session_state.saved)\n",
        default_timeout=30,
    )
    app.session_state["saved"] = RunResult(saved_run.directory, manifest)
    app.run()
    assert not app.exception
    token = saved_run.directory.name
    app.checkbox(key=f"inspect_frame_{token}").check().run()
    assert not app.exception
    app.slider(key=f"inspect_index_{token}").set_value(8).run()
    assert not app.exception
    assert any("geen detecties" in item.value for item in app.info)
    assert next(m.value for m in app.metric if m.label == "Spelers op het veld in dit frame") == "0"
    app.slider(key=f"inspect_index_{token}").set_value(9).run()
    assert not app.exception
    assert app.dataframe[0].value.iloc[0]["Frame"] == 9


def test_school_history_opens_without_upload_or_new_processing(saved_run, monkeypatch):
    from unittest.mock import Mock

    from football_pipeline import pipeline

    process = Mock(side_effect=AssertionError("Opening history must not process a video"))
    monkeypatch.setattr(pipeline, "process_video", process)
    monkeypatch.setenv("FOOTBALL_SCHOOL_MODE", "1")
    monkeypatch.setenv("FOOTBALL_RUNS", str(saved_run.directory.parent))
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    app.session_state["result"] = "active-upload-result"
    app.run()
    app.radio(key="workspace_view").set_value("Opgeslagen analyses").run()
    assert not app.exception
    assert not process.called
    assert app.session_state["result"].directory == saved_run.directory
    assert app.get("video")


def test_history_sorts_real_times_and_puts_unknown_dates_last(tmp_path):
    timestamps = {
        "a": "2026-10-28T10:00:00+02:00",
        "b": "2026-10-28T09:00:00+00:00",
        "c": "unknown",
        "d": "2026-10-28T08:30:00",
    }
    for letter, timestamp in timestamps.items():
        directory = tmp_path / (letter * 64)
        directory.mkdir()
        write_json(directory / "runmanifest.json", {"status": "completed", "completed_at": timestamp})
    items = saved_analyses(tmp_path)
    assert [item["directory"].name[0] for item in items] == ["b", "d", "a", "c"]
    assert "09:00 UTC" in items[0]["label"]
    assert "08:00 UTC" in items[2]["label"]
    assert "Datum onbekend" in items[3]["label"]


@pytest.mark.parametrize(
    "position",
    [[float("nan"), 0.5], [0.5, float("inf")], [-0.1, 0.5], [0.5, 1.1], [True, 0.5], ["0.2", 0.5], None],
)
def test_invalid_coordinates_are_not_exported_as_field_positions(position):
    record = {
        "frame_index": 0,
        "timestamp_s": 0,
        "detections": [
            {"field_position": position, "projection_status": "valid"},
        ],
    }
    table = position_table(record)
    assert table.loc[0, ["u", "v"]].isna().all()
    assert table.loc[0, "Veldpositie"] == "Ongeldige coördinaten"


@pytest.mark.parametrize(
    "invalid",
    [
        {"frame_index": False},
        {"timestamp_s": float("nan")},
        {"timestamp_s": -0.1},
        {"timestamp_s": True},
        {"detections": [None]},
    ],
)
def test_broken_frame_metadata_produces_a_readable_error(tmp_path, invalid):
    record = {"frame_index": 0, "timestamp_s": 0, "detections": [], **invalid}
    path = tmp_path / "records.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(PipelineError, match="framegegevens kunnen niet worden gelezen"):
        saved_record(path, 0, [0])
