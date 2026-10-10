/**
 * Signal UI Mobile: Trip State Machine for Fleet Drivers
 * States:
 * IDLE -> PREPARING (Pre-trip checks) -> READY -> ACTIVE (Driving) -> ENDING -> COMPLETED
 * Includes App Recovery State handling for unexpected restarts.
 */

export type TripState = 'IDLE' | 'PREPARING' | 'READY' | 'ACTIVE' | 'ENDING' | 'COMPLETED';

export interface PreTripChecklist {
  roadCamera: boolean;
  cabinCamera: boolean;
  gpsLocation: boolean;
  network4G: boolean;
  dmsStatus: boolean;
  vehicleAssigned: boolean;
}

export interface ActiveTripSession {
  sessionId: number;
  vehicleId: number;
  vehiclePlate: string;
  driverId: number;
  driverName: string;
  startedAt: string;
  status: 'active' | 'paused' | 'completed';
}

export class TripStateMachine {
  private state: TripState = 'IDLE';
  private checks: PreTripChecklist = {
    roadCamera: false,
    cabinCamera: false,
    gpsLocation: false,
    network4G: false,
    dmsStatus: false,
    vehicleAssigned: false,
  };
  private session: ActiveTripSession | null = null;

  constructor(initialState: TripState = 'IDLE') {
    this.state = initialState;
  }

  getState(): TripState {
    return this.state;
  }

  getChecklist(): PreTripChecklist {
    return { ...this.checks };
  }

  getSession(): ActiveTripSession | null {
    return this.session;
  }

  updateChecklist(partial: Partial<PreTripChecklist>) {
    this.checks = { ...this.checks, ...partial };
  }

  /**
   * Mandatory (Blocking) Checks:
   * 1. Road Camera
   * 2. GPS Location
   * 3. Vehicle Assigned
   *
   * Non-Blocking (Advisory):
   * 4. Cabin Camera / DMS (warns if offline but allows trip start if policy permits)
   * 5. Network (allows offline caching)
   */
  canStartTrip(): { allowed: boolean; reason?: string } {
    if (!this.checks.vehicleAssigned) {
      return { allowed: false, reason: 'Chưa chọn hoặc chưa được phân công phương tiện' };
    }
    if (!this.checks.gpsLocation) {
      return { allowed: false, reason: 'GPS chưa được kích hoạt hoặc không có tín hiệu định vị' };
    }
    if (!this.checks.roadCamera) {
      return { allowed: false, reason: 'Camera trước (Road Camera) chưa được kết nối hoặc bị lỗi' };
    }
    return { allowed: true };
  }

  transitionTo(nextState: TripState, payload?: { session?: ActiveTripSession }): boolean {
    switch (this.state) {
      case 'IDLE':
        if (nextState === 'PREPARING') {
          this.state = 'PREPARING';
          return true;
        }
        if (nextState === 'ACTIVE' && payload?.session) {
          // Recovery flow directly back to ACTIVE
          this.session = payload.session;
          this.state = 'ACTIVE';
          return true;
        }
        return false;

      case 'PREPARING':
        if (nextState === 'READY') {
          const { allowed } = this.canStartTrip();
          if (allowed) {
            this.state = 'READY';
            return true;
          }
          return false;
        }
        if (nextState === 'IDLE') {
          this.state = 'IDLE';
          return true;
        }
        return false;

      case 'READY':
        if (nextState === 'ACTIVE') {
          if (payload?.session) {
            this.session = payload.session;
          }
          this.state = 'ACTIVE';
          return true;
        }
        if (nextState === 'PREPARING') {
          this.state = 'PREPARING';
          return true;
        }
        return false;

      case 'ACTIVE':
        if (nextState === 'ENDING') {
          this.state = 'ENDING';
          return true;
        }
        return false;

      case 'ENDING':
        if (nextState === 'COMPLETED') {
          this.state = 'COMPLETED';
          return true;
        }
        if (nextState === 'ACTIVE') {
          // Resume if user canceled ending
          this.state = 'ACTIVE';
          return true;
        }
        return false;

      case 'COMPLETED':
        if (nextState === 'IDLE') {
          this.state = 'IDLE';
          this.session = null;
          this.checks = {
            roadCamera: false,
            cabinCamera: false,
            gpsLocation: false,
            network4G: false,
            dmsStatus: false,
            vehicleAssigned: false,
          };
          return true;
        }
        return false;

      default:
        return false;
    }
  }
}

export type TripReconciliationAction =
  | 'RESUME'
  | 'RECONCILE_BACKEND_WIN'
  | 'CLEAR_STALE'
  | 'RECOVER_ACTIVE'
  | 'IDLE';

export interface TripReconciliationResult {
  action: TripReconciliationAction;
  targetState: TripState;
  session: ActiveTripSession | null;
  message: string;
}

export function reconcileActiveTripState(
  localSession: ActiveTripSession | null,
  backendActiveTrip: { has_active_trip: boolean; session?: any } | null
): TripReconciliationResult {
  const backendHasActive = backendActiveTrip?.has_active_trip && !!backendActiveTrip?.session;
  const backendSess = backendActiveTrip?.session;

  // Case A: local ACTIVE + backend same ACTIVE trip -> RESUME
  if (localSession && backendHasActive && localSession.sessionId === backendSess.id) {
    return {
      action: 'RESUME',
      targetState: 'ACTIVE',
      session: {
        sessionId: backendSess.id,
        vehicleId: backendSess.vehicle_id || localSession.vehicleId,
        vehiclePlate: localSession.vehiclePlate,
        driverId: backendSess.driver_id || localSession.driverId,
        driverName: localSession.driverName,
        startedAt: backendSess.start_time || localSession.startedAt,
        status: 'active'
      },
      message: 'Tiếp tục hành trình đang hoạt động'
    };
  }

  // Case B: local ACTIVE trip A + backend ACTIVE trip B -> Backend wins
  if (localSession && backendHasActive && localSession.sessionId !== backendSess.id) {
    return {
      action: 'RECONCILE_BACKEND_WIN',
      targetState: 'ACTIVE',
      session: {
        sessionId: backendSess.id,
        vehicleId: backendSess.vehicle_id || 0,
        vehiclePlate: 'Xe Doanh Nghiệp',
        driverId: backendSess.driver_id || 0,
        driverName: 'Tài Xế',
        startedAt: backendSess.start_time,
        status: 'active'
      },
      message: 'Đồng bộ lại chuyến đi mới nhất từ máy chủ'
    };
  }

  // Case C: local ACTIVE + backend no active trip -> Clear stale
  if (localSession && !backendHasActive) {
    return {
      action: 'CLEAR_STALE',
      targetState: 'IDLE',
      session: null,
      message: 'Chuyến đi trước đã kết thúc trên máy chủ'
    };
  }

  // Case D: local empty + backend ACTIVE -> Recover
  if (!localSession && backendHasActive) {
    return {
      action: 'RECOVER_ACTIVE',
      targetState: 'ACTIVE',
      session: {
        sessionId: backendSess.id,
        vehicleId: backendSess.vehicle_id || 0,
        vehiclePlate: 'Xe Doanh Nghiệp',
        driverId: backendSess.driver_id || 0,
        driverName: 'Tài Xế',
        startedAt: backendSess.start_time,
        status: 'active'
      },
      message: 'Khôi phục chuyến đi đang diễn ra'
    };
  }

  // Default: both empty -> IDLE
  return {
    action: 'IDLE',
    targetState: 'IDLE',
    session: null,
    message: 'Sẵn sàng bắt đầu chuyến đi mới'
  };
}
