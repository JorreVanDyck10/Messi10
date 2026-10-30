import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from football_pipeline.automatic_calibration import (
    AutomaticCalibration,
    estimate_frame,
    load_automatic_calibration,
    project_automatic,
    transform,
)
from football_pipeline.contracts import Detection, PipelineError, sha256_file, write_json
from football_pipeline.demo import SyntheticDetector
from football_pipeline.field_layout import (
    COORDINATE_SYSTEM,
    LINES_UV,
    POINTS_UV,
    POLICY,
    UPSTREAM_REVISION,
    UPSTREAM_URL,
)
from football_pipeline.pipeline import process_video, validate_completed
from football_pipeline.video import ROOT, inspect_video


def observation(index=0, inverse=None):
    inverse = np.asarray(inverse if inverse is not None else [[560, 0, 40], [0, 280, 40], [0, 0, 1]], float)
    # No four outside corners: a partial view has enough interior semantic landmarks.
    ids = [5, 6, 9, 10, 21, 22, 25, 26, 45, 51, 57]
    pixels = transform([POINTS_UV[i] for i in ids], inverse)
    return {
        "frame_index": index,
        "timestamp_s": index / 10,
        "image_size": [640, 360],
        "points": [
            {"id": i, "x": float(p[0]), "y": float(p[1]), "confidence": 0.95}
            for i, p in zip(ids, pixels)
            if 0 <= p[0] < 640 and 0 <= p[1] < 360
        ],
        "lines": [
            {"id": i, "xy": transform(LINES_UV[i], inverse).tolist(), "confidence": 0.95}
            for i in [2, 5, 13]
            if (transform(LINES_UV[i], inverse) >= 0).all()
            and (transform(LINES_UV[i], inverse) < [640, 360]).all()
        ],
    }


def bundle_for(video, directory, rows=None):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "observations.jsonl"
    rows = rows if rows is not None else [observation(i) for i in range(video.frame_count)]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "kind": "automatic_field_observations",
        "coordinate_system": COORDINATE_SYSTEM,
        "video": {
            "sha256": video.sha256,
            "image_size": list(video.size),
            "frame_count": video.frame_count,
            "fps_num": video.fps_num,
            "fps_den": video.fps_den,
        },
        "policy": POLICY,
        "upstream": {"url": UPSTREAM_URL, "revision": UPSTREAM_REVISION},
        "observations_sha256": sha256_file(path),
        "source": "generated",
        "usage": "engineering test",
        "models": {k: {"sha256": "a" * 64} for k in ("keypoints", "lines")},
        "worker_sha256": "b" * 64,
        "dependencies": {"fixture": "synthetic"},
    }
    write_json(directory / "automatic_calibration.json", manifest)
    return AutomaticCalibration(manifest, str(path))


def test_pan_zoom_and_missing_corners_use_current_frame_transform():
    for inverse in [
        np.array([[560, 0, 40], [0, 280, 40], [0, 0, 1.0]]),
        np.array([[595, 12, 15], [2, 300, 15], [0.03, 0.01, 1.0]]),
    ]:
        state = estimate_frame(observation(inverse=inverse), (640, 360))
        assert state["status"] == "valid"
        target = [0.4, 0.5]
        pixel = transform([target], inverse)[0]
        d = Detection(
            "0:0", "player", 0, "player", [pixel[0] - 5, pixel[1] - 20, pixel[0] + 5, pixel[1]], 0.9
        )
        project_automatic(d, state, (640, 360))
        assert d.field_position == pytest.approx(target, abs=1e-5)


