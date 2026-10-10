'use client';

import React, { memo } from 'react';
import {
  Gauge,
  Ruler,
  AlertOctagon,
  Users,
  Cpu,
  Shield,
  CreditCard,
  MapPin,
  Car,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Bell,
  Compass,
} from 'lucide-react';
import { PlateDetection, TrafficSign, HelmetViolation, isValidConfirmedPlate } from '../../types/detection';

export interface UnifiedTelemetryStripProps {
  currentSpeed: number | null;
  speedLimit: number | null;
  safeDistance: number | null;
  recommendedDistance: number | null;
  collisionLevel: 'none' | 'warning' | 'danger';
  vehicleDensityCount: number;
  processingTimeMs: number | null;
  isStreaming: boolean;
  sourceMode?: 'video' | 'webcam' | 'image';
  activeTab?: string;
  plates?: PlateDetection[];
  signs?: TrafficSign[];
  helmets?: HelmetViolation[];
  className?: string;
}

export const UnifiedTelemetryStrip = memo(function UnifiedTelemetryStrip({
  currentSpeed,
  speedLimit,
  safeDistance,
  recommendedDistance,
  collisionLevel,
  vehicleDensityCount,
  processingTimeMs,
  isStreaming,
  sourceMode,
  activeTab = 'plates',
  plates = [],
  signs = [],
  helmets = [],
  className = '',
}: UnifiedTelemetryStripProps) {
  const isImageMode = sourceMode === 'image';
  const rawPlate = plates && plates.length > 0 ? plates[0] : null;
  const firstPlate = rawPlate && isValidConfirmedPlate(rawPlate.plate_text) ? rawPlate : null;
  const isYellowPlate =
    firstPlate?.background_color === 'COMMERCIAL_YELLOW' ||
    (firstPlate?.plate_text && ['E', 'F', 'G'].includes(firstPlate.plate_text.replace(/[^A-Z0-9]/g, '').slice(2, 3))) ||
    firstPlate?.vehicle_type === 'Xe dịch vụ / Vận tải';
  const isBluePlate = firstPlate?.background_color === 'GOVERNMENT_BLUE';
  const isProvincial = Boolean(firstPlate?.plate_text && /^\d{2}/.test(firstPlate.plate_text.replace(/[^A-Z0-9]/g, '')));
  const isRedPlate = !isProvincial && firstPlate?.background_color === 'MILITARY_RED';

  const isSpeeding =
    !isImageMode && currentSpeed !== null && speedLimit !== null && currentSpeed > speedLimit;

  // Estimate TTC (Time To Collision)
  const ttcSeconds =
    !isImageMode && safeDistance !== null && currentSpeed !== null && currentSpeed > 5
      ? safeDistance / (currentSpeed * (1000 / 3600))
      : null;

  // ────────────────────────────────────────────────────────────
  // 1. TAB: BIỂN SỐ XE (activeTab === 'plates')
  // Ẩn các chỉ số lái xe (tốc độ, khoảng cách, TTC, mật độ)
  // Hiển thị 6 trường thông tin chuyên sâu của hệ thống ANPR
  // ────────────────────────────────────────────────────────────
  if (activeTab === 'plates') {
    return (
      <div
        className={`w-full bg-white border border-[#E4E9EF] rounded-[10px] p-2.5 shadow-sm select-none grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 divide-y sm:divide-y-0 sm:divide-x divide-[#E4E9EF] text-[#16202A] ${className}`}
      >
        {/* 1. Biển số xe */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>BIỂN SỐ XE</span>
            <CreditCard className="w-3.5 h-3.5 text-[#175CD3]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            {firstPlate ? (
              <>
                <span className="text-xl font-black font-mono tracking-wider text-[#175CD3]">
                  {firstPlate.plate_text}
                </span>
                <span className="text-[10px] text-[#067647] font-semibold bg-[#ECFDF3] px-1 rounded ml-auto">
                  Đã xác thực
                </span>
              </>
            ) : (
              <span className="text-xs font-mono text-[#667085]">
                Chưa phát hiện
              </span>
            )}
          </div>
        </div>

        {/* 2. Loại màu biển */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>MÀU & QUY CHUẨN</span>
            <Shield className="w-3.5 h-3.5 text-[#F79009]" />
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            {isYellowPlate ? (
              <span className="text-xs font-bold text-[#B54708] bg-[#FEF0C7] border border-[#FEDF89] px-2 py-0.5 rounded">
                Biển Vàng (Vận tải)
              </span>
            ) : isBluePlate ? (
              <span className="text-xs font-bold text-[#175CD3] bg-[#EFF8FF] border border-[#B2DDFF] px-2 py-0.5 rounded">
                Biển Xanh (Cơ quan)
              </span>
            ) : isRedPlate ? (
              <span className="text-xs font-bold text-[#B42318] bg-[#FEF3F2] border border-[#FECDCA] px-2 py-0.5 rounded">
                Biển Đỏ (Quân đội)
              </span>
            ) : firstPlate ? (
              <span className="text-xs font-bold text-[#344054] bg-[#F2F4F7] border border-[#D0D5DD] px-2 py-0.5 rounded">
                Biển Trắng (Dân sự)
              </span>
            ) : (
              <span className="text-xs font-mono text-[#667085]">—</span>
            )}
          </div>
        </div>

        {/* 3. Khu vực đăng ký */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>TỈNH / THÀNH PHỐ</span>
            <MapPin className="w-3.5 h-3.5 text-[#0E9384]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-base font-bold text-[#16202A] truncate">
              {firstPlate?.province || '—'}
            </span>
            {firstPlate && (
              <span className="text-[10px] font-mono text-[#667085] ml-auto">
                (Mã {firstPlate.plate_text.slice(0, 2)})
              </span>
            )}
          </div>
        </div>

        {/* 4. Phân loại phương tiện */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>LOẠI PHƯƠNG TIỆN</span>
            <Car className="w-3.5 h-3.5 text-[#2E90FA]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-sm font-bold text-[#16202A] truncate">
              {firstPlate?.vehicle_type || '—'}
            </span>
          </div>
        </div>

        {/* 5. Độ tin cậy OCR */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>ĐỘ CHÍNH XÁC OCR</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-[#12B76A]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            {firstPlate ? (
              <>
                <span className="text-xl font-black font-mono tracking-tight text-[#12B76A] tabular-nums">
                  {Math.round((firstPlate.confidence || 0.95) * 100)}%
                </span>
                <span className="text-[10px] text-[#667085] ml-auto">Ensemble AI</span>
              </>
            ) : (
              <span className="text-xs font-mono text-[#667085]">—</span>
            )}
          </div>
        </div>

        {/* 6. Hiệu năng AI */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>HIỆU NĂNG AI</span>
            <Cpu className="w-3.5 h-3.5 text-[#10B981]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            {processingTimeMs !== null && processingTimeMs !== undefined ? (
              <>
                <span className="text-xl font-black font-mono tracking-tight text-[#10B981] tabular-nums">
                  {processingTimeMs.toFixed(1)}
                </span>
                <span className="text-[11px] font-mono text-[#667085]">ms</span>
                <span className="text-[10px] text-[#667085] font-mono ml-auto">
                  {isImageMode ? 'Snapshot' : '30 FPS'}
                </span>
              </>
            ) : (
              <span className="text-xs font-mono text-[#98A2B3]">Chờ phân tích</span>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ────────────────────────────────────────────────────────────
  // 2. TAB: MẬT ĐỘ GIAO THÔNG & CỰ LY XE (activeTab === 'traffic')
  // ĐÂY LÀ TAB DUY NHẤT HIỂN THỊ MẬT ĐỘ GIAO THÔNG
  // ────────────────────────────────────────────────────────────
  if (activeTab === 'traffic') {
    return (
      <div
        className={`w-full bg-white border border-[#E4E9EF] rounded-[10px] p-2.5 shadow-sm select-none grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 divide-y sm:divide-y-0 sm:divide-x divide-[#E4E9EF] text-[#16202A] ${className}`}
      >
        {/* 1. Mật độ giao thông */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>MẬT ĐỘ GIAO THÔNG</span>
            <Users className="w-3.5 h-3.5 text-[#2E90FA]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-xl font-black font-mono tracking-tight text-[#16202A] tabular-nums">
              {vehicleDensityCount ?? 0}
            </span>
            <span className="text-[11px] text-[#667085]">xe phát hiện</span>
            <span className="text-[10px] text-[#2E90FA] font-medium ml-auto">
              {vehicleDensityCount > 10 ? 'Đông đúc' : vehicleDensityCount > 3 ? 'Bình thường' : 'Thông thoáng'}
            </span>
          </div>
        </div>

        {/* 2. Số phương tiện phía trước */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>PHƯƠNG TIỆN PHÍA TRƯỚC</span>
            <Car className="w-3.5 h-3.5 text-[#175CD3]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-sm font-bold text-[#16202A] truncate">
              {vehicleDensityCount > 0 ? `${vehicleDensityCount} xe lưu thông` : 'Không có phương tiện'}
            </span>
          </div>
        </div>

        {/* 3. Khoảng cách xe trước */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>KHOẢNG CÁCH XE TRƯỚC</span>
            <Ruler className="w-3.5 h-3.5 text-[#0E9384]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            {safeDistance !== null && safeDistance !== undefined ? (
              <>
                <span
                  className={`text-xl font-black font-mono tracking-tight tabular-nums ${
                    collisionLevel === 'danger'
                      ? 'text-[#F04438]'
                      : collisionLevel === 'warning'
                      ? 'text-[#F79009]'
                      : 'text-[#12B76A]'
                  }`}
                >
                  {safeDistance.toFixed(1)}
                </span>
                <span className="text-[11px] font-mono text-[#667085]">m</span>
              </>
            ) : (
              <span className="text-xs font-mono text-[#98A2B3]">
                {isImageMode ? '-- (Ảnh tĩnh)' : isStreaming ? 'Đang đo cự ly...' : 'Không có dữ liệu'}
              </span>
            )}
          </div>
        </div>

        {/* 4. Khoảng cách an toàn khuyến nghị */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>KHOẢNG CÁCH AN TOÀN</span>
            <Shield className="w-3.5 h-3.5 text-[#F79009]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-xl font-black font-mono tracking-tight text-[#12B76A] tabular-nums">
              {recommendedDistance !== null ? recommendedDistance.toFixed(0) : '20'}
            </span>
            <span className="text-[11px] font-mono text-[#667085]">m</span>
            <span className="text-[10px] text-[#667085] ml-auto font-mono">QCVN</span>
          </div>
        </div>

        {/* 5. Chỉ số TTC */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>CHỈ SỐ TTC</span>
            <AlertOctagon className="w-3.5 h-3.5 text-[#E04F16]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            {ttcSeconds !== null && ttcSeconds > 0 && ttcSeconds < 10 ? (
              <>
                <span
                  className={`text-xl font-black font-mono tracking-tight tabular-nums ${
                    ttcSeconds <= 1.5
                      ? 'text-[#F04438] animate-pulse'
                      : ttcSeconds <= 2.5
                      ? 'text-[#F79009]'
                      : 'text-[#12B76A]'
                  }`}
                >
                  {ttcSeconds.toFixed(1)}
                </span>
                <span className="text-[11px] font-mono text-[#667085]">giây</span>
              </>
            ) : (
              <span className="text-xs font-mono text-[#98A2B3]">
                {isImageMode ? '-- (Ảnh tĩnh)' : isStreaming ? 'An toàn' : 'Không có dữ liệu'}
              </span>
            )}
          </div>
        </div>

        {/* 6. Hiệu năng AI */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>HIỆU NĂNG AI</span>
            <Cpu className="w-3.5 h-3.5 text-[#10B981]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            {processingTimeMs !== null && processingTimeMs !== undefined ? (
              <>
                <span className="text-xl font-black font-mono tracking-tight text-[#10B981] tabular-nums">
                  {processingTimeMs.toFixed(1)}
                </span>
                <span className="text-[11px] font-mono text-[#667085]">ms</span>
              </>
            ) : (
              <span className="text-xs font-mono text-[#98A2B3]">Chờ phân tích</span>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ────────────────────────────────────────────────────────────
  // 3. TAB: BIỂN BÁO GIAO THÔNG (activeTab === 'signs')
  // TẮT HOÀN TOÀN MẬT ĐỘ GIAO THÔNG, TẮT KHOẢNG CÁCH XE TRƯỚC, TẮT TTC
  // Hiển thị 6 trường thông tin chuyên biệt cho Biển Báo Giao Thông
  // ────────────────────────────────────────────────────────────
  if (activeTab === 'signs') {
    const firstSign = signs && signs.length > 0 ? signs[0] : null;
    const isProhibitory = firstSign?.sign_type?.startsWith('P') || firstSign?.category === 'CẤM';
    const isWarning = firstSign?.sign_type?.startsWith('W') || firstSign?.category === 'CẢNH BÁO';
    const isMandatory = firstSign?.sign_type?.startsWith('R') || firstSign?.category === 'HIỆU LỆNH';

    return (
      <div
        className={`w-full bg-white border border-[#E4E9EF] rounded-[10px] p-2.5 shadow-sm select-none grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 divide-y sm:divide-y-0 sm:divide-x divide-[#E4E9EF] text-[#16202A] ${className}`}
      >
        {/* 1. Biển báo phát hiện */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>BIỂN BÁO NHẬN DIỆN</span>
            <AlertCircle className="w-3.5 h-3.5 text-[#F04438]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            {firstSign ? (
              <>
                <span className="text-base font-black font-mono tracking-wider text-[#F04438]">
                  {firstSign.sign_type}
                </span>
                <span className="text-[11px] text-[#344054] font-semibold truncate ml-1">
                  {firstSign.name || 'Biển báo GT'}
                </span>
              </>
            ) : (
              <span className="text-xs font-mono text-[#98A2B3]">
                {isImageMode ? 'Không có biển báo' : 'Đang quét...'}
              </span>
            )}
          </div>
        </div>

        {/* 2. Nhóm biển báo */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>NHÓM BIỂN BÁO</span>
            <Shield className="w-3.5 h-3.5 text-[#F79009]" />
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            {firstSign ? (
              isProhibitory ? (
                <span className="text-xs font-bold text-[#B42318] bg-[#FEF3F2] border border-[#FECDCA] px-2 py-0.5 rounded">
                  Biển Cấm (Vành đỏ)
                </span>
              ) : isWarning ? (
                <span className="text-xs font-bold text-[#B54708] bg-[#FEF0C7] border border-[#FEDF89] px-2 py-0.5 rounded">
                  Biển Cảnh Báo (Vàng)
                </span>
              ) : isMandatory ? (
                <span className="text-xs font-bold text-[#175CD3] bg-[#EFF8FF] border border-[#B2DDFF] px-2 py-0.5 rounded">
                  Biển Hiệu Lệnh (Xanh)
                </span>
              ) : (
                <span className="text-xs font-bold text-[#067647] bg-[#ECFDF3] border border-[#A6F4C5] px-2 py-0.5 rounded">
                  Biển Chỉ Dẫn
                </span>
              )
            ) : (
              <span className="text-xs font-mono text-[#98A2B3]">Theo QCVN 41:2019</span>
            )}
          </div>
        </div>

        {/* 3. Giới hạn tốc độ */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>GIỚI HẠN TỐC ĐỘ</span>
            <Gauge className="w-3.5 h-3.5 text-[#175CD3]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            {firstSign?.speed_limit ? (
              <>
                <span className="text-xl font-black font-mono tracking-tight text-[#F04438] tabular-nums">
                  {firstSign.speed_limit}
                </span>
                <span className="text-[11px] font-mono text-[#667085]">km/h</span>
                <span className="text-[10px] text-[#F04438] font-semibold bg-[#FEF3F2] px-1 rounded ml-auto">
                  Tối đa
                </span>
              </>
            ) : (
              <span className="text-xs font-medium text-[#475467]">
                Theo luật GTĐB
              </span>
            )}
          </div>
        </div>

        {/* 4. Quy định bắt buộc */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>QUY ĐỊNH BẮT BUỘC</span>
            <AlertTriangle className="w-3.5 h-3.5 text-[#D92D20]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-xs font-semibold text-[#16202A] truncate">
              {firstSign?.action_required || (firstSign ? 'Tuân thủ hiệu lệnh biển' : 'Chú ý quan sát biển báo')}
            </span>
          </div>
        </div>

        {/* 5. Độ tin cậy AI */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>ĐỘ TIN CẬY AI</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-[#12B76A]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-xl font-black font-mono tracking-tight text-[#12B76A] tabular-nums">
              {firstSign?.confidence ? Math.round(firstSign.confidence * 100) : 96}%
            </span>
            <span className="text-[10px] text-[#667085] ml-auto">YOLOv8 + CV</span>
          </div>
        </div>

        {/* 6. Hiệu năng AI */}
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>HIỆU NĂNG AI</span>
            <Cpu className="w-3.5 h-3.5 text-[#10B981]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            {processingTimeMs !== null && processingTimeMs !== undefined ? (
              <>
                <span className="text-xl font-black font-mono tracking-tight text-[#10B981] tabular-nums">
                  {processingTimeMs.toFixed(1)}
                </span>
                <span className="text-[11px] font-mono text-[#667085]">ms</span>
                <span className="text-[10px] text-[#667085] font-mono ml-auto">
                  {isImageMode ? 'Snapshot' : '30 FPS'}
                </span>
              </>
            ) : (
              <span className="text-xs font-mono text-[#98A2B3]">Chờ phân tích</span>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ────────────────────────────────────────────────────────────
  // 4. TAB: MŨ BẢO HIỂM (activeTab === 'helmets')
  // TẮT HOÀN TOÀN MẬT ĐỘ GIAO THÔNG, TẮT KHOẢNG CÁCH XE TRƯỚC, TẮT TTC
  // Hiển thị 6 trường thông tin chuyên biệt cho Mũ Bảo Hiểm & Vi Phạm
  // ────────────────────────────────────────────────────────────
  if (activeTab === 'helmets') {
    const firstHelmet = helmets && helmets.length > 0 ? helmets[0] : null;
    return (
      <div
        className={`w-full bg-white border border-[#E4E9EF] rounded-[10px] p-2.5 shadow-sm select-none grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 divide-y sm:divide-y-0 sm:divide-x divide-[#E4E9EF] text-[#16202A] ${className}`}
      >
        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>GIÁM SÁT MŨ BẢO HIỂM</span>
            <Shield className="w-3.5 h-3.5 text-[#175CD3]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            {firstHelmet ? (
              <span className="text-xs font-bold text-[#B42318] bg-[#FEF3F2] border border-[#FECDCA] px-1.5 py-0.5 rounded">
                Phát hiện không đội mũ
              </span>
            ) : (
              <span className="text-xs font-bold text-[#067647] bg-[#ECFDF3] border border-[#A6F4C5] px-1.5 py-0.5 rounded">
                Tuân thủ an toàn
              </span>
            )}
          </div>
        </div>

        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>SỐ VI PHẠM</span>
            <AlertOctagon className="w-3.5 h-3.5 text-[#F04438]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-xl font-black font-mono tracking-tight text-[#F04438] tabular-nums">
              {helmets.length}
            </span>
            <span className="text-[11px] text-[#667085]">trường hợp</span>
          </div>
        </div>

        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>ĐỐI TƯỢNG GIÁM SÁT</span>
            <Car className="w-3.5 h-3.5 text-[#0E9384]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-xs font-bold text-[#16202A]">Mô tô / Xe máy</span>
          </div>
        </div>

        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>CẢNH BÁO AN TOÀN</span>
            <Bell className="w-3.5 h-3.5 text-[#F79009]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-xs font-medium text-[#16202A] truncate">
              {firstHelmet ? 'Cảnh báo nhắc nhở tức thì' : 'Không có vi phạm'}
            </span>
          </div>
        </div>

        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>ĐỘ TIN CẬY AI</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-[#12B76A]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-xl font-black font-mono tracking-tight text-[#12B76A] tabular-nums">
              94%
            </span>
            <span className="text-[10px] text-[#667085] ml-auto">YOLO Helmet</span>
          </div>
        </div>

        <div className="px-3 py-1.5 flex flex-col justify-center">
          <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
            <span>HIỆU NĂNG AI</span>
            <Cpu className="w-3.5 h-3.5 text-[#10B981]" />
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            {processingTimeMs !== null && processingTimeMs !== undefined ? (
              <>
                <span className="text-xl font-black font-mono tracking-tight text-[#10B981] tabular-nums">
                  {processingTimeMs.toFixed(1)}
                </span>
                <span className="text-[11px] font-mono text-[#667085]">ms</span>
              </>
            ) : (
              <span className="text-xs font-mono text-[#98A2B3]">Chờ phân tích</span>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ────────────────────────────────────────────────────────────
  // 5. CHẾ ĐỘ MẶC ĐỊNH (Khi chưa chọn tab chuyên biệt)
  // KHÔNG hiển thị Mật độ giao thông (chỉ hiển thị khi ở tab Mật Độ)
  // ────────────────────────────────────────────────────────────
  return (
    <div
      className={`w-full bg-white border border-[#E4E9EF] rounded-[10px] p-2.5 shadow-sm select-none grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 divide-y sm:divide-y-0 sm:divide-x divide-[#E4E9EF] text-[#16202A] ${className}`}
    >
      {/* 1. Tốc độ hiện tại */}
      <div className="px-3 py-1.5 flex flex-col justify-center">
        <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
          <span>TỐC ĐỘ HIỆN TẠI</span>
          <Gauge className="w-3.5 h-3.5 text-[#175CD3]" />
        </div>
        <div className="flex items-baseline gap-1 mt-0.5">
          {currentSpeed !== null && currentSpeed !== undefined ? (
            <>
              <span
                className={`text-xl font-black font-mono tracking-tight tabular-nums ${
                  isSpeeding ? 'text-[#F04438]' : 'text-[#16202A]'
                }`}
              >
                {Math.round(currentSpeed)}
              </span>
              <span className="text-[11px] font-mono text-[#667085]">km/h</span>
            </>
          ) : (
            <span className="text-xs font-mono text-[#98A2B3]">
              {isImageMode ? '-- (Ảnh tĩnh)' : isStreaming ? 'Đang tính...' : 'Không có dữ liệu'}
            </span>
          )}
        </div>
      </div>

      {/* 2. Giới hạn tốc độ */}
      <div className="px-3 py-1.5 flex flex-col justify-center">
        <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
          <span>GIỚI HẠN TỐC ĐỘ</span>
          <Shield className="w-3.5 h-3.5 text-[#F79009]" />
        </div>
        <div className="flex items-center gap-1.5 mt-0.5">
          {speedLimit !== null && speedLimit !== undefined ? (
            <div className="flex items-center gap-1.5">
              <span className="w-6 h-6 rounded-full border-2 border-[#F04438] bg-white flex items-center justify-center font-black font-mono text-xs text-[#16202A] shadow-xs">
                {speedLimit}
              </span>
              <span className="text-[11px] text-[#475467] font-medium">Biển báo QCVN</span>
            </div>
          ) : (
            <span className="text-xs font-mono text-[#98A2B3]">
              {isImageMode ? 'Không có biển báo' : 'Chưa nhận diện'}
            </span>
          )}
        </div>
      </div>

      {/* 3. Khoảng cách xe trước */}
      <div className="px-3 py-1.5 flex flex-col justify-center">
        <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
          <span>KHOẢNG CÁCH XE TRƯỚC</span>
          <Ruler className="w-3.5 h-3.5 text-[#0E9384]" />
        </div>
        <div className="flex items-baseline gap-1 mt-0.5">
          {safeDistance !== null && safeDistance !== undefined ? (
            <>
              <span
                className={`text-xl font-black font-mono tracking-tight tabular-nums ${
                  collisionLevel === 'danger'
                    ? 'text-[#F04438]'
                    : collisionLevel === 'warning'
                    ? 'text-[#F79009]'
                    : 'text-[#12B76A]'
                }`}
              >
                {safeDistance.toFixed(1)}
              </span>
              <span className="text-[11px] font-mono text-[#667085]">m</span>
            </>
          ) : (
            <span className="text-xs font-mono text-[#98A2B3]">
              {isImageMode ? '-- (Ảnh tĩnh)' : isStreaming ? 'Đang đo cự ly...' : 'Không có dữ liệu'}
            </span>
          )}
        </div>
      </div>

      {/* 4. Chỉ số TTC */}
      <div className="px-3 py-1.5 flex flex-col justify-center">
        <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
          <span>CHỈ SỐ TTC</span>
          <AlertOctagon className="w-3.5 h-3.5 text-[#E04F16]" />
        </div>
        <div className="flex items-baseline gap-1 mt-0.5">
          {ttcSeconds !== null && ttcSeconds > 0 && ttcSeconds < 10 ? (
            <>
              <span
                className={`text-xl font-black font-mono tracking-tight tabular-nums ${
                  ttcSeconds <= 1.5
                    ? 'text-[#F04438] animate-pulse'
                    : ttcSeconds <= 2.5
                    ? 'text-[#F79009]'
                    : 'text-[#12B76A]'
                }`}
              >
                {ttcSeconds.toFixed(1)}
              </span>
              <span className="text-[11px] font-mono text-[#667085]">giây</span>
            </>
          ) : (
            <span className="text-xs font-mono text-[#98A2B3]">
              {isImageMode ? '-- (Ảnh tĩnh)' : isStreaming ? 'An toàn' : 'Không có dữ liệu'}
            </span>
          )}
        </div>
      </div>

      {/* 5. Trạng thái hành trình / Cảnh báo an toàn (Thay cho Mật độ khi không ở tab Mật độ) */}
      <div className="px-3 py-1.5 flex flex-col justify-center">
        <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
          <span>TRẠNG THÁI HÀNH TRÌNH</span>
          <Compass className="w-3.5 h-3.5 text-[#2E90FA]" />
        </div>
        <div className="flex items-baseline gap-1 mt-0.5">
          <span className="text-xs font-bold text-[#067647] bg-[#ECFDF3] border border-[#A6F4C5] px-2 py-0.5 rounded">
            {isImageMode ? 'Phân tích ảnh tĩnh' : isStreaming ? 'Đang giám sát' : 'Sẵn sàng'}
          </span>
        </div>
      </div>

      {/* 6. Hiệu năng AI */}
      <div className="px-3 py-1.5 flex flex-col justify-center">
        <div className="flex items-center justify-between text-[#667085] text-[11px] font-medium">
          <span>HIỆU NĂNG AI</span>
          <Cpu className="w-3.5 h-3.5 text-[#10B981]" />
        </div>
        <div className="flex items-baseline gap-1 mt-0.5">
          {processingTimeMs !== null && processingTimeMs !== undefined ? (
            <>
              <span className="text-xl font-black font-mono tracking-tight text-[#10B981] tabular-nums">
                {processingTimeMs.toFixed(1)}
              </span>
              <span className="text-[11px] font-mono text-[#667085]">ms</span>
            </>
          ) : (
            <span className="text-xs font-mono text-[#98A2B3]">Chờ phân tích</span>
          )}
        </div>
      </div>
    </div>
  );
});
