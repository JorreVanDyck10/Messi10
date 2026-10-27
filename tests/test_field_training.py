import io
import json
import sys
import types
import zipfile
from pathlib import Path

import numpy as np
import pytest
import torch

from football_pipeline.contracts import sha256_file, write_json
from football_pipeline.field_data import (
    CorpusBudget,
    download,
    extract_archive,
    frame_signature,
    identify_match,
    match_split,
    near_duplicate,
    prepare_frames,
)
from football_pipeline.field_learning import (
    atomic_torch_save,
    clip_provider_lines,
    dataset_index,
    masked_heatmap_loss,
    publish_epoch_checkpoint,
    reprojection_metrics,
    run_epoch,
    validate_labels,
)
from football_pipeline.field_model_spec import RELEASE_WEIGHTS, validate_runtime_models


def test_reference_error_includes_visible_lines_when_virtual_endpoints_cross_horizon(monkeypatch):
    from football_pipeline.automatic_calibration import transform

    module = types.ModuleType("sn_calibration.src.soccerpitch")
    module.SoccerPitch = lambda: types.SimpleNamespace(
        line_extremities={"Side line top": np.array([[-52.5, -34, 0], [52.5, -34, 0]])}
    )
    monkeypatch.setitem(sys.modules, "sn_calibration.src.soccerpitch", module)
    inverse = np.array([[1000, 0, -600], [0, 200, 30], [1, 0, -0.5]], float)
    xy = transform([[0.7, 0], [0.9, 0]], inverse)
    labels = {"Side line top": [{"x": x / 1000, "y": y / 500} for x, y in xy]}
    state = {"status": "valid", "homography": np.linalg.inv(inverse).tolist()}
    result = reprojection_metrics({"image_size": [1000, 500]}, labels, {}, state=state)
    assert len(result["errors_px"]) == 2
    assert max(result["errors_px"]) < 1e-8
    labels["Side line top"][0]["y"] += 0.1
    changed = reprojection_metrics({"image_size": [1000, 500]}, labels, {}, state=state)
    assert max(changed["errors_px"]) > 40


class Response(io.BytesIO):
    def __init__(self, content, status=200, headers=None):
        super().__init__(content)
        self.status = status
        self.headers = headers or {"Content-Length": str(len(content)), "ETag": '"fixed"'}


def test_download_resumes_and_rehashes_completed_files(tmp_path, monkeypatch):
    body = b"complete research dataset"
    target = tmp_path / "data.zip"
    target.with_suffix(".zip.part").write_bytes(body[:8])
    write_json(
        target.with_suffix(".zip.download.json"), {"url": "https://example.test/data", "etag": '"fixed"'}
    )

    def open_request(request, timeout):
        assert request.headers["Range"] == "bytes=8-"
        assert request.headers["If-range"] == '"fixed"'
        return Response(
            body[8:],
            206,
            {"Content-Length": str(len(body) - 8), "Content-Range": f"bytes 8-{len(body) - 1}/{len(body)}"},
        )

    monkeypatch.setattr("urllib.request.urlopen", open_request)
    budget = CorpusBudget(tmp_path, 1024**2)
    budget.start_tracking()
    result = download("https://example.test/data", target, budget, len(body))
    assert target.read_bytes() == body
    assert result["sha256"] == sha256_file(target)
    assert budget.used() == sum(p.stat().st_size for p in tmp_path.iterdir() if p.is_file())
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: pytest.fail("Completed download repeated"))
    assert download("https://example.test/data", target, budget) == result
    target.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash"):
        download("https://example.test/data", target, budget)


def test_budget_rejects_before_download_writes(tmp_path, monkeypatch):
    target = tmp_path / "data.zip"
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: Response(b"x" * 200))
    with pytest.raises(ValueError, match="budget"):
        download("https://example.test/data", target, CorpusBudget(tmp_path, 100))
    assert not target.exists()


