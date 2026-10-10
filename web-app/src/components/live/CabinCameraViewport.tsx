'use client';

import React, { memo, useEffect, useRef, useState, useCallback } from 'react';
import {
  Eye,
  CameraOff,
  Clock,
  AlertTriangle,
  Camera,
  BellOff,
  Bell,
  Shield,
  Activity,
  RotateCcw,
} from 'lucide-react';
import { FaceLandmarker, FilesetResolver, DrawingUtils } from '@mediapipe/tasks-vision';
import { DriverMonitorResult } from '../../types/detection';
import { TGStatusBadge } from '../ui';

export interface CabinCameraViewportProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  driverResult: DriverMonitorResult | null;
  isStreaming: boolean;
  isWebcamActive?: boolean;
  onToggleWebcam?: () => void;
  driverName?: string;
  driverId?: number;
  driverPhone?: string;
  safetyScore?: number | null;
  continuousMinutes?: number;
  onDmsEvent?: (event: { type: string; level: 'warning' | 'critical'; closedDuration: number; ear: number }) => void;
}

const CFG = {
  EAR_CLOSED: 0.21,
  MAR_YAWN: 0.6,
  YAWN_MIN_MS: 1200,
  PERCLOS_WINDOW_MS: 30000,
  PERCLOS_WARN: 20,
  PERCLOS_DANGER: 40,
  CLOSED_WARN_S: 2.0,
  CLOSED_DANGER_S: 5.0,
};

const R_EYE = [33, 160, 158, 133, 153, 144];
const L_EYE = [362, 385, 387, 263, 373, 380];
const d = (a: any, b: any) => Math.hypot(a.x - b.x, a.y - b.y);

function ear(lm: any[], idx: number[]) {
  const [p1, p2, p3, p4, p5, p6] = idx.map((i) => lm[i]);
  return (d(p2, p6) + d(p3, p5)) / (2 * d(p1, p4));
}

function mar(lm: any[]) {
  return d(lm[13], lm[14]) / d(lm[78], lm[308]);
}

let audioCtx: AudioContext | null = null;
function beep(freq = 880, ms = 250) {
  if (typeof window === 'undefined') return;
  const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
  if (!AudioContextClass) return;
  audioCtx = audioCtx || new AudioContextClass();
  const o = audioCtx.createOscillator();
  const g = audioCtx.createGain();
  o.frequency.value = freq;
  o.connect(g);
  g.connect(audioCtx.destination);
  g.gain.value = 0.15;
  o.start();
  o.stop(audioCtx.currentTime + ms / 1000);
}

