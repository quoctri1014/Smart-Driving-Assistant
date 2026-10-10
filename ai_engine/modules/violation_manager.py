"""
violation_manager.py
---------------------
Liên kết vi phạm mũ bảo hiểm ↔ biển số xe và lưu hồ sơ vi phạm.

Luồng hoạt động:
  1. HelmetChecker phát hiện người không đội mũ (helmet_status = False)
  2. ViolationManager nhận track_id của người vi phạm
  3. Tìm xe máy (motorbike) chứa người đó → lấy plate_text nếu có
  4. Tạo bản ghi vi phạm (ViolationRecord) với đầy đủ thông tin
  5. Lưu vào bộ nhớ (deque) và có thể export CSV/DB sau

Đây là chức năng #6 trong tài liệu thiết kế.
"""

from __future__ import annotations

import csv
import os
import time
import config
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional


# Giới hạn số bản ghi giữ trong RAM
MAX_VIOLATIONS_IN_MEMORY = 500


@dataclass
class ViolationRecord:
    """Bản ghi một lần vi phạm."""
    violation_id: int
    timestamp: str                  # ISO 8601
    violation_type: str             # "no_helmet", "speeding", ...
    track_id: int                   # Track ID của người vi phạm
    vehicle_track_id: Optional[int] # Track ID của xe (nếu biết)
    plate_text: Optional[str]       # Biển số xe (nếu đọc được)
    plate_confidence: float
    severity: str                   # "low", "medium", "high", "critical"
    frame_idx: int
    extra: Dict = field(default_factory=dict)  # Dữ liệu thêm tuỳ loại vi phạm