@pytest.mark.parametrize(
    "condition,expected",
    [
        ("empty", "insufficient_points"),
        ("no_lines", "insufficient_lines"),
        ("bad_lines", "inconsistent_lines"),
        ("nan", "invalid_observation"),
        ("duplicate", "invalid_observation"),
        ("collinear", "degenerate_geometry"),
        ("mirrored", "orientation_unknown"),
    ],
)
def test_unreliable_frames_have_no_matrix(condition, expected):
    row = observation()
    if condition == "empty":
        row["points"] = []
    elif condition == "no_lines":
        row["lines"] = []
    elif condition == "bad_lines":
        row["lines"][0]["xy"][0][0] += 30
    elif condition == "nan":
        row["points"][0]["x"] = float("nan")
    elif condition == "duplicate":
        row["points"].append(row["points"][0])
    elif condition == "collinear":
        for point in row["points"]:
            point["y"] = 50
    elif condition == "mirrored":
        row = observation(inverse=[[-560, 0, 600], [0, 280, 40], [0, 0, 1]])
    state = estimate_frame(row, (640, 360))
    assert state["status"] == expected
    assert state["homography"] is None


def test_above_ground_points_never_enter_fit():
    row = observation()
    row["points"].extend({"id": i, "x": 10, "y": 10, "confidence": 0.99} for i in [12, 15, 16, 19])
    assert estimate_frame(row, (640, 360)) == estimate_frame(observation(), (640, 360))


@pytest.mark.parametrize(
    "box,expected",
    [
        ([90, 80, 110, 360], "truncated_bottom"),
        ([5, 100, 15, 150], "outside_field"),
        ([0, 0, float("nan"), 100], "invalid_box"),
    ],
)
def test_automatic_projection_rejects_truncated_outside_and_invalid_boxes(box, expected):
    state = estimate_frame(observation(), (640, 360))
    detection = Detection("0:0", "fixture", 0, "player", box, 0.9)
    project_automatic(detection, state, (640, 360))
    assert detection.field_position is None
    assert detection.projection_status == expected


def test_full_pipeline_loss_recovery_artifacts_cache_and_frame_identity(demo_fixture, tmp_path):
    video = inspect_video(demo_fixture["video"])
    rows = [observation(i) for i in range(video.frame_count)]
    rows[3]["points"] = []  # a cut/close-up must not retain frame 2's matrix
    rows[4]["lines"] = []
    bundle = bundle_for(video, tmp_path / "bundle", rows)
    result = process_video(
        video.path, bundle, demo_fixture["models"], tmp_path / "runs", detector=SyntheticDetector()
    )
    assert validate_completed(result.directory)["schema_version"] == 2
    records = [
        json.loads(line) for line in (result.directory / "framegegevens.jsonl").read_text().splitlines()
    ]
    assert records[2]["calibration"]["status"] == "valid"
    for i in (3, 4):
        assert records[i]["detections"][0]["field_position"] is None
        assert records[i]["detections"][0]["projection_status"] == "calibration_unavailable"
        assert records[i]["player_summary"]["on_field"] is None
        assert records[i]["detections"][0]["counted_as_player"] is False
    assert records[5]["detections"][0]["field_position"] is not None
    assert records[5]["player_summary"]["on_field"] == 1
    assert records[8]["detections"] == []
    assert records[8]["player_summary"]["on_field"] == 0
    assert records[19]["calibration"]["frame_index"] == 19
    assert result.manifest["measurements"]["calibration_usable_fraction"] == 0.9
    portable = load_automatic_calibration(result.directory / "calibration.json")
    portable.validate_for(video)
    repeated = process_video(
        video.path, portable, demo_fixture["models"], tmp_path / "runs", detector=SyntheticDetector()
    )
    assert repeated.reused
    tracked = process_video(
        video.path,
        bundle,
        demo_fixture["models"],
        tmp_path / "other",
        tracker_config_path=ROOT / "configs/bytetrack.yaml",
        detector=SyntheticDetector(),
    )
    assert tracked.manifest["tracking_policy"]["camera_compensation"] == "background_affine_ransac"
    assert tracked.manifest["mvp_acceptance"] is None
    assert tracked.manifest["tracking_policy"]["human_accuracy_validated"] is False


