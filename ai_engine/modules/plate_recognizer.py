"""
plate_recognizer.py
-------------------
Module nhận diện biển số xe cơ giới Việt Nam (VietnamesePlateRecognizer).
Kết hợp YOLO phát hiện vùng biển, CLAHE cân bằng sáng cục bộ, EasyOCR đọc ký tự và chuẩn hóa QCVN.
Tương thích hoàn toàn với mã nguồn Phụ lục C.2 trong Báo cáo Chuyên đề.
"""

import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

# Re-export utilities from scripts.plate_recognizer for backwards compatibility
try:
    from scripts.plate_recognizer import (
        preprocess,
        deskew,
        read_text,
        fix_plate,
        is_valid_vietnamese_plate,
        is_valid_plate_with_aspect_ratio,
        fmt as fmt_plate
    )
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "license_plate.pt"
if not DEFAULT_MODEL_PATH.exists():
    DEFAULT_MODEL_PATH = BASE_DIR / "models" / "license_plate.onnx"


class VietnamesePlateRecognizer:
    """
    Hệ thống nhận diện biển số xe Việt Nam:
    1. Phát hiện biển số qua mô hình YOLO (license_plate)
    2. Cân bằng sáng thích ứng giới hạn tương phản CLAHE & chuẩn hóa 240x80
    3. Nhận dạng ký tự EasyOCR
    4. Thẩm định và hiệu chỉnh định dạng chuẩn Cục Cảnh sát Giao thông
    """
    def __init__(self, yolo_plate_path: Optional[str] = None):
        model_path = yolo_plate_path or str(DEFAULT_MODEL_PATH)
        self.detector = None
        if os.path.exists(model_path):
            try:
                from ultralytics import YOLO
                self.detector = YOLO(model_path)
            except Exception:
                pass
        self._reader = None
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    @property
    def ocr(self):
        if self._reader is None:
            import easyocr
            self._reader = easyocr.Reader(['en'], gpu=False)
        return self._reader

    def deskew_and_enhance(self, plate_crop: np.ndarray) -> np.ndarray:
        """Cân bằng tương phản CLAHE và chuẩn hóa kích thước 240x80 pixel."""
        if len(plate_crop.shape) == 3:
            gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_crop
        enhanced = self.clahe.apply(gray)
        resized = cv2.resize(enhanced, (240, 80), interpolation=cv2.INTER_CUBIC)
        return resized

    def recognize(self, plate_crop: np.ndarray) -> Tuple[str, bool]:
        """Trích xuất và trả về chuỗi biển số xe chuẩn hóa (Ví dụ: 51H-982.45)."""
        if plate_crop is None or plate_crop.size == 0:
            return "", False

        prep = self.deskew_and_enhance(plate_crop)
        ocr_results = self.ocr.readtext(prep, detail=0)
        raw_text = ''.join(ocr_results).upper().replace(' ', '').replace('.', '').replace('-', '')

        pattern = r'^([0-9]{2})([A-Z]{1,2})([0-9]{4,5})$'
        match = re.match(pattern, raw_text)
        if match:
            province, series, seq = match.groups()
            if len(seq) == 5:
                formatted = f"{province}{series}-{seq[:3]}.{seq[3:]}"
            else:
                formatted = f"{province}{series}-{seq}"
            return formatted, True

        return raw_text, False
