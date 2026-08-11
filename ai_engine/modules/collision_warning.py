"""
collision_warning.py
---------------------
Cảnh báo "đang tiến lại gần quá nhanh" (giống demo dashcam trong clip mẫu).

Nguyên lý (không cần camera đã hiệu chỉnh/calibrate, không cần biết khoảng
cách thật): nếu một xe phía trước, nằm trong "làn đường" quan sát, có chiều
cao bounding box TĂNG NHANH qua các khung hình liên tiếp => xe đó đang lại
gần với tốc độ cao (hoặc mình đang lại gần nó nhanh) => cảnh báo.

Đây là ước lượng heuristic, đủ dùng cho demo / cảnh báo tương đối,
không thay thế được radar/lidar cho hệ thống ADAS thực tế.
"""

from ai_engine import config
from .utils import polygon_percent_to_pixels, point_in_polygon, draw_polygon, box_bottom_center


class CollisionWarning:
    def __init__(self, lane_polygon_percent=config.COLLISION_LANE_POLYGON):
        self.lane_polygon_percent = lane_polygon_percent
        self._pixel_cache = None
        self._cache_size = None

    def _get_lane_pixels(self, frame_w, frame_h):
        if self._cache_size != (frame_w, frame_h):
            self._pixel_cache = polygon_percent_to_pixels(
                self.lane_polygon_percent, frame_w, frame_h)
            self._cache_size = (frame_w, frame_h)
        return self._pixel_cache

    def check(self, tracks, frame_w, frame_h):
        """
        Trả về list các track đang trong vùng làn đường VÀ có tốc độ tăng
        kích thước hộp vượt ngưỡng cảnh báo.
        """
        lane_pixels = self._get_lane_pixels(frame_w, frame_h)
        warnings = []
        for track in tracks:
            if track.cls_name not in ("car", "truck", "bus", "motorbike"):
                continue
            point = box_bottom_center(track.current_box)
            if not point_in_polygon(point, lane_pixels):
                continue
            if len(track.boxes) < config.COLLISION_MIN_TRACK_LEN:
                continue
            rate = track.growth_rate(config.COLLISION_MIN_TRACK_LEN)
            if rate > config.COLLISION_GROWTH_RATE_THRESHOLD:
                warnings.append((track, rate))
        return warnings

    def draw_lane(self, frame):
        frame_h, frame_w = frame.shape[:2]
        lane_pixels = self._get_lane_pixels(frame_w, frame_h)
        draw_polygon(frame, lane_pixels, (255, 255, 255), label=None, alpha=0.08)
        return frame
