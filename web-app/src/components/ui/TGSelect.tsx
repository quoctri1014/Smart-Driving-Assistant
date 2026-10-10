'use client';

import React, { forwardRef } from 'react';
import { ChevronDown, AlertCircle } from 'lucide-react';

export interface TGSelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface TGSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  hint?: string;
  error?: string;
  options?: TGSelectOption[];
  leftIcon?: React.ReactNode;
  wrapperClassName?: string;
}

export const TGSelect = forwardRef<HTMLSelectElement, TGSelectProps>(
  (
    {
      label,
      hint,
      error,
      options = [],
      leftIcon,
      children,
      className = '',
      wrapperClassName = '',
      disabled,
      id,
      ...props
    },
    ref
  ) => {
    const selectId = id || (label ? `tg-select-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

    return (
      <div className={`w-full space-y-1.5 ${wrapperClassName}`}>
        {label && (
          <label
            htmlFor={selectId}
            className="block text-sm font-medium text-[#344054] tracking-tight"
          >
            {label}
            {props.required && <span className="text-[#F04438] ml-1">*</span>}
          </label>
        )}

        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3 flex items-center pointer-events-none text-[#667085]">
              {leftIcon}
            </div>
          )}

          <select
            id={selectId}
            ref={ref}
            disabled={disabled}
            className={`w-full h-10 appearance-none rounded-[8px] border bg-white px-3.5 pr-9 text-sm text-[#16202A] transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-[#175CD3]/20 focus:border-[#175CD3] disabled:bg-[#F1F4F7] disabled:text-[#98A2B3] disabled:cursor-not-allowed cursor-pointer ${
              leftIcon ? 'pl-9' : ''
            } ${
              error
                ? 'border-[#F04438] focus:border-[#F04438] focus:ring-[#F04438]/20'
                : 'border-[#E4E9EF] hover:border-[#D0D7DE]'
            } ${className}`}
            {...props}
          >
            {options.length > 0
              ? options.map((opt) => (
                  <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                    {opt.label}
                  </option>
                ))
              : children}
          </select>

          <div className="absolute right-3 flex items-center pointer-events-none text-[#667085]">
            {error ? (
              <AlertCircle className="w-4 h-4 text-[#F04438]" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </div>
        </div>

        {error ? (
          <p className="text-xs font-medium text-[#F04438] mt-1">{error}</p>
        ) : hint ? (
          <p className="text-xs text-[#667085] mt-1">{hint}</p>
        ) : null}
      </div>
    );
  }
);

TGSelect.displayName = 'TGSelect';
