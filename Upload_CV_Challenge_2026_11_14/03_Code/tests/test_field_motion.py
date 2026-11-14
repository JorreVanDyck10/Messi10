import json
from copy import deepcopy
from pathlib import Path

import cv2
import numpy as np
import pytest
from test_automatic_calibration import bundle_for, observation

from football_pipeline.automatic_calibration import AutomaticCalibration, transform
from football_pipeline.contracts import PipelineError, read_json, sha256_file
from football_pipeline.field_layout import LINES_UV, POINTS_UV
from football_pipeline.field_motion import DEFAULT_SETTINGS, CameraCalibration, estimate_checked, line_checks
from football_pipeline.field_review import failure_intervals, finalize_review, save_review
from football_pipeline.pipeline import process_video, validate_completed
from football_pipeline.video import ROOT, inspect_video


def test_visible_field_line_can_be_checked_when_virtual_endpoints_straddle_horizon():
    identifier, endpoints = next(
        (i, p) for i, p in LINES_UV.items() if p[0][1] == p[1][1] and {p[0][0], p[1][0]} == {0, 1}
    )
    inverse = np.array([[1000, 0, -600], [0, 200, 30], [1, 0, -0.5]], float)
    with pytest.raises(ValueError, match="horizon"):
        transform(endpoints, inverse)
    observed = transform([[0.7, endpoints[0][1]], [0.9, endpoints[0][1]]], inverse)
    errors, checked = line_checks([{"id": identifier, "xy": observed.tolist()}], inverse)
    assert checked == [identifier]
    assert max(errors) < 1e-8


def test_points_are_checked_without_mandatory_lines_and_controls_are_not_refitted():
    row = observation()
    row["lines"] = []
    state = estimate_checked(row, (640, 360))
    assert state["status"] == "valid"
    quality = state["quality"]
    assert len(quality["control_ids"]) == 2
    assert set(quality["control_ids"]).isdisjoint(quality["fit_ids"])
    assert quality["control_maximum_px"] < 0.001
    changed = deepcopy(row)
    next(p for p in changed["points"] if p["id"] == quality["control_ids"][0])["x"] += 40
    rejected = estimate_checked(changed, (640, 360))
    assert rejected["status"] == "inconsistent_controls"
    assert rejected["homography"] is None
    assert rejected["quality"]["fit_ids"] == quality["fit_ids"]


def test_exact_four_point_fit_needs_additional_nonparallel_line_controls():
    row = observation()
    row["points"] = [p for p in row["points"] if p["id"] in {5, 6, 25, 26}]
    row["lines"] = []
    assert estimate_checked(row, (640, 360))["status"] == "insufficient_controls"
    inverse = np.array([[560, 0, 40], [0, 280, 40], [0, 0, 1.0]])
    row["lines"] = [
        {"id": i, "xy": transform(LINES_UV[i], inverse).tolist(), "confidence": 0.99} for i in [2, 5]
    ]
    assert estimate_checked(row, (640, 360))["status"] == "insufficient_controls"
    row["lines"].append({"id": 17, "xy": transform(LINES_UV[17], inverse).tolist(), "confidence": 0.99})
    assert estimate_checked(row, (640, 360))["status"] == "valid"
    row["lines"][-1]["xy"][0][1] += 50
    assert estimate_checked(row, (640, 360))["status"] == "inconsistent_lines"


