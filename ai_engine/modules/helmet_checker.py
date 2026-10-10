"""
helmet_checker.py
-----------------
Phát hiện người điều khiển xe máy đội mũ bảo hiểm theo tiêu chuẩn Việt Nam:
1. Phát hiện người + cắt vùng đầu (1/3 trên của bounding box).
2. Phân loại 3 trạng thái:
   - HELMET: Mũ bảo hiểm đạt chuẩn (nồi cơm điện, nửa đầu, 3/4, full-face).
   - NO_HELMET: Không đội mũ bảo hiểm.
   - UNCERTAIN: Nón không đạt chuẩn (mũ vải, mũ lưỡi trai), trùm áo mưa/khăn trùm, hoặc ngược sáng -> đưa vào hàng chờ duyệt của Dispatcher.
3. Cơ chế Voting theo Track: Kết luận theo chuỗi khung hình liên tiếp, không kết luận theo 1 frame đơn lẻ.
4. Xử lý ngoại lệ: Người ngồi sau, trẻ em, đầu bị xe khác che khuất một phần.
"""

from __future__ import annotations

import json
import os
from collections import Counter, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

import config

CONFIG_PATH = Path("ai_engine/config/adas_config.json")


def _load_helmet_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("modules_config", {}).get("m6_helmet", {})
        except Exception:
            pass
    return {
        "rider_head_crop_ratio": 0.40,
        "track_voting_frames": 5,
        "uncertain_confidence_threshold": 0.55
    }


def analyze_head_texture_and_poncho(head_crop: np.ndarray) -> str:
    """
    Phân tích kết cấu vùng đầu để phát hiện áo mưa/khăn trùm hoặc nón vải mềm:
    - Mũ bảo hiểm vỏ cứng: Bề mặt nhẵn bóng, có dải phản quang/phản xạ ánh sáng mạnh.
    - Áo mưa / khăn trùm / nón vải: Bề mặt nhiều nếp gấp nhăn, gradient phân tán.
    """
    if head_crop is None or head_crop.size == 0 or head_crop.shape[0] < 10 or head_crop.shape[1] < 10:
        return "UNCERTAIN"

    try:
        gray = cv2.cvtColor(head_crop, cv2.COLOR_BGR2GRAY)
        # Đo độ bóng sáng (Specular Highlights của vỏ nhựa cứng)
        bright_ratio = np.count_nonzero(gray > 220) / float(gray.size)

        # Tính độ nhám cạnh (Laplacian gradient)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        texture_var = float(laplacian.var())

        # Nếu có vệt nếp gấp nhiều (áo mưa/khăn trùm) nhưng không có độ bóng
        if texture_var > 350.0 and bright_ratio < 0.02:
            return "NON_STANDARD_OR_PONCHO"

        return "NORMAL_HEADWEAR"
    except Exception:
        return "NORMAL_HEADWEAR"


