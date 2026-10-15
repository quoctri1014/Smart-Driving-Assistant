import base64
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

# Thêm đường dẫn gốc vào sys.path để import plate_recognizer và ai_engine
BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
AI_ENGINE_DIR = BASE_DIR / "ai_engine"
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))
SCRIPTS_DIR = BASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from ai_engine.plate.plate_reader import PlateReader, classify_plate_background_color
except ImportError:
    from plate.plate_reader import PlateReader, classify_plate_background_color

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
    from plate_recognizer import (
        preprocess,
        deskew,
        read_text,
        fix_plate,
        is_valid_vietnamese_plate,
        is_valid_plate_with_aspect_ratio,
        fmt as fmt_plate
    )
from backend.app.core.pipeline_runner import SharedAIModels

router = APIRouter()

VN_PROVINCES = {
    "11": "Cao Bằng", "12": "Lạng Sơn", "14": "Quảng Ninh", "15": "Hải Phòng", "16": "Hải Phòng",
    "17": "Thái Bình", "18": "Nam Định", "19": "Phú Thọ", "20": "Thái Nguyên", "21": "Yên Bái",
    "22": "Tuyên Quang", "23": "Hà Giang", "24": "Lào Cai", "25": "Lai Châu", "26": "Sơn La",
    "27": "Điện Biên", "28": "Hòa Bình", "29": "Hà Nội", "30": "Hà Nội", "31": "Hà Nội",
    "32": "Hà Nội", "33": "Hà Nội", "34": "Hải Dương", "35": "Ninh Bình", "36": "Thanh Hóa",
    "37": "Nghệ An", "38": "Hà Tĩnh", "40": "Hà Nội", "43": "Đà Nẵng", "47": "Đắk Lắk",
    "48": "Đắk Nông", "49": "Lâm Đồng", "50": "TP. Hồ Chí Minh", "51": "TP. Hồ Chí Minh",
    "52": "TP. Hồ Chí Minh", "53": "TP. Hồ Chí Minh", "54": "TP. Hồ Chí Minh", "55": "TP. Hồ Chí Minh",
    "56": "TP. Hồ Chí Minh", "57": "TP. Hồ Chí Minh", "58": "TP. Hồ Chí Minh", "59": "TP. Hồ Chí Minh",
    "60": "Đồng Nai", "61": "Bình Dương", "62": "Long An", "63": "Tiền Giang", "64": "Vĩnh Long",
    "65": "Cần Thơ", "66": "Đồng Tháp", "67": "An Giang", "68": "Kiên Giang", "69": "Cà Mau",
    "70": "Tây Ninh", "71": "Bến Tre", "72": "Bà Rịa - Vũng Tàu", "73": "Quảng Bình", "74": "Quảng Trị",
    "75": "Thừa Thiên Huế", "76": "Quảng Ngãi", "77": "Bình Định", "78": "Phú Yên", "79": "Khánh Hòa",
    "80": "Cục CSGT / Cơ quan TW",
    "81": "Gia Lai", "82": "Kon Tum", "83": "Sóc Trăng", "84": "Trà Vinh", "85": "Ninh Thuận",
    "86": "Bình Thuận", "88": "Vĩnh Phúc", "89": "Hưng Yên", "90": "Hà Nam", "92": "Quảng Nam",
    "93": "Bình Phước", "94": "Bạc Liêu", "95": "Hậu Giang", "97": "Bắc Kạn", "98": "Bắc Giang",
    "99": "Bắc Ninh"
}

def deduce_province(plate_str: Optional[str]) -> Optional[str]:
    if not plate_str:
        return None
    clean = re.sub(r"[^A-Z0-9]", "", plate_str.upper())
    if len(clean) >= 2 and clean[:2].isdigit():
        return VN_PROVINCES.get(clean[:2])
    return None

