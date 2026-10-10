'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { VehicleDetection, LineCrossingData } from '../types/detection';
import { soundEngine } from '../lib/soundEngine';

export interface ZoneStatus {
  dist: number | null;
  lvl: 0 | 1 | 2; // 0 = Safe, 1 = Warn, 2 = Danger
  cls?: string;
  vn?: string;
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
}: UseTrafficDistanceEngineProps) {
  // Configurable thresholds
  const [warnThreshold, setWarnThreshold] = useState<number>(8);
  const [dangerThreshold, setDangerThreshold] = useState<number>(4);
  const [focalLength, setFocalLength] = useState<number>(520);
  const [showZones, setShowZones] = useState<boolean>(true);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(false);
  const [simMode, setSimMode] = useState<boolean>(false);

  // 3-Zone states
  const [zoneLeft, setZoneLeft] = useState<ZoneStatus>({ dist: null, lvl: 0 });
  const [zoneFront, setZoneFront] = useState<ZoneStatus>({ dist: null, lvl: 0 });
  const [zoneRight, setZoneRight] = useState<ZoneStatus>({ dist: null, lvl: 0 });

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
    fetch('http://localhost:8000/api/v1/traffic-density/reset-line-crossings?session_id=live_stream', { method: 'POST' }).catch(() => {});
  }, []);

  // Simulation state
  const simObjsRef = useRef<any[]>([]);
  const nextIdRef = useRef<number>(1);
  const trackHistoryRef = useRef<Record<number, { d: number; v: number; seen: number }>>({});
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
          setZoneLeft({ dist: null, lvl: 0 });
          setZoneFront({ dist: null, lvl: 0 });
          setZoneRight({ dist: null, lvl: 0 });
          setTrackedVehicles([]);
          setAlertBanner(null);
        }
        animId = requestAnimationFrame(loop);
        return;
      }

      // Analyze vehicles in 3 zones
      const newZs: { L: ZoneStatus; F: ZoneStatus; R: ZoneStatus } = {
        L: { dist: null, lvl: 0 },
        F: { dist: null, lvl: 0 },
        R: { dist: null, lvl: 0 },
      };

      const computedTracked: TrackedVehicle[] = [];
      const top = HZ + (F0 * CAMH) / 32;
      const bot = HZ + (F0 * CAMH) / 2;

      list.forEach((d) => {
        const c = CLS_MAP[d.cls] || CLS_MAP.car;
        const hpx = Math.max(1, d.y2 - d.y1);
        const dist = d.distance_m != null ? d.distance_m : Math.max(1.5, Math.min(80, (F0 * c.h) / hpx));
        const xc = (d.x1 + d.x2) / 2;
        const hw = RH * (d.y2 - HZ) / CAMH;
        const u = hw !== 0 ? (xc - CX) / hw : 0;
        const inside = d.y2 >= top && d.y2 <= bot && Math.abs(u) <= 1.25;
        const zKey: 'L' | 'F' | 'R' = u < -0.33 ? 'L' : u > 0.33 ? 'R' : 'F';

        let tr = trackHistoryRef.current[d.id];
        if (!tr) tr = trackHistoryRef.current[d.id] = { d: dist, v: 0, seen: now };
        if (dt > 0) {
          const v = -(dist - tr.d) / dt;
          tr.v = tr.v * 0.9 + v * 0.1;
        }
        tr.d = dist;
        tr.seen = now;

        const lvl: 0 | 1 | 2 = dist <= dangerThreshold ? 2 : dist <= warnThreshold ? 1 : 0;
        const speedKmh = Math.abs(tr.v * 3.6);

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
                  { id: d.id, cls: d.cls, vn: c.vn, speed: Math.round(speedKmh), dir: 'IN', time: Date.now() },
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
                  { id: d.id, cls: d.cls, vn: c.vn, speed: Math.round(speedKmh), dir: 'OUT', time: Date.now() },
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
          speed: speedKmh,
          lvl,
          x1: d.x1,
          y1: d.y1,
          x2: d.x2,
          y2: d.y2,
          inside,
          direction,
        });

        if (inside && (!newZs[zKey].dist || dist < newZs[zKey].dist!)) {
          newZs[zKey] = {
            dist,
            lvl,
            cls: d.cls,
            vn: c.vn,
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

        // Determine worst alert for top banner
        let worst: { dist: number; lvl: 1 | 2; cls: string; vn: string; zoneKey: 'L' | 'F' | 'R' } | null = null;
        (['L', 'F', 'R'] as const).forEach((k) => {
          const z = newZs[k];
          if (z.dist && z.lvl > 0) {
            if (!worst || z.dist < worst.dist) {
              worst = {
                dist: z.dist,
                lvl: z.lvl as 1 | 2,
                cls: z.cls || 'car',
                vn: z.vn || 'Ô tô',
                zoneKey: k,
              };
            }
          }
        });

        if (worst) {
          const prefix = (worst as any).lvl === 2 ? 'NGUY HIỂM: ' : 'Chú ý: ';
          const zoneStr = (worst as any).zoneKey === 'F' ? 'phía trước' : (worst as any).zoneKey === 'L' ? 'bên trái' : 'bên phải';
          setAlertBanner({
            text: `${prefix}${(worst as any).vn.toLowerCase()} ${zoneStr} ${(worst as any).dist.toFixed(1)} m`,
            lvl: (worst as any).lvl,
          });

          // Trigger Audio beep & voice alert if enabled
          if (soundEnabled) {
            const gap = (worst as any).lvl === 2 ? 350 : 900;
            if (now - lastBeepRef.current > gap) {
              lastBeepRef.current = now;
              playBeep((worst as any).lvl === 2 ? 900 : 520);
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
  }, [realVehicles, simMode, isStreaming, isPaused, warnThreshold, dangerThreshold, focalLength, soundEnabled, playBeep]);

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