def test_bundle_rejects_different_video_and_corrupt_observations(demo_fixture, tmp_path):
    video = inspect_video(demo_fixture["video"])
    bundle = bundle_for(video, tmp_path)
    bundle.validate_for(video)
    other = deepcopy(bundle)
    other.manifest["video"]["sha256"] = "different"
    with pytest.raises(PipelineError, match="andere clip"):
        other.validate_for(video)
    Path(bundle.observations_path).write_text("modified")
    with pytest.raises(PipelineError, match="beschadigd"):
        bundle.validate_for(video)


@pytest.mark.parametrize("condition", ["missing", "extra", "timestamp", "duplicate_index"])
def test_timeline_errors_fail_even_if_bundle_hash_is_updated(demo_fixture, tmp_path, condition):
    video = inspect_video(demo_fixture["video"])
    rows = [observation(i) for i in range(video.frame_count)]
    if condition == "missing":
        rows.pop()
    elif condition == "extra":
        rows.append(observation(20))
    elif condition == "timestamp":
        rows[2]["timestamp_s"] = 10
    else:
        rows[2]["frame_index"] = 1
    bundle = bundle_for(video, tmp_path, rows)
    bundle.validate_for(video)
    with pytest.raises(PipelineError, match="kalibratie"):
        list(bundle.frames(video))


def test_automatic_replay_requires_same_calibration_and_recomputes_positions(
    demo_fixture, tmp_path, monkeypatch
):
    from football_pipeline import pipeline

    # Stub the network boundary only; production replay still requires real detector evidence.
    monkeypatch.setattr(pipeline, "UltralyticsDetector", lambda models: SyntheticDetector())
    video = inspect_video(demo_fixture["video"])
    bundle = bundle_for(video, tmp_path / "bundle")
    original = process_video(video.path, bundle, demo_fixture["models"], tmp_path / "runs")
    replayed = process_video(
        video.path, bundle, demo_fixture["models"], tmp_path / "replay", replay_run=original.directory
    )
    assert (replayed.directory / "framegegevens.jsonl").read_bytes() == (
        original.directory / "framegegevens.jsonl"
    ).read_bytes()
    changed = bundle_for(video, tmp_path / "changed")
    changed.manifest["source"] = "different provenance"
    with pytest.raises(PipelineError, match="dezelfde framekalibraties"):
        process_video(
            video.path,
            changed,
            demo_fixture["models"],
            tmp_path / "invalid-replay",
            replay_run=original.directory,
        )


def test_automatic_ui_processes_only_on_click_and_invalidates_when_switching(
    demo_fixture, tmp_path, monkeypatch
):
    from types import SimpleNamespace
    from unittest.mock import Mock

    import streamlit as st
    from streamlit.testing.v1 import AppTest

    from football_pipeline import pipeline

    video = inspect_video(demo_fixture["video"])
    bundle = bundle_for(video, tmp_path / "bundle")
    prepare = Mock(return_value=bundle)
    monkeypatch.setattr(pipeline, "prepare_automatic_calibration", prepare)
    monkeypatch.setattr(pipeline, "UltralyticsDetector", lambda models: SyntheticDetector())
    monkeypatch.setenv("FOOTBALL_MODELS", str(demo_fixture["models"]))
    monkeypatch.setenv("FOOTBALL_RUNS", str(tmp_path / "runs"))
    runtime = tmp_path / "runtime.json"
    identity_file = tmp_path / "weights.identity"
    identity_file.write_text("synthetic UI fixture")
    write_json(runtime, {"weights_keypoints": str(identity_file), "weights_lines": str(identity_file)})
    monkeypatch.setenv("FOOTBALL_FIELD_RUNTIME", str(runtime))
    content = demo_fixture["video"].read_bytes()
    upload = SimpleNamespace(file_id="automatic-ui-fixture", getbuffer=lambda: content)
    monkeypatch.setattr(st, "file_uploader", lambda *a, **kw: upload if kw["key"] == "video_upload" else None)
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    app.session_state["automatic_analysis"] = False
    app.run()
    app.segmented_control(key="calibration_mode").set_value("Automatische veldkalibratie").run()
    assert not app.exception
    assert not app.checkbox(key="tracking").disabled
    assert app.button(key="process").disabled
    app.text_input(key="field_source").set_value("generated test")
    app.text_input(key="field_usage").set_value("synthetic engineering fixture").run()
    assert not app.exception
    assert not app.button(key="process").disabled
    assert prepare.call_count == 0
    app.button(key="process").click().run()
    assert not app.exception
    assert prepare.call_count == 1
    assert app.session_state["result"].manifest["calibration_mode"] == "automatic"
    app.run()
    assert prepare.call_count == 1
    app.text_input(key="field_source").set_value("changed source").run()
    assert "result" not in app.session_state
    app.segmented_control(key="calibration_mode").set_value("Handmatig").run()
    assert not app.exception
    assert app.button(key="calculate").disabled


