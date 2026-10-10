'use client';

import React, { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import {
  ShieldCheck,
  Route,
  AlertTriangle,
  Clock,
  Car,
  Calendar,
  User,
  CheckCircle2,
  Video,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import { JourneySession } from '../../services/sessionService';
import { Violation } from '../../services/violationService';
import { useAuthStore } from '../../stores/authStore';
import {
  TGCard,
  TGCardHeader,
  TGCardTitle,
  TGCardContent,
  TGCardFooter,
  TGButton,
  TGStatusBadge,
  TGVehicleBadge,
  TGEmptyState,
} from '../ui';

export function DriverDashboardView() {
  const { user } = useAuthStore();
  const [sessions, setSessions] = useState<JourneySession[]>([]);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDriverData = async () => {
      setLoading(true);
      try {
        const [sessData, violData] = await Promise.all([
          apiClient.get<JourneySession[]>('/api/sessions/?skip=0&limit=10').catch(() => []),
          apiClient.get<Violation[]>('/api/violations/?skip=0&limit=10').catch(() => []),
        ]);
        if (Array.isArray(sessData)) setSessions(sessData);
        if (Array.isArray(violData)) setViolations(violData);
      } catch (err) {
        console.warn('Driver data warning:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDriverData();
  }, []);

  const totalMinutes = useMemo(
    () => sessions.reduce((acc, s) => acc + (s.total_minutes || 0), 0),
    [sessions]
  );
  const mySafetyScore = Math.max(70, 100 - violations.length * 5);

  return (
    <div className="space-y-6 max-w-5xl mx-auto select-none">
      {/* 1. Driver Welcome Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#E4E9EF]">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-bold text-[#16202A] tracking-tight">
              Chào mừng trở lại, {user?.full_name || 'Tài Xế'}
            </h1>
            <TGStatusBadge variant="safe" size="sm">
              Đang trong ca trực
            </TGStatusBadge>
          </div>
          <p className="text-xs sm:text-sm text-[#667085] mt-1">
            Tổng hợp hồ sơ an toàn, nhật ký chuyến đi và vi phạm cá nhân
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <TGVehicleBadge plateNumber="29A-888.88" type="car" status="safe" />
        </div>
      </div>

      {/* 2. Top Personal Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <TGCard variant="default" signalVariant="safe" className="p-4">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-[11px] font-bold uppercase text-[#667085] block">
                Điểm An Toàn Cá Nhân
              </span>
              <div className="text-2xl font-extrabold text-[#16202A] mt-1">
                {mySafetyScore} <span className="text-xs font-normal text-[#667085]">/ 100</span>
              </div>
            </div>
            <div className="w-8 h-8 rounded-[6px] bg-[#ECFDF3] text-[#17B26A] flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <p className="text-[11px] text-[#17B26A] font-semibold mt-2 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            Hạng A • Lái xe chuẩn mực
          </p>
        </TGCard>

        <TGCard variant="default" signalVariant="primary" className="p-4">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-[11px] font-bold uppercase text-[#667085] block">
                Tổng Chuyến Đi Của Tôi
              </span>
              <div className="text-2xl font-extrabold text-[#16202A] mt-1">
                {sessions.length}{' '}
                <span className="text-xs font-normal text-[#667085]">chuyến</span>
              </div>
            </div>
            <div className="w-8 h-8 rounded-[6px] bg-[#EFF4FF] text-[#175CD3] flex items-center justify-center">
              <Route className="w-4 h-4" />
            </div>
          </div>
          <p className="text-[11px] text-[#667085] mt-2">
            Tích lũy: {Math.round((totalMinutes / 60) * 10) / 10} giờ lái
          </p>
        </TGCard>

        <TGCard
          variant="default"
          signalVariant={violations.length === 0 ? 'safe' : 'critical'}
          className="p-4"
        >
          <div className="flex justify-between items-start">
            <div>
              <span className="text-[11px] font-bold uppercase text-[#667085] block">
                Vi Phạm Ghi Nhận
              </span>
              <div
                className={`text-2xl font-extrabold mt-1 ${
                  violations.length > 0 ? 'text-[#F04438]' : 'text-[#16202A]'
                }`}
              >
                {violations.length}{' '}
                <span className="text-xs font-normal text-[#667085]">sự kiện</span>
              </div>
            </div>
            <div
              className={`w-8 h-8 rounded-[6px] flex items-center justify-center ${
                violations.length > 0
                  ? 'bg-[#FEF3F2] text-[#F04438]'
                  : 'bg-[#ECFDF3] text-[#17B26A]'
              }`}
            >
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <p className="text-[11px] text-[#667085] mt-2">
            {violations.length === 0 ? 'Tuyệt đối an toàn' : 'Cần chú ý tốc độ & tập trung'}
          </p>
        </TGCard>
      </div>

      {/* 3. My Recent Trips */}
      <TGCard variant="default">
        <TGCardHeader>
          <TGCardTitle>
            <Route className="w-4 h-4 text-[#175CD3]" />
            Lịch Sử Chuyến Đi Gần Nhất
          </TGCardTitle>
          <Link href="/journeys">
            <TGButton variant="ghost" size="sm" className="text-xs text-[#175CD3]">
              Tất cả chuyến đi →
            </TGButton>
          </Link>
        </TGCardHeader>

        <TGCardContent className="p-0 overflow-x-auto">
          {sessions.length === 0 ? (
            <TGEmptyState
              icon={Route}
              title="Chưa có chuyến đi nào"
              description="Các phiên lái xe của bạn sẽ xuất hiện tại đây khi bắt đầu hành trình."
            />
          ) : (
            <table className="w-full text-xs text-left">
              <thead className="bg-[#F8FAFC] border-b border-[#E4E9EF] text-[11px] font-bold text-[#667085] uppercase">
                <tr>
                  <th className="px-4 py-3">Mã Chuyến</th>
                  <th className="px-4 py-3">Thời Gian Bắt Đầu</th>
                  <th className="px-4 py-3">Thời Lượng Lái</th>
                  <th className="px-4 py-3">Trạng Thái</th>
                  <th className="px-4 py-3 text-right">Xem Lại</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E4E9EF]">
                {sessions.slice(0, 5).map((s) => (
                  <tr key={s.id} className="hover:bg-[#F8FAFC] transition-colors">
                    <td className="px-4 py-3 font-mono font-bold text-[#175CD3]">
                      #{s.id}
                    </td>
                    <td className="px-4 py-3 text-[#667085] font-mono">
                      {s.start_time ? new Date(s.start_time).toLocaleString('vi-VN') : 'Hôm nay'}
                    </td>
                    <td className="px-4 py-3 text-[#16202A] font-semibold">
                      {s.total_minutes ? `${s.total_minutes} phút` : '< 1 phút'}
                    </td>
                    <td className="px-4 py-3">
                      <TGStatusBadge variant="safe" size="sm">
                        Hoàn thành
                      </TGStatusBadge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link href="/journeys">
                        <TGButton variant="outline" size="sm" className="h-7 text-[11px] px-2.5">
                          Xem lại lộ trình
                        </TGButton>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </TGCardContent>
      </TGCard>
    </div>
  );
}
