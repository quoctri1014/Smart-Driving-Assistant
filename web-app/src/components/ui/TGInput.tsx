'use client';

import React, { forwardRef } from 'react';
import { AlertCircle } from 'lucide-react';

export interface TGInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  wrapperClassName?: string;
}

export const TGInput = forwardRef<HTMLInputElement, TGInputProps>(
  (
    {
      label,
      hint,
      error,
      leftIcon,
      rightIcon,
      className = '',
      wrapperClassName = '',
      disabled,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || (label ? `tg-input-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

    return (
      <div className={`w-full space-y-1.5 ${wrapperClassName}`}>
        {label && (
          <label
            htmlFor={inputId}
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

          <input
            id={inputId}
            ref={ref}
            disabled={disabled}
            className={`w-full h-10 rounded-[8px] border bg-white px-3.5 text-sm text-[#16202A] placeholder-[#98A2B3] transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-[#175CD3]/20 focus:border-[#175CD3] disabled:bg-[#F1F4F7] disabled:text-[#98A2B3] disabled:cursor-not-allowed ${
              leftIcon ? 'pl-9' : ''
            } ${rightIcon || error ? 'pr-9' : ''} ${
              error
                ? 'border-[#F04438] focus:border-[#F04438] focus:ring-[#F04438]/20'
                : 'border-[#E4E9EF] hover:border-[#D0D7DE]'
            } ${className}`}
            {...props}
          />

          {error ? (
            <div className="absolute right-3 flex items-center pointer-events-none text-[#F04438]">
              <AlertCircle className="w-4 h-4" />
            </div>
          ) : (
            rightIcon && (
              <div className="absolute right-3 flex items-center text-[#667085]">
                {rightIcon}
              </div>
            )
          )}
        </div>

        {error ? (
          <p className="text-xs font-medium text-[#F04438] flex items-center gap-1 mt-1">
            {error}
          </p>
        ) : hint ? (
          <p className="text-xs text-[#667085] mt-1">{hint}</p>
        ) : null}
      </div>
    );
  }
);

TGInput.displayName = 'TGInput';
