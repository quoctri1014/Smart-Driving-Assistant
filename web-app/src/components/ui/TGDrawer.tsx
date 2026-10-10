'use client';

import React, { useEffect } from 'react';
import { X, type LucideIcon } from 'lucide-react';

export interface TGDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  icon?: LucideIcon | React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const DRAWER_SIZES = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
};

export function TGDrawer({
  isOpen,
  onClose,
  title,
  subtitle,
  icon,
  children,
  footer,
  size = 'md',
  className = '',
}: TGDrawerProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden select-none">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-[#0C111D]/40 backdrop-blur-[1px] transition-opacity duration-200"
        onClick={onClose}
      />

      {/* Slide-over panel */}
      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div
          className={`w-screen ${DRAWER_SIZES[size]} bg-white border-l border-[#E4E9EF] shadow-[0_20px_24px_-4px_rgba(16,24,40,0.1)] flex flex-col ${className}`}
        >
          {/* Header */}
          <div className="px-5 py-4 border-b border-[#E4E9EF] flex items-center justify-between gap-3 bg-white">
            <div className="flex items-center gap-2.5">
              {icon && (
                <div className="w-8 h-8 rounded-[6px] bg-[#EFF4FF] border border-[#B2CCFF] flex items-center justify-center text-[#175CD3] shrink-0">
                  {React.isValidElement(icon) ? (
                    icon
                  ) : (
                    React.createElement(icon as any, { className: 'w-4 h-4' })
                  )}
                </div>
              )}
              <div>
                <h3 className="text-sm font-bold text-[#16202A]">{title}</h3>
                {subtitle && (
                  <p className="text-xs text-[#667085] mt-0.5">{subtitle}</p>
                )}
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-[6px] text-[#667085] hover:text-[#16202A] hover:bg-[#F1F4F7] transition-colors"
              aria-label="Đóng"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Content */}
          <div className="p-5 flex-1 overflow-y-auto custom-scrollbar text-xs text-[#16202A]">
            {children}
          </div>

          {/* Footer */}
          {footer && (
            <div className="px-5 py-3.5 bg-[#F8FAFC] border-t border-[#E4E9EF] flex items-center justify-end gap-2.5">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
