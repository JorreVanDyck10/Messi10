"""Audit actual export contracts; fixtures below are explicitly synthetic software evidence."""

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from football_pipeline.appearance import ROLE_NAMES
from football_pipeline.contracts import Detection, FrameRecord
from scripts import verify_player_pipeline as verifier


def audit_fixture(tmp_path, monkeypatch):
    appearance = {
        "model_id": "fixture_roles",
        "role_names": ROLE_NAMES,
        "role_confidence": 0.65,
        "team_confidence": 0.65,
    }
    manifest = {
        "video": {"fps_num": 25, "fps_den": 1, "frame_count": 3},
        "models": {"models": [{"class_mapping": {"0": "player", "1": "person"}}], "appearance": appearance},
    }
    people = []
    for i, role in enumerate(ROLE_NAMES):
        people.append(
            Detection(
                f"0:{i}",
                "fixture",
                0,
                role,
                [10, 10, 30, 50],
                0.9,
                field_position=[0.5, 0.5],
                projection_status="valid",
                role_model_id="fixture_roles",
                role_class_id=i,
                role_confidence=0.9,
            )
        )
    people[0].team_id = "team_a"
    people[0].team_confidence = 0.9
    people[0].team_class_id = 0
    people[0].team_method = "supervised_match"
    uncertain = deepcopy(people[0])
    uncertain.detection_id = "0:uncertain"
    uncertain.semantic_class = "person"
    uncertain.role_confidence = 0.55
    uncertain.team_id = uncertain.team_confidence = uncertain.team_class_id = uncertain.team_method = None
    people.append(uncertain)
    rows = [FrameRecord(0, 0.0, (640, 360), people, {"status": "valid"}).to_dict()]
    # Same player candidate, but the field worker failed on this exact frame.
    unavailable = deepcopy(people[0])
    unavailable.field_position = None
    unavailable.projection_status = "calibration_unavailable"
    rows.append(FrameRecord(1, 0.04, (640, 360), [unavailable], {"status": "insufficient_points"}).to_dict())
    rows.append(FrameRecord(2, 0.08, (640, 360), [], {"status": "valid"}).to_dict())
    monkeypatch.setattr(
        verifier,
        "inspect_video",
        lambda path: SimpleNamespace(
            frame_count=3,
            codec="h264",
            size=(1920, 720),
        ),
    )
    return manifest, rows


def write_rows(directory, rows):
    (directory / "framegegevens.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows),
        encoding="utf-8",
    )


def test_joint_audit_checks_team_roles_unknown_field_and_empty_frame(tmp_path, monkeypatch):
    manifest, rows = audit_fixture(tmp_path, monkeypatch)
    write_rows(tmp_path, rows)
    report = verifier.verify_records(tmp_path, manifest)
    assert report["counted_player_observations_by_team"] == {"team_a": 1}
    assert report["role_classified_detections"] == 8
    assert report["unknown_player_count_frames"] == 1
    assert report["empty_detection_frames"] == 1
    assert report["known_player_count_min_median_max"] == [0, 0.5, 1]
    assert report["detections_by_role"]["assistant_referee"] == 1
    assert report["detections_by_role"]["steward"] == 1


@pytest.mark.parametrize("damage", ["team_total", "nonplayer_team", "role_class", "role_model", "timestamp"])
def test_joint_audit_rejects_inconsistent_export(tmp_path, monkeypatch, damage):
    manifest, rows = audit_fixture(tmp_path, monkeypatch)
    if damage == "team_total":
        rows[0]["player_summary"]["teams"]["team_b"] = 1
    elif damage == "nonplayer_team":
        rows[0]["detections"][3].update(team_id="team_b", team_method="supervised_match", team_confidence=0.8)
    elif damage == "role_class":
        rows[0]["detections"][0]["role_class_id"] = ROLE_NAMES.index("steward")
    elif damage == "role_model":
        rows[0]["detections"][0]["role_model_id"] = "another_model"
    else:
        rows[1]["timestamp_s"] = 0.1
    write_rows(tmp_path, rows)
    with pytest.raises(AssertionError):
        verifier.verify_records(tmp_path, manifest)


