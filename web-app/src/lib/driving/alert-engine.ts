import { DetectionResult, DriverMonitorResult } from '../../types/detection';

export type AlertPriority = 
  | 'COLLISION_DANGER'
  | 'DROWSINESS'
  | 'SPEED_DANGER'
  | 'COLLISION_CAUTION'
  | 'SPEED_WARNING'
  | 'SEATBELT_WARNING'
  | 'REST_REMINDER'
  | 'TRAFFIC_SIGN'
  | 'NORMAL'
  | 'UNAVAILABLE';

export interface DrivingUIState {
  priority: AlertPriority;
  message: string;
  recommendedSpeed: number | null;
  speedLimit: number | null;
  currentSpeed: number | null;
  safeDistance: number | null;
}

export interface DeriveDrivingUIStateOptions {
  sourceMode?: 'video' | 'webcam' | 'image';
  currentSpeed?: number | null;
  speedLimit?: number | null;
  safeDistance?: number | null;
  collisionLevel?: 'danger' | 'warning' | 'none';
}

export function deriveDrivingUIState(
  roadResult: DetectionResult | null,
  driverResult: DriverMonitorResult | null,
  roadStale: boolean,
  driverStale: boolean,
  options?: DeriveDrivingUIStateOptions
): DrivingUIState {
  
  const road = roadStale ? null : roadResult;
  const isImageMode = options?.sourceMode === 'image';

  // 1. Phân định giới hạn tốc độ pháp lý (Legal Speed Limit)
  // Ưu tiên: biển báo P.127 nhận diện được -> tùy chọn ngoài -> mặc định đô thị 50 km/h (TT 31/2019/TT-BGTVT)
  const detectedSignLimit = road?.traffic_signs?.find((s) => s.speed_limit != null)?.speed_limit ?? null;
  const legalLimit: number | null = isImageMode
    ? (options?.speedLimit ?? detectedSignLimit)
    : (options?.speedLimit ?? detectedSignLimit ?? 50);

  // 2. Vận tốc xe chủ hiện tại (Current Speed)
  // Trong chế độ ảnh tĩnh: không có vận tốc chuyển động (null)
  const currentSpeed: number | null = isImageMode
    ? null
    : (options?.currentSpeed !== undefined
        ? options.currentSpeed
        : (road?.speed_advice?.current_speed ?? null));

  // 3. Tốc độ khuyến nghị an toàn AI (Safety Advisory Speed theo thời tiết/mật độ đông)
  const recommendedSpeed: number | null = isImageMode
    ? null
    : (road?.speed_advice?.recommended_speed ?? legalLimit);

  // 4. Cự ly an toàn & mức độ cảnh báo va chạm
  const collisionLevel = options?.collisionLevel ?? road?.collision_warning?.level ?? 'none';
  const collisionDist = options?.safeDistance ?? road?.collision_warning?.recommended_distance_m ?? null;

  // 5. Kiểm tra vi phạm tốc độ theo Nghị định 100/2019/NĐ-CP & Nghị định 123/2021/NĐ-CP:
  // - Dung sai cho phép: <= 5 km/h không xử phạt vi phạm
  // - Quá tốc độ từ 5 đến 20 km/h: SPEED_WARNING (Phạt tiền)
  // - Quá tốc độ trên 20 km/h: SPEED_DANGER (Nguy hiểm nghiêm trọng, tước GPLX)
  const hasSpeedMetric = currentSpeed != null && legalLimit != null && !isImageMode;
  const speedDiff = hasSpeedMetric ? currentSpeed - legalLimit : 0;
  const isSpeedDanger = hasSpeedMetric && speedDiff > 20;
  const isSpeedWarning = hasSpeedMetric && speedDiff > 5 && !isSpeedDanger;

  // Nếu xe không quá giới hạn pháp lý nhưng vượt quá khuyến nghị an toàn do mật độ đông/mưa
  const isDensityAdvisory =
    hasSpeedMetric &&
    !isSpeedWarning &&
    !isSpeedDanger &&
    recommendedSpeed != null &&
    legalLimit != null &&
    recommendedSpeed < legalLimit &&
    currentSpeed > recommendedSpeed + 3;

  // 6. Trạng thái người lái (DMS)
  const closedDuration = driverResult?.drowsiness?.closed_duration_s ?? 0;
  const eyeState = driverResult?.drowsiness?.eye_state;
  const isClosedCritical = !driverStale && (eyeState === 'CLOSED_CRITICAL' || closedDuration >= 5.0);
  const isClosedWarn = !driverStale && (eyeState === 'CLOSED_WARN' || closedDuration >= 2.0);
  const isDrowsy = !driverStale && (driverResult?.drowsiness?.is_drowsy || isClosedCritical);
  const seatbeltOff = !driverStale && driverResult?.seatbelt?.seatbelt_on === false;
  const rest = !driverStale ? driverResult?.driving_time : null;

  // ── PHÂN CẤP ƯU TIÊN CẢNH BÁO (HIERARCHY) ──

  // ƯU TIÊN 1: NGUY CƠ VA CHẠM PHÍA TRƯỚC KHẨN CẤP
  if (collisionLevel === 'danger') {
    return {
      priority: 'COLLISION_DANGER',
      message: 'NGUY CƠ VA CHẠM PHÍA TRƯỚC - HÃY PHANH NGAY!',
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist,
    };
  }

  // ƯU TIÊN 2: TÀI XẾ NHẮM MẮT NGUY HIỂM (>= 5s HOẶC NGỦ GẬT)
  if (isClosedCritical || (isDrowsy && closedDuration >= 5.0)) {
    return {
      priority: 'DROWSINESS',
      message: driverResult?.speech_prompt || `CẢNH BÁO NGUY HIỂM: TÀI XẾ NHẮM MẮT QUÁ 5 GIÂY (${closedDuration.toFixed(1)}s)!`,
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist,
    };
  }

  // ƯU TIÊN 3: VƯỢT QUÁ TỐC ĐỘ GIỚI HẠN MỨC NGUY HIỂM (> 20 km/h)
  if (isSpeedDanger) {
    return {
      priority: 'SPEED_DANGER',
      message: `NGUY HIỂM: Vận tốc ${Math.round(currentSpeed!)} km/h vượt giới hạn +${Math.round(speedDiff)} km/h (${legalLimit} km/h) - Hãy giảm ga ngay!`,
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist,
    };
  }

  // ƯU TIÊN 4: TÀI XẾ CÓ DẤU HIỆU BUỒN NGỦ / CHỚM NHẮM MẮT (>= 2s)
  if (isClosedWarn || isDrowsy) {
    return {
      priority: 'DROWSINESS',
      message: `CẢNH BÁO: TÀI XẾ ĐANG NHẮM MẮT (${closedDuration.toFixed(1)}s / 5s) - HÃY TẬP TRUNG!`,
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist,
    };
  }

  // ƯU TIÊN 5: KHOẢNG CÁCH XE TRƯỚC CẬN AN TOÀN (CẢNH BÁO CỰ LY)
  if (collisionLevel === 'warning') {
    return {
      priority: 'COLLISION_CAUTION',
      message: 'Cảnh báo: Khoảng cách xe trước cận an toàn, giữ cự ly',
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist,
    };
  }

  // ƯU TIÊN 6: VƯỢT QUÁ TỐC ĐỘ GIỚI HẠN (5 - 20 km/h)
  if (isSpeedWarning) {
    return {
      priority: 'SPEED_WARNING',
      message: `Cảnh báo quá tốc độ: ${Math.round(currentSpeed!)} km/h / Giới hạn ${legalLimit} km/h (+${Math.round(speedDiff)} km/h)`,
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist,
    };
  }

  // ƯU TIÊN 7: LƯU Ý VẬN HÀNH DO MẬT ĐỘ GIAO THÔNG ĐÔNG HOẶC THỜI TIẾT
  if (isDensityAdvisory) {
    return {
      priority: 'COLLISION_CAUTION',
      message: `Mật độ phương tiện cao: Đề xuất duy trì dưới ${Math.round(recommendedSpeed!)} km/h để giữ cự ly an toàn`,
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist,
    };
  }

  // ƯU TIÊN 8: NHẮC NHỞ NGHỈ NGƠI SAU 4H LÁI XE
  if (rest?.should_rest || rest?.alert_level === 'reminder') {
    return {
      priority: 'REST_REMINDER',
      message: rest.message || 'Yêu cầu dừng xe nghỉ ngơi sau 4h lái liên tục',
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist,
    };
  }

  // ƯU TIÊN 9: CHƯA CÀI DÂY AN TOÀN
  if (seatbeltOff) {
    return {
      priority: 'SEATBELT_WARNING',
      message: 'Cảnh báo: Tài xế chưa thắt dây an toàn',
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist,
    };
  }

  if (!road) {
    return { 
      priority: 'NORMAL', 
      message: driverResult?.drowsiness ? 'Hệ thống DMS đang giám sát buồng lái - Tài xế tỉnh táo' : 'Hệ thống sẵn sàng phân tích an toàn', 
      recommendedSpeed: null, 
      speedLimit: legalLimit,
      currentSpeed: null,
      safeDistance: null 
    };
  }

  // ƯU TIÊN 10: THÔNG TIN BIỂN BÁO GIAO THÔNG
  if (road.traffic_signs && road.traffic_signs.length > 0) {
    const sign = road.traffic_signs[0];
    const signDesc = sign.speed_limit
      ? `Biển giới hạn tốc độ: ${sign.speed_limit} km/h (QCVN 41:2019)`
      : (sign.sign_type ? `Biển báo nhận diện: ${sign.sign_type}` : 'Nhận diện biển báo giao thông');
    return {
      priority: 'TRAFFIC_SIGN',
      message: signDesc,
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist,
    };
  }

  // ƯU TIÊN 11: TRẠNG THÁI HÀNH TRÌNH BÌNH THƯỜNG / AN TOÀN
  return {
    priority: 'NORMAL',
    message: 'Hệ thống AI đang quét làn đường & khoảng cách - Hành trình an toàn',
    recommendedSpeed,
    speedLimit: legalLimit,
    currentSpeed,
    safeDistance: collisionDist,
  };
}
