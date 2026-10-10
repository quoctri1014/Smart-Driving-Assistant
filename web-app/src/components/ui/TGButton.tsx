'use client';

import React from 'react';
import { Loader2 } from 'lucide-react';

export interface TGButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | 'primary'
    | 'secondary'
    | 'outline'
    | 'ghost'
    | 'danger'
    | 'safe'
    | 'success'
    | 'warning'
    | 'glass';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export function TGButton({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}: TGButtonProps) {
  const baseStyles =
    'inline-flex items-center justify-center rounded-[8px] font-semibold transition-all duration-150 select-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none active:scale-[0.98]';

  const variants = {
    primary:
      'bg-[#175CD3] text-white hover:bg-[#154EB7] focus:ring-[#175CD3] shadow-[0_1px_2px_rgba(16,24,40,0.05)] border border-[#175CD3]',
    secondary:
      'bg-white text-[#16202A] hover:bg-[#F1F4F7] focus:ring-[#98A2B3] border border-[#E4E9EF] shadow-[0_1px_2px_rgba(16,24,40,0.04)]',
    outline:
      'bg-transparent text-[#175CD3] hover:bg-[#EFF4FF] focus:ring-[#175CD3] border border-[#B2CCFF]',
    ghost:
      'bg-transparent text-[#667085] hover:text-[#16202A] hover:bg-[#F1F4F7] focus:ring-[#98A2B3]',
    danger:
      'bg-[#F04438] text-white hover:bg-[#D92D20] focus:ring-[#F04438] shadow-[0_1px_2px_rgba(16,24,40,0.05)] border border-[#F04438]',
    safe:
      'bg-[#17B26A] text-white hover:bg-[#129B5C] focus:ring-[#17B26A] shadow-[0_1px_2px_rgba(16,24,40,0.05)] border border-[#17B26A]',
    success:
      'bg-[#17B26A] text-white hover:bg-[#129B5C] focus:ring-[#17B26A] shadow-[0_1px_2px_rgba(16,24,40,0.05)] border border-[#17B26A]',
    warning:
      'bg-[#F79009] text-white hover:bg-[#DC7702] focus:ring-[#F79009] shadow-[0_1px_2px_rgba(16,24,40,0.05)] border border-[#F79009]',
    glass:
      'bg-white/80 backdrop-blur-sm text-[#16202A] hover:bg-white border border-[#E4E9EF] shadow-sm',
  };

  const sizes = {
    sm: 'h-8 px-3 text-xs gap-1.5',
    md: 'h-10 px-4 text-xs font-semibold gap-2',
    lg: 'h-12 px-6 text-sm gap-2.5',
    icon: 'h-9 w-9 p-0 justify-center',
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant] || variants.primary} ${sizes[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : (
        leftIcon && <span className="shrink-0">{leftIcon}</span>
      )}

      {children}

      {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
    </button>
  );
}

// Backward-compatible export
export const Button = TGButton;
