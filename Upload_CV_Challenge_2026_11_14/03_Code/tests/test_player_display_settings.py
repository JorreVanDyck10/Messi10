import json
from dataclasses import replace

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from football_pipeline.contracts import Detection, FrameRecord, PipelineError
from football_pipeline.demo import SyntheticDetector
from football_pipeline.participants import (
    counted_as_player,
    player_display_policy,
    player_summary,
    visible_in_record,
)
from football_pipeline.pipeline import process_video
from football_pipeline.render import render_frame
from football_pipeline.tracking import ByteTrackAdapter, load_tracker_config
from football_pipeline.video import ROOT


@pytest.mark.parametrize("track_id", [None, 7])
@pytest.mark.parametrize("confidence,expected", [(0.499, False), (0.5, True), (0.501, True)])
def test_strict_boundary_shared_by_render_counts_exports_and_roundtrip(track_id, confidence, expected):
    player = Detection(
        "p",
        "test",
        0,
        "player",
        [100, 100, 140, 180],
        confidence,
        track_id=track_id,
        field_position=[0.4, 0.5],
        projection_status="valid",
    )
    ball = Detection("b", "andrew", 0, "ball", [300, 200, 310, 210], 0.4)
    record = FrameRecord(
        0,
        0,
        (640, 360),
        [player, ball],
        analysis_scope="on_pitch_players",
        player_policy=player_display_policy(0.5),
    )
    assert counted_as_player(record, player) == expected
    assert visible_in_record(record, ball)
    serialized = record.to_dict()
    assert serialized["player_summary"]["on_field"] == int(expected)
    assert serialized["diagnostics"]["displayed_players"] == int(expected)
    assert serialized["detections"][0]["counted_as_player"] == expected
    assert FrameRecord.from_dict(serialized).to_dict() == serialized
    canvas = render_frame(np.zeros((360, 640, 3), np.uint8), record)
    without_player = render_frame(np.zeros((360, 640, 3), np.uint8), replace(record, detections=[ball]))
    assert np.array_equal(canvas, without_player) == (not expected)


def test_original_behavior_is_preserved_and_restorable_without_losing_evidence():
    d = Detection(
        "p",
        "test",
        0,
        "player",
        [100, 100, 140, 180],
        0.15,
        track_id=7,
        field_position=[0.4, 0.5],
        projection_status="valid",
    )
    original = FrameRecord(0, 0, (640, 360), [d])
    strict = replace(original, player_policy=player_display_policy(0.25))
    assert player_summary(original)["on_field"] == 1
    assert player_summary(strict)["on_field"] == 0
    assert len(strict.to_dict()["detections"]) == 1
    restored = replace(strict, player_policy=player_display_policy())
    assert player_summary(restored) == player_summary(original)
    assert "player_policy" not in original.to_dict()


@pytest.mark.parametrize("invalid", [True, -0.01, 1.01, float("nan"), float("inf")])
def test_invalid_threshold_fails_before_processing(invalid):
    with pytest.raises(PipelineError, match="spelersdrempel"):
        player_display_policy(invalid)


def test_filtering_does_not_modify_low_score_tracking():
    config = load_tracker_config(ROOT / "configs/bytetrack.yaml")
    outcomes = []
    for threshold in (None, 0.25, 0.9):
        tracker = ByteTrackAdapter(config, 25)
        ids, counts = [], []
        for index, confidence in enumerate((0.95, 0.15, 0.95)):
            d = Detection(
                str(index),
                "test",
                0,
                "player",
                [100, 100, 140, 180],
                confidence,
                field_position=[0.4, 0.5],
                projection_status="valid",
            )
            tracker.update([d], index, (640, 360))
            record = FrameRecord(
                index, index / 25, (640, 360), [d], player_policy=player_display_policy(threshold)
            )
            ids.append(d.track_id)
            counts.append(player_summary(record)["on_field"])
        outcomes.append((ids, counts))
    assert all(ids == [1, 1, 1] for ids, _ in outcomes)
    assert outcomes[0][1] == [1, 1, 1]
    assert outcomes[1][1] == outcomes[2][1] == [1, 0, 1]


def test_threshold_run_cache_and_default_restore(demo_fixture, tmp_path):
    args = (demo_fixture["video"], demo_fixture["calibration"], demo_fixture["models"], tmp_path)
    original = process_video(*args, detector=SyntheticDetector())
    strict = process_video(*args, detector=SyntheticDetector(), player_display_confidence=0.9)
    assert original.directory != strict.directory
    assert strict.manifest["player_policy"] == player_display_policy(0.9)
    restored = process_video(*args, detector=SyntheticDetector())
    assert restored.reused and restored.directory == original.directory
    rows = [json.loads(line) for line in (strict.directory / "framegegevens.jsonl").read_text().splitlines()]
    assert all(row["player_summary"]["display_confidence"] == 0.9 for row in rows)


def test_ui_change_and_restore_keep_model_and_tracker_files_unchanged():
    def script():
        from football_pipeline.player_controls_ui import player_controls
        from football_pipeline.video import ROOT

        player_controls({"models": []}, ROOT / "configs/bytetrack.yaml", 25, True)

    paths = [ROOT / "configs/models-broadcast.json", ROOT / "configs/bytetrack.yaml"]
    before = [p.read_bytes() for p in paths]
    app = AppTest.from_function(script, default_timeout=20).run()
    assert not app.exception
    assert app.session_state.player_display_original
    app.slider(key="player_display_confidence").set_value(0.65).run()
    assert not app.session_state.player_display_original
    assert any("Aangepaste" in c.value for c in app.caption)
    app.button(key="restore_player_display").click().run()
    assert not app.exception
    assert app.slider(key="player_display_confidence").value == 0.25
    assert app.session_state.player_display_original
    assert [p.read_bytes() for p in paths] == before


def test_automatic_upload_waits_for_process_after_threshold_change(model_manifest, tmp_path, monkeypatch):
    from football_pipeline import automatic_analysis_ui
    from football_pipeline.contracts import write_json

    profile, manifest = model_manifest
    weights = manifest["models"][0]["weights"]
    runtime = tmp_path / "runtime.json"
    write_json(runtime, {"weights_keypoints": weights, "weights_lines": weights})
    monkeypatch.setenv("FOOTBALL_AUTO_MODELS", str(profile))
    monkeypatch.setenv("FOOTBALL_FIELD_RUNTIME", str(runtime))
    calls = []

    def fake_process(*args, **kwargs):
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(automatic_analysis_ui, "process_video", fake_process)
    monkeypatch.setattr(automatic_analysis_ui, "show_result", lambda result: None)

    def script():
        from types import SimpleNamespace

        from football_pipeline.automatic_analysis_ui import automatic_analysis
        from football_pipeline.video import ROOT

        automatic_analysis(
            SimpleNamespace(fps=25, sha256="fixture", path="fixture.mp4"), "fixture.mp4", ROOT / "runs"
        )

    app = AppTest.from_function(script, default_timeout=30).run()
    assert not app.exception and len(calls) == 1
    assert calls[0]["player_display_confidence"] is None
    app.slider(key="player_display_confidence").set_value(0.65).run()
    assert not app.exception and len(calls) == 1
    assert "result" not in app.session_state
    app.button(key="automatic_process").click().run()
    assert len(calls) == 2 and calls[-1]["player_display_confidence"] == 0.65
    app.button(key="restore_player_display").click().run()
    assert len(calls) == 2
    app.button(key="automatic_process").click().run()
    assert not app.exception and len(calls) == 3
    assert calls[-1]["player_display_confidence"] is None
