"""
vehicle_detector.py
-------------------
Module phát hiện và phân loại phương tiện giao thông (VehicleDetector).
Tương thích hoàn toàn với kiến trúc mô tả trong Báo cáo Chuyên đề (Chương 4 & Phụ lục C.1).
"""

from ai_engine.modules.detector import *
from ai_engine.modules.detector import Detector

VehicleDetector = Detector

__all__ = ["VehicleDetector", "Detector", "apply_soft_nms", "compute_diou", "merge_truck_and_trailer"]
