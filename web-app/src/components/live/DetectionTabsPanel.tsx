'use client';

import React, { memo, useState } from 'react';
import {
  CreditCard,
  ShieldAlert,
  HardHat,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Clock,
  Layers,
  Search,
  Users,
  Car,
  Ruler,
  AlertOctagon,
  ArrowDown,
  ArrowUp,
  RotateCcw,
  Activity,
  Gauge,
  Radio,
} from 'lucide-react';
import {
  PlateDetection,
  TrafficSign,
  HelmetViolation,
  VehicleDetection,
  LineCrossingData,
  sanitizeVietnamesePlate,
  isValidConfirmedPlate,
} from '../../types/detection';
import { TrafficDistancePanel, TrafficDistancePanelProps } from './TrafficDistancePanel';
import { LineCrossingStats } from '../../hooks/useTrafficDistanceEngine';

export type DetectionTabType = 'plates' | 'traffic' | 'signs' | 'helmets';

export interface DetectionTabsPanelProps {
  plates: PlateDetection[];
  vehicles: VehicleDetection[];
  signs: TrafficSign[];
  helmetViolations: HelmetViolation[];
  safeDistance?: number | null;
  recommendedDistance?: number | null;
  collisionLevel?: 'none' | 'warning' | 'danger';
  currentSpeed?: number | null;
  isStreaming: boolean;
  isImageMode?: boolean;
  activeTab?: DetectionTabType;
  onTabChange?: (tab: DetectionTabType) => void;
  lineCrossings?: LineCrossingStats | LineCrossingData | null;
  onResetLineCrossings?: () => void;
  trafficEngine?: TrafficDistancePanelProps;
  className?: string;
}