export const CabinCameraViewport = memo(function CabinCameraViewport({
  videoRef,
  isStreaming,
  isWebcamActive = false,
  onToggleWebcam,
  driverName = 'Người Lái Xe',
  driverId = 1,
  driverPhone = '0901 234 567',
  continuousMinutes = 0,
  driverResult,
  onDmsEvent,
}: CabinCameraViewportProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [landmarker, setLandmarker] = useState<FaceLandmarker | null>(null);

  // Local States for DMS UI
  const [beltOn, setBeltOn] = useState<boolean | null>(null);
  const [muted, setMuted] = useState(false);
  const [yawnCount, setYawnCount] = useState(0);
  const [score, setScore] = useState(100);
  const [perclos, setPerclos] = useState(0);
  const [closedS, setClosedS] = useState(0);
  const [earValue, setEarValue] = useState<number | null>(null);
  const [eyeText, setEyeText] = useState('—');
  const [level, setLevel] = useState<'ok' | 'warn' | 'danger' | 'neutral'>('neutral');
  const [label, setLabel] = useState('Chờ camera');
  const [alertMsg, setAlertMsg] = useState('');

  // Refs for tracking across rAF frames without triggering re-renders
  const beltOnRef = useRef<boolean | null>(null);
  const mutedRef = useRef(false);
  const lastTsRef = useRef(-1);
  const runningRef = useRef(false);
  const samplesRef = useRef<{ t: number; closed: boolean }[]>([]);
  const closedSinceRef = useRef<number | null>(null);
  const yawnSinceRef = useRef<number | null>(null);
  const yawnCountedRef = useRef(false);
  const penaltyYawnRef = useRef(0);
  const lastBeepRef = useRef(0);
  const manualOverrideRef = useRef(false);

  useEffect(() => {
    beltOnRef.current = beltOn;
  }, [beltOn]);
  useEffect(() => {
    mutedRef.current = muted;
  }, [muted]);

  // Init MediaPipe model
  useEffect(() => {
    let active = true;
    const initModel = async () => {
      try {
        const fileset = await FilesetResolver.forVisionTasks(
          'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm'
        );
        const lm = await FaceLandmarker.createFromOptions(fileset, {
          baseOptions: {
            modelAssetPath:
              'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
            delegate: 'GPU',
          },
          runningMode: 'VIDEO',
          numFaces: 1,
        });
        if (active) setLandmarker(lm);
      } catch (err) {
        console.error('Failed to init FaceLandmarker', err);
      }
    };
    initModel();
    return () => {
      active = false;
    };
  }, []);

  // Belt Simulation Toggle & Backend Sync
  useEffect(() => {
    if (
      !manualOverrideRef.current &&
      driverResult?.seatbelt &&
      driverResult.seatbelt.seatbelt_on !== undefined &&
      driverResult.seatbelt.seatbelt_on !== null
    ) {
      setBeltOn(driverResult.seatbelt.seatbelt_on);
    }
  }, [driverResult?.seatbelt?.seatbelt_on]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === 'b' && document.activeElement?.tagName !== 'INPUT') {
        manualOverrideRef.current = true;
        setBeltOn((prev) => (prev === true ? false : true));
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Alarm function
  const triggerAlarm = useCallback((msg: string, lvl: 'warn' | 'danger') => {
    setAlertMsg(msg);
    if (!mutedRef.current) {
      const now = performance.now();
      if (now - lastBeepRef.current > (lvl === 'danger' ? 600 : 1500)) {
        beep(lvl === 'danger' ? 1000 : 700, 250);
        lastBeepRef.current = now;
      }
    }
  }, []);

  // Main Loop
  useEffect(() => {
    if (!isWebcamActive || !landmarker || !videoRef.current) {
      runningRef.current = false;
      setLevel('neutral');
      setLabel(isWebcamActive ? 'Đang phân tích...' : 'Chờ camera');
      setAlertMsg('');
      if (canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d');
        if (ctx) ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      }
      return;
    }

    runningRef.current = true;
    let frameId: number;

    const analyze = (lm: any) => {
      const now = performance.now();
      const e = (ear(lm, R_EYE) + ear(lm, L_EYE)) / 2;
      const m = mar(lm);
      const closed = e < CFG.EAR_CLOSED;

      if (closed) {
        closedSinceRef.current = closedSinceRef.current ?? now;
      } else {
        closedSinceRef.current = null;
      }
      const cS = closedSinceRef.current ? (now - closedSinceRef.current) / 1000 : 0;

      const samples = samplesRef.current;
      samples.push({ t: now, closed });
      while (samples.length && now - samples[0].t > CFG.PERCLOS_WINDOW_MS) samples.shift();
      const pclos = samples.length ? (100 * samples.filter((s) => s.closed).length) / samples.length : 0;

      if (m > CFG.MAR_YAWN) {
        yawnSinceRef.current = yawnSinceRef.current ?? now;
        if (!yawnCountedRef.current && now - yawnSinceRef.current >= CFG.YAWN_MIN_MS) {
          setYawnCount((prev) => prev + 1);
          yawnCountedRef.current = true;
          penaltyYawnRef.current += 5;
        }
      } else {
        yawnSinceRef.current = null;
        yawnCountedRef.current = false;
      }
      const yawning = Boolean(yawnSinceRef.current && now - yawnSinceRef.current > 400);

      let newScore = 100 - pclos * 0.6 - penaltyYawnRef.current - (cS >= CFG.CLOSED_WARN_S ? 15 : 0);
      if (beltOnRef.current === false) newScore -= 15;
      newScore = Math.max(0, Math.round(newScore));

      let lvl: 'ok' | 'warn' | 'danger' = 'ok';
      let lbl = 'Tỉnh táo';
      let msg = '';

      const currentYawnCount = penaltyYawnRef.current / 5;

      if (cS >= CFG.CLOSED_DANGER_S || pclos >= CFG.PERCLOS_DANGER) {
        lvl = 'danger';
        lbl = 'Nguy hiểm';
        msg = '⚠ CẢNH BÁO: TÀI XẾ NGỦ GẬT (NHẮM MẮT > 5S)!';
        onDmsEvent?.({
          type: 'eyes_closed_prolonged',
          level: 'critical',
          closedDuration: cS,
          ear: e
        });
      } else if (pclos >= CFG.PERCLOS_WARN || cS >= CFG.CLOSED_WARN_S || yawning || currentYawnCount >= 3) {
        lvl = 'warn';
        lbl = 'Buồn ngủ';
        msg = yawning ? '😮 Phát hiện ngáp – hãy chú ý' : '😴 Dấu hiệu buồn ngủ (Nhắm mắt > 2s)';
        if (cS >= CFG.CLOSED_WARN_S) {
          onDmsEvent?.({
            type: 'eyes_closed_warning',
            level: 'warning',
            closedDuration: cS,
            ear: e
          });
        }
      }

      if (beltOnRef.current === false && !msg) {
        msg = '🔓 Chưa cài dây an toàn!';
        triggerAlarm(msg, 'warn');
      } else if (msg) {
        triggerAlarm(msg, lvl as 'warn' | 'danger');
      } else {
        setAlertMsg('');
      }

      setEarValue(e);
      setClosedS(cS);
      setPerclos(pclos);
      setScore(newScore);
      setLevel(lvl);
      setLabel(lbl);
      setEyeText(closed ? (cS >= CFG.CLOSED_WARN_S ? 'Nhắm lâu' : 'Nhắm') : 'Mở');
    };

    const noFace = () => {
      closedSinceRef.current = null;
      triggerAlarm('👤 Không thấy khuôn mặt', 'warn');
      setEyeText('Không thấy');
      setLevel('warn');
      setLabel('Mất dấu mặt');
    };

    const loop = () => {
      if (!runningRef.current) return;
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (video && canvas && video.readyState >= 2 && video.videoWidth > 0 && video.videoHeight > 0) {
        if (video.currentTime !== lastTsRef.current) {
          lastTsRef.current = video.currentTime;

          if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
          }

          const ctx = canvas.getContext('2d');
          if (ctx) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            try {
              const startTimeMs = performance.now();
              const res = landmarker.detectForVideo(video, startTimeMs);
              if (res.faceLandmarks && res.faceLandmarks.length > 0) {
                const lm = res.faceLandmarks[0];
                const drawingUtils = new DrawingUtils(ctx);
                drawingUtils.drawConnectors(lm, FaceLandmarker.FACE_LANDMARKS_CONTOURS, {
                  color: '#38bdf888',
                  lineWidth: 1,
                });
                analyze(lm);
              } else {
                noFace();
              }
            } catch (e) {
              console.error('Tracking error:', e);
            }
          }
        }
      }
      frameId = requestAnimationFrame(loop);
    };

    frameId = requestAnimationFrame(loop);
    return () => {
      runningRef.current = false;
      cancelAnimationFrame(frameId);
    };
  }, [isWebcamActive, landmarker, videoRef, triggerAlarm]);

  const maxContinuousMinutes = 240;
  const continuousProgress = Math.min(100, Math.round((continuousMinutes / maxContinuousMinutes) * 100));
  const isContinuousWarning = continuousMinutes >= 210;

  const badgeVariant =
    level === 'danger'
      ? 'critical'
      : level === 'warn'
      ? 'warning'
      : level === 'ok'
      ? 'safe'
      : 'neutral';

  const resetAll = () => {
    samplesRef.current = [];
    penaltyYawnRef.current = 0;
    setYawnCount(0);
    setPerclos(0);
    setScore(100);
    setAlertMsg('');
  };

  const initials = driverName
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .slice(-2)
    .join('')
    .toUpperCase() || 'TX';

  return (
    <div className="w-full bg-white border border-[#E4E9EF] rounded-[10px] overflow-hidden shadow-sm flex flex-col select-none relative">
      {/* ── 1. HEADER (CLEAN & CONCISE) ── */}
      <div className="py-2.5 px-3.5 border-b border-[#E4E9EF] bg-[#F8FAFC] flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-[#EFF4FF] flex items-center justify-center text-[#175CD3]">
            <Eye className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-bold text-[#16202A] tracking-tight">
            Cabin DMS
          </span>
          <span className="text-[10px] text-[#98A2B3] font-mono hidden sm:inline">
            • Buồng lái
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {onToggleWebcam && (
            <button
              onClick={onToggleWebcam}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all cursor-pointer border ${
                isWebcamActive
                  ? 'bg-[#FEF3F2] text-[#B42318] border-[#FECDCA] hover:bg-[#FEE4E2]'
                  : 'bg-white text-[#175CD3] border-[#B2CCFF] hover:bg-[#EFF4FF]'
              }`}
              title="Bật/Tắt webcam buồng lái"
            >
              {isWebcamActive ? (
                <>
                  <CameraOff className="w-3 h-3 text-[#F04438]" />
                  <span>Tắt</span>
                </>
              ) : (
                <>
                  <Camera className="w-3 h-3 text-[#175CD3]" />
                  <span>Bật Webcam</span>
                </>
              )}
            </button>
          )}

          <TGStatusBadge variant={badgeVariant} size="sm" pulse={level === 'danger'}>
            {label}
          </TGStatusBadge>
        </div>
      </div>

      {/* ── 2. CABIN CAMERA VIEWPORT ── */}
      <div
        className="relative w-full bg-[#0C111D] overflow-hidden border-b border-[#E4E9EF]"
        style={{ aspectRatio: '16/9', minHeight: '175px' }}
      >
        <video
          ref={videoRef}
          playsInline
          muted
          autoPlay
          className="w-full h-full object-cover bg-[#0A0D14]"
          style={{ transform: 'scaleX(-1)' }}
        />

        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full object-cover pointer-events-none"
          style={{ transform: 'scaleX(-1)' }}
        />

        {/* Live Indicator */}
        {isWebcamActive && (
          <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-white text-[10px] font-bold z-10">
            <span className="w-1.5 h-1.5 rounded-full bg-[#12B76A] animate-pulse" />
            <span className="tracking-wider">DMS LIVE</span>
          </div>
        )}

        {/* Alert Toast Overlay */}
        {alertMsg && (
          <div
            className={`absolute top-2 inset-x-3 z-30 py-1.5 px-2.5 rounded-md font-bold text-center text-white shadow-xl animate-pulse border flex items-center justify-center gap-2 text-xs backdrop-blur-md ${
              level === 'danger' ? 'bg-red-600/90 border-red-400' : 'bg-orange-500/90 border-orange-300'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
            <span className="truncate">{alertMsg}</span>
          </div>
        )}

        {/* HUD Telemetry Strip */}
        {isWebcamActive && (
          <div className="absolute bottom-2 inset-x-2 flex items-center justify-between text-[10px] text-white/90 bg-[#0C111D]/85 backdrop-blur-md px-2.5 py-1 rounded-md border border-white/10 font-mono z-10">
            <div className="flex items-center gap-2">
              <span>
                EAR <strong className="text-white">{earValue !== null ? earValue.toFixed(2) : '—'}</strong>
              </span>
              <span className="text-white/30">•</span>
              <span>
                PERCLOS <strong className="text-white">{Math.round(perclos)}%</strong>
              </span>
            </div>
            <span className={`font-semibold ${beltOn ? 'text-[#12B76A]' : 'text-[#F04438]'}`}>
              {beltOn ? '✓ Dây đai' : '✗ Chưa cài'}
            </span>
          </div>
        )}

        {/* Minimalist Empty State when Webcam OFF (NO giant text paragraphs) */}
        {!isWebcamActive && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-b from-[#0C111D]/95 to-[#0A0D14]/95 text-white/70 p-4 text-center select-none z-20">
            <div className="w-9 h-9 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-1.5 text-white/40">
              <CameraOff className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-white/80">Camera Buồng Lái Đang Tắt</span>
            <span className="text-[10px] text-white/40 mt-0.5">MediaPipe Face Mesh • Giám sát tập trung</span>
            {onToggleWebcam && (
              <button
                onClick={onToggleWebcam}
                className="mt-2.5 flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#175CD3] hover:bg-[#155EEF] text-white text-xs font-bold transition-all cursor-pointer shadow-sm"
              >
                <Camera className="w-3.5 h-3.5" />
                <span>Bật Webcam Buồng Lái</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* ── 3. DRIVER IDENTITY & SAFETY SCORE ── */}
      <div className="p-3 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-[#EFF4FF] border border-[#B2CCFF] flex items-center justify-center font-bold text-xs text-[#175CD3]">
              {initials}
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-xs text-[#16202A]">{driverName}</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#F2F4F7] text-[#475467] font-mono">
                  #{driverId}
                </span>
              </div>
              <span className="text-[10px] text-[#667085] font-mono block leading-tight">{driverPhone}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-[#F8FAFC] border border-[#E4E9EF] px-2.5 py-1 rounded-md">
            <div className="text-right">
              <span className="text-[9px] uppercase tracking-wider text-[#667085] font-bold block">
                Điểm an toàn
              </span>
              <span
                className={`text-xs font-black font-mono leading-none ${
                  score < 50 ? 'text-[#F04438]' : score < 80 ? 'text-[#F79009]' : 'text-[#12B76A]'
                }`}
              >
                {isWebcamActive ? `${score}` : '—'}
                <span className="text-[10px] text-[#98A2B3] font-normal">/100</span>
              </span>
            </div>
          </div>
        </div>

        {/* ── 4. FOUR CLEAN MICRO-STAT CARDS (NO WRAPPING BUGS) ── */}
        <div className="grid grid-cols-2 gap-2">
          {/* PERCLOS */}
          <div className="p-2 rounded-md bg-[#F8FAFC] border border-[#E4E9EF] flex flex-col justify-between">
            <div className="flex items-center justify-between text-[#667085] text-[10px] font-medium">
              <span>TỈNH TÁO</span>
              <Activity className="w-3 h-3 text-[#175CD3]" />
            </div>
            <div className="flex items-baseline justify-between mt-1">
              <span
                className={`text-sm font-black font-mono ${
                  !isWebcamActive
                    ? 'text-[#98A2B3]'
                    : perclos > 40
                    ? 'text-[#F04438]'
                    : perclos > 20
                    ? 'text-[#F79009]'
                    : 'text-[#12B76A]'
                }`}
              >
                {isWebcamActive ? `${Math.round(perclos)}%` : '—'}
              </span>
              <span className="text-[9px] font-semibold text-[#667085]">
                {isWebcamActive
                  ? perclos > 40
                    ? 'Nguy hiểm'
                    : perclos > 20
                    ? 'Buồn ngủ'
                    : 'Tập trung'
                  : 'Chờ camera'}
              </span>
            </div>
          </div>

          {/* Dây an toàn */}
          <div className="p-2 rounded-md bg-[#F8FAFC] border border-[#E4E9EF] flex flex-col justify-between">
            <div className="flex items-center justify-between text-[#667085] text-[10px] font-medium">
              <span>DÂY AN TOÀN</span>
              <Shield className="w-3 h-3 text-[#6172F3]" />
            </div>
            <div className="flex items-baseline justify-between mt-1">
              <span
                className={`text-xs font-bold ${
                  beltOn === null ? 'text-[#98A2B3]' : beltOn ? 'text-[#12B76A]' : 'text-[#F04438]'
                }`}
              >
                {beltOn === null ? '—' : beltOn ? 'Đã cài' : 'Chưa cài'}
              </span>
              <span className="text-[9px] text-[#98A2B3] font-mono">[Phím B]</span>
            </div>
          </div>

          {/* Trạng thái mắt */}
          <div className="p-2 rounded-md bg-[#F8FAFC] border border-[#E4E9EF] flex flex-col justify-between">
            <div className="flex items-center justify-between text-[#667085] text-[10px] font-medium">
              <span>MẮT</span>
              <Eye className="w-3 h-3 text-[#0E9384]" />
            </div>
            <div className="flex items-baseline justify-between mt-1">
              <span
                className={`text-xs font-bold ${
                  !isWebcamActive
                    ? 'text-[#98A2B3]'
                    : eyeText.includes('Nhắm')
                    ? 'text-[#F04438]'
                    : 'text-[#12B76A]'
                }`}
              >
                {!isWebcamActive ? '—' : eyeText}
              </span>
              <span className="text-[9px] font-mono text-[#667085]">
                {isWebcamActive && earValue !== null ? `EAR ${earValue.toFixed(2)}` : 'MediaPipe'}
              </span>
            </div>
          </div>

          {/* Số lần ngáp */}
          <div className="p-2 rounded-md bg-[#F8FAFC] border border-[#E4E9EF] flex flex-col justify-between">
            <div className="flex items-center justify-between text-[#667085] text-[10px] font-medium">
              <span>LẦN NGÁP</span>
              <Clock className="w-3 h-3 text-[#F79009]" />
            </div>
            <div className="flex items-baseline justify-between mt-1">
              <span
                className={`text-sm font-black font-mono ${
                  yawnCount >= 3 ? 'text-[#F04438]' : yawnCount > 1 ? 'text-[#F79009]' : 'text-[#16202A]'
                }`}
              >
                {isWebcamActive ? `${yawnCount}` : '—'}
                <span className="text-[10px] font-normal text-[#98A2B3]"> lần</span>
              </span>
              <span className="text-[9px] font-semibold text-[#667085]">
                {yawnCount >= 3 ? 'Cần nghỉ' : 'Bình thường'}
              </span>
            </div>
          </div>
        </div>

        {/* ── 5. ACTION CONTROLS TOOLBAR ── */}
        <div className="flex gap-1.5 pt-0.5">
          <button
            onClick={() => {
              manualOverrideRef.current = true;
              setBeltOn((prev) => !prev);
            }}
            className={`flex-1 flex items-center justify-center gap-1.5 text-[11px] font-semibold py-1.5 rounded-md transition-all border cursor-pointer ${
              beltOn
                ? 'bg-[#ECFDF3] text-[#027A48] border-[#ABEFC6]'
                : 'bg-[#F8FAFC] text-[#475467] border-[#E4E9EF] hover:bg-[#F2F4F7]'
            }`}
            title="Nhấn phím B hoặc nút này để đổi trạng thái dây an toàn"
          >
            <Shield className="w-3 h-3" />
            <span>{beltOn ? 'Đã cài' : 'Cài dây'}</span>
          </button>

          <button
            onClick={() => setMuted(!muted)}
            className={`flex-1 flex items-center justify-center gap-1.5 text-[11px] font-semibold py-1.5 rounded-md transition-all border cursor-pointer ${
              !muted
                ? 'bg-[#EFF4FF] text-[#175CD3] border-[#B2CCFF]'
                : 'bg-[#F8FAFC] text-[#98A2B3] border-[#E4E9EF]'
            }`}
          >
            {muted ? <BellOff className="w-3 h-3" /> : <Bell className="w-3 h-3" />}
            <span>{muted ? 'Tắt âm' : 'Âm báo'}</span>
          </button>

          <button
            onClick={resetAll}
            className="flex-1 flex items-center justify-center gap-1.5 text-[11px] font-semibold py-1.5 rounded-md transition-all bg-[#F8FAFC] text-[#475467] border border-[#E4E9EF] hover:bg-[#F2F4F7] cursor-pointer"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Làm mới</span>
          </button>
        </div>

        {/* ── 6. 4-HOUR DRIVING REGULATION PROGRESS ── */}
        <div className="pt-2 border-t border-[#F2F4F7] space-y-1">
          <div className="flex items-center justify-between text-[11px]">
            <div className="flex items-center gap-1 text-[#475467] font-medium">
              <Clock className="w-3.5 h-3.5 text-[#175CD3]" />
              <span>Lái liên tục (Max 4h):</span>
            </div>
            <span className="font-mono font-bold text-[#16202A]">
              {Math.floor(continuousMinutes / 60)}h
              {(continuousMinutes % 60).toString().padStart(2, '0')}m / 4h00m
            </span>
          </div>

          <div className="w-full h-1.5 rounded-full bg-[#E4E9EF] overflow-hidden">
            <div
              className={`h-full transition-all duration-300 rounded-full ${
                isContinuousWarning
                  ? 'bg-[#F04438]'
                  : continuousMinutes >= 180
                  ? 'bg-[#F79009]'
                  : 'bg-[#175CD3]'
              }`}
              style={{ width: `${continuousProgress}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
});