def test_complete_partial_download_publishes_without_request(tmp_path, monkeypatch):
    target = tmp_path / "data.zip"
    partial = target.with_suffix(".zip.part")
    partial.write_bytes(b"complete")
    write_json(target.with_suffix(".zip.download.json"), {"url": "https://example.test/data"})
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: pytest.fail("Unexpected network request"))
    result = download("https://example.test/data", target, CorpusBudget(tmp_path), 8, sha256_file(partial))
    assert result["status"] == "complete" and target.read_bytes() == b"complete"


def test_exclusive_budget_tracking_accounts_atomic_metadata_and_refuses_overflow(tmp_path):
    budget = CorpusBudget(tmp_path, 200)
    budget.start_tracking()
    budget.write_json(tmp_path / "metadata.json", {"status": "ready"})
    assert budget.used() == (tmp_path / "metadata.json").stat().st_size
    with pytest.raises(ValueError, match="budget"):
        budget.write_json(tmp_path / "large.json", {"data": "x" * 200})


def test_zip_rejects_traversal_and_changed_extraction(tmp_path):
    archive = tmp_path / "source.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../escape.txt", "unsafe")
    with pytest.raises(ValueError, match="Unsafe"):
        extract_archive(archive, tmp_path / "dataset", CorpusBudget(tmp_path))
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("train/example.json", "{}")
    extract_archive(archive, tmp_path / "dataset", CorpusBudget(tmp_path))
    (tmp_path / "dataset/train/example.json").write_text("changed")
    with pytest.raises(ValueError, match="changed"):
        extract_archive(archive, tmp_path / "dataset", CorpusBudget(tmp_path))


def test_mask_removes_invisible_error_and_gradient_before_reduction():
    prediction = torch.tensor([[[[3.0]], [[100.0]]]], requires_grad=True)
    target = torch.zeros_like(prediction)
    mask = torch.tensor([[1.0, 0.0]])
    loss = masked_heatmap_loss(prediction, target, mask)
    assert loss.item() == 9.0
    loss.backward()
    assert prediction.grad.flatten().tolist() == [6.0, 0.0]
    assert masked_heatmap_loss(prediction, target, torch.zeros_like(mask)).item() == 0.0


def test_interrupted_checkpoint_publication_preserves_previous_committed_epoch(tmp_path, monkeypatch):
    previous = tmp_path / "keypoints-resume-001.pt"
    fresh = tmp_path / "keypoints-resume-002.pt"
    report_path = tmp_path / "report.json"
    atomic_torch_save({"epoch": 0, "weight": torch.tensor([1.0])}, previous)
    report = {"models": {"keypoints": {"last_path": str(previous), "last_sha256": sha256_file(previous)}}}
    write_json(report_path, report)

    def fail(*args):
        raise OSError("simulated interruption before report publication")

    monkeypatch.setattr("football_pipeline.field_learning.write_json", fail)
    with pytest.raises(OSError, match="simulated"):
        publish_epoch_checkpoint(
            report_path, report, "keypoints", {}, {"epoch": 1, "weight": torch.tensor([2.0])}, fresh
        )
    saved = json.loads(report_path.read_text())
    assert saved == report
    assert sha256_file(previous) == saved["models"]["keypoints"]["last_sha256"]
    assert torch.load(previous, weights_only=True)["epoch"] == 0
    monkeypatch.setattr("football_pipeline.field_learning.write_json", write_json)
    record = {"history": [{"epoch": 1}]}
    committed = publish_epoch_checkpoint(
        report_path, report, "keypoints", record, {"epoch": 1, "weight": torch.tensor([2.0])}, fresh
    )
    record["history"].append({"epoch": 2})
    assert committed["models"]["keypoints"]["history"] == [{"epoch": 1}]
    assert committed["models"]["keypoints"]["last_path"] == str(fresh.resolve())
    assert torch.load(fresh, weights_only=True)["epoch"] == 1


