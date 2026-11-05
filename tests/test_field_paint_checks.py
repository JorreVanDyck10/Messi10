import json

import numpy as np

from football_pipeline.field_paint_checks import paint_evidence


def state():
    return {"status": "valid", "homography": np.diag([1 / 1000, 1 / 600, 1]).tolist()}


def test_supported_lines_pass_and_two_distinct_mismatches_reject():
    frame = np.zeros((600, 1000, 3), np.uint8)
    vertical = np.column_stack((np.full(301, 500), np.arange(100, 401)))
    horizontal = np.column_stack((np.arange(100, 401), np.zeros(301)))
    valid = paint_evidence(frame, state(), chains_and_size=([vertical, horizontal], (1000, 600)))
    assert not valid["reject"]
    shifted = [vertical + [-150, 0], horizontal + [0, 100]]
    rejected = paint_evidence(frame, state(), chains_and_size=(shifted, (1000, 600)))
    assert rejected["reject"]
    assert sum(c["mismatch"] for c in rejected["chains"]) == 2
    json.dumps(rejected, allow_nan=False)


def test_one_chain_and_parallel_fragments_do_not_establish_independent_disagreement():
    frame = np.zeros((600, 1000, 3), np.uint8)
    horizontal = np.column_stack((np.arange(100, 401), np.full(301, 100)))
    for chains in ([horizontal], [horizontal, horizontal + [300, 0]]):
        evidence = paint_evidence(frame, state(), chains_and_size=(chains, (1000, 600)))
        assert not evidence["reject"]


def test_pixel_scale_and_projective_matrix_scale_do_not_change_evidence():
    frame = np.zeros((1200, 2000, 3), np.uint8)
    vertical = np.column_stack((np.full(301, 500), np.arange(100, 401)))
    original = state()
    original["homography"] = (np.asarray(original["homography"]) @ np.diag([0.5, 0.5, 1]) * -7).tolist()
    result = paint_evidence(frame, original, chains_and_size=([vertical], (1000, 600)))
    assert result["chains"][0]["median_px"] < 1e-8
    assert not result["reject"]


def test_unavailable_projection_is_never_recovered_by_paint():
    result = paint_evidence(np.zeros((10, 10, 3)), {"status": "insufficient_points"})
    assert result == {"status": "not_applicable", "reject": False, "chains": []}


def test_unrelated_white_structures_outside_pitch_cannot_veto_a_projection():
    frame = np.zeros((600, 1000, 3), np.uint8)
    lower_pitch = {"status": "valid", "homography": [[0.001, 0, 0], [0, 1 / 300, -1], [0, 0, 1]]}
    outside = [
        np.column_stack((np.arange(100, 401), np.full(301, 100))),
        np.column_stack((np.full(201, 350), np.arange(0, 201))),
    ]
    result = paint_evidence(frame, lower_pitch, chains_and_size=(outside, (1000, 600)))
    assert result["status"] == "unavailable"
    assert not result["reject"]