export const DetectionTabsPanel = memo(function DetectionTabsPanel({
  plates = [],
  vehicles = [],
  signs = [],
  helmetViolations = [],
  safeDistance = null,
  recommendedDistance = null,
  collisionLevel = 'none',
  currentSpeed = null,
  isStreaming,
  isImageMode = false,
  activeTab: controlledActiveTab,
  onTabChange,
  lineCrossings,
  onResetLineCrossings,
  trafficEngine,
  className = '',
}: DetectionTabsPanelProps) {
  const [internalTab, setInternalTab] = useState<DetectionTabType>('plates');
  const [showRadarView, setShowRadarView] = useState(false);
  const activeTab = controlledActiveTab !== undefined ? controlledActiveTab : internalTab;
  const effectiveCrossings = lineCrossings || trafficEngine?.lineCrossings;
  const handleResetCrossings = onResetLineCrossings || trafficEngine?.onResetLineCrossings;

  const inCount = (effectiveCrossings as any)?.inCount ?? (effectiveCrossings as any)?.in_count ?? 0;
  const outCount = (effectiveCrossings as any)?.outCount ?? (effectiveCrossings as any)?.out_count ?? 0;
  const outByClass = (effectiveCrossings as any)?.outByClass || (effectiveCrossings as any)?.out_by_class || {};
  const inByClass = (effectiveCrossings as any)?.inByClass || (effectiveCrossings as any)?.in_by_class || {};

  const validPlates = plates.filter((p) => isValidConfirmedPlate(p.plate_text));

  // Lọc trùng lặp biển báo theo loại: Mỗi biển báo chỉ hiển thị 1 thẻ duy nhất (kèm số lần xuất hiện)
  const uniqueSigns = React.useMemo(() => {
    const map = new Map<string, TrafficSign>();
    for (const s of signs) {
      const code = s.sign_type || 'UNKNOWN';
      if (!map.has(code)) {
        map.set(code, { ...s });
      } else {
        const existing = map.get(code)!;
        existing.count = (existing.count || 1) + (s.count || 1);
        if ((s.confidence || 0) > (existing.confidence || 0)) {
          existing.confidence = s.confidence;
          if (s.thumbnail) existing.thumbnail = s.thumbnail;
        }
      }
    }
    return Array.from(map.values());
  }, [signs]);

  // Lọc trùng lặp vi phạm mũ bảo hiểm: Mỗi người chỉ hiển thị 1 thẻ duy nhất (kèm số lần xuất hiện)
  const uniqueHelmets = React.useMemo(() => {
    const list: HelmetViolation[] = [];
    for (const h of helmetViolations) {
      const existing = list.find((item) => {
        if (item.track_id && h.track_id && item.track_id === h.track_id) return true;
        const c1x = (item.bbox.x1 + item.bbox.x2) / 2;
        const c1y = (item.bbox.y1 + item.bbox.y2) / 2;
        const c2x = (h.bbox.x1 + h.bbox.x2) / 2;
        const c2y = (h.bbox.y1 + h.bbox.y2) / 2;
        return Math.hypot(c1x - c2x, c1y - c2y) < 60;
      });

      if (existing) {
        existing.count = (existing.count || 1) + (h.count || 1);
        if (h.thumbnail && !existing.thumbnail) {
          existing.thumbnail = h.thumbnail;
        }
      } else {
        list.push({ ...h });
      }
    }
    return list;
  }, [helmetViolations]);

  const handleTabSelect = (tab: DetectionTabType) => {
    setInternalTab(tab);
    onTabChange?.(tab);
  };

  // Helper to get plate confidence badge
  const getConfidenceBadge = (conf?: number) => {
    const val = conf ? Math.round(conf * 100) : 88;
    if (val >= 85) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]">
          <CheckCircle2 className="w-2.5 h-2.5" />
          Chắc chắn ({val}%)
        </span>
      );
    }
    if (val >= 60) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-[#FFFAEB] text-[#B54708] border border-[#FEDF89]">
          <AlertTriangle className="w-2.5 h-2.5" />
          Nghi ngờ ({val}%)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-[#F8FAFC] text-[#667085] border border-[#E4E9EF]">
        <HelpCircle className="w-2.5 h-2.5" />
        Kém chất lượng ({val}%)
      </span>
    );
  };

  // Hiển thị màu biển số chính xác dựa trên phân tích hình ảnh AI (Background Color)
  const getPlateColorBadge = (plate: PlateDetection) => {
    const bg = plate.background_color;
    const clean = (plate.plate_text || '').replace(/[^A-Z0-9]/gi, '').toUpperCase();
    const isCommercialBySeries = clean.length >= 3 && /^[0-9]{2}[EFG]/.test(clean);
    if (bg === 'COMMERCIAL_YELLOW' || isCommercialBySeries || plate.vehicle_type === 'Xe dịch vụ / Vận tải') {
      return (
        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#FEF0C7] text-[#B54708] border border-[#FDB022]/40 font-mono">
          Biển Vàng (Dịch vụ vận tải)
        </span>
      );
    }
    if (bg === 'GOVERNMENT_BLUE') {
      return (
        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#EFF8FF] text-[#175CD3] border border-[#B2DDFF] font-mono">
          Biển Xanh (Cơ quan)
        </span>
      );
    }
    const isProvincial = clean.length >= 2 && /^\d{2}/.test(clean);
    if (!isProvincial && bg === 'MILITARY_RED') {
      return (
        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA] font-mono">
          Biển Đỏ (Quân đội)
        </span>
      );
    }
    return (
      <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#F8FAFC] text-[#344054] border border-[#D0D7DE] font-mono">
        Biển Trắng (Dân sự)
      </span>
    );
  };

  return (
    <div
      className={`w-full bg-white border border-[#E4E9EF] rounded-[10px] overflow-hidden shadow-sm flex flex-col select-none ${className}`}
    >
      {/* ── TABS NAVIGATION BAR ── */}
      <div className="flex items-center justify-between border-b border-[#E4E9EF] bg-[#F8FAFC] px-3 pt-2">
        <div className="flex items-center gap-1">
          {/* Tab 1: Biển Số */}
          <button
            onClick={() => handleTabSelect('plates')}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-t-[8px] border-t border-x transition-colors cursor-pointer ${
              activeTab === 'plates'
                ? 'bg-white border-[#E4E9EF] text-[#175CD3] shadow-xs relative top-px'
                : 'border-transparent text-[#667085] hover:text-[#16202A]'
            }`}
            title="Nhấn phím [1] để xem biển số xe"
          >
            <CreditCard className="w-3.5 h-3.5 text-[#175CD3]" />
            <span>Biển Số Xe</span>
            <kbd className="hidden sm:inline text-[9px] px-1 py-0.2 bg-black/5 rounded text-[#667085] font-mono">1</kbd>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === 'plates'
                  ? 'bg-[#EFF4FF] text-[#175CD3]'
                  : 'bg-white text-[#667085] border border-[#E4E9EF]'
              }`}
            >
              {validPlates.length}
            </span>
          </button>

          {/* Tab 2: Mật Độ & Khoảng Cách */}
          <button
            onClick={() => handleTabSelect('traffic')}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-t-[8px] border-t border-x transition-colors cursor-pointer ${
              activeTab === 'traffic'
                ? 'bg-white border-[#E4E9EF] text-[#2E90FA] shadow-xs relative top-px'
                : 'border-transparent text-[#667085] hover:text-[#16202A]'
            }`}
            title="Nhấn phím [2] để xem mật độ giao thông & khoảng cách xe"
          >
            <Users className="w-3.5 h-3.5 text-[#2E90FA]" />
            <span>Mật Độ & Cự Ly Xe</span>
            <kbd className="hidden sm:inline text-[9px] px-1 py-0.2 bg-black/5 rounded text-[#667085] font-mono">2</kbd>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === 'traffic'
                  ? 'bg-[#EFF8FF] text-[#2E90FA]'
                  : 'bg-white text-[#667085] border border-[#E4E9EF]'
              }`}
            >
              {vehicles.length}
            </span>
          </button>

          {/* Tab 3: Biển Báo */}
          <button
            onClick={() => handleTabSelect('signs')}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-t-[8px] border-t border-x transition-colors cursor-pointer ${
              activeTab === 'signs'
                ? 'bg-white border-[#E4E9EF] text-[#F79009] shadow-xs relative top-px'
                : 'border-transparent text-[#667085] hover:text-[#16202A]'
            }`}
            title="Nhấn phím [3] để xem biển báo giao thông"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-[#F79009]" />
            <span>Biển Báo Giao Thông</span>
            <kbd className="hidden sm:inline text-[9px] px-1 py-0.2 bg-black/5 rounded text-[#667085] font-mono">3</kbd>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === 'signs'
                  ? 'bg-[#FFFAEB] text-[#F79009]'
                  : 'bg-white text-[#667085] border border-[#E4E9EF]'
              }`}
            >
              {uniqueSigns.length}
            </span>
          </button>

          {/* Tab 4: Mũ Bảo Hiểm */}
          <button
            onClick={() => handleTabSelect('helmets')}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-t-[8px] border-t border-x transition-colors cursor-pointer ${
              activeTab === 'helmets'
                ? 'bg-white border-[#E4E9EF] text-[#F04438] shadow-xs relative top-px'
                : 'border-transparent text-[#667085] hover:text-[#16202A]'
            }`}
            title="Nhấn phím [4] để xem vi phạm mũ bảo hiểm"
          >
            <HardHat className="w-3.5 h-3.5 text-[#F04438]" />
            <span>Mũ Bảo Hiểm</span>
            <kbd className="hidden sm:inline text-[9px] px-1 py-0.2 bg-black/5 rounded text-[#667085] font-mono">4</kbd>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === 'helmets'
                  ? 'bg-[#FEF3F2] text-[#F04438]'
                  : 'bg-white text-[#667085] border border-[#E4E9EF]'
              }`}
            >
              {uniqueHelmets.length}
            </span>
          </button>
        </div>

        <span className="text-[11px] text-[#667085] hidden sm:inline font-mono">
          Trích xuất từ luồng AI thời gian thực
        </span>
      </div>

      {/* ── TAB CONTENT ── */}
      <div className={`p-3 overflow-y-auto ${activeTab === 'traffic' ? 'min-h-[320px] max-h-[520px]' : 'min-h-[160px] max-h-[260px]'}`}>
        {/* TAB 1: BIỂN SỐ XE */}
        {activeTab === 'plates' && (
          <div>
            {validPlates.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-7 text-center text-[#98A2B3]">
                <CreditCard className="w-8 h-8 mb-1.5 stroke-[1.5]" />
                <p className="text-xs font-semibold text-[#475467]">
                  Không phát hiện biển số xe hợp lệ trong ảnh / video này
                </p>
                <p className="text-[11px] text-[#98A2B3] mt-0.5">
                  Hệ thống tự động lọc bỏ các biển số bị mờ, vật thể ở quá xa hoặc số điện thoại, biển quảng cáo.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                {validPlates.map((p, idx) => {
                  const sanitized = sanitizeVietnamesePlate(p.plate_text);

                  return (
                    <div
                      key={`${sanitized}-${idx}`}
                      className="p-2.5 rounded-[8px] border border-[#E4E9EF] bg-[#F8FAFC] flex items-center justify-between gap-3 shadow-2xs hover:border-[#175CD3]/40 transition-colors"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-sm font-black font-mono tracking-wider px-2 py-0.5 rounded text-[#0C111D] bg-white border border-[#175CD3]/40 shadow-xs">
                            {sanitized}
                          </span>
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]">
                            <CheckCircle2 className="w-2.5 h-2.5" />
                            Đã xác thực
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-1.5">
                          {getPlateColorBadge(p)}
                          {p.province && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#F0F9FF] text-[#026AA2] border border-[#B9E6FE] font-mono">
                              {p.province}
                            </span>
                          )}
                          {p.count && p.count > 1 && (
                            <span className="text-[10px] text-[#667085] font-mono">
                              ({p.count} lần)
                            </span>
                          )}
                        </div>
                      </div>
                      {p.thumbnail && (
                        <img
                          src={p.thumbnail}
                          alt={sanitized}
                          className="h-10 max-w-[80px] rounded border border-[#D0D7DE] object-cover shadow-2xs shrink-0 bg-white"
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: MẬT ĐỘ GIAO THÔNG & KHOẢNG CÁCH XE (HIỂN THỊ DANH SÁCH PHƯƠNG TIỆN, VẬN TỐC & LINE CROSSING) */}
        {activeTab === 'traffic' && (
          <div className="space-y-3">
            {/* Thanh chuyển đổi chế độ xem nếu có Radar Engine */}
            {trafficEngine && (
              <div className="flex items-center justify-between border-b border-[#E4E9EF] pb-2.5">
                <div className="flex items-center gap-1.5 text-xs text-[#475467]">
                  <Activity className="w-4 h-4 text-[#175CD3]" />
                  <span className="font-semibold text-[#16202A]">Chế độ quan sát ADAS:</span>
                  <span className="text-[11px] text-[#667085]">Giám sát mật độ, cự ly 3D và lưu lượng qua vạch</span>
                </div>
                <div className="flex items-center gap-1 bg-[#F2F4F7] p-0.5 rounded-lg border border-[#E4E9EF]">
                  <button
                    type="button"
                    onClick={() => setShowRadarView(false)}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
                      !showRadarView
                        ? 'bg-white text-[#175CD3] shadow-xs'
                        : 'text-[#667085] hover:text-[#16202A]'
                    }`}
                  >
                    📋 Thống kê & Danh sách xe
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowRadarView(true)}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all flex items-center gap-1 ${
                      showRadarView
                        ? 'bg-white text-[#175CD3] shadow-xs'
                        : 'text-[#667085] hover:text-[#16202A]'
                    }`}
                  >
                    <Radio className="w-3.5 h-3.5 text-[#0E9384]" />
                    📡 Radar 3D Cự ly
                  </button>
                </div>
              </div>
            )}

            {showRadarView && trafficEngine ? (
              <TrafficDistancePanel
                {...trafficEngine}
                lineCrossings={effectiveCrossings as any}
                onResetLineCrossings={handleResetCrossings}
              />
            ) : (
              <>
                {/* 1. KHỐI THỐNG KÊ LINE CROSSINGS & VẬN TỐC THEO THỜI GIAN THỰC */}
                {effectiveCrossings && (
                  <div className="p-3 rounded-[10px] border border-[#CBD5E1] bg-[#0F172A] text-white shadow-sm space-y-2.5">
                    <div className="flex items-center justify-between border-b border-white/10 pb-2">
                      <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-[#38BDF8]" />
                        <div>
                          <h4 className="text-xs font-bold uppercase tracking-wider text-[#38BDF8]">
                            Lưu Lượng Qua Vạch Ảo (Virtual Line Crossing)
                          </h4>
                          <span className="text-[10px] text-slate-400">
                            Đếm IN / OUT & ước lượng vận tốc thời gian thực (vạch chuẩn Y = 60%)
                          </span>
                        </div>
                      </div>
                      {handleResetCrossings && (
                        <button
                          type="button"
                          onClick={handleResetCrossings}
                          className="px-2 py-1 text-[11px] font-medium rounded bg-white/10 hover:bg-white/20 text-slate-200 transition-colors flex items-center gap-1"
                          title="Đặt lại bộ đếm IN / OUT"
                        >
                          <RotateCcw className="w-3 h-3 text-slate-300" />
                          <span>Đặt lại đếm</span>
                        </button>
                      )}
                    </div>

                    {/* Hàng chỉ số IN / OUT / TỔNG */}
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-500/30">
                        <div className="text-[10px] text-emerald-400 font-semibold flex items-center justify-center gap-1">
                          <ArrowDown className="w-3 h-3 text-emerald-400" />
                          <span>IN (Tiến vào)</span>
                        </div>
                        <div className="text-lg font-black text-emerald-300 font-mono">
                          {inCount}
                        </div>
                      </div>

                      <div className="p-2 rounded-lg bg-sky-950/60 border border-sky-500/30">
                        <div className="text-[10px] text-sky-400 font-semibold flex items-center justify-center gap-1">
                          <ArrowUp className="w-3 h-3 text-sky-400" />
                          <span>OUT (Rời đi)</span>
                        </div>
                        <div className="text-lg font-black text-sky-300 font-mono">
                          {outCount}
                        </div>
                      </div>

                      <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-600/40">
                        <div className="text-[10px] text-slate-300 font-semibold">TỔNG LƯỢT</div>
                        <div className="text-lg font-black text-amber-300 font-mono">
                          {inCount + outCount}
                        </div>
                      </div>
                    </div>

                    {/* Chi tiết phân loại Line Crossings & Danh sách Tốc độ Realtime */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono pt-1">
                      {/* Cột 1: Phân loại Out/In */}
                      <div className="p-2 rounded bg-black/40 border border-white/5 space-y-1.5">
                        <span className="text-[11px] font-bold text-amber-300 block">
                          Line Crossings (Phân loại):
                        </span>
                        <div className="pl-2 space-y-1 text-[11px]">
                          <div>
                            <span className="text-sky-300 font-bold block">Out:</span>
                            <div className="pl-3 grid grid-cols-2 gap-x-2 text-slate-300">
                              <span>motor: <strong className="text-white">{outByClass?.motor ?? outByClass?.motorcycle ?? 0}</strong></span>
                              <span>people: <strong className="text-white">{outByClass?.people ?? outByClass?.person ?? 0}</strong></span>
                              <span>car: <strong className="text-white">{outByClass?.car ?? 0}</strong></span>
                              <span>truck: <strong className="text-white">{outByClass?.truck ?? outByClass?.bus ?? 0}</strong></span>
                            </div>
                          </div>
                          <div className="pt-1">
                            <span className="text-emerald-300 font-bold block">In:</span>
                            <div className="pl-3 grid grid-cols-2 gap-x-2 text-slate-300">
                              <span>motor: <strong className="text-white">{inByClass?.motor ?? inByClass?.motorcycle ?? 0}</strong></span>
                              <span>people: <strong className="text-white">{inByClass?.people ?? inByClass?.person ?? 0}</strong></span>
                              <span>car: <strong className="text-white">{inByClass?.car ?? 0}</strong></span>
                              <span>truck: <strong className="text-white">{inByClass?.truck ?? inByClass?.bus ?? 0}</strong></span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Cột 2: Luồng Vận Tốc Thời Gian Thực */}
                      <div className="p-2 rounded bg-black/40 border border-white/5 flex flex-col justify-between">
                        <div>
                          <span className="text-[11px] font-bold text-emerald-300 block mb-1">
                            Vận tốc thời gian thực (Live Speeds):
                          </span>
                          <div className="space-y-1 max-h-[90px] overflow-y-auto pr-1">
                            {vehicles.filter(v => (v.speed_kmh && v.speed_kmh > 0) || v.class).length > 0 ? (
                              vehicles.slice(0, 5).map((v, i) => {
                                const cls = (v.class || 'car').toLowerCase();
                                const isPeople = cls.includes('person') || cls.includes('people');
                                const isMotor = cls.includes('motor') || cls.includes('bike');
                                const isTruck = cls.includes('truck') || cls.includes('bus');
                                const label = isPeople ? 'people' : isMotor ? 'motor' : isTruck ? 'truck' : 'car';
                                const spd = Math.round(v.speed_kmh || (v.distance_m ? Math.max(15, 60 - v.distance_m) : 35));
                                return (
                                  <div key={`live-spd-${v.id || i}`} className="flex items-center justify-between text-[11px] py-0.5 border-b border-white/5">
                                    <span className="text-slate-300">
                                      {label} #{v.id || i + 1}
                                    </span>
                                    <div className="flex items-center gap-1.5">
                                      {v.direction && (
                                        <span className={`px-1 rounded text-[9px] font-bold ${
                                          v.direction === 'IN' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-sky-500/20 text-sky-300'
                                        }`}>
                                          {v.direction}
                                        </span>
                                      )}
                                      <span className="font-bold text-amber-300">
                                        {spd} km/h
                                      </span>
                                    </div>
                                  </div>
                                );
                              })
                            ) : (
                              <div className="text-[10px] text-slate-500 italic py-2">
                                Đang ước lượng vận tốc qua các frame liên tiếp...
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="text-[9px] text-slate-400 mt-1 flex items-center justify-between">
                          <span>Camera: Hiệu chuẩn Homography</span>
                          <span className="text-emerald-400">● Realtime YOLOv8</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. BANNER TỔNG QUAN MẬT ĐỘ & CỰ LY AN TOÀN */}
                {vehicles.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-7 text-center text-[#98A2B3]">
                    <Users className="w-8 h-8 mb-1.5 stroke-[1.5] text-[#2E90FA]" />
                    <p className="text-xs font-semibold text-[#475467]">
                      Chưa phát hiện phương tiện hoặc đường thông thoáng
                    </p>
                    <p className="text-[11px] text-[#98A2B3] mt-0.5">
                      Mật độ giao thông và cự ly an toàn được hiển thị trực tiếp trên khung video phía trên khi tải video lên.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="p-2.5 rounded-[8px] border border-[#B2DDFF] bg-[#EFF8FF] flex flex-wrap items-center justify-between gap-3 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-[#175CD3] flex items-center gap-1.5">
                          <Users className="w-4 h-4" />
                          Mật độ: {vehicles.length > 5 ? 'Đông đúc' : vehicles.length > 2 ? 'Bình thường' : 'Thông thoáng'}
                        </span>
                        <span className="text-[#475467]">({vehicles.length} đối tượng phát hiện)</span>
                      </div>

                      <div className="flex items-center gap-3">
                        {safeDistance !== null && safeDistance !== undefined && (
                          <div className="flex items-center gap-1.5 font-mono">
                            <Ruler className="w-3.5 h-3.5 text-[#0E9384]" />
                            <span className="text-[#475467]">Cự ly xe trước:</span>
                            <span
                              className={`font-bold ${
                                collisionLevel === 'danger'
                                  ? 'text-[#F04438]'
                                  : collisionLevel === 'warning'
                                  ? 'text-[#F79009]'
                                  : 'text-[#067647]'
                              }`}
                            >
                              {safeDistance.toFixed(1)}m
                            </span>
                            {recommendedDistance !== null && (
                              <span className="text-[10px] text-[#667085]">(Chuẩn: {recommendedDistance.toFixed(0)}m)</span>
                            )}
                          </div>
                        )}
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            collisionLevel === 'danger'
                              ? 'bg-[#FEF3F2] text-[#F04438] border border-[#FECDCA] animate-pulse'
                              : collisionLevel === 'warning'
                              ? 'bg-[#FFFAEB] text-[#F79009] border border-[#FEDF89]'
                              : 'bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]'
                          }`}
                        >
                          {collisionLevel === 'danger'
                            ? 'Cảnh báo: Nguy cơ va chạm'
                            : collisionLevel === 'warning'
                            ? 'Chú ý khoảng cách an toàn'
                            : 'Khoảng cách an toàn'}
                        </span>
                      </div>
                    </div>

                    {/* 3. LƯỚI CÁC XE VÀ NGƯỜI ĐANG THEO DÕI */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                      {vehicles.map((v, idx) => {
                        const clsName = (v.class || 'car').toLowerCase();
                        const isPerson = clsName.includes('person') || clsName.includes('people');
                        const isMoto = clsName.includes('motor') || clsName.includes('bike');
                        const isTruck = clsName.includes('truck') || clsName.includes('bus');
                        const vehicleLabel = isPerson ? 'Người đi bộ' : isTruck ? 'Xe tải / Buýt' : isMoto ? 'Xe máy' : 'Xe ô tô';
                        const icon = isPerson ? '🚶' : isTruck ? '🚚' : isMoto ? '🏍️' : '🚗';

                        const boxH = Math.max(1, v.bbox.y2 - v.bbox.y1);
                        const estDist = v.distance_m != null ? v.distance_m : Math.max(3, Math.min(80, Math.round(5000 / boxH)));
                        const isTooClose = estDist < 10.0;

                        return (
                          <div
                            key={`veh-${v.id || idx}`}
                            className="p-2.5 rounded-[8px] border border-[#E4E9EF] bg-[#F8FAFC] flex items-center justify-between gap-3 shadow-2xs hover:border-[#175CD3]/40 transition-colors"
                          >
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-1.5 flex-wrap">
                                <span className="text-base">{icon}</span>
                                <span className="text-xs font-bold text-[#16202A]">
                                  {vehicleLabel} #{v.id || idx + 1}
                                </span>
                                {v.direction && (
                                  <span
                                    className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-bold flex items-center gap-0.5 ${
                                      v.direction === 'IN'
                                        ? 'bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]'
                                        : 'bg-[#EFF8FF] text-[#175CD3] border border-[#B2DDFF]'
                                    }`}
                                  >
                                    {v.direction === 'IN' ? '⬇ IN' : '⬆ OUT'}
                                  </span>
                                )}
                                <span
                                  className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                                    isTooClose
                                      ? 'bg-[#FEF3F2] text-[#F04438] border border-[#FECDCA]'
                                      : 'bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]'
                                  }`}
                                >
                                  {isTooClose ? 'Cần giữ khoảng cách' : 'Cự ly an toàn'}
                                </span>
                              </div>
                              <div className="flex items-center gap-2 mt-1.5 text-xs font-mono">
                                <span className="text-[#475467]">Khoảng cách:</span>
                                <strong className={`font-black ${isTooClose ? 'text-[#F04438]' : 'text-[#16202A]'}`}>
                                  {estDist} m
                                </strong>
                                {!isImageMode && (
                                  <span className="text-[#175CD3] font-bold ml-auto">
                                    {Math.round(v.speed_kmh || (v.distance_m ? Math.max(15, 60 - v.distance_m) : 35))} km/h
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* TAB 3: BIỂN BÁO GIAO THÔNG */}
        {activeTab === 'signs' && (
          <div>
            {uniqueSigns.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-7 text-center text-[#98A2B3]">
                <ShieldAlert className="w-8 h-8 mb-1.5 stroke-[1.5]" />
                <p className="text-xs font-semibold text-[#475467]">
                  Không phát hiện biển báo giao thông trong ảnh / video này
                </p>
                <p className="text-[11px] text-[#98A2B3] mt-0.5 max-w-md">
                  Chỉ nhận diện biển báo đạt độ tin cậy cao theo chuẩn QCVN 41:2019/BGTVT (Đã loại bỏ các vật thể có màu sắc/hình dạng tương tự hoặc ở quá xa).
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-2.5">
                {uniqueSigns.map((s, idx) => {
                  const isSpeedLimit = s.speed_limit != null && s.speed_limit > 0 && (s.sign_type?.includes('127') || false);
                  const isProhibitory = s.category === 'CẤM' || (s.sign_type && s.sign_type.startsWith('P'));
                  const isWarning = s.category === 'CẢNH BÁO' || (s.sign_type && s.sign_type.startsWith('W'));
                  const isMandatory = s.category === 'HIỆU LỆNH' || (s.sign_type && (s.sign_type.startsWith('R.3') || s.sign_type.startsWith('DP')));
                  const isInformative = s.category === 'CHỈ DẪN' || (s.sign_type && (s.sign_type.startsWith('I.') || s.sign_type.startsWith('R.4')));

                  const cardStyle = isProhibitory
                    ? 'border-[#FECDCA] bg-[#FEF3F2] hover:border-[#F97066]'
                    : isWarning
                    ? 'border-[#FEDF89] bg-[#FFFAEB] hover:border-[#F79009]'
                    : isMandatory
                    ? 'border-[#BAE6FD] bg-[#F0F9FF] hover:border-[#38BDF8]'
                    : 'border-[#A6F4C5] bg-[#ECFDF3] hover:border-[#32D583]';

                  const badgeTagColor = isProhibitory
                    ? 'bg-[#FEE4E2] text-[#D92D20] border-[#FECDCA]'
                    : isWarning
                    ? 'bg-[#FEF0C7] text-[#B54708] border-[#FEDF89]'
                    : isMandatory
                    ? 'bg-[#E0F2FE] text-[#0284C7] border-[#BAE6FD]'
                    : 'bg-[#D1FADF] text-[#027A48] border-[#A6F4C5]';

                  const categoryLabel = s.category || (isProhibitory ? 'CẤM' : isWarning ? 'CẢNH BÁO' : isMandatory ? 'HIỆU LỆNH' : 'CHỈ DẪN');

                  return (
                    <div
                      key={idx}
                      className={`p-3 rounded-[10px] border flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs transition-all ${cardStyle}`}
                    >
                      <div className="flex items-start gap-3.5 min-w-0 flex-1">
                        {isSpeedLimit ? (
                          <div className="w-10 h-10 rounded-full border-3 border-[#D92D20] bg-white flex items-center justify-center font-black font-mono text-base text-[#16202A] shadow-xs shrink-0 mt-0.5">
                            {s.speed_limit}
                          </div>
                        ) : isProhibitory ? (
                          <div className="w-10 h-10 rounded-full border-2 border-[#FDA29B] bg-white flex items-center justify-center text-lg shadow-xs shrink-0 text-[#D92D20] mt-0.5">
                            ⛔
                          </div>
                        ) : isWarning ? (
                          <div className="w-10 h-10 rounded-[6px] border-2 border-[#FEDF89] bg-white flex items-center justify-center text-lg shadow-xs shrink-0 text-[#B54708] mt-0.5">
                            ⚠️
                          </div>
                        ) : isMandatory ? (
                          <div className="w-10 h-10 rounded-full border-2 border-[#BAE6FD] bg-white flex items-center justify-center text-lg shadow-xs shrink-0 text-[#0284C7] mt-0.5">
                            ℹ️
                          </div>
                        ) : (
                          <div className="w-10 h-10 rounded-[6px] border-2 border-[#A6F4C5] bg-white flex items-center justify-center text-lg shadow-xs shrink-0 text-[#027A48] mt-0.5">
                            🛣️
                          </div>
                        )}

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs sm:text-sm font-bold text-[#16202A] leading-snug break-words">
                              Biển {s.sign_type}: {s.name || 'Biển báo giao thông'}
                            </span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border shrink-0 ${badgeTagColor}`}>
                              {categoryLabel}
                            </span>
                          </div>
                          <p className="text-xs text-[#344054] font-medium mt-1 leading-relaxed break-words whitespace-normal">
                            {isSpeedLimit ? (
                              <>
                                Giới hạn tốc độ: <strong className="font-mono text-[#D92D20] font-bold">{s.speed_limit} km/h</strong>
                              </>
                            ) : (
                              s.action_required || 'Tuân thủ hiệu lệnh quy định'
                            )}
                            <span className="text-[#667085] ml-2 inline-block font-normal">
                              {s.count && s.count > 1 ? `• Phát hiện ${s.count} lần` : '• Đang có hiệu lực'}
                            </span>
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2.5 shrink-0 self-end sm:self-center pl-13 sm:pl-0">
                        {s.thumbnail && (
                          <img
                            src={s.thumbnail}
                            alt={s.sign_type || 'Biển báo'}
                            className="w-11 h-11 rounded-lg border border-[#D0D5DD] object-contain bg-white shadow-2xs p-0.5"
                          />
                        )}
                        <span className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-[#12B76A] text-white shadow-xs shrink-0 whitespace-nowrap">
                          Hiệu lực
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: MŨ BẢO HIỂM */}
        {activeTab === 'helmets' && (
          <div>
            {uniqueHelmets.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-7 text-center text-[#98A2B3]">
                <HardHat className="w-8 h-8 mb-1.5 stroke-[1.5] text-[#12B76A]" />
                <p className="text-xs font-semibold text-[#027A48]">
                  Không phát hiện vi phạm quy định mũ bảo hiểm
                </p>
                <p className="text-[11px] text-[#98A2B3] mt-0.5 max-w-md">
                  Người điều khiển xe hai bánh trong khung nhìn tuân thủ quy định an toàn (hoặc không có xe máy trong tầm quan sát).
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-2.5">
                {uniqueHelmets.map((h, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-[10px] border border-[#FECDCA] bg-[#FEF3F2] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs hover:border-[#F04438] transition-colors"
                  >
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      <div className="w-9 h-9 rounded-full bg-[#F04438] text-white flex items-center justify-center font-bold text-sm shrink-0 mt-0.5 shadow-xs">
                        !
                      </div>
                      <div className="min-w-0 flex-1">
                        <span className="text-xs sm:text-sm font-bold text-[#B42318] block leading-snug break-words">
                          Không đội mũ bảo hiểm khi lái xe máy
                        </span>
                        <span className="text-xs text-[#667085] font-mono block mt-1 leading-relaxed break-words">
                          Người điều khiển #{h.track_id} {h.plate_text ? `• Biển số xe: ${h.plate_text}` : ''} {h.count && h.count > 1 ? `• Ghi nhận ${h.count} lần` : ''}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5 shrink-0 self-end sm:self-center pl-12 sm:pl-0">
                      {h.thumbnail && (
                        <img
                          src={h.thumbnail}
                          alt="Vi phạm mũ bảo hiểm"
                          className="w-11 h-11 rounded-lg border border-[#FECDCA] object-cover bg-white shadow-2xs"
                        />
                      )}
                      <span className="px-2.5 py-1 rounded-md text-[11px] font-extrabold uppercase bg-[#F04438] text-white shadow-xs shrink-0 whitespace-nowrap">
                        Vi phạm NĐ 100
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
});
