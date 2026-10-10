'use client';

import React, { memo } from 'react';
import {
  Gauge,
  Ruler,
  Compass,
  Users,
  Activity,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
} from 'lucide-react';
import { TGCard, TGStatusBadge } from '../ui';

export interface TelemetryBarProps {
  currentSpeed?: number | null;
  speedLimit?: number | null;
  safeDistance?: number | null;
  recommendedDistance?: number | null;
  recommendedSpeed?: number | null;
  vehicleDensityCount?: number;
  driverStateText?: string;
  isDrowsy?: boolean;
}

export const TelemetryBar = memo(function TelemetryBar({
  currentSpeed = null,
  speedLimit = null,
  safeDistance = null,
  recommendedDistance = null,
  recommendedSpeed = null,
  vehicleDensityCount = 0,
  driverStateText = 'Đang giám sát',
  isDrowsy = false,
}: TelemetryBarProps) {
  const isSpeeding = currentSpeed != null && speedLimit != null && currentSpeed > speedLimit;
  const isDistanceClose = safeDistance != null && recommendedDistance != null && safeDistance < recommendedDistance * 0.7;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 select-none">
      {/* 1. Current Speed */}
      <TGCard
        variant="default"
        signalVariant={isSpeeding ? 'critical' : 'safe'}
        className="p-3.5 bg-white"
      >
        <div className="flex items-center justify-between">
          <span className="text-xs uppercase font-semibold text-[#475467] tracking-wider">
            Tốc Độ Hiện Tại
          </span>
          <Gauge className="w-4 h-4 text-[#175CD3]" />
        </div>

        <div className="flex items-baseline gap-1 mt-2">
          {currentSpeed !== null && currentSpeed !== undefined ? (
            <>
              <span
                className={`text-2xl font-bold font-mono tracking-tight ${
                  isSpeeding ? 'text-[#F04438]' : 'text-[#16202A]'
                }`}
              >
                {currentSpeed}
              </span>
              <span className="text-xs font-mono text-[#667085]">km/h</span>
            </>
          ) : (
            <span className="text-sm font-medium text-[#98A2B3]">Chưa có dữ liệu</span>
          )}
          <span className="text-xs text-[#98A2B3] ml-auto">
            {speedLimit !== null ? `(Tối đa: ${speedLimit})` : ''}
          </span>
        </div>
      </TGCard>

      {/* 2. Safe Distance */}
      <TGCard
        variant="default"
        signalVariant={isDistanceClose ? 'warning' : 'safe'}
        className="p-3.5 bg-white"
      >
        <div className="flex items-center justify-between">
          <span className="text-xs uppercase font-semibold text-[#475467] tracking-wider">
            Khoảng Cách Xe Trước
          </span>
          <Ruler className="w-4 h-4 text-[#0E9384]" />
        </div>

        <div className="flex items-baseline gap-1 mt-2">
          {safeDistance !== null && safeDistance !== undefined ? (
            <>
              <span
                className={`text-2xl font-bold font-mono tracking-tight ${
                  isDistanceClose ? 'text-[#F79009]' : 'text-[#16202A]'
                }`}
              >
                {safeDistance.toFixed(1)}
              </span>
              <span className="text-xs font-mono text-[#667085]">m</span>
            </>
          ) : (
            <span className="text-sm font-medium text-[#98A2B3]">Chưa có dữ liệu</span>
          )}
          {recommendedDistance !== null && (
            <span className="text-xs text-[#98A2B3] ml-auto">
              (Chuẩn: {recommendedDistance.toFixed(1)}m)
            </span>
          )}
        </div>
      </TGCard>

      {/* 3. Recommended Speed */}
      <TGCard variant="default" signalVariant="primary" className="p-3.5 bg-white">
        <div className="flex items-center justify-between">
          <span className="text-xs uppercase font-semibold text-[#475467] tracking-wider">
            Tốc Độ Khuyến Nghị
          </span>
          <Compass className="w-4 h-4 text-[#175CD3]" />
        </div>

        <div className="flex items-baseline gap-1 mt-2">
          {recommendedSpeed !== null && recommendedSpeed !== undefined ? (
            <>
              <span className="text-2xl font-bold font-mono text-[#175CD3] tracking-tight">
                {recommendedSpeed}
              </span>
              <span className="text-xs font-mono text-[#667085]">km/h</span>
            </>
          ) : (
            <span className="text-sm font-medium text-[#98A2B3]">Chưa có dữ liệu</span>
          )}
          <span className="text-xs text-[#17B26A] font-medium ml-auto">
            {recommendedSpeed !== null ? 'Tối ưu an toàn' : ''}
          </span>
        </div>
      </TGCard>

      {/* 4. Road Density */}
      <TGCard variant="default" signalVariant="info" className="p-3.5 bg-white">
        <div className="flex items-center justify-between">
          <span className="text-xs uppercase font-semibold text-[#475467] tracking-wider">
            Mật Độ Giao Thông
          </span>
          <Users className="w-4 h-4 text-[#2E90FA]" />
        </div>

        <div className="flex items-baseline gap-1 mt-2">
          <span className="text-2xl font-bold font-mono text-[#16202A] tracking-tight">
            {vehicleDensityCount ?? 0}
          </span>
          <span className="text-xs text-[#667085]">xe</span>
          <span className="text-xs text-[#2E90FA] font-medium ml-auto">
            {vehicleDensityCount > 10 ? 'Đông đúc' : vehicleDensityCount > 3 ? 'Bình thường' : 'Thông thoáng'}
          </span>
        </div>
      </TGCard>

      {/* 5. Driver State */}
      <TGCard
        variant="default"
        signalVariant={isDrowsy ? 'critical' : driverStateText.includes('Chưa') ? 'neutral' : 'safe'}
        className="p-3.5 bg-white col-span-2 sm:col-span-1"
      >
        <div className="flex items-center justify-between">
          <span className="text-xs uppercase font-semibold text-[#475467] tracking-wider">
            Trạng Thái Cabin (DMS)
          </span>
          <Activity className="w-4 h-4 text-[#17B26A]" />
        </div>

        <div className="flex items-center justify-between mt-2">
          <span
            className={`text-sm font-semibold truncate max-w-[130px] ${
              isDrowsy ? 'text-[#F04438]' : 'text-[#16202A]'
            }`}
          >
            {driverStateText}
          </span>
          <TGStatusBadge
            variant={isDrowsy ? 'critical' : driverStateText.includes('Chưa') ? 'neutral' : 'safe'}
            size="sm"
            showIcon={false}
          >
            {isDrowsy ? 'Cảnh báo' : driverStateText.includes('Chưa') ? 'Chưa kết nối' : 'Tỉnh táo'}
          </TGStatusBadge>
        </div>
      </TGCard>
    </div>
  );
});
