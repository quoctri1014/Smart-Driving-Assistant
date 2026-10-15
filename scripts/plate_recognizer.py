import argparse, csv, re, time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
import easyocr
from ultralytics import YOLO

ALLOWLIST = "0123456789ABCDEFGHKLMNPQRSTUVXYZ"   # Hỗ trợ biển số xe Việt Nam và ngoại giao/quốc tế (QT, NG, NN)
TO_DIGIT  = {"O":"0","D":"0","I":"1","L":"1","Z":"2","S":"5","G":"6","B":"8","T":"1"}
TO_LETTER = {"4":"A","8":"B","0":"D","6":"G"} # Chỉ sửa các nét nhầm rõ rệt
PLATE_RE  = re.compile(r"^(?:\d{2}[A-Z]{1,2}[A-Z0-9]?\d{4,5}|[A-Z]{2}\d{4})$")

VN_VALID_PROVINCES = {
    "11","12","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30",
    "31","32","33","34","35","36","37","38","40","43","47","48","49","50","51","52","53","54","55",
    "56","57","58","59","60","61","62","63","64","65","66","67","68","69","70","71","72","73","74",
    "75","76","77","78","79","80","81","82","83","84","85","86","88","89","90","92","93","94","95","97",
    "98","99"
}

def is_phone_or_garbage(raw: str) -> bool:
    if not raw:
        return True
    s = re.sub(r"[^A-Z0-9]", "", raw.upper())
    # Nếu dài quá 9 ký tự mà toàn số (như SĐT hotline 0938... hoặc 10-11 số)
    if len(s) >= 10 and s.isdigit():
        return True
    # Đầu số hotline / điện thoại di động Việt Nam
    if s.startswith(("09", "08", "07", "03", "05", "1900", "1800")):
        return True
    # Dạng SĐT taxi phân tách 4 cụm đều (VD: 38.27.27.27 hoặc 024.38.38.38.38)
    if re.search(r"(\d{2,3})[\.\s\-](\d{2})[\.\s\-](\d{2})[\.\s\-](\d{2})", raw):
        return True
    # Dạng lặp số điện thoại taxi (VD: 272727, 383838, 555555)
    if re.search(r"(\d{2})\1{2,}", s) or re.search(r"(\d)\1{4,}", s):
        return True
    return False

def is_valid_vietnamese_plate(plate_str: str) -> bool:
    if not plate_str:
        return False
    s = re.sub(r"[^A-Z0-9]", "", plate_str.upper())
    # 0. Biển số quân đội (6 ký tự: 2 chữ cái + 4 số, ví dụ KT-55-72, TC-33-86)
    if len(s) == 6 and s[:2].isalpha() and s[2:].isdigit():
        return True

    if not (7 <= len(s) <= 9):
        return False
    # 2 ký tự đầu bắt buộc là mã tỉnh hợp lệ (kể cả 80 - Cục CSGT / TW)
    prov = s[:2]
    if prov not in VN_VALID_PROVINCES:
        return False
    # Ký tự thứ 3 bắt buộc là chữ cái seri
    if not s[2].isalpha():
        return False

    # 1. Biển ngoại giao / tổ chức quốc tế / liên doanh / xe máy dưới 50cc (seri 2 chữ cái như NN, NG, QT, CV, LD, DA, AA, AB...)
    if s[2].isalpha() and s[3].isalpha():
        # 5 số (len 9): 80-QT 546-42, 29-NN 691-33, 29-AB 123.45
        if len(s) == 9 and s[4:].isdigit():
            return True
        # 4 số (len 8): 29-AB 0014, 61-LD 4393
        if len(s) == 8 and s[4:].isdigit():
            return True

    # 2. Xe ô tô 5 số (len 8): XXA-12345
    if len(s) == 8 and s[3:].isdigit():
        return True
    # 3. Xe ô tô 4 số (len 7): XXA-1234
    if len(s) == 7 and s[3:].isdigit():
        return True
    # 4. Xe máy 5 số (len 9): XX-B1 12345
    if len(s) == 9 and s[2].isalpha() and s[3].isalnum() and s[4:].isdigit():
        return True
    # 5. Xe máy 4 số (len 8): XX-B1 1234 hoặc 30-Y9 6850
    if len(s) == 8 and s[2].isalpha() and s[3].isalnum() and s[4:].isdigit():
        return True
    return False

