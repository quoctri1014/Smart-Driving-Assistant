'use client';

import React, { memo, useState } from 'react';
import {
  Clock,
  Filter,
  CheckCircle2,
  XCircle,
  AlertOctagon,
  AlertTriangle,
  Info,
  Image as ImageIcon,
  X,
  ExternalLink,
} from 'lucide-react';

export interface TimelineEventItem {
  id: string;
  timestamp: string;
  level: 'critical' | 'warning' | 'info';
  title: string;
  details: string;
  imageUrl?: string;
  status?: 'pending' | 'confirmed' | 'rejected';
}

export interface RealtimeEventTimelineProps {
  events: TimelineEventItem[];
  onConfirmEvent?: (id: string) => void;
  onRejectEvent?: (id: string) => void;
  className?: string;
}

export const RealtimeEventTimeline = memo(function RealtimeEventTimeline({
  events = [],
  onConfirmEvent,
  onRejectEvent,
  className = '',
}: RealtimeEventTimelineProps) {
  const [filterLevel, setFilterLevel] = useState<'all' | 'critical' | 'warning' | 'info'>('all');
  const [selectedEvidence, setSelectedEvidence] = useState<TimelineEventItem | null>(null);

  const filteredEvents = events.filter((ev) => {
    if (filterLevel === 'all') return true;
    return ev.level === filterLevel;
  });

  return (
    <div
      className={`w-full bg-white border border-[#E4E9EF] rounded-[10px] overflow-hidden shadow-sm flex flex-col select-none flex-1 min-h-[300px] transition-all ${className}`}
    >
      {/* ── HEADER ── */}
      <div className="py-2.5 px-3.5 border-b border-[#E4E9EF] bg-[#F8FAFC] flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-[#EFF4FF] flex items-center justify-center text-[#175CD3]">
            <Clock className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-bold text-[#16202A] tracking-tight">
            Sự Kiện Live
          </span>
          <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-[#EFF4FF] text-[#175CD3] font-bold">
            {events.length}
          </span>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 text-[10px]">
          <button
            onClick={() => setFilterLevel('all')}
            className={`px-2 py-0.5 rounded font-semibold transition-colors cursor-pointer ${
              filterLevel === 'all'
                ? 'bg-[#175CD3] text-white shadow-2xs'
                : 'bg-white text-[#667085] hover:text-[#16202A] border border-[#E4E9EF]'
            }`}
          >
            Tất cả
          </button>
          <button
            onClick={() => setFilterLevel('critical')}
            className={`px-2 py-0.5 rounded font-semibold transition-colors cursor-pointer ${
              filterLevel === 'critical'
                ? 'bg-[#F04438] text-white shadow-2xs'
                : 'bg-white text-[#F04438] hover:bg-[#FEF3F2] border border-[#FECDCA]'
            }`}
          >
            Nguy hiểm
          </button>
          <button
            onClick={() => setFilterLevel('warning')}
            className={`px-2 py-0.5 rounded font-semibold transition-colors cursor-pointer ${
              filterLevel === 'warning'
                ? 'bg-[#F79009] text-white shadow-2xs'
                : 'bg-white text-[#B54708] hover:bg-[#FFFAEB] border border-[#FEDF89]'
            }`}
          >
            Cảnh báo
          </button>
        </div>
      </div>

      {/* ── TIMELINE LIST (TỰ ĐỘNG GIÃN VÀ CÓ THANH CUỘN RÕ NÉT) ── */}
      <div className="p-3 flex-1 min-h-[220px] max-h-[460px] xl:max-h-[520px] overflow-y-auto space-y-2 timeline-scrollbar">
        {filteredEvents.length === 0 ? (
          <div className="h-full min-h-[190px] flex flex-col items-center justify-center py-8 text-center text-[#98A2B3]">
            <div className="w-9 h-9 rounded-full bg-[#EFF4FF] flex items-center justify-center mb-2 text-[#175CD3]">
              <Clock className="w-5 h-5 text-[#175CD3]" />
            </div>
            <span className="text-xs font-bold text-[#16202A]">Chưa có vi phạm / sự kiện mới</span>
            <span className="text-[11px] text-[#667085] mt-0.5">Tự động ghi nhận khi AI phát hiện vi phạm</span>
          </div>
        ) : (
          filteredEvents.map((ev) => {
            const isCrit = ev.level === 'critical';
            const isWarn = ev.level === 'warning';

            return (
              <div
                key={ev.id}
                className={`p-2.5 rounded-[8px] border transition-all text-xs ${
                  isCrit
                    ? 'border-[#FECDCA] bg-[#FEF3F2]/60 hover:bg-[#FEF3F2]'
                    : isWarn
                    ? 'border-[#FEDF89] bg-[#FFFAEB]/60 hover:bg-[#FFFAEB]'
                    : 'border-[#E4E9EF] bg-[#F8FAFC] hover:bg-white'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2">
                    <span
                      className={`w-2 h-2 rounded-full mt-1 shrink-0 ${
                        isCrit ? 'bg-[#F04438] animate-ping' : isWarn ? 'bg-[#F79009]' : 'bg-[#12B76A]'
                      }`}
                    />
                    <div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-bold text-[#16202A] text-[11px]">
                          {ev.title}
                        </span>
                        <span className="text-[10px] text-[#667085] font-mono">
                          {ev.timestamp}
                        </span>
                      </div>
                      <p className="text-[11px] text-[#475467] mt-0.5 leading-snug">
                        {ev.details}
                      </p>
                    </div>
                  </div>

                  {/* Actions: View Image / Confirm / Reject */}
                  <div className="flex items-center gap-1 shrink-0">
                    {ev.imageUrl && (
                      <button
                        onClick={() => setSelectedEvidence(ev)}
                        className="p-1 rounded hover:bg-black/5 text-[#175CD3] transition-colors"
                        title="Xem ảnh bằng chứng vi phạm"
                      >
                        <ImageIcon className="w-3.5 h-3.5" />
                      </button>
                    )}

                    {ev.status !== 'confirmed' && ev.status !== 'rejected' ? (
                      <>
                        <button
                          onClick={() => onConfirmEvent?.(ev.id)}
                          className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#12B76A] hover:bg-[#0E9384] text-white transition-colors"
                          title="Xác nhận vi phạm hợp lệ"
                        >
                          Xác nhận
                        </button>
                        <button
                          onClick={() => onRejectEvent?.(ev.id)}
                          className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-white hover:bg-[#F1F4F7] text-[#667085] border border-[#D0D7DE] transition-colors"
                          title="Bác bỏ cảnh báo giả"
                        >
                          Bác bỏ
                        </button>
                      </>
                    ) : (
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          ev.status === 'confirmed'
                            ? 'bg-[#ECFDF3] text-[#067647]'
                            : 'bg-[#F8FAFC] text-[#667085]'
                        }`}
                      >
                        {ev.status === 'confirmed' ? 'Đã xác nhận' : 'Đã bác bỏ'}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* ── MODAL XEM ẢNH BẰNG CHỨNG ── */}
      {selectedEvidence && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-[12px] border border-[#E4E9EF] max-w-lg w-full overflow-hidden shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="p-3.5 border-b border-[#E4E9EF] flex items-center justify-between bg-[#F8FAFC]">
              <div className="flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-[#175CD3]" />
                <span className="text-xs font-bold text-[#16202A]">
                  Ảnh Bằng Chứng Vi Phạm • {selectedEvidence.timestamp}
                </span>
              </div>
              <button
                onClick={() => setSelectedEvidence(null)}
                className="p-1 rounded-full hover:bg-black/10 text-[#667085]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 space-y-3">
              <div className="relative aspect-video bg-black rounded-[8px] overflow-hidden flex items-center justify-center">
                {selectedEvidence.imageUrl ? (
                  <img
                    src={selectedEvidence.imageUrl}
                    alt="Bằng chứng vi phạm"
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <div className="text-white/60 text-xs">Ảnh snapshot thời điểm phát hiện</div>
                )}
              </div>

              <div className="p-2.5 rounded-[6px] bg-[#F8FAFC] border border-[#E4E9EF] text-xs space-y-1">
                <div className="font-bold text-[#16202A]">{selectedEvidence.title}</div>
                <div className="text-[11px] text-[#475467]">{selectedEvidence.details}</div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#E4E9EF]">
                <button
                  onClick={() => {
                    onRejectEvent?.(selectedEvidence.id);
                    setSelectedEvidence(null);
                  }}
                  className="px-3 py-1.5 rounded-[6px] text-xs font-medium text-[#667085] hover:bg-[#F1F4F7] border border-[#D0D7DE]"
                >
                  Bác bỏ
                </button>
                <button
                  onClick={() => {
                    onConfirmEvent?.(selectedEvidence.id);
                    setSelectedEvidence(null);
                  }}
                  className="px-3.5 py-1.5 rounded-[6px] text-xs font-bold bg-[#175CD3] hover:bg-[#154EB7] text-white"
                >
                  Xác nhận vi phạm
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});
