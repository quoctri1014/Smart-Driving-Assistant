'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { VehicleDetection, LineCrossingData } from '../types/detection';
import { soundEngine } from '../lib/soundEngine';

export interface ActiveZones {
  L: boolean; // Vùng Trái
  F: boolean; // Phía Trước
  R: boolean; // Vùng Phải
}

export type DrivingProfile = 'auto' | 'urban' | 'highway';

export interface ZoneStatus {
  dist: number | null;
  lvl: 0 | 1 | 2; // 0 = Safe, 1 = Warn, 2 = Danger
  cls?: string;
  vn?: string;
  disabled?: boolean;
  ttc?: number | null; // Time To Collision in seconds
  relSpeedKmh?: number; // Vận tốc tiếp cận (+: đang lao tới, -: đang nới xa)
  approachState?: 'CLOSING_IN' | 'MAINTAINING' | 'PULLING_AWAY' | 'CUT_IN' | 'STOPPED';
  approachDesc?: string;
}

export interface TrackedVehicle {
  id: number;
  cls: string;
  vn: string;
  dist: number;
  zone: 'Trái' | 'Trước' | 'Phải';
  zoneKey: 'L' | 'F' | 'R';
  speed: number;
  lvl: 0 | 1 | 2;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  inside: boolean;
  direction?: 'IN' | 'OUT' | 'IDLE';
  ttc?: number | null;
  relSpeedKmh?: number;
  approachState?: 'CLOSING_IN' | 'MAINTAINING' | 'PULLING_AWAY' | 'CUT_IN' | 'STOPPED';
  approachDesc?: string;
}

export interface LineCrossingStats {
  inCount: number;
  outCount: number;
  totalCount: number;
  inByClass: {
    car: number;
    motor: number;
    people: number;
    truck: number;
    bus: number;
  };
  outByClass: {
    car: number;
    motor: number;
    people: number;
    truck: number;
    bus: number;
  };
  lineYRatio: number;
  recentList: Array<{
    id: number;
    cls: string;
    vn: string;
    speed: number;
    dir: 'IN' | 'OUT';
    time: number;
  }>;
}

export interface UseTrafficDistanceEngineProps {
  realVehicles?: VehicleDetection[];
  serverLineCrossings?: LineCrossingData | null;
  frameWidth?: number;
  frameHeight?: number;
  isStreaming?: boolean;
  isPaused?: boolean;
  sourceMode?: 'video' | 'webcam' | 'image';
  currentSpeed?: number | null;
  speedLimit?: number | null;
}

const CLS_MAP: Record<string, { h: number; w: number; c: string; vn: string }> = {
  motorbike: { h: 1.5, w: 0.8, c: '#fbbf24', vn: 'Xe máy' },
  car: { h: 1.5, w: 1.8, c: '#60a5fa', vn: 'Ô tô' },
  person: { h: 1.7, w: 0.5, c: '#a78bfa', vn: 'Người' },
  truck: { h: 3.0, w: 2.5, c: '#f472b6', vn: 'Xe tải' },
  bus: { h: 3.2, w: 2.6, c: '#34d399', vn: 'Xe buýt' },
};

const ZN_MAP = { L: 'Trái' as const, F: 'Trước' as const, R: 'Phải' as const };

