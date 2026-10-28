from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from football_pipeline.contracts import Detection
from football_pipeline.tracking import ByteTrackAdapter, Trajectories, load_tracker_config
from football_pipeline.tracking_motion import warp_xyah
from football_pipeline.video import ROOT


def background():
    noise = np.random.default_rng(42).integers(30, 180, (360, 640, 3), dtype=np.uint8)
    return cv2.GaussianBlur(noise, (5, 5), 0)


def view(source, index, *, shift=0, zoom=1, confidence=0.9, field=True):
    matrix = np.array([[zoom, 0, shift], [0, zoom, 0]], float)
    frame = cv2.warpAffine(source, matrix, (640, 360), borderMode=cv2.BORDER_REFLECT)
    box = np.array([230, 120, 260, 200], float) * zoom + [shift, 0, shift, 0]
    d = Detection(
        str(index),
        "fixture",
        0,
        "player",
        box.tolist(),
        confidence,
        field_position=[0.4 + index * 0.001, 0.5] if field else None,
        projection_status="valid" if field else "calibration_unavailable",
    )
    x1, y1, x2, y2 = box.astype(int)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (10, 10, 230), -1)
    return frame, d


@pytest.mark.parametrize("shift,zoom", [(35, 1), (15, 1.04), (-25, 0.97)])
def test_compensation_preserves_ids_through_pan_zoom_and_field_dropout(shift, zoom):
    tracker = ByteTrackAdapter(load_tracker_config(ROOT / "configs/bytetrack.yaml"), 25, camera_motion=True)
    source = background()
    histories = Trajectories(25)
    for index in range(4):
        frame, d = view(
            source,
            index,
            shift=shift * index,
            zoom=zoom**index,
            confidence=0.15 if index == 2 else 0.9,
            field=index != 2,
        )
        tracker.update([d], index, (640, 360), frame=frame)
        histories.update([d], index)
        assert d.track_id == 1
        if index:
            assert tracker.motion.state["status"] == "compensated"
            assert tracker.motion.state["inlier_ratio"] >= 0.6
        if index == 2:
            assert d.field_position is None
    assert [(a[0], b[0]) for a, b in histories.segments(1)] == [(0, 1)]


def test_camera_cuts_reset_ids_without_reusing_numbers_or_joining_trajectories():
    tracker = ByteTrackAdapter(load_tracker_config(ROOT / "configs/bytetrack.yaml"), 25, camera_motion=True)
    frame, d = view(background(), 0)
    tracker.update([d], 0, (640, 360), frame=frame)
    assert d.track_id == 1
    cut = np.full_like(frame, (20, 180, 20))
    _, second = view(background(), 1)
    tracker.update([second], 1, (640, 360), frame=cut)
    assert tracker.motion.state["status"] == "camera_cut"
    assert second.track_id == 2
    _, third = view(background(), 2)
    tracker.update([third], 2, (640, 360), frame=cut)
    assert third.track_id == 2


def test_unmeasured_motion_resets_and_never_tracks_nonplayers_or_offfield_players():
    tracker = ByteTrackAdapter(load_tracker_config(ROOT / "configs/bytetrack.yaml"), 25, camera_motion=True)
    blank = np.full((360, 640, 3), 100, np.uint8)
    _, d = view(background(), 0)
    tracker.update([d], 0, (640, 360), frame=blank)
    _, second = view(background(), 1)
    _, referee = view(background(), 1)
    referee.semantic_class = "referee"
    _, outside = view(background(), 1)
    outside.projection_status, outside.field_position = "outside_field", None
    tracker.update([second, referee, outside], 1, (640, 360), frame=blank + 5)
    assert tracker.motion.state["reset_tracks"]
    assert second.track_id == 2
    assert referee.track_id is outside.track_id is None


def test_zoom_preserves_aspect_and_rotation_uses_a_box_envelope():
    mean = np.array([320.0, 180.0, 0.25, 120.0, 3.0, -2.0, 0.01, 1.0])
    track = SimpleNamespace(mean=mean.copy(), covariance=np.eye(8))
    warp_xyah([track], np.array([[1.1, 0.0, 12.0], [0.0, 1.1, -4.0]]))
    assert track.mean[2] == pytest.approx(0.25)
    assert track.mean[3] == pytest.approx(132.0)
    assert track.mean[6] == pytest.approx(0.01)
    matrix = cv2.getRotationMatrix2D((320, 180), 0.17, 1.005)
    track = SimpleNamespace(mean=mean.copy(), covariance=np.eye(8))
    warp_xyah([track], matrix)
    corners = np.array([[305.0, 120.0], [335.0, 120.0], [335.0, 240.0], [305.0, 240.0]])
    transformed = corners @ matrix[:, :2].T + matrix[:, 2]
    extent = np.ptp(transformed, axis=0)
    assert track.mean[2:4] == pytest.approx([extent[0] / extent[1], extent[1]])
    assert np.linalg.eigvalsh(track.covariance).min() > 0
    numerical = np.empty((8, 8))
    for axis in range(8):
        offset = np.eye(8)[axis] * 1e-5
        plus = SimpleNamespace(mean=mean + offset, covariance=np.eye(8))
        minus = SimpleNamespace(mean=mean - offset, covariance=np.eye(8))
        warp_xyah([plus], matrix)
        warp_xyah([minus], matrix)
        numerical[:, axis] = (plus.mean - minus.mean) / 2e-5
    assert np.allclose(track.covariance, numerical @ numerical.T, atol=1e-6)


@pytest.mark.parametrize("angle", [-0.17, 0.17])
def test_player_id_survives_small_camera_rotation_and_zoom(angle):
    tracker = ByteTrackAdapter(load_tracker_config(ROOT / "configs/bytetrack.yaml"), 25, camera_motion=True)
    source = background()
    corners = np.array([[230.0, 120.0], [260.0, 120.0], [260.0, 200.0], [230.0, 200.0]])
    for index in range(8):
        matrix = cv2.getRotationMatrix2D((320, 180), angle * index, 1.005**index)
        matrix[:, 2] += [8 * index, 0]
        frame = cv2.warpAffine(source, matrix, (640, 360), borderMode=cv2.BORDER_REFLECT)
        transformed = corners @ matrix[:, :2].T + matrix[:, 2]
        box = [*transformed.min(0), *transformed.max(0)]
        detection = Detection(
            str(index), "fixture", 0, "player", box, 0.9, field_position=[0.4, 0.5], projection_status="valid"
        )
        tracker.update([detection], index, (640, 360), frame=frame)
        assert detection.track_id == 1
        assert tracker.tracker.tracked_stracks[0].mean[2] > 0.3
