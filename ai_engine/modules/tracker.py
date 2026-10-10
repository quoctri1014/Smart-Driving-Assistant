"""
tracker.py
----------
Bộ theo dõi đa đối tượng tiên tiến kết hợp BoT-SORT / ByteTrack và Kalman Filter 2D:
1. Camera Motion Compensation (CMC): Bù rung xóc camera bằng Phase Correlation / ECC.
2. ReID Appearance Embedding: Trích xuất vector đặc trưng diện mạo (HSV Color Histogram) để nhận diện lại xe.
3. Xử lý che khuất dài (> 1 giây): Lưu vết ở trạng thái 'lost' và khôi phục ID gốc bằng ReID khi xe xuất hiện lại.
4. Triệt tiêu track ma (Ghost Tracks): Tự động xóa sớm các track rác chưa đủ số lần match.
5. Cấu hình ngưỡng linh hoạt từ adas_config.json, tương thích 100% giao diện SimpleTracker.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np

try:
    import config
except ImportError:
    from ai_engine import config
from .utils import box_center, iou

CONFIG_PATH = Path("ai_engine/config/adas_config.json")


def _load_tracker_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("modules_config", {}).get("m2_tracking", {})
        except Exception:
            pass
    return {
        "max_lost_frames": 35,
        "reid_similarity_threshold": 0.65,
        "ecc_camera_motion_compensation": True,
        "ghost_track_min_hits": 2
    }


def compute_appearance_embedding(crop: np.ndarray) -> Optional[np.ndarray]:
    """Trích xuất histogram màu HSV 2D chuẩn hóa làm vector diện mạo (ReID)."""
    if crop is None or crop.size == 0 or crop.shape[0] < 10 or crop.shape[1] < 10:
        return None
    try:
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [8, 8], [0, 180, 0, 256])
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        return hist.flatten()
    except Exception:
        return None


def appearance_similarity(emb1: Optional[np.ndarray], emb2: Optional[np.ndarray]) -> float:
    """Đo độ tương đồng diện mạo giữa 2 embedding (1.0 = giống hệt, 0.0 = khác biệt)."""
    if emb1 is None or emb2 is None:
        return 0.0
    # Dùng Cosine similarity
    dot = np.dot(emb1, emb2)
    norm = (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    return float(dot / norm) if norm > 0 else 0.0


class KalmanBoxTracker:
    """
    Bộ lọc Kalman 2D theo dõi trạng thái bounding box:
    State: [x_center, y_center, aspect_ratio (w/h), height, dx, dy, da, dh]
    """
    count = 0

    def __init__(self, bbox):
        self.dim_x = 8
        self.dim_z = 4

        self.x = np.zeros((self.dim_x, 1))
        self.F = np.eye(self.dim_x)
        for i in range(4):
            self.F[i, i + 4] = 1.0

        self.H = np.zeros((self.dim_z, self.dim_x))
        for i in range(4):
            self.H[i, i] = 1.0

        self.P = np.eye(self.dim_x) * 10.0
        self.P[4:, 4:] *= 100.0

        self.R = np.eye(self.dim_z) * 1.0
        self.R[2:, 2:] *= 10.0

        self.Q = np.eye(self.dim_x) * 0.01
        self.Q[4:, 4:] *= 0.1

        w = max(1.0, bbox[2] - bbox[0])
        h = max(1.0, bbox[3] - bbox[1])
        cx = bbox[0] + w / 2.0
        cy = bbox[1] + h / 2.0
        self.x[0, 0] = cx
        self.x[1, 0] = cy
        self.x[2, 0] = w / h
        self.x[3, 0] = h

    def predict(self):
        """Dự đoán trạng thái ở bước tiếp theo."""
        self.x = np.dot(self.F, self.x)
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q
        return self.get_state()

    def update(self, bbox):
        """Cập nhật trạng thái khi có bounding box đo lường."""
        w = max(1.0, bbox[2] - bbox[0])
        h = max(1.0, bbox[3] - bbox[1])
        cx = bbox[0] + w / 2.0
        cy = bbox[1] + h / 2.0
        z = np.array([[cx], [cy], [w / h], [h]])

        y = z - np.dot(self.H, self.x)
        S = np.dot(np.dot(self.H, self.P), self.H.T) + self.R
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))

        self.x = self.x + np.dot(K, y)
        I = np.eye(self.dim_x)
        self.P = np.dot(I - np.dot(K, self.H), self.P)

    def apply_cmc_offset(self, dx: float, dy: float):
        """Bù dịch chuyển do rung lắc camera (Camera Motion Compensation)."""
        self.x[0, 0] += dx
        self.x[1, 0] += dy

    def get_state(self):
        """Chuyển đổi trạng thái Kalman về dạng (x1, y1, x2, y2)."""
        cx = float(self.x[0, 0])
        cy = float(self.x[1, 0])
        s = max(0.1, float(self.x[2, 0]))
        h = max(1.0, float(self.x[3, 0]))
        w = max(1.0, s * h)
        return (cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0)


class Track:
    """
    Quản lý thông tin và lịch sử của một phương tiện/đối tượng theo dõi.
    """
    def __init__(self, track_id: int, box: Tuple[float, float, float, float], cls_name: str, timestamp: float = 0.0):
        self.id = track_id
        self.cls_name = cls_name
        self.kalman = KalmanBoxTracker(box)
        self.boxes = [box]
        self.timestamps = [timestamp]
        self.centers = [box_center(box)]
        self.age = 0
        self.hits = 1
        self.zones_visited: Set[str] = set()
        self.plate_text: Optional[str] = None
        self.plate_votes = Counter()
        self.plate_confidence = 0.0
        self.plate_status = "NOT_READABLE"
        self.helmet_status = None
        self.last_seen_frame = 0
        self._velocity = (0.0, 0.0)
        self.embedding: Optional[np.ndarray] = None
        self.is_lost = False

    def predict(self):
        return self.kalman.predict()

    def update(self, box, frame_idx: int, timestamp=None, crop=None):
        self.kalman.update(box)
        state_box = self.kalman.get_state()

        prev_cx, prev_cy = self.centers[-1]
        new_cx, new_cy = box_center(state_box)
        self._velocity = (new_cx - prev_cx, new_cy - prev_cy)

        self.kalman_box = state_box
        self.boxes.append(box)
        self.timestamps.append(frame_idx / 25.0 if timestamp is None else timestamp)
        self.centers.append((new_cx, new_cy))

        if len(self.boxes) > 40:
            self.boxes.pop(0)
            self.centers.pop(0)
            self.timestamps.pop(0)

        self.age = 0
        self.hits += 1
        self.last_seen_frame = frame_idx
        self.is_lost = False

        # Cập nhật ReID appearance embedding
        if crop is not None:
            new_emb = compute_appearance_embedding(crop)
            if new_emb is not None:
                if self.embedding is None:
                    self.embedding = new_emb
                else:
                    self.embedding = 0.85 * self.embedding + 0.15 * new_emb

    def mark_missed(self):
        self.age += 1
        if self.age > 2:
            self.is_lost = True

    @property
    def current_box(self):
        return self.boxes[-1]

    def growth_rate(self, n_frames=5):
        if len(self.boxes) < n_frames:
            return 0.0
        h_old = self.boxes[-n_frames][3] - self.boxes[-n_frames][1]
        h_new = self.boxes[-1][3] - self.boxes[-1][1]
        if h_old <= 0:
            return 0.0
        elapsed = self.timestamps[-1] - self.timestamps[-n_frames]
        return (h_new - h_old) / h_old / elapsed if elapsed > 0 else 0.0


class SimpleTracker:
    """
    ByteTrack / BoT-SORT Tracker kết hợp Kalman Filter, CMC và ReID appearance recovery.
    """
    def __init__(self, max_age: int = 25, min_hits: int = 2, iou_threshold: float = 0.3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.tracks: List[Track] = []
        self.lost_tracks: List[Track] = []  # Lưu track bị che khuất để nhận diện lại
        self.next_id = 1
        self.cfg = _load_tracker_config()
        self._prev_gray: Optional[np.ndarray] = None

    def _estimate_camera_motion(self, frame: Optional[np.ndarray]) -> Tuple[float, float]:
        """Ước lượng chuyển động rung của camera bằng Phase Correlation."""
        if frame is None or not self.cfg.get("ecc_camera_motion_compensation", True):
            return 0.0, 0.0

        try:
            curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Thu nhỏ để xử lý nhanh
            small_curr = cv2.resize(curr_gray, (320, 180)).astype(np.float32)

            if self._prev_gray is None:
                self._prev_gray = small_curr
                return 0.0, 0.0

            shift, response = cv2.phaseCorrelate(self._prev_gray, small_curr)
            self._prev_gray = small_curr

            if response > 0.35:
                # Nhân lại theo tỷ lệ khung hình gốc (ví dụ 1280x720 / 320x180 = 4)
                scale_x = frame.shape[1] / 320.0
                scale_y = frame.shape[0] / 180.0
                dx = -float(shift[0]) * scale_x
                dy = -float(shift[1]) * scale_y
                # Giới hạn ngưỡng rung hợp lý (< 40 pixel)
                if abs(dx) < 40 and abs(dy) < 40:
                    return dx, dy
        except Exception:
            pass

        return 0.0, 0.0

    def update(self, det_pairs, frame_idx: int, timestamp=None, frame=None):
        """
        det_pairs: List of (box, cls_name) hoặc (box, cls_name, conf)
        frame: Optional ảnh màu hiện tại để chạy CMC và trích xuất crop ReID.
        """
        # 1. Bù rung lắc camera cho tất cả active tracks
        dx, dy = self._estimate_camera_motion(frame)
        if abs(dx) > 0.1 or abs(dy) > 0.1:
            for t in self.tracks:
                t.kalman.apply_cmc_offset(dx, dy)

        # 2. Dự đoán vị trí Kalman
        for t in self.tracks:
            t.predict()

        # Chuẩn hóa det_pairs
        normalized_dets = []
        crops = []
        h_f, w_f = (frame.shape[:2]) if frame is not None else (720, 1280)

        for item in det_pairs:
            if len(item) == 2:
                box, cls_name = item
                conf = 0.9
            else:
                box, cls_name, conf = item
            normalized_dets.append((box, cls_name, conf))

            # Crop nếu có frame
            if frame is not None:
                x1, y1, x2, y2 = [int(max(0, v)) for v in box]
                x2, y2 = min(w_f, x2), min(h_f, y2)
                crop = frame[y1:y2, x1:x2] if (x2 > x1 and y2 > y1) else None
                crops.append(crop)
            else:
                crops.append(None)

        matched_tracks = set()
        matched_dets = set()

        # 3. Vòng 1: Khớp IoU + ReID giữa Active Tracks và Detections
        if self.tracks and normalized_dets:
            iou_matrix = np.zeros((len(self.tracks), len(normalized_dets)))
            for i, trk in enumerate(self.tracks):
                for j, (dbox, dcls, dconf) in enumerate(normalized_dets):
                    if trk.cls_name == dcls or (trk.cls_name in ("car", "truck", "bus") and dcls in ("car", "truck", "bus")):
                        base_iou = iou(trk.current_box, dbox)
                        if base_iou > 0.1 and trk.embedding is not None and crops[j] is not None:
                            det_emb = compute_appearance_embedding(crops[j])
                            sim = appearance_similarity(trk.embedding, det_emb)
                            # Kết hợp 70% IoU + 30% ReID
                            iou_matrix[i, j] = 0.70 * base_iou + 0.30 * sim
                        else:
                            iou_matrix[i, j] = base_iou
                    else:
                        iou_matrix[i, j] = 0.0

            while True:
                max_val = np.max(iou_matrix) if iou_matrix.size > 0 else 0.0
                if max_val < self.iou_threshold:
                    break
                i, j = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
                if i not in matched_tracks and j not in matched_dets:
                    trk = self.tracks[i]
                    dbox, dcls, _ = normalized_dets[j]
                    trk.update(dbox, frame_idx, timestamp, crop=crops[j])
                    matched_tracks.add(i)
                    matched_dets.add(j)
                iou_matrix[i, :] = -1
                iou_matrix[:, j] = -1

        # 4. Vòng 2: Xử lý che khuất dài (> 1s). Khớp các detections còn sót với Lost Tracks bằng ReID
        reid_threshold = self.cfg.get("reid_similarity_threshold", 0.65)
        for j, (dbox, dcls, dconf) in enumerate(normalized_dets):
            if j in matched_dets:
                continue
            if not self.lost_tracks or crops[j] is None:
                continue

            det_emb = compute_appearance_embedding(crops[j])
            if det_emb is None:
                continue

            best_lost_idx = -1
            best_sim = 0.0
            for l_idx, lost_trk in enumerate(self.lost_tracks):
                if lost_trk.cls_name == dcls and lost_trk.embedding is not None:
                    sim = appearance_similarity(lost_trk.embedding, det_emb)
                    if sim > best_sim and sim >= reid_threshold:
                        best_sim = sim
                        best_lost_idx = l_idx

            if best_lost_idx >= 0:
                recovered_trk = self.lost_tracks.pop(best_lost_idx)
                recovered_trk.update(dbox, frame_idx, timestamp, crop=crops[j])
                self.tracks.append(recovered_trk)
                matched_dets.add(j)

        # 5. Cập nhật các track chưa khớp
        for i, trk in enumerate(self.tracks):
            if i not in matched_tracks:
                trk.mark_missed()

        # 6. Khởi tạo track mới cho các detections còn lại
        for j, (dbox, dcls, dconf) in enumerate(normalized_dets):
            if j not in matched_dets:
                new_trk = Track(
                    self.next_id,
                    dbox,
                    dcls,
                    timestamp=frame_idx / 25.0 if timestamp is None else timestamp
                )
                if crops[j] is not None:
                    new_trk.embedding = compute_appearance_embedding(crops[j])
                self.next_id += 1
                self.tracks.append(new_trk)

        # 7. Phân loại track: Active, Lost, hoặc Xóa Ghost Tracks
        max_lost_frames = self.cfg.get("max_lost_frames", 35)
        surviving_tracks = []
        for t in self.tracks:
            # Triệt tiêu Ghost track (chỉ có 1 hit mà mất ngay ở frame kế tiếp)
            if t.hits < self.cfg.get("ghost_track_min_hits", 2) and t.age >= 2:
                continue

            if t.age == 0:
                surviving_tracks.append(t)
            elif t.age <= self.max_age:
                surviving_tracks.append(t)
            elif t.age <= max_lost_frames and t.hits >= 3:
                # Đưa vào danh sách Lost để chờ phục hồi
                self.lost_tracks.append(t)

        self.tracks = surviving_tracks
        # Dọn dẹp lost tracks quá cũ
        self.lost_tracks = [t for t in self.lost_tracks if t.age <= max_lost_frames]

        # Trả về các track đang hoạt động
        return [t for t in self.tracks if t.hits >= 1 and t.age == 0]