@pytest.mark.parametrize("coordinate", [-0.01, 1.01, float("nan"), float("inf"), "0.5"])
def test_invalid_normalized_labels_rejected(coordinate):
    with pytest.raises(ValueError):
        validate_labels({"Middle line": [{"x": coordinate, "y": 0.5}]})


def test_label_roundoff_is_clamped_without_changing_raw_labels():
    original = {"Middle line": [{"x": 1.0000052452087402, "y": -0.000001}]}
    normalized = validate_labels(original)
    assert normalized["Middle line"] == [{"x": 1.0, "y": 0.0}]
    assert original["Middle line"][0]["x"] > 1
    assert original["Middle line"][0]["y"] < 0


def test_provider_border_clipping_preserves_line_geometry_without_changing_raw_labels():
    source = {"Middle line": [{"x": 0.4, "y": 0.0}, {"x": 0.6, "y": 1.002}]}
    clipped = clip_provider_lines(source)
    assert clipped["Middle line"][-1]["y"] == 1.0
    assert clipped["Middle line"][-1]["x"] == pytest.approx(0.4 + 0.2 / 1.002)
    assert source["Middle line"][-1]["y"] == 1.002
    with pytest.raises(ValueError, match="bounded"):
        clip_provider_lines({"Middle line": [{"x": 0.4, "y": 0.0}, {"x": 0.6, "y": 1.1}]})


