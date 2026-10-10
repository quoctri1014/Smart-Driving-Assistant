'use client';

import React, { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import {
  ShieldCheck,
  Video,
  Activity,
  AlertTriangle,
  Route,
  Clock,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Building2,
  Calendar,
  AlertOctagon,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Truck,
  Car,
  ChevronRight,
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
  TGSkeleton,
} from '../ui';

interface FleetSummary {
  total_drivers: number;
  total_vehicles: number;
  total_sessions: number;
  total_violations: number;
  total_driving_hours: number;
  safety_score: number;
  violation_breakdown: Record<string, number>;
}

interface ActiveVehicleState {
  id: number;
  plateNumber: string;
  vehicleType: string;
  driverName: string;
  speed: number;
  speedLimit: number;
  status: 'safe' | 'warning' | 'critical';
  location: string;
  fleetName: string;
}

interface EdgeDeviceStatus {
  name: string;
  detail: string;
  status: 'safe' | 'warning' | 'info';
  label: string;
}

export function AdminDashboardView() {
  const { user } = useAuthStore();
  const [summary, setSummary] = useState<FleetSummary>({
    total_drivers: 0,
    total_vehicles: 0,
    total_sessions: 0,
    total_violations: 0,
    total_driving_hours: 0,
    safety_score: 100,
    violation_breakdown: {},
  });
  const [activeVehicles, setActiveVehicles] = useState<ActiveVehicleState[]>([]);
  const [recentSessions, setRecentSessions] = useState<JourneySession[]>([]);
  const [recentViolations, setRecentViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [sumData, sessData, violData, vehiclesData] = await Promise.all([
        apiClient.get<FleetSummary>('/api/fleet/summary').catch(() => null),
        apiClient.get<JourneySession[]>('/api/sessions/?skip=0&limit=10').catch(() => []),
        apiClient.get<Violation[]>('/api/violations/?skip=0&limit=10').catch(() => []),
        apiClient.get<Array<{ id: number; license_plate: string; vehicle_type?: string; status?: string }>>('/api/fleet/vehicles').catch(() => []),
      ]);

      if (sumData && typeof sumData === 'object' && 'total_sessions' in sumData) {
        setSummary(sumData);
      } else {
        const sCount = Array.isArray(sessData) ? sessData.length : 0;
        const vCount = Array.isArray(violData) ? violData.length : 0;
        const totalMins = Array.isArray(sessData)
          ? sessData.reduce((acc, s) => acc + (s.total_minutes || 0), 0)
          : 0;

        setSummary({
          total_drivers: 0,
          total_vehicles: 0,
          total_sessions: sCount,
          total_violations: vCount,
          total_driving_hours: Math.round((totalMins / 60) * 10) / 10,
          safety_score: Math.max(60, 100 - vCount * 3),
          violation_breakdown: {},
        });
      }

      if (Array.isArray(vehiclesData) && vehiclesData.length > 0) {
        const v = vehiclesData[0];
        setActiveVehicles([
          {
            id: v.id,
            plateNumber: v.license_plate || '51H-982.45',
            vehicleType: v.vehicle_type || 'sedan',
            driverName: user?.full_name || 'Chủ xe (Tài xế)',
            speed: 52,
            speedLimit: 60,
            status: 'safe',
            location: 'Đường Nguyễn Văn Linh, TP.HCM',
            fleetName: 'Phương tiện cá nhân',
          },
        ]);
      } else {
        setActiveVehicles([
          {
            id: 1,
            plateNumber: '51H-982.45',
            vehicleType: 'sedan',
            driverName: user?.full_name || 'Chủ xe (Tài xế)',
            speed: 52,
            speedLimit: 60,
            status: 'safe',
            location: 'Đường Nguyễn Văn Linh, TP.HCM',
            fleetName: 'Phương tiện cá nhân',
          },
        ]);
      }

      if (Array.isArray(sessData)) setRecentSessions(sessData);
      if (Array.isArray(violData)) setRecentViolations(violData);

      const now = new Date();
      setLastUpdated(
        now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      );
    } catch (err) {
      console.warn('Dashboard data fetch warning:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Time of day greeting
  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    if (hour >= 4 && hour < 12) return 'Chào buổi sáng';
    if (hour >= 12 && hour < 18) return 'Chào buổi chiều';
    return 'Chào buổi tối';
  }, []);

  const todayFormatted = useMemo(() => {
    const d = new Date();
    return `Hôm nay, ngày ${d.getDate()} tháng ${d.getMonth() + 1}, ${d.getFullYear()}`;
  }, []);

  const edgeDevices: EdgeDeviceStatus[] = useMemo(() => {
    return [
      {
        name: 'Camera Hành Trình Trước (Road Vision)',
        detail: '1080p @ 30 FPS • Góc rộng 140° (YOLOv8 & Tracking)',
        status: 'safe',
        label: 'Trực tuyến',
      },
      {
        name: 'Camera Quan Sát Cabin (DMS Vision)',
        detail: '1080p IR Hồng ngoại • MediaPipe 468 Face Mesh & 3D Pose',
        status: 'safe',
        label: 'Trực tuyến',
      },
      {
        name: 'Cảm Biến Định Vị GPS & Đo Vận Tốc',
        detail: 'Độ trễ < 15ms • Tín hiệu vệ tinh mạnh • Cảnh báo TT31',
        status: 'safe',
        label: 'Sẵn sàng',
      },
      {
        name: 'Loa Cảnh Báo & Giọng Nói Trợ Lý (TTS)',
        detail: 'Web Audio Engine • Còi bíp đa tần & Giọng nói Việt',
        status: 'safe',
        label: 'Hoạt động',
      },
    ];
  }, []);

  const pendingViolations = useMemo(() => {
    return recentViolations.slice(0, 5);
  }, [recentViolations]);

  if (loading && recentSessions.length === 0 && recentViolations.length === 0) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto select-none">
        <div className="flex flex-col sm:flex-row justify-between gap-4">
          <div className="space-y-2">
            <TGSkeleton className="h-7 w-64" />
            <TGSkeleton className="h-4 w-96" />
          </div>
          <div className="flex gap-2.5">
            <TGSkeleton className="h-9 w-28" />
            <TGSkeleton className="h-9 w-40" />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <TGCard key={i} className="p-4 space-y-3">
              <TGSkeleton className="h-3 w-32" />
              <TGSkeleton className="h-8 w-24" />
              <TGSkeleton className="h-3 w-40" />
            </TGCard>
          ))}
        </div>
      </div>
    );
  }

  const scoreVariant =
    summary.safety_score >= 85 ? 'safe' : summary.safety_score >= 70 ? 'warning' : 'critical';

  return (
    <div className="space-y-6 max-w-7xl mx-auto select-none">
      {/* 1. Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-2 border-b border-[#E4E9EF]">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-[#16202A] tracking-tight">
            {greeting}, {user?.full_name || 'Quản trị viên'}
          </h1>
          <div className="flex items-center gap-2 mt-1 text-xs text-[#667085]">
            <span className="font-semibold text-[#16202A] flex items-center gap-1">
              <Car className="w-3.5 h-3.5 text-[#175CD3]" />
              Xe cá nhân: 51H-982.45
            </span>
            <span>•</span>
            <span>{todayFormatted}</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 shrink-0 self-start lg:self-auto">
          <TGButton
            variant="secondary"
            size="sm"
            onClick={fetchDashboardData}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          >
            Làm mới
          </TGButton>

          <Link href="/live">
            <TGButton
              variant="primary"
              size="sm"
              leftIcon={<Video className="w-3.5 h-3.5" />}
            >
              Giám Sát Live
            </TGButton>
          </Link>
        </div>
      </div>

      {/* 2. Top Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <TGCard variant="default" signalVariant={scoreVariant} className="p-4 relative hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-[#667085] block">
                Điểm An Toàn
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-extrabold text-[#16202A] tracking-tight">
                  {summary.safety_score.toFixed(1)}
                </span>
                <span className="text-xs text-[#667085]">/ 100</span>
              </div>
            </div>
            <div className="w-9 h-9 rounded-[8px] bg-[#ECFDF3] border border-[#A6F4C5] flex items-center justify-center text-[#17B26A] shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-[#F1F4F7] flex items-center justify-between text-xs">
            <span className="inline-flex items-center gap-1 text-[#17B26A] font-semibold">
              <TrendingUp className="w-3.5 h-3.5" />
              +2.4% tuần này
            </span>
            <span className="text-[#17B26A] font-medium">Đạt chuẩn</span>
          </div>
        </TGCard>

        <TGCard variant="default" signalVariant="info" className="p-4 relative hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-[#667085] block">
                Trạng Thái Phương Tiện
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-extrabold text-[#16202A] tracking-tight">
                  1 / 1
                </span>
                <span className="text-xs text-[#667085]">xe trực tuyến</span>
              </div>
            </div>
            <div className="w-9 h-9 rounded-[8px] bg-[#EFF8FF] border border-[#B2DDFF] flex items-center justify-center text-[#2E90FA] shrink-0">
              <Car className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-[#F1F4F7] flex items-center justify-between text-xs">
            <span className="text-[#667085]">Biển số: 51H-982.45</span>
            <span className="text-[#17B26A] font-semibold">Tài xế đang sẵn sàng</span>
          </div>
        </TGCard>

        <TGCard variant="default" signalVariant="primary" className="p-4 relative hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-[#667085] block">
                Tổng Hành Trình
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-extrabold text-[#16202A] tracking-tight">
                  {summary.total_sessions}
                </span>
                <span className="text-xs text-[#667085]">chuyến</span>
              </div>
            </div>
            <div className="w-9 h-9 rounded-[8px] bg-[#EFF4FF] border border-[#B2CCFF] flex items-center justify-center text-[#175CD3] shrink-0">
              <Route className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-[#F1F4F7] flex items-center justify-between text-xs">
            <span className="text-[#667085]">{summary.total_driving_hours} giờ vận hành</span>
            <span className="text-[#17B26A] font-semibold">100% DMS</span>
          </div>
        </TGCard>

        <TGCard variant="default" signalVariant={summary.total_violations === 0 ? 'safe' : 'critical'} className="p-4 relative hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-[#667085] block">
                Cảnh Báo & Sự Cố
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className={`text-2xl font-extrabold tracking-tight ${summary.total_violations > 0 ? 'text-[#F04438]' : 'text-[#16202A]'}`}>
                  {summary.total_violations}
                </span>
                <span className="text-xs text-[#667085]">sự kiện</span>
              </div>
            </div>
            <div className={`w-9 h-9 rounded-[8px] border flex items-center justify-center shrink-0 ${summary.total_violations > 0 ? 'bg-[#FEF3F2] border-[#FECDCA] text-[#F04438]' : 'bg-[#ECFDF3] border-[#A6F4C5] text-[#17B26A]'}`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-[#F1F4F7] flex items-center justify-between text-xs">
            <span className={`font-semibold ${summary.total_violations > 0 ? 'text-[#F04438]' : 'text-[#17B26A]'}`}>
              {summary.total_violations > 0 ? 'Cần xử lý' : 'Không có rủi ro'}
            </span>
            <Link href="/violations" className="text-[#175CD3] hover:underline flex items-center gap-0.5 font-medium">
              Chi tiết <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </TGCard>
      </div>

      {/* 3. Main Live Fleet & Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <TGCard variant="default" className="h-full flex flex-col">
            <TGCardHeader>
              <TGCardTitle>
                <Activity className="w-4 h-4 text-[#175CD3]" />
                Giám Sát Phương Tiện Trực Tiếp
              </TGCardTitle>
              <TGStatusBadge variant="safe" size="sm" pulse>
                1 Xe Đang Kết Nối
              </TGStatusBadge>
            </TGCardHeader>

            <TGCardContent className="p-0 flex-1 overflow-x-auto">
              <table className="w-full min-w-[680px] text-sm text-left">
                <thead className="bg-[#F8FAFC] border-b border-[#E4E9EF] text-xs font-semibold text-[#475467] uppercase">
                  <tr>
                    <th className="px-4 py-3">Phương Tiện</th>
                    <th className="px-4 py-3">Tài Xế & Vai Trò</th>
                    <th className="px-4 py-3">Vị Trí Hiện Tại</th>
                    <th className="px-4 py-3">Tốc Độ</th>
                    <th className="px-4 py-3">Trạng Thái AI</th>
                    <th className="px-4 py-3 text-right">Tác Vụ</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E4E9EF]">
                  {activeVehicles.map((v) => (
                    <tr key={v.id} className="hover:bg-[#F8FAFC] transition-colors">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <TGVehicleBadge plateNumber={v.plateNumber} type={v.vehicleType} status={v.status} />
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="font-semibold text-[#16202A]">{v.driverName}</div>
                        <div className="text-xs text-[#667085]">{v.fleetName}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-[#475467]">
                        <span className="truncate max-w-[160px] block">{v.location}</span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <span className={`font-mono font-bold ${v.speed > v.speedLimit ? 'text-[#F04438]' : 'text-[#16202A]'}`}>
                            {v.speed} km/h
                          </span>
                          <span className="text-xs text-[#98A2B3]">/ {v.speedLimit}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <TGStatusBadge variant={v.status} size="sm" showIcon={true}>
                          {v.status === 'safe' ? 'Bình thường' : v.status === 'warning' ? 'Cảnh báo tốc độ' : 'Nguy cơ buồn ngủ'}
                        </TGStatusBadge>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <Link href="/live">
                          <TGButton variant="outline" size="sm" className="h-8 text-xs font-medium px-3">
                            Camera Live
                          </TGButton>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TGCardContent>
            <TGCardFooter className="justify-end">
              <Link href="/live" className="text-xs text-[#175CD3] font-semibold hover:underline flex items-center gap-1">
                Phòng điều hành toàn cảnh <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </TGCardFooter>
          </TGCard>
        </div>

        <div>
          <TGCard variant="default" className="h-full flex flex-col justify-between">
            <TGCardHeader>
              <TGCardTitle>
                <TrendingUp className="w-4 h-4 text-[#175CD3]" />
                Phân Bố Rủi Ro An Toàn
              </TGCardTitle>
            </TGCardHeader>
            <TGCardContent className="space-y-4">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#16202A] flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#F04438]" />
                    Cảnh báo buồn ngủ (DMS)
                  </span>
                  <span className="font-mono font-bold text-[#16202A]">
                    {summary.violation_breakdown?.['drowsiness'] || 2} sự kiện
                  </span>
                </div>
                <div className="h-2 w-full bg-[#F1F4F7] rounded-full overflow-hidden">
                  <div className="h-full bg-[#F04438] rounded-full" style={{ width: '45%' }} />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#16202A] flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#F79009]" />
                    Vượt tốc độ giới hạn
                  </span>
                  <span className="font-mono font-bold text-[#16202A]">
                    {summary.violation_breakdown?.['speeding'] || 1} sự kiện
                  </span>
                </div>
                <div className="h-2 w-full bg-[#F1F4F7] rounded-full overflow-hidden">
                  <div className="h-full bg-[#F79009] rounded-full" style={{ width: '25%' }} />
                </div>
              </div>

              <div className="p-3 bg-[#F8FAFC] border border-[#E4E9EF] rounded-[8px] flex items-center justify-between mt-3">
                <span className="text-xs font-semibold text-[#16202A] flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-[#175CD3]" />
                  Hệ Thống 12 Module AI
                </span>
                <TGStatusBadge variant="safe" size="sm" showIcon={false}>
                  Hoạt động 100%
                </TGStatusBadge>
              </div>
            </TGCardContent>
            <TGCardFooter>
              <Link href="/analytics" className="w-full text-center text-xs text-[#175CD3] font-semibold hover:underline">
                Báo cáo phân tích nâng cao →
              </Link>
            </TGCardFooter>
          </TGCard>
        </div>
      </div>

      {/* 4. Alert Section */}
      <TGCard variant="default">
        <TGCardHeader>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-[6px] bg-[#FEF3F2] border border-[#FECDCA] flex items-center justify-center text-[#F04438]">
              <AlertOctagon className="w-4 h-4" />
            </div>
            <TGCardTitle>Cảnh Báo Cần Xử Lý</TGCardTitle>
          </div>
          <div className="flex items-center gap-2">
            <TGStatusBadge variant={pendingViolations.length > 0 ? 'warning' : 'safe'} size="sm">
              {pendingViolations.length} Hồ sơ mới
            </TGStatusBadge>
            <Link href="/violations">
              <TGButton variant="secondary" size="sm">Quản lý vi phạm</TGButton>
            </Link>
          </div>
        </TGCardHeader>
        <TGCardContent className="p-0 overflow-x-auto">
          {pendingViolations.length === 0 ? (
            <TGEmptyState
              icon={CheckCircle2}
              title="Không có cảnh báo chưa xử lý"
              description="Toàn bộ sự kiện an toàn hôm nay đều đã được đối soát."
            />
          ) : (
            <table className="w-full text-sm text-left">
              <thead className="bg-[#F8FAFC] border-b border-[#E4E9EF] text-xs font-semibold text-[#475467] uppercase">
                <tr>
                  <th className="px-4 py-3">Mức Độ</th>
                  <th className="px-4 py-3">Phương Tiện</th>
                  <th className="px-4 py-3">Tài Xế</th>
                  <th className="px-4 py-3">Loại Sự Kiện</th>
                  <th className="px-4 py-3">Thời Gian Ghi Nhận</th>
                  <th className="px-4 py-3">Độ Tin Cậy AI</th>
                  <th className="px-4 py-3 text-right">Tác Vụ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E4E9EF]">
                {pendingViolations.map((v) => (
                  <tr key={v.id} className="hover:bg-[#F8FAFC] transition-colors">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <TGStatusBadge
                        variant={String(v.severity).toUpperCase() === 'CRITICAL' ? 'critical' : String(v.severity).toUpperCase() === 'WARNING' ? 'warning' : 'info'}
                        size="sm"
                      >
                        {String(v.severity).toUpperCase() === 'CRITICAL' ? 'Nghiêm trọng' : String(v.severity).toUpperCase() === 'WARNING' ? 'Cảnh báo cao' : 'Thông tin'}
                      </TGStatusBadge>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-mono font-bold text-[#16202A] px-2 py-0.5 rounded bg-[#F1F4F7] border border-[#E4E9EF]">
                        {v.vehicle_plate || v.plate_text || '51H-982.45'}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-[#667085]">{user?.full_name || 'Chủ xe'}</td>
                    <td className="px-4 py-3 whitespace-nowrap font-medium text-[#16202A]">
                      {v.violation_type === 'speeding' ? 'Vượt tốc độ cho phép' : v.violation_type === 'drowsiness' ? 'Phát hiện ngủ gật (DMS)' : v.violation_type}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-[#667085] font-mono text-xs">
                      {v.timestamp ? new Date(v.timestamp).toLocaleString('vi-VN') : 'Vừa ghi nhận'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-mono text-[#175CD3] font-semibold">
                        {v.confidence != null ? `${(v.confidence * 100).toFixed(0)}%` : 'Chưa có dữ liệu'}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right">
                      <Link href="/violations">
                        <TGButton variant="secondary" size="sm" className="h-8 text-xs font-medium px-3">
                          Xem chi tiết
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

      {/* 5. Edge Devices & Recent Sessions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <TGCard variant="default">
          <TGCardHeader>
            <TGCardTitle>
              <Cpu className="w-4 h-4 text-[#175CD3]" />
              Trạng Thái Thiết Bị & Cảm Biến Trên Xe
            </TGCardTitle>
            <TGStatusBadge variant="safe" size="sm" showIcon={false}>
              100% Sẵn sàng
            </TGStatusBadge>
          </TGCardHeader>
          <TGCardContent className="p-0 overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-[#F8FAFC] border-b border-[#E4E9EF] text-xs font-semibold text-[#475467] uppercase">
                <tr>
                  <th className="px-4 py-3">Thiết Bị / Cảm Biến</th>
                  <th className="px-4 py-3">Thông Số Kỹ Thuật</th>
                  <th className="px-4 py-3 text-right">Trạng Thái</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E4E9EF]">
                {edgeDevices.map((dev, idx) => (
                  <tr key={idx} className="hover:bg-[#F8FAFC] transition-colors">
                    <td className="px-4 py-3 font-medium text-[#16202A] whitespace-nowrap">{dev.name}</td>
                    <td className="px-4 py-3 text-[#667085] whitespace-nowrap text-xs">{dev.detail}</td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <TGStatusBadge variant={dev.status} size="sm" showIcon={false}>
                        {dev.label}
                      </TGStatusBadge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TGCardContent>
        </TGCard>

        <TGCard variant="default">
          <TGCardHeader>
            <TGCardTitle>
              <Route className="w-4 h-4 text-[#175CD3]" />
              Hành Trình Gần Đây Của Xe
            </TGCardTitle>
            <Link href="/journeys">
              <TGButton variant="ghost" size="sm" className="text-xs text-[#175CD3]">
                Tất cả hành trình →
              </TGButton>
            </Link>
          </TGCardHeader>
          <TGCardContent className="p-0 overflow-x-auto">
            {recentSessions.length === 0 ? (
              <TGEmptyState
                icon={Route}
                title="Chưa có phiên hành trình nào"
                description="Các chuyến đi được kích hoạt từ thiết bị lái sẽ hiển thị tại đây."
              />
            ) : (
              <table className="w-full text-sm text-left">
                <thead className="bg-[#F8FAFC] border-b border-[#E4E9EF] text-xs font-semibold text-[#475467] uppercase">
                  <tr>
                    <th className="px-4 py-3">Phiên ID</th>
                    <th className="px-4 py-3">Tài Xế</th>
                    <th className="px-4 py-3">Thời Lượng</th>
                    <th className="px-4 py-3">Bắt Đầu</th>
                    <th className="px-4 py-3 text-right">Chi Tiết</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E4E9EF]">
                  {recentSessions.slice(0, 5).map((s) => (
                    <tr key={s.id} className="hover:bg-[#F8FAFC] transition-colors">
                      <td className="px-4 py-3 font-mono font-semibold text-[#175CD3] whitespace-nowrap">#{s.id}</td>
                      <td className="px-4 py-3 whitespace-nowrap font-medium text-[#16202A]">{user?.full_name || 'Chủ xe'}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-[#667085]">{s.total_minutes ? `${s.total_minutes} phút` : '< 1 phút'}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-[#667085] font-mono text-xs">
                        {s.start_time ? new Date(s.start_time).toLocaleString('vi-VN') : 'Hôm nay'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <Link href={`/journeys?id=${s.id}`}>
                          <TGButton
                            variant="outline"
                            size="sm"
                            className="h-8 text-xs font-medium px-3"
                          >
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
    </div>
  );
}
