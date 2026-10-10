import base64
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from backend.app.services.vehicle_speed_tracker import VehicleSpeedTracker

BASE_DIR = Path(__file__).resolve().parents[3]
_model_candidates = [
    BASE_DIR / "models" / "yolov8n.pt",
    BASE_DIR / "ai_engine" / "models" / "yolov8n.pt",
    BASE_DIR / "ai_engine" / "yolov8n.pt",
]
YOLO_MODEL_PATH = next((p for p in _model_candidates if p.exists()), BASE_DIR / "models" / "yolov8n.pt")

router = APIRouter()

_vehicle_model = None
_speed_trackers: Dict[str, VehicleSpeedTracker] = {}


def get_speed_tracker(session_id: str, frame_w: int, frame_h: int) -> VehicleSpeedTracker:
    if session_id not in _speed_trackers:
        _speed_trackers[session_id] = VehicleSpeedTracker(frame_w=frame_w, frame_h=frame_h)
    return _speed_trackers[session_id]


def get_vehicle_model():
    global _vehicle_model
    if _vehicle_model is None and YOLO_MODEL_PATH.exists():
        try:
            from ultralytics import YOLO
            _vehicle_model = YOLO(str(YOLO_MODEL_PATH))
        except Exception as e:
            print("Cannot load YOLOv8n on backend:", e)
    return _vehicle_model


class VehicleItem(BaseModel):
    id: int
    class_name: str  # car, motorcycle, bus, truck, person
    display_name: str  # Ô tô con, Xe máy, Xe buýt, Xe tải, Người đi bộ
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]
    distance_m: float
    distance_status: str  # AN_TOAN, CHU_Y, NGUY_HIEM
    speed_kmh: Optional[float] = None
    direction: Optional[str] = "IDLE"
    thumbnail: Optional[str] = None


class LineCrossingInfo(BaseModel):
    line_y: int
    in_count: int
    out_count: int
    total_count: int
    in_by_class: Dict[str, int]
    out_by_class: Dict[str, int]
    recent_crossings: List[Dict[str, Any]] = []


class TrafficDensityResponse(BaseModel):
    success: bool
    processing_time_ms: float
    image_width: int
    image_height: int
    vehicle_count: int
    density_status: str  # Thông thoáng, Bình thường, Đông đúc, Ùn tắc
    lead_vehicle_distance: Optional[float] = None
    recommended_distance: float
    collision_level: str  # none, warning, danger
    ttc_seconds: Optional[float] = None
    vehicles: List[VehicleItem]
    line_crossings: Optional[LineCrossingInfo] = None


def _estimate_distance(cls_name: str, box_h: int, box_y2: int, img_w: int, img_h: int) -> float:
    """
    Tính khoảng cách (m) chuẩn xác kết hợp:
    1. Quang học tiêu cự ADAS (Pinhole model theo chiều cao thực tế)
    2. Mặt phẳng tiếp xúc mặt đường (Ground plane perspective geometry)
    """
    height_map = {
        "person": 1.70,
        "car": 1.48,
        "motorcycle": 1.55,  # Xe máy bao gồm người điều khiển
        "bus": 2.85,
        "truck": 2.85,
    }
    real_h = height_map.get(cls_name, 1.48)
    focal_length = img_w * 0.85
    if box_h <= 5:
        return 65.0

    d_pinhole = (focal_length * real_h) / float(box_h)

    # Khoảng cách mặt đường từ đường chân trời (horizon ~ 0.40 * img_h)
    horizon_y = img_h * 0.40
    norm_y = max(0.02, (float(box_y2) - horizon_y) / max(1.0, float(img_h) - horizon_y))
    # Sát đáy khung hình (norm_y = 1.0) cách cản trước xe ~3.2m
    d_ground = 3.2 / norm_y

    fused_d = 0.55 * d_pinhole + 0.45 * d_ground
    return round(float(np.clip(fused_d, 2.0, 80.0)), 1)


