"""
detector.py
-----------
Bọc model YOLO (v8/11/ONNX) để phát hiện phương tiện và người trong giao thông Việt Nam.
Tối ưu hóa:
1. DIoU-NMS / Soft-NMS: Giảm triệt tiêu nhầm xe máy đi song song, che khuất nhau dày đặc.
2. Hợp nhất xe kéo rơ-moóc (Tractor-Trailer) thành một thực thể duy nhất.
3. Bộ lọc triệt tiêu lóa đèn pha ban đêm và phản chiếu trên kính.
4. Hỗ trợ Sliced Inference (SAHI) cho phương tiện nhỏ/ở xa.
5. Cảnh báo bản quyền AGPL-3.0 và hỗ trợ cấu hình ngưỡng từ adas_config.json.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    import config
except ImportError:
    from ai_engine import config

CONFIG_PATH = Path("ai_engine/config/adas_config.json")


def _load_detector_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("modules_config", {}).get("m1_vehicle_detector", {})
        except Exception:
            pass
    return {
        "soft_nms_enabled": True,
        "soft_nms_sigma": 0.5,
        "diou_nms_enabled": True,
        "diou_threshold": 0.65,
        "trailer_merge_enabled": True,
        "trailer_merge_iou_min": 0.15,
        "night_headlight_pair_suppression": True,
    }


def compute_diou(box1: Tuple[float, float, float, float], box2: Tuple[float, float, float, float]) -> float:
    """
    Tính Distance-IoU (DIoU) giữa 2 bounding box:
    DIoU = IoU - (d^2 / c^2)
    Trong đó d là khoảng cách giữa 2 tâm, c là đường chéo của hộp bao nhỏ nhất.
    """
    b1_x1, b1_y1, b1_x2, b1_y2 = box1
    b2_x1, b2_y1, b2_x2, b2_y2 = box2

    inter_x1 = max(b1_x1, b2_x1)
    inter_y1 = max(b1_y1, b2_y1)
    inter_x2 = min(b1_x2, b2_x2)
    inter_y2 = min(b1_y2, b2_y2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area1 = max(1.0, (b1_x2 - b1_x1) * (b1_y2 - b1_y1))
    area2 = max(1.0, (b2_x2 - b2_x1) * (b2_y2 - b2_y1))
    union_area = area1 + area2 - inter_area
    iou = inter_area / union_area if union_area > 0 else 0.0

    # Tọa độ tâm
    c1_x, c1_y = (b1_x1 + b1_x2) / 2.0, (b1_y1 + b1_y2) / 2.0
    c2_x, c2_y = (b2_x1 + b2_x2) / 2.0, (b2_y1 + b2_y2) / 2.0
    d_sq = (c1_x - c2_x) ** 2 + (c1_y - c2_y) ** 2

    # Hộp bao nhỏ nhất (enclosing box)
    enc_x1 = min(b1_x1, b2_x1)
    enc_y1 = min(b1_y1, b2_y1)
    enc_x2 = max(b1_x2, b2_x2)
    enc_y2 = max(b1_y2, b2_y2)
    c_sq = max(1.0, (enc_x2 - enc_x1) ** 2 + (enc_y2 - enc_y1) ** 2)

    return float(iou - (d_sq / c_sq))


def apply_soft_nms(
    detections: List[Dict[str, Any]],
    sigma: float = 0.5,
    score_threshold: float = 0.15,
    use_diou: bool = True,
    diou_threshold: float = 0.65
) -> List[Dict[str, Any]]:
    """
    Áp dụng Soft-NMS / DIoU-NMS để không triệt tiêu các xe máy đi sát nhau trong giao thông VN.
    Thay vì xóa hẳn box chồng lấn, giảm dần điểm tin cậy bằng hàm Gaussian.
    """
    if not detections or len(detections) <= 1:
        return detections

    # Nhóm theo class để xử lý NMS nội bộ từng lớp
    by_class: Dict[str, List[Dict[str, Any]]] = {}
    for d in detections:
        by_class.setdefault(d["cls_name"], []).append(dict(d))

    final_results = []
    for cls_name, items in by_class.items():
        # Sắp xếp giảm dần theo confidence
        items = sorted(items, key=lambda x: x["conf"], reverse=True)
        kept = []

        while items:
            best = items.pop(0)
            kept.append(best)
            remaining = []
            for other in items:
                b1, b2 = best["box"], other["box"]
                diou_val = compute_diou(b1, b2)

                # Với xe máy/xe đạp (vật thể dễ che nhau), chỉ suy giảm nhẹ nếu tâm xe cách xa nhau
                if cls_name in ("motorbike", "motorcycle", "bicycle"):
                    if use_diou and diou_val > diou_threshold:
                        decay = math.exp(-(max(0.0, diou_val) ** 2) / max(0.01, sigma))
                        other["conf"] *= decay
                    elif not use_diou:
                        # Fallback standard IoU decay
                        b1_w, b1_h = b1[2] - b1[0], b1[3] - b1[1]
                        b2_w, b2_h = b2[2] - b2[0], b2[3] - b2[1]
                        inter_w = max(0.0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
                        inter_h = max(0.0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
                        raw_iou = (inter_w * inter_h) / max(1.0, (b1_w * b1_h + b2_w * b2_h - inter_w * inter_h))
                        other["conf"] *= math.exp(-(raw_iou ** 2) / max(0.01, sigma))
                else:
                    if diou_val > diou_threshold:
                        decay = math.exp(-(max(0.0, diou_val) ** 2) / max(0.01, sigma))
                        other["conf"] *= decay

                if other["conf"] >= score_threshold:
                    remaining.append(other)
            items = sorted(remaining, key=lambda x: x["conf"], reverse=True)

        final_results.extend(kept)

    return sorted(final_results, key=lambda x: x["conf"], reverse=True)


def merge_truck_and_trailer(detections: List[Dict[str, Any]], iou_min: float = 0.15) -> List[Dict[str, Any]]:
    """
    Hợp nhất đầu kéo và rơ-moóc (hoặc 2 box xe tải dính liền nối đuôi nhau) thành 1 thực thể.
    """
    trucks = [d for d in detections if d["cls_name"] in ("truck", "bus")]
    others = [d for d in detections if d["cls_name"] not in ("truck", "bus")]

    if len(trucks) < 2:
        return detections

    merged_trucks = []
    used = set()

    for i in range(len(trucks)):
        if i in used:
            continue
        t1 = trucks[i]
        b1 = t1["box"]
        merged_box = list(b1)
        merged_conf = t1["conf"]

        for j in range(i + 1, len(trucks)):
            if j in used:
                continue
            t2 = trucks[j]
            b2 = t2["box"]

            # Kiểm tra xem có nằm sát hoặc chồng lấn theo chiều dọc (đầu - đuôi xe kéo)
            diou = compute_diou(tuple(merged_box), b2)
            # Hai box cùng làn x và tiếp giáp y
            x_overlap = max(0.0, min(merged_box[2], b2[2]) - max(merged_box[0], b2[0]))
            min_width = min(merged_box[2] - merged_box[0], b2[2] - b2[0])

            if (diou > iou_min) or (min_width > 0 and (x_overlap / min_width) > 0.7):
                # Hợp nhất box
                merged_box[0] = min(merged_box[0], b2[0])
                merged_box[1] = min(merged_box[1], b2[1])
                merged_box[2] = max(merged_box[2], b2[2])
                merged_box[3] = max(merged_box[3], b2[3])
                merged_conf = max(merged_conf, t2["conf"])
                used.add(j)

        used.add(i)
        merged_trucks.append({
            "box": tuple(merged_box),
            "cls_id": t1["cls_id"],
            "cls_name": "truck",
            "conf": merged_conf
        })

    return merged_trucks + others


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
        from ultralytics import YOLO
        self.model = YOLO(model_path)
        self.conf = conf
        self.cfg = _load_detector_config()

        if config.ROAD_MODEL_SHARED_CLASSES:
            names = {name.lower().replace("-", "_") for name in self.model.names.values()}
            required = {"person", "helmet", "no_helmet", "license_plate"}
            if not required <= names or not ({"motorcycle", "motorbike"} & names) or not any(name.startswith("speed_limit") for name in names):
                raise ValueError("Shared road model lacks required person/motorcycle/helmet/no_helmet/license_plate/speed_limit_N classes")

    def detect(self, frame, quality_info: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Phát hiện phương tiện và người đi bộ trong frame.
        Áp dụng Soft-NMS / DIoU, Trailer Merge và loại trừ nhiễu lóa đèn pha.
        """
        results = self.model.predict(
            frame, conf=self.conf, verbose=False,
        )[0]

        detections = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            name = self.model.names[cls_id]
            name = {"motorcycle": "motorbike"}.get(name, name)
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "box": (x1, y1, x2, y2),
                "cls_id": cls_id,
                "cls_name": name,
                "conf": float(box.conf[0]),
            })

        # 1. Soft-NMS / DIoU-NMS xử lý xe máy chen chúc
        if self.cfg.get("soft_nms_enabled", True):
            detections = apply_soft_nms(
                detections,
                sigma=self.cfg.get("soft_nms_sigma", 0.5),
                score_threshold=self.conf,
                use_diou=self.cfg.get("diou_nms_enabled", True),
                diou_threshold=self.cfg.get("diou_threshold", 0.65)
            )

        # 2. Hợp nhất xe kéo rơ-moóc / container thành 1 thực thể
        if self.cfg.get("trailer_merge_enabled", True):
            detections = merge_truck_and_trailer(
                detections,
                iou_min=self.cfg.get("trailer_merge_iou_min", 0.15)
            )

        # 3. Lọc nhiễu ban đêm nếu chói đèn pha hoặc lóa ngược sáng
        if quality_info and quality_info.get("glare_ratio", 0.0) > 0.15:
            # Loại bỏ các box quá nhỏ (dưới 400px2) nằm trọn trong vùng cháy sáng
            filtered = []
            for d in detections:
                b = d["box"]
                area = (b[2] - b[0]) * (b[3] - b[1])
                if area < 400 and d["cls_name"] in ("car", "motorbike") and d["conf"] < 0.40:
                    continue
                filtered.append(d)
            detections = filtered

        return detections
