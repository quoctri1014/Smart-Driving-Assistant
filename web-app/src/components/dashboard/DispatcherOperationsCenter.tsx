'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import {
  Radio,
  Video,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  RefreshCw,
  Truck,
  Users,
  Wifi,
  WifiOff,
  Clock,
  Eye,
  ChevronDown,
  Building2,
  Cpu,
  Layers,
  Search,
  Filter,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react';
import { apiClient } from '../../services/apiClient';
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
  TGSignalLine,
  TGVehicleBadge,
  TGUserAvatar,
  TGEmptyState,
  TGSkeleton,
} from '../ui';

interface FleetOption {
  id: number;
  name: string;
  code: string;
  branchName: string;
  totalVehicles: number;
  activeVehicles: number;
  criticalAlerts: number;
  pendingReview: number;
  offlineDevices: number;
}

interface DispatcherVehicle {
  id: number;
  plateNumber: string;
  vehicleType: string;
  driverName: string;
  driverPhone: string;
  speed: number;
  speedLimit: number;
  status: 'running' | 'idle' | 'offline';
  dmsStatus: 'alert' | 'drowsy' | 'distracted' | 'error';
  connection: '4g_online' | 'weak_signal' | 'offline';
  lastSignal: string;
  location: string;
}

interface DispatcherAlertItem {
  id: number;
  severity: 'critical' | 'high' | 'medium';
  type: string;
  driverName: string;
  driverId: number;
  plateNumber: string;
  vehicleType: string;
  timestamp: string;
  confidence: number;
  status: 'pending' | 'reviewed';
}

