'use client';

import React from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';
import { TGButton } from './TGButton';

export interface TGErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
}

export function TGErrorState({
  title = 'Không thể tải dữ liệu',
  message = 'Đã có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại hoặc kiểm tra kết nối máy chủ.',
  onRetry,
  retryLabel = 'Thử lại',
  className = '',
}: TGErrorStateProps) {
  return (
    <div
      className={`p-8 text-center bg-[#FEF3F2] rounded-[10px] border border-[#FECDCA] flex flex-col items-center justify-center select-none ${className}`}
    >
      <div className="w-12 h-12 rounded-[10px] bg-[#FEE4E2] border border-[#FECDCA] flex items-center justify-center text-[#F04438] mb-3">
        <AlertOctagon className="w-6 h-6" />
      </div>

      <h3 className="text-sm font-bold text-[#B42318] mb-1">{title}</h3>

      <p className="text-xs text-[#7A271A] max-w-sm mb-4 leading-relaxed">
        {message}
      </p>

      {onRetry && (
        <TGButton
          variant="danger"
          size="sm"
          onClick={onRetry}
          leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
        >
          {retryLabel}
        </TGButton>
      )}
    </div>
  );
}