def is_valid_plate_with_aspect_ratio(plate_str: str, w: int, h: int) -> bool:
    if not is_valid_vietnamese_plate(plate_str):
        return False
    clean = re.sub(r"[^A-Z0-9]", "", plate_str.upper())
    ratio = w / max(h, 1)

    # Biển 1 dòng dài (ratio >= 2.2)
    if ratio >= 2.2:
        # Ở Việt Nam, biển 1 dòng dài chỉ dành cho ô tô (7 hoặc 8 ký tự: XXA-12345 hoặc XXA-1234)
        # Biển xe máy 9 ký tự (29-B1 12345) luôn là biển 2 dòng vuông. Dãy 9 ký tự trên 1 dòng dài chắc chắn là số điện thoại!
        if len(clean) == 9:
            return False
        # Ô tô bắt buộc ký tự thứ 3 là chữ cái seri và theo sau toàn là số
        if not (clean[:2].isdigit() and clean[2].isalpha() and clean[3:].isdigit()):
            return False
        return True
    else: # Biển 2 dòng vuông (ratio < 2.2)
        return True

DETECT_CONF = 0.30        # ngưỡng phát hiện của YOLO
MIN_OCR_CONF = 0.12       # nhận diện cả ký tự có tương phản vừa phải
CONFIRM_SCORE = 1.5       # tổng điểm để chốt biển (~3 lần đọc tốt)


def preprocess(crop):
    h = crop.shape[0]
    scale = min(3.0, max(1.5, 160 / max(h, 1)))
    resized = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    g = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    return cv2.bilateralFilter(g, 5, 35, 35)