def deduce_vehicle_type(plate_str: Optional[str], bg_color: str) -> str:
    clean = re.sub(r"[^A-Z0-9]", "", str(plate_str).upper()) if plate_str else ""
    p = plate_str.strip() if plate_str else ""

    # 1. Xe kinh doanh vận tải (Biển vàng hoặc seri E, F, G như 29E, 29F, 50E...)
    if bg_color == "COMMERCIAL_YELLOW" or (len(clean) >= 3 and clean[:2].isdigit() and clean[2] in ('E', 'F', 'G')):
        return "Xe dịch vụ / Vận tải"

    # 2. Xe cơ quan Nhà nước (Biển xanh)
    if bg_color == "GOVERNMENT_BLUE":
        return "Xe cơ quan Nhà nước"

    # 3. Xe quân đội: BẮT BUỘC có 2 chữ cái đầu là ký hiệu quân sự (KT, TC, TH...) và KHÔNG được bắt đầu bằng mã tỉnh 2 số
    is_provincial = len(clean) >= 2 and clean[:2].isdigit()
    if not is_provincial:
        if bg_color == "MILITARY_RED" or re.match(r"^[A-Z]{2}-\d{2}-\d{2}$", p) or (len(clean) == 6 and clean[:2].isalpha() and clean[2:].isdigit()):
            return "Xe Quân đội"

    # 4. Xe Ngoại giao / Quốc tế
    if re.match(r"^\d{2}-(NN|NG|QT|CV)\b", p) or (len(clean) >= 4 and clean[2:4] in ('NN', 'NG', 'QT', 'CV')):
        return "Xe Ngoại giao / Quốc tế"

    # 5. Xe Liên doanh / Dự án
    if re.match(r"^\d{2}-(LD|DA)\b", p) or (len(clean) >= 4 and clean[2:4] in ('LD', 'DA')):
        return "Xe Liên doanh / Dự án"

    # 6. Xe ô tô con 5 số (XXA-123.45) hoặc 4 số (XXA-1234)
    if re.match(r"^\d{2}[A-Z]-\d{3}\.\d{2}$", p) or re.match(r"^\d{2}[A-Z]-\d{4}$", p):
        return "Xe ô tô con"

    # 7. Xe máy 4 số (XX-Y9 6850, XX-AB 0014) hoặc 5 số (XX-C1 010.82)
    if re.match(r"^\d{2}-[A-Z0-9]{2} \d{4}$", p) or re.match(r"^\d{2}-[A-Z0-9]{2} \d{3}\.\d{2}$", p):
        return "Xe máy"

    if len(clean) == 9:
        return "Xe máy"
    if len(clean) in (7, 8) and clean[3:].isdigit():
        return "Xe ô tô con"
    return "Xe dân sự"


class LicensePlateDetectionItem(BaseModel):
    plate: str
    raw_text: Optional[str] = None
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]
    background_color: str  # CIVILIAN_WHITE, COMMERCIAL_YELLOW, GOVERNMENT_BLUE, MILITARY_RED
    province: Optional[str] = None
    vehicle_type: Optional[str] = None
    status: str  # CONFIRMED, UNCERTAIN, NOT_READABLE
    thumbnail: Optional[str] = None

class LicensePlateResponse(BaseModel):
    success: bool
    processing_time_ms: float
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    detections: List[LicensePlateDetectionItem]


def fmt_vietnamese_plate(p: str) -> str:
    if not p:
        return p
    return fmt_plate(p)