def texture(seed=4):
    rng = np.random.default_rng(seed)
    gray = rng.integers(40, 180, (360, 640), dtype=np.uint8)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return np.stack((gray // 2, gray, gray // 2), axis=2)


def unknown():
    return estimate_checked({"points": [], "lines": []}, (640, 360))


def test_actual_optical_flow_measures_pan_zoom_and_expires_without_refreshing_anchor():
    frame = texture()
    camera = CameraCalibration(10)
    anchor = estimate_checked(observation(), (640, 360))
    camera.update(frame, anchor, 0)
    movement = np.array([[1.01, 0, 3], [0, 1.01, 2], [0, 0, 1.0]])
    moved = cv2.warpPerspective(frame, movement, (640, 360))
    state = camera.update(moved, unknown(), 1)
    assert state["status"] == "valid", state
    assert state["source"] == "tracked"
    assert state["reference_frame"] == 0
    assert state["age_s"] == 0.1
    assert state["motion_quality"]["inliers"] >= 20
    reference_xy = [[220, 120], [400, 240]]
    expected = transform(reference_xy, np.array(anchor["homography"]))
    actual = transform(transform(reference_xy, movement), np.array(state["homography"]))
    assert actual == pytest.approx(expected, abs=0.003)
    assert state["homography"] != anchor["homography"]
    # Equal images yield a measured identity motion, but never reset the independent reference age.
    for index in range(2, 21):
        still = camera.update(moved, unknown(), index)
    assert still["status"] == "valid"
    expired = camera.update(moved, unknown(), 21)
    assert expired["status"] == "bridge_expired"
    assert expired["homography"] is None
    assert camera.update(moved, unknown(), 22)["status"] != "valid"
    assert camera.update(moved, anchor, 23)["source"] == "detected"


@pytest.mark.parametrize("failure", ["cut", "no_features", "geometry", "drift", "blur"])
def test_motion_failure_resets_then_direct_recognition_recovers(failure):
    camera = CameraCalibration(25)
    frame = texture()
    direct = estimate_checked(observation(), (640, 360))
    camera.update(frame, direct, 0)
    missing = unknown()
    if failure == "cut":
        frame = np.full_like(frame, 230)
    elif failure == "no_features":
        # Constant grass is insufficient even if there is no histogram cut.
        frame = np.full_like(frame, (55, 110, 55))
    elif failure == "geometry":
        missing["status"] = "degenerate_geometry"
    elif failure == "drift":
        missing["points"] = deepcopy(direct["points"][:2])
        for p in missing["points"]:
            p["x"] += 50
    else:
        frame = cv2.GaussianBlur(frame, (51, 51), 15)
    failed = camera.update(frame, missing, 1)
    assert failed["status"] != "valid"
    assert failed["homography"] is None
    assert camera.state is None
    assert camera.update(frame, direct, 2)["source"] == "detected"


def test_confidence_is_a_separate_profile_and_old_identity_is_preserved(demo_fixture, tmp_path):
    video = inspect_video(demo_fixture["video"])
    old = bundle_for(video, tmp_path)
    old_identity = old.identity
    assert old.settings is None
    checked = AutomaticCalibration(old.manifest, old.observations_path, {"motion": False})
    relaxed = AutomaticCalibration(
        {**old.manifest, "schema_version": 2, "score_storage": "all_ground_peaks_before_threshold"},
        old.observations_path,
        {"keypoint_threshold": 0.25, "motion": False},
    )
    assert len({old_identity, checked.identity, relaxed.identity}) == 3
    assert old.identity == old_identity
    invalid = AutomaticCalibration(old.manifest, old.observations_path, {"maximum_age_s": 5})
    with pytest.raises(PipelineError, match="grenzen"):
        invalid.validate_for(video)
    filtered = AutomaticCalibration(old.manifest, old.observations_path, {"keypoint_threshold": 0.25})
    with pytest.raises(PipelineError, match="gefilterde scores"):
        filtered.validate_for(video)


def test_confidence_comparison_filters_the_same_raw_observations():
    row = observation()
    for point in row["points"]:
        point.update(confidence=0.3, raw_score=0.3)
    original = deepcopy(row)
    assert estimate_checked(row, (640, 360))["status"] == "insufficient_points"
    settings = {**DEFAULT_SETTINGS, "keypoint_threshold": 0.25}
    assert estimate_checked(row, (640, 360), settings)["status"] == "valid"
    assert row == original


@pytest.mark.parametrize("fault", [None, "missing_point", "missing_line", "missing_score", "score_mismatch"])
def test_full_score_bundles_validate_completeness_before_comparisons(demo_fixture, tmp_path, fault):
    video = inspect_video(demo_fixture["video"])
    rows = [observation(i) for i in range(video.frame_count)]
    for row in rows:
        present = {p["id"] for p in row["points"]}
        row["points"].extend(
            {"id": i, "x": 0, "y": 0, "confidence": 0} for i in POINTS_UV if i not in present
        )
        present = {p["id"] for p in row["lines"]}
        row["lines"].extend(
            {"id": i, "xy": [[0, 0], [0, 0]], "confidence": 0} for i in LINES_UV if i not in present
        )
        for point in row["points"]:
            point["raw_score"] = point["confidence"]
        for line in row["lines"]:
            line["raw_scores"] = [line["confidence"], line["confidence"]]
    bundle = bundle_for(video, tmp_path / "raw", rows)
    bundle.manifest.update(schema_version=2, score_storage="all_ground_peaks_before_threshold")
    bundle.validate_for(video)
    if fault:
        if fault == "missing_point":
            rows[0]["points"].pop()
        elif fault == "missing_line":
            rows[0]["lines"].pop()
        elif fault == "missing_score":
            rows[0]["points"][0].pop("raw_score")
        else:
            rows[0]["lines"][0]["raw_scores"] = [0.1, 0.2]
        path = Path(bundle.observations_path)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        bundle.manifest["observations_sha256"] = sha256_file(path)
        bundle.validate_for(video)
        with pytest.raises(PipelineError, match="kalibratieframe"):
            list(bundle.frames(video))
    else:
        states = list(bundle.frames(video))
        assert all(state["status"] == "valid" for state in states)


def test_motion_also_checks_available_lines_and_resets_across_missing_indices():
    frame = texture()
    camera = CameraCalibration(25)
    direct = estimate_checked(observation(), (640, 360))
    camera.update(frame, direct, 0)
    dropout = unknown()
    dropout["lines"] = deepcopy(direct["lines"])
    for line in dropout["lines"]:
        for point in line["xy"]:
            point[0] += 50
    assert camera.update(frame, dropout, 1)["status"] == "motion_line_disagreement"
    camera.update(frame, direct, 2)
    assert camera.update(frame, unknown(), 4)["status"] != "valid"


@pytest.mark.parametrize("inliers", [0, 19, 25])
def test_motion_rejects_fewer_than_twenty_or_low_ratio_inliers(monkeypatch, inliers):
    camera = CameraCalibration(25)
    frame = texture()
    camera.update(frame, estimate_checked(observation(), (640, 360)), 0)

    def bad_consensus(a, b, *args):
        mask = np.zeros((len(a), 1), np.uint8)
        mask[:inliers] = 1
        return np.eye(3), mask

    monkeypatch.setattr(cv2, "findHomography", bad_consensus)
    state = camera.update(frame, unknown(), 1)
    assert state["status"] == "inconsistent_motion"
    assert state["homography"] is None


def test_recalibration_reuses_detections_but_recomputes_current_geometry(demo_fixture, tmp_path, monkeypatch):
    from football_pipeline import pipeline
    from football_pipeline.demo import SyntheticDetector

    monkeypatch.setattr(pipeline, "UltralyticsDetector", lambda _: SyntheticDetector())
    video = inspect_video(demo_fixture["video"])
    bundle = bundle_for(video, tmp_path / "bundle")
    original = process_video(video.path, bundle, demo_fixture["models"], tmp_path / "original")
    candidate = AutomaticCalibration(bundle.manifest, bundle.observations_path, {"motion": False})
    result = process_video(
        video.path,
        candidate,
        demo_fixture["models"],
        tmp_path / "candidate",
        replay_run=original.directory,
        recalibrate_replay=True,
    )
    manifest = validate_completed(result.directory)
    assert manifest["schema_version"] == 3
    assert manifest["calibration_id"] != original.manifest["calibration_id"]
    assert manifest["tracker_config"] is None
    rows = [json.loads(line) for line in (result.directory / "framegegevens.jsonl").read_text().splitlines()]
    assert rows[0]["calibration"]["source"] == "detected"
    replayed = process_video(
        video.path, candidate, demo_fixture["models"], tmp_path / "repeat", replay_run=result.directory
    )
    assert (replayed.directory / "framegegevens.jsonl").read_bytes() == (
        result.directory / "framegegevens.jsonl"
    ).read_bytes()
    tracked = process_video(
        video.path,
        candidate,
        demo_fixture["models"],
        tmp_path / "tracked",
        tracker_config_path=ROOT / "configs/bytetrack.yaml",
        replay_run=result.directory,
    )
    assert tracked.manifest["tracking_policy"]["camera_compensation"] == "background_affine_ransac"
    assert tracked.manifest["mvp_acceptance"] is None


def test_human_references_require_explicit_input_and_completion_is_separate(tmp_path):
    path = tmp_path / "review.json"
    template = {
        "video_sha256": "abc",
        "calibration_id": "candidate",
        "selection_frozen_at": "before",
        "settings_frozen_at": "frozen",
        "used_for_tuning": False,
        "image_size": [640, 360],
        "selected_frame_indices": [2, 5],
    }
    points = [{"id": 5, "x": 50, "y": 60}, {"id": 25, "x": 100, "y": 150}]
    with pytest.raises(PipelineError, match="Bevestig"):
        save_review(path, template, index=2, points=points, calibratable=True, reviewer="test")
    saved = save_review(
        path, template, index=2, points=points, calibratable=True, reviewer="test", confirmed=True
    )
    assert saved["human_reviewed"] is False
    assert saved["frames"][0]["human_reviewed"] is True
    with pytest.raises(PipelineError):
        finalize_review(path, confirmed=True)
    save_review(path, template, index=5, points=[], calibratable=False, reviewer="test", confirmed=True)
    assert finalize_review(path, confirmed=True)["human_reviewed"] is True
    template["calibration_id"] = "other"
    with pytest.raises(PipelineError, match="andere selectie"):
        save_review(
            path, template, index=2, points=points, calibratable=True, reviewer="test", confirmed=True
        )
    assert read_json(path)["calibration_id"] == "candidate"


def test_failed_intervals_include_first_last_and_empty():
    records = [
        {"calibration": {"status": s}} for s in ["missing", "missing", "valid", "missing", "valid", "missing"]
    ]
    assert failure_intervals(records) == [(0, 1), (3, 3), (5, 5)]
    assert failure_intervals([]) == []


def test_new_ui_saved_run_uses_same_frame_and_point_toggles(demo_fixture, tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    from football_pipeline.demo import SyntheticDetector

    video = inspect_video(demo_fixture["video"])
    old = bundle_for(video, tmp_path / "bundle")
    candidate = AutomaticCalibration(old.manifest, old.observations_path, {"motion": False})
    result = process_video(
        video.path, candidate, demo_fixture["models"], tmp_path / "runs", detector=SyntheticDetector()
    )
    monkeypatch.setenv("FOOTBALL_RUNS", str(tmp_path / "runs"))
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    app.session_state["automatic_analysis"] = False
    app.run()
    app.radio(key="workspace_view").set_value("Veldcontrole").run()
    assert not app.exception

    token = result.manifest["cache_key"][:12]
    app.slider(key=f"review_frame_{token}").set_value(4).run()
    assert not app.exception
    assert any("frame 4" in element.value for element in app.markdown)
    app.checkbox(key=f"recognized_{token}").uncheck().run()
    app.checkbox(key=f"tracked_{token}").uncheck().run()
    assert not app.exception


def test_ui_human_reference_is_only_saved_after_explicit_input(demo_fixture, tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    from football_pipeline import field_review_ui
    from football_pipeline.contracts import write_json
    from football_pipeline.demo import SyntheticDetector

    video = inspect_video(demo_fixture["video"])
    old = bundle_for(video, tmp_path / "bundle")
    candidate = AutomaticCalibration(old.manifest, old.observations_path, {"motion": False})
    result = process_video(
        video.path, candidate, demo_fixture["models"], tmp_path / "runs", detector=SyntheticDetector()
    )
    (tmp_path / "configs").mkdir()
    write_json(
        tmp_path / "configs/broadcast-field-selection.json",
        {
            "video_sha256": video.sha256,
            "development_indices": [0],
            "evaluation_indices": [1],
            "selection_frozen_at": "before",
            "source": "synthetic test",
            "usage": "software test only",
        },
    )
    monkeypatch.setattr(field_review_ui, "ROOT", tmp_path)
    monkeypatch.setenv("FOOTBALL_RUNS", str(tmp_path / "runs"))
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    app.session_state["automatic_analysis"] = False
    app.run()
    app.radio(key="workspace_view").set_value("Veldcontrole").run()
    assert not app.exception
    token = result.manifest["cache_key"][:12]
    assert not (tmp_path / "data/field-reviews").exists()
    app.text_input(key=f"reviewer_{token}").set_value("Synthetic reviewer test")
    app.segmented_control(key=f"possible_{token}_0_Ontwikkeling").set_value("Ja").run()
    app.button(key=f"save_review_{token}").click().run()
    assert any("minstens twee" in e.value for e in app.error)
    key = f"human_points_{token}_Ontwikkeling_0"
    points = deepcopy(app.session_state[key])
    points[0].update(x=40, y=40)
    points[1].update(x=320, y=40)
    app.session_state[key] = points
    app.button(key=f"save_review_{token}").click().run()
    assert not app.exception
    path = next((tmp_path / "data/field-reviews").rglob("*.json"))
    document = read_json(path)
    assert document["human_reviewed"] is False
    assert document["used_for_tuning"] is True
    assert len(document["frames"][0]["points"]) == 2
    app.checkbox(key=f"confirm_set_{token}_Ontwikkeling").check().run()
    app.button(key=f"finalize_{token}_Ontwikkeling").click().run()
    assert not app.exception
    assert read_json(path)["human_reviewed"] is True
