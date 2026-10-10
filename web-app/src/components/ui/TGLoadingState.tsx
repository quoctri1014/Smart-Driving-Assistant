'use client';

import React from 'react';
import { Loader2 } from 'lucide-react';

export interface TGLoadingStateProps {
  message?: string;
  subMessage?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function TGLoadingState({
  message = 'Đang tải dữ liệu...',
  subMessage,
  size = 'md',
  className = '',
}: TGLoadingStateProps) {
  const spinnerSizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div
      className={`p-8 text-center bg-white rounded-[10px] border border-[#E4E9EF] flex flex-col items-center justify-center select-none ${className}`}
    >
      <Loader2 className={`${spinnerSizes[size]} text-[#175CD3] animate-spin mb-3`} />
      <p className="text-xs font-semibold text-[#16202A]">{message}</p>
      {subMessage && (
        <p className="text-[11px] text-[#667085] mt-1">{subMessage}</p>
      )}
    </div>
  );
}

export function TGSkeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse bg-[#F1F4F7] rounded-[6px] ${className}`} />;
}
