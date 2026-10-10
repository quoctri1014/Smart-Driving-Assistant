'use client';

import React, { memo } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  Volume2,
  VolumeX,
  Info,
} from 'lucide-react';
import { AlertPriority } from '../../lib/driving/alert-engine';

export interface PriorityAlertBarProps {
  priority: AlertPriority;
  message: string;
  isMuted: boolean;
  onToggleMute: () => void;
  safeDistance?: number | null;
  recommendedSpeed?: number | null;
  speedLimit?: number | null;
  currentSpeed?: number | null;
  className?: string;
}

export const PriorityAlertBar = memo(function PriorityAlertBar({
  priority,
  message,
  isMuted,
  onToggleMute,
  safeDistance,
  recommendedSpeed,
  speedLimit,
  currentSpeed,
  className = '',
}: PriorityAlertBarProps) {
  const isDanger =
    priority === 'COLLISION_DANGER' ||
    priority === 'SPEED_DANGER' ||
    (priority === 'DROWSINESS' && (message.includes('NGUY HIỂM') || message.includes('5 GIÂY') || message.includes('ngủ gật')));

  const isWarning =
    priority === 'COLLISION_CAUTION' ||
    priority === 'SPEED_WARNING' ||
    priority === 'DROWSINESS' ||
    priority === 'SEATBELT_WARNING' ||
    priority === 'REST_REMINDER';

  const isInfo = priority === 'TRAFFIC_SIGN';
  const isSafe = !isDanger && !isWarning && !isInfo && priority === 'NORMAL';

  // Khi ở trạng thái an toàn: Ẩn thanh để không gây rối mắt, chỉ hiển thị khi có cảnh báo thật sự
  if (isSafe) {
    return null;
  }

  // Semantic color styling
  const bgStyle = isDanger
    ? 'bg-[#FEF3F2] border-[#FECDCA] text-[#B42318]'
    : isWarning
    ? 'bg-[#FFFAEB] border-[#FEDF89] text-[#B54708]'
    : isInfo
    ? 'bg-[#EFF8FF] border-[#B2DDFF] text-[#175CD3]'
    : 'bg-[#ECFDF3] border-[#ABEFC6] text-[#067647]';

  const badgeStyle = isDanger
    ? 'bg-[#F04438] text-white animate-pulse'
    : isWarning
    ? 'bg-[#F79009] text-white'
    : isInfo
    ? 'bg-[#175CD3] text-white'
    : 'bg-[#12B76A] text-white';

  const displayTitle =
    priority === 'COLLISION_DANGER'
      ? 'NGUY HIỂM: NGUY CƠ VA CHẠM'
      : priority === 'SPEED_DANGER'
      ? 'CẢNH BÁO TỐC ĐỘ NGUY HIỂM'
      : priority === 'DROWSINESS'
      ? (isDanger ? 'CẢNH BÁO TÀI XẾ NGUY HIỂM' : 'CẢNH BÁO BUỒNG LÁI DMS')
      : priority === 'SPEED_WARNING'
      ? 'CẢNH BÁO QUÁ TỐC ĐỘ'
      : priority === 'COLLISION_CAUTION'
      ? (message.includes('Mật độ') ? 'LƯU Ý VẬN HÀNH' : 'CẢNH BÁO CỰ LY AN TOÀN')
      : priority === 'SEATBELT_WARNING'
      ? 'NHẮC NHỞ AN TOÀN'
      : priority === 'REST_REMINDER'
      ? 'NHẮC NHỞ NGHỈ NGƠI'
      : priority === 'TRAFFIC_SIGN'
      ? 'THÔNG TIN BIỂN BÁO'
      : 'HÀNH TRÌNH AN TOÀN';

  const displayMessage =
    message ||
    (isSafe
      ? 'Hệ thống AI đang quét làn đường & khoảng cách - Không có mối nguy hiểm'
      : 'Đang phân tích các yếu tố an toàn');

  return (
    <div
      className={`w-full rounded-[10px] border p-3 flex items-center justify-between gap-3 shadow-sm select-none transition-all duration-200 ${bgStyle} ${className}`}
    >
      {/* Left: Icon & Alert Message */}
      <div className="flex items-center gap-3 min-w-0">
        <div
          className={`w-8 h-8 rounded-[8px] flex items-center justify-center shrink-0 ${badgeStyle}`}
        >
          {isDanger ? (
            <AlertOctagon className="w-4 h-4" />
          ) : isWarning ? (
            <AlertTriangle className="w-4 h-4" />
          ) : isInfo ? (
            <Info className="w-4 h-4" />
          ) : (
            <CheckCircle2 className="w-4 h-4" />
          )}
        </div>

        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-extrabold uppercase tracking-wider font-mono">
              {displayTitle}
            </span>

            {/* Giới hạn tốc độ pháp lý */}
            {speedLimit !== null && speedLimit !== undefined && (
              <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-black/10 border border-black/5">
                Giới hạn: <strong>{speedLimit} km/h</strong>
              </span>
            )}

            {/* Vận tốc xe chủ hiện tại */}
            {currentSpeed !== null && currentSpeed !== undefined && (
              <span
                className={`text-[11px] font-mono px-1.5 py-0.5 rounded border ${
                  priority === 'SPEED_DANGER'
                    ? 'bg-red-500/20 text-red-700 border-red-500/30'
                    : priority === 'SPEED_WARNING'
                    ? 'bg-amber-500/20 text-amber-800 border-amber-500/30'
                    : 'bg-black/10 border-black/5'
                }`}
              >
                Vận tốc: <strong>{Math.round(currentSpeed)} km/h</strong>
              </span>
            )}

            {/* Cự ly an toàn (khi có nguy cơ va chạm) */}
            {safeDistance !== null && safeDistance !== undefined && (priority === 'COLLISION_DANGER' || priority === 'COLLISION_CAUTION') && (
              <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-black/10 border border-black/5">
                Cự ly: <strong>{safeDistance.toFixed(1)}m</strong>
              </span>
            )}

            {/* Tốc độ khuyến nghị an toàn do mật độ đông (khi thấp hơn giới hạn pháp lý) */}
            {recommendedSpeed !== null &&
              recommendedSpeed !== undefined &&
              speedLimit !== null &&
              speedLimit !== undefined &&
              recommendedSpeed < speedLimit &&
              !priority.startsWith('SPEED_') && (
                <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-black/10 border border-black/5">
                  Gợi ý an toàn: <strong>{recommendedSpeed} km/h</strong>
                </span>
            )}
          </div>
          <p className="text-sm font-semibold truncate mt-0.5">
            {displayMessage}
          </p>
        </div>
      </div>

      {/* Right: Audio Voice Mute Toggle */}
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={onToggleMute}
          title={isMuted ? 'Bật giọng đọc cảnh báo cabin (Phím M)' : 'Tắt tiếng cảnh báo cabin (Phím M)'}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-[6px] text-xs font-medium border transition-colors cursor-pointer ${
            isMuted
              ? 'bg-white/80 border-[#D0D7DE] text-[#667085] hover:bg-white'
              : 'bg-white border-current text-current shadow-xs'
          }`}
        >
          {isMuted ? (
            <>
              <VolumeX className="w-3.5 h-3.5 text-[#F04438]" />
              <span className="hidden sm:inline">Giọng đọc: Tắt</span>
            </>
          ) : (
            <>
              <Volume2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Giọng đọc: Bật</span>
            </>
          )}
          <kbd className="hidden sm:inline text-[10px] font-mono px-1 py-0.2 rounded bg-black/5 border border-black/10 ml-0.5">
            M
          </kbd>
        </button>
      </div>
    </div>
  );
});
