"""Meet achtergrondbeweging voor cameracompensatie van tracks, onafhankelijk van veldpuntherkenning."""

import cv2
import numpy as np

from .geometry import valid_box


def warp_xyah(tracks, matrix):
    """Transform XYAH Kalman states without rotating aspect into pixel height.

    ByteTrack's generic GMC uses four XY pairs, but its state is actually
    x/y/aspect/height and their velocities. Use the transformed box envelope
    and its Jacobian; pure zoom must leave aspect unchanged.
    """
    rotation, translation = np.asarray(matrix, float)[:, :2], np.asarray(matrix, float)[:, 2]
    u, v = np.abs(rotation[0])
    r, s = np.abs(rotation[1])
    determinant = u * s - v * r
    for track in tracks:
        mean = track.mean.copy()
        aspect, height, aspect_velocity, height_velocity = mean[[2, 3, 6, 7]]
        factor = r * aspect + s
        derivative = determinant / factor**2
        jacobian = np.zeros((8, 8))
        jacobian[:2, :2] = jacobian[4:6, 4:6] = rotation
        jacobian[2, 2] = derivative
        jacobian[3, 2], jacobian[3, 3] = height * r, factor
        jacobian[6, 2], jacobian[6, 6] = -2 * r * determinant / factor**3 * aspect_velocity, derivative
        jacobian[7, 2], jacobian[7, 3] = r * height_velocity, r * aspect_velocity
        jacobian[7, 6], jacobian[7, 7] = r * height, factor
        mean[:2] = rotation @ mean[:2] + translation
        mean[4:6] = rotation @ mean[4:6]
        mean[2], mean[3] = (u * aspect + v) / factor, height * factor
        mean[6] = derivative * aspect_velocity
        mean[7] = factor * height_velocity + height * r * aspect_velocity
        track.mean = mean
        track.covariance = jacobian @ track.covariance @ jacobian.T


class BackgroundMotion:
    def __init__(self):
        self.previous = None
        self.mask = None
        self.histogram = None
        self.matrix = np.eye(2, 3)
        self.state = {}

    def apply(self, image, detections=None):
        # ByteTrack calls this between Kalman prediction and association.
        return self.matrix

    def reset_params(self):
        pass  # Our frame history is managed by measure(), not ByteTrack.reset().

    def measure(self, frame, detections):
        height, width = frame.shape[:2]
        scale = min(1.0, 960 / width)
        size = (round(width * scale), round(height * scale))
        small = cv2.resize(frame, size)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        histogram = cv2.normalize(
            cv2.calcHist([small], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3), None
        ).flatten()
        mask = np.full(gray.shape, 255, np.uint8)
        for detection in detections:
            if valid_box(detection, (width, height)):
                x1, y1, x2, y2 = np.rint(np.asarray(detection.bbox_xyxy) * scale).astype(int)
                cv2.rectangle(mask, (max(0, x1 - 5), max(0, y1 - 5)), (x2 + 5, y2 + 5), 0, -1)
        self.matrix = np.eye(2, 3)
        self.state = {"status": "initial", "reset_tracks": False}
        try:
            if self.previous is None:
                return self.state
            if gray.shape != self.previous.shape:
                raise ValueError("frame_size_changed")
            distance = float(cv2.compareHist(self.histogram, histogram, cv2.HISTCMP_BHATTACHARYYA))
            difference = float(np.mean(cv2.absdiff(self.previous, gray)))
            self.state.update(histogram_distance=distance, mean_difference=difference)
            if distance > 0.55:
                raise ValueError("camera_cut")
            if difference < 0.5:
                self.state["status"] = "stationary"
                return self.state
            points = cv2.goodFeaturesToTrack(
                self.previous, mask=self.mask, maxCorners=600, qualityLevel=0.01, minDistance=8
            )
            if points is None or len(points) < 20:
                raise ValueError("insufficient_background")
            lk = {"winSize": (31, 31), "maxLevel": 4}
            current, forward, _ = cv2.calcOpticalFlowPyrLK(self.previous, gray, points, None, **lk)
            if current is None or forward is None:
                raise ValueError("motion_unavailable")
            backward, status, _ = cv2.calcOpticalFlowPyrLK(gray, self.previous, current, None, **lk)
            if backward is None or status is None:
                raise ValueError("motion_unavailable")
            a, b = points.reshape(-1, 2), current.reshape(-1, 2)
            valid = (
                forward.ravel().astype(bool)
                & status.ravel().astype(bool)
                & np.isfinite(b).all(axis=1)
                & (np.linalg.norm(points - backward, axis=2).ravel() <= 1.5)
                & (b >= 0).all(axis=1)
                & (b < size).all(axis=1)
            )
            a, b = a[valid], b[valid]
            if len(a):
                on_background = mask[b[:, 1].astype(int), b[:, 0].astype(int)] > 0
                a, b = a[on_background], b[on_background]
            if len(a) < 20:
                raise ValueError("insufficient_background")
            cv2.setRNGSeed(0)
            matrix, inliers = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC, ransacReprojThreshold=3)
            if matrix is None or inliers is None or not np.isfinite(matrix).all():
                raise ValueError("motion_unavailable")
            good = inliers.ravel().astype(bool)
            self.state.update(matches=len(a), inliers=int(good.sum()), inlier_ratio=float(good.mean()))
            if good.sum() < 20 or good.mean() < 0.6:
                raise ValueError("inconsistent_motion")
            spread = cv2.contourArea(cv2.convexHull(a[good])) / np.prod(size)
            residuals = np.linalg.norm(a[good] @ matrix[:, :2].T + matrix[:, 2] - b[good], axis=1)
            zoom = float(np.linalg.norm(matrix[:, 0]))
            angle = float(np.degrees(np.arctan2(matrix[1, 0], matrix[0, 0])))
            self.state.update(zoom=zoom, rotation_degrees=angle, median_error_px=float(np.median(residuals)))
            if (
                spread < 0.05
                or np.median(residuals) > 1.5
                or not 0.8 <= zoom <= 1.25
                or abs(angle) > 15
                or np.linalg.norm(matrix[:, 2]) > np.hypot(*size) * 0.35
            ):
                raise ValueError("unreliable_motion")
            matrix[:, 2] /= scale
            self.matrix = matrix
            self.state.update(status="compensated", matrix=matrix.tolist())
        except (ValueError, cv2.error) as exc:
            self.state.update(
                status=str(exc) if isinstance(exc, ValueError) else "motion_unavailable", reset_tracks=True
            )
        finally:
            self.previous, self.mask, self.histogram = gray, mask, histogram
        return self.state