def test_joint_app_runs_automatic_field_and_preserves_roles_teams_on_review(
    demo_fixture,
    model_manifest,
    tmp_path,
    monkeypatch,
):
    from streamlit.testing.v1 import AppTest
    from test_automatic_calibration import bundle_for

    from football_pipeline import pipeline
    from football_pipeline.contracts import read_json, sha256_file, write_json
    from football_pipeline.video import ROOT, inspect_video

    profile, models = model_manifest
    models["appearance"] = {
        "weights": models["models"][0]["weights"],
        "weights_sha256": sha256_file(models["models"][0]["weights"]),
        "role_names": ROLE_NAMES,
        "model_id": "fixture_roles",
        "device": "cpu",
        "role_confidence": 0.65,
        "team_confidence": 0.65,
    }
    write_json(profile, models)
    calibration = bundle_for(inspect_video(demo_fixture["video"]), tmp_path / "bundle")
    runtime = tmp_path / "runtime.json"
    write_json(
        runtime,
        {
            "weights_keypoints": models["models"][0]["weights"],
            "weights_lines": models["models"][0]["weights"],
        },
    )
    calls = []

    def prepare(video_path, runtime_path, output_root, **kwargs):
        calls.append(kwargs)
        return calibration

    class JointDetector:
        evidence_kind = "synthetic"
        provenance = {"fixture": "all_roles_and_teams_no_accuracy_claim"}

        def detect(self, frame, frame_index):
            if frame_index == 8:
                return []
            detections = []
            for i, role in enumerate(ROLE_NAMES):
                detections.append(
                    Detection(
                        f"{frame_index}:{i}",
                        "fixture",
                        0,
                        role,
                        [100 + i * 40, 120, 125 + i * 40, 180],
                        0.9,
                        role_model_id="fixture_roles",
                        role_class_id=i,
                        role_confidence=0.9,
                    )
                )
            detections[0].team_id = "team_b"
            detections[0].team_method = "supervised_match"
            detections[0].team_confidence = 0.9
            detections[0].team_class_id = 1
            return detections

    real_process = pipeline.process_video
    monkeypatch.setattr(pipeline, "prepare_automatic_calibration", prepare)
    monkeypatch.setattr(
        pipeline, "process_video", lambda *a, **kw: real_process(*a, **kw, detector=JointDetector())
    )
    monkeypatch.setenv("FOOTBALL_CALIBRATION_MODE", "automatic")
    monkeypatch.setenv("FOOTBALL_MODELS", str(profile))
    monkeypatch.setenv("FOOTBALL_FIELD_RUNTIME", str(runtime))
    monkeypatch.setenv("FOOTBALL_RUNS", str(tmp_path / "runs"))
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    app.file_uploader(key="video_upload").set_value(
        ("joint-synthetic.mp4", demo_fixture["video"].read_bytes(), "video/mp4"),
    ).run()
    assert app.session_state["calibration_mode"] == "Automatische veldkalibratie"
    assert not app.exception
    assert app.checkbox(key="tracking").disabled
    app.text_input(key="field_source").set_value("Synthetic software test")
    app.text_input(key="field_usage").set_value("Engineering only").run()
    app.button(key="process").click().run()
    assert not app.exception and not app.error
    assert len(calls) == 1 and calls[0]["source"] == "Synthetic software test"
    result = app.session_state["result"]
    assert result.manifest["evidence_kind"] == "synthetic"
    audit = verifier.verify_records(result.directory, result.manifest)
    assert audit["counted_player_observations_by_team"] == {"team_b": 19}
    assert audit["empty_detection_frames"] == 1
    assert "mvp_acceptance.json" not in result.manifest["artifacts"]
    assert not read_json(result.directory / "calibration.json").get("human_reviewed")
    app.run()
    assert len(calls) == 1  # Rerendering does not silently run either model again.
    app.checkbox(key="open_field_review").check().run()
    assert not app.exception
    token = result.manifest["cache_key"][:12]
    app.slider(key=f"review_frame_{token}").set_value(8).run()
    assert not app.exception and any("frame 8" in m.value for m in app.markdown)
