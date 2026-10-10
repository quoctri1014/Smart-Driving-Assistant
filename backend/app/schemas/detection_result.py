from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class VehicleDetection(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    bbox: BoundingBox
    class_name: str = Field(alias="class")
    zone: Optional[str] = None
    speed_kmh: Optional[float] = None
    plate_text: Optional[str] = None
    plate_status: Optional[str] = None

class PlateDetection(BaseModel):
    plate_text: str
    bbox: BoundingBox
    confidence: Optional[float] = None

class HelmetViolation(BaseModel):
    track_id: int
    plate_text: Optional[str] = None
    bbox: BoundingBox

class SpeedAdvice(BaseModel):
    current_speed: Optional[float] = None
    recommended_speed: Optional[float] = None
    reason: str

class CollisionWarning(BaseModel):
    level: str  # "none", "warning", "danger"
    distance_estimate: Optional[float] = None
    recommended_distance_m: Optional[float] = None
    recommended_speed_kmh: Optional[float] = None

class TrafficSign(BaseModel):
    sign_type: Optional[str] = None
    speed_limit: Optional[float] = None

class DetectionResult(BaseModel):
    frame_width: Optional[int] = None
    frame_height: Optional[int] = None
    frame_id: int
    timestamp: float
    vehicles: List[VehicleDetection] = []
    plates: List[PlateDetection] = []
    helmet_violations: List[HelmetViolation] = []
    collision_warning: Optional[CollisionWarning] = None
    speed_advice: Optional[SpeedAdvice] = None
    traffic_signs: List[TrafficSign] = []
    zone_counts: dict[str, int] = Field(default_factory=dict)
    zone_occupancy: dict[str, int] = Field(default_factory=dict)
    processing_time_ms: float
    speech_prompt: Optional[str] = None
    sound_alert: Optional[str] = None
    decision: Optional[dict] = None
    quality_score: Optional[float] = None
    is_low_quality: bool = False
    system_health: Optional[dict] = None
    fused_telemetry: Optional[dict] = None

class DrowsinessStatus(BaseModel):
    is_drowsy: bool
    ear_value: float
    yawn_count: int
    alert_level: str
    is_calibrated: Optional[bool] = None
    baseline_ear: Optional[float] = None

class SeatbeltStatus(BaseModel):
    seatbelt_on: Optional[bool] = None
    confidence: float

class DrivingTimeStatus(BaseModel):
    continuous_minutes: float
    should_rest: bool
    message: str

class DriverMonitorResult(BaseModel):
    frame_id: int
    timestamp: float
    drowsiness: DrowsinessStatus
    seatbelt: SeatbeltStatus
    driving_time: DrivingTimeStatus
    processing_time_ms: float
    speech_prompt: Optional[str] = None
    sound_alert: Optional[str] = None
    decision: Optional[dict] = None
