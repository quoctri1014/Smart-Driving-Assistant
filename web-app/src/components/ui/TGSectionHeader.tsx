'use client';

import React from 'react';

export interface TGSectionHeaderProps {
  title: string;
  description?: string;
  counter?: number | string;
  actions?: React.ReactNode;
  className?: string;
}

export function TGSectionHeader({
  title,
  description,
  counter,
  actions,
  className = '',
}: TGSectionHeaderProps) {
  return (
    <div className={`flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 mb-4 ${className}`}>
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-bold text-[#16202A] tracking-tight">
            {title}
          </h2>
          {counter !== undefined && (
            <span className="px-2 py-0.5 rounded-full bg-[#F1F4F7] border border-[#E4E9EF] text-[11px] font-semibold text-[#667085]">
              {counter}
            </span>
          )}
        </div>
        {description && (
          <p className="text-xs text-[#667085] mt-0.5">{description}</p>
        )}
      </div>

      {actions && (
        <div className="flex items-center gap-2 shrink-0">
          {actions}
        </div>
      )}
    </div>
  );
}
