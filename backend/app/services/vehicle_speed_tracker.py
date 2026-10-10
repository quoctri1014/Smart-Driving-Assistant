import math
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


class VehicleSpeedTracker:
    """
    Module ước lượng vận tốc phương tiện trên video thời gian thực
    dựa trên thị giác máy tính và hình học phối cảnh mặt đường (Road Homography).
    Tuân thủ đúng 4 bước theo tài liệu:
    1. Tracking ID cố định qua các khung hình.
    2. Điểm đại diện: Điểm giữa cạnh dưới bounding box (bánh xe chạm mặt đường): ((x1 + x2)/2, y2).
    3. Đổi pixel sang mét bằng ma trận phối cảnh cv2.getPerspectiveTransform.
    4. Tính vận tốc qua cửa sổ thời gian (0.5s - 1.0s) và làm mượt chống nhiễu.
    """

    def __init__(self, frame_w: int = 1280, frame_h: int = 720, window_sec: float = 0.6, line_y: Optional[float] = None):
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.window_sec = window_sec
        self.min_window_sec = 0.35  # Thời gian tối thiểu để bắt đầu tính tốc độ
        self.line_y = line_y if line_y is not None else float(frame_h * 0.60)

        # Khởi tạo ma trận Homography chuyển từ pixel mặt đường sang tọa độ thực tế (mét)
        # Điểm đo: Làn đường tiêu chuẩn Việt Nam (rộng 3.5m, quan sát đoạn đường 30m phía trước)
        src = np.float32([
            [0.15 * frame_w, 0.95 * frame_h],  # Góc gần bên trái
            [0.85 * frame_w, 0.95 * frame_h],  # Góc gần bên phải
            [0.62 * frame_w, 0.50 * frame_h],  # Góc xa bên phải
            [0.38 * frame_w, 0.50 * frame_h],  # Góc xa bên trái
        ])
        dst = np.float32([
            [-3.5, 3.5],   # x = -3.5m (lề trái), y = 3.5m (cách đầu xe 3.5m)
            [3.5, 3.5],    # x = +3.5m (lề phải), y = 3.5m
            [3.5, 32.0],   # x = +3.5m, y = 32m phía trước
            [-3.5, 32.0],  # x = -3.5m, y = 32m phía trước
        ])
        self.H_matrix = cv2.getPerspectiveTransform(src, dst)

        # Lịch sử vị trí theo ID: id -> deque[(timestamp, X_meters, Y_meters)]
        self.history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=45))
        # Bộ lọc làm mượt tốc độ theo ID: id -> smoothed_speed
        self.smoothed_speeds: Dict[int, float] = {}
        # Thời điểm cập nhật cuối
        self.last_seen: Dict[int, float] = {}

        # ── LINE CROSSING & IN / OUT TRACKING ──
        self.prev_y: Dict[int, float] = {}
        self.in_count = 0
        self.out_count = 0
        self.in_by_class: Dict[str, int] = defaultdict(int)
        self.out_by_class: Dict[str, int] = defaultdict(int)
        self.crossed_in_ids: set = set()
        self.crossed_out_ids: set = set()
        self.recent_crossings: deque = deque(maxlen=25)

    def to_meters(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """Chuyển đổi điểm pixel (x, y) trên mặt đường sang tọa độ mét thực tế (X, Y)."""
        pt = np.float32([[[pixel_x, pixel_y]]])
        projected = cv2.perspectiveTransform(pt, self.H_matrix)[0][0]
        return float(projected[0]), float(projected[1])

    def update_vehicle(
        self,
        vehicle_id: int,
        bbox: List[int],
        cls_name: str = "car",
        timestamp_sec: Optional[float] = None
    ) -> Tuple[Optional[float], str]:
        """
        Cập nhật vị trí của một xe, tính toán vận tốc tức thời (km/h) và xác định hướng cắt vạch (IN/OUT).
        Trả về (speed_kmh, direction) với direction thuộc {'IN', 'OUT', 'IDLE'}.
        """
        now = timestamp_sec if timestamp_sec is not None else time.time()
        self.last_seen[vehicle_id] = now

        x1, y1, x2, y2 = bbox
        # BƯỚC 2: Điểm đại diện là điểm giữa cạnh dưới (tiếp xúc mặt đường)
        bottom_center_x = (x1 + x2) / 2.0
        bottom_center_y = float(y2)

        # BƯỚC 3: Đổi pixel sang mét
        xm, ym = self.to_meters(bottom_center_x, bottom_center_y)

        hist = self.history[vehicle_id]
        hist.append((now, xm, ym))

        # Tính toán hướng Line Crossing dựa trên vị trí Y trước và hiện tại
        direction = "IDLE"
        if vehicle_id in self.prev_y:
            py = self.prev_y[vehicle_id]
            # Xe di chuyển xuống dưới màn hình (tiến lại gần camera) và vượt qua vạch -> IN
            if py < self.line_y <= bottom_center_y:
                direction = "IN"
                if vehicle_id not in self.crossed_in_ids:
                    self.crossed_in_ids.add(vehicle_id)
                    self.in_count += 1
                    self.in_by_class[cls_name] = self.in_by_class.get(cls_name, 0) + 1
                    self.recent_crossings.append({
                        "id": vehicle_id,
                        "class": cls_name,
                        "direction": "IN",
                        "speed_kmh": self.smoothed_speeds.get(vehicle_id, 0.0),
                        "timestamp": round(now, 2),
                    })
            # Xe di chuyển lên trên màn hình (rời đi xa camera) và vượt qua vạch -> OUT
            elif py > self.line_y >= bottom_center_y:
                direction = "OUT"
                if vehicle_id not in self.crossed_out_ids:
                    self.crossed_out_ids.add(vehicle_id)
                    self.out_count += 1
                    self.out_by_class[cls_name] = self.out_by_class.get(cls_name, 0) + 1
                    self.recent_crossings.append({
                        "id": vehicle_id,
                        "class": cls_name,
                        "direction": "OUT",
                        "speed_kmh": self.smoothed_speeds.get(vehicle_id, 0.0),
                        "timestamp": round(now, 2),
                    })
        self.prev_y[vehicle_id] = bottom_center_y

        # Cần ít nhất 2 mẫu và khoảng thời gian >= min_window_sec (để loại bỏ nhiễu rung lắc pixel)
        if len(hist) < 2:
            return self.smoothed_speeds.get(vehicle_id), direction

        # Tìm mẫu cũ nhất trong cửa sổ [now - window_sec, now]
        oldest = hist[0]
        for item in hist:
            if now - item[0] >= self.min_window_sec:
                oldest = item
                break

        dt = now - oldest[0]
        if dt < self.min_window_sec:
            return self.smoothed_speeds.get(vehicle_id), direction

        # BƯỚC 4: Tính vận tốc = quãng đường / thời gian
        dx = xm - oldest[1]
        dy = ym - oldest[2]
        dist_meters = math.hypot(dx, dy)

        v_ms = dist_meters / dt
        raw_speed_kmh = v_ms * 3.6

        # Deadband: Nếu xe di chuyển < 0.35m trong cửa sổ thời gian hoặc vận tốc < 2.5 km/h -> Xe đứng yên
        if raw_speed_kmh < 2.5 or dist_meters < 0.35:
            current_speed = 0.0
        else:
            # Giới hạn vận tốc hợp lý trong đô thị (0 - 140 km/h)
            current_speed = min(140.0, raw_speed_kmh)

        # Làm mượt (Exponential Moving Average)
        prev_smoothed = self.smoothed_speeds.get(vehicle_id)
        if prev_smoothed is None:
            smoothed = current_speed
        else:
            smoothed = 0.65 * prev_smoothed + 0.35 * current_speed

        smoothed_rounded = round(smoothed, 1)
        self.smoothed_speeds[vehicle_id] = smoothed_rounded
        return smoothed_rounded, direction

    def get_line_crossings(self) -> Dict[str, Any]:
        """Lấy toàn bộ thông số đếm lưu lượng xe qua vạch cắt ngang đường."""
        return {
            "line_y": int(self.line_y),
            "in_count": self.in_count,
            "out_count": self.out_count,
            "total_count": self.in_count + self.out_count,
            "in_by_class": dict(self.in_by_class),
            "out_by_class": dict(self.out_by_class),
            "recent_crossings": list(self.recent_crossings),
        }

    def reset_line_crossings(self):
        """Đặt lại bộ đếm lưu lượng IN / OUT."""
        self.in_count = 0
        self.out_count = 0
        self.in_by_class.clear()
        self.out_by_class.clear()
        self.crossed_in_ids.clear()
        self.crossed_out_ids.clear()
        self.recent_crossings.clear()

    def clean_stale_tracks(self, max_idle_sec: float = 3.0):
        """Dọn dẹp các ID xe đã rời khỏi màn hình quá lâu."""
        now = time.time()
        stale_ids = [tid for tid, last_t in self.last_seen.items() if now - last_t > max_idle_sec]
        for tid in stale_ids:
            self.history.pop(tid, None)
            self.smoothed_speeds.pop(tid, None)
            self.last_seen.pop(tid, None)
            self.prev_y.pop(tid, None)
