from copy import deepcopy
from dataclasses import replace

import numpy as np
import pytest
from test_automatic_calibration import observation

from football_pipeline.automatic_calibration import transform
from football_pipeline.contracts import PipelineError
from football_pipeline.field_comparison import (
    evaluate_field_records,
    release_decision,
    summarize_field_records,
)
from football_pipeline.field_layout import POINTS_UV
from football_pipeline.field_motion import RELIABLE_SETTINGS, estimate_checked


def reviewed_fixture(video_metadata):
    video = replace(video_metadata, frame_count=30)
    state = estimate_checked(observation(), video.size, RELIABLE_SETTINGS)
    records = [
        {
            "frame_index": i,
            "timestamp_s": i / video.fps,
            "image_size": list(video.size),
            "calibration": deepcopy(state),
            "detections": [],
        }
        for i in range(30)
    ]
    uv = np.array([POINTS_UV[i] for i in [5, 25]])
    xy = transform(uv, np.linalg.inv(np.asarray(state["homography"])))
    points = [{"x": x, "y": y, "u": u, "v": v} for (x, y), (u, v) in zip(xy, uv)]
    reference = {
        "schema_version": 1,
        "video_sha256": video.sha256,
        "image_size": list(video.size),
        "human_reviewed": True,
        "reviewer": "synthetic test fixture",
        "used_for_tuning": False,
        "selection_frozen_at": "before",
        "settings_frozen_at": "before",
        "source": "synthetic fixture",
        "usage": "test",
        "selected_frame_indices": list(range(30)),
        "frames": [
            {"frame_index": i, "calibratable": True, "human_reviewed": True, "points": deepcopy(points)}
            for i in range(30)
        ],
    }
    return video, records, reference


def test_wrong_valid_missing_and_correct_projections_are_reported_separately(video_metadata):
    video, records, reference = reviewed_fixture(video_metadata)
    records[1]["calibration"] = dict(records[1]["calibration"], status="missing", homography=None)
    reference["frames"][2].update(calibratable=False, points=[])
    wrong = records[3]["calibration"]
    inverse = np.linalg.inv(np.array(wrong["homography"]))
    inverse = np.array([[1, 0, 30], [0, 1, 0], [0, 0, 1]]) @ inverse
    wrong["homography"] = np.linalg.inv(inverse).tolist()
    report = evaluate_field_records(records, video, reference)
    assert report["calibratable_frames"] == 29
    assert report["correct_frames"] == 27
    assert report["wrong_frames"] == 2
    assert report["false_valid_on_uncalibratable_frames"] == 1
    assert report["correct_coverage"] == 27 / 29
    assert report["maximum_error_px"] == pytest.approx(30)
    assert report["numerical_criteria_passed"] is False
    summary = summarize_field_records(records, video.fps)
    assert summary["wrong_frames"] is None
    assert summary["human_reviewed"] is False
    assert summary["longest_failure_s"] == 1 / video.fps


@pytest.mark.parametrize(
    "fault",
    [
        "unreviewed",
        "tuning",
        "too_few",
        "duplicate",
        "nan",
        "wrong_video",
        "bad_timeline",
        "unreviewed_frame",
    ],
)
def test_evaluation_rejects_untrusted_or_misaligned_references(video_metadata, fault):
    video, records, reference = reviewed_fixture(video_metadata)
    if fault == "unreviewed":
        reference["human_reviewed"] = False
    elif fault == "tuning":
        reference["used_for_tuning"] = True
    elif fault == "too_few":
        reference["frames"].pop()
    elif fault == "duplicate":
        reference["selected_frame_indices"][1] = 0
    elif fault == "nan":
        reference["frames"][0]["points"][0]["x"] = float("nan")
    elif fault == "wrong_video":
        reference["video_sha256"] = "other"
    elif fault == "bad_timeline":
        records[5]["timestamp_s"] += 1
    else:
        reference["frames"][0]["human_reviewed"] = False
    with pytest.raises(PipelineError):
        evaluate_field_records(records, video, reference)


def metric_pair():
    baseline = {
        "human_reviewed": True,
        "reference_sha256": "same",
        "wrong_frames": 2,
        "correct_coverage": 0.8,
        "median_error_px": 5,
        "p95_error_px": 10,
        "maximum_error_px": 12,
        "numerical_criteria_passed": False,
    }
    candidate = {**baseline, "wrong_frames": 1}
    return {"baseline": baseline, "candidate": candidate}


def test_release_requires_both_video_types_and_reviewed_improvement():
    pair = metric_pair()
    assert release_decision({"broadcast": pair})["eligible_for_activation"] is False
    pairs = {"broadcast": deepcopy(pair), "fixed": deepcopy(pair)}
    result = release_decision(pairs)
    assert result["eligible_for_activation"] is True
    assert result["activated"] is result["full_acceptance"] is False
    pairs["fixed"]["candidate"]["human_reviewed"] = False
    assert release_decision(pairs)["reasons"] == ["fixed:human_review_pending"]


@pytest.mark.parametrize("fault", ["coverage", "wrong", "error", "same", "missing", "different_reference"])
def test_release_rejects_regressions_and_missing_evidence(fault):
    pairs = {"broadcast": metric_pair(), "fixed": metric_pair()}
    baseline, candidate = pairs["fixed"]["baseline"], pairs["fixed"]["candidate"]
    if fault == "coverage":
        candidate["correct_coverage"] = baseline["correct_coverage"] - 0.051
    elif fault == "wrong":
        candidate["wrong_frames"] += 2
    elif fault == "error":
        candidate["maximum_error_px"] += 1
    elif fault == "same":
        candidate.update(baseline)
    elif fault == "missing":
        candidate["median_error_px"] = None
    else:
        candidate["reference_sha256"] = "different"
    assert release_decision(pairs)["eligible_for_activation"] is False


def test_release_allows_exactly_five_percentage_points_and_lower_error():
    pairs = {"broadcast": metric_pair(), "fixed": metric_pair()}
    for pair in pairs.values():
        pair["candidate"].update(correct_coverage=0.75, wrong_frames=2, median_error_px=4)
    assert release_decision(pairs)["eligible_for_activation"] is True


def test_export_review_writes_original_frames_and_json_guide_without_labels(demo_fixture, tmp_path):
    import cv2

    from football_pipeline.contracts import read_json, write_json
    from football_pipeline.video import inspect_video
    from scripts.compare_field_reliability import export_review

    video = inspect_video(demo_fixture["video"])
    write_json(
        tmp_path / "selection.json",
        {"video": {"path": video.path}, "video_sha256": video.sha256, "evaluation_indices": [1, 9]},
    )
    export_review(tmp_path)
    guide = read_json(tmp_path / "review-frames/guide.json")
    assert guide["human_reviewed"] is False
    assert guide["no_model_predictions_exported"] is True
    assert guide["selected_frame_indices"] == [1, 9]
    assert guide["field_point_ids_uv"]
    image = cv2.imread(str(tmp_path / "review-frames/frame-000009.jpg"))
    assert image.shape[:2] == (video.height, video.width)
    with pytest.raises(PipelineError):
        export_review(tmp_path)
