'use client';

import React from 'react';
import { TGSignalLine, SignalVariant } from './TGSignalLine';

export interface TGTimelineItem {
  id?: string | number;
  time: string;
  title: string;
  description?: string;
  variant?: SignalVariant;
  icon?: React.ReactNode;
  tags?: React.ReactNode;
}

export interface TGTimelineProps {
  items: TGTimelineItem[];
  className?: string;
}

export function TGTimeline({ items, className = '' }: TGTimelineProps) {
  if (!items || items.length === 0) return null;

  return (
    <div className={`relative pl-6 space-y-6 ${className}`}>
      {/* Background continuous track line */}
      <div className="absolute left-2.5 top-2 bottom-2 w-0.5 bg-[#E4E9EF] -translate-x-1/2" />

      {items.map((item, idx) => {
        const variant = item.variant || 'safe';

        return (
          <div key={item.id ?? idx} className="relative group">
            {/* Marker Dot */}
            <div className="absolute -left-6 top-1 transform -translate-x-1/2 flex items-center justify-center">
              <div className="w-5 h-5 rounded-full bg-white border-2 border-[#E4E9EF] flex items-center justify-center">
                <TGSignalLine variant={variant} placement="marker" size="sm" />
              </div>
            </div>

            {/* Content Card */}
            <div className="bg-white border border-[#E4E9EF] rounded-[8px] p-3 shadow-[0_1px_2px_rgba(16,24,40,0.04)] hover:border-[#D0D7DE] transition-colors">
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-xs font-bold text-[#16202A]">{item.title}</span>
                <span className="text-[11px] font-mono text-[#667085]">{item.time}</span>
              </div>

              {item.description && (
                <p className="text-xs text-[#667085] leading-relaxed mb-2">
                  {item.description}
                </p>
              )}

              {item.tags && (
                <div className="flex items-center gap-1.5 flex-wrap pt-1 border-t border-[#F1F4F7]">
                  {item.tags}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
