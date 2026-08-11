"""
detector.py
-----------
Bọc (wrap) model YOLOv8 của ultralytics để phát hiện phương tiện và người.
Dùng chung 1 model gốc (COCO) cho toàn bộ hệ thống nhằm tối ưu tốc độ,
thay vì chạy nhiều model riêng lẻ cho từng tính năng.
"""

from ultralytics import YOLO
from ai_engine import config


class VehicleDetector:
    CLASS_NAMES = {
        0: "person",
        1: "bicycle",
        2: "car",
        3: "motorbike",
        5: "bus",
        7: "truck",
    }

    def __init__(self, model_path=config.VEHICLE_MODEL_PATH, conf=config.CONF_VEHICLE):
        self.model = YOLO(model_path)
        self.conf = conf

    def detect(self, frame):
        """
        Trả về list các dict: {box:(x1,y1,x2,y2), cls_id:int, cls_name:str, conf:float}
        Chỉ giữ lại các lớp quan tâm (người + phương tiện) khai báo trong config.
        """
        results = self.model.predict(
            frame, conf=self.conf, verbose=False,
            classes=config.COCO_VEHICLE_CLASSES + [config.COCO_PERSON_CLASS]
        )[0]

        detections = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in self.CLASS_NAMES:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "box": (x1, y1, x2, y2),
                "cls_id": cls_id,
                "cls_name": self.CLASS_NAMES[cls_id],
                "conf": float(box.conf[0]),
            })
        return detections
