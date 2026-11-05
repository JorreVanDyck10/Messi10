import importlib
from copy import deepcopy
from pathlib import Path

from football_pipeline.contracts import write_json


def test_out_of_contract_field_reference_is_unscored_without_dropping_people(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    evaluator = importlib.import_module("scripts.evaluate_temporal_extension_field")
    label = tmp_path / "provider-field.json"
    write_json(label, {"Side line top": [{"x": -0.02, "y": 0.2}, {"x": 0.8, "y": 0.2}]})
    row = {
        "frame_index": 7,
        "field_label": str(label),
        "label_policy": "provider_visible_polylines_v1",
        "width": 640,
        "height": 360,
        "people": [{"role": "player"}],
    }
    before = deepcopy(row)
    result = evaluator.reference_metrics([row], [{}], [{"status": "valid"}])
    assert result["frames"] == 1
    assert result["unsupported_field_reference"] == 1
    assert result["correct"] == result["wrong"] == 0
    assert result["per_frame"][0]["status"] == "unsupported_field_reference"
    assert row == before
