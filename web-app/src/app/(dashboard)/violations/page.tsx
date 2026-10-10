'use client';

import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  ShieldCheck,
  RotateCcw,
  Sparkles,
  MapPin,
  Car,
  ChevronRight,
  Layers,
  XCircle,
  HelpCircle
} from 'lucide-react';
import { violationService, Violation } from '../../../services/violationService';
import { useAuthStore } from '../../../stores/authStore';
import { hasPermission } from '../../../lib/permissions';
import { TGCard, TGCardHeader, TGCardTitle, TGCardContent } from '../../../components/ui/TGCard';
import { TGStatusBadge } from '../../../components/ui/TGStatusBadge';
import { TGVehicleBadge } from '../../../components/ui/TGVehicleBadge';
import { TGButton } from '../../../components/ui/TGButton';
import { IncidentReviewDrawer } from '../../../components/violations/IncidentReviewDrawer';

export const formatViolationType = (type: string): string => {
  const map: Record<string, string> = {
    drowsy: 'Ngủ gật / Buồn ngủ (DMS)',
    fatigue: 'Mệt mỏi / Buồn ngủ',
    no_seatbelt: 'Không thắt dây an toàn',
    seatbelt: 'Không thắt dây an toàn',
    collision: 'Nguy cơ va chạm (FCW)',
    collision_danger: 'Nguy cơ va chạm (FCW)',
    speed_limit: 'Vượt quá tốc độ giới hạn',
    speeding: 'Vượt quá tốc độ giới hạn',
    helmet_violation: 'Không đội mũ bảo hiểm',
    no_helmet: 'Không đội mũ bảo hiểm',
    phone_distraction: 'Dùng điện thoại khi lái',
    distracted: 'Mất tập trung khi lái',
  };
  return map[type.toLowerCase()] || type;
};

export const formatResolutionStatus = (status?: string): string => {
  if (!status) return 'Đang mở';
  const map: Record<string, string> = {
    OPEN: 'Đang mở',
    IN_PROGRESS: 'Đang xử lý',
    RESOLVED: 'Đã xử lý',
    CLOSED: 'Đã đóng',
  };
  return map[status.toUpperCase()] || status;
};

export const formatDateTime = (isoString?: string): string => {
  if (!isoString) return 'Chưa có dữ liệu';
  try {
    const d = new Date(isoString);
    return d.toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return isoString;
  }
};

