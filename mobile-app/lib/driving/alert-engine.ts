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
  const detectedSignLimit = road?.traffic_signs?.find((s) => s.speed_limit != null)?.speed_limit ?? null;
  const legalLimit: number | null = isImageMode
    ? (options?.speedLimit ?? detectedSignLimit)
    : (options?.speedLimit ?? detectedSignLimit ?? 50);

  // 2. Vận tốc xe chủ hiện tại (Current Speed)
  const currentSpeed: number | null = isImageMode
    ? null
    : (options?.currentSpeed !== undefined
        ? options.currentSpeed
        : (road?.speed_advice?.current_speed ?? null));

  // 3. Tốc độ khuyến nghị an toàn AI (Safety Advisory Speed theo thời tiết/mật độ)
  const recommendedSpeed: number | null = isImageMode
    ? null
    : (road?.speed_advice?.recommended_speed ?? legalLimit);

  // 4. Cự ly an toàn & mức độ va chạm
  const collisionLevel = options?.collisionLevel ?? road?.collision_warning?.level ?? 'none';
  const collisionDist = options?.safeDistance ?? road?.collision_warning?.recommended_distance_m ?? null;

  // 5. Kiểm tra vi phạm tốc độ theo NĐ 100/2019/NĐ-CP:
  const hasSpeedMetric = currentSpeed != null && legalLimit != null && !isImageMode;
  const speedDiff = hasSpeedMetric ? currentSpeed - legalLimit : 0;
  const isSpeedDanger = hasSpeedMetric && speedDiff > 20;
  const isSpeedWarning = hasSpeedMetric && speedDiff > 5 && !isSpeedDanger;

  // Khuyến nghị mật độ đông / thời tiết
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

  // ── PHÂN CẤP ƯU TIÊN CẢNH BÁO ──

  // 1. COLLISION_DANGER
  if (collisionLevel === 'danger') {
    return {
      priority: 'COLLISION_DANGER',
      message: 'NGUY CƠ VA CHẠM PHÍA TRƯỚC - HÃY PHANH NGAY!',
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist
    };
  }

  // 2. DROWSINESS CRITICAL
  if (isClosedCritical || (isDrowsy && closedDuration >= 5.0)) {
    return {
      priority: 'DROWSINESS',
      message: driverResult?.speech_prompt || `CẢNH BÁO NGUY HIỂM: TÀI XẾ NHẮM MẮT QUÁ 5 GIÂY (${closedDuration.toFixed(1)}s)!`,
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist
    };
  }

  // 3. SPEED_DANGER
  if (isSpeedDanger) {
    return {
      priority: 'SPEED_DANGER',
      message: `NGUY HIỂM: Vận tốc ${Math.round(currentSpeed!)} km/h vượt giới hạn +${Math.round(speedDiff)} km/h (${legalLimit} km/h) - Giảm ga ngay!`,
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist,
    };
  }

  // 4. DROWSINESS WARNING
  if (isClosedWarn || isDrowsy) {
    return {
      priority: 'DROWSINESS',
      message: `CẢNH BÁO: TÀI XẾ ĐANG NHẮM MẮT (${closedDuration.toFixed(1)}s / 5s) - HÃY TẬP TRUNG!`,
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist
    };
  }

  // 5. COLLISION_CAUTION
  if (collisionLevel === 'warning') {
    return {
      priority: 'COLLISION_CAUTION',
      message: 'Cảnh báo: Khoảng cách xe trước cận an toàn, giữ cự ly',
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist
    };
  }

  // 6. SPEED_WARNING
  if (isSpeedWarning) {
    return {
      priority: 'SPEED_WARNING',
      message: `Cảnh báo quá tốc độ: ${Math.round(currentSpeed!)} km/h / Giới hạn ${legalLimit} km/h (+${Math.round(speedDiff)} km/h)`,
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist
    };
  }

  // 7. DENSITY ADVISORY
  if (isDensityAdvisory) {
    return {
      priority: 'COLLISION_CAUTION',
      message: `Mật độ phương tiện cao: Đề xuất duy trì dưới ${Math.round(recommendedSpeed!)} km/h để giữ cự ly an toàn`,
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist
    };
  }

  // 8. REST_REMINDER
  if (rest?.should_rest || rest?.alert_level === 'reminder') {
    return {
      priority: 'REST_REMINDER',
      message: rest.message || 'Yêu cầu dừng xe nghỉ ngơi sau 4h lái liên tục',
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist
    };
  }

  // 9. SEATBELT_WARNING
  if (seatbeltOff) {
    return {
      priority: 'SEATBELT_WARNING',
      message: 'Cảnh báo: Tài xế chưa thắt dây an toàn',
      recommendedSpeed,
      speedLimit: legalLimit,
      currentSpeed,
      safeDistance: collisionDist
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

  // 10. TRAFFIC_SIGN
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
      safeDistance: collisionDist
    };
  }

  // 11. NORMAL
  return {
    priority: 'NORMAL',
    message: 'Hệ thống AI đang quét làn đường & khoảng cách - Hành trình an toàn',
    recommendedSpeed,
    speedLimit: legalLimit,
    currentSpeed,
    safeDistance: collisionDist
  };
}
