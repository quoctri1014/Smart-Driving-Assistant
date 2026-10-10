'use client';

import React from 'react';
import { TGSignalLine, SignalVariant, SignalPlacement } from './TGSignalLine';

export interface TGCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'subtle' | 'elevated' | 'glass';
  signalVariant?: SignalVariant;
  signalPlacement?: SignalPlacement;
  signalAnimated?: boolean;
}

export function TGCard({
  children,
  variant = 'default',
  signalVariant,
  signalPlacement = 'left',
  signalAnimated = false,
  className = '',
  ...props
}: TGCardProps) {
  const variantStyles = {
    default: 'bg-white border border-[#E4E9EF] shadow-[0_1px_3px_rgba(16,24,40,0.06)]',
    subtle: 'bg-[#F1F4F7] border border-[#E4E9EF]',
    elevated: 'bg-white border border-[#E4E9EF] shadow-[0_4px_12px_-2px_rgba(16,24,40,0.08)]',
    glass: 'bg-white/90 backdrop-blur-sm border border-[#E4E9EF]',
  };

  return (
    <div
      className={`relative rounded-[10px] overflow-hidden transition-all duration-150 ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {signalVariant && (
        <TGSignalLine
          variant={signalVariant}
          placement={signalPlacement}
          animated={signalAnimated}
        />
      )}
      {children}
    </div>
  );
}

export function TGCardHeader({
  className = '',
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`px-5 py-4 border-b border-[#E4E9EF] flex items-center justify-between gap-3 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function TGCardTitle({
  className = '',
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={`text-sm font-bold text-[#16202A] tracking-tight flex items-center gap-2 ${className}`}
      {...props}
    >
      {children}
    </h3>
  );
}

export function TGCardDescription({
  className = '',
  children,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={`text-xs text-[#667085] mt-0.5 ${className}`}
      {...props}
    >
      {children}
    </p>
  );
}

export function TGCardContent({
  className = '',
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`p-5 text-sm text-[#16202A] ${className}`} {...props}>
      {children}
    </div>
  );
}

export function TGCardFooter({
  className = '',
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`px-5 py-3.5 bg-[#F6F8FA] border-t border-[#E4E9EF] flex items-center justify-between gap-3 text-xs text-[#667085] ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

// Backward-compatible exports
export const Card = TGCard;
export const CardHeader = TGCardHeader;
export const CardTitle = TGCardTitle;
export const CardContent = TGCardContent;
export const CardFooter = TGCardFooter;
