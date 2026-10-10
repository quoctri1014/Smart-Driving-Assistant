"""
decision_engine.py
------------------
Decision Engine trung tâm cho hệ thống ADAS và Fleet Management:
1. Thu nhận mọi sự kiện từ cả Road Camera (ADAS đường) và Cabin Camera (DMS).
2. Lọc nhiễu qua EventNoiseFilter.
3. Trọng tài ưu tiên (Priority Arbiter):
   TTC > DMS Ngủ gật > Cự ly an toàn > Quá tốc độ > Dây an toàn/Giờ lái > Biển báo > Info.
4. Preemption (cảnh báo mức cao ngắt cảnh báo mức thấp).
5. Quyết định hành vi: UI Theme, Còi báo động (Sound Alert), Giọng đọc Tiếng Việt (Speech Prompt), Lưu Vi phạm & Bằng chứng DB.
"""

import time
import logging
from typing import List, Optional, Dict, Any

from backend.app.schemas.adas_event import AdasEvent, DecisionResult
from backend.app.core.noise_filter import EventNoiseFilter
from backend.app.core.voice_generator import VietnameseVoiceGenerator

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Trọng tài quyết định tập trung cho toàn bộ hệ thống ADAS.
    """

    # Thứ tự ưu tiên (số nhỏ hơn = ưu tiên cao hơn)
    MODULE_PRIORITY = {
        "ttc": 1,              # Va chạm: cao nhất
        "drowsiness": 2,       # Ngủ gật: cao thứ hai
        "dms": 2,              # EyesClosedMonitor: giám sát nhắm mắt tài xế
        "safe_distance": 3,    # Cự ly an toàn
        "speed": 4,            # Quá tốc độ
        "seatbelt": 5,         # Dây an toàn
        "driving_timer": 6,    # Nghỉ ngơi quá 4 giờ
        "helmet": 7,           # Mũ bảo hiểm
        "sign": 8,             # Biển báo giao thông
        "plate_ocr": 9,        # Biển số
        "zone": 10             # Thông tin làn/vùng
    }

    SEVERITY_WEIGHT = {
        "critical": 100,
        "warning": 50,
        "info": 10
    }

    def __init__(self, speech_cooldown: float = 4.0):
        self.noise_filter = EventNoiseFilter()
        self.speech_generator = VietnameseVoiceGenerator()
        
        # Quản lý giọng đọc: chống nói đè & lặp
        self.speech_cooldown = speech_cooldown
        self._last_speech_time = 0.0
        self._last_speech_priority = 999
        self._last_spoken_type = ""

        # Quản lý lưu vết vi phạm DB (chống ghi đè liên tục)
        self._last_recorded_violation = {}
        self.violation_cooldown = 15.0  # Giảm từ 30s xuống 15s để phản ứng nhạy hơn

    def _calculate_event_score(self, event: AdasEvent) -> int:
        """
        Tính điểm ưu tiên kết hợp giữa Module Priority và Severity.
        Điểm càng cao thì quyền ưu tiên càng lớn.
        """
        base_priority = self.MODULE_PRIORITY.get(event.module, 99)
        sev_weight = self.SEVERITY_WEIGHT.get(event.severity, 0)
        # Module ưu tiên cao (1, 2) có hệ số nhân lớn
        module_score = (20 - base_priority) * 10
        return sev_weight + module_score

    def process_events(
        self, 
        raw_events: List[AdasEvent], 
        session_id: Optional[int] = None, 
        driver_id: Optional[int] = None
    ) -> DecisionResult:
        """
        Nhận danh sách các sự kiện thô trong 1 khung hình, lọc nhiễu và đưa ra phán quyết.
        """
        now = time.time()
        
        # 1. Lọc qua Noise Filter
        valid_events: List[AdasEvent] = []
        active_keys = set()
        for ev in raw_events:
            if session_id:
                ev.session_id = session_id
            if driver_id:
                ev.driver_id = driver_id
                
            active_keys.add(f"{ev.module}:{ev.type}:{ev.payload.get('track_id') or 'global'}")
            filtered = self.noise_filter.filter_event(ev)
            if filtered:
                valid_events.append(filtered)
                
        self.noise_filter.decay_missing(active_keys)

        if not valid_events:
            return DecisionResult(
                primary_event=None,
                active_alerts=[],
                speech_prompt=None,
                sound_alert=None,
                should_record_violation=False,
                should_save_evidence=False,
                ui_theme="normal"
            )

        # 2. Xếp hạng ưu tiên các sự kiện đã qua lọc
        valid_events.sort(key=lambda ev: self._calculate_event_score(ev), reverse=True)
        primary = valid_events[0]
        primary_priority = self.MODULE_PRIORITY.get(primary.module, 99)

        # 3. Quyết định UI Theme
        if any(ev.severity == "critical" for ev in valid_events):
            ui_theme = "critical"
        elif any(ev.severity == "warning" for ev in valid_events):
            ui_theme = "warning"
        else:
            ui_theme = "caution"

        # 4. Quyết định Còi Báo Động (Sound Alert)
        sound_alert = None
        if primary.severity == "critical":
            sound_alert = "alarm_critical"
        elif primary.severity == "warning":
            sound_alert = "chime"

        # 5. Quyết định Giọng đọc tiếng Việt (Speech Prompt & Preemption Logic)
        speech_prompt = None
        time_since_last_speech = now - self._last_speech_time
        
        # Kiểm tra điều kiện ngắt (Preemption):
        # Nếu sự kiện hiện tại là CRITICAL và có độ ưu tiên cao hơn sự kiện trước,
        # cho phép ngắt ngang ngay cả khi chưa hết cooldown thông thường.
        is_preemption = (
            primary.severity == "critical" 
            and primary_priority < self._last_speech_priority
            and time_since_last_speech > 1.0  # Ít nhất 1s để không nát âm thanh
        )
        is_cooldown_passed = (time_since_last_speech >= self.speech_cooldown)

        if is_preemption or (is_cooldown_passed and primary.type != self._last_spoken_type):
            generated_text = self.speech_generator.generate_prompt(primary)
            if generated_text:
                speech_prompt = generated_text
                primary.speech_prompt = generated_text
                self._last_speech_time = now
                self._last_speech_priority = primary_priority
                self._last_spoken_type = primary.type

        # 6. Quyết định Ghi nhận Vi phạm DB và Lưu ảnh Bằng chứng
        should_record = False
        violation_type = None
        violation_severity = None
        should_save_evidence = False

        # Các module thuộc diện vi phạm cần xử lý lưu trữ
        recordable_modules = {"ttc", "drowsiness", "dms", "speed", "seatbelt", "helmet", "safe_distance", "driving_timer"}
        if primary.module in recordable_modules and primary.severity in ("warning", "critical"):
            last_recorded = self._last_recorded_violation.get(primary.type, 0.0)
            if (now - last_recorded) >= self.violation_cooldown:
                should_record = True
                violation_type = primary.type
                violation_severity = primary.severity
                should_save_evidence = True
                self._last_recorded_violation[primary.type] = now

        return DecisionResult(
            primary_event=primary,
            active_alerts=valid_events,
            speech_prompt=speech_prompt,
            sound_alert=sound_alert,
            should_record_violation=should_record,
            violation_type=violation_type,
            violation_severity=violation_severity,
            should_save_evidence=should_save_evidence,
            ui_theme=ui_theme
        )

    def reset(self):
        """Khởi động lại Decision Engine."""
        self.noise_filter.reset()
        self._last_speech_time = 0.0
        self._last_speech_priority = 999
        self._last_spoken_type = ""
        self._last_recorded_violation.clear()