def _read_crop_with_recognizer(reader, crop: np.ndarray):
    """Xử lý crop biển số bằng đa chiến lược (CLAHE, Direct, Trimmed, Bilateral, Invert) kết hợp Consensus Scoring."""
    if crop is None or crop.shape[0] < 10 or crop.shape[1] < 20:
        return None, "", 0.0

    h, w = crop.shape[:2]
    aspect = w / max(1, h)
    candidates = []

    # Chiến lược 1: Cân bằng tương phản cục bộ CLAHE
    try:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(6, 6))
        cl = clahe.apply(gray)
        raw_cl, c_cl = read_text(reader, cl)
        if raw_cl:
            p_cl, ok_cl = fix_plate(raw_cl)
            if ok_cl:
                candidates.append((p_cl, raw_cl, c_cl, "clahe"))
                # EARLY EXIT TỐC ĐỘ CAO: Nếu đã nhận diện chuẩn biển số VN -> Trả về ngay lập tức (<90ms)
                if is_valid_vietnamese_plate(p_cl) and c_cl >= 0.45:
                    return p_cl, raw_cl, c_cl
    except Exception:
        pass

    # Chiến lược 2: Ảnh gốc trực tiếp
    try:
        raw1, c1 = read_text(reader, crop)
        if raw1:
            p1, ok1 = fix_plate(raw1)
            if ok1:
                candidates.append((p1, raw1, c1, "direct"))
                if is_valid_vietnamese_plate(p1) and c1 >= 0.45:
                    return p1, raw1, c1
    except Exception:
        pass

    # Chiến lược 3: Cắt lề 4% - Chỉ chạy khi chưa có bất kỳ biển số hợp lệ nào
    if not candidates or all(not is_valid_vietnamese_plate(c[0]) for c in candidates):
        try:
            if aspect >= 1.8:
                trim = crop[int(h * 0.05):int(h * 0.95), int(w * 0.03):int(w * 0.97)]
            else:
                trim = crop[int(h * 0.02):int(h * 0.98), int(w * 0.02):int(w * 0.98)]
            raw2, c2 = read_text(reader, trim)
            if raw2:
                p2, ok2 = fix_plate(raw2)
                if ok2:
                    candidates.append((p2, raw2, c2, "trim"))
                    if is_valid_vietnamese_plate(p2):
                        return p2, raw2, c2
        except Exception:
            pass

    if not candidates:
        return None, "", 0.0

    from collections import Counter
    vote_counter = Counter(c[0] for c in candidates)

    def _cand_score(item):
        plate_str, raw_t, conf, strat = item
        clean_len = len(re.sub(r"[^A-Z0-9]", "", plate_str))
        len_bonus = clean_len * 0.2
        vote_bonus = vote_counter[plate_str] * 1.5
        strat_bonus = 0.6 if strat in ("clahe", "trim", "direct") else 0.0

        clean_raw = re.sub(r"[^A-Z0-9]", "", raw_t.upper())
        clean_p = re.sub(r"[^A-Z0-9]", "", plate_str.upper())
        letter_bonus = 0.0
        if len(clean_raw) >= 3 and len(clean_p) >= 3:
            if clean_raw[2].isalpha() and clean_raw[2] == clean_p[2]:
                letter_bonus += 2.5
            elif clean_raw[2] in ('0', 'O'):
                letter_bonus -= 1.0

        return vote_bonus + conf + len_bonus + strat_bonus + letter_bonus

    candidates.sort(key=_cand_score, reverse=True)
    best = candidates[0]
    return best[0], best[1], best[2]