def test_independent_evaluation_reports_coverage_and_rejects_unreviewed_labels(tmp_path, monkeypatch):
    from football_pipeline import calibration_evaluation

    directory = tmp_path / "run"
    directory.mkdir()
    manifest = {
        "calibration_mode": "automatic",
        "calibration_id": "fixture",
        "video": {"sha256": "abc", "width": 640, "height": 360, "frame_count": 30},
    }
    monkeypatch.setattr(calibration_evaluation, "validate_completed", lambda _: manifest)
    states = [estimate_frame(observation(), (640, 360)) for _ in range(30)]
    states[1] = estimate_frame({"points": [], "lines": []}, (640, 360))
    (directory / "framegegevens.jsonl").write_text(
        "".join(json.dumps({"frame_index": i, "calibration": s}) + "\n" for i, s in enumerate(states)),
        encoding="utf-8",
    )
    reference = {
        "schema_version": 1,
        "video_sha256": "abc",
        "human_reviewed": True,
        "reviewer": "synthetic test fixture only",
        "used_for_tuning": False,
        "selection_frozen_at": "2026-10-16T10:00:00Z",
        "source": "generated",
        "usage": "test",
        "selected_frame_indices": list(range(30)),
        "frames": [
            {
                "frame_index": i,
                "calibratable": True,
                "points": [{"x": 320, "y": 40, "u": 0.5, "v": 0}, {"x": 320, "y": 320, "u": 0.5, "v": 1}],
            }
            for i in range(30)
        ],
    }
    path = tmp_path / "reference.json"
    write_json(path, reference)
    report = calibration_evaluation.evaluate_calibration(directory, path)
    assert report["coverage_on_calibratable_frames"] == pytest.approx(29 / 30)
    assert report["within_limits_frames"] == 29
    assert report["maximum_error_px"] < 0.001
    reference["human_reviewed"] = False
    write_json(path, reference)
    with pytest.raises(PipelineError, match="menselijke review"):
        calibration_evaluation.evaluate_calibration(directory, path)


