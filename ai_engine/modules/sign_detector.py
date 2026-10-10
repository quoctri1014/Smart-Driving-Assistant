"""
sign_detector.py
----------------
Nhận diện biển báo tốc độ — Chức năng #8 trong tài liệu thiết kế.

Đây là module chính thức theo đúng tên trong tài liệu.
Bao gồm 2 lớp phát hiện:
  1. Heuristic: Phân tích màu sắc (HSV) để phát hiện biển tròn đỏ/trắng
  2. Model YOLO: Khi được cung cấp model fine-tune (ưu tiên hơn)

Để train model riêng:
  - Dataset gợi ý: Roboflow "Vietnam Traffic Signs" hoặc GTSRB (German)
  - Chạy: python train.py (xem train.py để biết thêm)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
import cv2
import numpy as np
import re
import config


# Giới hạn tốc độ phổ biến tại Việt Nam (km/h)
VN_SPEED_LIMITS = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120]


def _detect_round_red_sign(frame: np.ndarray) -> Optional[Dict[str, Any]]:
    """
    Heuristic phát hiện biển báo tốc độ dựa trên:
    - Màu đỏ viền (HSV)
    - Hình tròn (circularity ≥ 0.55)
    - Kích thước hợp lý (0.1% – 15% diện tích frame)
    """
    if frame is None or frame.size == 0:
        return None

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Dải màu đỏ trong HSV (2 vùng: 0-10° và 170-180°)
    mask1 = cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255]))
    mask2 = cv2.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255]))
    mask_red = cv2.bitwise_or(mask1, mask2)

    # Morphology để điền lỗ và làm mịn
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    frame_area = frame.shape[0] * frame.shape[1]

    best = None
    best_score = 0.0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < frame_area * 0.001 or area > frame_area * 0.15:
            continue

        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue

        circularity = 4 * np.pi * area / (perimeter ** 2)
        if circularity < 0.50:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        aspect = w / max(1, h)
        if not (0.6 <= aspect <= 1.6):
            continue

        score = circularity * (area / frame_area) ** 0.3
        if score > best_score:
            best_score = score
            best = {"box": (x, y, x + w, y + h), "circularity": circularity, "area": area}

    if best:
        best["confidence"] = round(min(1.0, best["circularity"]), 2)
        return best
    return None


class SignDetector:
    """
    Nhận diện biển báo tốc độ — chức năng #8.

    Khi chưa có model AI riêng, dùng phân tích màu sắc (heuristic).
    Khi có model YOLO fine-tune, tự động ưu tiên model.

    Sử dụng:
        detector = SignDetector()
        result = detector.detect(frame, detections)
        # result: {"detected": bool, "type": str, "speed_limit": float, "confidence": float}
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self._use_heuristic = True

        if model_path is not None and not config.ROAD_MODEL_SHARED_CLASSES:
            try:
                import os
                from ultralytics import YOLO
                if os.path.exists(model_path):
                    self.model = YOLO(model_path)
                    self._use_heuristic = False
            except Exception:
                pass

    def detect(
        self,
        frame: Optional[np.ndarray],
        detections: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Phát hiện biển báo tốc độ trong frame.

        Args:
            frame: Khung hình BGR (numpy array)
            detections: Danh sách detections từ YOLO chung (tùy chọn)

        Returns:
            Dict: detected, type, speed_limit, confidence, box, method
        """
        # Ưu tiên model YOLO chuyên dụng nếu có
        shared = self._from_detections(detections or [], "shared_model")
        if shared is not None:
            return shared
        if self.model is not None and frame is not None:
            return self._detect_with_model(frame)

        # Heuristic phân tích màu sắc
        if frame is not None:
            result = _detect_round_red_sign(frame)
            if result:
                return {
                    "detected": True,
                    "type": "unclassified_red_sign",
                    "speed_limit": None,   # Heuristic chỉ phát hiện biển, chưa đọc số
                    "confidence": result["confidence"],
                    "box": result["box"],
                    "method": "heuristic",
                }

        return {
            "detected": False,
            "type": None,
            "speed_limit": None,
            "confidence": 0.0,
        }

    def _detect_with_model(self, frame: np.ndarray) -> Dict[str, Any]:
        """Phát hiện bằng YOLO model fine-tune."""
        results = self.model(frame, verbose=False)
        if not results or len(results[0].boxes) == 0:
            return {"detected": False, "type": None, "speed_limit": None, "confidence": 0.0}

        detections = [{"cls_name": self.model.names[int(b.cls[0])],
                       "conf": float(b.conf[0]), "box": b.xyxy[0].tolist()}
                      for b in results[0].boxes]
        return self._from_detections(detections, "model") or {
            "detected": False, "type": None, "speed_limit": None, "confidence": 0.0}

    @staticmethod
    def _from_detections(detections, method):
        candidates = []
        for detection in detections:
            label = str(detection.get("cls_name", "")).lower().replace("-", "_").replace(" ", "_")
            limit = getattr(config, "SIGN_SPEED_LABELS", {}).get(label)
            match = re.fullmatch(r"speed_limit_?(\d{2,3})", label)
            if limit is None and match:
                limit = int(match.group(1))
            if limit not in VN_SPEED_LIMITS or detection.get("conf", 0) < config.CONF_VEHICLE:
                continue
            candidates.append({"detected": True, "type": "speed_limit", "speed_limit": limit,
                               "confidence": detection["conf"], "box": detection.get("box"), "method": method})
        return max(candidates, key=lambda item: item["confidence"]) if candidates else None

    # Backward compatible alias (giữ cho code cũ vẫn chạy)
    def read_speed_limit_sign(
        self, detections: List[Dict], frame: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Alias tương thích ngược với sign_recognition.py cũ."""
        return self.detect(frame, detections)