def test_head_only_training_keeps_pretrained_normalization_statistics_frozen():
    class TinyNetwork(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.features = torch.nn.Sequential(torch.nn.Conv2d(3, 4, 1), torch.nn.BatchNorm2d(4))
            self.head = torch.nn.Sequential(
                torch.nn.Sequential(
                    torch.nn.Conv2d(4, 4, 1),
                    torch.nn.BatchNorm2d(4),
                    torch.nn.ReLU(),
                    torch.nn.Conv2d(4, 2, 1),
                    torch.nn.Softmax(dim=1),
                )
            )

        def forward(self, image):
            return self.head(self.features(image))

    model = TinyNetwork()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    for parameter in model.head[0][3].parameters():
        parameter.requires_grad_(True)
    before = model.features[1].running_mean.clone()
    last = model.head[0][3].weight.detach().clone()
    optimizer = torch.optim.Adam(model.head[0][3].parameters(), lr=0.01)
    scaler = torch.amp.GradScaler("cpu", enabled=False)
    target = torch.zeros(1, 2, 4, 4)
    target[:, 0] = 1
    run_epoch(
        model,
        [(torch.ones(1, 3, 4, 4), target, torch.ones(1, 2))],
        torch.device("cpu"),
        optimizer,
        scaler,
        frozen_features=True,
    )
    assert torch.equal(model.features[1].running_mean, before)
    assert not torch.equal(model.head[0][3].weight, last)


def test_duplicate_and_compilation_selection():
    image = np.random.default_rng(42).integers(0, 255, (90, 160, 3), dtype=np.uint8)
    assert near_duplicate(frame_signature(image), [frame_signature(image.copy())])
    other = np.random.default_rng(99).integers(0, 255, image.shape, dtype=np.uint8)
    assert not near_duplicate(frame_signature(other), [frame_signature(image)])
    assert identify_match("Top 10 goals - highlights") is None
    match = identify_match("France v Argentina | Extended highlights")
    assert match and match_split(match) == match_split(match)


def test_frame_preparation_spacing_provenance_and_resume(tmp_path, monkeypatch):
    import cv2

    source = tmp_path / "video.mp4"
    source.write_bytes(b"test source")
    write_json(
        tmp_path / "highlight-inventory.json",
        {
            "videos": [
                {
                    "id": "example",
                    "status": "complete",
                    "file": source.name,
                    "sha256": sha256_file(source),
                    "url": "https://example.test/video",
                    "match_id": "match1",
                    "split": "train",
                }
            ]
        },
    )

    class Capture:
        def get(self, property_id):
            return {cv2.CAP_PROP_FPS: 10, cv2.CAP_PROP_FRAME_WIDTH: 160, cv2.CAP_PROP_FRAME_HEIGHT: 96}[
                property_id
            ]

        def release(self):
            pass

    def frames(*args):
        rng = np.random.default_rng(42)
        for index in range(0, 61, 5):
            gray = rng.integers(30, 80, (96, 160, 1), dtype=np.uint8)
            yield index, np.repeat(gray, 3, axis=2)

    monkeypatch.setattr(cv2, "VideoCapture", lambda path: Capture())
    monkeypatch.setattr("football_pipeline.field_data.sampled_frames", frames)
    prepare_frames(tmp_path, CorpusBudget(tmp_path), maximum_per_video=3, ffmpeg="unused")
    result = json.loads((tmp_path / "frames/example/manifest.json").read_text())
    assert [f["timestamp_s"] for f in result["frames"]] == [0.0, 2.0, 4.0]
    assert all(not f["training_eligible"] for f in result["frames"])
    monkeypatch.setattr("football_pipeline.field_data.sampled_frames", lambda *a: pytest.fail("Cache missed"))
    prepare_frames(tmp_path, CorpusBudget(tmp_path), ffmpeg="unused")


def make_dataset(tmp_path):
    for split in ("train", "valid"):
        root = tmp_path / split
        root.mkdir()
        (root / "main.jpg").write_bytes(split.encode())
        (root / "replay.jpg").write_bytes(b"replay")
        for name in ("main", "replay"):
            write_json(root / (name + ".json"), {"Middle line": [{"x": 0.2, "y": 0.3}, {"x": 0.4, "y": 0.5}]})
        write_json(
            root / "match_info.json",
            {
                "main.jpg": {"ms_time": 100, "replay_time": 100},
                "replay.jpg": {"ms_time": 200, "replay_time": 100},
            },
        )


def test_both_networks_use_same_windows_safe_main_camera_index(tmp_path):
    make_dataset(tmp_path)
    index = dataset_index(tmp_path)
    assert len(index["frames"]) == 2
    assert all(Path(row["image"]).name == "main.jpg" for row in index["frames"])
    assert {row["split"] for row in index["frames"]} == {"train", "valid"}
    assert index["pretraining_overlap"]
    (tmp_path / "valid/main.jpg").write_bytes(b"train")
    with pytest.raises(ValueError, match="duplicate"):
        dataset_index(tmp_path)


def test_match_overlap_rejected_even_when_images_differ(tmp_path):
    make_dataset(tmp_path)
    for split in ("train", "valid"):
        path = tmp_path / split / "match_info.json"
        info = json.loads(path.read_text())
        info["main.jpg"].update(league="example", season="2026", date="2026-10-16", match="A - B")
        write_json(path, info)
    with pytest.raises(ValueError, match="Same match"):
        dataset_index(tmp_path)


def test_finetuned_runtime_requires_matching_completed_report(tmp_path):
    report = {"status": "complete", "dataset_fingerprint": "a" * 64, "is_smoke_test": True, "models": {}}
    runtime = {"models": {}}
    report_path = tmp_path / "report.json"
    for role in ("keypoints", "lines"):
        weights = tmp_path / (role + ".pt")
        weights.write_bytes(role.encode())
        model = {
            "kind": "finetuned",
            "name": role,
            "path": str(weights),
            "sha256": sha256_file(weights),
            "base_model": RELEASE_WEIGHTS[role],
            "dataset_fingerprint": "a" * 64,
            "training_report": str(report_path),
            "is_smoke_test": True,
        }
        report["models"][role] = {"status": "complete", "sha256": model["sha256"]}
        runtime["models"][role] = model
        runtime["weights_keypoints" if role == "keypoints" else "weights_lines"] = str(weights)
    write_json(report_path, report)
    for model in runtime["models"].values():
        model["training_report_sha256"] = sha256_file(report_path)
    validate_runtime_models(runtime)
    report["status"] = "running"
    write_json(report_path, report)
    with pytest.raises(ValueError, match="report changed"):
        validate_runtime_models(runtime)
