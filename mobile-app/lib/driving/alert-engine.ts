import { DetectionResult, DriverMonitorResult } from '../../types/detection';

export type AlertPriority = 
  | 'COLLISION_DANGER'
  | 'DROWSINESS'
  | 'COLLISION_CAUTION'
  | 'SPEED_WARNING'
  | 'SEATBELT_WARNING'
  | 'TRAFFIC_SIGN'
  | 'NORMAL'
  | 'UNAVAILABLE';

export interface DrivingUIState {
  priority: AlertPriority;
  message: string;
  recommendedSpeed: number | null;
  safeDistance: number | null;
}

export function deriveDrivingUIState(
  roadResult: DetectionResult | null,
  driverResult: DriverMonitorResult | null,
  roadStale: boolean,
  driverStale: boolean
): DrivingUIState {
  
  if (roadStale || !roadResult) {
    return {
      priority: 'UNAVAILABLE',
      message: 'AI Data Unavailable / Reconnecting...',
      recommendedSpeed: null,
      safeDistance: null
    };
  }

  // Helper variables from results
  const collisionLevel = roadResult.collision_warning?.level || 'none';
  const collisionDist = roadResult.collision_warning?.distance_estimate || null;
  const recommendedSpeed = roadResult.speed_advice?.recommended_speed || null;
  const isSpeeding = roadResult.speed_advice?.reason === 'speed_limit_exceeded' 
    || roadResult.speed_advice?.reason === 'too_fast_for_conditions';
    
  const isDrowsy = !driverStale && driverResult?.drowsiness?.is_drowsy;
  const seatbeltOff = !driverStale && driverResult?.seatbelt && !driverResult.seatbelt.seatbelt_on;

  // 1. COLLISION_DANGER
  if (collisionLevel === 'danger') {
    return {
      priority: 'COLLISION_DANGER',
      message: 'BRAKE NOW! COLLISION RISK',
      recommendedSpeed,
      safeDistance: collisionDist
    };
  }

  // 2. DROWSINESS
  if (isDrowsy) {
    return {
      priority: 'DROWSINESS',
      message: 'DROWSINESS DETECTED - STAY ATTENTIVE',
      recommendedSpeed,
      safeDistance: collisionDist
    };
  }

  // 3. COLLISION_CAUTION
  if (collisionLevel === 'warning') {
    return {
      priority: 'COLLISION_CAUTION',
      message: 'Maintain Safe Distance',
      recommendedSpeed,
      safeDistance: collisionDist
    };
  }

  // 4. SPEED_WARNING
  if (isSpeeding) {
    return {
      priority: 'SPEED_WARNING',
      message: 'Reduce Speed',
      recommendedSpeed,
      safeDistance: collisionDist
    };
  }

  // 5. SEATBELT_WARNING
  if (seatbeltOff) {
    return {
      priority: 'SEATBELT_WARNING',
      message: 'Please fasten seatbelt',
      recommendedSpeed,
      safeDistance: collisionDist
    };
  }

  // 6. TRAFFIC_SIGN
  if (roadResult.traffic_signs && roadResult.traffic_signs.length > 0) {
    const sign = roadResult.traffic_signs[0];
    return {
      priority: 'TRAFFIC_SIGN',
      message: sign.sign_type ? `Detected: ${sign.sign_type}` : 'Traffic Sign Detected',
      recommendedSpeed,
      safeDistance: collisionDist
    };
  }

  // 7. NORMAL
  return {
    priority: 'NORMAL',
    message: 'Safe Driving',
    recommendedSpeed,
    safeDistance: collisionDist
  };
}
