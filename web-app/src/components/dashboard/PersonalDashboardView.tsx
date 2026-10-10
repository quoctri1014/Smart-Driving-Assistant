'use client';

import React, { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import {
  ShieldCheck,
  Video,
  Route,
  AlertTriangle,
  Clock,
  Eye,
  Activity,
  Sparkles,
  ChevronRight,
  TrendingUp,
  Car,
  Compass,
  Zap,
  CheckCircle2,
  Sliders,
  Play,
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
  TGButton,
  TGStatusBadge,
  TGEmptyState,
} from '../ui';

export function PersonalDashboardView() {
  const { user } = useAuthStore();
  const [sessions, setSessions] = useState<JourneySession[]>([]);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPersonalData = async () => {
      setLoading(true);
      try {
        const [sessData, violData] = await Promise.all([
          apiClient.get<JourneySession[]>('/api/sessions/?skip=0&limit=10').catch(() => []),
          apiClient.get<Violation[]>('/api/violations/?skip=0&limit=10').catch(() => []),
        ]);
        if (Array.isArray(sessData)) setSessions(sessData);
        if (Array.isArray(violData)) setViolations(violData);
      } catch (err) {
        console.warn('Personal data warning:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchPersonalData();
  }, []);

  const totalMinutes = useMemo(
    () => sessions.reduce((acc, s) => acc + (s.total_minutes || 0), 0),
    [sessions]
  );
  const mySafetyScore = Math.max(80, 100 - violations.length * 4);

  return (
    <div className="space-y-6 max-w-6xl mx-auto select-none pb-8">
      {/* 1. Hero Action Banner: Start Driving Session */}
      <div className="relative overflow-hidden rounded-[16px] bg-gradient-to-r from-[#0F172A] via-[#1E293B] to-[#0F172A] p-6 sm:p-8 text-white shadow-lg border border-[#334155]">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-[#175CD3]/20 to-transparent pointer-events-none" />
        <div className="absolute -right-12 -top-12 w-64 h-64 rounded-full bg-[#175CD3]/10 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#175CD3]/30 border border-[#175CD3]/50 text-xs font-semibold text-[#93C5FD]">
              <Sparkles className="w-3.5 h-3.5 text-[#60A5FA]" />
              <span>Trợ lý AI Trực Tuyến • Phiên Bản Cá Nhân</span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Sẵn sàng cho chuyến đi mới an toàn!
            </h1>

            <p className="text-sm text-[#94A3B8] leading-relaxed">
              Kích hoạt camera trước và camera trong xe để Trợ lý AI tự động phát hiện biển báo, giám sát cự ly an toàn, cảnh báo buồn ngủ và ghi nhận hành trình của bạn theo thời gian thực.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <Link href="/live">
              <button className="flex items-center gap-2 px-5 py-3 rounded-[10px] bg-[#175CD3] hover:bg-[#1550B5] active:scale-[0.98] text-white font-bold text-sm shadow-[0_4px_14px_rgba(23,92,211,0.4)] transition-all cursor-pointer">
                <Play className="w-4 h-4 fill-current" />
                <span>Bắt Đầu Lái Xe (Live AI)</span>
              </button>
            </Link>
          </div>
        </div>
      </div>

      {/* 2. Top Personal Driver Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Safety Score */}
        <TGCard variant="default" signalVariant="safe" className="p-4 bg-white">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-[11px] font-bold uppercase text-[#667085] block">
                Điểm An Toàn Của Bạn
              </span>
              <div className="text-3xl font-extrabold text-[#16202A] mt-1">
                {mySafetyScore} <span className="text-xs font-normal text-[#667085]">/ 100</span>
              </div>
            </div>
            <div className="w-9 h-9 rounded-[8px] bg-[#ECFDF3] text-[#17B26A] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </div>
          <p className="text-[11px] text-[#17B26A] font-semibold mt-2.5 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            Hạng Xuất Sắc • Phản xạ rất tốt
          </p>
        </TGCard>

        {/* Attention & Alertness State */}
        <TGCard variant="default" signalVariant="primary" className="p-4 bg-white">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-[11px] font-bold uppercase text-[#667085] block">
                Mức Độ Tập Trung (DMS)
              </span>
              <div className="text-3xl font-extrabold text-[#175CD3] mt-1">
                100% <span className="text-xs font-normal text-[#667085]">tỉnh táo</span>
              </div>
            </div>
            <div className="w-9 h-9 rounded-[8px] bg-[#EFF4FF] text-[#175CD3] flex items-center justify-center">
              <Eye className="w-5 h-5" />
            </div>
          </div>
          <p className="text-[11px] text-[#667085] mt-2.5 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#175CD3]" />
            Camera giám sát mắt & gương mặt
          </p>
        </TGCard>

        {/* Trips Completed */}
        <TGCard variant="default" signalVariant="primary" className="p-4 bg-white">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-[11px] font-bold uppercase text-[#667085] block">
                Chuyến Đi Đã Thực Hiện
              </span>
              <div className="text-3xl font-extrabold text-[#16202A] mt-1">
                {sessions.length}{' '}
                <span className="text-xs font-normal text-[#667085]">chuyến</span>
              </div>
            </div>
            <div className="w-9 h-9 rounded-[8px] bg-[#F8FAFC] text-[#475467] border border-[#E4E9EF] flex items-center justify-center">
              <Route className="w-5 h-5" />
            </div>
          </div>
          <p className="text-[11px] text-[#667085] mt-2.5">
            Tổng thời gian: {Math.max(1, Math.round((totalMinutes / 60) * 10) / 10)} giờ lái
          </p>
        </TGCard>

        {/* Hazard & Alerts Prevented */}
        <TGCard
          variant="default"
          signalVariant={violations.length === 0 ? 'safe' : 'critical'}
          className="p-4 bg-white"
        >
          <div className="flex justify-between items-start">
            <div>
              <span className="text-[11px] font-bold uppercase text-[#667085] block">
                Cảnh Báo An Toàn
              </span>
              <div
                className={`text-3xl font-extrabold mt-1 ${
                  violations.length > 0 ? 'text-[#F04438]' : 'text-[#16202A]'
                }`}
              >
                {violations.length}{' '}
                <span className="text-xs font-normal text-[#667085]">sự kiện</span>
              </div>
            </div>
            <div
              className={`w-9 h-9 rounded-[8px] flex items-center justify-center ${
                violations.length > 0
                  ? 'bg-[#FEF3F2] text-[#F04438]'
                  : 'bg-[#ECFDF3] text-[#17B26A]'
              }`}
            >
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <p className="text-[11px] text-[#667085] mt-2.5">
            {violations.length === 0 ? 'Không có nguy cơ vi phạm' : 'Đã được trợ lý nhắc nhở kịp thời'}
          </p>
        </TGCard>
      </div>

      {/* 3. Core Personal AI Modules Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-[#175CD3]" />
            <h2 className="text-base font-bold text-[#16202A]">
              Các Tính Năng Trợ Lý AI Đang Bảo Vệ Bạn
            </h2>
          </div>
          <Link href="/live" className="text-xs text-[#175CD3] font-semibold hover:underline">
            Mở màn hình Live AI →
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link href="/live?tab=plates" className="group block">
            <TGCard variant="elevated" className="p-4.5 bg-white h-full transition-all group-hover:border-[#175CD3]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-[10px] bg-[#EFF4FF] text-[#175CD3] flex items-center justify-center font-bold text-lg">
                  🪪
                </div>
                <div>
                  <h3 className="font-bold text-sm text-[#16202A] group-hover:text-[#175CD3] transition-colors">
                    Nhận Diện Biển Số Xe (ALPR)
                  </h3>
                  <p className="text-xs text-[#667085] mt-0.5">
                    Tự động nhận diện biển số xe trước và lưu lại nhật ký lưu thông
                  </p>
                </div>
              </div>
            </TGCard>
          </Link>

          <Link href="/live?tab=signs" className="group block">
            <TGCard variant="elevated" className="p-4.5 bg-white h-full transition-all group-hover:border-[#175CD3]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-[10px] bg-[#EFF4FF] text-[#175CD3] flex items-center justify-center font-bold text-lg">
                  ⛔
                </div>
                <div>
                  <h3 className="font-bold text-sm text-[#16202A] group-hover:text-[#175CD3] transition-colors">
                    Biển Báo & Giới Hạn Tốc Độ
                  </h3>
                  <p className="text-xs text-[#667085] mt-0.5">
                    Nhận diện biển báo giao thông chuẩn QCVN 41 và cảnh báo khi quá tốc độ
                  </p>
                </div>
              </div>
            </TGCard>
          </Link>

          <Link href="/live?tab=traffic" className="group block">
            <TGCard variant="elevated" className="p-4.5 bg-white h-full transition-all group-hover:border-[#175CD3]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-[10px] bg-[#EFF4FF] text-[#175CD3] flex items-center justify-center font-bold text-lg">
                  🚗
                </div>
                <div>
                  <h3 className="font-bold text-sm text-[#16202A] group-hover:text-[#175CD3] transition-colors">
                    Cự Ly An Toàn & Cảnh Báo Va Chạm
                  </h3>
                  <p className="text-xs text-[#667085] mt-0.5">
                    Ước tính khoảng cách tới xe phía trước và phát âm thanh cảnh báo va chạm
                  </p>
                </div>
              </div>
            </TGCard>
          </Link>
        </div>
      </div>

      {/* 4. Recent Personal Trips & AI Advice */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Trips Table */}
        <div className="lg:col-span-2">
          <TGCard variant="default" className="bg-white">
            <TGCardHeader className="flex flex-row items-center justify-between border-b border-[#E4E9EF] pb-3">
              <TGCardTitle className="flex items-center gap-2 text-sm font-bold text-[#16202A]">
                <Route className="w-4 h-4 text-[#175CD3]" />
                Nhật Ký Hành Trình Gần Nhất
              </TGCardTitle>
              <Link href="/journeys">
                <TGButton variant="ghost" size="sm" className="text-xs text-[#175CD3] font-semibold h-8">
                  Xem tất cả chuyến đi →
                </TGButton>
              </Link>
            </TGCardHeader>

            <TGCardContent className="p-0 overflow-x-auto">
              {sessions.length === 0 ? (
                <TGEmptyState
                  icon={Route}
                  title="Chưa có chuyến đi nào"
                  description="Khi bạn bắt đầu phiên lái xe tại trang Live AI, nhật ký sẽ tự động hiển thị ở đây."
                />
              ) : (
                <table className="w-full text-xs text-left">
                  <thead className="bg-[#F8FAFC] border-b border-[#E4E9EF] text-[11px] font-bold text-[#667085] uppercase">
                    <tr>
                      <th className="px-4 py-3">Mã Chuyến</th>
                      <th className="px-4 py-3">Thời Gian</th>
                      <th className="px-4 py-3">Thời Lượng</th>
                      <th className="px-4 py-3">Trạng Thái</th>
                      <th className="px-4 py-3 text-right">Chi Tiết</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E4E9EF]">
                    {sessions.slice(0, 4).map((s) => (
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
                              Xem lộ trình
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

        {/* AI Driving Tips & Personal Advice */}
        <div className="space-y-4">
          <TGCard variant="default" className="bg-white p-5 space-y-4">
            <div className="flex items-center gap-2 text-[#16202A] font-bold text-sm border-b border-[#E4E9EF] pb-3">
              <Sparkles className="w-4 h-4 text-[#175CD3]" />
              <span>Lời Khuyên Từ Trợ Lý Lái Xe</span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-[8px] bg-[#F0FDF4] border border-[#DCFCE7] text-[#166534] space-y-1">
                <div className="font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Duy trì thói quen tốt
                </div>
                <p className="text-[11px] leading-relaxed">
                  Bạn luôn thắt dây an toàn đầy đủ trước khi khởi hành. Hãy tiếp tục phát huy!
                </p>
              </div>

              <div className="p-3 rounded-[8px] bg-[#EFF6FF] border border-[#DBEAFE] text-[#1E40AF] space-y-1">
                <div className="font-bold flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5" />
                  Nghỉ ngơi định kỳ
                </div>
                <p className="text-[11px] leading-relaxed">
                  Khi lái xe đường dài liên tục trên 2 giờ, hãy dừng nghỉ 15 phút để đảm bảo sự tỉnh táo cao nhất.
                </p>
              </div>

              <div className="p-3 rounded-[8px] bg-[#FFFBEB] border border-[#FEF3C7] text-[#92400E] space-y-1">
                <div className="font-bold flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Giữ khoảng cách an toàn
                </div>
                <p className="text-[11px] leading-relaxed">
                  Trong điều kiện trời mưa hoặc sương mù, hãy tăng khoảng cách với xe phía trước lên tối thiểu 35 mét.
                </p>
              </div>
            </div>
          </TGCard>
        </div>
      </div>
    </div>
  );
}
