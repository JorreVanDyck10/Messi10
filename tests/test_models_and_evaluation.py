from copy import deepcopy

import pytest

from football_pipeline.contracts import PipelineError, write_json
from football_pipeline.detection import load_model_manifest
from football_pipeline.evaluation import evaluate_frames


def test_duplicate_semantic_suppliers_rejected(model_manifest):
    path, manifest = model_manifest
    other = deepcopy(manifest["models"][0])
    other["model_id"] = "other"
    manifest["models"].append(other)
    write_json(path, manifest)
    with pytest.raises(PipelineError, match="Dubbele leverancier"):
        load_model_manifest(path)


def test_person_never_becomes_player(model_manifest):
    path, manifest = model_manifest
    manifest["models"][0]["expected_names"] = {"0": "person"}
    write_json(path, manifest)
    with pytest.raises(PipelineError, match="stilzwijgend"):
        load_model_manifest(path)


def test_handover_weight_hash_is_verified(model_manifest):
    path, manifest = model_manifest
    manifest["models"][0]["weights_sha256"] = "wrong_hash"
    write_json(path, manifest)
    with pytest.raises(PipelineError, match="Gewichtshash"):
        load_model_manifest(path)


def test_non_object_manifest_is_an_actionable_error(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(PipelineError, match="JSON-object"):
        load_model_manifest(path)


def test_evaluation_switches_takeovers_gaps_and_full_occlusion():
    reference = [
        {"frame_index": i, "objects": [{"reference_id": "a", "visible": i != 3, "bbox_xyxy": [0, 0, 10, 20]}]}
        for i in range(5)
    ]
    ids = [1, None, 2, None, 2]
    predictions = [
        {
            "frame_index": i,
            "detections": []
            if identifier is None
            else [{"track_id": identifier, "semantic_class": "player", "bbox_xyxy": [0, 0, 10, 20]}],
        }
        for i, identifier in enumerate(ids)
    ]
    report = evaluate_frames(predictions, reference)
    assert report["counts"]["id_switches"] == 1
    assert report["counts"]["interruptions"] == 1
    assert report["counts"]["missed_visible_observations"] == 1
    reference[-1]["objects"][0]["reference_id"] = "b"
    assert evaluate_frames(predictions, reference)["counts"]["id_takeovers"] == 1


def test_evaluation_uses_one_to_one_assignment():
    predictions = [
        {
            "frame_index": 0,
            "detections": [
                {"track_id": t, "semantic_class": "player", "bbox_xyxy": [0, 0, 10, 20]} for t in [1, 2]
            ],
        }
    ]
    refs = [
        {"frame_index": 0, "objects": [{"reference_id": "a", "visible": True, "bbox_xyxy": [0, 0, 10, 20]}]}
    ]
    report = evaluate_frames(predictions, refs)
    assert report["counts"]["matched_observations"] == 1
    assert report["counts"]["false_track_observations"] == 1
