'use client';

import React, { useEffect, useState } from 'react';
import {
  Route,
  Clock,
  User,
  Calendar,
  CheckCircle2,
  Play,
  RotateCcw,
  Search,
} from 'lucide-react';
import { sessionService, JourneySession } from '../../../services/sessionService';
import { TGCard, TGCardHeader, TGCardTitle, TGCardContent } from '../../../components/ui/TGCard';
import { TGStatusBadge } from '../../../components/ui/TGStatusBadge';
import { TGButton } from '../../../components/ui/TGButton';

export default function JourneysPage() {
  const [sessions, setSessions] = useState<JourneySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const data = await sessionService.getSessions(0, 100);
      if (Array.isArray(data)) {
        setSessions(data);
      }
    } catch (e) {
      console.warn('Sessions fetch error', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const totalMins = sessions.reduce((acc, s) => acc + (s.total_minutes || 0), 0);
  const completedCount = sessions.filter((s) => s.end_time).length;

  const filteredSessions = sessions.filter(
    (s) =>
      String(s.id).includes(search) ||
      (s.driver_id && String(s.driver_id).includes(search))
  );

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-[#16202A] flex items-center gap-2.5">
            <Route className="w-6 h-6 text-[#175CD3]" />
            Lịch Sử Hành Trình Của Bạn
          </h1>
          <p className="text-xs text-[#667085] mt-0.5">
            Ghi nhận chi tiết thời gian bắt đầu, thời lượng và thông tin các phiên lái xe cá nhân
          </p>
        </div>

        <TGButton variant="outline" size="sm" onClick={fetchSessions} isLoading={loading}>
          <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
          Làm mới
        </TGButton>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <TGCard variant="default" className="p-4">
          <span className="text-xs font-medium text-[#667085]">Tổng số chuyến đi</span>
          <p className="text-xl font-bold text-[#16202A] mt-1.5">{sessions.length}</p>
        </TGCard>
        <TGCard variant="default" className="p-4">
          <span className="text-xs font-medium text-[#667085]">Tổng thời gian vận hành</span>
          <p className="text-xl font-bold text-[#16202A] mt-1.5">
            {Math.round((totalMins / 60) * 10) / 10} <span className="text-xs font-normal text-[#667085]">giờ</span>
          </p>
        </TGCard>
        <TGCard variant="default" signalVariant="safe" className="p-4">
          <span className="text-xs font-medium text-[#667085]">Chuyến đã hoàn thành</span>
          <p className="text-xl font-bold text-[#16202A] mt-1.5">{completedCount}</p>
        </TGCard>
      </div>

      {/* Main Table */}
      <TGCard variant="default" className="overflow-hidden">
        <div className="p-3 bg-[#F8FAFC] border-b border-[#E4E9EF] flex justify-between items-center">
          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 text-[#98A2B3] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Tìm mã phiên, tài xế ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#FFFFFF] border border-[#E4E9EF] rounded-lg pl-9 pr-3 py-1.5 text-xs text-[#16202A] focus:outline-none focus:border-[#175CD3]"
            />
          </div>
          <span className="text-xs text-[#667085]">
            Hiển thị: <strong>{filteredSessions.length}</strong> chuyến
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F8FAFC] border-b border-[#E4E9EF] text-[#667085] font-semibold">
              <tr>
                <th className="p-3.5">Mã chuyến</th>
                <th className="p-3.5">Tài xế</th>
                <th className="p-3.5">Thời điểm bắt đầu</th>
                <th className="p-3.5">Thời lượng</th>
                <th className="p-3.5">Trạng thái</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E4E9EF] text-[#16202A]">
              {loading ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-[#667085]">
                    Đang nạp dữ liệu hành trình...
                  </td>
                </tr>
              ) : filteredSessions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-12 text-center text-[#667085] space-y-2">
                    <CheckCircle2 className="w-8 h-8 mx-auto text-[#175CD3]/50" />
                    <p className="text-xs font-semibold text-[#16202A]">Chưa có phiên hành trình nào</p>
                  </td>
                </tr>
              ) : (
                filteredSessions.map((s) => (
                  <tr key={s.id} className="hover:bg-[#F8FAFC] transition-colors">
                    <td className="p-3.5 font-semibold text-[#175CD3]">#{s.id}</td>
                    <td className="p-3.5 font-medium text-[#16202A]">
                      Tài xế ID: #{s.driver_id || 1}
                    </td>
                    <td className="p-3.5 text-xs text-[#16202A]">
                      {new Date(s.start_time).toLocaleString('vi-VN')}
                    </td>
                    <td className="p-3.5 text-xs text-[#667085]">
                      {s.total_minutes ? `${Math.round(s.total_minutes)} phút` : 'Đang tiếp diễn'}
                    </td>
                    <td className="p-3.5">
                      <TGStatusBadge
                        variant={s.end_time ? 'safe' : 'warning'}
                        size="sm"
                      >
                        {s.end_time ? 'Đã hoàn thành' : 'Đang diễn ra'}
                      </TGStatusBadge>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </TGCard>
    </div>
  );
}
