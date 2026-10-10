'use client';

import React from 'react';
import { Search, RotateCcw } from 'lucide-react';
import { TGButton } from './TGButton';

export interface TGFilterBarProps {
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  searchPlaceholder?: string;
  totalCount?: number;
  filteredCount?: number;
  itemLabel?: string;
  onReset?: () => void;
  children?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export function TGFilterBar({
  searchValue,
  onSearchChange,
  searchPlaceholder = 'Tìm kiếm dữ liệu...',
  totalCount,
  filteredCount,
  itemLabel = 'mục',
  onReset,
  children,
  actions,
  className = '',
}: TGFilterBarProps) {
  const isFiltered =
    Boolean(searchValue) || (totalCount !== undefined && filteredCount !== undefined && filteredCount < totalCount);

  return (
    <div
      className={`bg-white border border-[#E4E9EF] rounded-[10px] p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-[0_1px_2px_rgba(16,24,40,0.04)] mb-4 ${className}`}
    >
      {/* Left: Search + Filters */}
      <div className="flex flex-1 items-center gap-2.5 flex-wrap">
        {onSearchChange !== undefined && (
          <div className="relative min-w-[200px] max-w-sm flex-1">
            <Search className="w-4 h-4 text-[#98A2B3] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchValue ?? ''}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder={searchPlaceholder}
              className="w-full h-9 pl-9 pr-3 rounded-[8px] border border-[#E4E9EF] bg-[#F8FAFC] text-xs text-[#16202A] placeholder-[#98A2B3] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#175CD3]/20 focus:border-[#175CD3] transition-all"
            />
          </div>
        )}

        {children}

        {isFiltered && onReset && (
          <TGButton
            variant="ghost"
            size="sm"
            onClick={onReset}
            leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
            className="text-xs text-[#667085] hover:text-[#16202A]"
          >
            Đặt lại
          </TGButton>
        )}
      </div>

      {/* Right: Counter & Actions */}
      <div className="flex items-center gap-3 shrink-0 self-end md:self-auto">
        {totalCount !== undefined && (
          <div className="text-xs text-[#667085] whitespace-nowrap">
            {filteredCount !== undefined && filteredCount !== totalCount ? (
              <span>
                Hiển thị <strong className="text-[#16202A]">{filteredCount}</strong> / {totalCount} {itemLabel}
              </span>
            ) : (
              <span>
                Tổng cộng <strong className="text-[#16202A]">{totalCount}</strong> {itemLabel}
              </span>
            )}
          </div>
        )}

        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </div>
  );
}
