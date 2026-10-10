"""Phát hiện nhắm mắt kéo dài (DMS) bằng state machine theo thời gian thực.

Cách dùng trong pipeline (mỗi khung hình camera cabin):

    monitor = EyesClosedMonitor()
    result = monitor.update(time.monotonic(), face_found, ear, quality, head_pitch)
    for ev in result.events:      # -> đẩy vào Decision Engine dưới dạng AdasEvent
        ...
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EyeState(str, Enum):
    UNKNOWN = "UNKNOWN"            # không thấy mặt / ảnh kém -> KHÔNG cảnh báo
    CALIBRATING = "CALIBRATING"    # đang hiệu chuẩn theo tài xế
    OPEN = "OPEN"
    CLOSING = "CLOSING"            # đang nhắm nhưng chưa tới ngưỡng
    CLOSED_WARN = "CLOSED_WARN"    # >= warn_s
    CLOSED_CRITICAL = "CLOSED_CRITICAL"  # >= critical_s


@dataclass
class EyesClosedConfig:  # nên nạp từ adas_config.json
    warn_s: float = 2.0
    critical_s: float = 5.0
    gap_tolerance_s: float = 0.35    # mắt mở thoáng/mất detect <= 0.35s không reset
    min_blink_s: float = 0.5         # nhắm ngắn hơn coi là chớp mắt
    calib_s: float = 10.0            # thời gian hiệu chuẩn (chỉ tính khi thấy mặt)
    calib_min_samples: int = 30
    closed_ratio: float = 0.75       # ngưỡng nhắm = ratio * EAR mắt mở của tài xế
    open_ear_floor: float = 0.15     # mẫu EAR thấp hơn mức này không dùng để hiệu chuẩn
    min_quality: float = 0.5         # dưới mức này -> UNKNOWN
    cooldown_s: float = 10.0         # lặp lại cảnh báo critical nếu vẫn nhắm
    max_frame_gap_s: float = 3.5     # giữa 2 khung cách nhau > mức này (mạng lag) -> reset
    pitch_down_deg: float = -25.0    # cúi đầu: tăng độ tin cậy


@dataclass
class DmsResult:
    state: EyeState
    closed_duration_s: float = 0.0
    ear: Optional[float] = None
    threshold: Optional[float] = None
    events: list = field(default_factory=list)


class EyesClosedMonitor:
    def __init__(self, cfg: EyesClosedConfig | None = None,
                 baseline_ear: Optional[float] = None):
        self.cfg = cfg or EyesClosedConfig()
        self.baseline: Optional[float] = baseline_ear  # có sẵn -> bỏ qua hiệu chuẩn
        self._calib_samples: list[float] = []
        self._calib_started: Optional[float] = None
        self._reset_episode()
        self._last_update: Optional[float] = None

    # ------------------------------------------------------------------
    def _reset_episode(self):
        self._closed_start: Optional[float] = None
        self._last_closed: Optional[float] = None
        self._warn_sent = False
        self._last_critical: Optional[float] = None
        self._critical_sent = False

    @property
    def threshold(self) -> Optional[float]:
        return None if self.baseline is None else self.cfg.closed_ratio * self.baseline

    def _event(self, etype, severity, now, dur, ear, quality, pitch):
        conf = max(0.0, min(1.0, quality))
        if pitch is not None and pitch < self.cfg.pitch_down_deg:
            conf = min(1.0, conf + 0.1)  # cúi đầu + nhắm mắt: đáng tin hơn
        return {
            "module": "dms", "type": etype, "severity": severity, "timestamp": now,
            "confidence": round(conf, 3),
            "payload": {"duration_s": round(dur, 2), "ear": ear,
                        "threshold": self.threshold, "head_pitch": pitch},
        }

    # ------------------------------------------------------------------
    def update(self, now: float, face_found: bool, ear: Optional[float],
               quality: float = 1.0, head_pitch: Optional[float] = None) -> DmsResult:
        c = self.cfg
        events: list = []

        # Khoảng trống lớn giữa 2 khung (lag/đứng hình) -> không suy diễn
        if self._last_update is not None and now - self._last_update > c.max_frame_gap_s:
            self._reset_episode()
        self._last_update = now

        # 1) Không thấy mặt / ảnh kém / EAR không hợp lệ -> kiểm tra dung sai gap tolerance
        if (not face_found) or ear is None or quality < c.min_quality:
            if self._closed_start is not None and self._last_closed is not None:
                if now - self._last_closed <= c.gap_tolerance_s:
                    dur = now - self._closed_start
                    state = EyeState.CLOSED_CRITICAL if dur >= c.critical_s else (EyeState.CLOSED_WARN if dur >= c.warn_s else EyeState.CLOSING)
                    return DmsResult(state, dur, ear, self.threshold, events)
                else:
                    dur = self._last_closed - self._closed_start
                    if self._critical_sent:
                        events.append(self._event("eyes_reopened", "info", now, dur, ear, quality, head_pitch))
            self._reset_episode()
            return DmsResult(EyeState.UNKNOWN, 0.0, ear, self.threshold, events)

        # 2) Hiệu chuẩn cá nhân
        if self.baseline is None:
            if self._calib_started is None:
                self._calib_started = now
            if ear >= c.open_ear_floor:
                self._calib_samples.append(ear)
            if (now - self._calib_started >= c.calib_s
                    and len(self._calib_samples) >= c.calib_min_samples):
                self.baseline = statistics.median(self._calib_samples)
            else:
                return DmsResult(EyeState.CALIBRATING, 0.0, ear, None)

        closed = ear < self.threshold

        # 3) Cập nhật đợt nhắm mắt (có dung sai khoảng hở)
        if closed:
            self._last_closed = now
            if self._closed_start is None:
                self._closed_start = now
        elif self._closed_start is not None and now - self._last_closed > c.gap_tolerance_s:
            dur = self._last_closed - self._closed_start
            if self._critical_sent:
                events.append(self._event("eyes_reopened", "info", now, dur, ear, quality, head_pitch))
            self._reset_episode()

        # 4) Tính thời lượng và trạng thái
        if self._closed_start is None:
            return DmsResult(EyeState.OPEN, 0.0, ear, self.threshold, events)

        dur = (now if closed else self._last_closed) - self._closed_start
        if dur >= c.critical_s:
            state = EyeState.CLOSED_CRITICAL
            first = not self._critical_sent
            repeat = (self._last_critical is not None
                      and now - self._last_critical >= c.cooldown_s)
            if closed and (first or repeat):
                events.append(self._event("eyes_closed_prolonged", "critical",
                                          now, dur, ear, quality, head_pitch))
                self._last_critical = now
                self._critical_sent = True
        elif dur >= c.warn_s:
            state = EyeState.CLOSED_WARN
            if not self._warn_sent and closed:
                events.append(self._event("eyes_closed_warning", "warning",
                                          now, dur, ear, quality, head_pitch))
                self._warn_sent = True
        elif dur >= c.min_blink_s:
            state = EyeState.CLOSING
        else:
            state = EyeState.OPEN  # chớp mắt bình thường

        return DmsResult(state, dur, ear, self.threshold, events)
