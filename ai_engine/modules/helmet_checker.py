"""
helmet_checker.py
------------------
Phát hiện người điều khiển xe máy có đội mũ bảo hiểm hay không.

Model COCO gốc của YOLO KHÔNG có sẵn lớp "helmet", nên tính năng này cần
1 model YOLO đã được fine-tune riêng trên tập dữ liệu mũ bảo hiểm
(2 lớp: "helmet" và "no-helmet"/"head"). Có nhiều dataset mở sẵn trên
Roboflow Universe (tìm "helmet detection yolov8") để bạn tự train, xem
hướng dẫn trong README phần "Huấn luyện thêm".

Nếu chưa có model, module sẽ tự động chuyển sang chế độ "bỏ qua" (disabled)
và toàn bộ pipeline vẫn chạy bình thường với 3 tính năng còn lại.
"""

import os
from ultralytics import YOLO
from ai_engine import config


class HelmetChecker:
    def __init__(self, model_path=config.HELMET_MODEL_PATH, conf=config.CONF_HELMET):
        self.enabled = os.path.exists(model_path)
        self.conf = conf
        if self.enabled:
            self.model = YOLO(model_path)
            print(f"[HelmetChecker] Đã tải model: {model_path}")
        else:
            print(f"[HelmetChecker] Không tìm thấy model tại '{model_path}'. "
                  f"Tính năng phát hiện mũ bảo hiểm sẽ bị TẮT. "
                  f"Xem README để huấn luyện model riêng.")

    def check(self, frame, rider_box):
        """
        Kiểm tra vùng ảnh quanh đầu người lái (1/3 trên của box người) xem
        có đội mũ bảo hiểm không.
        Trả về: True (có mũ) / False (không mũ) / None (không xác định được)
        """
        if not self.enabled:
            return None

        x1, y1, x2, y2 = [int(v) for v in rider_box]
        head_y2 = y1 + int((y2 - y1) * 0.4)  # lấy 40% phần trên của box = vùng đầu
        head_crop = frame[max(0, y1):max(0, head_y2), max(0, x1):max(0, x2)]
        if head_crop.size == 0:
            return None

        results = self.model.predict(head_crop, conf=self.conf, verbose=False)[0]
        if len(results.boxes) == 0:
            return None

        # Giả định model có 2 lớp: 0 = helmet, 1 = no-helmet (điều chỉnh theo model bạn train)
        best_box = max(results.boxes, key=lambda b: float(b.conf[0]))
        cls_id = int(best_box.cls[0])
        return cls_id == 0  # True nếu là lớp "helmet"
