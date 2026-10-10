"""
load_shedder.py
---------------
0.5 Adaptive Load Shedding (Cơ chế giảm tải thích nghi khi quá tải):
- Giám sát độ trễ (latency ms) và tốc độ khung hình (FPS) theo cửa sổ trượt.
- Khi phần cứng quá tải (> 140ms / khung hình):
  * Tự động hạ độ phân giải ảnh đầu vào (scale factor 0.75).
  * Giảm tần suất chạy các module thứ cấp (Biển số xe, Nhận diện biển báo: chạy cách quãng).
  * NGUYÊN TẮC BẢO VỆ TUYỆT ĐỐI: KHÔNG BAO GIỜ bỏ qua các module an toàn sinh mạng:
    TTC (Cảnh báo va chạm khẩn) và DMS (Cảnh báo ngủ gật).
- Tự động phục hồi về NORMAL khi độ trễ giảm an toàn (< 80ms).
"""

from collections import deque
from typing import Dict, Any, Tuple
import numpy as np
import cv2


class AdaptiveLoadShedder:
    def __init__(
        self,
        target_fps: float = 25.0,
        overload_threshold_ms: float = 140.0,
        recovery_threshold_ms: float = 80.0,
        window_size: int = 15
    ):
        self.target_fps = target_fps
        self.overload_threshold_ms = overload_threshold_ms
        self.recovery_threshold_ms = recovery_threshold_ms
        self.latencies = deque(maxlen=window_size)
        self.state: str = "NORMAL" # 'NORMAL', 'OVERLOADED'
        self.frame_counter: int = 0
        self.scale_factor: float = 1.0

    def record_frame_latency(self, latency_ms: float):
        self.latencies.append(latency_ms)
        self.frame_counter += 1

        if len(self.latencies) >= 5:
            avg_lat = float(np.mean(self.latencies))
            if self.state == "NORMAL" and avg_lat > self.overload_threshold_ms:
                self.state = "OVERLOADED"
                self.scale_factor = 0.75
            elif self.state == "OVERLOADED" and avg_lat < self.recovery_threshold_ms:
                self.state = "NORMAL"
                self.scale_factor = 1.0

    def should_process_module(self, module_name: str) -> bool:
        """
        Xác định xem module có được phép chạy trên khung hình hiện tại không.
        Các module khẩn cấp luôn được chạy 100% khung hình.
        """
        # Critical safety modules are NEVER shed
        if module_name in ("collision_warning", "drowsiness_detector", "vehicle_detection"):
            return True

        if self.state == "OVERLOADED":
            # Module thứ cấp (Plate OCR, Biển báo): Chỉ chạy 1 lần mỗi 3 khung hình
            if module_name in ("plate_reader", "sign_recognition", "helmet_checker"):
                return (self.frame_counter % 3 == 0)

        return True

    def adapt_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Thu nhỏ độ phân giải nếu đang trong trạng thái OVERLOADED.
        Trả về (scaled_frame, scale_applied).
        """
        if self.scale_factor == 1.0 or frame is None:
            return frame, 1.0

        h, w = frame.shape[:2]
        new_w = int(w * self.scale_factor)
        new_h = int(h * self.scale_factor)
        scaled = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        return scaled, self.scale_factor

    def get_status(self) -> Dict[str, Any]:
        avg_lat = float(np.mean(self.latencies)) if self.latencies else 0.0
        fps = round(1000.0 / avg_lat, 1) if avg_lat > 0 else 0.0
        return {
            "load_state": self.state,
            "avg_latency_ms": round(avg_lat, 1),
            "effective_fps": fps,
            "scale_factor": self.scale_factor,
            "shedding_active": (self.state == "OVERLOADED")
        }
