"""
driver_monitor.py
-----------------
Pipeline orchestrator cho giám sát tài xế trong cabin (DMS):
- #10: DrowsinessDetector (MediaPipe Face Mesh + Auto-calibration + MAR fix)
- #11: SeatbeltChecker (Tư thế và dây an toàn qua vai)
- #12: DrivingTimer (Theo dõi thời gian lái xe liên tục theo luật GTVT)
- Tích hợp DecisionEngine để xếp ưu tiên, phát giọng đọc tiếng Việt và còi cảnh báo.
"""

import time
import logging
from typing import Optional, List

from .drowsiness_detector import DrowsinessDetector
from .seatbelt_checker import SeatbeltChecker
from .driving_timer import DrivingTimer
from backend.app.schemas.adas_event import AdasEvent, DecisionResult as AdasDecisionResult
from backend.app.core.decision_engine import DecisionEngine

logger = logging.getLogger(__name__)


class DriverPipelineSession:
    """
    Per-connection session cho camera cabin (giám sát tài xế).
    """

    def __init__(self):
        self.drowsiness_detector = DrowsinessDetector()
        self.seatbelt_checker = SeatbeltChecker()
        self.driving_timer = DrivingTimer()
        self.decision_engine = DecisionEngine()
        self.frame_idx = 0
        self.last_decision: Optional[AdasDecisionResult] = None

    def process_driver_frame(
        self, 
        frame,
        session_id: Optional[int] = None,
        driver_id: Optional[int] = None
    ) -> dict:
        """
        Xử lý 1 frame từ camera cabin và phát quyết định qua Decision Engine.
        """
        t_start = time.time()
        self.frame_idx += 1

        drowsiness_res = self.drowsiness_detector.detect(frame)
        seatbelt_res = self.seatbelt_checker.check(frame)
        time_res = self.driving_timer.update()

        # Tổng hợp các sự kiện cabin
        raw_events: List[AdasEvent] = []

        # 1. Sự kiện từ EyesClosedMonitor / DMS
        dms_events = drowsiness_res.get("events", [])
        if dms_events:
            for dev in dms_events:
                raw_events.append(AdasEvent(
                    module="dms",
                    type=dev.get("type", "eyes_closed_prolonged"),
                    severity=dev.get("severity", "critical"),
                    confidence=dev.get("confidence", 0.90),
                    payload=dev.get("payload", {})
                ))

        drowsy_level = drowsiness_res.get("alert_level", "normal")
        if not dms_events and drowsy_level in ("warning", "critical"):
            raw_events.append(AdasEvent(
                module="drowsiness",
                type="drowsy",
                severity=drowsy_level,
                confidence=0.85,
                payload={"ear": drowsiness_res.get("ear_value"), "yawns": drowsiness_res.get("yawn_count")}
            ))

        # 2. Sự kiện chưa thắt dây an toàn
        if seatbelt_res.get("seatbelt_on") is False:
            raw_events.append(AdasEvent(
                module="seatbelt",
                type="no_seatbelt",
                severity="critical",
                confidence=seatbelt_res.get("confidence", 0.80)
            ))

        # 3. Sự kiện lái xe quá 4 giờ liên tục
        if time_res.get("should_rest") is True:
            raw_events.append(AdasEvent(
                module="driving_timer",
                type="fatigue_break",
                severity="warning",
                confidence=0.99,
                payload={"hours": time_res.get("continuous_minutes", 240) / 60.0}
            ))

        # Xử lý qua Decision Engine
        decision = self.decision_engine.process_events(
            raw_events, session_id=session_id, driver_id=driver_id
        )
        self.last_decision = decision

        # Tổng hợp mức cảnh báo tổng thể cabin
        combined = self.driving_timer.combined_alert_level(drowsy_level)
        if seatbelt_res.get("seatbelt_on") is False and combined != "critical":
            combined = "warning"

        proc_time = (time.time() - t_start) * 1000

        return {
            "frame_id": self.frame_idx,
            "timestamp": time.time(),
            "drowsiness": drowsiness_res,
            "seatbelt": seatbelt_res,
            "driving_time": time_res,
            "combined_alert_level": combined,
            "processing_time_ms": round(proc_time, 2),
            "speech_prompt": decision.speech_prompt,
            "sound_alert": decision.sound_alert,
            "decision": decision.model_dump()
        }

    def notify_break_started(self):
        """Gọi khi phát hiện tài xế dừng xe nghỉ ngơi."""
        self.driving_timer.start_break()
        self.drowsiness_detector.reset()
        self.decision_engine.reset()

    def notify_break_ended(self):
        """Gọi khi tài xế bắt đầu lái lại sau nghỉ."""
        self.driving_timer.end_break()

    def close(self):
        self.drowsiness_detector.close()
