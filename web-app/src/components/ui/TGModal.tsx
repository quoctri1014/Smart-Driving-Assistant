'use client';

import React, { useEffect } from 'react';
import { X, type LucideIcon } from 'lucide-react';

export interface TGModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  icon?: LucideIcon | React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const MODAL_SIZES = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
};

export function TGModal({
  isOpen,
  onClose,
  title,
  subtitle,
  icon,
  children,
  footer,
  size = 'md',
  className = '',
}: TGModalProps) {
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-[#0C111D]/40 backdrop-blur-[2px] transition-opacity duration-200"
        onClick={onClose}
      />

      {/* Modal Card */}
      <div
        className={`relative w-full ${MODAL_SIZES[size]} bg-white rounded-[12px] border border-[#E4E9EF] shadow-[0_20px_24px_-4px_rgba(16,24,40,0.1),0_8px_8px_-4px_rgba(16,24,40,0.04)] overflow-hidden z-10 flex flex-col max-h-[90vh] ${className}`}
        role="dialog"
        aria-modal="true"
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

        {/* Body */}
        <div className="p-5 overflow-y-auto flex-1 custom-scrollbar text-xs text-[#16202A]">
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
  );
}
