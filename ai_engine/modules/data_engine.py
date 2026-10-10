"""
data_engine.py
--------------
0.4 Data Engine (Vòng lặp học - Active Learning & Hard Cases):
- Thu thập tự động các ca khó (Hard Cases):
  * Dự đoán có độ tin cậy thấp (Low confidence).
  * Ca bị Dispatcher bác bỏ (Dương tính giả - FALSE_POSITIVE).
  * Khung hình chất lượng kém (Low quality / chói / giọt mưa).
  * Ca bỏ sót phản hồi từ tài xế / điều độ viên.
- Lưu trữ snapshot ảnh và metadata đầy đủ (giờ, chất lượng, tốc độ, cảm biến).
- Xuất dữ liệu sẵn sàng gán nhãn lại cho CVAT hoặc Label Studio để fine-tune.
"""

import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import cv2
import numpy as np


HARD_CASES_DIR = Path("storage/hard_cases")
IMAGES_DIR = HARD_CASES_DIR / "images"
MANIFEST_FILE = HARD_CASES_DIR / "manifest.jsonl"


class DataEngine:
    def __init__(self, storage_dir: Path = HARD_CASES_DIR):
        self.storage_dir = storage_dir
        self.images_dir = self.storage_dir / "images"
        self.manifest_file = self.storage_dir / "manifest.jsonl"

        self.images_dir.mkdir(parents=True, exist_ok=True)

    def record_hard_case(
        self,
        frame: np.ndarray,
        trigger_reason: str, # 'LOW_CONFIDENCE', 'FALSE_POSITIVE', 'LOW_QUALITY', 'MISSED_DETECTION'
        module_name: str,
        predictions: Optional[List[Dict[str, Any]]] = None,
        telemetry: Optional[Dict[str, Any]] = None,
        quality_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Lưu 1 mẫu ca khó vào kho dữ liệu phục vụ tái huấn luyện (Re-training).
        """
        case_id = f"case_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        image_filename = f"{case_id}.jpg"
        image_path = self.images_dir / image_filename

        # Lưu ảnh JPG chất lượng cao
        if frame is not None and frame.size > 0:
            cv2.imwrite(str(image_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

        record = {
            "case_id": case_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trigger_reason": trigger_reason,
            "module_name": module_name,
            "image_path": str(image_path.as_posix()),
            "image_filename": image_filename,
            "predictions": predictions or [],
            "telemetry": telemetry or {},
            "quality_info": quality_info or {}
        }

        # Ghi append vào file manifest JSONL
        with open(self.manifest_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return case_id

    def get_hard_cases_count(self) -> int:
        if not self.manifest_file.exists():
            return 0
        with open(self.manifest_file, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

    def export_for_annotation(self, export_dir: Path, target_format: str = "label_studio") -> str:
        """
        Xuất bộ dữ liệu ca khó phục vụ gán nhãn trên Label Studio hoặc CVAT.
        """
        export_dir = Path(export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        export_manifest = []

        if not self.manifest_file.exists():
            return "Chưa có ca khó nào trong kho lưu trữ."

        with open(self.manifest_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                item = json.loads(line)
                if target_format == "label_studio":
                    export_manifest.append({
                        "data": {
                            "image": f"/data/local-files/?d={item['image_filename']}",
                            "trigger_reason": item["trigger_reason"],
                            "module": item["module_name"]
                        },
                        "meta": item.get("telemetry", {})
                    })
                elif target_format == "cvat":
                    export_manifest.append({
                        "image": item["image_filename"],
                        "module": item["module_name"],
                        "predictions": item["predictions"]
                    })

        out_file = export_dir / f"annotation_tasks_{target_format}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(export_manifest, f, ensure_ascii=False, indent=2)

        return str(out_file)
