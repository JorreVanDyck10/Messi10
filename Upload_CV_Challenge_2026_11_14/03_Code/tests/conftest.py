import pytest

from football_pipeline.contracts import VideoMetadata
from football_pipeline.demo import default_points, generate_demo
from football_pipeline.geometry import create_calibration


@pytest.fixture
def video_metadata():
    return VideoMetadata("fixture.mp4", "abc", 640, 360, 25, 1, 100, "h264", 4)


@pytest.fixture
def calibration(video_metadata):
    points = default_points(640, 360)
    for p in points:
        p["x"], p["y"] = 40 + p["u"] * 560, 40 + p["v"] * 280
    result = create_calibration(video_metadata, points)
    result.review = {
        "approved": True,
        "reviewer": "test",
        "static_camera_confirmed": True,
        "temporal_frames": [0, 50, 99],
        "source": "synthetic",
        "usage": "test",
    }
    return result


@pytest.fixture(scope="session")
def demo_fixture(tmp_path_factory):
    return generate_demo(tmp_path_factory.mktemp("demo"))


@pytest.fixture
def model_manifest(tmp_path):
    from football_pipeline.contracts import write_json

    weights = tmp_path / "identity.pt"
    weights.write_bytes(b"fake weights for manifest validation only")
    manifest = {
        "schema_version": 1,
        "models": [
            {
                "model_id": "p",
                "weights": str(weights),
                "class_mapping": {"0": "player"},
                "expected_names": {"0": "player"},
                "imgsz": 640,
                "confidence": 0.1,
                "iou": 0.7,
                "device": "cpu",
            }
        ],
    }
    path = tmp_path / "models.json"
    write_json(path, manifest)
    return path, manifest
