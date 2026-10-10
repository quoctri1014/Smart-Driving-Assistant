'use client';

import React, { memo } from 'react';
import {
  Play,
  Square,
  Pause,
  Clock,
  Upload,
  LayoutGrid,
  Gauge,
  Activity,
  Car,
  ShieldCheck,
} from 'lucide-react';
import { TGButton, TGStatusBadge } from '../ui';
import { SessionState } from '../../hooks/useDrivingSession';

export type LiveViewMode = 'matrix' | 'hud' | 'diagnostics';

export interface LiveHeaderProps {
  plateNumber: string;
  vehicleType?: string;
  driverName?: string;
  fleetName?: string;
  sessionState: SessionState;
  connectionStatus: 'online' | 'reconnecting' | 'offline';
  durationFormatted: string;
  sourceMode: 'video' | 'webcam' | 'image';
  onSourceModeChange: (mode: 'video' | 'webcam' | 'image') => void;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onUploadClick: () => void;
  videoFileName?: string;
  viewMode?: LiveViewMode;
  onViewModeChange?: (mode: LiveViewMode) => void;
}

export const LiveHeader = memo(function LiveHeader({
  plateNumber,
  driverName = 'Người Lái Xe',
  sessionState,
  connectionStatus,
  durationFormatted,
  sourceMode,
  onStart,
  onPause,
  onResume,
  onStop,
  onUploadClick,
  videoFileName,
  viewMode = 'matrix',
  onViewModeChange,
}: LiveHeaderProps) {
  const isStreaming = sessionState === 'STREAMING';
  const isPaused = sessionState === 'PAUSED';
  const isConnecting = sessionState === 'CONNECTING' || sessionState === 'PREPARING';

  return (
    <div className="bg-white border border-[#E4E9EF] rounded-[12px] p-4 shadow-sm flex flex-col xl:flex-row xl:items-center justify-between gap-4 select-none">
      {/* Left: Trip Duration & Live Indicator */}
      <div className="flex items-center gap-3">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-[8px] bg-[#F8FAFC] border border-[#E4E9EF] text-xs font-medium text-[#16202A]">
          <Clock className="w-4 h-4 text-[#175CD3]" />
          <span>Thời gian lái: <strong className="font-mono text-sm text-[#175CD3] font-bold">{durationFormatted}</strong></span>
        </div>

        {isStreaming && (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#ECFDF3] border border-[#ABEFC6] text-xs font-semibold text-[#079455]">
            <span className="w-2 h-2 rounded-full bg-[#12B76A] animate-ping" />
            <span>Đang ghi nhận hành trình</span>
          </div>
        )}
      </div>

      {/* Right: Controls & View Modes */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* View Mode Selector */}
        {onViewModeChange && (
          <div className="flex items-center rounded-[8px] border border-[#E4E9EF] bg-[#F8FAFC] p-1 text-xs">
            <button
              onClick={() => onViewModeChange('matrix')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] font-semibold transition-all cursor-pointer ${
                viewMode === 'matrix'
                  ? 'bg-[#175CD3] text-white shadow-xs'
                  : 'text-[#667085] hover:text-[#16202A] hover:bg-white/60'
              }`}
              title="Chế độ giám sát toàn cảnh"
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Toàn cảnh</span>
            </button>
            <button
              onClick={() => onViewModeChange('hud')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] font-semibold transition-all cursor-pointer ${
                viewMode === 'hud'
                  ? 'bg-[#175CD3] text-white shadow-xs'
                  : 'text-[#667085] hover:text-[#16202A] hover:bg-white/60'
              }`}
              title="Góc nhìn tập trung tài xế / HUD Buồng lái (Phím H)"
            >
              <Gauge className="w-3.5 h-3.5" />
              <span>Tài xế HUD</span>
              <kbd className="hidden lg:inline text-[9px] px-1 py-0.2 bg-black/10 rounded font-mono">H</kbd>
            </button>
            <button
              onClick={() => onViewModeChange('diagnostics')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] font-semibold transition-all cursor-pointer ${
                viewMode === 'diagnostics'
                  ? 'bg-[#175CD3] text-white shadow-xs'
                  : 'text-[#667085] hover:text-[#16202A] hover:bg-white/60'
              }`}
              title="Chẩn đoán kỹ thuật AI & độ trễ"
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Chẩn đoán</span>
            </button>
          </div>
        )}

        {/* Video / Image Upload Button */}
        <TGButton
          variant="secondary"
          size="sm"
          onClick={onUploadClick}
          disabled={isStreaming}
          leftIcon={<Upload className="w-3.5 h-3.5" />}
          className="text-xs font-semibold cursor-pointer h-9 px-3.5"
        >
          {videoFileName ? videoFileName.substring(0, 16) + '...' : 'Tải video / ảnh'}
        </TGButton>

        {/* Stream Play/Pause/Stop Action Buttons */}
        {sourceMode === 'image' ? (
          <div className="flex items-center gap-2">
            <TGButton
              variant="secondary"
              size="sm"
              onClick={onUploadClick}
              leftIcon={<Upload className="w-3.5 h-3.5" />}
              className="text-xs cursor-pointer font-medium h-9"
            >
              Chọn tệp khác
            </TGButton>
            <TGButton
              variant="danger"
              size="sm"
              onClick={onStop}
              leftIcon={<Square className="w-3.5 h-3.5 fill-current" />}
              className="text-xs cursor-pointer h-9"
            >
              Xóa ảnh
            </TGButton>
          </div>
        ) : !isStreaming && !isPaused ? (
          <TGButton
            variant="primary"
            size="sm"
            onClick={onStart}
            isLoading={isConnecting}
            leftIcon={<Play className="w-3.5 h-3.5 fill-current" />}
            className="text-xs font-bold cursor-pointer h-9 px-4 shadow-[0_2px_6px_rgba(23,92,211,0.25)]"
          >
            Bắt đầu giám sát
          </TGButton>
        ) : (
          <div className="flex items-center gap-2">
            {isPaused ? (
              <TGButton
                variant="primary"
                size="sm"
                onClick={onResume}
                leftIcon={<Play className="w-3.5 h-3.5 fill-current" />}
                className="text-xs font-bold cursor-pointer h-9 px-4"
              >
                Tiếp tục
              </TGButton>
            ) : (
              <TGButton
                variant="secondary"
                size="sm"
                onClick={onPause}
                leftIcon={<Pause className="w-3.5 h-3.5" />}
                className="text-xs cursor-pointer font-semibold h-9"
                title="Tạm dừng video và tự động nhận diện trên khung hình"
              >
                Tạm dừng & Quét
              </TGButton>
            )}

            <TGButton
              variant="danger"
              size="sm"
              onClick={onStop}
              leftIcon={<Square className="w-3.5 h-3.5 fill-current" />}
              className="text-xs cursor-pointer h-9"
            >
              Dừng luồng
            </TGButton>
          </div>
        )}
      </div>
    </div>
  );
});