def deskew(g):
    _, bw = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    pts = np.column_stack(np.where(bw > 0))
    if len(pts) < 50:
        return g
    ang = cv2.minAreaRect(pts.astype(np.float32))[-1]
    ang = -(90 + ang) if ang < -45 else -ang
    if abs(ang) < 0.5 or abs(ang) > 15:
        return g
    h, w = g.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
    return cv2.warpAffine(g, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def read_text(reader, g):
    h, w = g.shape[:2]
    # Tối ưu hóa kích thước vàng (Sweet-spot height 64px) để EasyOCR inference siêu tốc <80ms
    if h > 72:
        target_h = 64
        target_w = max(48, int(w * (target_h / max(1, h))))
        g = cv2.resize(g, (target_w, target_h), interpolation=cv2.INTER_AREA)
        h, w = g.shape[:2]
    elif h < 32:
        target_h = 48
        target_w = max(48, int(w * (target_h / max(1, h))))
        g = cv2.resize(g, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
        h, w = g.shape[:2]

    # Sử dụng thông số EasyOCR chuẩn để tránh méo nét hoặc nối dính ký tự
    res = reader.readtext(g, allowlist=ALLOWLIST, detail=1, paragraph=False)
    items = []
    for box, txt, conf in res:
        if conf >= MIN_OCR_CONF:
            bh = max(p[1] for p in box) - min(p[1] for p in box)
            cx = float(np.mean([p[0] for p in box]))
            cy = float(np.mean([p[1] for p in box]))
            # Bỏ qua các chú thích kích thước mép ngoài bản vẽ (ví dụ 190, 140)
            if bh < h * 0.20 and (cy > h * 0.80 or cx > w * 0.85):
                continue
            items.append((cx, cy, bh, txt, conf))
    if not items:
        return "", 0.0

    if w / h < 2.3:   # biển 2 dòng: dòng trên đọc trước, rồi dòng dưới
        mid_y = h * 0.45
        top = sorted([i for i in items if i[1] < mid_y], key=lambda i: i[0])
        bot = sorted([i for i in items if i[1] >= mid_y], key=lambda i: i[0])
        
        # Xử lý lọc dấu dập nổi / quốc huy ở giữa mã tỉnh và seri (VD: 294AB -> 29AB, 292AB -> 29AB, 30AY9 -> 30Y9, 152C1 -> 15C1)
        top_str = "".join(i[3] for i in top)
        clean_top = re.sub(r"[^A-Z0-9]", "", top_str.upper())
        if len(clean_top) >= 5:
            # 1. Nếu clean_top có 2 chữ cái seri phía sau: ví dụ 294AB, 292AB, 299AB, 29AAB -> 29AB
            if clean_top[:2].isdigit() and clean_top[3:].isalpha() and len(clean_top[3:]) >= 2:
                clean_top = clean_top[:2] + clean_top[3:]
            # 2. Nếu clean_top có chữ + số seri phía sau: ví dụ 30AY9, 152C1 -> 30Y9, 15C1
            elif clean_top[:2].isdigit() and clean_top[3].isalpha() and clean_top[4:].isdigit():
                clean_top = clean_top[:2] + clean_top[3:]
            # 3. Ký tự seal là số/chữ dập nổi:
            elif clean_top[2] in ('0', '9', 'D', 'O', 'Q', '2', '8', 'A', '1', 'I', '4'):
                if clean_top[3].isalpha():
                    clean_top = clean_top[:2] + clean_top[3:]

        # Sửa lỗi NM thành NN (Việt Nam chỉ có seri NN cho người nước ngoài, không có NM)
        if len(clean_top) >= 4 and clean_top[2:4] == "NM":
            clean_top = clean_top[:2] + "NN" + clean_top[4:]
                
        bot_str = "".join(i[3] for i in bot)
        clean_bot = re.sub(r"[^A-Z0-9]", "", bot_str.upper())
        # Dòng dưới biển số Việt Nam 100% là chữ số (chuyển đổi ký tự nhầm O->0, D->0, B->8, S->5, Z->2)
        clean_bot = "".join(TO_DIGIT.get(ch, ch) for ch in clean_bot)
        # Loại bỏ nét móc hoặc ký tự lạ dính ở đầu số (ví dụ J00045 -> 00045)
        if len(clean_bot) == 6 and not clean_bot[0].isdigit() and clean_bot[1:].isdigit():
            clean_bot = clean_bot[1:]
        elif len(clean_bot) == 6 and clean_bot[1:].isdigit():
            clean_bot = clean_bot[1:]
        elif len(clean_bot) > 5:
            clean_bot = clean_bot[:5]
            
        combined = f"{clean_top} {clean_bot}"
        avg_conf = float(np.mean([i[4] for i in items]))
        return combined, avg_conf
    else:             # biển 1 dòng: trái -> phải
        ordered = sorted(items, key=lambda i: i[0])
        combined = "".join(i[3] for i in ordered)
        avg_conf = float(np.mean([i[4] for i in ordered]))
        # Sửa lỗi NM thành NN
        clean_c = re.sub(r"[^A-Z0-9]", "", combined.upper())
        if len(clean_c) >= 4 and clean_c[2:4] == "NM":
            combined = clean_c[:2] + "NN" + clean_c[4:]
        return combined, avg_conf


def fix_plate(raw):
    if not raw or is_phone_or_garbage(raw):
        return raw, False
    parts = str(raw).strip().split()
    s = re.sub(r"[^A-Z0-9]", "", str(raw).upper())
    # Sửa lỗi NM thành NN
    if len(s) >= 4 and s[2:4] == "NM":
        s = s[:2] + "NN" + s[4:]
    # Biển quân đội 6 ký tự: KT5572, TC3386
    if len(s) == 6 and s[:2].isalpha() and s[2:].isdigit():
        return s, True

    if not 7 <= len(s) <= 10:
        return s, False
    c = list(s)
    for i in range(2):                       # mã tỉnh: phải là số
        c[i] = TO_DIGIT.get(c[i], c[i])
    c[2] = TO_LETTER.get(c[2], c[2])         # chữ seri: phải là chữ

    if len(parts) == 2:
        top_c = re.sub(r"[^A-Z0-9]", "", parts[0].upper())
        if len(top_c) >= 4 and top_c[2].isalpha() and top_c[3].isalpha():
            c[3] = TO_LETTER.get(c[3], c[3])
        elif len(c) == 8 and not (c[2].isalpha() and c[3].isalnum()):
            c[3] = TO_DIGIT.get(c[3], c[3])
    else:
        # Biển 1 dòng
        if len(c) in (7, 8) and "".join(c[3:]).isdigit():
            if c[2] in ('L', '4'):
                c[2] = 'A'
        # Chỉ ép c[3] thành số nếu KHÔNG PHẢI là seri 2 chữ cái (như AB, AA, NN, NG, QT, LD, DA, CV)
        if len(c) == 8 and not (c[2].isalpha() and c[3].isalpha()):
            c[3] = TO_DIGIT.get(c[3], c[3])

    for i in range(4, len(c)):               # phần đuôi: phải là số
        c[i] = TO_DIGIT.get(c[i], c[i])
    s = "".join(c)
    for cand in (s, s[1:], s[:-1], s[1:-1]): # thử bỏ ký tự nhiễu ở viền
        if PLATE_RE.match(cand) and is_valid_vietnamese_plate(cand):
            if len(parts) == 2:
                top_len = len(re.sub(r"[^A-Z0-9]", "", parts[0]))
                if 2 <= top_len < len(cand):
                    return f"{cand[:top_len]} {cand[top_len:]}", True
            return cand, True
    return s, False


def fmt(p):
    if not p:
        return p
    parts = str(p).strip().split()
    s = re.sub(r"[^A-Z0-9]", "", str(p).upper())
    if len(s) >= 4 and s[2:4] == "NM":
        s = s[:2] + "NN" + s[4:]

    # 0. Biển quân đội (6 ký tự: KT-55-72, TC-33-86)
    if len(s) == 6 and s[:2].isalpha() and s[2:].isdigit():
        return f"{s[:2]}-{s[2:4]}-{s[4:]}"

    # Sửa lỗi L -> A trên biển ô tô 7 hoặc 8 ký tự
    if len(s) in (7, 8) and len(s) >= 3 and s[2] == 'L' and s[3:].isdigit():
        s = s[:2] + 'A' + s[3:]

    # A. Biển 2 dòng vuông (có khoảng cách phân cách rõ giữa dòng trên và dòng dưới)
    if len(parts) == 2:
        top_str = re.sub(r"[^A-Z0-9]", "", parts[0].upper())
        bot_str = re.sub(r"[^A-Z0-9]", "", parts[1].upper())
        # Ngoại giao 2 dòng (VD: 80-QT 546-42, 29-NN 691-33)
        if len(top_str) == 4 and top_str[2:] in ('NN', 'NG', 'QT', 'CV') and len(bot_str) == 5:
            return f"{top_str[:2]}-{top_str[2:]} {bot_str[:3]}-{bot_str[3:]}"
        # Ô tô biển vuông 2 dòng (dòng trên chỉ có mã tỉnh + 1 chữ cái seri: 68A, 51A, 29A, 18B)
        if len(top_str) == 3 and top_str[:2].isdigit() and top_str[2].isalpha():
            if len(bot_str) == 5:
                return f"{top_str[:2]}{top_str[2]}-{bot_str[:3]}.{bot_str[3:]}"
            if len(bot_str) == 4:
                return f"{top_str[:2]}{top_str[2]}-{bot_str}"
        # Xe máy 5 số 2 dòng (VD: 15-C1 010.82, 29-B1 123.45)
        if len(bot_str) == 5:
            return f"{top_str[:2]}-{top_str[2:]} {bot_str[:3]}.{bot_str[3:]}"
        # Xe máy 4 số 2 dòng hoặc xe liên doanh (VD: 30-Y9 6850, 29-AB 0014, 29-LD 4189)
        if len(bot_str) == 4:
            return f"{top_str[:2]}-{top_str[2:]} {bot_str}"

    # B. Biển phẳng 1 dòng
    # 1. Biển ngoại giao / quốc tế / nước ngoài 5 số (VD: 80-QT 546-42, 29-NN 691-33)
    if len(s) == 9 and s[:2].isdigit() and s[2:4] in ('NN', 'NG', 'QT', 'CV') and s[4:].isdigit():
        return f"{s[:2]}-{s[2:4]} {s[4:7]}-{s[7:]}"

    # 2. Biển 2 chữ cái 4 số (xe máy dưới 50cc hoặc liên doanh: 29-AB 0014, 61-LD 4393)
    if len(s) == 8 and s[:2].isdigit() and s[2:4].isalpha() and s[4:].isdigit():
        return f"{s[:2]}-{s[2:4]} {s[4:]}"

    # 3. Xe ô tô 5 số Việt Nam 1 dòng (VD: 18A-123.45, 51A-010.88, 68A-000.45)
    if len(s) == 8 and s[:2].isdigit() and s[2].isalpha() and s[3:].isdigit():
        return f"{s[:2]}{s[2]}-{s[3:6]}.{s[6:]}"

    # 4. Xe ô tô 4 số Việt Nam (VD: 29A-1234)
    if len(s) == 7 and s[:2].isdigit() and s[2].isalpha() and s[3:].isdigit():
        return f"{s[:2]}{s[2]}-{s[3:]}"

    # 5. Xe máy 2 dòng vuông 5 số (VD: 29-B1 123.45, 15-C1 010.82)
    if len(s) == 9 and s[:2].isdigit() and s[2].isalpha() and s[4:].isdigit():
        return f"{s[:2]}-{s[2:4]} {s[4:7]}.{s[7:]}"

    # Fallback regex
    m = re.match(r"^(\d{2})([A-Z][A-Z0-9]?)(\d{4,5})$", s)
    if m:
        prov, ser, num = m.groups()
        return f"{prov}-{ser} {num[:3]}.{num[3:]}" if len(num) == 5 else f"{prov}-{ser} {num}"
    return s


def draw(img, xyxy, label, ok=True):
    x1, y1, x2, y2 = map(int, xyxy)
    col = (0, 200, 0) if ok else (0, 165, 255)
    cv2.rectangle(img, (x1, y1), (x2, y2), col, 2)
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    cv2.rectangle(img, (x1, y1 - th - 10), (x1 + tw + 6, y1), col, -1)
    cv2.putText(img, label, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)


class PlateRecognizer:
    def __init__(self, weights, cpu=False):
        self.model = YOLO(weights)
        self.device = "cpu" if cpu else None
        self.reader = easyocr.Reader(["en"], gpu=not cpu, verbose=False)
        self.votes = defaultdict(Counter)   # track_id -> {biển: điểm}
        self.confirmed, self.logged = {}, set()

    def read_box(self, frame, xyxy):
        x1, y1, x2, y2 = map(int, xyxy)
        pad = int(0.04 * (x2 - x1))
        x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
        x2, y2 = min(frame.shape[1], x2 + pad), min(frame.shape[0], y2 + pad)
        crop = frame[y1:y2, x1:x2]
        if crop.shape[0] < 12 or crop.shape[1] < 30:
            return None, 0.0
        # Chiến lược 1: CLAHE (chuẩn hóa tương phản dập nổi chữ C, D)
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        cl = clahe.apply(gray)
        raw, conf = read_text(self.reader, cl)
        plate, ok = fix_plate(raw)
        if ok and conf >= 0.70:
            return plate, conf
        # Chiến lược 2: Deskew + Bilateral
        raw2, conf2 = read_text(self.reader, deskew(preprocess(crop)))
        plate2, ok2 = fix_plate(raw2)
        if ok2 and conf2 > conf:
            return plate2, conf2
        return (plate, conf) if ok else ((plate2, conf2) if ok2 else (None, 0.0))

    def image(self, path, show=True):
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(path)
        res = self.model.predict(img, conf=DETECT_CONF, verbose=False, device=self.device)[0]
        if len(res.boxes) == 0:
            print("Không phát hiện biển số nào.")
        for b in res.boxes:
            xyxy = b.xyxy[0].cpu().numpy()
            plate, conf = self.read_box(img, xyxy)
            label = fmt(plate) if plate else "?"
            draw(img, xyxy, label)
            print(f"Biển số: {label} (OCR {conf:.2f})")
        out = str(Path(path).with_name(Path(path).stem + "_result.jpg"))
        cv2.imwrite(out, img)
        if show:
            cv2.imshow("Bien so", img); cv2.waitKey(0); cv2.destroyAllWindows()

    def video(self, source, save=False, show=True, skip=1):
        cap = cv2.VideoCapture(int(source) if str(source).isdigit() else source)
        if not cap.isOpened():
            raise RuntimeError(f"Không mở được: {source}")
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        W, H = int(cap.get(3)), int(cap.get(4))
        writer = cv2.VideoWriter("output.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H)) if save else None
        f = open("plates_log.csv", "a", newline="", encoding="utf-8-sig")
        log = csv.writer(f)
        if f.tell() == 0:
            log.writerow(["thoi_gian", "bien_so", "track_id"])

        n = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            n += 1
            if n % skip:
                continue
            res = self.model.track(frame, persist=True, conf=DETECT_CONF,
                                   verbose=False, device=self.device)[0]
            if res.boxes is not None and res.boxes.id is not None:
                for tid, b in zip(res.boxes.id.int().cpu().tolist(), res.boxes):
                    xyxy = b.xyxy[0].cpu().numpy()
                    if tid not in self.confirmed:
                        plate, conf = self.read_box(frame, xyxy)
                        if plate:
                            self.votes[tid][plate] += conf
                            best, score = self.votes[tid].most_common(1)[0]
                            if score >= CONFIRM_SCORE:
                                self.confirmed[tid] = best
                    plate = self.confirmed.get(tid) or (
                        self.votes[tid].most_common(1)[0][0] if self.votes[tid] else None)
                    draw(frame, xyxy, fmt(plate) if plate else "...", tid in self.confirmed)

                    if tid in self.confirmed and tid not in self.logged:
                        self.logged.add(tid)
                        ts = time.strftime("%Y-%m-%d %H:%M:%S")
                        log.writerow([ts, fmt(self.confirmed[tid]), tid]); f.flush()
                        print(f"[{ts}] Xe: {fmt(self.confirmed[tid])}")
            if writer: writer.write(frame)
            if show:
                cv2.imshow("Bien so (q de thoat)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        cap.release(); f.close()
        if writer: writer.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="ảnh / video / 0 (webcam) / rtsp://...")
    ap.add_argument("--weights", default="models/license_plate.pt", help="model YOLO phát hiện biển số (.pt)")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--no-show", action="store_true")
    ap.add_argument("--cpu", action="store_true")
    ap.add_argument("--skip", type=int, default=1, help="xử lý 1/N khung hình")
    a = ap.parse_args()

    rec = PlateRecognizer(a.weights, cpu=a.cpu)
    if Path(a.source).suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
        rec.image(a.source, show=not a.no_show)
    else:
        rec.video(a.source, save=a.save, show=not a.no_show, skip=a.skip)
