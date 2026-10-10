'use client';

import React, { memo } from 'react';
import {
  Video,
  Radio,
  Wifi,
  WifiOff,
  Cpu,
  Keyboard,
  Shield,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import { SocketStatus } from '../../hooks/useRoadDrivingSocket';

export interface SystemHealthBannerProps {
  roadStatus: 'online' | 'waiting' | 'error';
  cabinStatus: 'online' | 'offline';
  socketStatus: SocketStatus;
  processingTimeMs: number | null;
  loadScale?: number;
  className?: string;
}

export const SystemHealthBanner = memo(function SystemHealthBanner({
  roadStatus,
  cabinStatus,
  socketStatus,
  processingTimeMs,
  loadScale = 1.0,
  className = '',
}: SystemHealthBannerProps) {
  const isWsConnected = socketStatus === 'CONNECTED';

  return (
    <div
      className={`w-full bg-[#0C111D] border border-white/10 rounded-[8px] px-3.5 py-2 flex items-center justify-between gap-3 text-xs text-white/80 select-none flex-wrap shadow-sm ${className}`}
    >
      {/* Left: System Sub-Sensors */}
      <div className="flex items-center gap-3.5 flex-wrap">
        {/* Role identifier: Single Admin Role */}
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-[4px] bg-[#175CD3]/20 border border-[#175CD3]/40 text-[#53B1FD] font-semibold text-[11px]">
          <Shield className="w-3.5 h-3.5" />
          <span>QUẢN TRỊ VIÊN HỆ THỐNG</span>
        </div>

        {/* Road Camera Sensor */}
        <div className="flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${
              roadStatus === 'online'
                ? 'bg-[#12B76A] ring-2 ring-[#12B76A]/30'
                : 'bg-[#F79009] ring-2 ring-[#F79009]/30'
            }`}
          />
          <span className="text-[11px] text-white/60">Cam đường:</span>
          <span className="text-[11px] font-medium text-white font-mono">
            {roadStatus === 'online' ? 'Sẵn sàng' : 'Chờ tín hiệu'}
          </span>
        </div>

        {/* Cabin Camera Sensor */}
        <div className="flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${
              cabinStatus === 'online'
                ? 'bg-[#12B76A] ring-2 ring-[#12B76A]/30'
                : 'bg-[#667085]'
            }`}
          />
          <span className="text-[11px] text-white/60">Cam cabin (DMS):</span>
          <span className="text-[11px] font-medium text-white/90 font-mono">
            {cabinStatus === 'online' ? 'Đã kết nối' : 'Chưa có'}
          </span>
        </div>

        {/* WebSocket Real-time Link */}
        <div className="flex items-center gap-1.5">
          {isWsConnected ? (
            <Wifi className="w-3.5 h-3.5 text-[#12B76A]" />
          ) : socketStatus === 'CONNECTING' ? (
            <Wifi className="w-3.5 h-3.5 text-[#F79009] animate-pulse" />
          ) : (
            <WifiOff className="w-3.5 h-3.5 text-white/40" />
          )}
          <span className="text-[11px] text-white/60">WebSocket:</span>
          <span
            className={`text-[11px] font-mono font-semibold ${
              isWsConnected
                ? 'text-[#12B76A]'
                : socketStatus === 'CONNECTING'
                ? 'text-[#F79009]'
                : 'text-white/60'
            }`}
          >
            {isWsConnected
              ? `${processingTimeMs !== null ? processingTimeMs.toFixed(1) : '24'}ms (10 FPS)`
              : socketStatus === 'CONNECTING'
              ? 'Đang kết nối...'
              : 'Sẵn sàng kết nối'}
          </span>
        </div>

        {/* AI Load Shedding Engine */}
        <div className="hidden xl:flex items-center gap-1.5">
          <Cpu className="w-3.5 h-3.5 text-[#3B82F6]" />
          <span className="text-[11px] text-white/60">Tải AI:</span>
          <span className="text-[11px] font-mono text-[#53B1FD]">
            {loadScale >= 1.0 ? '100% (Chuẩn)' : `${Math.round(loadScale * 100)}% (Giảm tải)`}
          </span>
        </div>
      </div>

      {/* Right: Keyboard Shortcuts Guide */}
      <div className="hidden md:flex items-center gap-3 text-[11px] text-white/50 font-mono">
        <div className="flex items-center gap-1">
          <Keyboard className="w-3 h-3 text-white/40" />
          <span>Phím tắt:</span>
        </div>
        <span>
          <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-white/90 border border-white/15">
            Space
          </kbd>{' '}
          Chạy/Dừng
        </span>
        <span>
          <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-white/90 border border-white/15">
            M
          </kbd>{' '}
          Tắt/Bật tiếng
        </span>
      </div>
    </div>
  );
});
