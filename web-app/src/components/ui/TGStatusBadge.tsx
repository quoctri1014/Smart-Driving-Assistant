'use client';

import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Info,
  ShieldCheck,
  CircleDot,
  type LucideIcon,
} from 'lucide-react';
import { SignalVariant } from './TGSignalLine';

export interface TGStatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: SignalVariant;
  size?: 'sm' | 'md' | 'lg';
  icon?: LucideIcon | React.ReactNode;
  showIcon?: boolean;
  pulse?: boolean;
}

const BADGE_STYLES: Record<
  string,
  { bg: string; text: string; border: string; defaultIcon: LucideIcon }
> = {
  safe: {
    bg: 'bg-[#ECFDF3]',
    text: 'text-[#027A48]',
    border: 'border-[#A6F4C5]',
    defaultIcon: CheckCircle2,
  },
  success: {
    bg: 'bg-[#ECFDF3]',
    text: 'text-[#027A48]',
    border: 'border-[#A6F4C5]',
    defaultIcon: CheckCircle2,
  },
  warning: {
    bg: 'bg-[#FFFAEB]',
    text: 'text-[#B54708]',
    border: 'border-[#FEDF89]',
    defaultIcon: AlertTriangle,
  },
  critical: {
    bg: 'bg-[#FEF3F2]',
    text: 'text-[#B42318]',
    border: 'border-[#FECDCA]',
    defaultIcon: AlertOctagon,
  },
  danger: {
    bg: 'bg-[#FEF3F2]',
    text: 'text-[#B42318]',
    border: 'border-[#FECDCA]',
    defaultIcon: AlertOctagon,
  },
  info: {
    bg: 'bg-[#EFF8FF]',
    text: 'text-[#175CD3]',
    border: 'border-[#B2DDFF]',
    defaultIcon: Info,
  },
  primary: {
    bg: 'bg-[#EFF4FF]',
    text: 'text-[#175CD3]',
    border: 'border-[#B2CCFF]',
    defaultIcon: ShieldCheck,
  },
  neutral: {
    bg: 'bg-[#F1F4F7]',
    text: 'text-[#344054]',
    border: 'border-[#D0D7DE]',
    defaultIcon: CircleDot,
  },
  default: {
    bg: 'bg-[#F1F4F7]',
    text: 'text-[#344054]',
    border: 'border-[#D0D7DE]',
    defaultIcon: CircleDot,
  },
};

const BADGE_SIZES = {
  sm: 'px-2 py-0.5 text-xs font-medium gap-1',
  md: 'px-2.5 py-1 text-xs font-semibold gap-1.5',
  lg: 'px-3 py-1.5 text-sm font-semibold gap-2',
};

const ICON_SIZES = {
  sm: 'w-3.5 h-3.5',
  md: 'w-3.5 h-3.5',
  lg: 'w-4 h-4',
};

export function TGStatusBadge({
  children,
  variant = 'neutral',
  size = 'md',
  icon,
  showIcon = true,
  pulse = false,
  className = '',
  ...props
}: TGStatusBadgeProps) {
  const style = BADGE_STYLES[variant] || BADGE_STYLES.neutral;
  const DefaultIcon = style.defaultIcon;

  return (
    <span
      className={`inline-flex items-center justify-center rounded-[6px] border whitespace-nowrap select-none transition-colors ${
        style.bg
      } ${style.text} ${style.border} ${BADGE_SIZES[size]} ${className}`}
      {...props}
    >
      {pulse && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            variant === 'safe' || variant === 'success'
              ? 'bg-[#17B26A]'
              : variant === 'critical' || variant === 'danger'
              ? 'bg-[#F04438]'
              : variant === 'warning'
              ? 'bg-[#F79009]'
              : 'bg-[#2E90FA]'
          } animate-ping mr-0.5`}
        />
      )}

      {showIcon && (
        icon ? (
          React.isValidElement(icon) ? (
            <span className="shrink-0">{icon}</span>
          ) : (
            React.createElement(icon as any, { className: `${ICON_SIZES[size]} shrink-0` })
          )
        ) : (
          <DefaultIcon className={`${ICON_SIZES[size]} shrink-0`} />
        )
      )}

      <span>{children}</span>
    </span>
  );
}

// Backward-compatible export
export const Badge = TGStatusBadge;