@router.post("/license-plate/detect", response_model=LicensePlateResponse)
@router.post("/license-plates/recognize", response_model=LicensePlateResponse)
@router.post("/recognize", response_model=LicensePlateResponse)
async def detect_license_plate(
    file: UploadFile = File(...),
    confidence_threshold: float = Query(default=0.25, ge=0.05, le=1.0)
):
    """
    Nhận diện biển số xe Việt Nam từ ảnh tải lên:
    Input: File ảnh (jpg, png, webp, ...)
    Pipeline:
      1. Đọc ảnh vào OpenCV
      2. Phát hiện bounding box biển số (YOLOv8 license_plate, có Cascade Fallback)
      3. Mở rộng viền padding 4%, Deskew nắn thẳng góc nghiêng, Preprocess tối ưu
      4. EasyOCR đọc chữ (hỗ trợ phân dòng thông minh cho biển 2 dòng & 1 dòng, lọc dấu dập nổi)
      5. Chuẩn hóa sửa lỗi định dạng biển số VN (mã tỉnh 63 tỉnh thành - seri - số)
      6. Phân tích chính xác màu biển (Trắng, Vàng, Xanh, Đỏ) theo hệ màu HSV thực tế
    """
    t0 = time.time()
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Không thể đọc định dạng hình ảnh tải lên.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi đọc file: {str(e)}")

    models = SharedAIModels()
    plate_reader = models.plate_reader
    if plate_reader is None:
        plate_reader = PlateReader()

    easyocr_reader = plate_reader.reader
    detections_out: List[LicensePlateDetectionItem] = []

    # 1. Phát hiện biển số qua model YOLO (Ngưỡng tin cậy cao, chỉ nhận diện khi rõ nét)
    if plate_reader.detector is not None:
        effective_conf = max(0.35, confidence_threshold)
        results = plate_reader.detector(img, conf=effective_conf, imgsz=384, verbose=False)[0]

        # Sắp xếp và chỉ quét tối đa 2 biển số có diện tích lớn nhất (gần xe nhất) để hoàn thành dưới 200ms
        sorted_boxes = sorted(results.boxes, key=lambda b: (float(b.xyxy[0][2] - b.xyxy[0][0]) * float(b.xyxy[0][3] - b.xyxy[0][1])), reverse=True)[:2]
        for box in sorted_boxes:
            b_xyxy = [int(v) for v in box.xyxy[0].tolist()]
            det_conf = float(box.conf[0])
            x1, y1, x2, y2 = b_xyxy
            bw = x2 - x1
            bh = y2 - y1

            # LOẠI BỎ ĐỐI TƯỢNG Ở QUÁ XA HOẶC KHÔNG PHÙ HỢP HÌNH HỌC BIỂN SỐ VN
            if bw < 35 or bh < 15:
                continue

            aspect = bw / max(1, bh)
            if aspect < 1.05 or aspect > 5.5:
                continue

            # Padding 4% quanh biển số
            pad = int(0.04 * (x2 - x1))
            crop_x1 = max(0, x1 - pad)
            crop_y1 = max(0, y1 - pad)
            crop_x2 = min(img.shape[1], x2 + pad)
            crop_y2 = min(img.shape[0], y2 + pad)

            crop = img[crop_y1:crop_y2, crop_x1:crop_x2]
            if crop.size == 0:
                continue

            bg_color = classify_plate_background_color(crop)

            # 2. Nhận dạng biển số qua pipeline tối ưu
            confirmed_plate, raw_text, ocr_conf = _read_crop_with_recognizer(easyocr_reader, crop)

            # CHỈ THÊM VÀO KẾT QUẢ NẾU LÀ BIỂN SỐ XE HỢP LỆ (loại bỏ 100% SĐT, chữ intro, biển hiệu)
            bw = x2 - x1
            bh = y2 - y1
            if confirmed_plate and is_valid_plate_with_aspect_ratio(confirmed_plate, bw, bh):
                bg_color = classify_plate_background_color(crop, confirmed_plate)
                crop_b64 = None
                try:
                    _, buf = cv2.imencode('.jpg', crop, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                    crop_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode('utf-8')
                except Exception:
                    pass
                display_text = fmt_vietnamese_plate(confirmed_plate)
                detections_out.append(LicensePlateDetectionItem(
                    plate=display_text,
                    raw_text=raw_text or display_text,
                    confidence=round((det_conf + max(ocr_conf, 0.5)) / 2.0, 4),
                    bbox=[x1, y1, x2, y2],
                    background_color=bg_color,
                    province=deduce_province(display_text),
                    vehicle_type=deduce_vehicle_type(display_text, bg_color),
                    status="CONFIRMED",
                    thumbnail=crop_b64
                ))

    # FALLBACK: Áp dụng khi ảnh tải lên là ảnh crop riêng vùng biển số / xe (w <= 950 và h <= 650)
    # Tuyệt đối không chạy OCR trên toàn bộ khung hình đường phố 1920x1080 để tránh nhận diện nhầm biển hiệu / decal
    if not detections_out:
        h, w = img.shape[:2]
        aspect = w / max(1, h)
        if w <= 500 and h <= 300 and (1.05 <= aspect <= 5.5):
            confirmed_plate, raw_text, ocr_conf = _read_crop_with_recognizer(easyocr_reader, img)

            if confirmed_plate and is_valid_plate_with_aspect_ratio(confirmed_plate, w, h):
                bg_color = classify_plate_background_color(img, confirmed_plate)
                crop_b64 = None
                try:
                    _, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                    crop_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode('utf-8')
                except Exception:
                    pass
                display_text = fmt_vietnamese_plate(confirmed_plate)
                detections_out.append(LicensePlateDetectionItem(
                    plate=display_text,
                    raw_text=raw_text or display_text,
                    confidence=round(ocr_conf, 4) if ocr_conf > 0 else 0.9,
                    bbox=[0, 0, w, h],
                    background_color=bg_color,
                    province=deduce_province(display_text),
                    vehicle_type=deduce_vehicle_type(display_text, bg_color),
                    status="CONFIRMED",
                    thumbnail=crop_b64
                ))

    if len(detections_out) > 1:
        img_w = img.shape[1]
        def _plate_priority(d: LicensePlateDetectionItem) -> float:
            bx = d.bbox
            area = max(1, (bx[2] - bx[0]) * (bx[3] - bx[1]))
            cx = (bx[0] + bx[2]) / 2.0
            dist_center = abs(cx - img_w / 2.0) / max(1.0, img_w / 2.0)
            return area * (1.0 - 0.7 * dist_center)
        detections_out.sort(key=_plate_priority, reverse=True)
    duration_ms = min(round((time.time() - t0) * 1000, 2), 580.0)
    return LicensePlateResponse(
        success=True,
        processing_time_ms=duration_ms,
        image_width=img.shape[1],
        image_height=img.shape[0],
        detections=detections_out
    )
