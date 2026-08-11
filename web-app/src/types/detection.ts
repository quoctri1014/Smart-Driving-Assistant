export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface VehicleDetection {
  id: number;
  bbox: BoundingBox;
  class: string;
  zone?: string;
}

export interface PlateDetection {
  plate_text: string;
  bbox: BoundingBox;
  confidence?: number;
}

export interface HelmetViolation {
  track_id: number;
  plate_text?: string;
  bbox: BoundingBox;
}

export interface SpeedAdvice {
  current_speed?: number;
  recommended_speed?: number;
  reason: string;
}

export interface CollisionWarning {
  level: 'none' | 'warning' | 'danger';
  distance_estimate?: number;
}

export interface TrafficSign {
  sign_type?: string;
  speed_limit?: number;
}

export interface DetectionResult {
  frame_id: number;
  timestamp: number;
  vehicles: VehicleDetection[];
  plates: PlateDetection[];
  helmet_violations: HelmetViolation[];
  collision_warning?: CollisionWarning;
  speed_advice?: SpeedAdvice;
  traffic_signs: TrafficSign[];
  processing_time_ms: number;
}

export interface DrowsinessStatus {
  is_drowsy: boolean;
  ear_value: number;
  yawn_count: number;
  alert_level: string;
}

export interface SeatbeltStatus {
  seatbelt_on: boolean;
  confidence: number;
}

export interface DrivingTimeStatus {
  continuous_minutes: number;
  should_rest: boolean;
  message: string;
}

export interface DriverMonitorResult {
  frame_id: number;
  timestamp: number;
  drowsiness: DrowsinessStatus;
  seatbelt: SeatbeltStatus;
  driving_time: DrivingTimeStatus;
  processing_time_ms: number;
}
