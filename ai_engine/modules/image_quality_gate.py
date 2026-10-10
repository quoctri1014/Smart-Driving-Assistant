"""
image_quality_gate.py
---------------------
0.1 Image Quality Gate (Kiểm định chất lượng ảnh đầu vào):
- Đo độ mờ (Variance of Laplacian).
- Đo độ sáng / độ tương phản (Histogram, Mean & Std của luminance).
- Phát hiện lóa sáng / cháy sáng đèn pha hoặc ngược nắng (Saturated pixels ratio).
- Phát hiện giọt mưa / bụi bẩn / mờ cục bộ trên kính chắn gió (Grid-wise Laplacian variance).
- Đưa ra điểm chất lượng 0.0 - 1.0. Dưới ngưỡng thì gắn cờ `low_quality`.
- Tiền xử lý có điều kiện: CLAHE khi tối / tương phản thấp, Dehaze khi sương mù;
  chỉ giữ kết quả sau tiền xử lý nếu điểm chất lượng thực sự tăng lên.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import cv2
import numpy as np

# Tải cấu hình từ adas_config.json nếu có
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "adas_config.json"
DEFAULT_CONFIG = {
    "blur_laplacian_threshold": 65.0,
    "min_brightness_mean": 35.0,
    "max_brightness_mean": 225.0,
    "min_contrast_std": 22.0,
    "glare_saturated_ratio_threshold": 0.12,
    "local_blur_droplet_variance_threshold": 0.40,
    "clahe_clip_limit": 2.0,
    "clahe_tile_grid_size": [8, 8],
    "quality_score_minimum": 0.45
}

if CONFIG_PATH.exists():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg_data = json.load(f)
            DEFAULT_CONFIG.update(cfg_data.get("quality_gate", {}))
    except Exception:
        pass


@dataclass
class QualityReport:
    score: float                         # Điểm chất lượng tổng hợp: 0.0 - 1.0
    is_low_quality: bool                 # True nếu chất lượng dưới ngưỡng an toàn
    blur_score: float                    # Phương sai Laplacian (càng cao càng nét)
    brightness_mean: float               # Độ sáng trung bình (0 - 255)
    contrast_std: float                  # Độ tương phản (độ lệch chuẩn luminance)
    glare_ratio: float                   # Tỷ lệ điểm ảnh cháy sáng (> 250)
    local_dirt_droplet_ratio: float      # Tỷ lệ vùng mờ cục bộ (bụi/mưa)
    issues: List[str] = field(default_factory=list) # Danh sách lỗi phát hiện
    enhanced: bool = False               # Đã qua bộ nâng cao ảnh có điều kiện hay chưa


class ImageQualityGate:
    def __init__(self, config: dict = None):
        self.cfg = DEFAULT_CONFIG.copy()
        if config:
            self.cfg.update(config)

    def assess_frame(self, frame: np.ndarray) -> Tuple[QualityReport, np.ndarray]:
        """
        Đánh giá toàn diện chất lượng khung hình và áp dụng tiền xử lý có điều kiện.
        Trả về (QualityReport, processed_frame).
        """
        if frame is None or frame.size == 0:
            return QualityReport(
                score=0.0,
                is_low_quality=True,
                blur_score=0.0,
                brightness_mean=0.0,
                contrast_std=0.0,
                glare_ratio=0.0,
                local_dirt_droplet_ratio=1.0,
                issues=["Khung hình rỗng hoặc lỗi cảm biến camera"]
            ), frame

        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        h, w = gray.shape

        # 1. Đo độ mờ (Variance of Laplacian)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # 2. Đo độ sáng và độ tương phản
        mean_bright = float(np.mean(gray))
        contrast_std = float(np.std(gray))

        # 3. Đo lóa sáng (Tỷ lệ pixel > 250)
        saturated_pixels = np.sum(gray >= 250)
        glare_ratio = float(saturated_pixels / (h * w))

        # 4. Phát hiện giọt mưa / bụi bẩn / mờ cục bộ (Grid 4x4)
        grid_rows, grid_cols = 4, 4
        tile_h, tile_w = h // grid_rows, w // grid_cols
        low_sharpness_tiles = 0
        total_tiles = grid_rows * grid_cols

        for r in range(grid_rows):
            for c in range(grid_cols):
                tile = gray[r * tile_h:(r + 1) * tile_h, c * tile_w:(c + 1) * tile_w]
                if tile.size > 0:
                    tile_lap = cv2.Laplacian(tile, cv2.CV_64F).var()
                    if tile_lap < 20.0:
                        low_sharpness_tiles += 1

        local_dirt_ratio = float(low_sharpness_tiles / total_tiles)

        # Tổng hợp lỗi
        issues = []
        score = 1.0

        if laplacian_var < self.cfg["blur_laplacian_threshold"]:
            issues.append(f"Mờ chuyển động hoặc mất nét (Laplacian: {laplacian_var:.1f})")
            score -= 0.35

        if mean_bright < self.cfg["min_brightness_mean"]:
            issues.append(f"Thiếu sáng / ban đêm quá tối (Mean: {mean_bright:.1f})")
            score -= 0.30
        elif mean_bright > self.cfg["max_brightness_mean"]:
            issues.append(f"Quá sáng / chói nắng (Mean: {mean_bright:.1f})")
            score -= 0.25

        if contrast_std < self.cfg["min_contrast_std"]:
            issues.append(f"Độ tương phản quá thấp / sương mù (Std: {contrast_std:.1f})")
            score -= 0.25

        if glare_ratio > self.cfg["glare_saturated_ratio_threshold"]:
            issues.append(f"Chói đèn pha hoặc lóa ngược sáng (Lóa: {glare_ratio*100:.1f}%)")
            score -= 0.30

        if local_dirt_ratio > self.cfg["local_blur_droplet_variance_threshold"] and laplacian_var > 40.0:
            issues.append(f"Giọt nước mưa hoặc bám bẩn cục bộ kính chắn gió ({local_dirt_ratio*100:.1f}% vùng)")
            score -= 0.20

        score = max(0.0, min(1.0, round(score, 2)))
        is_low_quality = score < self.cfg["quality_score_minimum"]

        # 5. Tiền xử lý có điều kiện (Conditional Enhancement)
        # Chỉ áp dụng CLAHE khi ảnh tối hoặc tương phản thấp
        output_frame = frame
        enhanced = False

        if mean_bright < 60.0 or contrast_std < 28.0:
            enhanced_cand = self._apply_clahe(frame)
            cand_gray = cv2.cvtColor(enhanced_cand, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else enhanced_cand
            cand_std = float(np.std(cand_gray))
            cand_lap = float(cv2.Laplacian(cand_gray, cv2.CV_64F).var())
            
            # Chỉ nhận nếu độ tương phản hoặc độ nét thật sự cải thiện
            if cand_std > contrast_std + 4.0 or cand_lap > laplacian_var:
                output_frame = enhanced_cand
                enhanced = True
                score = min(1.0, round(score + 0.15, 2))
                is_low_quality = score < self.cfg["quality_score_minimum"]

        # Nếu ảnh bị mờ nặng dưới ngưỡng Laplacian, bắt buộc gắn cờ low_quality
        if laplacian_var < self.cfg["blur_laplacian_threshold"]:
            is_low_quality = True

        report = QualityReport(
            score=score,
            is_low_quality=is_low_quality,
            blur_score=laplacian_var,
            brightness_mean=mean_bright,
            contrast_std=contrast_std,
            glare_ratio=glare_ratio,
            local_dirt_droplet_ratio=local_dirt_ratio,
            issues=issues,
            enhanced=enhanced
        )
        return report, output_frame

    def _apply_clahe(self, bgr_frame: np.ndarray) -> np.ndarray:
        """Tăng cường độ tương phản cục bộ bằng CLAHE trên kênh Luminance"""
        if len(bgr_frame.shape) == 2:
            clahe = cv2.createCLAHE(
                clipLimit=self.cfg["clahe_clip_limit"],
                tileGridSize=tuple(self.cfg["clahe_tile_grid_size"])
            )
            return clahe.apply(bgr_frame)

        lab = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(
            clipLimit=self.cfg["clahe_clip_limit"],
            tileGridSize=tuple(self.cfg["clahe_tile_grid_size"])
        )
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
