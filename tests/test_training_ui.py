from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from football_pipeline import training_ui as ui
from football_pipeline.contracts import PipelineError
from football_pipeline.training_workbench import TASKS


def button(app, label):
    return next(item for item in app.button if item.label == label)


@pytest.fixture
def training_app(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(ui, "ROOT", tmp_path)
    monkeypatch.setattr(ui, "training_processes", lambda: [])
    monkeypatch.setattr(ui, "jobs", lambda: [])
    monkeypatch.setattr(
        ui,
        "hardware_snapshot",
        lambda: {"ready": True, "gpus": [{"name": "Test GPU", "memory_gib": 8}]},
    )

    def launch(tasks, inputs, **limits):
        calls.append((tasks, inputs, limits))
        return tmp_path / "training-round"

    monkeypatch.setattr(ui, "launch", launch)
    app = AppTest.from_string(
        "from football_pipeline.training_ui import training_page\ntraining_page()", default_timeout=20
    ).run()
    assert not app.exception
    return app, calls


@pytest.mark.parametrize(
    ("label", "tasks"),
    [(f"Train {label.lower()}", [key]) for key, label in TASKS.items()]
    + [("Train veldmodel volledig", ["field_points", "field_lines"]), ("Alles trainen", list(TASKS))],
)
def test_frontend_requires_gpu_then_starts_selected_models_with_form_settings(training_app, label, tasks):
    app, calls = training_app
    assert button(app, label).disabled
    button(app, "Controleer deze GPU").click().run()
    assert not app.exception
    assert not button(app, label).disabled
    app.number_input[0].set_value(3)
    app.number_input[1].set_value(7)
    app.text_input(key="training_input_profile").set_value("configs/my-profile.json")
    button(app, label).click().run()
    assert not app.exception
    assert calls == [
        (tasks, {**ui.default_inputs(), "profile": "configs/my-profile.json"}, {"epochs": 3, "minutes": 7})
    ]
    assert any("Training gestart" in alert.value for alert in app.success)


def test_frontend_prevents_second_training_while_worker_is_active(training_app, monkeypatch):
    app, calls = training_app
    monkeypatch.setattr(ui, "training_processes", lambda: [{"pid": 42}])
    button(app, "Controleer deze GPU").click().run()
    assert not app.exception
    assert button(app, "Alles trainen").disabled
    assert all(button(app, f"Train {label.lower()}").disabled for label in TASKS.values())
    assert not calls


def test_frontend_explains_invalid_training_inputs_without_crashing(training_app, monkeypatch):
    app, _ = training_app

    def fail(*args, **kwargs):
        raise PipelineError("Trainingsbeelden ontbreken")

    monkeypatch.setattr(ui, "launch", fail)
    button(app, "Controleer deze GPU").click().run()
    button(app, "Train spelers").click().run()
    assert not app.exception
    assert any("Trainingsbeelden ontbreken" in alert.value for alert in app.error)


def test_training_page_is_reachable_from_main_sidebar(monkeypatch):
    monkeypatch.setattr(ui, "training_processes", lambda: [])
    monkeypatch.setattr(ui, "jobs", lambda: [])
    entrypoint = Path(__file__).resolve().parents[1] / "streamlit_app.py"
    app = AppTest.from_file(str(entrypoint), default_timeout=40)
    app.session_state["workspace_view"] = "Modellen trainen"
    app.run()
    assert not app.exception
    assert any(title.value == "Modellen trainen" for title in app.title)
    assert button(app, "Alles trainen").disabled
