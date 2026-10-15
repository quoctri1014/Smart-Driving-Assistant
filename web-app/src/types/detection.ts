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
  class_name?: string;
  zone?: string;
  speed_kmh?: number | null;
  distance_m?: number | null;
  distance_status?: string | null;
  direction?: 'IN' | 'OUT' | 'IDLE';
  thumbnail?: string;
  plate_text?: string | null;
  plate_status?: string | null;
  ttc?: number | null;
  rel_speed_kmh?: number | null;
  approach_state?: string | null;
  approach_desc?: string | null;
}

export interface LineCrossingData {
  line_y: number;
  in_count: number;
  out_count: number;
  total_count: number;
  in_by_class: Record<string, number>;
  out_by_class: Record<string, number>;
  recent_crossings?: Array<{
    id: number;
    class: string;
    direction: 'IN' | 'OUT';
    speed_kmh: number;
    timestamp: number;
  }>;
}

export interface PlateDetection {
  plate_text: string;
  bbox: BoundingBox;
  confidence?: number;
  thumbnail?: string;
  count?: number;
  last_seen?: number;
  background_color?: string;
  province?: string;
  vehicle_type?: string;
  status?: string;
}

export interface HelmetViolation {
  track_id: number;
  plate_text?: string;
  bbox: BoundingBox;
  thumbnail?: string;
  count?: number;
  last_seen?: number;
}

export interface SpeedAdvice {
  current_speed?: number;
  recommended_speed?: number;
  reason: string;
}

export interface CollisionWarning {
  level: 'none' | 'warning' | 'danger';
  distance_estimate?: number;
  recommended_distance_m?: number | null;
  recommended_speed_kmh?: number | null;
}

export interface TrafficSign {
  sign_type?: string;
  name?: string;
  category?: string;
  speed_limit?: number | null;
  confidence?: number;
  bbox?: BoundingBox;
  thumbnail?: string;
  count?: number;
  last_seen?: number;
  action_required?: string;
  time_window?: string | null;
  penalty?: string; // Mức xử phạt vi phạm theo Nghị định 100/2019/NĐ-CP & 123/2021/NĐ-CP
}

export interface DetectionResult {
  frame_width?: number | null;
  frame_height?: number | null;
  frame_id: number;
  timestamp: number;
  vehicles: VehicleDetection[];
  plates: PlateDetection[];
  helmet_violations: HelmetViolation[];
  collision_warning?: CollisionWarning;
  speed_advice?: SpeedAdvice;
  traffic_signs: TrafficSign[];
  line_crossings?: LineCrossingData | null;
  processing_time_ms: number;
  speech_prompt?: string | null;
  sound_alert?: string | null;
  decision?: Record<string, unknown> | null;
}

export interface DrowsinessStatus {
  is_drowsy: boolean;
  available?: boolean;
  face_detected?: boolean;
  ear_value: number;
  yawn_count: number;
  alert_level: string;
  closed_duration_s?: number;
  eye_state?: string;
  events?: Array<Record<string, unknown>>;
}

export interface SeatbeltStatus {
  seatbelt_on: boolean | null;
  mode?: string;
  confidence: number;
}

export interface DrivingTimeStatus {
  continuous_minutes: number;
  alert_level?: string;
  is_resting?: boolean;
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
  combined_alert_level?: string;
  speech_prompt?: string | null;
  sound_alert?: string | null;
}

