"""
driving_timer.py
-----------------
Theo dõi thời gian lái xe liên tục và tổng thời gian lái xe trong ngày:
Căn cứ pháp lý:
- Điều 65 Luật Giao thông đường bộ & Luật Trật tự, an toàn giao thông đường bộ:
  1. Thời gian lái xe liên tục của người lái xe ô tô không quá 04 giờ.
  2. Tổng thời gian lái xe trong một ngày không quá 10 giờ.
  3. Thời gian nghỉ tối thiểu sau 04 giờ lái liên tục là 15 phút.

Quy tắc xử lý ngoại lệ:
- Dừng đèn đỏ / kẹt xe (< 15 phút): TUYỆT ĐỐI KHÔNG TÍNH LÀ NGHỈ NGƠI, đồng hồ lái vẫn tiếp tục đếm.
- Lưu trạng thái bền vững (Persistent Storage): Không mất dữ liệu khi app bị tắt/kill đột ngột.
- Khôi phục phiên khi mở lại app: Nếu thời gian tắt app < 15 phút thì cộng dồn tiếp; nếu >= 15 phút thì tính là đợt nghỉ hợp lệ.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import config

CONFIG_PATH = Path("ai_engine/config/adas_config.json")
STORAGE_PATH = Path("storage/driving_timer_state.json")


def _load_driving_timer_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("modules_config", {}).get("m12_seatbelt_driving_timer", {})
        except Exception:
            pass
    return {
        "continuous_driving_limit_hours": 4.0,
        "daily_driving_limit_hours": 10.0,
        "min_rest_duration_minutes": 15.0
    }


class DrivingTimer:
    """
    Bộ đếm thời gian lái xe tuân thủ pháp luật và lưu trữ bền vững.
    """

    def __init__(self, clock=None, state_file: Optional[Path] = None):
        self._clock = clock or time.time
        self.state_file = state_file or STORAGE_PATH
        self.cfg = _load_driving_timer_config()

        self.max_continuous_minutes = float(self.cfg.get("continuous_driving_limit_hours", 4.0)) * 60.0
        self.max_daily_minutes = float(self.cfg.get("daily_driving_limit_hours", 10.0)) * 60.0
        self.min_rest_minutes = float(self.cfg.get("min_rest_duration_minutes", 15.0))

        # Khởi tạo hoặc tải từ file lưu trữ bền vững
        self.continuous_seconds = 0.0
        self.daily_seconds = 0.0
        self.last_update_ts = self._clock()
        self.rest_start_ts: Optional[float] = None
        self.is_resting = False

        if clock is None:
            self._load_persistent_state()

    def _load_persistent_state(self):
        """Khôi phục trạng thái khi app/service bị kill hoặc khởi động lại."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                last_ts = data.get("last_update_ts", 0.0)
                now = self._clock()
                elapsed_minutes = (now - last_ts) / 60.0 if last_ts > 0 else 0.0

                if elapsed_minutes >= self.min_rest_minutes:
                    # Nghỉ đủ >= 15 phút trong lúc tắt app -> reset đồng hồ liên tục
                    self.continuous_seconds = 0.0
                    self.daily_seconds = data.get("daily_seconds", 0.0)
                else:
                    # Tắt app chớp nhoáng hoặc đứt mạng -> cộng dồn tiếp
                    self.continuous_seconds = data.get("continuous_seconds", 0.0)
                    self.daily_seconds = data.get("daily_seconds", 0.0)
            except Exception:
                pass

    def _save_persistent_state(self):
        """Lưu bền vững ra disk."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump({
                    "continuous_seconds": self.continuous_seconds,
                    "daily_seconds": self.daily_seconds,
                    "last_update_ts": self.last_update_ts,
                    "is_resting": self.is_resting
                }, f)
        except Exception:
            pass

    def update(self, is_vehicle_moving: Optional[bool] = None, speed_kmh: Optional[float] = None) -> Dict[str, Any]:
        """
        Cập nhật trạng thái thời gian lái xe:
        - Nếu dừng đèn đỏ (speed < 1.5 km/h) nhưng thời gian dừng chưa đủ 15 phút: VẪN TÍNH LÀ ĐANG LÁI.
        - Chỉ reset khi tài xế chủ động nghỉ hoặc đỗ xe liên tục >= 15 phút.
        """
        now = self._clock()
        dt = max(0.0, now - self.last_update_ts)
        self.last_update_ts = now

        # Dừng xe hoặc đỗ
        if self.is_resting:
            if is_vehicle_moving is True and (speed_kmh is None or speed_kmh >= 1.5):
                # Xe bắt đầu di chuyển lại
                self.is_resting = False
                self.rest_start_ts = None
                self.continuous_seconds += dt
                self.daily_seconds += dt
            else:
                # Vẫn đang nghỉ
                rest_elapsed_min = (now - self.rest_start_ts) / 60.0 if self.rest_start_ts else 0.0
                if rest_elapsed_min >= self.min_rest_minutes:
                    self.continuous_seconds = 0.0
        elif is_vehicle_moving is False or (speed_kmh is not None and speed_kmh < 1.5):
            self.rest_start_ts = now
            self.is_resting = True
        else:
            self.continuous_seconds += dt
            self.daily_seconds += dt

        continuous_min = self.continuous_seconds / 60.0
        daily_min = self.daily_seconds / 60.0

        alert_level = "normal"
        message = "Thời gian lái xe trong giới hạn an toàn."

        # Cảnh báo theo quy định
        if continuous_min >= self.max_continuous_minutes:
            alert_level = "critical"
            message = (
                f"⚠️ VI PHẠM LUẬT GIAO THÔNG: Đã lái liên tục {continuous_min:.0f} phút "
                f"(vượt ngưỡng 4 giờ / 240 phút). Dừng xe nghỉ tối thiểu 15 phút ngay!"
            )
        elif daily_min >= self.max_daily_minutes:
            alert_level = "critical"
            message = f"⚠️ VI PHẠM: Tổng thời gian lái trong ngày đã vượt 10 giờ ({daily_min:.0f} phút). Ngừng lái xe!"
        elif continuous_min >= (self.max_continuous_minutes - 15.0):
            alert_level = "reminder"
            remaining = self.max_continuous_minutes - continuous_min
            message = f"🔔 NHẮC NHỞ: Còn {remaining:.0f} phút nữa sẽ chạm giới hạn 4 giờ lái xe liên tục."

        self._save_persistent_state()

        return {
            "continuous_minutes": round(continuous_min, 1),
            "daily_minutes": round(daily_min, 1),
            "max_continuous_minutes": self.max_continuous_minutes,
            "max_daily_minutes": self.max_daily_minutes,
            "alert_level": alert_level,
            "should_rest": alert_level == "critical",
            "message": message,
            "is_resting": self.is_resting,
            "legal_source": "Điều 65 Luật Giao thông đường bộ (Tối đa 4h liên tục, 10h/ngày, nghỉ >= 15p)"
        }

    def combined_alert_level(self, drowsiness_level: str) -> str:
        """
        Kết hợp alert từ buồn ngủ + thời gian lái xe theo thang ưu tiên cabin.
        """
        timer_status = self.update()
        timer_level = timer_status["alert_level"]

        severity_rank = {"normal": 0, "caution": 1, "reminder": 1, "warning": 2, "critical": 3}
        t_rank = severity_rank.get(timer_level, 0)
        d_rank = severity_rank.get(drowsiness_level, 0)

        if t_rank >= 3 or d_rank >= 3 or (t_rank >= 1 and d_rank >= 2):
            return "critical"
        if t_rank >= 2 or d_rank >= 2:
            return "warning"
        if t_rank >= 1 or d_rank >= 1:
            return "caution"
        return "normal"

    def start_break(self):
        """Bắt đầu phiên nghỉ ngơi chính thức."""
        self.is_resting = True
        self.rest_start_ts = self._clock()

    def end_break(self):
        """Kết thúc phiên nghỉ ngơi."""
        now = self._clock()
        if self.is_resting and self.rest_start_ts:
            rest_minutes = (now - self.rest_start_ts) / 60.0
            if rest_minutes >= self.min_rest_minutes:
                self.continuous_seconds = 0.0
        self.is_resting = False
        self.rest_start_ts = None
        self._save_persistent_state()

    def reset(self):
        """Reset phiên lái mới (đầu ngày hoặc đổi tài xế)."""
        self.continuous_seconds = 0.0
        self.daily_seconds = 0.0
        self.is_resting = False
        self.rest_start_ts = None
        self._save_persistent_state()