export default function ViolationsPage() {
  const { user } = useAuthStore();
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [selectedViolation, setSelectedViolation] = useState<Violation | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const userCanReview = hasPermission('violation.review', user?.role, user?.permissions);

  const fetchViolations = async () => {
    setLoading(true);
    try {
      const data = await violationService.getViolations({
        review_status: statusFilter === 'ALL' ? undefined : statusFilter,
        severity: severityFilter === 'ALL' ? undefined : severityFilter,
        violation_type: typeFilter === 'ALL' ? undefined : typeFilter,
        search: searchTerm.trim() || undefined,
        limit: 100
      });
      if (Array.isArray(data)) {
        setViolations(data);
      }
    } catch (e) {
      console.warn('Violations fetch error', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchViolations();
  }, [statusFilter, severityFilter, typeFilter]);

  const handleRowClick = async (v: Violation) => {
    try {
      const detail = await violationService.getViolationDetail(v.id);
      setSelectedViolation(detail);
      setIsDrawerOpen(true);
    } catch (e) {
      setSelectedViolation(v);
      setIsDrawerOpen(true);
    }
  };

  const handleReviewSubmit = async (violationId: number, action: string, note: string, expectedVersion: number) => {
    await violationService.reviewViolation(violationId, action, note, expectedVersion);
    await fetchViolations();
    return true;
  };

  // Metrics
  const pendingCount = violations.filter((v) => v.review_status === 'PENDING_REVIEW').length;
  const confirmedCount = violations.filter((v) => v.review_status === 'CONFIRMED').length;
  const fpCount = violations.filter((v) => v.review_status === 'FALSE_POSITIVE').length;
  const resolvedCount = violations.filter((v) => v.resolution_status === 'RESOLVED').length;

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#16202A] flex items-center gap-2.5">
            <ShieldCheck className="w-6 h-6 text-[#175CD3]" />
            Lịch Sử Cảnh Báo & An Toàn
          </h1>
          <p className="text-xs text-[#667085] mt-0.5">
            Nhật ký ghi nhận các cảnh báo an toàn cá nhân: buồn ngủ, quá tốc độ, không thắt dây an toàn
          </p>
        </div>

        <div className="flex items-center gap-2">
          <TGButton variant="outline" size="sm" onClick={fetchViolations} isLoading={loading}>
            <RotateCcw className="w-4 h-4 mr-1.5" />
            Làm mới
          </TGButton>
        </div>
      </div>

      {/* Top Status Tabs / KPI Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <button
          onClick={() => setStatusFilter('ALL')}
          className={`p-3.5 rounded-lg border text-left transition-all ${
            statusFilter === 'ALL'
              ? 'bg-white border-[#175CD3] ring-1 ring-[#175CD3]'
              : 'bg-white border-[#E4E9EF] hover:border-[#98A2B3]'
          }`}
        >
          <span className="text-sm font-medium text-[#475467]">Tất cả hồ sơ</span>
          <p className="text-2xl font-bold text-[#16202A] mt-1">{violations.length}</p>
        </button>

        <button
          onClick={() => setStatusFilter('PENDING_REVIEW')}
          className={`p-3.5 rounded-lg border text-left transition-all ${
            statusFilter === 'PENDING_REVIEW'
              ? 'bg-white border-[#F79009] ring-1 ring-[#F79009]'
              : 'bg-white border-[#E4E9EF] hover:border-[#98A2B3]'
          }`}
        >
          <span className="text-sm text-[#F79009] font-medium flex items-center gap-1.5">
            <Clock className="w-4 h-4" />
            Cần thẩm định
          </span>
          <p className="text-2xl font-bold text-[#16202A] mt-1">{pendingCount}</p>
        </button>

        <button
          onClick={() => setStatusFilter('CONFIRMED')}
          className={`p-3.5 rounded-lg border text-left transition-all ${
            statusFilter === 'CONFIRMED'
              ? 'bg-white border-[#F04438] ring-1 ring-[#F04438]'
              : 'bg-white border-[#E4E9EF] hover:border-[#98A2B3]'
          }`}
        >
          <span className="text-sm text-[#F04438] font-medium flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4" />
            Đã xác nhận
          </span>
          <p className="text-2xl font-bold text-[#16202A] mt-1">{confirmedCount}</p>
        </button>

        <button
          onClick={() => setStatusFilter('FALSE_POSITIVE')}
          className={`p-3.5 rounded-lg border text-left transition-all ${
            statusFilter === 'FALSE_POSITIVE'
              ? 'bg-white border-[#98A2B3] ring-1 ring-[#98A2B3]'
              : 'bg-white border-[#E4E9EF] hover:border-[#98A2B3]'
          }`}
        >
          <span className="text-sm text-[#475467] font-medium flex items-center gap-1.5">
            <XCircle className="w-4 h-4" />
            Báo sai AI
          </span>
          <p className="text-2xl font-bold text-[#16202A] mt-1">{fpCount}</p>
        </button>

        <button
          onClick={() => setStatusFilter('RESOLVED')}
          className={`p-3.5 rounded-lg border text-left transition-all ${
            statusFilter === 'RESOLVED'
              ? 'bg-white border-[#17B26A] ring-1 ring-[#17B26A]'
              : 'bg-white border-[#E4E9EF] hover:border-[#98A2B3]'
          }`}
        >
          <span className="text-sm text-[#17B26A] font-medium flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4" />
            Đã xử lý
          </span>
          <p className="text-2xl font-bold text-[#16202A] mt-1">{resolvedCount}</p>
        </button>
      </div>

      {/* Filter Toolbar */}
      <TGCard variant="default" className="p-3.5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="relative w-72">
              <Search className="w-4 h-4 text-[#98A2B3] absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Tìm loại lỗi, địa điểm..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchViolations()}
                className="w-full bg-[#F8FAFC] border border-[#E4E9EF] rounded-lg pl-9 pr-3 py-2 text-sm text-[#16202A] focus:outline-none focus:border-[#175CD3]"
              />
            </div>

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-[#F8FAFC] border border-[#E4E9EF] rounded-lg px-3 py-2 text-sm text-[#16202A] focus:outline-none focus:border-[#175CD3]"
            >
              <option value="ALL">Tất cả mức độ</option>
              <option value="CRITICAL">Khẩn cấp</option>
              <option value="WARNING">Cảnh báo</option>
              <option value="INFO">Nhắc nhở</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-[#F8FAFC] border border-[#E4E9EF] rounded-lg px-3 py-2 text-sm text-[#16202A] focus:outline-none focus:border-[#175CD3]"
            >
              <option value="ALL">Tất cả hành vi</option>
              <option value="drowsy">Ngủ gật / Buồn ngủ</option>
              <option value="speed_limit">Quá tốc độ</option>
              <option value="collision_danger">Nguy cơ va chạm</option>
              <option value="no_seatbelt">Không thắt dây an toàn</option>
              <option value="helmet_violation">Không đội mũ bảo hiểm</option>
            </select>
          </div>

          <span className="text-sm text-[#667085]">
            Hiển thị: <strong className="text-[#16202A]">{violations.length}</strong> sự cố
          </span>
        </div>
      </TGCard>

      {/* Main Table */}
      <TGCard variant="default" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#F8FAFC] border-b border-[#E4E9EF] text-xs font-semibold text-[#475467] uppercase">
              <tr>
                <th className="p-3.5">Mã sự cố</th>
                <th className="p-3.5">Hành vi phát hiện</th>
                <th className="p-3.5">Mức độ</th>
                <th className="p-3.5">Phương tiện / Tài xế</th>
                <th className="p-3.5">Thời điểm & Tốc độ</th>
                <th className="p-3.5">Độ tin cậy</th>
                <th className="p-3.5">Thẩm định</th>
                <th className="p-3.5">Xử lý</th>
                <th className="p-3.5 text-right">Chi tiết</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E4E9EF] text-[#16202A]">
              {loading ? (
                <tr>
                  <td colSpan={9} className="p-8 text-center text-[#667085]">
                    Đang tải dữ liệu sự cố từ hệ thống...
                  </td>
                </tr>
              ) : violations.length === 0 ? (
                <tr>
                  <td colSpan={9} className="p-12 text-center text-[#667085] space-y-2">
                    <CheckCircle2 className="w-8 h-8 mx-auto text-[#17B26A]/50" />
                    <p className="text-sm font-semibold text-[#16202A]">Không có sự cố vi phạm nào</p>
                  </td>
                </tr>
              ) : (
                violations.map((v) => {
                  const confDisplay = v.confidence !== null && v.confidence !== undefined
                    ? `${(v.confidence * 100).toFixed(0)}%`
                    : null;
                  const sevVariant = v.severity === 'CRITICAL' ? 'critical' : v.severity === 'WARNING' ? 'warning' : 'info';

                  return (
                    <tr
                      key={v.id}
                      onClick={() => handleRowClick(v)}
                      className="hover:bg-[#F8FAFC] cursor-pointer transition-colors"
                    >
                      <td className="p-3.5 text-[#175CD3] font-semibold">
                        #VIOL-{v.id}
                      </td>
                      <td className="p-3.5">
                        <span className="font-semibold text-[#16202A] block">{formatViolationType(v.violation_type)}</span>
                        {v.location_name && (
                          <span className="text-[11px] text-[#667085] truncate max-w-[200px] block mt-0.5">
                            📍 {v.location_name}
                          </span>
                        )}
                      </td>
                      <td className="p-3.5">
                        <TGStatusBadge variant={sevVariant} size="sm">
                          {v.severity === 'CRITICAL' ? 'Khẩn cấp' : v.severity === 'WARNING' ? 'Cảnh báo' : 'Nhắc nhở'}
                        </TGStatusBadge>
                      </td>
                      <td className="p-3.5">
                        <div className="flex items-center gap-2">
                          <TGVehicleBadge plateNumber={v.vehicle_plate || (v.vehicle_id ? `Xe #${v.vehicle_id}` : '29A-888.88')} />
                          <span className="text-xs text-[#667085]">{v.driver_name || `Tài xế #${v.driver_id || 1}`}</span>
                        </div>
                      </td>
                      <td className="p-3.5 text-xs text-[#475467]">
                        <span className="block font-medium">{formatDateTime(v.detected_at)}</span>
                        {v.speed_kph ? (
                          <span className="text-[#175CD3] font-semibold">
                            ⚡ {v.speed_kph} km/h {v.speed_limit_kph ? `(GH ${v.speed_limit_kph})` : ''}
                          </span>
                        ) : null}
                      </td>
                      <td className="p-3.5 text-xs font-semibold">
                        {confDisplay ? (
                          <span className="text-[#175CD3] bg-[#EFF8FF] px-2 py-0.5 rounded border border-[#B2DDFF]">
                            {confDisplay}
                          </span>
                        ) : (
                          <span className="text-[#98A2B3]">Chưa có dữ liệu</span>
                        )}
                      </td>
                      <td className="p-3.5">
                        <TGStatusBadge
                          variant={v.review_status === 'CONFIRMED' ? 'safe' : v.review_status === 'FALSE_POSITIVE' ? 'neutral' : 'warning'}
                          size="sm"
                        >
                          {v.review_status === 'PENDING_REVIEW' ? 'Chờ duyệt' : v.review_status === 'CONFIRMED' ? 'Đã xác nhận' : 'Báo sai'}
                        </TGStatusBadge>
                      </td>
                      <td className="p-3.5">
                        <TGStatusBadge
                          variant={v.resolution_status === 'RESOLVED' ? 'safe' : 'info'}
                          size="sm"
                        >
                          {formatResolutionStatus(v.resolution_status)}
                        </TGStatusBadge>
                      </td>
                      <td className="p-3.5 text-right">
                        <span className="text-sm text-[#175CD3] font-semibold flex items-center justify-end gap-1 hover:underline">
                          Thẩm định
                          <ChevronRight className="w-4 h-4" />
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </TGCard>

      {/* Incident Review Inspector Drawer */}
      <IncidentReviewDrawer
        violation={selectedViolation}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        onReviewSubmit={handleReviewSubmit}
        canReview={userCanReview}
      />
    </div>
  );
}
