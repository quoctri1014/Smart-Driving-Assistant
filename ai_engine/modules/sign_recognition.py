"""
sign_recognition.py
-------------------
Nhận diện biển báo giao thông.
Phase 1: Adapter/Mock.
"""
from typing import List, Dict, Any

class SignRecognition:
    def __init__(self):
        # TODO: Tích hợp model traffic-sign recognition thật vào đây
        # VD: load mô hình phân loại biển báo YOLO
        pass
        
    def read_speed_limit_sign(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Nhận danh sách detections từ detector gốc (YOLO).
        Lọc và trả về biển báo tốc độ nếu có.
        """
        # MOCK: Hiện tại trả về không phát hiện được
        # Nếu model thật có class_name == "traffic_sign",
        # tiến hành crop và phân loại tốc độ cụ thể.
        return {
            "detected": False,
            "type": None,
            "speed_limit": None,
            "confidence": None
        }