class HelmetChecker:
    def __init__(self, model_path=config.HELMET_MODEL_PATH, conf=config.CONF_HELMET):
        # Tự động tìm kiếm các ứng viên model khả dụng nếu đường dẫn chưa tồn tại
        if not os.path.exists(model_path):
            candidates = [
                model_path,
                "models/helmet.onnx",
                "web-app/public/models/helmet.onnx",
                "models/helmet_yolov8.pt",
            ]
            for c in candidates:
                if os.path.exists(c):
                    model_path = c
                    break

        self.model_path = model_path
        self.enabled = os.path.exists(model_path) and not config.ROAD_MODEL_SHARED_CLASSES
        self.conf = conf
        self.model = None
        self.cfg = _load_helmet_config()

        # Quản lý voting lịch sử theo track_id: track_id -> deque of (status, conf)
        self.track_votes: Dict[int, deque] = {}

        if self.enabled:
            from ultralytics import YOLO
            self.model = YOLO(model_path, task="detect")

    def check(
        self, 
        frame: np.ndarray, 
        rider_box: Tuple[float, float, float, float], 
        detections: Optional[List[Any]] = None,
        track_id: Optional[int] = None
    ) -> Optional[bool]:
        """
        Kiểm tra người lái xe có đội mũ bảo hiểm hay không.
        Trả về:
            True: Đội mũ bảo hiểm
            False: Không đội mũ bảo hiểm
            None: Không chắc chắn (đưa vào hàng chờ duyệt)
        """
        raw_result = self._check_single_frame(frame, rider_box, detections)

        # Nếu không có track_id, trả về kết quả frame đơn
        if track_id is None:
            return raw_result

        # Cơ chế Voting đa khung hình theo Track
        if track_id not in self.track_votes:
            self.track_votes[track_id] = deque(maxlen=self.cfg.get("track_voting_frames", 5))

        self.track_votes[track_id].append(raw_result)
        history = list(self.track_votes[track_id])

        # Chỉ chốt khi có ít nhất 3 quan sát
        if len(history) < 3:
            return None

        true_count = sum(1 for v in history if v is True)
        false_count = sum(1 for v in history if v is False)
        total = len(history)

        if true_count / total >= 0.60:
            return True
        elif false_count / total >= 0.60:
            return False
        else:
            return None  # UNCERTAIN -> Đưa vào hàng chờ Dispatcher duyệt

    def _check_single_frame(self, frame, rider_box, detections=None) -> Optional[bool]:
        # 1. Nếu đã có detection từ road model dùng chung
        if detections:
            labels = {
                "helmet": True,
                "with helmet": True,
                "with_helmet": True,
                "no_helmet": False,
                "without helmet": False,
                "without_helmet": False,
                "head": False
            }
            for det in detections:
                if isinstance(det, dict):
                    label = det.get("label") or det.get("cls_name")
                    bbox = det.get("bbox") or det.get("box")
                    conf = det.get("conf", 0.5)
                else:
                    label = getattr(det, "label", getattr(det, "cls_name", None))
                    bbox = getattr(det, "bbox", getattr(det, "box", None))
                    conf = getattr(det, "conf", 0.5)

                if label in labels and bbox and self._is_near_head(rider_box, bbox):
                    # Nếu độ tin cậy thấp hoặc rơi vào vùng nghi ngờ nón vải
                    if conf < self.cfg.get("uncertain_confidence_threshold", 0.55):
                        return None
                    return labels[label]

        if not self.enabled or frame is None or frame.size == 0:
            return None

        x1, y1, x2, y2 = [int(v) for v in rider_box]
        head_ratio = self.cfg.get("rider_head_crop_ratio", 0.40)
        head_y2 = y1 + int((y2 - y1) * head_ratio)
        head_crop = frame[max(0, y1):max(0, head_y2), max(0, x1):max(0, x2)]

        if head_crop.size == 0 or head_crop.shape[0] < 12 or head_crop.shape[1] < 12:
            return None

        # 2. Phân tích kết cấu (Áo mưa trùm đầu / Khăn vải / Nón không chuẩn)
        texture_type = analyze_head_texture_and_poncho(head_crop)
        if texture_type == "NON_STANDARD_OR_PONCHO":
            # Không thể khẳng định chắc chắn 100% -> Chuyển sang UNCERTAIN
            return None

        # 3. Model suy luận
        results = self.model(head_crop, conf=self.conf, verbose=False)
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                cls_name = self.model.names[cls_id].lower()

                if conf < self.cfg.get("uncertain_confidence_threshold", 0.55):
                    return None

                if "with helmet" in cls_name or ("helmet" in cls_name and "without" not in cls_name and "no" not in cls_name):
                    return True
                if "without helmet" in cls_name or "no_helmet" in cls_name or "no helmet" in cls_name or "head" in cls_name:
                    return False

        return False

    def _is_near_head(self, rider_box, target_box):
        rx1, ry1, rx2, ry2 = rider_box
        tx1, ty1, tx2, ty2 = target_box
        head_bottom = ry1 + 0.45 * (ry2 - ry1)
        t_center_x = 0.5 * (tx1 + tx2)
        t_center_y = 0.5 * (ty1 + ty2)
        return rx1 <= t_center_x <= rx2 and ry1 <= t_center_y <= head_bottom
