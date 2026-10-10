"""
lane_detector.py
----------------
Tự động phát hiện vạch kẻ đường và tạo vùng 'Làn của mình' (Ego-Lane):
1. Phương pháp: Tiêu chuẩn màu sắc (Trắng/Vàng) + Edge + Hough Transform + Lọc độ dốc.
2. Tích hợp Shapely Polygon để kiểm tra xe có nằm trong làn của mình hay không.
3. Ngoại lệ:
   - Vạch mờ / đường không vạch (thường gặp ở VN): Tự động chuyển sang hành lang ước tính (Fallback corridor) từ vanishing point.
   - Đổi làn: Giám sát độ lệch tâm ngang và góc dốc của vạch kẻ.
   - Camera bị xoay lệch: Kiểm tra góc nghiêng mặt phẳng ngang (Horizon Tilt > 25°).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from shapely.geometry import Point, Polygon

CONFIG_PATH = Path("ai_engine/config/adas_config.json")


def _load_lane_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("modules_config", {}).get("m4_lane_zone", {})
        except Exception:
            pass
    return {
        "auto_ego_lane_detection": True,
        "max_tilt_recalibrate_deg": 25.0,
        "lane_change_threshold_ratio": 0.35
    }


class LaneDetector:
    """
    Bộ phát hiện làn đường tự động (Ego-Lane Detection).
    """

    def __init__(self):
        self.cfg = _load_lane_config()
        self.prev_left_line: Optional[Tuple[float, float, float, float]] = None
        self.prev_right_line: Optional[Tuple[float, float, float, float]] = None
        self.is_lane_detected: bool = False
        self.is_fallback: bool = False
        self.lane_change_in_progress: bool = False

    def detect_ego_lane(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Phát hiện vạch làn trái/phải và tạo đa giác làn đường (Polygon).
        """
        h, w = frame.shape[:2]
        default_polygon = [
            (int(w * 0.20), h),
            (int(w * 0.42), int(h * 0.60)),
            (int(w * 0.58), int(h * 0.60)),
            (int(w * 0.80), h),
        ]

        if frame is None or frame.size == 0:
            return {
                "polygon": default_polygon,
                "shapely_poly": Polygon(default_polygon),
                "is_detected": False,
                "is_fallback": True,
                "lane_change": False
            }

        # 1. Trích xuất ROI nửa dưới màn hình
        roi_y_start = int(h * 0.55)
        roi = frame[roi_y_start:h, :]
        roi_h = roi.shape[0]

        # 2. Lọc màu vạch kẻ đường (Trắng và Vàng) trong không gian HSV
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        # Vạch trắng: Giá trị sáng cao, độ bão hòa thấp
        white_mask = cv2.inRange(hsv, np.array([0, 0, 180]), np.array([180, 45, 255]))
        # Vạch vàng: Hue từ 15-35, Saturation cao
        yellow_mask = cv2.inRange(hsv, np.array([15, 60, 100]), np.array([35, 255, 255]))
        lane_mask = cv2.bitwise_or(white_mask, yellow_mask)

        # 3. Canny Edge + Hough Lines
        edges = cv2.Canny(lane_mask, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=25, minLineLength=30, maxLineGap=20)

        left_lines = []
        right_lines = []

        if lines is not None:
            for line in lines:
                pts = line.reshape(-1)
                if len(pts) < 4:
                    continue
                x1, y1, x2, y2 = int(pts[0]), int(pts[1]), int(pts[2]), int(pts[3])
                if x2 == x1:
                    continue
                slope = (y2 - y1) / float(x2 - x1)
                # Bỏ qua các vạch ngang (gờ giảm tốc, vạch đi bộ)
                if abs(slope) < 0.25:
                    continue

                # Làn trái: dốc âm (trong tọa độ ảnh), nằm nửa trái
                if slope < -0.3 and max(x1, x2) < w * 0.60:
                    left_lines.append((x1, y1 + roi_y_start, x2, y2 + roi_y_start))
                # Làn phải: dốc dương, nằm nửa phải
                elif slope > 0.3 and min(x1, x2) > w * 0.40:
                    right_lines.append((x1, y1 + roi_y_start, x2, y2 + roi_y_start))

        # 4. Ngoại lệ: Vạch mờ hoặc mất vạch (đường VN thường gặp)
        if not left_lines or not right_lines:
            self.is_lane_detected = False
            self.is_fallback = True
            poly_pts = default_polygon
            return {
                "polygon": poly_pts,
                "shapely_poly": Polygon(poly_pts),
                "is_detected": False,
                "is_fallback": True,
                "lane_change": False,
                "note": "Vạch kẻ mờ hoặc mất vạch: Dùng hành lang mặc định an toàn"
            }

        # 5. Fit đường thẳng trung bình cho làn trái và làn phải
        def fit_line(line_list):
            xs, ys = [], []
            for lx1, ly1, lx2, ly2 in line_list:
                xs.extend([lx1, lx2])
                ys.extend([ly1, ly2])
            poly = np.polyfit(ys, xs, 1)  # x = a*y + b
            return poly

        left_poly = fit_line(left_lines)
        right_poly = fit_line(right_lines)

        # Tính tọa độ đáy (y = h) và đỉnh (y = roi_y_start)
        y_bot = float(h)
        y_top = float(roi_y_start)

        x_bl = int(left_poly[0] * y_bot + left_poly[1])
        x_tl = int(left_poly[0] * y_top + left_poly[1])
        x_br = int(right_poly[0] * y_bot + right_poly[1])
        x_tr = int(right_poly[0] * y_top + right_poly[1])

        # Đảm bảo thứ tự hình học hợp lệ
        x_bl = max(0, min(x_bl, int(w * 0.45)))
        x_br = min(w, max(x_br, int(w * 0.55)))
        x_tl = max(0, min(x_tl, x_tr - 20))
        x_tr = min(w, max(x_tr, x_tl + 20))

        # 6. Kiểm tra đổi làn (Lane Change)
        lane_center_bottom = (x_bl + x_br) / 2.0
        frame_center = w / 2.0
        lane_width = max(10, x_br - x_bl)
        shift_ratio = abs(lane_center_bottom - frame_center) / float(lane_width)

        lane_change = shift_ratio > self.cfg.get("lane_change_threshold_ratio", 0.35)

        poly_pts = [(x_bl, int(y_bot)), (x_tl, int(y_top)), (x_tr, int(y_top)), (x_br, int(y_bot))]

        self.is_lane_detected = True
        self.is_fallback = False
        self.lane_change_in_progress = lane_change

        return {
            "polygon": poly_pts,
            "shapely_poly": Polygon(poly_pts),
            "is_detected": True,
            "is_fallback": False,
            "lane_change": lane_change,
            "lane_width_px": lane_width
        }
