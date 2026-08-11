from pydantic import BaseModel, Field
from typing import List, Optional

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class VehicleDetection(BaseModel):
    id: int
    bbox: BoundingBox
    class_name: str = Field(alias="class")
    zone: Optional[str] = None
    
    class Config:
        populate_by_name = True

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

class TrafficSign(BaseModel):
    sign_type: Optional[str] = None
    speed_limit: Optional[float] = None

class DetectionResult(BaseModel):
    frame_id: int
    timestamp: float
    vehicles: List[VehicleDetection] = []
    plates: List[PlateDetection] = []
    helmet_violations: List[HelmetViolation] = []
    collision_warning: Optional[CollisionWarning] = None
    speed_advice: Optional[SpeedAdvice] = None
    traffic_signs: List[TrafficSign] = []
    processing_time_ms: float

class DrowsinessStatus(BaseModel):
    is_drowsy: bool
    ear_value: float
    yawn_count: int
    alert_level: str

class SeatbeltStatus(BaseModel):
    seatbelt_on: bool
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
