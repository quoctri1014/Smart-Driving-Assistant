'use client';

import React, { memo } from 'react';
import { AlertOctagon, AlertTriangle, Volume2, ShieldAlert } from 'lucide-react';
import { TGAlert } from '../ui';
import { AlertPriority } from '../../lib/driving/alert-engine';

export interface CriticalAlertBannerProps {
  priority: AlertPriority;
  message: string;
  onDismiss?: () => void;
}

export const CriticalAlertBanner = memo(function CriticalAlertBanner({
  priority,
  message,
  onDismiss,
}: CriticalAlertBannerProps) {
  if (priority === 'NORMAL' || priority === 'UNAVAILABLE') {
    return null;
  }

  const isCritical = priority === 'COLLISION_DANGER' || priority === 'DROWSINESS';
  const variant = isCritical ? 'critical' : 'warning';

  return (
    <div className="w-full select-none animate-bounce-short">
      <TGAlert
        variant={variant}
        icon={isCritical ? AlertOctagon : AlertTriangle}
        title={isCritical ? 'CẢNH BÁO AN TOÀN KHẨN CẤP' : 'LƯU Ý AN TOÀN'}
        message={
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <span className="font-bold text-xs">{message}</span>
            <div className="flex items-center gap-2 text-[11px]">
              <span className="inline-flex items-center gap-1 font-mono">
                <Volume2 className="w-3 h-3" />
                Cảnh báo âm thanh cabin: Đang phát
              </span>
            </div>
          </div>
        }
        onDismiss={onDismiss}
      />
    </div>
  );
});