class ViolationManager:
    """
    Phát hiện và lưu vi phạm liên quan đến mũ bảo hiểm và biển số xe.

    Sử dụng:
        vm = ViolationManager()
        # Mỗi frame:
        vm.process_frame(vehicle_tracks, person_tracks, frame_idx)
        # Lấy danh sách:
        violations = vm.get_recent_violations()
    """

    def __init__(self, export_path: Optional[str] = None):
        self.violations: deque[ViolationRecord] = deque(maxlen=MAX_VIOLATIONS_IN_MEMORY)
        self.export_path = export_path  # Đường dẫn file CSV để export (None = không export)
        self._violation_counter = 0
        # Cache để tránh ghi trùng vi phạm của cùng 1 track trong nhiều frame
        self._seen_violations: Dict[str, float] = {}  # key → timestamp lần cuối
        self._dedupe_cooldown = 5.0  # giây

    def process_frame(
        self,
        vehicle_tracks: list,
        person_tracks: list,
        frame_idx: int,
        frame=None,
        plate_reader=None,
    ) -> List[ViolationRecord]:
        """
        Kiểm tra và ghi nhận vi phạm trong frame hiện tại.

        Args:
            vehicle_tracks: Danh sách track xe (từ tracker)
            person_tracks: Danh sách track người (từ tracker)
            frame_idx: Chỉ số frame hiện tại

        Returns:
            Danh sách vi phạm mới phát hiện trong frame này
        """
        new_violations = []

        # Tìm xe máy chứa từng người
        motorbike_tracks = [t for t in vehicle_tracks if t.cls_name == "motorbike"]
        person_to_bike = self._map_person_to_bike(person_tracks, motorbike_tracks)

        for person in person_tracks:
            if person.helmet_status is not False:
                continue
            if person.helmet_status is False:
                bike = person_to_bike.get(person.id)
                if bike is None:
                    continue  # Không ghi người đi bộ thành vi phạm xe máy.
                existing = next((r for r in reversed(self.violations)
                                 if r.violation_type == "no_helmet" and r.track_id == person.id), None)
                if not bike.plate_text and frame is not None and plate_reader is not None and (
                        existing is None or frame_idx % config.PLATE_OCR_INTERVAL == 0):
                    bike.plate_text = plate_reader.read_plate(frame, bike.current_box)
                if existing is not None:
                    if bike.plate_text and not existing.plate_text:
                        existing.plate_text = bike.plate_text
                        existing.plate_confidence = bike.plate_confidence
                        existing.extra["plate_read"] = True
                        if self.export_path:
                            self._update_csv(existing)
                    continue
                record = self._create_helmet_violation(person, bike, frame_idx)
                if record:
                    new_violations.append(record)
                    self.violations.append(record)
                    if self.export_path:
                        self._append_csv(record)

        return new_violations

    def add_speeding_violation(
        self,
        track,
        speed_kmh: float,
        speed_limit: float,
        frame_idx: int,
    ) -> Optional[ViolationRecord]:
        """Thêm bản ghi vượt tốc độ."""
        key = f"speeding_{track.id}"
        if self._is_duplicate(key):
            return None

        self._violation_counter += 1
        record = ViolationRecord(
            violation_id=self._violation_counter,
            timestamp=datetime.now().isoformat(),
            violation_type="speeding",
            track_id=track.id,
            vehicle_track_id=track.id,
            plate_text=track.plate_text,
            plate_confidence=track.plate_confidence,
            severity="high" if speed_kmh > speed_limit * 1.3 else "medium",
            frame_idx=frame_idx,
            extra={"speed_kmh": speed_kmh, "speed_limit": speed_limit},
        )
        self._mark_seen(key)
        self.violations.append(record)
        if self.export_path:
            self._append_csv(record)
        return record

    def get_recent_violations(self, n: int = 20) -> List[ViolationRecord]:
        """Trả về n vi phạm gần nhất."""
        return list(self.violations)[-n:]

    def get_violations_by_type(self, violation_type: str) -> List[ViolationRecord]:
        """Lọc vi phạm theo loại."""
        return [v for v in self.violations if v.violation_type == violation_type]

    def get_violations_by_plate(self, plate_text: str) -> List[ViolationRecord]:
        """Tìm vi phạm theo biển số xe."""
        return [v for v in self.violations if v.plate_text == plate_text]

    def export_csv(self, path: str) -> int:
        """Xuất toàn bộ vi phạm ra file CSV. Trả về số bản ghi đã ghi."""
        if not self.violations:
            return 0
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        rows = [asdict(v) for v in self.violations]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)

    # ------------------------------------------------------------------ private

    def _map_person_to_bike(self, person_tracks, motorbike_tracks) -> Dict[int, object]:
        """Ánh xạ person_id → motorbike track dựa trên vị trí centroid."""
        mapping = {}
        for person in person_tracks:
            px, py = person.centers[-1]
            for bike in motorbike_tracks:
                bx1, by1, bx2, by2 = bike.current_box
                # Mở rộng vùng bike 30% để bắt được người ngồi lệch
                pad_y = (by2 - by1) * 0.3
                if bx1 <= px <= bx2 and by1 - (by2 - by1) <= py <= by2 + pad_y:
                    mapping[person.id] = bike
                    break
        return mapping

    def _create_helmet_violation(
        self,
        person,
        bike,
        frame_idx: int,
    ) -> Optional[ViolationRecord]:
        """Tạo ViolationRecord cho vi phạm không đội mũ bảo hiểm."""
        key = f"no_helmet_{person.id}"
        if self._is_duplicate(key):
            return None

        self._violation_counter += 1
        plate_text = bike.plate_text if bike else None
        plate_conf = bike.plate_confidence if bike else 0.0
        bike_id = bike.id if bike else None

        record = ViolationRecord(
            violation_id=self._violation_counter,
            timestamp=datetime.now().isoformat(),
            violation_type="no_helmet",
            track_id=person.id,
            vehicle_track_id=bike_id,
            plate_text=plate_text,
            plate_confidence=plate_conf,
            severity="critical",
            frame_idx=frame_idx,
            extra={"plate_read": plate_text is not None},
        )
        self._mark_seen(key)
        return record

    def _is_duplicate(self, key: str) -> bool:
        last = self._seen_violations.get(key, 0.0)
        return (time.time() - last) < self._dedupe_cooldown

    def _mark_seen(self, key: str):
        self._seen_violations[key] = time.time()

    def _append_csv(self, record: ViolationRecord):
        """Ghi thêm 1 dòng vào file CSV (append mode)."""
        os.makedirs(os.path.dirname(os.path.abspath(self.export_path)), exist_ok=True)
        row = asdict(record)
        file_exists = os.path.isfile(self.export_path)
        with open(self.export_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    def _update_csv(self, record):
        """Enrich the original record when OCR arrives later; retain older rows."""
        with open(self.export_path, newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            fields = reader.fieldnames
            rows = list(reader)
        for row in rows:
            if row["violation_id"] == str(record.violation_id):
                row.update(asdict(record))
        temporary = self.export_path + ".tmp"
        with open(temporary, "w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, self.export_path)
