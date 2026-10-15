'use client';

import React, { useEffect, useRef } from 'react';
import { Upload, Pause, Play, RefreshCw } from 'lucide-react';
import { TrackedVehicle, ZoneStatus, LineCrossingStats, ActiveZones, DrivingProfile } from '../../hooks/useTrafficDistanceEngine';

export interface TrafficDistancePanelProps {
  zoneLeft: ZoneStatus;
  zoneFront: ZoneStatus;
  zoneRight: ZoneStatus;
  activeZones?: ActiveZones;
  toggleZone?: (zone: 'L' | 'F' | 'R') => void;
  setAllZones?: (zones: ActiveZones) => void;
  warnThreshold: number;
  setWarnThreshold: (val: number) => void;
  dangerThreshold: number;
  setDangerThreshold: (val: number) => void;
  focalLength: number;
  setFocalLength: (val: number) => void;
  showZones: boolean;
  setShowZones: (val: boolean) => void;
  soundEnabled: boolean;
  setSoundEnabled: (val: boolean) => void;
  simMode: boolean;
  setSimMode: (val: boolean) => void;
  trackedVehicles: TrackedVehicle[];
  isPaused: boolean;
  onTogglePause?: () => void;
  onUploadVideo?: () => void;
  onResetSim?: () => void;
  alertBanner?: { text: string; lvl: 1 | 2 } | null;
  lineCrossings?: LineCrossingStats;
  onResetLineCrossings?: () => void;
  drivingProfile?: DrivingProfile;
  setDrivingProfile?: (profile: DrivingProfile) => void;
  dynamicSafeDistance?: number;
  effectiveWarnDist?: number;
  effectiveDangerDist?: number;
}

const CLS_MAP: Record<string, { h: number; w: number; c: string; vn: string }> = {
  motorbike: { h: 1.5, w: 0.8, c: '#fbbf24', vn: 'Xe máy' },
  car: { h: 1.5, w: 1.8, c: '#60a5fa', vn: 'Ô tô' },
  person: { h: 1.7, w: 0.5, c: '#a78bfa', vn: 'Người' },
  truck: { h: 3.0, w: 2.5, c: '#f472b6', vn: 'Xe tải' },
  bus: { h: 3.2, w: 2.6, c: '#34d399', vn: 'Xe buýt' },
};

