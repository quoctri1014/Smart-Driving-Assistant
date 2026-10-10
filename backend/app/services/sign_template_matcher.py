import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[3]
QCVN_CATALOG_PATH = BASE_DIR / "backend" / "app" / "assets" / "qcvn_signs" / "qcvn_signs_catalog.json"
QCVN_IMG_DIR = BASE_DIR / "backend" / "app" / "assets" / "qcvn_signs"
MD_PATH = BASE_DIR / "Bien_bao_giao_thong_Viet_Nam_md" / "Bien_bao_giao_thong_Viet_Nam.md"
MD_IMG_DIR = BASE_DIR / "Bien_bao_giao_thong_Viet_Nam_md" / "img"

TEMPLATE_SIZE = (96, 96)


class SignTemplate:
    def __init__(self, code: str, name: str, category: str, action: str, img_filename: str, speed_limit: Optional[int] = None):
        self.code = code
        self.name = name
        self.category = category
        self.action = action
        self.img_filename = img_filename
        self.speed_limit = speed_limit
        self.image: Optional[np.ndarray] = None
        self.gray: Optional[np.ndarray] = None
        self.hsv: Optional[np.ndarray] = None
        self.edges: Optional[np.ndarray] = None
        self.feature_vec: Optional[np.ndarray] = None
        self.inner_glyph: Optional[np.ndarray] = None


