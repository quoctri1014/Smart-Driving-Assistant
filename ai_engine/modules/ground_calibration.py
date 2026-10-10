"""Map road contact points to meters using measured ground-plane correspondences.

Image points are normalized to [0, 1], so calibration survives frame resizing.
Only valid for a fixed camera, a planar road and the calibrated polygon.
"""
from dataclasses import dataclass
import cv2
import numpy as np


@dataclass
class GroundCalibration:
    image_points: list
    ground_points_m: list

    def __post_init__(self):
        source = np.asarray(self.image_points, dtype=np.float64)
        target = np.asarray(self.ground_points_m, dtype=np.float64)
        if source.shape != (4, 2) or target.shape != (4, 2):
            raise ValueError("Four corresponding image and measured ground points are required")
        if not np.isfinite(source).all() or not np.isfinite(target).all():
            raise ValueError("Calibration points must be finite")
        if (source < 0).any() or (source > 1).any():
            raise ValueError("Image points must be normalized to [0, 1]")
        for points in (source, target):
            contour = points.astype(np.float32)
            if not cv2.isContourConvex(contour) or cv2.contourArea(contour) < 1e-8:
                raise ValueError("Points must form an ordered convex quadrilateral")
        self._polygon = source.astype(np.float32)
        self._matrix = cv2.getPerspectiveTransform(source.astype(np.float32), target.astype(np.float32))
        if not np.isfinite(self._matrix).all() or abs(np.linalg.det(self._matrix)) < 1e-10:
            raise ValueError("Degenerate calibration")

    def project(self, box, frame_width, frame_height):
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError("Invalid frame dimensions")
        x1, y1, x2, y2 = box
        point = ((x1 + x2) / (2 * frame_width), y2 / frame_height)
        if not np.isfinite(point).all() or cv2.pointPolygonTest(self._polygon, point, False) < 0:
            return None
        projected = self._matrix @ np.array([*point, 1.0])
        if abs(projected[2]) < 1e-10:
            return None
        result = projected[:2] / projected[2]
        return tuple(result) if np.isfinite(result).all() else None