def test_upload_automatically_runs_field_players_tracking_and_does_not_repeat(
    demo_fixture, tmp_path, monkeypatch
):
    from unittest.mock import Mock

    from streamlit.testing.v1 import AppTest

    from football_pipeline import automatic_analysis_ui, pipeline

    video = inspect_video(demo_fixture["video"])
    bundle = bundle_for(video, tmp_path / "bundle")
    prepare = Mock(return_value=bundle)
    monkeypatch.setattr(pipeline, "prepare_automatic_calibration", prepare)
    actual_process = pipeline.process_video
    process = Mock(side_effect=lambda *a, **kw: actual_process(*a, **kw, detector=SyntheticDetector()))
    monkeypatch.setattr(automatic_analysis_ui, "process_video", process)
    monkeypatch.setenv("FOOTBALL_AUTO_MODELS", str(demo_fixture["models"]))
    monkeypatch.setenv("FOOTBALL_RUNS", str(tmp_path / "runs"))
    custom_teams = tmp_path / "configured-teams.json"
    custom_teams.write_bytes((ROOT / "configs/teams.json").read_bytes())
    monkeypatch.setenv("FOOTBALL_TEAMS", str(custom_teams))
    identity = tmp_path / "identity"
    identity.write_text("synthetic model identity")
    runtime = tmp_path / "runtime.json"
    write_json(runtime, {"weights_keypoints": str(identity), "weights_lines": str(identity)})
    monkeypatch.setenv("FOOTBALL_FIELD_RUNTIME", str(runtime))
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=40).run()
    assert app.toggle(key="automatic_analysis").value
    app.file_uploader(key="video_upload").set_value(
        ("match.mp4", demo_fixture["video"].read_bytes(), "video/mp4")
    ).run()
    assert not app.exception
    assert not app.error
    assert process.call_count == prepare.call_count == 1
    assert process.call_args.kwargs["team_config_path"] == custom_teams
    result = app.session_state["result"]
    assert result.manifest["tracker_config"] is not None
    assert result.manifest["mvp_acceptance"] is None
    assert result.manifest["evidence_kind"] == "synthetic"
    records = [json.loads(row) for row in (result.directory / "framegegevens.jsonl").read_text().splitlines()]
    assert records[0]["detections"][0]["track_id"] == 1
    assert "tracking" in records[0]
    # Automatic uploads still require no model/calibration inputs. Team correction
    # controls are offered only after the analysis has completed.
    assert all(widget.key.startswith("team_") for widget in app.selectbox)
    assert all(widget.key.startswith("team_name_") for widget in app.text_input)
    assert result.manifest["team_settings"] is not None
    app.run()
    assert not app.exception
    assert process.call_count == prepare.call_count == 1


def test_automatic_analysis_failure_requires_explicit_retry_and_survives_repeated_failure(
    demo_fixture, tmp_path, monkeypatch
):
    from unittest.mock import Mock

    from streamlit.testing.v1 import AppTest

    from football_pipeline import automatic_analysis_ui

    process = Mock(side_effect=PipelineError("synthetic failure"))
    monkeypatch.setattr(automatic_analysis_ui, "process_video", process)
    monkeypatch.setenv("FOOTBALL_AUTO_MODELS", str(demo_fixture["models"]))
    identity = tmp_path / "identity"
    identity.write_text("fixture")
    runtime = tmp_path / "runtime.json"
    write_json(runtime, {"weights_keypoints": str(identity), "weights_lines": str(identity)})
    monkeypatch.setenv("FOOTBALL_FIELD_RUNTIME", str(runtime))
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    app.file_uploader(key="video_upload").set_value(
        ("failed.mp4", demo_fixture["video"].read_bytes(), "video/mp4")
    ).run()
    assert not app.exception
    assert process.call_count == 1
    app.run()
    assert not app.exception
    assert process.call_count == 1
    app.button(key="automatic_retry").click().run()
    assert not app.exception
    assert process.call_count == 2
    assert any("synthetic failure" in error.value for error in app.error)


def test_runtime_geometry_policy_is_used_and_explicit_policy_takes_precedence(
    demo_fixture, tmp_path, monkeypatch
):
    from football_pipeline import pipeline

    video = inspect_video(demo_fixture["video"])
    bundle = bundle_for(video, tmp_path / "bundle")
    monkeypatch.setattr(pipeline, "prepare_automatic_calibration", lambda *a, **kw: bundle)
    runtime = tmp_path / "runtime.json"
    write_json(runtime, {"calibration_settings": {"motion": False}})
    for i, override in enumerate((None, {"motion": True})):
        result = process_video(
            video.path,
            None,
            demo_fixture["models"],
            tmp_path / f"run-{i}",
            field_runtime_path=runtime,
            field_settings=override,
            detector=SyntheticDetector(),
        )
        assert result.manifest["field_settings"]["motion"] == (override is not None)