export function TrafficDistancePanel({
  zoneLeft,
  zoneFront,
  zoneRight,
  activeZones = { L: true, F: true, R: true },
  toggleZone,
  setAllZones,
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
  trackedVehicles,
  isPaused,
  onTogglePause,
  onUploadVideo,
  onResetSim,
  alertBanner,
  lineCrossings,
  onResetLineCrossings,
  drivingProfile = 'auto',
  setDrivingProfile,
  dynamicSafeDistance,
  effectiveWarnDist,
  effectiveDangerDist,
}: TrafficDistancePanelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const phaseRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(performance.now());

  const sortedRows = [...trackedVehicles].filter((o) => o.inside).sort((a, b) => a.dist - b.dist).slice(0, 8);

  const formatZoneSpan = (z: ZoneStatus, isActive: boolean = true) => {
    if (!isActive || z.disabled) return 'Đã tắt';
    if (!z.dist) return 'An toàn';
    return `${z.dist.toFixed(1)} m`;
  };

  const getZoneBorderColor = (z: ZoneStatus, isActive: boolean = true) => {
    if (!isActive || z.disabled) return 'border-l-slate-400 text-slate-400 opacity-60';
    if (z.lvl === 2) return 'border-l-[#EF4444] text-[#B42318]';
    if (z.lvl === 1) return 'border-l-[#F59E0B] text-[#B54708]';
    return 'border-l-[#12B76A] text-[#027A48]';
  };

  const edgeLvlL = (activeZones.L !== false ? zoneLeft?.lvl : 0) || 0;
  const edgeLvlF = (activeZones.F !== false ? zoneFront?.lvl : 0) || 0;
  const edgeLvlR = (activeZones.R !== false ? zoneRight?.lvl : 0) || 0;



  // ── VẼ SÂN KHẤU 3D RADAR CỰ LY (CANVAS 540x720 GIỐNG FILE CẢNH BÁO KHOẢNG CÁCH XE.HTML) ──
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    const W = 540;
    const H = 720;
    const HZ = 288;
    const CAMH = 1.3;
    const CX = W / 2;
    const RH = 5.5;
    const F0 = focalLength || 520;

    const P = (X: number, Z: number) => [
      CX + (F0 * X) / Z,
      HZ + (F0 * CAMH) / Z,
    ];

    const render = (now: number) => {
      const dt = Math.min((now - lastTimeRef.current) / 1000, 0.1);
      lastTimeRef.current = now;

      ctx.clearRect(0, 0, W, H);

      // 1. Nền hoàng hôn Sunset Gradient + Mặt đất tối
      const g = ctx.createLinearGradient(0, 0, 0, HZ);
      g.addColorStop(0, '#1d2a44');
      g.addColorStop(0.7, '#c2703d');
      g.addColorStop(1, '#f0b562');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, HZ);

      // Mặt đường & mặt đất phía dưới đường chân trời
      ctx.fillStyle = '#22262b';
      ctx.fillRect(0, HZ, W, H - HZ);

      // Khối mặt đường hình thang Perspective Road
      const e = (RH * (H - HZ)) / CAMH;
      ctx.fillStyle = '#343a41';
      ctx.beginPath();
      ctx.moveTo(CX, HZ);
      ctx.lineTo(CX - e, H);
      ctx.lineTo(CX + e, H);
      ctx.fill();

      // Vạch kẻ đường di chuyển mô phỏng tốc độ xe
      if (!isPaused) {
        phaseRef.current = (phaseRef.current + dt * 6) % 8;
      }
      ctx.strokeStyle = '#e5e7eb';
      ctx.lineWidth = 2;
      [-1.85, 1.85].forEach((X) => {
        for (let z = 2 - phaseRef.current; z < 40; z += 8) {
          const a = Math.max(z, 1.6);
          const b = Math.max(z + 3, 1.6);
          if (z + 3 < 1.6) continue;
          const p = P(X, a);
          const q = P(X, b);
          ctx.beginPath();
          ctx.moveTo(p[0], p[1]);
          ctx.lineTo(q[0], q[1]);
          ctx.stroke();
        }
      });

      // 2. Vẽ 3 Vùng Giám Sát Cự Ly (Vùng trái, Vùng trước, Vùng phải - Tôn trọng Bật/Tắt)
      if (showZones) {
        const Zs = 2;
        const Ze = 32;
        const edges = {
          L: { a: -RH, b: -1.85, name: 'Vùng trái', col: '249, 115, 22', status: zoneLeft, active: activeZones.L !== false },
          F: { a: -1.85, b: 1.85, name: 'Vùng trước', col: '168, 85, 247', status: zoneFront, active: activeZones.F !== false },
          R: { a: 1.85, b: RH, name: 'Vùng phải', col: '34, 197, 94', status: zoneRight, active: activeZones.R !== false },
        };

        for (const k of ['L', 'F', 'R'] as const) {
          const { a, b, name, col, status, active } = edges[k];
          const pts = [P(a, Ze), P(b, Ze), P(b, Zs), P(a, Zs)];
          const lv = status?.lvl || 0;

          ctx.beginPath();
          pts.forEach((p, i) => (i === 0 ? ctx.moveTo(p[0], p[1]) : ctx.lineTo(p[0], p[1])));
          ctx.closePath();

          if (!active) {
            ctx.fillStyle = 'rgba(100, 116, 139, 0.05)';
            ctx.fill();
            ctx.setLineDash([6, 6]);
            ctx.strokeStyle = 'rgba(148, 163, 184, 0.35)';
            ctx.lineWidth = 1.5;
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.fillStyle = 'rgba(148, 163, 184, 0.55)';
            ctx.font = 'bold 12px sans-serif';
            ctx.fillText(`${name} (TẮT)`, pts[0][0] + 4, pts[0][1] - 4);
          } else {
            ctx.fillStyle =
              lv === 2
                ? 'rgba(239, 68, 68, 0.35)'
                : lv === 1
                ? 'rgba(245, 158, 11, 0.28)'
                : `rgba(${col}, 0.14)`;
            ctx.fill();

            ctx.strokeStyle = `rgb(${col})`;
            ctx.lineWidth = 2;
            ctx.stroke();

            ctx.fillStyle = `rgb(${col})`;
            ctx.font = 'bold 13px sans-serif';
            ctx.fillText(name, pts[0][0] + 4, pts[0][1] - 4);
          }
        }

        // 3. Vạch kẻ ngang ngưỡng cự ly cảnh báo (Vàng 8m, Đỏ 4m)
        [
          { d: warnThreshold, c: '#f59e0b' },
          { d: dangerThreshold, c: '#ef4444' },
        ].forEach(({ d, c }) => {
          const p = P(-RH, d);
          const q = P(RH, d);
          ctx.setLineDash([8, 6]);
          ctx.strokeStyle = c;
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(p[0], p[1]);
          ctx.lineTo(q[0], q[1]);
          ctx.stroke();
          ctx.setLineDash([]);

          ctx.fillStyle = c;
          ctx.font = 'bold 12px sans-serif';
          ctx.fillText(`${d} m`, W / 2 - 14, p[1] - 4);
        });

        // 3b. Vạch đếm lưu lượng Line Crossing (Tại Z = 12m)
        const lineZ = 12.0;
        const pLineL = P(-RH, lineZ);
        const pLineR = P(RH, lineZ);
        ctx.save();
        ctx.strokeStyle = '#06B6D4';
        ctx.lineWidth = 2.5;
        ctx.setLineDash([8, 6]);
        ctx.beginPath();
        ctx.moveTo(pLineL[0], pLineL[1]);
        ctx.lineTo(pLineR[0], pLineR[1]);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = '#06B6D4';
        ctx.font = 'bold 11px monospace, sans-serif';
        const inC = lineCrossings?.inCount || 0;
        const outC = lineCrossings?.outCount || 0;
        ctx.fillText(`━━━ LINE CROSSING ━━━ [IN: ${inC} ⬇ | OUT: ${outC} ⬆]`, W / 2 - 130, pLineL[1] - 5);
        ctx.restore();
      }

      // 4. Vẽ Khung Bounding Box Phương Tiện Đang Theo Dõi & Nhãn Vận Tốc
      trackedVehicles.forEach((o) => {
        const col =
          o.lvl === 2
            ? '#ef4444'
            : o.lvl === 1
            ? '#f59e0b'
            : CLS_MAP[o.cls]?.c || '#60a5fa';

        ctx.strokeStyle = col;
        ctx.lineWidth = o.lvl ? 3 : 2;
        ctx.strokeRect(o.x1, o.y1, o.x2 - o.x1, o.y2 - o.y1);

        const dirTag = o.direction === 'IN' ? ' ⬇IN' : o.direction === 'OUT' ? ' ⬆OUT' : '';
        const tag = `${o.vn} #${o.id} • ${o.dist.toFixed(1)}m • ${Math.round(Math.abs(o.speed))} km/h${dirTag}`;

        ctx.font = 'bold 12px sans-serif';
        const tw = ctx.measureText(tag).width + 10;
        const y = Math.max(0, o.y1 - 18);
        ctx.fillStyle = 'rgba(10, 12, 16, 0.88)';
        ctx.fillRect(o.x1, y, tw, 18);
        ctx.fillStyle = col;
        ctx.fillText(tag, o.x1 + 5, y + 13);
      });

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, [
    zoneLeft,
    zoneFront,
    zoneRight,
    warnThreshold,
    dangerThreshold,
    focalLength,
    showZones,
    trackedVehicles,
    isPaused,
    lineCrossings,
  ]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start select-none font-sans text-xs">
      {/* ── CỘT TRÁI (5 COLS): SÂN KHẤU MÔ PHỎNG / RADAR CỰ LY 3D (ĐÚNG NHƯ HÌNH BẠN YÊU CẦU) ── */}
      <div className="lg:col-span-5 xl:col-span-5 space-y-3">
        <div className="relative rounded-[12px] overflow-hidden bg-[#0A0D14] border border-[#242C3D] shadow-xl aspect-[3/4] max-h-[580px] w-full flex items-center justify-center">
          <canvas
            ref={canvasRef}
            width={540}
            height={720}
            className="w-full h-full object-contain block"
          />

          {/* Vùng phát quang cảnh báo góc sân khấu (Edge Glows) */}
          <div
            className={`absolute left-0 top-0 bottom-0 w-[24%] pointer-events-none transition-opacity duration-150 ${
              edgeLvlL === 2
                ? 'opacity-100 bg-gradient-to-r from-[rgba(239,68,68,0.85)] to-transparent animate-pulse'
                : edgeLvlL === 1
                ? 'opacity-100 bg-gradient-to-r from-[rgba(245,158,11,0.7)] to-transparent'
                : 'opacity-0'
            }`}
          />
          <div
            className={`absolute left-0 right-0 top-0 h-[20%] pointer-events-none transition-opacity duration-150 ${
              edgeLvlF === 2
                ? 'opacity-100 bg-gradient-to-b from-[rgba(239,68,68,0.85)] to-transparent animate-pulse'
                : edgeLvlF === 1
                ? 'opacity-100 bg-gradient-to-b from-[rgba(245,158,11,0.7)] to-transparent'
                : 'opacity-0'
            }`}
          />
          <div
            className={`absolute right-0 top-0 bottom-0 w-[24%] pointer-events-none transition-opacity duration-150 ${
              edgeLvlR === 2
                ? 'opacity-100 bg-gradient-to-l from-[rgba(239,68,68,0.85)] to-transparent animate-pulse'
                : edgeLvlR === 1
                ? 'opacity-100 bg-gradient-to-l from-[rgba(245,158,11,0.7)] to-transparent'
                : 'opacity-0'
            }`}
          />


        </div>

        <div className="text-[11px] text-[#667085] leading-relaxed bg-[#F8FAFC] p-2.5 rounded-[8px] border border-[#E4E9EF]">
          💡 <strong>Không gian ADAS 3D</strong>: Mô phỏng không gian cự ly theo tiêu cự camera. Vùng trái (cam), vùng trước (tím), vùng phải (xanh) và vạch đỏ {dangerThreshold}m, vàng {warnThreshold}m.
        </div>
      </div>

      {/* ── CỘT PHẢI (7 COLS): CÁC BẢNG ĐIỀU KHIỂN & BẢNG THEO DÕI CỰ LY ── */}
      <div className="lg:col-span-7 xl:col-span-7 space-y-3.5">
        {/* CARD 1: TRẠNG THÁI CÁC VÙNG */}
        <div className="bg-white rounded-[10px] border border-[#E4E9EF] p-4 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold text-[#16202A] uppercase tracking-wider">
              Trạng thái các vùng
            </h3>
            <span className="text-[11px] text-[#667085]">
              (Nhấn BẬT/TẮT để kích hoạt hoặc bỏ qua từng vùng)
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Vùng trái */}
            <div
              className={`bg-[#F8FAFC] rounded-[8px] p-3 border-l-4 ${getZoneBorderColor(zoneLeft, activeZones.L !== false)} border border-r-[#E4E9EF] border-y-[#E4E9EF] transition-colors`}
            >
              <div className="flex items-center justify-between">
                <span className="block text-[11px] font-semibold text-[#667085] uppercase tracking-wide">
                  Vùng trái
                </span>
                {toggleZone && (
                  <button
                    type="button"
                    onClick={() => toggleZone('L')}
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold cursor-pointer transition-colors ${
                      activeZones.L !== false
                        ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                        : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                    }`}
                  >
                    {activeZones.L !== false ? '● BẬT' : '○ TẮT'}
                  </button>
                )}
              </div>
              <span className="text-xl font-extrabold text-[#16202A] block mt-1">
                {formatZoneSpan(zoneLeft, activeZones.L !== false)}
              </span>
            </div>

            {/* Phía trước */}
            <div
              className={`bg-[#F8FAFC] rounded-[8px] p-3 border-l-4 ${getZoneBorderColor(zoneFront, activeZones.F !== false)} border border-r-[#E4E9EF] border-y-[#E4E9EF] transition-colors`}
            >
              <div className="flex items-center justify-between">
                <span className="block text-[11px] font-semibold text-[#667085] uppercase tracking-wide">
                  Phía trước
                </span>
                {toggleZone && (
                  <button
                    type="button"
                    onClick={() => toggleZone('F')}
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold cursor-pointer transition-colors ${
                      activeZones.F !== false
                        ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                        : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                    }`}
                  >
                    {activeZones.F !== false ? '● BẬT' : '○ TẮT'}
                  </button>
                )}
              </div>
              <span className="text-xl font-extrabold text-[#16202A] block mt-1">
                {formatZoneSpan(zoneFront, activeZones.F !== false)}
              </span>
            </div>

            {/* Vùng phải */}
            <div
              className={`bg-[#F8FAFC] rounded-[8px] p-3 border-l-4 ${getZoneBorderColor(zoneRight, activeZones.R !== false)} border border-r-[#E4E9EF] border-y-[#E4E9EF] transition-colors`}
            >
              <div className="flex items-center justify-between">
                <span className="block text-[11px] font-semibold text-[#667085] uppercase tracking-wide">
                  Vùng phải
                </span>
                {toggleZone && (
                  <button
                    type="button"
                    onClick={() => toggleZone('R')}
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold cursor-pointer transition-colors ${
                      activeZones.R !== false
                        ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                        : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                    }`}
                  >
                    {activeZones.R !== false ? '● BẬT' : '○ TẮT'}
                  </button>
                )}
              </div>
              <span className="text-xl font-extrabold text-[#16202A] block mt-1">
                {formatZoneSpan(zoneRight, activeZones.R !== false)}
              </span>
            </div>
          </div>
        </div>

        {/* ── CARD: BỘ ĐẾM LƯU LƯỢNG & ĐẾM XE QUA VẠCH (LINE CROSSING: IN / OUT & REALTIME SPEED) ── */}
        <div className="bg-white rounded-[10px] border border-[#E4E9EF] p-4 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-[#16202A] uppercase tracking-wider flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#06B6D4] animate-pulse" />
                Lưu lượng & Đếm xe qua vạch (Line Crossing)
              </h3>
              <p className="text-[11px] text-[#667085] mt-0.5">
                Theo dõi vận tốc (km/h) & đếm số lượng phương tiện, người đi bộ cắt qua vạch kiểm soát
              </p>
            </div>
            {onResetLineCrossings && (
              <button
                onClick={onResetLineCrossings}
                className="px-2.5 py-1 text-[11px] font-semibold text-[#344054] hover:text-[#175CD3] hover:bg-[#EFF4FF] border border-[#D0D7DE] rounded-[6px] transition-colors cursor-pointer"
                title="Đặt lại bộ đếm IN/OUT về 0"
              >
                Đặt lại đếm
              </button>
            )}
          </div>

          {/* 3 Thẻ thống kê lớn: IN • OUT • TỔNG */}
          <div className="grid grid-cols-3 gap-2.5">
            <div className="bg-[#ECFDF3] border border-[#ABEFC6] rounded-[8px] p-2.5 text-center">
              <span className="text-[10px] uppercase font-bold text-[#067647] block tracking-wide">
                ⬇ IN (Tiến lại)
              </span>
              <span className="text-2xl font-black text-[#027A48] font-mono block mt-0.5">
                {lineCrossings?.inCount || 0}
              </span>
              <span className="text-[10px] text-[#067647]/80 block mt-0.5">
                Hướng đi vào
              </span>
            </div>

            <div className="bg-[#EFF8FF] border border-[#B2DDFF] rounded-[8px] p-2.5 text-center">
              <span className="text-[10px] uppercase font-bold text-[#175CD3] block tracking-wide">
                ⬆ OUT (Đi xa)
              </span>
              <span className="text-2xl font-black text-[#175CD3] font-mono block mt-0.5">
                {lineCrossings?.outCount || 0}
              </span>
              <span className="text-[10px] text-[#175CD3]/80 block mt-0.5">
                Hướng đi ra
              </span>
            </div>

            <div className="bg-[#F8F9FC] border border-[#D0D5DD] rounded-[8px] p-2.5 text-center">
              <span className="text-[10px] uppercase font-bold text-[#344054] block tracking-wide">
                Tổng Lưu Lượng
              </span>
              <span className="text-2xl font-black text-[#101828] font-mono block mt-0.5">
                {lineCrossings?.totalCount || 0}
              </span>
              <span className="text-[10px] text-[#667085] block mt-0.5">
                Đã qua vạch
              </span>
            </div>
          </div>

          {/* Bảng chi tiết Line Crossings theo nhóm đối tượng & Dòng tốc độ thời gian thực */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {/* Cột 1: Chi tiết phân loại Line Crossings */}
            <div className="bg-[#F8FAFC] border border-[#E4E9EF] rounded-[8px] p-3 space-y-2">
              <span className="text-[11px] font-bold text-[#16202A] block uppercase tracking-wider">
                Line Crossings Chi Tiết
              </span>
              <div className="space-y-1.5 text-xs font-mono">
                <div className="text-[#175CD3] font-semibold border-b border-[#E4E9EF] pb-1 flex justify-between">
                  <span>Out:</span>
                  <span className="font-bold">{lineCrossings?.outCount || 0}</span>
                </div>
                <div className="pl-3 space-y-0.5 text-[11px] text-[#475467]">
                  <div className="flex justify-between">
                    <span>motor:</span>
                    <span className="font-semibold text-[#16202A]">{lineCrossings?.outByClass?.motor || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>people:</span>
                    <span className="font-semibold text-[#16202A]">{lineCrossings?.outByClass?.people || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>car:</span>
                    <span className="font-semibold text-[#16202A]">{lineCrossings?.outByClass?.car || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>truck / bus:</span>
                    <span className="font-semibold text-[#16202A]">
                      {(lineCrossings?.outByClass?.truck || 0) + (lineCrossings?.outByClass?.bus || 0)}
                    </span>
                  </div>
                </div>

                <div className="text-[#067647] font-semibold border-b border-[#E4E9EF] pb-1 pt-1 flex justify-between">
                  <span>In:</span>
                  <span className="font-bold">{lineCrossings?.inCount || 0}</span>
                </div>
                <div className="pl-3 space-y-0.5 text-[11px] text-[#475467]">
                  <div className="flex justify-between">
                    <span>motor:</span>
                    <span className="font-semibold text-[#16202A]">{lineCrossings?.inByClass?.motor || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>people:</span>
                    <span className="font-semibold text-[#16202A]">{lineCrossings?.inByClass?.people || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>car:</span>
                    <span className="font-semibold text-[#16202A]">{lineCrossings?.inByClass?.car || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>truck / bus:</span>
                    <span className="font-semibold text-[#16202A]">
                      {(lineCrossings?.inByClass?.truck || 0) + (lineCrossings?.inByClass?.bus || 0)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Cột 2: Danh sách vận tốc thời gian thực (Speed Stream) */}
            <div className="bg-[#0C111D] border border-white/10 rounded-[8px] p-3 text-white flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-white/10 pb-1.5 mb-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-white/80">
                    Tốc độ thời gian thực
                  </span>
                  <span className="text-[10px] font-mono text-[#10B981]">
                    ● LIVE
                  </span>
                </div>

                <div className="space-y-1 font-mono text-xs max-h-[145px] overflow-y-auto pr-1">
                  {trackedVehicles.length === 0 ? (
                    <div className="text-white/40 text-[11px] py-4 text-center">
                      Đang đợi đối tượng xuất hiện...
                    </div>
                  ) : (
                    trackedVehicles.map((v) => {
                      const tagCls = v.cls === 'motorbike' ? 'motor' : v.cls === 'person' ? 'people' : v.cls;
                      const spText = `${Math.round(Math.abs(v.speed))} km/h`;
                      const dirBadge = v.direction === 'IN' ? '⬇ in' : v.direction === 'OUT' ? '⬆ out' : '';

                      return (
                        <div key={`sp-${v.id}`} className="flex items-center justify-between py-0.5 border-b border-white/5">
                          <span className="text-[#38BDF8] font-bold">
                            {tagCls} #{v.id}
                          </span>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white">
                              {spText}
                            </span>
                            {dirBadge && (
                              <span className={`text-[9px] px-1 rounded font-bold ${
                                v.direction === 'IN' ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40' : 'bg-sky-950 text-sky-300 border border-sky-500/40'
                              }`}>
                                {dirBadge}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              <div className="pt-2 border-t border-white/10 text-[10px] text-white/50 flex justify-between font-mono">
                <span>Ước lượng: Homography + Calib</span>
                <span>Vạch cắt: 60%</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-[10px] border border-[#E4E9EF] p-4 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-[#16202A] uppercase tracking-wider">
              Cài đặt & Hồ sơ ADAS
            </h3>
            {dynamicSafeDistance != null && (
              <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold bg-[#E0F2FE] text-[#0369A1] border border-[#BAE6FD]">
                Chuẩn 2s: ~{Math.round(dynamicSafeDistance)}m
              </span>
            )}
          </div>

          {/* Hồ sơ lái thích ứng theo tốc độ xe */}
          <div className="p-2.5 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-[#1E293B] uppercase tracking-wide">
                Chế độ thích ứng cự ly
              </span>
              <span className="text-[10px] text-[#64748B]">
                {drivingProfile === 'urban'
                  ? '🚗 Đô thị / Phố đông'
                  : drivingProfile === 'highway'
                  ? '🛣️ Cao tốc / Đường trường'
                  : '🔄 Tự động (Theo tốc độ)'}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-1.5">
              <button
                type="button"
                onClick={() => setDrivingProfile?.('auto')}
                className={`px-2 py-1.5 rounded-md text-[11px] font-semibold transition-all cursor-pointer text-center ${
                  drivingProfile === 'auto'
                    ? 'bg-[#175CD3] text-white shadow-xs font-bold'
                    : 'bg-white border border-[#E2E8F0] text-[#475467] hover:bg-slate-50'
                }`}
                title="Tự động co giãn cự ly an toàn và ngưỡng cảnh báo theo tốc độ di chuyển thực tế"
              >
                🔄 Tự động
              </button>

              <button
                type="button"
                onClick={() => setDrivingProfile?.('urban')}
                className={`px-2 py-1.5 rounded-md text-[11px] font-semibold transition-all cursor-pointer text-center ${
                  drivingProfile === 'urban'
                    ? 'bg-[#175CD3] text-white shadow-xs font-bold'
                    : 'bg-white border border-[#E2E8F0] text-[#475467] hover:bg-slate-50'
                }`}
                title="Đô thị: Chống hú còi khi dừng đèn đỏ/kẹt xe, cự ly bám đuôi ngắn hơn"
              >
                🚗 Đô thị
              </button>

              <button
                type="button"
                onClick={() => setDrivingProfile?.('highway')}
                className={`px-2 py-1.5 rounded-md text-[11px] font-semibold transition-all cursor-pointer text-center ${
                  drivingProfile === 'highway'
                    ? 'bg-[#175CD3] text-white shadow-xs font-bold'
                    : 'bg-white border border-[#E2E8F0] text-[#475467] hover:bg-slate-50'
                }`}
                title="Cao tốc: Mở rộng vùng quét lên 35-65m, cảnh báo sớm phanh gấp"
              >
                🛣️ Cao tốc
              </button>
            </div>

            <div className="flex items-center justify-between text-[10px] text-[#64748B] pt-0.5">
              <span>Ngưỡng hiệu dụng:</span>
              <span className="font-mono">
                Vàng: <strong className="text-[#D97706]">{effectiveWarnDist ? effectiveWarnDist.toFixed(1) : warnThreshold}m</strong>
                {' • '}
                Đỏ: <strong className="text-[#DC2626]">{effectiveDangerDist ? effectiveDangerDist.toFixed(1) : dangerThreshold}m</strong>
              </span>
            </div>
          </div>

          {/* Slider 1: Cảnh báo vàng */}
          <div className="space-y-1">
            <div className="flex justify-between items-center text-xs">
              <span className="text-[#475467] font-medium">Cảnh báo vàng khi gần hơn</span>
              <span className="font-bold text-[#D97706] font-mono">{warnThreshold} m</span>
            </div>
            <input
              type="range"
              min="3"
              max="20"
              step="0.5"
              value={warnThreshold}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                setWarnThreshold(val);
                if (dangerThreshold > val) setDangerThreshold(val);
              }}
              className="w-full h-1.5 bg-[#E4E9EF] rounded-lg appearance-none cursor-pointer accent-[#F59E0B]"
            />
          </div>

          {/* Slider 2: Cảnh báo đỏ */}
          <div className="space-y-1">
            <div className="flex justify-between items-center text-xs">
              <span className="text-[#475467] font-medium">Cảnh báo đỏ khi gần hơn</span>
              <span className="font-bold text-[#DC2626] font-mono">{dangerThreshold} m</span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              step="0.5"
              value={dangerThreshold}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                if (val <= warnThreshold) setDangerThreshold(val);
              }}
              className="w-full h-1.5 bg-[#E4E9EF] rounded-lg appearance-none cursor-pointer accent-[#EF4444]"
            />
          </div>

          {/* Slider 3: Tiêu cự camera */}
          <div className="space-y-1">
            <div className="flex justify-between items-center text-xs">
              <span className="text-[#475467] font-medium">Tiêu cự camera (px)</span>
              <span className="font-bold text-[#175CD3] font-mono">{focalLength}</span>
            </div>
            <input
              type="range"
              min="300"
              max="900"
              step="10"
              value={focalLength}
              onChange={(e) => setFocalLength(parseInt(e.target.value, 10))}
              className="w-full h-1.5 bg-[#E4E9EF] rounded-lg appearance-none cursor-pointer accent-[#175CD3]"
            />
          </div>

          {/* Tùy chọn độc lập 3 vùng cảnh báo va chạm (Trái - Trước - Phải) */}
          <div className="pt-2 border-t border-[#F1F4F7] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#16202A] uppercase tracking-wide">
                Bật/Tắt Vùng Cảnh Báo (3 Phía)
              </span>
              <span className="text-[11px] text-[#667085]">
                {Number(activeZones.L !== false) + Number(activeZones.F !== false) + Number(activeZones.R !== false)}/3 vùng đang bật
              </span>
            </div>

            {/* 3 Nút bấm độc lập */}
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => toggleZone?.('L')}
                className={`flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
                  activeZones.L !== false
                    ? 'bg-[#EFF8FF] border-[#B2DDFF] text-[#175CD3]'
                    : 'bg-[#F8FAFC] border-[#E4E9EF] text-[#98A2B3]'
                }`}
              >
                <span>⬅</span>
                <span>Vùng Trái</span>
                <span className={`text-[9px] px-1 rounded font-bold ${
                  activeZones.L !== false ? 'bg-[#175CD3] text-white' : 'bg-gray-200 text-gray-500'
                }`}>
                  {activeZones.L !== false ? 'BẬT' : 'TẮT'}
                </span>
              </button>

              <button
                type="button"
                onClick={() => toggleZone?.('F')}
                className={`flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
                  activeZones.F !== false
                    ? 'bg-[#EFF8FF] border-[#B2DDFF] text-[#175CD3]'
                    : 'bg-[#F8FAFC] border-[#E4E9EF] text-[#98A2B3]'
                }`}
              >
                <span>▲</span>
                <span>Phía Trước</span>
                <span className={`text-[9px] px-1 rounded font-bold ${
                  activeZones.F !== false ? 'bg-[#175CD3] text-white' : 'bg-gray-200 text-gray-500'
                }`}>
                  {activeZones.F !== false ? 'BẬT' : 'TẮT'}
                </span>
              </button>

              <button
                type="button"
                onClick={() => toggleZone?.('R')}
                className={`flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
                  activeZones.R !== false
                    ? 'bg-[#EFF8FF] border-[#B2DDFF] text-[#175CD3]'
                    : 'bg-[#F8FAFC] border-[#E4E9EF] text-[#98A2B3]'
                }`}
              >
                <span>➡</span>
                <span>Vùng Phải</span>
                <span className={`text-[9px] px-1 rounded font-bold ${
                  activeZones.R !== false ? 'bg-[#175CD3] text-white' : 'bg-gray-200 text-gray-500'
                }`}>
                  {activeZones.R !== false ? 'BẬT' : 'TẮT'}
                </span>
              </button>
            </div>

            {/* Nút Preset cấu hình nhanh theo nhu cầu thực tế */}
            <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px]">
              <span className="text-[#667085] font-medium mr-0.5">Mẫu nhanh:</span>
              <button
                type="button"
                onClick={() => setAllZones?.({ L: false, F: true, R: false })}
                className="px-2 py-0.5 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium cursor-pointer transition-colors"
                title="Chỉ cảnh báo xe phía trước, tắt bên trái và phải"
              >
                Chỉ phía trước
              </button>
              <button
                type="button"
                onClick={() => setAllZones?.({ L: false, F: true, R: true })}
                className="px-2 py-0.5 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium cursor-pointer transition-colors"
                title="Cảnh báo phía trước và bên phải, tắt bên trái"
              >
                Trước + Phải
              </button>
              <button
                type="button"
                onClick={() => setAllZones?.({ L: true, F: true, R: false })}
                className="px-2 py-0.5 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium cursor-pointer transition-colors"
                title="Cảnh báo phía trước và bên trái, tắt bên phải"
              >
                Trước + Trái
              </button>
              <button
                type="button"
                onClick={() => setAllZones?.({ L: true, F: true, R: true })}
                className="px-2 py-0.5 rounded bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold cursor-pointer transition-colors"
                title="Bật cả 3 phía (mặc định)"
              >
                Bật cả 3 phía
              </button>
            </div>
          </div>

          {/* Checkboxes */}
          <div className="space-y-1.5 pt-2 border-t border-[#F1F4F7]">
            <label className="flex items-center gap-2 text-xs text-[#344054] cursor-pointer">
              <input
                type="checkbox"
                checked={showZones}
                onChange={(e) => setShowZones(e.target.checked)}
                className="rounded border-[#D0D7DE] text-[#175CD3] focus:ring-0 cursor-pointer"
              />
              <span>Hiện vùng và vạch khoảng cách</span>
            </label>

            <label className="flex items-center gap-2 text-xs text-[#344054] cursor-pointer">
              <input
                type="checkbox"
                checked={soundEnabled}
                onChange={(e) => setSoundEnabled(e.target.checked)}
                className="rounded border-[#D0D7DE] text-[#175CD3] focus:ring-0 cursor-pointer"
              />
              <span>Bật âm báo khi nguy hiểm</span>
            </label>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#F1F4F7]">
            {onTogglePause && (
              <button
                onClick={onTogglePause}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] border border-[#D0D7DE] bg-[#F8FAFC] hover:bg-[#F1F4F7] text-xs font-semibold text-[#344054] transition-colors cursor-pointer"
              >
                {isPaused ? <Play className="w-3.5 h-3.5 fill-current" /> : <Pause className="w-3.5 h-3.5" />}
                <span>{isPaused ? 'Tiếp tục' : 'Tạm dừng'}</span>
              </button>
            )}

            {onUploadVideo && (
              <button
                onClick={onUploadVideo}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] border border-[#D0D7DE] bg-[#F8FAFC] hover:bg-[#F1F4F7] text-xs font-semibold text-[#344054] transition-colors cursor-pointer"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Nạp video nền</span>
              </button>
            )}

            <button
              onClick={() => {
                setSimMode(!simMode);
                if (onResetSim) onResetSim();
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] border text-xs font-semibold transition-colors cursor-pointer ${
                simMode
                  ? 'border-[#175CD3] bg-[#EFF4FF] text-[#175CD3]'
                  : 'border-[#D0D7DE] bg-[#F8FAFC] hover:bg-[#F1F4F7] text-[#344054]'
              }`}
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>{simMode ? 'Đang bật mô phỏng' : 'Về mô phỏng'}</span>
            </button>
          </div>
        </div>

        {/* CARD 3: PHƯƠNG TIỆN ĐANG THEO DÕI */}
        <div className="bg-white rounded-[10px] border border-[#E4E9EF] p-4 shadow-xs">
          <h3 className="text-xs font-bold text-[#16202A] mb-3 uppercase tracking-wider">
            Phương tiện đang theo dõi ({sortedRows.length})
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-[#E4E9EF] text-[#667085] font-semibold text-[11px]">
                  <th className="pb-2 pl-1">Loại</th>
                  <th className="pb-2">Cự ly</th>
                  <th className="pb-2">Vùng</th>
                  <th className="pb-2">Hướng</th>
                  <th className="pb-2">Vận tốc</th>
                  <th className="pb-2 text-center">TTC</th>
                  <th className="pb-2 text-right pr-1">Tiếp cận</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F1F4F7]">
                {sortedRows.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-4 text-center text-[#98A2B3]">
                      Chưa có phương tiện trong vùng theo dõi
                    </td>
                  </tr>
                ) : (
                  sortedRows.map((o) => {
                    const dotColor = o.lvl === 2 ? '#EF4444' : o.lvl === 1 ? '#F59E0B' : '#12B76A';
                    return (
                      <tr key={`trk-${o.id}`} className="hover:bg-[#F8FAFC] transition-colors">
                        <td className="py-2 pl-1 font-medium text-[#16202A] flex items-center gap-1.5">
                          <span
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{ backgroundColor: dotColor }}
                          />
                          <span>{o.vn} #{o.id}</span>
                        </td>
                        <td className="py-2 font-mono font-bold text-[#16202A]">
                          {o.dist.toFixed(1)} m
                        </td>
                        <td className="py-2 text-[#475467]">
                          <span className="px-1.5 py-0.5 rounded bg-[#F1F4F7] text-[10px] font-semibold">
                            {o.zone}
                          </span>
                        </td>
                        <td className="py-2">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            o.direction === 'IN'
                              ? 'bg-emerald-100 text-emerald-700 border border-emerald-300'
                              : o.direction === 'OUT'
                              ? 'bg-sky-100 text-sky-700 border border-sky-300'
                              : 'bg-gray-100 text-gray-600'
                          }`}>
                            {o.direction === 'IN' ? '⬇ IN' : o.direction === 'OUT' ? '⬆ OUT' : '•'}
                          </span>
                        </td>
                        <td className="py-2 font-mono font-bold text-[#16202A]">
                          {Math.round(Math.abs(o.speed))} km/h
                        </td>
                        <td className="py-2 text-center">
                          {o.ttc != null && o.ttc > 0 && o.ttc <= 10 ? (
                            <span
                              className={`px-1.5 py-0.5 rounded font-mono text-[10px] font-bold ${
                                o.ttc <= 1.8
                                  ? 'bg-red-100 text-red-700 border border-red-300 animate-pulse'
                                  : o.ttc <= 3.2
                                  ? 'bg-amber-100 text-amber-700 border border-amber-300'
                                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              }`}
                            >
                              {o.ttc.toFixed(1)}s
                            </span>
                          ) : (
                            <span className="text-[#94A3B8] font-mono text-[10px]">—</span>
                          )}
                        </td>
                        <td className="py-2 text-right pr-1">
                          {o.approachState === 'CUT_IN' ? (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-extrabold bg-red-600 text-white animate-bounce">
                              🚨 TẠT ĐẦU
                            </span>
                          ) : o.approachDesc ? (
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                                o.approachState === 'CLOSING_IN'
                                  ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                  : o.approachState === 'PULLING_AWAY'
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {o.approachDesc}
                            </span>
                          ) : (
                            <span className="text-[#94A3B8] text-[10px]">Ổn định</span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
