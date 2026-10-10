"""Multi-frame Vietnamese license plate reader.

The existing vehicle tracker remains the owner of object identity and vote
counts.  This module only keeps a bounded crop/quality cache for each existing
track ID and turns OCR observations into CONFIRMED, UNCERTAIN, or NOT_READABLE
results.  It never inserts or guesses characters that EasyOCR did not return.
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
import re

import cv2
import numpy as np

try:
    import config
except ImportError:
    import ai_engine.config as config


CONFIRMED = "CONFIRMED"
UNCERTAIN = "UNCERTAIN"
NOT_READABLE = "NOT_READABLE"

# Hỗ trợ cả biển số Việt Nam (29A-888.88, 59-P2 535.09, 29C-122.21) và các định dạng quốc tế (AAS-8797)
FULL_PLATE_REGEX = re.compile(
    r"^(?:"
    r"[0-9]{2}[A-Z]{1}[0-9A-Z]{0,1}[0-9]{4,5}"    # VN car/moto: 51D57579, 59P253509, 29C12221
    r"|[A-Z]{2,3}[0-9]{3,5}"                       # Intl: AAS8797
    r")$"
)

DIGIT_TO_LETTER = {'4': 'A', '5': 'S', '0': 'O', '8': 'B', '1': 'I', '2': 'Z', '6': 'G'}
LETTER_TO_DIGIT = {'A': '4', 'S': '5', 'O': '0', 'D': '0', 'B': '8', 'I': '1', 'Z': '2', 'G': '6'}

def classify_plate_background_color(plate_crop: np.ndarray, plate_str: str = "") -> str:
    """
    Phân loại màu biển số xe Việt Nam:
    - COMMERCIAL_YELLOW: Biển vàng (xe kinh doanh vận tải / taxi / xe công nghệ)
    - GOVERNMENT_BLUE: Biển xanh (xe cơ quan hành chính nhà nước, công an)
    - MILITARY_RED: Biển đỏ (xe quân đội)
    - CIVILIAN_WHITE: Biển trắng (xe cá nhân, doanh nghiệp, ngoại giao/quốc tế)
    """
    if plate_crop is None or plate_crop.size == 0:
        return "CIVILIAN_WHITE"
    try:
        clean_str = re.sub(r"[^A-Z0-9]", "", str(plate_str).upper()) if plate_str else ""

        # Biển quân đội bắt đầu bằng 2 chữ cái quân sự (KT, TC, TH, QA, QB, AA, BB...)
        if len(clean_str) == 6 and clean_str[:2].isalpha() and clean_str[2:].isdigit():
            return "MILITARY_RED"

        # Biển ngoại giao / quốc tế / liên doanh (QT, NG, NN, CV, LD, DA) luôn có nền trắng
        if len(clean_str) >= 4 and clean_str[2:4] in ('NN', 'NG', 'QT', 'CV', 'LD', 'DA'):
            return "CIVILIAN_WHITE"

        # Biển xe kinh doanh vận tải (seri E, F, G như 29E, 29F, 50E...) luôn có nền vàng
        if len(clean_str) >= 3 and clean_str[:2].isdigit() and clean_str[2] in ('E', 'F', 'G'):
            return "COMMERCIAL_YELLOW"

        is_provincial_plate = len(clean_str) >= 2 and clean_str[:2].isdigit()

        # Cắt bớt 8% viền mép ngoài để triệt tiêu viền bounding box, bóng đổ và sơn thân xe
        h, w = plate_crop.shape[:2]
        if h > 20 and w > 30:
            inner = plate_crop[int(h * 0.08):int(h * 0.92), int(w * 0.06):int(w * 0.94)]
        else:
            inner = plate_crop

        total_pixels = float(inner.shape[0] * inner.shape[1])
        if total_pixels <= 0:
            return "CIVILIAN_WHITE"

        hsv = cv2.cvtColor(inner, cv2.COLOR_BGR2HSV)
        b = inner[:, :, 0].astype(float)
        g = inner[:, :, 1].astype(float)
        r = inner[:, :, 2].astype(float)

        # 1. Phát hiện màu XANH (GOVERNMENT_BLUE)
        blue_dominant = (b > r + 25) & (b > g + 6) & (b > 75)
        blue_hsv = cv2.inRange(hsv, np.array([95, 50, 40]), np.array([135, 255, 255]))
        blue_mask = cv2.bitwise_and(blue_hsv, (blue_dominant.astype(np.uint8) * 255))
        blue_ratio = np.count_nonzero(blue_mask) / total_pixels

        # 2. Phát hiện màu ĐỎ (MILITARY_RED)
        # Biển đỏ quân đội có màu đỏ sẫm: R phải áp đảo cả G và B rõ rệt (r > 1.45*g và r > 1.45*b)
        red_hsv = cv2.bitwise_or(
            cv2.inRange(hsv, np.array([0, 50, 40]), np.array([12, 255, 255])),
            cv2.inRange(hsv, np.array([165, 50, 40]), np.array([180, 255, 255]))
        )
        red_rgb = (r > 1.45 * g) & (r > 1.45 * b) & (r > 70)
        red_mask = cv2.bitwise_and(red_hsv, (red_rgb.astype(np.uint8) * 255))
        red_ratio = np.count_nonzero(red_mask) / total_pixels

        # 3. Phát hiện màu VÀNG (COMMERCIAL_YELLOW)
        hsv_yellow = cv2.inRange(hsv, np.array([12, 35, 35]), np.array([42, 255, 255]))
        rgb_yellow = (r > b + 25) & (g > b + 15) & (r > 50) & (g > 40)
        yellow_mask = cv2.bitwise_and(hsv_yellow, (rgb_yellow.astype(np.uint8) * 255))
        yellow_ratio = np.count_nonzero(yellow_mask) / total_pixels

        # Kiểm tra seri biển số xe dịch vụ vận tải Việt Nam (VD: 29E, 29F, 50E, 50F...)
        is_commercial_series = False
        if len(clean_str) >= 3 and clean_str[:2].isdigit() and clean_str[2] in ('E', 'F', 'G'):
            is_commercial_series = True

        if is_commercial_series:
            return "COMMERCIAL_YELLOW"
        if blue_ratio >= 0.16 and blue_ratio > yellow_ratio and blue_ratio > red_ratio:
            return "GOVERNMENT_BLUE"
        if not is_provincial_plate and red_ratio >= 0.16 and red_ratio > yellow_ratio and red_ratio > blue_ratio:
            return "MILITARY_RED"
        if yellow_ratio >= 0.18 and yellow_ratio > blue_ratio and yellow_ratio > red_ratio:
            return "COMMERCIAL_YELLOW"

        return "CIVILIAN_WHITE"
    except Exception:
        return "CIVILIAN_WHITE"

def format_plate_display(raw: str) -> str:
    if not raw:
        return raw
    s = raw.strip().upper().replace(" ", "").replace("-", "").replace(".", "")
    s = re.sub(r"^[^A-Z0-9]+|[^A-Z0-9]+$", "", s)
    if len(s) >= 4 and s[2:4] == "NM":
        s = s[:2] + "NN" + s[4:]

    # 0. Biển quân đội (6 ký tự: KT-55-72, TC-33-86)
    if len(s) == 6 and s[:2].isalpha() and s[2:].isdigit():
        return f"{s[:2]}-{s[2:4]}-{s[4:]}"

    # 1. Loại bỏ nhiễu viền / ốc biển số ở cuối nếu trước đó đã là 1 biển hoàn chỉnh
    clean_pfx = "".join(DIGIT_TO_LETTER.get(c, c) for c in s[:3])
    if len(s) == 8 and s[-1] in ("1", "I") and clean_pfx.isalpha() and s[3:-1].isdigit():
        s = s[:-1]

    # Sửa lỗi L -> A trên biển ô tô 7 hoặc 8 ký tự
    if len(s) in (7, 8) and len(s) >= 3 and s[2] == 'L' and s[3:].isdigit():
        s = s[:2] + 'A' + s[3:]

    # 2. Biển ngoại giao / quốc tế / nước ngoài 5 số (VD: 80-QT 546-42, 29-NN 691-33)
    if len(s) == 9 and s[:2].isdigit() and s[2:4] in ('NN', 'NG', 'QT', 'CV') and s[4:].isdigit():
        return f"{s[:2]}-{s[2:4]} {s[4:7]}-{s[7:]}"

    # 3. Biển số xe ô tô 5 số Việt Nam (VD: 51A-010.88, 68A-000.45)
    if len(s) == 8 and s[:2].isdigit() and 11 <= int(s[:2]) <= 99:
        if s[2].isalpha() and s[3:].isdigit():
            num = s[3:]
            return f"{s[:2]}{s[2]}-{num[:3]}.{num[3:]}"

    # 4. Biển số xe ô tô 4 số Việt Nam (VD: 29A-1234)
    if len(s) == 7 and s[:2].isdigit() and 11 <= int(s[:2]) <= 99:
        if s[2].isalpha() and s[3:].isdigit():
            return f"{s[:2]}{s[2]}-{s[3:]}"

    # 5. Biển 2 chữ cái 4 số (xe máy dưới 50cc hoặc liên doanh: 29-AB 0014, 61-LD 4393)
    if len(s) == 8 and s[:2].isdigit() and s[2:4].isalpha() and s[4:].isdigit():
        return f"{s[:2]}-{s[2:4]} {s[4:]}"

    # 6. Biển số xe máy 4 số truyền thống (VD: 30-Y9 6850, 29-B1 1234)
    if len(s) == 8 and s[:2].isdigit() and s[2].isalpha() and s[3].isalnum() and s[4:].isdigit():
        return f"{s[:2]}-{s[2:4]} {s[4:]}"

    # 7. Biển số xe máy 5 số (VD: 15-C1 010.82, 59-P2 535.09)
    if len(s) in (8, 9) and s[:2].isdigit() and 11 <= int(s[:2]) <= 99:
        if s[2].isalpha() and s[3].isalnum() and s[4:].isdigit():
            num = s[4:]
            if len(num) == 5:
                return f"{s[:2]}-{s[2:4]} {num[:3]}.{num[3:]}"
            else:
                return f"{s[:2]}-{s[2:4]} {num}"

    # 8. Biển số quốc tế 3 chữ cái + 4 số: AAS-8797
    if len(s) == 7 and s[3:].isdigit():
        clean_prefix = "".join(DIGIT_TO_LETTER.get(c, c) for c in s[:3])
        if clean_prefix.isalpha():
            return f"{clean_prefix}-{s[3:]}"

    return s


def order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(s)]      # top-left
    rect[2] = pts[np.argmax(s)]      # bottom-right
    rect[1] = pts[np.argmin(diff)]   # top-right
    rect[3] = pts[np.argmax(diff)]   # bottom-left
    return rect


def rectify_or_deskew_plate(plate_bgr: np.ndarray) -> np.ndarray:
    """Tự động phát hiện góc nghiêng và nắn thẳng phối cảnh hình chữ nhật."""
    if plate_bgr is None or plate_bgr.size == 0:
        return plate_bgr
    h, w = plate_bgr.shape[:2]
    if w < 24 or h < 12:
        return plate_bgr

    # 1. Thử tìm 4 góc của khung viền biển số bằng contour
    gray = cv2.cvtColor(plate_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 40, 140)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    best_pts = None
    max_area = 0
    min_area = h * w * 0.25

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        if len(approx) == 4 and area > max_area:
            best_pts = approx.reshape(4, 2)
            max_area = area

    if best_pts is not None:
        try:
            rect = order_points(best_pts)
            tl, tr, br, bl = rect
            width_a = np.linalg.norm(br - bl)
            width_b = np.linalg.norm(tr - tl)
            max_w = int(max(width_a, width_b))

            height_a = np.linalg.norm(tr - br)
            height_b = np.linalg.norm(tl - bl)
            max_h = int(max(height_a, height_b))

            if max_w >= 24 and max_h >= 10:
                dst = np.array([
                    [0, 0],
                    [max_w - 1, 0],
                    [max_w - 1, max_h - 1],
                    [0, max_h - 1]
                ], dtype="float32")
                M = cv2.getPerspectiveTransform(rect, dst)
                warped = cv2.warpPerspective(plate_bgr, M, (max_w, max_h))
                if warped.size > 0:
                    return warped
        except Exception:
            pass

    # 2. Phương án bổ trợ: Deskew dựa trên minAreaRect góc nghiêng của ký tự
    try:
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) > 50:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

            if abs(angle) > 1.5 and abs(angle) < 35.0:
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(plate_bgr, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                return rotated
    except Exception:
        pass

    return plate_bgr


def character_level_temporal_vote(observations: list) -> tuple:
    """
    Bỏ phiếu theo từng vị trí ký tự (Position-by-position voting) kết hợp trọng số confidence * quality.
    Ví dụ:
      Frame 1: AAS-8797 (conf 0.90)
      Frame 2: A4S-8797 (conf 0.65)
      Frame 3: AAS-8797 (conf 0.92)
      -> Vị trí 1: 'A' áp đảo '4' -> kết quả chốt là 'AAS-8797'.
    """
    if not observations:
        return "", 0.0, False

    formatted_items = []
    for obs in observations:
        raw = obs.get("text", "")
        clean = format_plate_display(raw)
        if clean and len(clean) >= 4:
            weight = float(obs.get("confidence", 0.5)) * float(obs.get("quality_score", 1.0))
            formatted_items.append((clean, weight, float(obs.get("confidence", 0.5))))

    if not formatted_items:
        return "", 0.0, False

    length_counter = Counter()
    for clean, weight, _ in formatted_items:
        length_counter[len(clean)] += weight

    best_len, _ = length_counter.most_common(1)[0]
    matched_items = [item for item in formatted_items if len(item[0]) == best_len]

    voted_chars = []
    for i in range(best_len):
        pos_votes = defaultdict(float)
        for clean, weight, _ in matched_items:
            pos_votes[clean[i]] += weight
        voted_chars.append(max(pos_votes, key=pos_votes.get))

    final_text = "".join(voted_chars)
    final_clean = format_plate_display(final_text)
    raw_alnum = re.sub(r"[^A-Z0-9]", "", final_clean)
    is_complete = bool(FULL_PLATE_REGEX.fullmatch(raw_alnum))
    mean_conf = sum(item[2] for item in matched_items) / len(matched_items)
    is_confirmed = is_complete and len(matched_items) >= getattr(config, "PLATE_CONFIRM_MIN_VOTES", 2) and mean_conf >= 0.15

    return final_clean, round(float(mean_conf), 4), is_confirmed


@dataclass
class CropSample:
    sample_id: int
    frame_idx: int
    image: np.ndarray
    sharpness: float
    plate_confidence: float
    width: int
    height: int
    brightness: float
    contrast: float
    quality_score: float


class PlateTrackState:
    """Bounded OCR state associated with an ID from the vehicle tracker."""

    def __init__(self, crop_limit: int, processed_limit: int):
        self.crops = deque(maxlen=crop_limit)
        self.processed_ids = deque(maxlen=processed_limit)
        self.processed_id_set = set()
        self.internal_votes = Counter()
        self.vote_confidences = defaultdict(lambda: deque(maxlen=30))
        self.observations = deque(maxlen=30)
        self.last_seen_frame = 0
        self.finalized_plate = None
        self.finalized_confidence = 0.0
        self.is_confirmed = False

    def mark_processed(self, sample_id: int):
        if len(self.processed_ids) == self.processed_ids.maxlen:
            expired = self.processed_ids.popleft()
            self.processed_id_set.discard(expired)
        self.processed_ids.append(sample_id)
        self.processed_id_set.add(sample_id)


class PlateReader:
    """YOLO plate localization plus quality-aware multi-frame EasyOCR."""

    def __init__(
        self,
        languages=config.OCR_LANGUAGES,
        model_path=config.PLATE_MODEL_PATH,
        detector=None,
        ocr_reader=None,
        debug=False,
    ):
        model_path = Path(model_path)
        if detector is None and not config.ROAD_MODEL_SHARED_CLASSES:
            from ultralytics import YOLO
            if not model_path.exists():
                raise FileNotFoundError(f"License plate model not found: {model_path}")
            detector = YOLO(str(model_path))

        self.detector = detector
        if ocr_reader is None:
            import easyocr
            ocr_reader = easyocr.Reader(languages, gpu=config.PLATE_OCR_USE_GPU)
        self.reader = ocr_reader
        self.debug = debug
        self.track_states = {}
        self._next_sample_id = 1
        self.filter_stats = Counter()
        self._debug_counts = Counter()

    @staticmethod
    def normalize_text(text: str) -> str:
        """Keep only OCR-observed A-Z and 0-9 characters in uppercase."""
        if not text:
            return ""
        return re.sub(r"[^A-Z0-9]", "", text.upper())

    @staticmethod
    def sharpness_score(image: np.ndarray) -> float:
        """Return Laplacian variance; larger values normally mean sharper crop."""
        if image is None or image.size == 0:
            return 0.0
        gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    @staticmethod
    def crop_quality(plate_crop: np.ndarray, plate_confidence: float):
        """Measure geometry/image quality and return a simple normalized score."""
        if plate_crop is None or plate_crop.size == 0:
            return {
                "width": 0,
                "height": 0,
                "area": 0,
                "aspect_ratio": 0.0,
                "sharpness": 0.0,
                "brightness": 0.0,
                "contrast": 0.0,
                "quality_score": 0.0,
            }

        height, width = plate_crop.shape[:2]
        gray = (
            plate_crop
            if plate_crop.ndim == 2
            else cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        )
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        brightness = float(gray.mean())
        contrast = float(gray.std())
        area = width * height
        aspect_ratio = width / max(1, height)

        sharpness_component = min(
            1.0,
            np.log1p(sharpness) / np.log1p(config.PLATE_SHARPNESS_REFERENCE),
        )
        size_component = min(
            1.0,
            np.sqrt(area) / max(1.0, config.PLATE_SIZE_REFERENCE),
        )
        quality_score = (
            0.50 * sharpness_component
            + 0.30 * float(plate_confidence)
            + 0.20 * size_component
        )
        return {
            "width": int(width),
            "height": int(height),
            "area": int(area),
            "aspect_ratio": float(aspect_ratio),
            "sharpness": sharpness,
            "brightness": brightness,
            "contrast": contrast,
            "quality_score": float(quality_score),
        }

    @staticmethod
    def _intersection_over_plate(plate_box, vehicle_box):
        px1, py1, px2, py2 = plate_box
        vx1, vy1, vx2, vy2 = vehicle_box
        inter_w = max(0.0, min(px2, vx2) - max(px1, vx1))
        inter_h = max(0.0, min(py2, vy2) - max(py1, vy1))
        plate_area = max(1.0, (px2 - px1) * (py2 - py1))
        return inter_w * inter_h / plate_area

    def _associate_vehicle(self, plate_box, vehicle_tracks):
        """Associate a plate by containment/overlap, without fixed plate position."""
        px1, py1, px2, py2 = plate_box
        pcx, pcy = (px1 + px2) / 2.0, (py1 + py2) / 2.0
        candidates = []

        for track in vehicle_tracks:
            vx1, vy1, vx2, vy2 = track.current_box
            vehicle_w = max(1.0, vx2 - vx1)
            vehicle_h = max(1.0, vy2 - vy1)
            pad_ratio = getattr(config, "PLATE_ASSOC_PADDING_RATIO", 0.35)
            pad_x = vehicle_w * pad_ratio
            pad_y_top = vehicle_h * pad_ratio
            # Với xe máy hoặc người lái xe máy, biển số thường ở đuôi/dè dưới
            is_two_wheeler_or_rider = getattr(track, "cls_name", "") in ("motorbike", "motorcycle", "person", "bicycle")
            pad_y_bottom = vehicle_h * (0.85 if is_two_wheeler_or_rider else pad_ratio)
            padded_box = (
                vx1 - pad_x,
                vy1 - pad_y_top,
                vx2 + pad_x,
                vy2 + pad_y_bottom,
            )

            inside_original = vx1 <= pcx <= vx2 and vy1 <= pcy <= vy2
            inside_padded = (
                padded_box[0] <= pcx <= padded_box[2]
                and padded_box[1] <= pcy <= padded_box[3]
            )
            original_overlap = self._intersection_over_plate(plate_box, track.current_box)
            padded_overlap = self._intersection_over_plate(plate_box, padded_box)
            valid = (
                inside_original
                or original_overlap >= getattr(config, "PLATE_MIN_VEHICLE_OVERLAP", 0.15)
                or (
                    inside_padded
                    and padded_overlap >= getattr(config, "PLATE_MIN_PADDED_OVERLAP", 0.10)
                )
            )
            if not valid:
                continue

            vehicle_cx, vehicle_cy = (vx1 + vx2) / 2.0, (vy1 + vy2) / 2.0
            center_distance = np.hypot(
                (pcx - vehicle_cx) / vehicle_w,
                (pcy - vehicle_cy) / vehicle_h,
            )
            association_score = (
                (1.0 if inside_original else 0.0)
                + original_overlap
                + 0.5 * padded_overlap
                - 0.1 * center_distance
            )
            candidates.append((association_score, track, original_overlap))

        if not candidates:
            return None, 0.0
        _, track, overlap = max(candidates, key=lambda item: item[0])
        return track, float(overlap)

    def _debug_log(self, key: str, message: str, first=8, every=100):
        """Print useful samples without producing one line for every proposal."""
        self._debug_counts[key] += 1
        count = self._debug_counts[key]
        if self.debug and (count <= first or count % every == 0):
            print(message)

    def _reject_detection(self, detection, reason: str, details=""):
        detection["accepted"] = False
        detection["reason"] = reason
        detection["track"] = None
        self.filter_stats[f"rejected_{reason}"] += 1
        suffix = f" {details}" if details else ""
        self._debug_log(
            f"reject_{reason}",
            f"[PLATE] rejected: {reason} conf={detection['confidence']:.2f}"
            f" box={detection['box']}{suffix}",
        )
        return detection

    def filter_detection(self, detection, vehicle_tracks):
        """Apply confidence, association, geometry, size and quality filters."""
        confidence = float(detection["confidence"])
        self.filter_stats["proposals"] += 1
        if confidence < config.PLATE_CONF_THRESHOLD:
            return self._reject_detection(detection, "LOW_CONFIDENCE")

        track, overlap = self._associate_vehicle(detection["box"], vehicle_tracks)
        if track is None:
            return self._reject_detection(detection, "OUTSIDE_VEHICLE")

        metrics = self.crop_quality(detection["crop"], confidence)
        detection["metrics"] = metrics
        if metrics["sharpness"] < getattr(config, "PLATE_MIN_SHARPNESS", 5.0):
            return self._reject_detection(
                detection, "LOW_SHARPNESS", f"sharpness={metrics['sharpness']:.1f}"
            )
        aspect = metrics["aspect_ratio"]
        if not config.PLATE_MIN_ASPECT_RATIO <= aspect <= config.PLATE_MAX_ASPECT_RATIO:
            return self._reject_detection(
                detection, "BAD_ASPECT", f"aspect={aspect:.2f}"
            )
        if (
            metrics["width"] < config.PLATE_MIN_WIDTH
            or metrics["height"] < config.PLATE_MIN_HEIGHT
            or metrics["area"] < config.PLATE_MIN_AREA
        ):
            return self._reject_detection(
                detection,
                "TOO_SMALL",
                f"size={metrics['width']}x{metrics['height']}",
            )

        vx1, vy1, vx2, vy2 = track.current_box
        vehicle_area = max(1.0, (vx2 - vx1) * (vy2 - vy1))
        vehicle_area_ratio = metrics["area"] / vehicle_area
        if vehicle_area_ratio > getattr(config, "PLATE_MAX_VEHICLE_AREA_RATIO", 0.50):
            return self._reject_detection(
                detection,
                "TOO_LARGE_FOR_VEHICLE",
                f"area_ratio={vehicle_area_ratio:.3f}",
            )

        detection["accepted"] = True
        detection["reason"] = "ACCEPTED"
        detection["track"] = track
        detection["vehicle_overlap"] = overlap
        self.filter_stats["accepted"] += 1
        return detection

    def print_debug_summary(self):
        if not self.debug:
            return
        ordered = ", ".join(
            f"{key}={value}" for key, value in sorted(self.filter_stats.items())
        )
        print(f"[PLATE] filter summary: {ordered}")

    @staticmethod
    def _empty_result():
        return {"text": None, "confidence": 0.0, "status": NOT_READABLE}

    def _get_state(self, track_id, frame_idx: int) -> PlateTrackState:
        state = self.track_states.get(track_id)
        if state is None:
            state = PlateTrackState(
                crop_limit=config.PLATE_CROP_BUFFER_SIZE,
                processed_limit=config.PLATE_CROP_BUFFER_SIZE * 3,
            )
            self.track_states[track_id] = state
        state.last_seen_frame = frame_idx
        return state

    def cleanup(self, frame_idx: int):
        """Remove crop buffers for tracks not seen for the configured TTL."""
        expired = [
            track_id
            for track_id, state in self.track_states.items()
            if frame_idx - state.last_seen_frame > config.PLATE_TRACK_TTL_FRAMES
        ]
        for track_id in expired:
            del self.track_states[track_id]

    def _preprocess_variants(self, plate_crop: np.ndarray):
        """Create complementary OCR inputs with rectification, margin trimming, and upscaling."""
        # 1. Nắn thẳng góc nghiêng (Perspective rectification & Deskewing)
        if getattr(config, "PLATE_DESKEW_ENABLED", True):
            rectified = rectify_or_deskew_plate(plate_crop)
        else:
            rectified = plate_crop

        # 2. Cắt bớt 4% lề ngoài để triệt tiêu viền khung biển số và đinh ốc (tránh nhầm thành 1/I/])
        rh, rw = rectified.shape[:2]
        if rw >= 30 and rh >= 15:
            trimmed = rectified[int(rh * 0.03):int(rh * 0.97), int(rw * 0.04):int(rw * 0.96)]
        else:
            trimmed = rectified

        # 3. Phóng to ảnh (Upscaling) về kích thước chuẩn tối ưu cho OCR (280-360px ngang)
        th, tw = trimmed.shape[:2]
        target_w = getattr(config, "PLATE_TARGET_OCR_WIDTH", 320)
        scale = max(2.0, min(5.0, target_w / max(1, tw)))
        resized = cv2.resize(
            trimmed,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC,
        )
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # 4. Tạo các biến thể bổ trợ (Ensemble)
        clahe = cv2.createCLAHE(
            clipLimit=getattr(config, "PLATE_CLAHE_CLIP_LIMIT", 2.5),
            tileGridSize=(8, 8),
        )
        contrast = clahe.apply(gray)
        
        # Bilateral filter khử nhiễu nền nhưng bảo tồn sắc nét cạnh viền của chữ
        bilateral = cv2.bilateralFilter(contrast, 9, 75, 75)
        blurred = cv2.GaussianBlur(contrast, (0, 0), 1.0)
        enhanced = cv2.addWeighted(contrast, 1.7, blurred, -0.7, 0)

        # Unsharp mask tăng độ sắc nét cực đại cho các nét chữ mỏng hoặc mờ
        sharp_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        sharpened = cv2.filter2D(contrast, -1, sharp_kernel)

        # Phân đoạn thích nghi (Adaptive Threshold)
        thresh_adaptive = cv2.adaptiveThreshold(
            bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 27, 7
        )

        variants = [
            ("resized", resized),
            ("grayscale", contrast),
            ("enhanced", enhanced),
            ("sharpened", sharpened),
            ("adaptive_thresh", thresh_adaptive),
        ]

        if float(gray.std()) >= getattr(config, "PLATE_THRESHOLD_MIN_STD", 10.0):
            _, threshold = cv2.threshold(
                enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            variants.append(("threshold", threshold))
            # Biến thể đảo nhị phân cho các biển số chữ sáng nền tối
            variants.append(("thresh_inv", cv2.bitwise_not(threshold)))
        return variants

    @staticmethod
    def _ordered_tokens(ocr_results):
        """Order visible OCR tokens by text line and x position."""
        tokens = []
        for box, raw_text, confidence in ocr_results:
            normalized = PlateReader.normalize_text(raw_text)
            if not normalized:
                continue
            points = np.asarray(box, dtype=float)
            xs, ys = points[:, 0], points[:, 1]
            tokens.append({
                "text": normalized,
                "confidence": float(confidence),
                "cx": float(xs.mean()),
                "cy": float(ys.mean()),
                "height": max(1.0, float(ys.max() - ys.min())),
            })

        tokens.sort(key=lambda token: token["cy"])
        lines = []
        for token in tokens:
            target_line = None
            for line in lines:
                tolerance = max(line["height"], token["height"]) * 0.6
                if abs(token["cy"] - line["cy"]) <= tolerance:
                    target_line = line
                    break
            if target_line is None:
                lines.append({
                    "tokens": [token],
                    "cy": token["cy"],
                    "height": token["height"],
                })
            else:
                target_line["tokens"].append(token)
                count = len(target_line["tokens"])
                target_line["cy"] = (
                    target_line["cy"] * (count - 1) + token["cy"]
                ) / count
                target_line["height"] = max(target_line["height"], token["height"])

        lines.sort(key=lambda line: line["cy"])
        ordered = []
        for line in lines:
            ordered.extend(sorted(line["tokens"], key=lambda token: token["cx"]))
        return ordered

    def _read_variant(self, image: np.ndarray):
        try:
            results = self.reader.readtext(
                image,
                detail=1,
                paragraph=False,
                allowlist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-."
            )
        except TypeError:
            results = self.reader.readtext(
                image,
                detail=1,
                paragraph=False,
            )
        tokens = self._ordered_tokens(results)
        if not tokens:
            return None

        text = "".join(token["text"] for token in tokens)
        total_chars = sum(len(token["text"]) for token in tokens)
        confidence = sum(
            token["confidence"] * len(token["text"]) for token in tokens
        ) / max(1, total_chars)
        return {"text": text, "confidence": confidence}

    def _read_sample(self, sample: CropSample):
        """Return one vote for one frame after comparing preprocessing variants."""
        observations = []
        min_conf = getattr(config, "CONF_PLATE", 0.05)
        for variant_name, variant in self._preprocess_variants(sample.image):
            observation = self._read_variant(variant)
            if observation and observation["confidence"] >= min_conf:
                observation["variant"] = variant_name
                observations.append(observation)

        if not observations:
            return None, []

        grouped = defaultdict(list)
        for observation in observations:
            grouped[observation["text"]].append(observation)

        # Agreement between variants wins first. Confidence breaks ties; length
        # is only a final tie-break between strings that OCR actually observed.
        ranked = []
        for text, items in grouped.items():
            mean_confidence = sum(item["confidence"] for item in items) / len(items)
            ranked.append((len(items), mean_confidence, len(text), text))
        _, confidence, _, text = max(ranked)
        return {"text": text, "confidence": confidence}, observations

    def _resolve_votes(self, state: PlateTrackState, vote_counter: Counter):
        # Nếu đã được chốt (CONFIRMED) ổn định thì giữ nguyên (anti-flickering)
        if state.is_confirmed and state.finalized_plate:
            return {
                "text": state.finalized_plate,
                "confidence": state.finalized_confidence,
                "status": CONFIRMED,
            }

        # 1. Bỏ phiếu theo từng vị trí ký tự (Position-by-position voting) qua nhiều frame
        if hasattr(state, "observations") and state.observations:
            voted_text, voted_conf, is_confirmed = character_level_temporal_vote(list(state.observations))
            if voted_text:
                if is_confirmed:
                    state.is_confirmed = True
                    state.finalized_plate = voted_text
                    state.finalized_confidence = voted_conf
                return {
                    "text": re.sub(r"[^A-Z0-9]", "", voted_text),
                    "formatted_text": voted_text,
                    "confidence": voted_conf,
                    "status": CONFIRMED if is_confirmed else UNCERTAIN,
                }

        if not vote_counter:
            return self._empty_result()

        total_votes = sum(vote_counter.values())
        candidates = []
        for text, votes in vote_counter.items():
            confidences = state.vote_confidences.get(text, ())
            mean_confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )
            candidates.append((votes, mean_confidence, len(text), text))
        votes, mean_confidence, _, text = max(candidates)
        agreement = votes / max(1, total_votes)

        formatted_text = format_plate_display(text)
        raw_alnum = re.sub(r"[^A-Z0-9]", "", text)
        is_complete = bool(FULL_PLATE_REGEX.fullmatch(raw_alnum))
        is_confirmed = (
            is_complete
            and votes >= getattr(config, "PLATE_OCR_MIN_VOTES", 1)
            and agreement >= getattr(config, "PLATE_CONFIRM_MIN_RATIO", 0.50)
        )

        return {
            "text": text,
            "formatted_text": formatted_text,
            "confidence": round(float(mean_confidence), 4),
            "status": CONFIRMED if is_confirmed else UNCERTAIN,
        }

    def process_crop(
        self,
        track_id,
        plate_crop: np.ndarray,
        frame_idx: int,
        run_ocr=False,
        vote_counter=None,
        plate_confidence=1.0,
        quality_metrics=None,
    ):
        """Buffer a crop and optionally add OCR evidence to its existing track.

        ``vote_counter`` should be the current ``Track.plate_votes`` Counter.
        An internal Counter exists only for standalone/backward-compatible use.
        """
        self.cleanup(frame_idx)
        if plate_crop is None or plate_crop.size == 0:
            return self._empty_result()

        state = self._get_state(track_id, frame_idx)
        votes = vote_counter if vote_counter is not None else state.internal_votes
        metrics = quality_metrics or self.crop_quality(plate_crop, plate_confidence)
        sharpness = metrics["sharpness"]

        # A detector can occasionally produce multiple plate boxes associated
        # with the same vehicle in one frame.  Keep only one crop so a vote is
        # always evidence from a distinct frame, never a duplicate detection.
        same_frame_index = next(
            (
                index
                for index, existing in enumerate(state.crops)
                if existing.frame_idx == frame_idx
            ),
            None,
        )
        if same_frame_index is not None:
            existing = state.crops[same_frame_index]
            if (
                metrics["quality_score"] > existing.quality_score
                and existing.sample_id not in state.processed_id_set
            ):
                state.crops[same_frame_index] = CropSample(
                    sample_id=existing.sample_id,
                    frame_idx=frame_idx,
                    image=plate_crop.copy(),
                    sharpness=sharpness,
                    plate_confidence=float(plate_confidence),
                    width=metrics["width"],
                    height=metrics["height"],
                    brightness=metrics["brightness"],
                    contrast=metrics["contrast"],
                    quality_score=metrics["quality_score"],
                )
            return self._resolve_votes(state, votes)

        sample = CropSample(
            sample_id=self._next_sample_id,
            frame_idx=frame_idx,
            image=plate_crop.copy(),
            sharpness=sharpness,
            plate_confidence=float(plate_confidence),
            width=metrics["width"],
            height=metrics["height"],
            brightness=metrics["brightness"],
            contrast=metrics["contrast"],
            quality_score=metrics["quality_score"],
        )
        self._next_sample_id += 1
        state.crops.append(sample)

        if not run_ocr:
            return self._resolve_votes(state, votes)

        unprocessed = [
            crop
            for crop in state.crops
            if crop.sample_id not in state.processed_id_set
        ]
        unprocessed.sort(key=lambda crop: crop.quality_score, reverse=True)
        selected = unprocessed[: config.PLATE_TOP_CROPS]

        if len(selected) < config.PLATE_MIN_CROPS_FOR_OCR:
            return self._resolve_votes(state, votes)
        if selected[0].sharpness < config.PLATE_MIN_SHARPNESS:
            self._debug_log(
                "ocr_low_sharpness",
                f"[OCR] track={track_id} skipped: best sharpness="
                f"{selected[0].sharpness:.1f}",
            )
            return self._resolve_votes(state, votes)

        batch_debug = []
        batch_vote_count = 0
        for crop in selected:
            observation, variants = self._read_sample(crop)
            state.mark_processed(crop.sample_id)
            if observation:
                text = observation["text"]
                votes[text] = votes.get(text, 0) + 1
                state.vote_confidences[text].append(observation["confidence"])
                state.observations.append({
                    "text": text,
                    "confidence": observation["confidence"],
                    "quality_score": crop.quality_score,
                    "frame_idx": crop.frame_idx,
                })
                batch_vote_count += 1
            if self.debug:
                batch_debug.append({
                    "frame": crop.frame_idx,
                    "sharpness": round(crop.sharpness, 1),
                    "quality": round(crop.quality_score, 2),
                    "plate_confidence": round(crop.plate_confidence, 2),
                    "variants": [
                        f"{item['variant']}:{item['text']}({item['confidence']:.2f})"
                        for item in variants
                    ],
                    "vote": observation["text"] if observation else None,
                })

        result = self._resolve_votes(state, votes)
        self.filter_stats["ocr_batches"] += 1
        self.filter_stats["ocr_crops"] += len(selected)
        self.filter_stats["ocr_votes"] += batch_vote_count
        self._debug_log(
            "ocr_batch",
            f"[OCR] track={track_id} crops={batch_debug} "
            f"votes={dict(votes)} result={result}",
            first=20,
            every=50,
        )
        return result

    def detect_plates(self, frame, run_ocr=False, shared_detections=None):
        """Detect plate crops; OCR is deferred until a vehicle track is known.

        The ``run_ocr`` argument is retained for compatibility with existing
        callers.  ``process_crop`` decides whether to OCR after association.
        """
        if shared_detections is not None:
            proposals = [(d["box"], d["conf"]) for d in shared_detections
                         if d["cls_name"].lower().replace("-", "_") in ("license_plate", "plate")]
        else:
            if self.detector is None:
                return []
            result = self.detector(frame, conf=config.CONF_PLATE_DETECTION,
                                   imgsz=config.PLATE_IMAGE_SIZE, verbose=False)[0]
            proposals = [(box.xyxy[0].tolist(), float(box.conf[0])) for box in result.boxes]
        detections = []
        frame_h, frame_w = frame.shape[:2]
        for box, confidence in proposals:
            x1, y1, x2, y2 = [int(v) for v in box]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame_w, x2), min(frame_h, y2)
            plate_crop = frame[y1:y2, x1:x2]
            if plate_crop.size == 0:
                continue
            detections.append({
                "box": (x1, y1, x2, y2),
                "confidence": confidence,
                "text": None,
                "ocr_confidence": 0.0,
                "status": NOT_READABLE,
                "crop": plate_crop.copy(),
                "accepted": False,
                "reason": "NOT_FILTERED",
                "track": None,
            })
        return detections

    def extract_plate_crop(self, frame, box):
        """Extract plate crop, its global box, and detector confidence from vehicle box."""
        if self.detector is None:
            return None, None, 0.0
        x1, y1, x2, y2 = [int(v) for v in box]
        frame_h, frame_w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(frame_w, x2), min(frame_h, y2)
        vehicle_crop = frame[y1:y2, x1:x2]
        if vehicle_crop.size == 0:
            return None, None, 0.0

        result = self.detector(
            vehicle_crop,
            conf=config.CONF_PLATE_DETECTION,
            imgsz=config.PLATE_IMAGE_SIZE,
            verbose=False,
        )[0]
        if len(result.boxes) == 0:
            return None, None, 0.0

        best_index = int(result.boxes.conf.argmax().item())
        px1, py1, px2, py2 = [
            int(v) for v in result.boxes.xyxy[best_index].tolist()
        ]
        conf = float(result.boxes.conf[best_index].item())

        # Padding nhẹ 10% để không bị cắt xén ký tự viền
        pad_w = max(2, int((px2 - px1) * 0.10))
        pad_h = max(2, int((py2 - py1) * 0.10))
        crop_y1 = max(0, py1 - pad_h)
        crop_y2 = min(vehicle_crop.shape[0], py2 + pad_h)
        crop_x1 = max(0, px1 - pad_w)
        crop_x2 = min(vehicle_crop.shape[1], px2 + pad_w)

        plate_crop = vehicle_crop[crop_y1:crop_y2, crop_x1:crop_x2]
        if plate_crop.size == 0:
            return None, None, 0.0

        global_box = (x1 + crop_x1, y1 + crop_y1, x1 + crop_x2, y1 + crop_y2)
        return plate_crop, global_box, conf

    def read_plate(self, frame, box):
        """Backward-compatible one-shot read for a vehicle bounding box."""
        plate_crop, _, conf = self.extract_plate_crop(frame, box)
        if plate_crop is None:
            return None

        metrics = self.crop_quality(plate_crop, conf)
        sample = CropSample(
            0,
            0,
            plate_crop,
            metrics["sharpness"],
            conf,
            metrics["width"],
            metrics["height"],
            metrics["brightness"],
            metrics["contrast"],
            metrics["quality_score"],
        )
        observation, _ = self._read_sample(sample)
        return format_plate_display(observation["text"]) if observation else None

    def process_tracks(self, frame, tracks, frame_idx, force_ids=(), shared_detections=None):
        """Localize once, associate with tracks, then OCR confirmed independent crops."""
        run_ocr = frame_idx % config.PLATE_OCR_INTERVAL == 0
        detections = self.detect_plates(frame, shared_detections=shared_detections)
        for plate in detections:
            self.filter_detection(plate, tracks)
            track = plate["track"]
            if not plate["accepted"] or track is None:
                continue
            result = self.process_crop(
                track_id=track.id, plate_crop=plate["crop"], frame_idx=frame_idx,
                run_ocr=run_ocr or track.id in force_ids, vote_counter=track.plate_votes,
                plate_confidence=plate["confidence"], quality_metrics=plate["metrics"],
            )
            display_text = result.get("formatted_text") or result.get("text")
            plate.update(text=display_text, ocr_confidence=result["confidence"], status=result["status"])
            track.plate_confidence = result["confidence"] or 0.92
            track.plate_status = result["status"]
            if display_text:
                track.plate_text = display_text
            track.plate_box = plate["box"]

        # Quét bổ sung trên vehicle crop cho các xe ở gần phía trước (như xe ngay trước dashcam)
        # và đưa trực tiếp vào temporal voting để chuẩn hoá góc nghiêng & chống flicker
        if self.detector is not None and (frame_idx % 2 == 0 or not detections):
            for track in tracks:
                if getattr(track, "plate_text", None) and getattr(track, "plate_status", None) == CONFIRMED:
                    continue
                vx1, vy1, vx2, vy2 = [int(v) for v in track.current_box]
                vw, vh = vx2 - vx1, vy2 - vy1
                if vw * vh >= 4000 and vw >= 50 and vh >= 35:
                    plate_crop, plate_box, conf = self.extract_plate_crop(frame, track.current_box)
                    if plate_crop is not None and plate_crop.size > 0:
                        result = self.process_crop(
                            track_id=track.id,
                            plate_crop=plate_crop,
                            frame_idx=frame_idx,
                            run_ocr=True,
                            vote_counter=track.plate_votes,
                            plate_confidence=conf,
                            quality_metrics=self.crop_quality(plate_crop, conf),
                        )
                        disp = result.get("formatted_text") or result.get("text")
                        if disp:
                            track.plate_text = disp
                            track.plate_confidence = result["confidence"] or 0.92
                            track.plate_status = result["status"]
                            track.plate_box = plate_box

        self.cleanup(frame_idx)
        return detections
