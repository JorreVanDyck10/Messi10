from pathlib import Path

from football_pipeline.contracts import read_json
from football_pipeline.field_motion import DEFAULT_SETTINGS, MOTION_RANK_SETTINGS, validate_settings


def test_unvalidated_motion_rank_policy_remains_explicit_opt_in():
    root = Path(__file__).resolve().parents[1]
    model = read_json(root / "configs/models-broadcast.json")
    configured = {**DEFAULT_SETTINGS, **model.get("field_settings", {})}
    assert validate_settings(configured)["holdout_rule"] == "two_semantic_tertiles_no_refit"
    candidate = read_json(root / "configs/field-motion-rank.json")
    assert validate_settings(candidate) == MOTION_RANK_SETTINGS
