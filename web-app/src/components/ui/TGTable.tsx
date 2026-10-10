'use client';

import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { TGSignalLine, SignalVariant } from './TGSignalLine';

export interface TGTableProps extends React.TableHTMLAttributes<HTMLTableElement> {
  wrapperClassName?: string;
}

export function TGTable({ className = '', wrapperClassName = '', ...props }: TGTableProps) {
  return (
    <div
      className={`w-full overflow-x-auto rounded-[10px] border border-[#E4E9EF] bg-white shadow-[0_1px_2px_rgba(16,24,40,0.04)] ${wrapperClassName}`}
    >
      <table className={`w-full text-sm text-left text-[#16202A] ${className}`} {...props} />
    </div>
  );
}

export function TGTableHeader({
  className = '',
  ...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead
      className={`bg-[#F8FAFC] text-xs font-semibold text-[#475467] uppercase tracking-wider border-b border-[#E4E9EF] select-none ${className}`}
      {...props}
    />
  );
}

export function TGTableBody({
  className = '',
  ...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody className={`divide-y divide-[#E4E9EF] ${className}`} {...props} />;
}

export interface TGTableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  signalVariant?: SignalVariant;
  selected?: boolean;
}

export function TGTableRow({
  signalVariant,
  selected = false,
  className = '',
  children,
  ...props
}: TGTableRowProps) {
  return (
    <tr
      className={`relative transition-colors ${
        selected ? 'bg-[#EFF4FF]' : 'hover:bg-[#F8FAFC]'
      } ${className}`}
      {...props}
    >
      {signalVariant && (
        <td className="w-1 p-0 absolute left-0 top-0 bottom-0 pointer-events-none">
          <TGSignalLine variant={signalVariant} placement="left" size="sm" />
        </td>
      )}
      {children}
    </tr>
  );
}

export function TGTableHead({
  className = '',
  ...props
}: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={`px-4 py-3 font-bold whitespace-nowrap text-[#667085] ${className}`}
      {...props}
    />
  );
}

export function TGTableCell({
  className = '',
  ...props
}: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td
      className={`px-4 py-3 whitespace-nowrap text-[#16202A] align-middle ${className}`}
      {...props}
    />
  );
}

export interface TGPaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  totalItems?: number;
  pageSize?: number;
  className?: string;
}

export function TGPagination({
  currentPage,
  totalPages,
  onPageChange,
  totalItems,
  pageSize,
  className = '',
}: TGPaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div
      className={`px-4 py-3 bg-[#F8FAFC] border-t border-[#E4E9EF] flex items-center justify-between text-xs text-[#667085] select-none ${className}`}
    >
      <div>
        {totalItems !== undefined && pageSize !== undefined ? (
          <span>
            Hiển thị {(currentPage - 1) * pageSize + 1} -{' '}
            {Math.min(currentPage * pageSize, totalItems)} trong số{' '}
            <strong>{totalItems}</strong> mục
          </span>
        ) : (
          <span>
            Trang <strong>{currentPage}</strong> / {totalPages}
          </span>
        )}
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage <= 1}
          className="p-1.5 rounded-[6px] border border-[#E4E9EF] bg-white text-[#667085] hover:bg-[#F1F4F7] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          aria-label="Trang trước"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <span className="px-3 py-1 font-semibold text-[#16202A] bg-white border border-[#E4E9EF] rounded-[6px]">
          {currentPage}
        </span>

        <button
          onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage >= totalPages}
          className="p-1.5 rounded-[6px] border border-[#E4E9EF] bg-white text-[#667085] hover:bg-[#F1F4F7] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          aria-label="Trang sau"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// Backward-compatible exports
export const Table = TGTable;
export const TableHeader = TGTableHeader;
export const TableBody = TGTableBody;
export const TableRow = TGTableRow;
export const TableHead = TGTableHead;
export const TableCell = TGTableCell;
