'use client';

import React from 'react';
import { ChevronRight, type LucideIcon } from 'lucide-react';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface TGPageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: LucideIcon | React.ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export function TGPageHeader({
  title,
  subtitle,
  icon,
  breadcrumbs,
  badge,
  actions,
  className = '',
}: TGPageHeaderProps) {
  return (
    <div className={`mb-6 space-y-2 select-none ${className}`}>
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center gap-1.5 text-xs text-[#667085]">
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={idx}>
              {idx > 0 && <ChevronRight className="w-3.5 h-3.5 text-[#98A2B3] shrink-0" />}
              {crumb.href ? (
                <a
                  href={crumb.href}
                  className="hover:text-[#175CD3] transition-colors"
                >
                  {crumb.label}
                </a>
              ) : (
                <span className="font-medium text-[#16202A]">{crumb.label}</span>
              )}
            </React.Fragment>
          ))}
        </nav>
      )}

      {/* Main Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-start gap-3">
          {icon && (
            <div className="w-10 h-10 rounded-[8px] bg-[#EFF4FF] border border-[#B2CCFF] flex items-center justify-center text-[#175CD3] shrink-0 mt-0.5">
              {React.isValidElement(icon) ? (
                icon
              ) : (
                React.createElement(icon as any, { className: 'w-5 h-5' })
              )}
            </div>
          )}

          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-xl sm:text-2xl font-bold text-[#16202A] tracking-tight">
                {title}
              </h1>
              {badge && <span className="shrink-0">{badge}</span>}
            </div>

            {subtitle && (
              <p className="text-xs sm:text-sm text-[#667085] mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
        </div>

        {actions && (
          <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}
