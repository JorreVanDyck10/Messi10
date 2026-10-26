from pathlib import Path

import pytest
import torch
import yaml

from football_pipeline.appearance import ROLE_NAMES, TEAM_NAMES
from persoon1.role_training import augment_role_tensor
from scripts.evaluate_role_extension import cohorts
from scripts.football48_ball_experiment import create_coco_view
from scripts.merge_role_heads import blend_role_states


def test_role_cohorts_do_not_misreport_new_rare_photos_as_match_crops():
    rows = [
        {"id": str(i), "origin": origin}
        for i, origin in enumerate(["retained_v1", "new_masked_match_val", "new_rare_role_photo"])
    ]
    groups = cohorts(rows)
    assert groups["all_val"] == rows
    assert groups["new_match_val"] == [rows[1]]
    assert groups["new_rare_roles_val"] == [rows[2]]
    assert set(cohorts(rows[:1])) == {"all_val", "retained_val"}


def test_coco_view_preserves_ball_32_and_generic_person_0(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    image = source / "frame.png"
    image.write_bytes(b"fixture image bytes")
    label = source / "frame.txt"
    label.write_text("0 .5 .5 .2 .4\n1 .3 .3 .01 .01\n", encoding="utf-8")
    original = label.read_bytes()
    manifest = {"frames": [{"image": "frame.png", "label": "frame.txt", "split": "train"}]}
    names = {i: f"other_{i}" for i in range(80)}
    names.update({0: "person", 32: "sports ball"})
    output = tmp_path / "view"
    create_coco_view(source, output, manifest, names)
    assert (output / "frame.txt").read_text().splitlines() == ["0 .5 .5 .2 .4", "32 .3 .3 .01 .01"]
    assert label.read_bytes() == original
    assert (output / "frame.png").read_bytes() == image.read_bytes()
    exported = yaml.safe_load((output / "data.yaml").read_text())
    assert len(exported["names"]) == 80
    assert exported["names"][0] == "person"
    assert exported["names"][32] == "sports ball"
    with pytest.raises(ValueError, match="fresh dataset"):
        create_coco_view(source, output, manifest, names)


def test_coco_view_rejects_test_frames_before_opening_their_images(tmp_path):
    names = {i: f"other_{i}" for i in range(80)}
    names.update({0: "person", 32: "sports ball"})
    manifest = {"frames": [{"split": "test", "image": "does-not-exist.png", "label": "missing.txt"}]}
    with pytest.raises(ValueError, match="reserved"):
        create_coco_view(Path(tmp_path / "source"), tmp_path / "output", manifest, names)
    assert not (tmp_path / "output").exists()


def test_head_interpolation_matches_logits_and_retains_original_team_model():
    base = {
        "role_names": ROLE_NAMES,
        "team_names": TEAM_NAMES,
        "role_colour_scale": 8,
        "backbone": {"weight": torch.ones(2)},
        "mean": torch.zeros(3),
        "std": torch.ones(3),
        "role_head": {"weight": torch.arange(18).reshape(6, 3).float(), "bias": torch.zeros(6)},
        "team_head": {"weight": torch.ones(2, 3)},
        "team_video_hashes": ["verified-match"],
    }
    import copy

    other = copy.deepcopy(base)
    other["role_head"]["weight"] *= -2
    other["team_head"]["weight"] *= 4
    mixed = blend_role_states(base, other, 0.25)
    x = torch.tensor([[0.2, -0.1, 0.7]])
    linear = torch.nn.functional.linear
    actual = linear(x, **mixed["role_head"])
    expected = 0.75 * linear(x, **base["role_head"]) + 0.25 * linear(x, **other["role_head"])
    assert torch.allclose(actual, expected)
    assert torch.equal(mixed["team_head"]["weight"], base["team_head"]["weight"])
    assert mixed["team_video_hashes"] == base["team_video_hashes"]
    other["backbone"]["weight"][0] += 1
    with pytest.raises(ValueError, match="EXACTLY"):
        blend_role_states(base, other, 0.5)
    other = copy.deepcopy(base)
    other["role_colour_scale"] = 1
    with pytest.raises(ValueError, match="colour"):
        blend_role_states(base, other, 0.5)


def test_low_resolution_photo_transform_really_removes_detail_and_keeps_full_crop():
    checker = ((torch.arange(192)[:, None] + torch.arange(128)[None, :]) % 2).float()
    pixels = checker.expand(3, -1, -1).clone()
    assert torch.equal(augment_role_tensor(pixels, 0), pixels)
    assert torch.equal(augment_role_tensor(pixels, 1), pixels.flip(2))
    blurred = augment_role_tensor(pixels, 2)
    assert blurred.shape == pixels.shape
    assert blurred.var() < pixels.var() * 0.05
    with pytest.raises(ValueError, match="Unknown"):
        augment_role_tensor(pixels, 6)
