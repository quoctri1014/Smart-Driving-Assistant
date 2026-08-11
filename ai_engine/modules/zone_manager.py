"""
zone_manager.py
---------------
Quản lý các vùng đếm (Zone 1, Zone 2, Zone 3 ...) giống clip mẫu.
Mỗi track chỉ được đếm 1 lần cho mỗi zone (dựa vào zones_visited trong Track).
"""

from ai_engine import config
from .utils import polygon_percent_to_pixels, point_in_polygon, draw_polygon, box_bottom_center

# Bảng màu cho từng zone (BGR)
ZONE_COLORS = [
    (0, 140, 255),   # cam
    (255, 0, 200),   # tím hồng
    (0, 255, 100),   # xanh lá
    (255, 200, 0),   # xanh dương nhạt
]


class ZoneManager:
    def __init__(self, zones_percent=config.ZONES):
        self.zones_percent = zones_percent
        self.counts = {name: 0 for name in zones_percent}
        self._pixel_cache = {}
        self._cache_size = None

    def _get_pixel_zones(self, frame_w, frame_h):
        if self._cache_size != (frame_w, frame_h):
            self._pixel_cache = {
                name: polygon_percent_to_pixels(pts, frame_w, frame_h)
                for name, pts in self.zones_percent.items()
            }
            self._cache_size = (frame_w, frame_h)
        return self._pixel_cache

    def update(self, tracks, frame_w, frame_h):
        """Kiểm tra từng track xem có vừa đi vào zone nào không, cộng dồn số đếm."""
        pixel_zones = self._get_pixel_zones(frame_w, frame_h)
        current_zone_of_track = {}

        for track in tracks:
            point = box_bottom_center(track.current_box)
            for zone_name, polygon in pixel_zones.items():
                if point_in_polygon(point, polygon):
                    current_zone_of_track[track.id] = zone_name
                    if zone_name not in track.zones_visited:
                        track.zones_visited.add(zone_name)
                        self.counts[zone_name] += 1
                    break
        return current_zone_of_track

    def draw(self, frame):
        frame_h, frame_w = frame.shape[:2]
        pixel_zones = self._get_pixel_zones(frame_w, frame_h)
        for idx, (zone_name, polygon) in enumerate(pixel_zones.items()):
            color = ZONE_COLORS[idx % len(ZONE_COLORS)]
            label = f"{zone_name}: {self.counts[zone_name]}"
            draw_polygon(frame, polygon, color, label=label)
        return frame