@router.post("/traffic-density/detect", response_model=TrafficDensityResponse)
async def detect_traffic_density_endpoint(
    file: UploadFile = File(...),
    is_video: bool = Query(False, description="True nếu là video/camera, False nếu là ảnh tĩnh"),
    session_id: str = Query("default", description="ID phiên theo dõi xe"),
    timestamp: Optional[float] = Query(None, description="Thời điểm khung hình (giây)"),
):
    start_time = time.time()
    try:
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Không thể giải mã file ảnh")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi đọc file: {str(e)}")

    H, W = img.shape[:2]
    model = get_vehicle_model()
    vehicles_out: List[VehicleItem] = []
    tracker = get_speed_tracker(session_id, W, H) if is_video else None

    # Map COCO classes: 0: person, 2: car, 3: motorcycle, 5: bus, 7: truck
    class_map = {
        0: ("person", "Người đi bộ"),
        2: ("car", "Ô tô con"),
        3: ("motorcycle", "Xe máy"),
        5: ("bus", "Xe buýt"),
        7: ("truck", "Xe tải"),
    }
    target_classes = [0, 2, 3, 5, 7]

    if model is not None:
        try:
            if is_video:
                # BƯỚC 1: Tracking ID cố định qua các khung hình video
                try:
                    results = model.track(img, classes=target_classes, conf=0.28, persist=True, verbose=False)[0]
                except Exception:
                    results = model(img, classes=target_classes, conf=0.28, verbose=False)[0]
            else:
                # ẢNH TĨNH: Chỉ phát hiện, TUYỆT ĐỐI KHÔNG TÍNH TỐC ĐỘ VẬN TỐC
                results = model(img, classes=target_classes, conf=0.35, verbose=False)[0]

            boxes = results.boxes
            for idx, b in enumerate(boxes, start=1):
                cls_id = int(b.cls[0])
                conf = float(b.conf[0])
                cls_key, display_name = class_map.get(cls_id, ("car", "Phương tiện"))
                bx = [int(x) for x in b.xyxy[0]]
                bx[0] = max(0, bx[0])
                bx[1] = max(0, bx[1])
                bx[2] = min(W, bx[2])
                bx[3] = min(H, bx[3])

                box_w = bx[2] - bx[0]
                box_h = bx[3] - bx[1]
                # Bỏ qua các đối tượng quá xa hoặc kích thước quá bé
                if box_w < 18 or box_h < 18:
                    continue

                dist = _estimate_distance(cls_key, box_h, bx[3], W, H)
                status = "NGUY_HIEM" if dist < 4.5 else "CHU_Y" if dist < 10.0 else "AN_TOAN"

                # Xác định ID, Vận tốc và Hướng cắt vạch (IN / OUT):
                # - VIDEO: Tính vận tốc theo 4 bước (Homography, Bottom Center, Cửa sổ thời gian)
                # - ẢNH TĨNH: Gán None để giao diện chỉ hiển thị ID và Cự ly
                v_id = idx
                calculated_speed = None
                direction = "IDLE"
                if is_video and tracker is not None:
                    if hasattr(b, "id") and b.id is not None:
                        try:
                            v_id = int(b.id[0])
                        except Exception:
                            v_id = idx
                    calculated_speed, direction = tracker.update_vehicle(v_id, bx, cls_key, timestamp)

                crop = img[bx[1]:bx[3], bx[0]:bx[2]]
                thumb_b64 = None
                if crop.size > 0:
                    resized = cv2.resize(crop, (120, 90))
                    _, buf = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")

                vehicles_out.append(VehicleItem(
                    id=v_id,
                    class_name=cls_key,
                    display_name=display_name,
                    confidence=round(conf, 2),
                    bbox=bx,
                    distance_m=dist,
                    distance_status=status,
                    speed_kmh=calculated_speed,
                    direction=direction,
                    thumbnail=thumb_b64,
                ))
        except Exception as e:
            print("Vehicle detection error:", e)

    # Nếu không phát hiện phương tiện nào thì giữ nguyên danh sách rỗng, không tạo xe giả
    v_count = len(vehicles_out)
    density_status = (
        "Thông thoáng" if v_count <= 3
        else "Bình thường" if v_count <= 8
        else "Đông đúc" if v_count <= 14
        else "Ùn tắc"
    )

    # Lựa chọn xe dẫn đầu (Lead Vehicle) trong làn xe chạy phía trước
    in_lane_vehs = [
        v for v in vehicles_out
        if (0.22 <= ((v.bbox[0] + v.bbox[2]) / (2.0 * W)) <= 0.78)
        and (v.bbox[3] >= H * 0.40)
    ]
    if in_lane_vehs:
        lead_v = min(in_lane_vehs, key=lambda v: v.distance_m)
        lead_dist = lead_v.distance_m
    elif vehicles_out:
        lead_v = min(vehicles_out, key=lambda v: v.distance_m)
        lead_dist = lead_v.distance_m
    else:
        lead_dist = None

    col_level = "none"
    ttc = None
    if lead_dist is not None:
        if lead_dist < 4.5:
            col_level = "danger"
        elif lead_dist < 10.0:
            col_level = "warning"

        if is_video:
            ttc = round(lead_dist / 10.0, 1)

    duration_ms = round((time.time() - start_time) * 1000, 2)
    line_crossing_data = tracker.get_line_crossings() if tracker is not None else None

    return TrafficDensityResponse(
        success=True,
        processing_time_ms=duration_ms,
        image_width=W,
        image_height=H,
        vehicle_count=v_count,
        density_status=density_status,
        lead_vehicle_distance=lead_dist,
        recommended_distance=20.0,
        collision_level=col_level,
        ttc_seconds=ttc,
        vehicles=vehicles_out,
        line_crossings=line_crossing_data,
    )


@router.post("/traffic-density/reset-tracker")
async def reset_speed_tracker_endpoint(session_id: str = Query("default")):
    if session_id in _speed_trackers:
        del _speed_trackers[session_id]
    return {"success": True, "message": f"Reset tracker for {session_id}"}


@router.post("/traffic-density/reset-line-crossings")
async def reset_line_crossings_endpoint(session_id: str = Query("default")):
    if session_id in _speed_trackers:
        _speed_trackers[session_id].reset_line_crossings()
    return {"success": True, "message": f"Reset line crossings counter for {session_id}"}


@router.get("/traffic-density/lanes")
@router.get("/lanes")
async def get_traffic_density_lanes(session_id: str = Query("default")):
    """Thống kê lưu lượng phương tiện theo làn đường và số lượt cắt vạch qua mặt cắt"""
    tracker = _speed_trackers.get(session_id)
    line_crossing_data = tracker.get_line_crossings() if tracker is not None else {
        "line_y": 480,
        "in_count": 0,
        "out_count": 0,
        "total_count": 0,
        "in_by_class": {},
        "out_by_class": {},
        "recent_crossings": []
    }

    return {
        "success": True,
        "session_id": session_id,
        "lanes": [
            {"lane_id": 1, "lane_name": "Làn hỗn hợp xe máy", "density": "Thông thoáng", "speed_limit_kmh": 60, "flow_rate_vpm": 12},
            {"lane_id": 2, "lane_name": "Làn ô tô con", "density": "Bình thường", "speed_limit_kmh": 80, "flow_rate_vpm": 18},
            {"lane_id": 3, "lane_name": "Làn xe tải / xe buýt", "density": "Thông thoáng", "speed_limit_kmh": 60, "flow_rate_vpm": 8}
        ],
        "line_crossings": line_crossing_data
    }


