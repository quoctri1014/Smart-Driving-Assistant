"""
noise_filter.py
---------------
Bộ lọc chống nhiễu cho sự kiện ADAS:
1. Gating theo ngưỡng Confidence (loại bỏ phán đoán yếu).
2. Yêu cầu duy trì N khung hình liên tiếp (Temporal Persistence Voting).
3. Cooldown giữa các lần kích hoạt (Anti-flickering & Debounce).
"""

import time
from typing import Dict, Optional, Tuple
from backend.app.schemas.adas_event import AdasEvent


class EventNoiseFilter:
    """
    Bộ lọc chống nhiễu thông minh cho luồng sự kiện ADAS thời gian thực.
    """
    
    # Cấu hình mặc định cho từng loại module:
    # (min_confidence, min_consecutive_frames, cooldown_seconds)
    DEFAULT_FILTER_RULES = {
        "ttc": (0.65, 3, 4.0),             # Va chạm: độ nhạy cao, 3 frame, cooldown 4s
        "drowsiness": (0.70, 5, 8.0),      # Ngủ gật: 5 frame (chống chớp mắt bình thường), cooldown 8s
        "dms": (0.50, 1, 0.0),             # EyesClosedMonitor: State machine đã tính giây và cooldown
        "safe_distance": (0.60, 4, 6.0),   # Cự ly an toàn: 4 frame, cooldown 6s
        "speed": (0.75, 5, 10.0),          # Quá tốc độ: 5 frame, cooldown 10s
        "sign": (0.70, 5, 12.0),           # Biển báo: 5 frame voting, cooldown 12s
        "seatbelt": (0.80, 8, 15.0),       # Dây an toàn: 8 frame, cooldown 15s
        "helmet": (0.75, 4, 10.0),         # Mũ bảo hiểm: 4 frame, cooldown 10s
        "driving_timer": (0.90, 1, 60.0),  # Đếm giờ lái: 1 frame, cooldown 60s
        "plate_ocr": (0.70, 3, 5.0),       # Biển số: 3 frame voting, cooldown 5s
        "zone": (0.50, 1, 1.0),            # Zone count: tức thì
    }

    def __init__(self, custom_rules: Optional[Dict[str, Tuple[float, int, float]]] = None):
        self.rules = dict(self.DEFAULT_FILTER_RULES)
        if custom_rules:
            self.rules.update(custom_rules)
            
        # Lưu vết frame liên tiếp: key = f"{module}:{type}:{target_id}" -> count
        self._consecutive_counts: Dict[str, int] = {}
        
        # Lưu vết thời điểm kích hoạt cuối cùng: key -> timestamp
        self._last_triggered_time: Dict[str, float] = {}

    def _get_key(self, event: AdasEvent) -> str:
        target_id = event.payload.get("target_id") or event.payload.get("track_id") or "global"
        return f"{event.module}:{event.type}:{target_id}"

    def filter_event(self, event: AdasEvent) -> Optional[AdasEvent]:
        """
        Nhận 1 sự kiện thô, kiểm tra qua 3 tầng lọc:
        1. Confidence check
        2. Temporal persistence (N-frame check)
        3. Cooldown check
        
        Trả về event nếu vượt qua lọc, None nếu bị chặn do nhiễu.
        """
        now = time.time()
        rule = self.rules.get(event.module, (0.60, 3, 5.0))
        min_conf, min_frames, cooldown = rule
        
        # Tầng 1: Lọc theo Confidence
        if event.confidence < min_conf:
            return None
            
        key = self._get_key(event)
        
        # Tầng 2: Kiểm tra Cooldown
        last_time = self._last_triggered_time.get(key, 0.0)
        if (now - last_time) < cooldown:
            # Vẫn đang trong thời gian cooldown kể từ lần cảnh báo trước
            return None
            
        # Tầng 3: Tích lũy N khung hình liên tiếp
        current_count = self._consecutive_counts.get(key, 0) + 1
        self._consecutive_counts[key] = current_count
        
        if current_count >= min_frames:
            # Đủ N frame liên tiếp -> Xác nhận sự kiện
            self._last_triggered_time[key] = now
            self._consecutive_counts[key] = 0  # Reset đếm sau khi đã trigger
            return event
            
        return None

    def decay_missing(self, active_keys: set[str]):
        """
        Giảm dần đếm đối với các sự kiện không còn xuất hiện trong frame này.
        """
        for k in list(self._consecutive_counts.keys()):
            if k not in active_keys:
                self._consecutive_counts[k] = max(0, self._consecutive_counts[k] - 1)
                if self._consecutive_counts[k] == 0:
                    del self._consecutive_counts[k]

    def reset(self):
        """Reset toàn bộ trạng thái bộ lọc (khi bắt đầu phiên mới)."""
        self._consecutive_counts.clear()
        self._last_triggered_time.clear()
