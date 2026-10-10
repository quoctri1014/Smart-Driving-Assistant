'use client';

import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Info,
  X,
  type LucideIcon,
} from 'lucide-react';
import { SignalVariant } from './TGSignalLine';

export interface TGAlertProps {
  variant?: SignalVariant;
  title?: string;
  message?: React.ReactNode;
  children?: React.ReactNode;
  icon?: LucideIcon | React.ReactNode;
  onDismiss?: () => void;
  className?: string;
}

const ALERT_STYLES: Record<
  string,
  { bg: string; border: string; text: string; subtext: string; iconColor: string; defaultIcon: LucideIcon }
> = {
  safe: {
    bg: 'bg-[#ECFDF3]',
    border: 'border-[#A6F4C5]',
    text: 'text-[#027A48]',
    subtext: 'text-[#05603A]',
    iconColor: 'text-[#12B76A]',
    defaultIcon: CheckCircle2,
  },
  success: {
    bg: 'bg-[#ECFDF3]',
    border: 'border-[#A6F4C5]',
    text: 'text-[#027A48]',
    subtext: 'text-[#05603A]',
    iconColor: 'text-[#12B76A]',
    defaultIcon: CheckCircle2,
  },
  warning: {
    bg: 'bg-[#FFFAEB]',
    border: 'border-[#FEDF89]',
    text: 'text-[#B54708]',
    subtext: 'text-[#93370D]',
    iconColor: 'text-[#F79009]',
    defaultIcon: AlertTriangle,
  },
  critical: {
    bg: 'bg-[#FEF3F2]',
    border: 'border-[#FECDCA]',
    text: 'text-[#B42318]',
    subtext: 'text-[#912018]',
    iconColor: 'text-[#F04438]',
    defaultIcon: AlertOctagon,
  },
  danger: {
    bg: 'bg-[#FEF3F2]',
    border: 'border-[#FECDCA]',
    text: 'text-[#B42318]',
    subtext: 'text-[#912018]',
    iconColor: 'text-[#F04438]',
    defaultIcon: AlertOctagon,
  },
  info: {
    bg: 'bg-[#EFF8FF]',
    border: 'border-[#B2DDFF]',
    text: 'text-[#175CD3]',
    subtext: 'text-[#1849A9]',
    iconColor: 'text-[#2E90FA]',
    defaultIcon: Info,
  },
  primary: {
    bg: 'bg-[#EFF4FF]',
    border: 'border-[#B2CCFF]',
    text: 'text-[#175CD3]',
    subtext: 'text-[#1849A9]',
    iconColor: 'text-[#175CD3]',
    defaultIcon: Info,
  },
  neutral: {
    bg: 'bg-[#F1F4F7]',
    border: 'border-[#D0D7DE]',
    text: 'text-[#16202A]',
    subtext: 'text-[#667085]',
    iconColor: 'text-[#667085]',
    defaultIcon: Info,
  },
  default: {
    bg: 'bg-[#F1F4F7]',
    border: 'border-[#D0D7DE]',
    text: 'text-[#16202A]',
    subtext: 'text-[#667085]',
    iconColor: 'text-[#667085]',
    defaultIcon: Info,
  },
};

export function TGAlert({
  variant = 'info',
  title,
  message,
  children,
  icon,
  onDismiss,
  className = '',
}: TGAlertProps) {
  const style = ALERT_STYLES[variant] || ALERT_STYLES.info;
  const DefaultIcon = style.defaultIcon;

  return (
    <div
      className={`rounded-[8px] border p-3.5 flex items-start gap-3 transition-all ${style.bg} ${style.border} ${className}`}
      role="alert"
    >
      <div className={`shrink-0 mt-0.5 ${style.iconColor}`}>
        {icon ? (
          React.isValidElement(icon) ? (
            icon
          ) : (
            React.createElement(icon as any, { className: 'w-4 h-4' })
          )
        ) : (
          <DefaultIcon className="w-4 h-4" />
        )}
      </div>

      <div className="flex-1 text-xs">
        {title && (
          <h4 className={`font-bold leading-none mb-1 ${style.text}`}>{title}</h4>
        )}
        <div className={`leading-relaxed ${style.subtext}`}>
          {message || children}
        </div>
      </div>

      {onDismiss && (
        <button
          onClick={onDismiss}
          className={`p-1 rounded hover:bg-black/5 ${style.text} transition-colors shrink-0`}
          aria-label="Đóng thông báo"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}

// Backward-compatible export
export const AlertBanner = TGAlert;
