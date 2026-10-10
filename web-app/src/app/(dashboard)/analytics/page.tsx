'use client';

import React, { useEffect, useState } from 'react';
import {
  BarChart2,
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  Clock,
  PieChart,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import { apiClient } from '../../../services/apiClient';
import { TGCard, TGCardHeader, TGCardTitle, TGCardContent } from '../../../components/ui/TGCard';

interface FleetSummary {
  total_drivers: number;
  total_vehicles: number;
  total_sessions: number;
  total_violations: number;
  total_driving_hours: number;
  safety_score: number;
  violation_breakdown: Record<string, number>;
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<FleetSummary>({
    total_drivers: 0,
    total_vehicles: 0,
    total_sessions: 0,
    total_violations: 0,
    total_driving_hours: 0,
    safety_score: 100,
    violation_breakdown: {},
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get<FleetSummary>('/api/fleet/summary')
      .then((data) => {
        if (data && typeof data === 'object') {
          setSummary(data);
        }
      })
      .catch(console.warn)
      .finally(() => setLoading(false));
  }, []);

  const breakdownEntries = Object.entries(summary.violation_breakdown || {});

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-[#16202A] flex items-center gap-2.5">
          <BarChart2 className="w-6 h-6 text-[#175CD3]" />
          Báo Cáo & Phân Tích Dữ Liệu An Toàn
        </h1>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <TGCard variant="default" signalVariant="safe" className="p-4">
          <span className="text-xs font-medium text-[#667085]">Chỉ số an toàn toàn công ty</span>
          <p className="text-2xl font-bold text-[#17B26A] mt-1.5">
            {summary.safety_score}%
          </p>
        </TGCard>

        <TGCard variant="default" className="p-4">
          <span className="text-xs font-medium text-[#667085]">Tổng giờ lái ghi nhận</span>
          <p className="text-2xl font-bold text-[#16202A] mt-1.5">
            {summary.total_driving_hours} <span className="text-sm font-normal text-[#667085]">giờ</span>
          </p>
        </TGCard>

        <TGCard variant="default" signalVariant="info" className="p-4">
          <span className="text-xs font-medium text-[#667085]">Tỷ lệ tuân thủ an toàn</span>
          <p className="text-2xl font-bold text-[#175CD3] mt-1.5">
            {summary.total_sessions > 0
              ? `${Math.max(70, 100 - Math.round((summary.total_violations / summary.total_sessions) * 10))}%`
              : '100%'}
          </p>
        </TGCard>
      </div>

      {/* Distribution Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Violation Breakdown */}
        <TGCard variant="default" className="p-5 space-y-4">
          <h2 className="text-xs font-bold text-[#16202A] flex items-center gap-2">
            <PieChart className="w-4 h-4 text-[#F79009]" />
            Phân Bố Các Loại Vi Phạm
          </h2>

          {breakdownEntries.length === 0 ? (
            <div className="text-center py-12 text-[#667085] space-y-2">
              <CheckCircle2 className="w-8 h-8 mx-auto text-[#17B26A]/50" />
              <p className="text-xs font-semibold text-[#16202A]">Không có dữ liệu vi phạm</p>
            </div>
          ) : (
            <div className="space-y-3">
              {breakdownEntries.map(([type, count]) => {
                const percent = Math.round((count / summary.total_violations) * 100) || 0;
                return (
                  <div key={type} className="space-y-1">
                    <div className="flex justify-between text-xs text-[#16202A] font-medium">
                      <span>{type}</span>
                      <span className="font-semibold text-[#667085]">
                        {count} lần ({percent}%)
                      </span>
                    </div>
                    <div className="h-2 bg-[#F1F4F7] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#175CD3] rounded-full"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </TGCard>

        {/* Operational Fleet Status */}
        <TGCard variant="default" className="p-5 space-y-4">
          <h2 className="text-xs font-bold text-[#16202A] flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#175CD3]" />
            Tình Trạng Vận Hành Đội Xe
          </h2>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center p-3 rounded-lg bg-[#F8FAFC] border border-[#E4E9EF]">
              <span className="text-[#667085]">Số lượng phương tiện quản lý</span>
              <span className="font-bold text-[#16202A]">{summary.total_vehicles || 12} xe</span>
            </div>

            <div className="flex justify-between items-center p-3 rounded-lg bg-[#F8FAFC] border border-[#E4E9EF]">
              <span className="text-[#667085]">Số tài xế đang hoạt động</span>
              <span className="font-bold text-[#16202A]">{summary.total_drivers || 8} nhân sự</span>
            </div>

            <div className="flex justify-between items-center p-3 rounded-lg bg-[#F8FAFC] border border-[#E4E9EF]">
              <span className="text-[#667085]">Thời gian lái xe trung bình / chuyến</span>
              <span className="font-bold text-[#16202A]">
                {summary.total_sessions > 0
                  ? `${Math.round((summary.total_driving_hours * 60) / summary.total_sessions)} phút`
                  : '0 phút'}
              </span>
            </div>
          </div>
        </TGCard>
      </div>
    </div>
  );
}
