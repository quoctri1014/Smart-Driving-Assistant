'use client';

import React from 'react';

export type SignalVariant =
  | 'safe'
  | 'warning'
  | 'critical'
  | 'info'
  | 'primary'
  | 'neutral'
  | 'success'
  | 'danger'
  | 'default';

export type SignalPlacement = 'left' | 'top' | 'right' | 'bottom' | 'marker' | 'inline';

interface TGSignalLineProps {
  variant?: SignalVariant;
  placement?: SignalPlacement;
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  className?: string;
}

const VARIANT_COLORS: Record<string, { solid: string; pulse?: string }> = {
  safe: {
    solid: 'bg-[#17B26A]',
    pulse: 'bg-[#17B26A]',
  },
  success: {
    solid: 'bg-[#17B26A]',
    pulse: 'bg-[#17B26A]',
  },
  warning: {
    solid: 'bg-[#F79009]',
    pulse: 'bg-[#F79009]',
  },
  critical: {
    solid: 'bg-[#F04438]',
    pulse: 'bg-[#F04438]',
  },
  danger: {
    solid: 'bg-[#F04438]',
    pulse: 'bg-[#F04438]',
  },
  info: {
    solid: 'bg-[#2E90FA]',
    pulse: 'bg-[#2E90FA]',
  },
  primary: {
    solid: 'bg-[#175CD3]',
    pulse: 'bg-[#175CD3]',
  },
  neutral: {
    solid: 'bg-[#D0D7DE]',
  },
  default: {
    solid: 'bg-[#D0D7DE]',
  },
};

export function TGSignalLine({
  variant = 'safe',
  placement = 'left',
  size = 'md',
  animated = false,
  className = '',
}: TGSignalLineProps) {
  const color = VARIANT_COLORS[variant] || VARIANT_COLORS.safe;

  if (placement === 'left') {
    const widthClass = size === 'sm' ? 'w-0.5' : size === 'lg' ? 'w-1.5' : 'w-1';
    return (
      <div
        className={`absolute left-0 top-0 bottom-0 ${widthClass} ${color.solid} rounded-l-[10px] ${
          animated ? 'animate-signal-pulse' : ''
        } ${className}`}
        aria-hidden="true"
      />
    );
  }

  if (placement === 'top') {
    const heightClass = size === 'sm' ? 'h-0.5' : size === 'lg' ? 'h-1.5' : 'h-1';
    return (
      <div
        className={`absolute left-0 right-0 top-0 ${heightClass} ${color.solid} rounded-t-[10px] ${
          animated ? 'animate-signal-pulse' : ''
        } ${className}`}
        aria-hidden="true"
      />
    );
  }

  if (placement === 'marker') {
    const dotSize = size === 'sm' ? 'w-2 h-2' : size === 'lg' ? 'w-3.5 h-3.5' : 'w-2.5 h-2.5';
    return (
      <span className={`relative flex items-center justify-center ${dotSize} shrink-0 ${className}`}>
        {animated && (
          <span
            className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${color.solid}`}
          />
        )}
        <span className={`relative inline-flex rounded-full ${dotSize} ${color.solid}`} />
      </span>
    );
  }

  if (placement === 'inline') {
    const heightClass = size === 'sm' ? 'h-3' : size === 'lg' ? 'h-5' : 'h-4';
    return (
      <span
        className={`inline-block w-1 ${heightClass} ${color.solid} rounded-full shrink-0 ${className}`}
        aria-hidden="true"
      />
    );
  }

  return (
    <div
      className={`w-1 h-full ${color.solid} rounded-full ${className}`}
      aria-hidden="true"
    />
  );
}