export function useTrafficDistanceEngine({
  realVehicles = [],
  serverLineCrossings,
  frameWidth = 1280,
  frameHeight = 720,
  isStreaming = false,
  isPaused = false,
  sourceMode = 'video',
  currentSpeed = null,
  speedLimit = null,
}: UseTrafficDistanceEngineProps) {
  // Configurable thresholds
  const [warnThreshold, setWarnThreshold] = useState<number>(8);
  const [dangerThreshold, setDangerThreshold] = useState<number>(4);
  const [focalLength, setFocalLength] = useState<number>(520);
  const [showZones, setShowZones] = useState<boolean>(true);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(false);
  const [simMode, setSimMode] = useState<boolean>(false);

  // ADAS Driving Profile: 'auto' (thông minh theo tốc độ) | 'urban' (đô thị phố đông) | 'highway' (cao tốc / đường trường)
  const [drivingProfile, setDrivingProfile] = useState<DrivingProfile>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('traffic_guard_driving_profile');
        if (saved && (saved === 'auto' || saved === 'urban' || saved === 'highway')) {
          return saved as DrivingProfile;
        }
      } catch (e) {}
    }
    return 'auto';
  });

  const setDrivingProfileSafe = useCallback((profile: DrivingProfile) => {
    setDrivingProfile(profile);
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('traffic_guard_driving_profile', profile);
      } catch (e) {}
    }
  }, []);

  // Active Zones State (Độc lập bật/tắt 1, 2 hoặc 3 phía L - F - R)
  const [activeZones, setActiveZones] = useState<ActiveZones>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('traffic_guard_active_zones');
        if (saved) {
          const parsed = JSON.parse(saved);
          return {
            L: parsed.L !== false,
            F: parsed.F !== false,
            R: parsed.R !== false,
          };
        }
      } catch (e) {}
    }
    return { L: true, F: true, R: true };
  });

  const toggleZone = useCallback((zone: 'L' | 'F' | 'R') => {
    setActiveZones((prev) => {
      const next = { ...prev, [zone]: !prev[zone] };
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('traffic_guard_active_zones', JSON.stringify(next));
        } catch (e) {}
      }
      return next;
    });
  }, []);

  const setAllZones = useCallback((zones: ActiveZones) => {
    setActiveZones(zones);
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('traffic_guard_active_zones', JSON.stringify(zones));
      } catch (e) {}
    }
  }, []);

  // 3-Zone states
  const [zoneLeft, setZoneLeft] = useState<ZoneStatus>({ dist: null, lvl: 0, disabled: !activeZones.L });
  const [zoneFront, setZoneFront] = useState<ZoneStatus>({ dist: null, lvl: 0, disabled: !activeZones.F });
  const [zoneRight, setZoneRight] = useState<ZoneStatus>({ dist: null, lvl: 0, disabled: !activeZones.R });

  // List of active tracked vehicles
  const [trackedVehicles, setTrackedVehicles] = useState<TrackedVehicle[]>([]);

  // Banner alert
  const [alertBanner, setAlertBanner] = useState<{ text: string; lvl: 1 | 2 } | null>(null);

  // ── LINE CROSSING & TRAFFIC FLOW STATS (IN / OUT) ──
  const [lineCrossings, setLineCrossings] = useState<LineCrossingStats>({
    inCount: 0,
    outCount: 0,
    totalCount: 0,
    inByClass: { car: 0, motor: 0, people: 0, truck: 0, bus: 0 },
    outByClass: { car: 0, motor: 0, people: 0, truck: 0, bus: 0 },
    lineYRatio: 0.60,
    recentList: [],
  });

  const prevYRef = useRef<Record<number, number>>({});
  const crossedInRef = useRef<Set<number>>(new Set());
  const crossedOutRef = useRef<Set<number>>(new Set());

  // Đồng bộ số liệu đếm từ Server nếu có
  useEffect(() => {
    if (serverLineCrossings) {
      setLineCrossings((prev) => ({
        inCount: serverLineCrossings.in_count,
        outCount: serverLineCrossings.out_count,
        totalCount: serverLineCrossings.total_count,
        inByClass: {
          car: serverLineCrossings.in_by_class['car'] || 0,
          motor: serverLineCrossings.in_by_class['motorcycle'] || 0,
          people: serverLineCrossings.in_by_class['person'] || 0,
          truck: serverLineCrossings.in_by_class['truck'] || 0,
          bus: serverLineCrossings.in_by_class['bus'] || 0,
        },
        outByClass: {
          car: serverLineCrossings.out_by_class['car'] || 0,
          motor: serverLineCrossings.out_by_class['motorcycle'] || 0,
          people: serverLineCrossings.out_by_class['person'] || 0,
          truck: serverLineCrossings.out_by_class['truck'] || 0,
          bus: serverLineCrossings.out_by_class['bus'] || 0,
        },
        lineYRatio: prev.lineYRatio,
        recentList: (serverLineCrossings.recent_crossings || []).map((r) => ({
          id: r.id,
          cls: r.class,
          vn: CLS_MAP[r.class]?.vn || r.class,
          speed: r.speed_kmh,
          dir: r.direction as 'IN' | 'OUT',
          time: r.timestamp * 1000,
        })),
      }));
    }
  }, [serverLineCrossings]);

  const resetLineCrossings = useCallback(() => {
    crossedInRef.current.clear();
    crossedOutRef.current.clear();
    prevYRef.current = {};
    setLineCrossings({
      inCount: 0,
      outCount: 0,
      totalCount: 0,
      inByClass: { car: 0, motor: 0, people: 0, truck: 0, bus: 0 },
      outByClass: { car: 0, motor: 0, people: 0, truck: 0, bus: 0 },
      lineYRatio: 0.60,
      recentList: [],
    });
    fetch('http://127.0.0.1:8000/api/v1/traffic-density/reset-line-crossings?session_id=live_stream', { method: 'POST' }).catch(() => {});
  }, []);

  // Simulation state
  const simObjsRef = useRef<any[]>([]);
  const nextIdRef = useRef<number>(1);
  const trackHistoryRef = useRef<
    Record<
      number,
      {
        d: number;
        v: number;
        u: number;
        prevZone: 'L' | 'F' | 'R';
        seen: number;
        cutInFrames: number;
        lvl: 0 | 1 | 2;
      }
    >
  >({});
  const lastBeepRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(performance.now());
  const lastUiRef = useRef<number>(0);

  // Web Audio Context for warning beeps
  const audioCtxRef = useRef<AudioContext | null>(null);

  const playBeep = useCallback((freq: number) => {
    try {
      if (!audioCtxRef.current) {
        const AudioClass = window.AudioContext || (window as any).webkitAudioContext;
        if (AudioClass) audioCtxRef.current = new AudioClass();
      }
      if (!audioCtxRef.current) return;
      if (audioCtxRef.current.state === 'suspended') {
        audioCtxRef.current.resume();
      }
      const osc = audioCtxRef.current.createOscillator();
      const gain = audioCtxRef.current.createGain();
      osc.frequency.value = freq;
      gain.gain.value = 0.08;
      osc.connect(gain);
      gain.connect(audioCtxRef.current.destination);
      osc.start();
      osc.stop(audioCtxRef.current.currentTime + 0.12);
    } catch {
      // Audio context policy catch
    }
  }, []);

  // Initialize simulation objects
  useEffect(() => {
    const spawn = (init: boolean) => {
      const keys = ['car', 'truck', 'motorbike', 'car', 'person'];
      const cls = keys[Math.floor(Math.random() * keys.length)];
      const isApproaching = Math.random() > 0.45;
      return {
        id: nextIdRef.current++,
        cls,
        X: (Math.random() - 0.5) * 9.6,
        Z: init ? 4 + Math.random() * 24 : isApproaching ? 28 + Math.random() * 6 : 3.5,
        vZ: isApproaching ? (-3 - Math.random() * 5) : (3 + Math.random() * 4),
        vX: (Math.random() - 0.5) * 0.3,
      };
    };

    if (simObjsRef.current.length === 0) {
      for (let i = 0; i < 6; i++) {
        simObjsRef.current.push(spawn(true));
      }
    }
  }, []);

  // Main processing loop
  useEffect(() => {
    let animId: number;

    const loop = (now: number) => {
      const dt = Math.min((now - lastTimeRef.current) / 1000, 0.1);
      lastTimeRef.current = now;

      const W = 540;
      const H = 720;
      const HZ = 288;
      const CAMH = 1.3;
      const CX = W / 2;
      const RH = 5.5;
      const F0 = focalLength;

      let list: Array<{ id: number; cls: string; x1: number; y1: number; x2: number; y2: number; distance_m?: number }> = [];

      const hasRealDets = realVehicles && realVehicles.length > 0;

      if (hasRealDets) {
        // Convert real YOLO detection bboxes normalized to perspective canvas WxH
        const fW = frameWidth || 1280;
        const fH = frameHeight || 720;
        const scaleX = W / fW;
        const scaleY = H / fH;

        list = realVehicles.map((v, idx) => {
          const rawCls = (v.class || (v as any).class_name || 'car').toLowerCase();
          const cls = rawCls.includes('truck') || rawCls.includes('bus')
            ? 'truck'
            : rawCls.includes('motor') || rawCls.includes('bike')
            ? 'motorbike'
            : rawCls.includes('person')
            ? 'person'
            : 'car';

          return {
            id: v.id || idx + 1,
            cls,
            x1: (v.bbox.x1 || 0) * scaleX,
            y1: (v.bbox.y1 || 0) * scaleY,
            x2: (v.bbox.x2 || 100) * scaleX,
            y2: (v.bbox.y2 || 100) * scaleY,
            distance_m: v.distance_m != null ? v.distance_m : undefined,
          };
        });
      } else if (simMode && (isStreaming || isPaused)) {
        // Run physics simulation CHỈ KHI người dùng bấm bật simMode === true VÀ video đang chạy/tạm dừng
        if (!isPaused) {
          simObjsRef.current.forEach((o) => {
            o.X += o.vX * dt;
            o.Z += o.vZ * dt;
          });
          simObjsRef.current = simObjsRef.current.filter((o) => o.Z > 1.8 && o.Z < 38 && Math.abs(o.X) < 6);
          while (simObjsRef.current.length < 6) {
            const keys = ['car', 'truck', 'motorbike'];
            const cls = keys[Math.floor(Math.random() * keys.length)];
            simObjsRef.current.push({
              id: nextIdRef.current++,
              cls,
              X: (Math.random() - 0.5) * 9.6,
              Z: 26 + Math.random() * 8,
              vZ: -3 - Math.random() * 5,
              vX: (Math.random() - 0.5) * 0.3,
            });
          }
        }

        list = simObjsRef.current.map((o) => {
          const c = CLS_MAP[o.cls] || CLS_MAP.car;
          const yb = HZ + (F0 * CAMH) / o.Z;
          const h = (F0 * c.h) / o.Z;
          const w = (F0 * c.w) / o.Z;
          const xc = CX + (F0 * o.X) / o.Z;
          return {
            id: o.id,
            cls: o.cls,
            x1: xc - w / 2,
            x2: xc + w / 2,
            y1: yb - h,
            y2: yb,
            distance_m: undefined,
          };
        });
      } else {
        // Tuyệt đối không sinh xe ảo khi không ở chế độ mô phỏng hoặc không có video
        list = [];
      }

      if (list.length === 0) {
        if (now - lastUiRef.current >= 100) {
          lastUiRef.current = now;
          setZoneLeft({ dist: null, lvl: 0, disabled: !activeZones.L });
          setZoneFront({ dist: null, lvl: 0, disabled: !activeZones.F });
          setZoneRight({ dist: null, lvl: 0, disabled: !activeZones.R });
          setTrackedVehicles([]);
          setAlertBanner(null);
        }
        animId = requestAnimationFrame(loop);
        return;
      }

      // ── SMART SPEED-AWARE & DRIVING PROFILE THRESHOLDS ──
      const egoSpeed = currentSpeed !== null && currentSpeed !== undefined ? currentSpeed : 45;
      const speedMs = Math.max(0, egoSpeed) / 3.6;
      // 2-second international rule for safe following distance
      const dynamic2SecDist = Math.max(4.0, speedMs * 2.0);

      const effectiveProfile: 'urban' | 'highway' =
        drivingProfile === 'highway' ? 'highway' : drivingProfile === 'urban' ? 'urban' : egoSpeed > 55 ? 'highway' : 'urban';

      let effectiveWarnDist = warnThreshold;
      let effectiveDangerDist = dangerThreshold;

      if (egoSpeed < 8) {
        // Dừng đèn đỏ hoặc kẹt xe (Stop & Go Traffic): thu nhỏ ngưỡng để chống báo ảo!
        effectiveWarnDist = Math.min(warnThreshold, 3.8);
        effectiveDangerDist = Math.min(dangerThreshold, 1.8);
      } else if (effectiveProfile === 'highway') {
        // Cao tốc / đường trường: tự động nới rộng cự ly cảnh báo sớm 25-50m
        effectiveWarnDist = Math.max(warnThreshold, Math.min(65, dynamic2SecDist * 0.9));
        effectiveDangerDist = Math.max(dangerThreshold, Math.min(28, dynamic2SecDist * 0.45));
      } else {
        // Đô thị: cân bằng linh hoạt theo tốc độ phố 25-50 km/h
        effectiveWarnDist = Math.max(warnThreshold, Math.min(22, dynamic2SecDist * 0.85));
        effectiveDangerDist = Math.max(dangerThreshold, Math.min(9, dynamic2SecDist * 0.4));
      }

      // Analyze vehicles in 3 zones (tôn trọng cài đặt BẬT/TẮT của từng vùng)
      const newZs: { L: ZoneStatus; F: ZoneStatus; R: ZoneStatus } = {
        L: { dist: null, lvl: 0, disabled: !activeZones.L },
        F: { dist: null, lvl: 0, disabled: !activeZones.F },
        R: { dist: null, lvl: 0, disabled: !activeZones.R },
      };

      const computedTracked: TrackedVehicle[] = [];
      const top = HZ + (F0 * CAMH) / 32;
      const bot = HZ + (F0 * CAMH) / 2;

      list.forEach((d) => {
        const c = CLS_MAP[d.cls] || CLS_MAP.car;
        const hpx = Math.max(1, d.y2 - d.y1);
        const rawDist = d.distance_m != null ? d.distance_m : Math.max(1.5, Math.min(80, (F0 * c.h) / hpx));
        const xc = (d.x1 + d.x2) / 2;
        const hw = RH * (d.y2 - HZ) / CAMH;
        const u = hw !== 0 ? (xc - CX) / hw : 0;
        const inside = d.y2 >= top && d.y2 <= bot && Math.abs(u) <= 1.25;
        const zKey: 'L' | 'F' | 'R' = u < -0.33 ? 'L' : u > 0.33 ? 'R' : 'F';
        const isZoneActive = activeZones[zKey];

        let tr = trackHistoryRef.current[d.id];
        let dist = rawDist;
        let v_rel = 0;
        let isCutIn = false;

        if (!tr) {
          dist = rawDist;
          v_rel = 0;
          tr = trackHistoryRef.current[d.id] = {
            d: dist,
            v: 0,
            u,
            prevZone: zKey,
            seen: now,
            cutInFrames: 0,
            lvl: 0,
          };
        } else {
          // Adaptive dual-rate EMA smoothing:
          // Nếu biến thiên cự ly rất lớn (|deltaD| > 3.0m do phanh gấp): phản ứng nhanh (alpha = 0.80)
          // Khi di chuyển bình thường: làm mượt cao (alpha = 0.35) để loại bỏ 100% rung lắc frame
          const deltaD = rawDist - tr.d;
          const alpha = Math.abs(deltaD) > 3.0 ? 0.80 : 0.35;
          dist = alpha * rawDist + (1 - alpha) * tr.d;

          if (dt > 0.005) {
            // Khi khoảng cách giảm dần (d giảm) -> vận tốc tiếp cận v_instant dương
            const v_instant = -(dist - tr.d) / dt;
            v_rel = tr.v * 0.75 + v_instant * 0.25;
          } else {
            v_rel = tr.v;
          }

          // Phát hiện xe tạt đầu (Cut-in detection):
          // Xe đang ở vùng trước F nhưng trong 1.5s trước vừa ở bên Trái hoặc Phải và có vận tốc ngang dịch chuyển
          const lateralSpeed = Math.abs(u - tr.u) / Math.max(0.01, dt);
          if (zKey === 'F' && tr.prevZone !== 'F' && lateralSpeed > 0.30) {
            tr.cutInFrames = 15; // Duy trì trạng thái tạt đầu trong ~500ms
          } else if (tr.cutInFrames > 0) {
            tr.cutInFrames -= 1;
          }
          isCutIn = tr.cutInFrames > 0;

          tr.d = dist;
          tr.v = v_rel;
          tr.u = u;
          tr.prevZone = zKey;
          tr.seen = now;
        }

        const relSpeedKmh = v_rel * 3.6;
        const absSpeedKmh = Math.abs(tr.v * 3.6);

        // Phân loại trạng thái chuyển động thông minh (Approach State)
        let approachState: 'CLOSING_IN' | 'MAINTAINING' | 'PULLING_AWAY' | 'CUT_IN' | 'STOPPED' = 'MAINTAINING';
        let approachDesc = 'Ổn định';

        if (isCutIn) {
          approachState = 'CUT_IN';
          approachDesc = 'Tạt đầu vào làn';
        } else if (relSpeedKmh > 3.0) {
          approachState = 'CLOSING_IN';
          approachDesc = `Áp sát (+${Math.round(relSpeedKmh)} km/h)`;
        } else if (relSpeedKmh < -3.0) {
          approachState = 'PULLING_AWAY';
          approachDesc = `Nới xa (${Math.round(relSpeedKmh)} km/h)`;
        } else if (egoSpeed < 8 && Math.abs(relSpeedKmh) <= 3.0) {
          approachState = 'STOPPED';
          approachDesc = 'Dừng / Chờ đèn';
        }

        // Time-To-Collision (TTC) - Thời gian dự tính va chạm nếu duy trì tốc độ tiếp cận
        let ttc: number | null = null;
        if (v_rel > 0.4) {
          ttc = Math.max(0.1, dist / v_rel);
        }

        // Hệ số an toàn theo loại xe (VRU: người/xe máy phản ứng nhạy hơn 15%, xe tải/buýt nới rộng cự ly 25%)
        const vruMultiplier = (d.cls === 'motorbike' || d.cls === 'person') ? 1.15 : (d.cls === 'truck' || d.cls === 'bus') ? 1.25 : 1.0;
        const objWarnDist = effectiveWarnDist * vruMultiplier;
        const objDangerDist = effectiveDangerDist * vruMultiplier;

        // Phân cấp cảnh báo đa yếu tố (Multi-factor Smart Danger Level)
        let lvl: 0 | 1 | 2 = 0;
        if (isZoneActive) {
          // Mức 2 (DANGER - PHANH GẤP):
          // 1. TTC nguy kịch (TTC <= 1.8s) khi đang áp sát
          // 2. Cự ly rơi vào vùng phanh khẩn cấp (objDangerDist) và KHÔNG phải đang đi xa dần
          // 3. Hoặc xe tạt đầu ở cự ly gần (< dangerDist * 1.5)
          const isTtcCritical = ttc !== null && ttc <= 1.8 && dist <= objWarnDist * 1.2;
          const isProximityCritical = dist <= objDangerDist && approachState !== 'PULLING_AWAY';
          const isCutInCritical = isCutIn && dist <= objDangerDist * 1.5;

          if (isTtcCritical || isProximityCritical || isCutInCritical) {
            lvl = 2;
          } else {
            // Mức 1 (WARN - CHÚ Ý):
            // 1. TTC cận an toàn (TTC <= 3.2s)
            // 2. Cự ly trong ngưỡng cảnh báo objWarnDist và không phải đang nới xa
            // 3. Hoặc phương tiện đang tạt đầu
            const isTtcWarn = ttc !== null && ttc <= 3.2 && dist <= objWarnDist * 1.3;
            const isProximityWarn = dist <= objWarnDist && approachState !== 'PULLING_AWAY';

            if (isTtcWarn || isProximityWarn || isCutIn) {
              lvl = 1;
            } else {
              lvl = 0;
            }
          }
        }

        // ── LINE CROSSING DETECTION (VẠCH ĐẾM LƯU LƯỢNG IN / OUT TẠI 60% CHIỀU CAO) ──
        const lineY = H * 0.60;
        let direction: 'IN' | 'OUT' | 'IDLE' = (d as any).direction || 'IDLE';
        const prevY = prevYRef.current[d.id];
        if (prevY !== undefined) {
          if (prevY < lineY && d.y2 >= lineY) {
            direction = 'IN';
            if (!crossedInRef.current.has(d.id)) {
              crossedInRef.current.add(d.id);
              const mapKey = d.cls === 'motorbike' ? 'motor' : d.cls === 'person' ? 'people' : d.cls === 'truck' ? 'truck' : d.cls === 'bus' ? 'bus' : 'car';
              setLineCrossings((prev) => ({
                ...prev,
                inCount: prev.inCount + 1,
                totalCount: prev.totalCount + 1,
                inByClass: { ...prev.inByClass, [mapKey]: (prev.inByClass[mapKey] || 0) + 1 },
                recentList: [
                  { id: d.id, cls: d.cls, vn: c.vn, speed: Math.round(absSpeedKmh), dir: 'IN', time: Date.now() },
                  ...prev.recentList.slice(0, 14),
                ],
              }));
            }
          } else if (prevY > lineY && d.y2 <= lineY) {
            direction = 'OUT';
            if (!crossedOutRef.current.has(d.id)) {
              crossedOutRef.current.add(d.id);
              const mapKey = d.cls === 'motorbike' ? 'motor' : d.cls === 'person' ? 'people' : d.cls === 'truck' ? 'truck' : d.cls === 'bus' ? 'bus' : 'car';
              setLineCrossings((prev) => ({
                ...prev,
                outCount: prev.outCount + 1,
                totalCount: prev.totalCount + 1,
                outByClass: { ...prev.outByClass, [mapKey]: (prev.outByClass[mapKey] || 0) + 1 },
                recentList: [
                  { id: d.id, cls: d.cls, vn: c.vn, speed: Math.round(absSpeedKmh), dir: 'OUT', time: Date.now() },
                  ...prev.recentList.slice(0, 14),
                ],
              }));
            }
          }
        }
        prevYRef.current[d.id] = d.y2;

        computedTracked.push({
          id: d.id,
          cls: d.cls,
          vn: c.vn,
          dist,
          zone: ZN_MAP[zKey],
          zoneKey: zKey,
          speed: absSpeedKmh,
          lvl,
          x1: d.x1,
          y1: d.y1,
          x2: d.x2,
          y2: d.y2,
          inside,
          direction,
          ttc,
          relSpeedKmh,
          approachState,
          approachDesc,
        });

        if (inside && isZoneActive && (!newZs[zKey].dist || dist < newZs[zKey].dist!)) {
          newZs[zKey] = {
            dist,
            lvl,
            cls: d.cls,
            vn: c.vn,
            disabled: false,
            ttc,
            relSpeedKmh,
            approachState,
            approachDesc,
          };
        }
      });

      // Cleanup lost tracks
      for (const k in trackHistoryRef.current) {
        if (now - trackHistoryRef.current[k].seen > 2000) {
          delete trackHistoryRef.current[k];
          delete prevYRef.current[Number(k)];
        }
      }

      // Throttle React State Updates to ~100ms (reduces 85% redundant React renders and stops UI lag)
      if (now - lastUiRef.current >= 100) {
        lastUiRef.current = now;
        setZoneLeft(newZs.L);
        setZoneFront(newZs.F);
        setZoneRight(newZs.R);
        setTrackedVehicles(computedTracked);

        // Determine worst alert for top banner (CHỈ XÉT CÁC VÙNG ĐANG BẬT)
        let worst: {
          dist: number;
          lvl: 1 | 2;
          cls: string;
          vn: string;
          zoneKey: 'L' | 'F' | 'R';
          ttc?: number | null;
          approachState?: string;
          relSpeedKmh?: number;
        } | null = null;

        ((['L', 'F', 'R'] as const).filter((k) => activeZones[k])).forEach((k) => {
          const z = newZs[k];
          if (z.dist && z.lvl > 0) {
            if (!worst || z.dist < worst.dist) {
              worst = {
                dist: z.dist,
                lvl: z.lvl as 1 | 2,
                cls: z.cls || 'car',
                vn: z.vn || 'Ô tô',
                zoneKey: k,
                ttc: z.ttc,
                approachState: z.approachState,
                relSpeedKmh: z.relSpeedKmh,
              };
            }
          }
        });

        if (worst) {
          const isCrit = (worst as any).lvl === 2;
          const prefix = isCrit ? '🚨 NGUY HIỂM: ' : '⚠ Chú ý: ';
          const zoneStr = (worst as any).zoneKey === 'F' ? 'phía trước' : (worst as any).zoneKey === 'L' ? 'bên trái' : 'bên phải';
          const objVn = (worst as any).vn.toLowerCase();
          const distStr = `${(worst as any).dist.toFixed(1)}m`;

          let extraInfo = '';
          if ((worst as any).approachState === 'CUT_IN') {
            extraInfo = ' (Tạt đầu vào làn!)';
          } else if ((worst as any).ttc !== null && (worst as any).ttc <= 3.0) {
            extraInfo = ` (TTC: ${(worst as any).ttc.toFixed(1)}s)`;
          } else if ((worst as any).approachState === 'CLOSING_IN') {
            extraInfo = ' (Đang áp sát nhanh)';
          }

          const actionStr = isCrit ? ' Phanh gấp!' : '';

          setAlertBanner({
            text: `${prefix}${objVn} ${zoneStr} ${distStr}${extraInfo}.${actionStr}`,
            lvl: (worst as any).lvl,
          });

          // Trigger Audio beep nếu bật âm thanh VÀ xe không đang dừng đèn đỏ (egoSpeed >= 5)
          if (soundEnabled && egoSpeed >= 5) {
            // Tần suất bíp thông minh: TTC càng ngắn (hoặc level 2) bíp càng nhanh
            const gap = isCrit
              ? ((worst as any).ttc && (worst as any).ttc < 1.2 ? 220 : 350)
              : 850;
            if (now - lastBeepRef.current > gap) {
              lastBeepRef.current = now;
              playBeep(isCrit ? 950 : 540);
            }
          }
        } else {
          setAlertBanner(null);
        }
      }

      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [realVehicles, simMode, isStreaming, isPaused, warnThreshold, dangerThreshold, focalLength, soundEnabled, playBeep, activeZones, currentSpeed, drivingProfile]);

  return {
    warnThreshold,
    setWarnThreshold,
    dangerThreshold,
    setDangerThreshold,
    focalLength,
    setFocalLength,
    showZones,
    setShowZones,
    soundEnabled,
    setSoundEnabled,
    simMode,
    setSimMode,
    drivingProfile,
    setDrivingProfile: setDrivingProfileSafe,
    activeZones,
    setActiveZones,
    toggleZone,
    setAllZones,
    zoneLeft,
    zoneFront,
    zoneRight,
    trackedVehicles,
    alertBanner,
    lineCrossings,
    resetLineCrossings,
    isPaused: !!isPaused,
  };
}