export function sanitizeVietnamesePlate(p: string): string {
  if (!p) return p;
  let clean = p.toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (clean.length >= 4 && clean.slice(2, 4) === 'NM') {
    clean = clean.slice(0, 2) + 'NN' + clean.slice(4);
  }

  // 0. Biển quân đội 6 ký tự (KT-55-72, TC-33-86)
  if (clean.length === 6 && /^[A-Z]{2}\d{4}$/.test(clean)) {
    return `${clean.slice(0, 2)}-${clean.slice(2, 4)}-${clean.slice(4)}`;
  }

  // Sửa lỗi OCR: trên biển ô tô 1 dòng dài (7 hoặc 8 ký tự), chữ 'A' hay bị đọc thành 'L' hoặc '4'
  if ((clean.length === 7 || clean.length === 8) && clean.length >= 3 && /^\d+$/.test(clean.slice(3))) {
    if (clean[2] === 'L' || clean[2] === '4') {
      clean = clean.slice(0, 2) + 'A' + clean.slice(3);
    }
  }

  // 1. Biển ngoại giao / quốc tế / nước ngoài 5 số (80-QT 546-42, 29-NN 691-33)
  if (clean.length === 9 && /^\d{2}(NN|NG|QT|CV)\d{5}$/.test(clean)) {
    return `${clean.slice(0, 2)}-${clean.slice(2, 4)} ${clean.slice(4, 7)}-${clean.slice(7)}`;
  }

  // 2. Ô tô 5 số: 51A-010.88, 68A-000.45
  if (clean.length === 8 && /^\d{2}[A-Z]\d{5}$/.test(clean)) {
    return `${clean.slice(0, 2)}${clean[2]}-${clean.slice(3, 6)}.${clean.slice(6)}`;
  }

  // 3. Ô tô 4 số: 29A-1234
  if (clean.length === 7 && /^\d{2}[A-Z]\d{4}$/.test(clean)) {
    return `${clean.slice(0, 2)}${clean[2]}-${clean.slice(3)}`;
  }

  // 4. Biển 2 chữ cái 4 số (xe máy dưới 50cc hoặc liên doanh: 29-AB 0014, 61-LD 4393)
  if (clean.length === 8 && /^\d{2}[A-Z]{2}\d{4}$/.test(clean)) {
    return `${clean.slice(0, 2)}-${clean.slice(2, 4)} ${clean.slice(4)}`;
  }

  // 5. Xe máy 4 số truyền thống (30-Y9 6850, 29-B1 1234)
  if (clean.length === 8 && /^\d{2}[A-Z][0-9A-Z]\d{4}$/.test(clean)) {
    return `${clean.slice(0, 2)}-${clean.slice(2, 4)} ${clean.slice(4)}`;
  }

  // 6. Xe máy / vuông 5 số: 15-C1 010.82, 29-B1 123.45, 29-AB 123.45
  if (clean.length === 9 && /^\d{2}[A-Z][0-9A-Z]\d{5}$/.test(clean)) {
    return `${clean.slice(0, 2)}-${clean.slice(2, 4)} ${clean.slice(4, 7)}.${clean.slice(7)}`;
  }

  return p;
}

export function isValidConfirmedPlate(p?: string | null): boolean {
  if (!p) return false;
  if (
    p.includes('Đang') ||
    p.includes('Biển số') ||
    p.includes('BIEN_SO') ||
    p.includes('quét') ||
    p.includes('nhận dạng') ||
    p.includes('đọc')
  ) {
    return false;
  }
  const clean = p.toUpperCase().replace(/[^A-Z0-9]/g, '');

  // Biển quân đội 6 ký tự: KT-55-72, TC-33-86
  if (clean.length === 6 && /^[A-Z]{2}\d{4}$/.test(clean)) {
    return true;
  }

  // Chiều dài biển số xe Việt Nam chuẩn: 7 đến 9 ký tự
  if (clean.length < 7 || clean.length > 9) return false;
  // 2 ký tự đầu bắt buộc là mã tỉnh 2 chữ số (11 đến 99, kể cả 80 - TW/Cục CSGT)
  if (!/^\d{2}/.test(clean)) return false;
  // Ký tự thứ 3 bắt buộc là chữ cái seri
  if (!/^\d{2}[A-Z]/.test(clean)) return false;
  // Loại trừ số điện thoại taxi lặp nhóm (ví dụ 38272727, 272727, 383838)
  if (/^(\d{2})\1{2,}/.test(clean)) return false;
  return true;
}
