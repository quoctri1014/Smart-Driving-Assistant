import base64
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parents[3]
HELMET_MODEL_PATH = BASE_DIR / "web-app" / "public" / "models" / "helmet.onnx"

router = APIRouter()

_helmet_sess = None

def get_helmet_session():
    global _helmet_sess
    if _helmet_sess is None and HELMET_MODEL_PATH.exists():
        try:
            import onnxruntime as ort
            _helmet_sess = ort.InferenceSession(str(HELMET_MODEL_PATH), providers=['CPUExecutionProvider'])
        except Exception as e:
            print("Cannot load helmet ONNX on backend:", e)
    return _helmet_sess


class HelmetViolationItem(BaseModel):
    track_id: int
    status: str  # NO_HELMET, WITH_HELMET
    violation_type: str
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]
    action_required: str
    thumbnail: Optional[str] = None


class HelmetResponse(BaseModel):
    success: bool
    processing_time_ms: float
    image_width: int
    image_height: int
    violation_count: int
    compliant_count: int
    violations: List[HelmetViolationItem]


def _detect_helmets_onnx(img: np.ndarray, conf_thresh: float = 0.40):
    sess = get_helmet_session()
    if sess is None:
        return [], []

    H, W = img.shape[:2]
    S = 640
    sc = min(S / W, S / H)
    nw, nh = int(W * sc), int(H * sc)
    px, py = (S - nw) // 2, (S - nh) // 2

    resized = cv2.resize(img, (nw, nh))
    canvas = np.full((S, S, 3), 114, dtype=np.uint8)
    canvas[py:py+nh, px:px+nw] = resized

    inp = canvas.transpose(2, 0, 1).astype(np.float32) / 255.0
    inp = np.expand_dims(inp, axis=0)

    out = sess.run(None, {sess.get_inputs()[0].name: inp})[0]
    # out is (1, 6, 8400) -> 0..3: cx,cy,w,h; 4: With Helmet, 5: Without Helmet
    d = out[0]
    scores_with = d[4, :]
    scores_without = d[5, :]

    all_dets = []
    for i in range(d.shape[1]):
        sw = float(scores_with[i])
        swo = float(scores_without[i])

        # Chỉ kết luận vi phạm (Without Helmet) nếu mô hình thực sự tự tin và vượt trội so với có mũ
        if swo > sw:
            # Ngưỡng cho vi phạm Nghị định 100: swo >= 0.45 và cách biệt ít nhất 0.15
            if swo < 0.45 or (swo - sw) < 0.15:
                continue
            cls_id = 1
            conf_val = swo
        else:
            if sw < conf_thresh:
                continue
            cls_id = 0
            conf_val = sw

        cx, cy, w, h = float(d[0, i]), float(d[1, i]), float(d[2, i]), float(d[3, i])

        x1 = max(0, int((cx - w / 2 - px) / sc))
        y1 = max(0, int((cy - h / 2 - py) / sc))
        x2 = min(W, int((cx + w / 2 - px) / sc))
        y2 = min(H, int((cy + h / 2 - py) / sc))

        # Bỏ qua những đối tượng ở quá xa (< 28px, không thể xác định rõ)
        if (x2 - x1) < 28 or (y2 - y1) < 28:
            continue

        # Kiểm tra bề mặt vỏ mũ bảo hiểm (loại trừ nón bảo hiểm màu trắng, sáng bóng như Vietcombank)
        # CHỈ áp dụng khi mô hình chưa hoàn toàn chắc chắn (conf_val < 0.75) VÀ
        # nửa trên đầu thực sự mang đặc trưng của vỏ nón trắng nhựa (độ sáng trung bình rất cao > 165 VÀ tỷ lệ điểm sáng > 50%)
        if cls_id == 1 and conf_val < 0.75:
            head_crop = img[y1:y2, x1:x2]
            if head_crop.size > 0:
                ch, cw = head_crop.shape[:2]
                top_h = max(1, int(ch * 0.45))
                top_part = head_crop[:top_h, :]
                gray_top = cv2.cvtColor(top_part, cv2.COLOR_BGR2GRAY)
                mean_lum = float(np.mean(gray_top))
                bright_ratio = float(np.count_nonzero(gray_top > 160) / max(1, gray_top.size))
                if mean_lum > 165 and bright_ratio > 0.50:
                    cls_id = 0
                    conf_val = 0.95

        all_dets.append({
            "cls": cls_id,
            "conf": conf_val,
            "bbox": [x1, y1, x2, y2],
        })

    # NMS nghiêm ngặt chống nhân đôi thẻ cho cùng một người
    all_dets.sort(key=lambda x: x["conf"], reverse=True)
    kept = []
    for det in all_dets:
        overlap = False
        for k in kept:
            xx1 = max(det["bbox"][0], k["bbox"][0])
            yy1 = max(det["bbox"][1], k["bbox"][1])
            xx2 = min(det["bbox"][2], k["bbox"][2])
            yy2 = min(det["bbox"][3], k["bbox"][3])
            inter = max(0, xx2 - xx1) * max(0, yy2 - yy1)
            if inter > 0:
                area_a = (det["bbox"][2] - det["bbox"][0]) * (det["bbox"][3] - det["bbox"][1])
                area_k = (k["bbox"][2] - k["bbox"][0]) * (k["bbox"][3] - k["bbox"][1])
                union = area_a + area_k - inter
                iou = inter / max(1.0, union)
                iomin = inter / max(1.0, min(area_a, area_k))
                if iou > 0.35 or iomin > 0.45:
                    overlap = True
                    break
        if not overlap:
            kept.append(det)

    violations = [d for d in kept if d["cls"] == 1]
    compliant = [d for d in kept if d["cls"] == 0]
    return violations, compliant


@router.post("/helmets/detect", response_model=HelmetResponse)
@router.post("/helmets/check", response_model=HelmetResponse)
@router.post("/check", response_model=HelmetResponse)
async def detect_helmets_endpoint(file: UploadFile = File(...)):
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
    raw_violations, raw_compliant = _detect_helmets_onnx(img, conf_thresh=0.25)

    violations_out = []
    for idx, v in enumerate(raw_violations, start=1):
        bx = v["bbox"]
        crop = img[max(0, bx[1]):min(H, bx[3]), max(0, bx[0]):min(W, bx[2])]
        thumb_b64 = None
        if crop.size > 0:
            resized = cv2.resize(crop, (100, 100))
            _, buf = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
            thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")

        violations_out.append(HelmetViolationItem(
            track_id=idx,
            status="NO_HELMET",
            violation_type="Không đội mũ bảo hiểm",
            confidence=round(v["conf"], 2),
            bbox=bx,
            action_required="Nhắc nhở người điều khiển xe máy đội mũ bảo hiểm đạt chuẩn",
            thumbnail=thumb_b64,
        ))

    duration_ms = round((time.time() - start_time) * 1000, 2)
    return HelmetResponse(
        success=True,
        processing_time_ms=duration_ms,
        image_width=W,
        image_height=H,
        violation_count=len(violations_out),
        compliant_count=len(raw_compliant),
        violations=violations_out,
    )
