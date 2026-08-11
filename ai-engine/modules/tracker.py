"""
tracker.py
----------
Bộ theo dõi đối tượng (tracker) đơn giản dựa trên IoU + khoảng cách tâm điểm.
Không cần thư viện nặng (DeepSORT/ByteTrack) vẫn đủ ổn định cho demo.
Mỗi track giữ lịch sử bounding box để phục vụ:
  - Đếm zone (biết track đã đi qua zone nào)
  - Cảnh báo va chạm (tính tốc độ tăng kích thước hộp)
  - Giới hạn tần suất OCR biển số theo từng track
"""

from .utils import iou, box_center
import numpy as np


class Track:
    def __init__(self, track_id, box, cls_name):
        self.id = track_id
        self.cls_name = cls_name
        self.boxes = [box]           # lịch sử bounding box
        self.centers = [box_center(box)]
        self.age = 0                 # số khung hình chưa bị mất dấu
        self.hits = 1                # số lần được match liên tiếp
        self.zones_visited = set()   # các zone đã đi qua (để không đếm trùng)
        self.plate_text = None       # biển số đã đọc được (cache)
        self.helmet_status = None    # None=chưa xác định, True=có mũ, False=không mũ
        self.last_seen_frame = 0

    def update(self, box, frame_idx):
        self.boxes.append(box)
        self.centers.append(box_center(box))
        if len(self.boxes) > 30:
            self.boxes.pop(0)
            self.centers.pop(0)
        self.age = 0
        self.hits += 1
        self.last_seen_frame = frame_idx

    @property
    def current_box(self):
        return self.boxes[-1]

    def growth_rate(self, n_frames=5):
        """Tốc độ tăng chiều cao hộp trong n_frames gần nhất (dùng cho collision warning)."""
        if len(self.boxes) < n_frames:
            return 0.0
        h_old = self.boxes[-n_frames][3] - self.boxes[-n_frames][1]
        h_new = self.boxes[-1][3] - self.boxes[-1][1]
        if h_old <= 0:
            return 0.0
        return (h_new - h_old) / h_old


class SimpleTracker:
    """Tracker theo IoU giữa khung hình liên tiếp, gán ID bền vững cho mỗi đối tượng."""

    def __init__(self, iou_threshold=0.3, max_age=15):
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.next_id = 1
        self.tracks = {}  # id -> Track

    def update(self, detections, frame_idx):
        """
        detections: list of (box, cls_name)
        Trả về list of Track hiện đang active (đã match hoặc mới tạo trong khung này)
        """
        unmatched_tracks = set(self.tracks.keys())
        matched_this_frame = []

        for box, cls_name in detections:
            best_id, best_iou = None, 0.0
            for tid in unmatched_tracks:
                track = self.tracks[tid]
                if track.cls_name != cls_name:
                    continue
                score = iou(track.current_box, box)
                if score > best_iou:
                    best_iou = score
                    best_id = tid

            if best_id is not None and best_iou >= self.iou_threshold:
                self.tracks[best_id].update(box, frame_idx)
                unmatched_tracks.discard(best_id)
                matched_this_frame.append(self.tracks[best_id])
            else:
                new_track = Track(self.next_id, box, cls_name)
                new_track.last_seen_frame = frame_idx
                self.tracks[self.next_id] = new_track
                matched_this_frame.append(new_track)
                self.next_id += 1

        # Tăng tuổi (age) cho các track không match, xoá nếu quá cũ
        for tid in list(self.tracks.keys()):
            if tid not in [t.id for t in matched_this_frame]:
                self.tracks[tid].age += 1
                if self.tracks[tid].age > self.max_age:
                    del self.tracks[tid]

        return matched_this_frame
