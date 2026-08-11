"""
plate_reader.py
----------------
Nhận diện biển số xe. Vì không phải lúc nào cũng có sẵn model YOLO
chuyên phát hiện biển số, module này dùng cách tiếp cận đơn giản và hiệu quả:
  1. Cắt vùng ảnh của xe (box) ra từ khung hình.
  2. Chạy EasyOCR trên vùng ảnh đó để đọc mọi ký tự.
  3. Lọc kết quả theo mẫu regex giống biển số xe Việt Nam (vd: 29N8-0100, 30A-123.45).

Muốn chính xác hơn: train thêm 1 model YOLO chuyên phát hiện VỊ TRÍ biển số
(dataset kiểu "license-plate-recognition" trên Roboflow) rồi crop đúng vùng
biển số trước khi đưa vào EasyOCR. Xem README phần "Nâng cấp".
"""

import re
import cv2
import easyocr
from ai_engine import config

# Mẫu biển số VN phổ biến: 2 số + 1-2 chữ + (dấu - hoặc khoảng trắng) + 4-5 số
PLATE_REGEX = re.compile(r"^[0-9]{2}[A-Z]{1,2}[0-9]?[\-\. ]?[0-9]{3,5}$")


class PlateReader:
    def __init__(self, languages=config.OCR_LANGUAGES):
        self.reader = easyocr.Reader(languages, gpu=True)

    def read_plate(self, frame, box):
        """
        Trả về chuỗi biển số nếu đọc được, ngược lại None.
        box: (x1, y1, x2, y2) của phương tiện (không cần chính xác tuyệt đối,
        EasyOCR sẽ tự tìm vùng có chữ trong crop này).
        """
        x1, y1, x2, y2 = [int(v) for v in box]
        x1, y1 = max(0, x1), max(0, y1)
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None

        # Phóng to nhẹ giúp OCR đọc tốt hơn với vùng ảnh nhỏ
        crop = cv2.resize(crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        results = self.reader.readtext(crop)

        best_candidate = None
        for _, text, conf in results:
            cleaned = text.upper().replace(" ", "").strip()
            if conf < config.CONF_PLATE:
                continue
            if PLATE_REGEX.match(cleaned):
                return cleaned
            if best_candidate is None and len(cleaned) >= 5:
                best_candidate = cleaned  # fallback: chuỗi dài nhất có vẻ hợp lý
        return best_candidate
