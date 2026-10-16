import pytest
import torch
from streamlit.testing.v1 import AppTest

from football_pipeline.contracts import write_json
from football_pipeline.video import ROOT


@pytest.mark.parametrize("cuda_available", [False, True])
@pytest.mark.parametrize("role", ["player", "person"])
def test_player_app_checks_runtime_and_preserves_automatic_tracking_limit(
    demo_fixture, model_manifest, tmp_path, monkeypatch, cuda_available, role
):
    profile, manifest = model_manifest
    manifest["models"][0]["device"] = "0"
    manifest["models"][0]["class_mapping"] = {"0": role}
    manifest["models"][0]["expected_names"] = {"0": role}
    write_json(profile, manifest)
    runtime = tmp_path / "field-runtime.json"
    write_json(
        runtime,
        {
            "weights_keypoints": manifest["models"][0]["weights"],
            "weights_lines": manifest["models"][0]["weights"],
        },
    )
    monkeypatch.setenv("FOOTBALL_MODELS", str(profile))
    monkeypatch.setenv("FOOTBALL_FIELD_RUNTIME", str(runtime))
    monkeypatch.setattr(torch.cuda, "is_available", lambda: cuda_available)
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 1 if cuda_available else 0)
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    app.file_uploader(key="video_upload").set_value(
        ("synthetic-runtime-check.mp4", demo_fixture["video"].read_bytes(), "video/mp4")
    ).run()
    app.get("button_group")[0].set_value("Automatische veldkalibratie").run()
    assert not app.exception
    if not cuda_available:
        assert any("CUDA-GPU" in error.value and "-Device cpu" in error.value for error in app.error)
        assert not any(button.key == "process" for button in app.button)
    else:
        assert not app.error
        app.text_input(key="field_source").set_value("Synthetic software test")
        app.text_input(key="field_usage").set_value("Synthetic software test").run()
        assert not app.button(key="process").disabled
        assert app.checkbox(key="tracking").disabled
        assert any(("speler" if role == "player" else "persoon") in caption.value for caption in app.caption)
