'use client';

import React from 'react';
import { TrendingUp, TrendingDown, Minus, type LucideIcon } from 'lucide-react';
import { TGCard } from './TGCard';
import { SignalVariant } from './TGSignalLine';

export interface TGMetricProps {
  label: string;
  value: string | number;
  unit?: string;
  subValue?: string;
  trend?: {
    value: string | number;
    direction: 'up' | 'down' | 'neutral';
    label?: string;
  };
  icon?: LucideIcon | React.ReactNode;
  signalVariant?: SignalVariant;
  className?: string;
  onClick?: () => void;
}

export function TGMetric({
  label,
  value,
  unit,
  subValue,
  trend,
  icon,
  signalVariant = 'primary',
  className = '',
  onClick,
}: TGMetricProps) {
  const isClickable = Boolean(onClick);

  return (
    <TGCard
      variant="default"
      signalVariant={signalVariant}
      className={`p-4 transition-all duration-150 ${
        isClickable ? 'cursor-pointer hover:border-[#B2CCFF] hover:shadow-md' : ''
      } ${className}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#667085]">
            {label}
          </p>

          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-extrabold text-[#16202A] tracking-tight font-sans">
              {value}
            </span>
            {unit && <span className="text-xs font-medium text-[#667085]">{unit}</span>}
          </div>

          {subValue && (
            <p className="text-[11px] text-[#98A2B3] mt-0.5">{subValue}</p>
          )}
        </div>

        {icon && (
          <div className="w-9 h-9 rounded-[8px] bg-[#F1F4F7] border border-[#E4E9EF] flex items-center justify-center text-[#175CD3] shrink-0">
            {React.isValidElement(icon) ? (
              icon
            ) : (
              React.createElement(icon as any, { className: 'w-4 h-4' })
            )}
          </div>
        )}
      </div>

      {trend && (
        <div className="mt-3 pt-2.5 border-t border-[#F1F4F7] flex items-center gap-1.5 text-[11px]">
          {trend.direction === 'up' && (
            <span className="inline-flex items-center gap-0.5 text-[#17B26A] font-semibold">
              <TrendingUp className="w-3 h-3" />
              {trend.value}
            </span>
          )}
          {trend.direction === 'down' && (
            <span className="inline-flex items-center gap-0.5 text-[#F04438] font-semibold">
              <TrendingDown className="w-3 h-3" />
              {trend.value}
            </span>
          )}
          {trend.direction === 'neutral' && (
            <span className="inline-flex items-center gap-0.5 text-[#667085] font-semibold">
              <Minus className="w-3 h-3" />
              {trend.value}
            </span>
          )}
          {trend.label && <span className="text-[#98A2B3]">{trend.label}</span>}
        </div>
      )}
    </TGCard>
  );
}
