'use client';

import React from 'react';
import { Inbox, type LucideIcon } from 'lucide-react';
import { TGButton } from './TGButton';

export interface TGEmptyStateProps {
  icon?: LucideIcon | React.ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function TGEmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  className = '',
}: TGEmptyStateProps) {
  return (
    <div
      className={`p-8 text-center bg-white rounded-[10px] border border-[#E4E9EF] flex flex-col items-center justify-center select-none ${className}`}
    >
      <div className="w-12 h-12 rounded-[10px] bg-[#F1F4F7] border border-[#E4E9EF] flex items-center justify-center text-[#98A2B3] mb-3">
        {icon ? (
          React.isValidElement(icon) ? (
            icon
          ) : (
            React.createElement(icon as any, { className: 'w-6 h-6' })
          )
        ) : (
          <Inbox className="w-6 h-6" />
        )}
      </div>

      <h3 className="text-sm font-bold text-[#16202A] mb-1">{title}</h3>

      {description && (
        <p className="text-xs text-[#667085] max-w-sm mb-4 leading-relaxed">
          {description}
        </p>
      )}

      {actionLabel && onAction && (
        <TGButton variant="secondary" size="sm" onClick={onAction}>
          {actionLabel}
        </TGButton>
      )}
    </div>
  );
}
