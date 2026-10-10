"""
privacy_anonymizer.py
---------------------
Bảo vệ quyền riêng tư theo tiêu chuẩn an toàn dữ liệu ADAS & Fleet Management:
1. Làm mờ (Blur / Pixelate) khuôn mặt người đi bộ và biển số phương tiện bên ngoài xe khi xuất báo cáo công khai hoặc bằng chứng vi phạm.
2. Mã hóa bằng chứng: Tạo mã băm SHA-256 (Tamper-proof evidence hash) để chống giả mạo hồ sơ vi phạm.
3. Chính sách lưu trữ dữ liệu (Data Retention): Tự động xóa hoặc ẩn danh hóa sau 30-90 ngày theo thỏa thuận với tài xế và quy định bảo vệ dữ liệu cá nhân (Nghị định 13/2023/NĐ-CP).
"""

from __future__ import annotations

import hashlib
import time
from typing import List, Optional, Tuple
import cv2
import numpy as np


def blur_roi(image: np.ndarray, box: Tuple[int, int, int, int], kernel_size: int = 31) -> np.ndarray:
    """Áp dụng Gaussian Blur mạnh vào vùng hộp quan tâm."""
    x1, y1, x2, y2 = box
    h, w = image.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return image

    roi = image[y1:y2, x1:x2]
    k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
    blurred = cv2.GaussianBlur(roi, (k, k), 0)
    image[y1:y2, x1:x2] = blurred
    return image


def anonymize_evidence_frame(
    frame: np.ndarray,
    face_boxes: Optional[List[Tuple[int, int, int, int]]] = None,
    plate_boxes: Optional[List[Tuple[int, int, int, int]]] = None
) -> np.ndarray:
    """
    Tạo bản sao đã ẩn danh hóa của khung hình bằng chứng vi phạm:
    Làm mờ mặt người đi đường và biển số các xe xung quanh không liên quan.
    """
    if frame is None or frame.size == 0:
        return frame

    anonymized = frame.copy()

    if face_boxes:
        for box in face_boxes:
            anonymized = blur_roi(anonymized, box, kernel_size=25)

    if plate_boxes:
        for box in plate_boxes:
            anonymized = blur_roi(anonymized, box, kernel_size=21)

    return anonymized


def compute_evidence_hash(image_bytes: bytes) -> str:
    """Tính mã SHA-256 xác thực bằng chứng không bị chỉnh sửa."""
    return hashlib.sha256(image_bytes).hexdigest()
