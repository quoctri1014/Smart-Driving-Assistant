"""
adas_event.py
-------------
Schema sự kiện ADAS chuẩn hoá (Pydantic).
Mọi module trong AI Pipeline và Decision Engine đều giao tiếp qua Schema này.
"""

from typing import Any, Dict, Optional, Literal
from pydantic import BaseModel, Field
import uuid
import time


class AdasEvent(BaseModel):
    """
    Schema chuẩn cho tất cả các sự kiện an toàn giao thông và hành vi tài xế.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[int] = None
    vehicle_id: Optional[str] = None
    driver_id: Optional[int] = None
    
    # Module phát sinh sự kiện
    module: Literal[
        "ttc",              # Time-to-Collision / Va chạm sớm
        "drowsiness",       # DMS ngủ gật
        "safe_distance",    # Cự ly an toàn
        "speed",            # Giám sát tốc độ
        "sign",             # Nhận diện biển báo giao thông
        "seatbelt",         # Dây an toàn
        "helmet",           # Mũ bảo hiểm xe máy
        "driving_timer",    # Thời gian lái xe liên tục
        "zone",             # Quản lý làn/vùng
        "plate_ocr"         # Nhận diện biển số xe
    ]
    
    # Loại sự kiện chi tiết
    type: str
    
    # Mức độ nghiêm trọng
    severity: Literal["info", "warning", "critical"]
    
    # Độ tin cậy thuật toán (0.0 đến 1.0)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    
    # Thời gian phát sinh (timestamp unix)
    timestamp: float = Field(default_factory=time.time)
    
    # Chi tiết dữ liệu đính kèm
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    # Đường dẫn ảnh bằng chứng (nếu có)
    evidence_ref: Optional[str] = None
    
    # Câu nhắc giọng đọc tiếng Việt sinh ra từ Decision Engine
    speech_prompt: Optional[str] = None
    
    # Hành động khuyến nghị cho tài xế / hệ thống
    action_required: Optional[str] = None


class DecisionResult(BaseModel):
    """
    Kết quả quyết định sau khi Decision Engine tổng hợp và xử lý ưu tiên.
    """
    primary_event: Optional[AdasEvent] = None
    active_alerts: list[AdasEvent] = Field(default_factory=list)
    speech_prompt: Optional[str] = None
    sound_alert: Optional[str] = None  # None, "chime", "alarm_critical"
    should_record_violation: bool = False
    violation_type: Optional[str] = None
    violation_severity: Optional[str] = None
    should_save_evidence: bool = False
    ui_theme: Literal["normal", "caution", "warning", "critical"] = "normal"