class SignTemplateMatcher:
    _instance = None

    def __init__(self):
        self.templates: Dict[str, SignTemplate] = {}
        self.groups: Dict[str, List[SignTemplate]] = {
            "P": [],   # Biển Cấm (Tròn viền đỏ)
            "DP": [],  # Hết cấm (Tròn có vạch xám/đen)
            "W": [],   # Cảnh báo (Tam giác vàng viền đỏ)
            "R": [],   # Hiệu lệnh (Tròn xanh hoặc bát giác)
            "I": [],   # Chỉ dẫn (Vuông/Chữ nhật xanh)
            "S": [],   # Biển phụ (Chữ nhật trắng)
        }
        self._load_qcvn_catalog()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SignTemplateMatcher()
        return cls._instance

    def _load_qcvn_catalog(self):
        # 1. Load from QCVN 41:2019 / 01-06-2020 Catalog
        if QCVN_CATALOG_PATH.exists():
            try:
                with open(QCVN_CATALOG_PATH, "r", encoding="utf-8") as f:
                    catalog_data = json.load(f)

                for item in catalog_data:
                    code = item["code"]
                    fname = item.get("img_filename", f"{code.replace('.', '_')}.png")
                    fpath = QCVN_IMG_DIR / fname
                    if not fpath.exists():
                        continue

                    img = cv2.imread(str(fpath), cv2.IMREAD_UNCHANGED)
                    if img is None:
                        continue

                    if len(img.shape) == 3 and img.shape[2] == 4:
                        alpha = img[:, :, 3] / 255.0
                        bgr = img[:, :, :3]
                        img = (bgr * alpha[:, :, None] + 255 * (1 - alpha[:, :, None])).astype(np.uint8)

                    tmpl = SignTemplate(
                        code=code,
                        name=item["name"],
                        category=item["category"],
                        action=item["action"],
                        img_filename=fname,
                        speed_limit=item.get("speed_limit")
                    )

                    tmpl.image = cv2.resize(img, TEMPLATE_SIZE)
                    tmpl.gray = cv2.cvtColor(tmpl.image, cv2.COLOR_BGR2GRAY)
                    tmpl.hsv = cv2.cvtColor(tmpl.image, cv2.COLOR_BGR2HSV)
                    tmpl.edges = cv2.Canny(tmpl.gray, 50, 150)

                    # Normalized spatial thumbnail + edge vector for fast cosine similarity
                    thumb = cv2.resize(tmpl.gray, (32, 32)).astype(np.float32) / 255.0
                    edge_thumb = cv2.resize(tmpl.edges, (32, 32)).astype(np.float32) / 255.0
                    tmpl.feature_vec = np.hstack([thumb.flatten(), edge_thumb.flatten()])
                    norm = np.linalg.norm(tmpl.feature_vec)
                    if norm > 0:
                        tmpl.feature_vec /= norm

                    prefix = code.split(".")[0]
                    self.templates[code] = tmpl
                    if prefix in self.groups:
                        self.groups[prefix].append(tmpl)

                print(f"[SignTemplateMatcher] Loaded {len(self.templates)} official Vietnamese traffic signs from QCVN catalog.")
                return
            except Exception as e:
                print(f"[SignTemplateMatcher] Error loading QCVN catalog: {e}")

        # 2. Fallback to Markdown and img directory if catalog not available
        self._load_from_markdown_fallback()

    def _load_from_markdown_fallback(self):
        if not MD_IMG_DIR.exists():
            return
        for fname in os.listdir(MD_IMG_DIR):
            if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            fpath = MD_IMG_DIR / fname
            img = cv2.imread(str(fpath))
            if img is None:
                continue

            code = fname.rsplit(".", 1)[0].replace("_", ".")
            prefix = code.split(".")[0]
            cat = "CẤM" if prefix in ("P", "DP") else "CẢNH BÁO" if prefix == "W" else "HIỆU LỆNH" if prefix == "R" else "CHỈ DẪN"
            tmpl = SignTemplate(code=code, name=f"Biển {code}", category=cat, action="Tuân thủ theo quy định QCVN 41", img_filename=fname)
            tmpl.image = cv2.resize(img, TEMPLATE_SIZE)
            tmpl.gray = cv2.cvtColor(tmpl.image, cv2.COLOR_BGR2GRAY)
            tmpl.edges = cv2.Canny(tmpl.gray, 50, 150)
            thumb = cv2.resize(tmpl.gray, (32, 32)).astype(np.float32) / 255.0
            edge_thumb = cv2.resize(tmpl.edges, (32, 32)).astype(np.float32) / 255.0
            tmpl.feature_vec = np.hstack([thumb.flatten(), edge_thumb.flatten()])
            norm = np.linalg.norm(tmpl.feature_vec)
            if norm > 0:
                tmpl.feature_vec /= norm
            self.templates[code] = tmpl
            if prefix in self.groups:
                self.groups[prefix].append(tmpl)

    def center_crop_circle(self, crop: np.ndarray) -> np.ndarray:
        """Tự động căn tâm và cắt sát vòng tròn biển báo (loại bỏ phông nền ngoại cảnh)"""
        if crop is None or crop.shape[0] < 20 or crop.shape[1] < 20:
            return crop
        H, W = crop.shape[:2]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        r1 = cv2.inRange(hsv, np.array([0, 50, 40]), np.array([14, 255, 255]))
        r2 = cv2.inRange(hsv, np.array([155, 50, 40]), np.array([180, 255, 255]))
        red = cv2.bitwise_or(r1, r2)
        blue = cv2.inRange(hsv, np.array([95, 60, 45]), np.array([130, 255, 255]))
        color_mask = cv2.bitwise_or(red, blue)

        cnts, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            c_max = max(cnts, key=cv2.contourArea)
            if cv2.contourArea(c_max) > (W * H * 0.08):
                (cx, cy), radius = cv2.minEnclosingCircle(c_max)
                r = int(radius * 1.05)
                x1 = max(0, int(cx - r))
                y1 = max(0, int(cy - r))
                x2 = min(W, int(cx + r))
                y2 = min(H, int(cy + r))
                if (x2 - x1) >= 20 and (y2 - y1) >= 20:
                    return crop[y1:y2, x1:x2]
        return crop

    def match_crop(self, crop: np.ndarray, category_hint: Optional[str] = None) -> Optional[Tuple[SignTemplate, float]]:
        """
        Đối soát siêu tốc và chính xác cao giữa vùng crop và 144 mẫu biển báo chuẩn QCVN 41
        """
        if crop is None or crop.shape[0] < 16 or crop.shape[1] < 16:
            return None

        # Tự động căn tâm nếu là biển tròn
        tight = self.center_crop_circle(crop)
        H, W = tight.shape[:2]
        aspect = W / max(1, H)

        resized = cv2.resize(tight, TEMPLATE_SIZE)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        edges = cv2.Canny(gray, 50, 150)

        # Đo tỉ lệ các màu đặc trưng của biển báo Việt Nam
        red1 = cv2.inRange(hsv, np.array([0, 50, 40]), np.array([14, 255, 255]))
        red2 = cv2.inRange(hsv, np.array([155, 50, 40]), np.array([180, 255, 255]))
        red_mask = cv2.bitwise_or(red1, red2)
        red_ratio = np.count_nonzero(red_mask) / (TEMPLATE_SIZE[0] * TEMPLATE_SIZE[1])

        yellow = cv2.inRange(hsv, np.array([15, 65, 60]), np.array([36, 255, 255]))
        yellow_ratio = np.count_nonzero(yellow) / (TEMPLATE_SIZE[0] * TEMPLATE_SIZE[1])

        blue = cv2.inRange(hsv, np.array([95, 60, 45]), np.array([135, 255, 255]))
        blue_ratio = np.count_nonzero(blue) / (TEMPLATE_SIZE[0] * TEMPLATE_SIZE[1])

        # Chọn nhóm ứng viên phù hợp
        target_group = category_hint
        if not target_group:
            if yellow_ratio >= 0.14 and 0.65 <= aspect <= 1.45:
                target_group = "W"
            elif red_ratio >= 0.08 and 0.65 <= aspect <= 1.40:
                target_group = "P"
            elif blue_ratio >= 0.14:
                target_group = "R" if (0.70 <= aspect <= 1.35) else "I"
            elif aspect >= 1.20 or aspect <= 0.85:
                # Dấu hiệu biển phụ (S) hoặc biển chỉ dẫn chữ nhật
                target_group = "S"
            else:
                return None

        # Kiểm tra hình học tương thích
        if target_group in ("P", "W", "R") and (aspect < 0.60 or aspect > 1.45):
            return None

        candidates = self.groups.get(target_group, [])
        if not candidates and target_group == "S":
            candidates = self.groups.get("S", [])
        if not candidates:
            return None

        # Trích xuất feature vector
        thumb = cv2.resize(gray, (32, 32)).astype(np.float32) / 255.0
        edge_thumb = cv2.resize(edges, (32, 32)).astype(np.float32) / 255.0
        feat = np.hstack([thumb.flatten(), edge_thumb.flatten()])
        norm = np.linalg.norm(feat)
        if norm > 0:
            feat /= norm
        else:
            return None

        best_tmpl = None
        best_score = -1.0

        for tmpl in candidates:
            if tmpl.feature_vec is None:
                continue

            # Biển cấm dừng / đỗ (P.130, P.131a, P.131b, P.131c):
            # Trong điều kiện ban ngày có màu xanh, ban đêm có thể tối hơn
            if tmpl.code not in ("P.130", "P.131a", "P.131b", "P.131c") and blue_ratio >= 0.28:
                continue

            sim = float(np.dot(feat, tmpl.feature_vec))
            if sim > best_score:
                best_score = sim
                best_tmpl = tmpl

        if best_tmpl and best_score >= 0.68:
            return best_tmpl, best_score

        return None
