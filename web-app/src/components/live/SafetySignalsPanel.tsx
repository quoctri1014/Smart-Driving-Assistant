'use client';

import React, { memo } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  Ruler,
  Activity,
  Gauge,
  CheckCircle2,
  XCircle,
  Eye,
} from 'lucide-react';
import { TGCard, TGCardHeader, TGCardTitle, TGCardContent, TGStatusBadge, TGSignalLine } from '../ui';
import { SignalVariant } from '../ui/TGSignalLine';

export interface SafetySignalsPanelProps {
  distanceStatus?: 'safe' | 'warning' | 'critical';
  distanceValue?: string;
  seatbeltStatus?: 'safe' | 'critical';
  drowsinessStatus?: 'safe' | 'warning' | 'critical';
  drowsinessValue?: string;
  collisionStatus?: 'safe' | 'warning' | 'critical';
  collisionValue?: string;
  speedStatus?: 'safe' | 'warning' | 'critical';
  speedValue?: string;
}

interface SignalRowItem {
  id: string;
  label: string;
  sublabel: string;
  status: SignalVariant;
  statusText: string;
  icon: React.ReactNode;
}

export const SafetySignalsPanel = memo(function SafetySignalsPanel({
  distanceStatus = 'safe',
  distanceValue = 'Đang đo đạc...',
  seatbeltStatus = 'safe',
  drowsinessStatus = 'safe',
  drowsinessValue = 'Đang theo dõi...',
  collisionStatus = 'safe',
  collisionValue = 'Đang theo dõi...',
  speedStatus = 'safe',
  speedValue = 'Đang đo đạc...',
}: SafetySignalsPanelProps) {
  const signalRows: SignalRowItem[] = [
    {
      id: 'distance',
      label: 'Khoảng Cách An Toàn',
      sublabel: distanceValue,
      status: distanceStatus,
      statusText: distanceStatus === 'safe' ? 'Đạt chuẩn' : distanceStatus === 'warning' ? 'Khoảng cách gần' : 'Nguy cơ va chạm',
      icon: <Ruler className="w-4 h-4 text-[#0E9384]" />,
    },
    {
      id: 'seatbelt',
      label: 'Thắt Dây An Toàn',
      sublabel: seatbeltStatus === 'safe' ? 'Đã cài chốt dây ghế lái' : 'Chưa thắt dây an toàn',
      status: seatbeltStatus,
      statusText: seatbeltStatus === 'safe' ? 'Tuân thủ' : 'Vi phạm',
      icon: <CheckCircle2 className={`w-4 h-4 ${seatbeltStatus === 'safe' ? 'text-[#17B26A]' : 'text-[#F04438]'}`} />,
    },
    {
      id: 'drowsiness',
      label: 'Cảnh Giác & Buồn Ngủ',
      sublabel: drowsinessValue,
      status: drowsinessStatus,
      statusText: drowsinessStatus === 'safe' ? 'Tỉnh táo' : drowsinessStatus === 'warning' ? 'Mất tập trung' : 'Ngủ gật nguy hiểm',
      icon: <Eye className="w-4 h-4 text-[#175CD3]" />,
    },
    {
      id: 'collision',
      label: 'Cảnh Báo Va Chạm Sớm',
      sublabel: collisionValue,
      status: collisionStatus,
      statusText: collisionStatus === 'safe' ? 'An toàn' : collisionStatus === 'warning' ? 'Cần giảm tốc' : 'Phanh khẩn cấp',
      icon: <AlertTriangle className="w-4 h-4 text-[#F79009]" />,
    },
    {
      id: 'speed',
      label: 'Tuân Thủ Giới Hạn Tốc Độ',
      sublabel: speedValue,
      status: speedStatus,
      statusText: speedStatus === 'safe' ? 'Đúng tốc độ' : speedStatus === 'warning' ? 'Cận giới hạn' : 'Vượt tốc độ',
      icon: <Gauge className="w-4 h-4 text-[#2E90FA]" />,
    },
  ];

  return (
    <TGCard variant="default" className="flex flex-col select-none">
      <TGCardHeader className="py-3 px-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-[#175CD3]" />
          <TGCardTitle className="text-xs">Tín Hiệu Giám Sát An Toàn</TGCardTitle>
        </div>
      </TGCardHeader>

      <TGCardContent className="p-0 divide-y divide-[#E4E9EF]">
        {signalRows.map((row) => (
          <div
            key={row.id}
            className="relative px-4 py-2.5 flex items-center justify-between gap-3 hover:bg-[#F8FAFC] transition-colors"
          >
            {/* Left Signal Indicator */}
            <TGSignalLine variant={row.status} placement="left" size="sm" />

            <div className="flex items-center gap-2.5 min-w-0">
              <div className="p-1 rounded-[6px] bg-[#F1F4F7] shrink-0">
                {row.icon}
              </div>
              <div className="truncate">
                <span className="text-xs font-bold text-[#16202A] block truncate">
                  {row.label}
                </span>
                <span className="text-[11px] text-[#667085] truncate block">
                  {row.sublabel}
                </span>
              </div>
            </div>

            <TGStatusBadge
              variant={row.status}
              size="sm"
              showIcon={false}
              className="shrink-0 font-semibold"
            >
              {row.statusText}
            </TGStatusBadge>
          </div>
        ))}
      </TGCardContent>
    </TGCard>
  );
});