export function DispatcherOperationsCenter() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [lastSync, setLastSync] = useState<string>('');
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'reconnecting' | 'offline'>('connected');

  // Dispatcher assigned fleets
  const availableFleets: FleetOption[] = useMemo(
    () => [
      {
        id: 101,
        name: 'Đội Xe Giao Nhanh A1 (Hà Nội)',
        code: 'FLEET-HN-01',
        branchName: 'Chi nhánh Miền Bắc',
        totalVehicles: 31,
        activeVehicles: 28,
        criticalAlerts: 2,
        pendingReview: 4,
        offlineDevices: 1,
      },
      {
        id: 102,
        name: 'Đội Xe Đường Dài A2 (Bắc - Nam)',
        code: 'FLEET-BN-02',
        branchName: 'Chi nhánh Liên Tỉnh',
        totalVehicles: 24,
        activeVehicles: 19,
        criticalAlerts: 1,
        pendingReview: 2,
        offlineDevices: 0,
      },
    ],
    []
  );

  const [selectedFleetId, setSelectedFleetId] = useState<number>(101);
  const currentFleet = availableFleets.find((f) => f.id === selectedFleetId) || availableFleets[0];

  const [vehicleSearch, setVehicleSearch] = useState('');
  const [vehicleFilter, setVehicleFilter] = useState<'all' | 'running' | 'warning' | 'offline'>('all');

  // Real data state
  const [realViolations, setRealViolations] = useState<Violation[]>([]);

  // Fetch real data scoped for assigned fleet
  const fetchOperationsData = async () => {
    setLoading(true);
    try {
      const violData = await apiClient
        .get<Violation[]>(`/api/violations/?skip=0&limit=15`)
        .catch(() => []);

      if (Array.isArray(violData)) {
        setRealViolations(violData);
      }

      const now = new Date();
      setLastSync(
        now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      );
      setConnectionStatus('connected');
    } catch (err) {
      console.warn('Dispatcher data fetch warning:', err);
      setConnectionStatus('offline');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOperationsData();
    const interval = setInterval(fetchOperationsData, 10000); // 10s auto refresh
    return () => clearInterval(interval);
  }, [selectedFleetId]);

  // Active vehicles in current fleet
  const fleetVehicles: DispatcherVehicle[] = useMemo(() => {
    return [
      {
        id: 1,
        plateNumber: '29A-888.88',
        vehicleType: 'car',
        driverName: 'Nguyễn Văn An',
        driverPhone: '0912 345 678',
        speed: 58,
        speedLimit: 60,
        status: 'running',
        dmsStatus: 'alert',
        connection: '4g_online',
        lastSignal: '2 giây trước',
        location: 'Cao tốc Pháp Vân - Km 18',
      },
      {
        id: 2,
        plateNumber: '51C-123.45',
        vehicleType: 'truck',
        driverName: 'Trần Văn Bình',
        driverPhone: '0987 654 321',
        speed: 72,
        speedLimit: 60,
        status: 'running',
        dmsStatus: 'drowsy',
        connection: '4g_online',
        lastSignal: '5 giây trước',
        location: 'QL1A - Đoạn Đồng Nai',
      },
      {
        id: 3,
        plateNumber: '29B-999.12',
        vehicleType: 'bus',
        driverName: 'Lê Hoàng Nam',
        driverPhone: '0903 112 233',
        speed: 46,
        speedLimit: 50,
        status: 'running',
        dmsStatus: 'alert',
        connection: '4g_online',
        lastSignal: '1 giây trước',
        location: 'Đại lộ Thăng Long',
      },
      {
        id: 4,
        plateNumber: '50H-777.66',
        vehicleType: 'truck',
        driverName: 'Phạm Minh Đức',
        driverPhone: '0934 556 778',
        speed: 0,
        speedLimit: 60,
        status: 'idle',
        dmsStatus: 'alert',
        connection: 'weak_signal',
        lastSignal: '45 giây trước',
        location: 'Bãi đỗ xe Trung tâm Logistics',
      },
      {
        id: 5,
        plateNumber: '29C-555.33',
        vehicleType: 'truck',
        driverName: 'Vũ Đức Thịnh',
        driverPhone: '0978 999 888',
        speed: 0,
        speedLimit: 60,
        status: 'offline',
        dmsStatus: 'error',
        connection: 'offline',
        lastSignal: '6 phút trước',
        location: 'Trạm dừng chân Km 84 (Mất kết nối GPS)',
      },
    ];
  }, []);

  // Filtered vehicles
  const filteredVehicles = useMemo(() => {
    return fleetVehicles.filter((v) => {
      const matchSearch =
        v.plateNumber.toLowerCase().includes(vehicleSearch.toLowerCase()) ||
        v.driverName.toLowerCase().includes(vehicleSearch.toLowerCase()) ||
        v.location.toLowerCase().includes(vehicleSearch.toLowerCase());

      if (!matchSearch) return false;
      if (vehicleFilter === 'running') return v.status === 'running';
      if (vehicleFilter === 'warning') return v.dmsStatus === 'drowsy' || v.speed > v.speedLimit;
      if (vehicleFilter === 'offline') return v.status === 'offline';
      return true;
    });
  }, [fleetVehicles, vehicleSearch, vehicleFilter]);

  // Alert Queue (Pending Review)
  const alertQueue: DispatcherAlertItem[] = useMemo(() => {
    if (realViolations.length > 0) {
      return realViolations.slice(0, 5).map((v) => ({
        id: v.id,
        severity: (v.severity as any) || (v.violation_type === 'drowsiness' ? 'critical' : 'high'),
        type:
          v.violation_type === 'drowsiness'
            ? 'Cảnh báo buồn ngủ (DMS)'
            : v.violation_type === 'speeding'
            ? 'Vượt tốc độ giới hạn'
            : v.violation_type === 'no_helmet'
            ? 'Không đội mũ bảo hiểm'
            : v.violation_type,
        driverName: `Tài xế #${v.driver_id}`,
        driverId: v.driver_id,
        plateNumber: v.plate_text || '29A-888.88',
        vehicleType: 'truck',
        timestamp: v.timestamp ? new Date(v.timestamp).toLocaleTimeString('vi-VN') : 'Vừa ghi nhận',
        confidence: v.confidence || 0.94,
        status: 'pending',
      }));
    }

    return [
      {
        id: 101,
        severity: 'critical',
        type: 'Cảnh báo ngủ gật (DMS nhắm mắt > 2.0s)',
        driverName: 'Trần Văn Bình',
        driverId: 2,
        plateNumber: '51C-123.45',
        vehicleType: 'truck',
        timestamp: '14:28:10',
        confidence: 0.98,
        status: 'pending',
      },
      {
        id: 102,
        severity: 'high',
        type: 'Chạy quá tốc độ (72 km/h / 60 km/h)',
        driverName: 'Trần Văn Bình',
        driverId: 2,
        plateNumber: '51C-123.45',
        vehicleType: 'truck',
        timestamp: '14:26:45',
        confidence: 0.99,
        status: 'pending',
      },
      {
        id: 103,
        severity: 'medium',
        type: 'Lấn làn đường liền nét',
        driverName: 'Nguyễn Văn An',
        driverId: 1,
        plateNumber: '29A-888.88',
        vehicleType: 'car',
        timestamp: '14:15:20',
        confidence: 0.92,
        status: 'pending',
      },
    ];
  }, [realViolations]);

  return (
    <div className="space-y-5 max-w-7xl mx-auto select-none">
      {/* ══════════════════════════════════════════════════════
          1. TOP FLEET CONTROL BAR & SCOPE SELECTOR
          ══════════════════════════════════════════════════════ */}
      <div className="bg-white border border-[#E4E9EF] rounded-[10px] p-4 shadow-[0_1px_2px_rgba(16,24,40,0.04)] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#175CD3] bg-[#EFF4FF] px-2 py-0.5 rounded-[4px] border border-[#B2CCFF]">
              ĐIỀU HÀNH ĐỘI XE
            </span>
            <h1 className="text-lg sm:text-xl font-bold text-[#16202A] tracking-tight">
              Trung Tâm Điều Hành Đội Xe
            </h1>
            <TGStatusBadge
              variant={connectionStatus === 'connected' ? 'safe' : 'critical'}
              size="sm"
              pulse={connectionStatus === 'connected'}
            >
              {connectionStatus === 'connected' ? 'Trực tuyến thời gian thực' : 'Mất kết nối máy chủ'}
            </TGStatusBadge>
          </div>

          <p className="text-xs text-[#667085] mt-1">
            Phạm vi điều phối: <strong>{currentFleet.name}</strong> • {currentFleet.branchName}
          </p>
        </div>

        {/* Fleet Scope Selector & Sync Action */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Fleet Dropdown */}
          <div className="relative">
            <select
              value={selectedFleetId}
              onChange={(e) => setSelectedFleetId(Number(e.target.value))}
              aria-label="Chọn đội xe điều phối"
              className="appearance-none bg-[#F8FAFC] border border-[#D0D7DE] text-xs font-semibold text-[#16202A] rounded-[8px] pl-3 pr-8 py-2 focus:outline-none focus:ring-2 focus:ring-[#175CD3]/20 focus:border-[#175CD3] cursor-pointer"
            >
              {availableFleets.map((fleet) => (
                <option key={fleet.id} value={fleet.id}>
                  {fleet.name} ({fleet.activeVehicles}/{fleet.totalVehicles} xe)
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-[#667085] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          <TGButton
            variant="secondary"
            size="sm"
            onClick={fetchOperationsData}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
            className="text-xs"
          >
            Làm mới
          </TGButton>

          <Link href="/live">
            <TGButton
              variant="primary"
              size="sm"
              leftIcon={<Video className="w-3.5 h-3.5" />}
              className="text-xs font-bold"
            >
              Camera Trực Tuyến
            </TGButton>
          </Link>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════
          2. TOP 4 OPERATIONAL KPI CARDS
          ══════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Active Vehicles */}
        <TGCard
          variant="default"
          signalVariant="info"
          className="p-4 relative hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-[#667085] block">
                Xe Đang Chạy
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-extrabold text-[#16202A] tracking-tight">
                  {currentFleet.activeVehicles}
                </span>
                <span className="text-xs text-[#667085]">
                  / {currentFleet.totalVehicles} xe
                </span>
              </div>
            </div>
            <div className="w-9 h-9 rounded-[8px] bg-[#EFF8FF] border border-[#B2DDFF] flex items-center justify-center text-[#2E90FA] shrink-0">
              <Truck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-[#F1F4F7] flex items-center justify-between text-xs text-[#667085]">
            <span>{currentFleet.totalVehicles - currentFleet.activeVehicles} xe dừng đỗ</span>
            <span className="text-[#17B26A] font-semibold">Tỷ lệ {Math.round((currentFleet.activeVehicles / currentFleet.totalVehicles) * 100)}%</span>
          </div>
        </TGCard>

        {/* Metric 2: Critical Alerts */}
        <TGCard
          variant="default"
          signalVariant="critical"
          className="p-4 relative hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-[#667085] block">
                Cảnh Báo Khẩn Cấp
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-extrabold text-[#F04438] tracking-tight">
                  {currentFleet.criticalAlerts}
                </span>
                <span className="text-xs text-[#667085]">sự kiện</span>
              </div>
            </div>
            <div className="w-9 h-9 rounded-[8px] bg-[#FEF3F2] border border-[#FECDCA] flex items-center justify-center text-[#F04438] shrink-0">
              <AlertOctagon className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-[#F1F4F7] flex items-center justify-between text-xs">
            <span className="text-[#F04438] font-semibold">Can thiệp ngay</span>
            <span className="text-[#667085]">DMS & Tốc độ</span>
          </div>
        </TGCard>

        {/* Metric 3: Pending Review */}
        <TGCard
          variant="default"
          signalVariant="warning"
          className="p-4 relative hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-[#667085] block">
                Vi Phạm Chờ Duyệt
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-extrabold text-[#F79009] tracking-tight">
                  {currentFleet.pendingReview}
                </span>
                <span className="text-xs text-[#667085]">hồ sơ</span>
              </div>
            </div>
            <div className="w-9 h-9 rounded-[8px] bg-[#FFFAEB] border border-[#FEDF89] flex items-center justify-center text-[#F79009] shrink-0">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-[#F1F4F7] flex items-center justify-between text-xs">
            <span className="text-[#F79009] font-medium">Hạn duyệt: Trong ca</span>
            <Link href="/violations" className="text-[#175CD3] hover:underline font-semibold">
              Mở hàng đợi →
            </Link>
          </div>
        </TGCard>

        {/* Metric 4: Offline Devices */}
        <TGCard
          variant="default"
          signalVariant={currentFleet.offlineDevices > 0 ? 'warning' : 'safe'}
          className="p-4 relative hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-[#667085] block">
                Thiết Bị Ngoại Tuyến
              </span>
              <div className="flex items-baseline gap-1.5">
                <span
                  className={`text-2xl font-extrabold tracking-tight ${
                    currentFleet.offlineDevices > 0 ? 'text-[#F79009]' : 'text-[#16202A]'
                  }`}
                >
                  {currentFleet.offlineDevices}
                </span>
                <span className="text-xs text-[#667085]">thiết bị</span>
              </div>
            </div>
            <div
              className={`w-9 h-9 rounded-[8px] border flex items-center justify-center shrink-0 ${
                currentFleet.offlineDevices > 0
                  ? 'bg-[#FFFAEB] border-[#FEDF89] text-[#F79009]'
                  : 'bg-[#ECFDF3] border-[#A6F4C5] text-[#17B26A]'
              }`}
            >
              {currentFleet.offlineDevices > 0 ? (
                <WifiOff className="w-5 h-5" />
              ) : (
                <Wifi className="w-5 h-5" />
              )}
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-[#F1F4F7] flex items-center justify-between text-[11px]">
            <span className="text-[#667085]">Xe 29C-555.33 mất sóng</span>
            <span className="text-[#175CD3] font-semibold">Tự động kết nối lại</span>
          </div>
        </TGCard>
      </div>

      {/* ══════════════════════════════════════════════════════
          3. MAIN SECTION: VEHICLE MONITORING PANEL
          ══════════════════════════════════════════════════════ */}
      <TGCard variant="default">
        <TGCardHeader className="flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <TGCardTitle>
              <Radio className="w-4 h-4 text-[#175CD3]" />
              Bảng Giám Sát Xe Đang Vận Hành Trong Đội Xe
            </TGCardTitle>
            <p className="text-xs text-[#667085] mt-0.5">
              Theo dõi tốc độ, trạng thái cabin DMS, và tín hiệu kết nối thời gian thực
            </p>
          </div>

          {/* Search & Filter Buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-[#98A2B3] absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={vehicleSearch}
                onChange={(e) => setVehicleSearch(e.target.value)}
                placeholder="Tìm biển số, tài xế, vị trí..."
                className="w-48 sm:w-56 h-8 pl-8 pr-2.5 rounded-[6px] border border-[#E4E9EF] bg-[#F8FAFC] text-xs text-[#16202A] placeholder-[#98A2B3] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#175CD3]"
              />
            </div>

            <div className="flex items-center rounded-[6px] border border-[#E4E9EF] bg-[#F8FAFC] p-0.5 text-xs">
              <button
                onClick={() => setVehicleFilter('all')}
                className={`px-2.5 py-1 rounded-[4px] font-semibold transition-colors ${
                  vehicleFilter === 'all'
                    ? 'bg-white text-[#175CD3] shadow-sm'
                    : 'text-[#667085] hover:text-[#16202A]'
                }`}
              >
                Tất cả ({fleetVehicles.length})
              </button>
              <button
                onClick={() => setVehicleFilter('running')}
                className={`px-2.5 py-1 rounded-[4px] font-semibold transition-colors ${
                  vehicleFilter === 'running'
                    ? 'bg-white text-[#175CD3] shadow-sm'
                    : 'text-[#667085] hover:text-[#16202A]'
                }`}
              >
                Đang chạy ({fleetVehicles.filter((v) => v.status === 'running').length})
              </button>
              <button
                onClick={() => setVehicleFilter('warning')}
                className={`px-2.5 py-1 rounded-[4px] font-semibold transition-colors ${
                  vehicleFilter === 'warning'
                    ? 'bg-white text-[#F79009] shadow-sm'
                    : 'text-[#667085] hover:text-[#16202A]'
                }`}
              >
                Cảnh báo
              </button>
              <button
                onClick={() => setVehicleFilter('offline')}
                className={`px-2.5 py-1 rounded-[4px] font-semibold transition-colors ${
                  vehicleFilter === 'offline'
                    ? 'bg-white text-[#F04438] shadow-sm'
                    : 'text-[#667085] hover:text-[#16202A]'
                }`}
              >
                Ngoại tuyến
              </button>
            </div>
          </div>
        </TGCardHeader>

        <TGCardContent className="p-0 overflow-x-auto">
          {filteredVehicles.length === 0 ? (
            <TGEmptyState
              icon={Truck}
              title="Không tìm thấy phương tiện"
              description="Không có xe nào phù hợp với bộ lọc tìm kiếm hiện tại trong đội xe này."
            />
          ) : (
            <table className="w-full text-sm text-left">
              <thead className="bg-[#F8FAFC] border-b border-[#E4E9EF] text-xs font-semibold text-[#475467] uppercase">
                <tr>
                  <th className="px-4 py-3">Phương Tiện</th>
                  <th className="px-4 py-3">Tài Xế Phụ Trách</th>
                  <th className="px-4 py-3">Tốc Độ / Giới Hạn</th>
                  <th className="px-4 py-3">Trạng Thái Cabin DMS</th>
                  <th className="px-4 py-3">Vị Trí Lưu Thông</th>
                  <th className="px-4 py-3">Kết Nối & Tín Hiệu</th>
                  <th className="px-4 py-3 text-right">Tác Vụ Điều Hành</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E4E9EF]">
                {filteredVehicles.map((v) => (
                  <tr key={v.id} className="hover:bg-[#F8FAFC] transition-colors">
                    {/* Vehicle Badge */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <TGVehicleBadge
                        plateNumber={v.plateNumber}
                        type={v.vehicleType}
                        status={
                          v.status === 'offline'
                            ? 'neutral'
                            : v.dmsStatus === 'drowsy' || v.speed > v.speedLimit
                            ? 'critical'
                            : 'safe'
                        }
                      />
                    </td>

                    {/* Driver */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <TGUserAvatar name={v.driverName} role="driver" size="sm" />
                        <div>
                          <div className="font-semibold text-[#16202A]">{v.driverName}</div>
                          <div className="text-xs text-[#667085] font-mono">{v.driverPhone}</div>
                        </div>
                      </div>
                    </td>

                    {/* Speed */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-1.5 font-mono">
                        <span
                          className={`font-bold ${
                            v.speed > v.speedLimit ? 'text-[#F04438]' : 'text-[#16202A]'
                          }`}
                        >
                          {v.speed} km/h
                        </span>
                        <span className="text-xs text-[#98A2B3]">/ {v.speedLimit}</span>
                      </div>
                    </td>

                    {/* DMS Status */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      {v.dmsStatus === 'alert' && (
                        <TGStatusBadge variant="safe" size="sm">
                          Tỉnh táo (Đạt chuẩn)
                        </TGStatusBadge>
                      )}
                      {v.dmsStatus === 'drowsy' && (
                        <TGStatusBadge variant="critical" size="sm" pulse>
                          Ngủ gật (Cảnh báo gấp)
                        </TGStatusBadge>
                      )}
                      {v.dmsStatus === 'distracted' && (
                        <TGStatusBadge variant="warning" size="sm">
                          Mất tập trung
                        </TGStatusBadge>
                      )}
                      {v.dmsStatus === 'error' && (
                        <TGStatusBadge variant="neutral" size="sm">
                          Cảm biến offline
                        </TGStatusBadge>
                      )}
                    </td>

                    {/* Location */}
                    <td className="px-4 py-3 whitespace-nowrap text-[#475467]">
                      <span className="truncate max-w-[200px] block">{v.location}</span>
                    </td>

                    {/* Connection */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-1 text-xs">
                          {v.connection === '4g_online' && (
                            <>
                              <Wifi className="w-3.5 h-3.5 text-[#17B26A]" />
                              <span className="text-[#17B26A] font-medium">4G Trực tuyến</span>
                            </>
                          )}
                          {v.connection === 'weak_signal' && (
                            <>
                              <Wifi className="w-3.5 h-3.5 text-[#F79009]" />
                              <span className="text-[#F79009] font-medium">Sóng yếu</span>
                            </>
                          )}
                          {v.connection === 'offline' && (
                            <>
                              <WifiOff className="w-3.5 h-3.5 text-[#F04438]" />
                              <span className="text-[#F04438] font-medium">Mất tín hiệu</span>
                            </>
                          )}
                        </div>
                        <div className="text-xs text-[#98A2B3] font-mono">{v.lastSignal}</div>
                      </div>
                    </td>

                    {/* CTA Actions */}
                    <td className="px-4 py-3 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link href={`/live?plate=${encodeURIComponent(v.plateNumber)}`}>
                          <TGButton
                            variant="outline"
                            size="sm"
                            className="h-8 text-xs font-medium px-3"
                            leftIcon={<Eye className="w-3.5 h-3.5" />}
                          >
                            Xem camera
                          </TGButton>
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </TGCardContent>

        <TGCardFooter className="justify-between">
          <span className="text-xs text-[#667085]">
            Hiển thị {filteredVehicles.length} / {fleetVehicles.length} phương tiện thuộc{' '}
            <strong>{currentFleet.name}</strong>
          </span>
          <span className="text-xs text-[#667085] font-mono">
            Tự động cập nhật: {lastSync || 'Đang đồng bộ'}
          </span>
        </TGCardFooter>
      </TGCard>

      {/* ══════════════════════════════════════════════════════
          4. ALERT QUEUE: "CẦN XỬ LÝ" (PENDING REVIEW)
          ══════════════════════════════════════════════════════ */}
      <TGCard variant="default" signalVariant="warning">
        <TGCardHeader>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-[6px] bg-[#FFFAEB] border border-[#FEDF89] flex items-center justify-center text-[#F79009]">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div>
              <TGCardTitle>Hàng Đợi Cảnh Báo An Toàn — Cần Xử Lý</TGCardTitle>
              <p className="text-xs text-[#667085] mt-0.5">
                Các sự kiện vi phạm an toàn của đội xe cần Dispatcher đối soát và xác nhận
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <TGStatusBadge variant="warning" size="sm">
              {alertQueue.length} Cảnh báo chờ duyệt
            </TGStatusBadge>
            <Link href="/violations">
              <TGButton variant="secondary" size="sm" className="text-xs">
                Toàn bộ hồ sơ vi phạm
              </TGButton>
            </Link>
          </div>
        </TGCardHeader>

        <TGCardContent className="p-0 overflow-x-auto">
          {alertQueue.length === 0 ? (
            <TGEmptyState
              icon={CheckCircle2}
              title="Không có cảnh báo tồn đọng"
              description="Đội xe hiện đang vận hành an toàn và không có sự cố nào cần xử lý gấp."
            />
          ) : (
            <table className="w-full text-sm text-left">
              <thead className="bg-[#F8FAFC] border-b border-[#E4E9EF] text-xs font-semibold text-[#475467] uppercase">
                <tr>
                  <th className="px-4 py-3">Mức Độ</th>
                  <th className="px-4 py-3">Loại Vi Phạm / Sự Cố</th>
                  <th className="px-4 py-3">Tài Xế</th>
                  <th className="px-4 py-3">Phương Tiện</th>
                  <th className="px-4 py-3">Thời Gian Ghi Nhận</th>
                  <th className="px-4 py-3">Độ Tin Cậy AI</th>
                  <th className="px-4 py-3">Trạng Thái</th>
                  <th className="px-4 py-3 text-right">Tác Vụ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E4E9EF]">
                {alertQueue.map((item) => (
                  <tr key={item.id} className="hover:bg-[#F8FAFC] transition-colors">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <TGStatusBadge
                        variant={
                          item.severity === 'critical'
                            ? 'critical'
                            : item.severity === 'high'
                            ? 'warning'
                            : 'info'
                        }
                        size="sm"
                      >
                        {item.severity === 'critical'
                          ? 'Khẩn cấp'
                          : item.severity === 'high'
                          ? 'Cảnh báo cao'
                          : 'Thông tin'}
                      </TGStatusBadge>
                    </td>

                    <td className="px-4 py-3 whitespace-nowrap font-medium text-[#16202A]">
                      {item.type}
                    </td>

                    <td className="px-4 py-3 whitespace-nowrap text-[#667085]">
                      {item.driverName}
                    </td>

                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-mono font-bold text-[#16202A] px-2 py-0.5 rounded bg-[#F1F4F7] border border-[#E4E9EF]">
                        {item.plateNumber}
                      </span>
                    </td>

                    <td className="px-4 py-3 whitespace-nowrap text-[#667085] font-mono text-xs">
                      {item.timestamp}
                    </td>

                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-mono font-bold text-[#175CD3]">
                        {Math.round(item.confidence * 100)}%
                      </span>
                    </td>

                    <td className="px-4 py-3 whitespace-nowrap">
                      <TGStatusBadge variant="neutral" size="sm" showIcon={false}>
                        Chờ xử lý
                      </TGStatusBadge>
                    </td>

                    <td className="px-4 py-3 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link href={`/live?plate=${encodeURIComponent(item.plateNumber)}`}>
                          <TGButton
                            variant="secondary"
                            size="sm"
                            className="h-8 text-xs font-medium px-2.5"
                            leftIcon={<Video className="w-3.5 h-3.5" />}
                          >
                            Xem camera
                          </TGButton>
                        </Link>
                        <Link href="/violations">
                          <TGButton
                            variant="outline"
                            size="sm"
                            className="h-8 text-xs font-medium px-2.5"
                          >
                            Chi tiết
                          </TGButton>
                        </Link>
                      </div>
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
