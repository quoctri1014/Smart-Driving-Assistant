'use client';

import React, { useEffect, useState } from 'react';
import {
  HardDrive,
  Radio,
  Camera,
  Eye,
  MapPin,
  Wifi,
  Database,
  RotateCcw,
  Search,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  X,
  ChevronRight,
  ShieldAlert
} from 'lucide-react';
import { apiClient } from '../../../services/apiClient';
import { TGCard, TGCardHeader, TGCardTitle, TGCardContent } from '../../../components/ui/TGCard';
import { TGStatusBadge } from '../../../components/ui/TGStatusBadge';
import { TGButton } from '../../../components/ui/TGButton';
import { TGVehicleBadge } from '../../../components/ui/TGVehicleBadge';

export interface DeviceHealthItem {
  id: number;
  device_id: string;
  vehicle_id?: number | null;
  fleet_id?: number | null;
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE' | 'UNKNOWN';
  road_camera_status: string;
  cabin_camera_status: string;
  gps_status: string;
  dms_status: string;
  network_status: string;
  storage_status: string;
  firmware_version: string;
  last_heartbeat_at?: string;
  seconds_since_last_seen: number;
}

export default function DevicesPage() {
  const [devices, setDevices] = useState<DeviceHealthItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedDevice, setSelectedDevice] = useState<DeviceHealthItem | null>(null);

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<DeviceHealthItem[]>('/api/v1/devices');
      if (Array.isArray(data)) {
        setDevices(data);
      }
    } catch (e) {
      console.warn('Devices fetch error', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const filteredDevices = devices.filter((d) => {
    const matchStatus = statusFilter === 'ALL' || d.status === statusFilter;
    const matchSearch =
      d.device_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (d.vehicle_id && String(d.vehicle_id).includes(searchTerm));
    return matchStatus && matchSearch;
  });

  const onlineCount = devices.filter((d) => d.status === 'ONLINE').length;
  const degradedCount = devices.filter((d) => d.status === 'DEGRADED').length;
  const offlineCount = devices.filter((d) => d.status === 'OFFLINE').length;

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#16202A] flex items-center gap-2.5">
            <Radio className="w-6 h-6 text-[#175CD3]" />
            Giám Sát Sức Khỏe Thiết Bị & Đội Xe
          </h1>
        </div>

        <TGButton variant="outline" size="sm" onClick={fetchDevices} isLoading={loading}>
          <RotateCcw className="w-4 h-4 mr-1.5" />
          Làm mới
        </TGButton>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <TGCard variant="default" signalVariant="safe" className="p-4">
          <span className="text-sm font-medium text-[#475467]">Thiết bị trực tuyến</span>
          <p className="text-2xl font-bold text-[#16202A] mt-1.5">{onlineCount}</p>
        </TGCard>

        <TGCard variant="default" signalVariant="warning" className="p-4">
          <span className="text-sm font-medium text-[#475467]">Cảnh báo suy giảm</span>
          <p className="text-2xl font-bold text-[#16202A] mt-1.5">{degradedCount}</p>
        </TGCard>

        <TGCard variant="default" signalVariant="critical" className="p-4">
          <span className="text-sm font-medium text-[#475467]">Mất tín hiệu</span>
          <p className="text-2xl font-bold text-[#16202A] mt-1.5">{offlineCount}</p>
        </TGCard>

        <TGCard variant="default" className="p-4">
          <span className="text-sm font-medium text-[#475467]">Tổng thiết bị quản lý</span>
          <p className="text-2xl font-bold text-[#16202A] mt-1.5">{devices.length}</p>
        </TGCard>
      </div>

      {/* Main Table */}
      <TGCard variant="default" className="overflow-hidden">
        <div className="p-3.5 bg-[#F8FAFC] border-b border-[#E4E9EF] flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="relative w-72">
              <Search className="w-4 h-4 text-[#98A2B3] absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Tìm mã thiết bị, xe ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-white border border-[#E4E9EF] rounded-lg pl-9 pr-3 py-2 text-sm text-[#16202A] focus:outline-none focus:border-[#175CD3]"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-white border border-[#E4E9EF] rounded-lg px-3 py-2 text-sm text-[#16202A]"
            >
              <option value="ALL">Tất cả trạng thái</option>
              <option value="ONLINE">Trực tuyến</option>
              <option value="DEGRADED">Suy giảm</option>
              <option value="OFFLINE">Mất tín hiệu</option>
            </select>
          </div>

          <span className="text-sm text-[#667085]">
            Hiển thị: <strong className="text-[#16202A]">{filteredDevices.length}</strong> thiết bị
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#F8FAFC] border-b border-[#E4E9EF] text-xs font-semibold text-[#475467] uppercase">
              <tr>
                <th className="p-3.5">Mã thiết bị</th>
                <th className="p-3.5">Phương tiện</th>
                <th className="p-3.5">Trạng thái</th>
                <th className="p-3.5">Camera đường</th>
                <th className="p-3.5">Camera cabin</th>
                <th className="p-3.5">GPS</th>
                <th className="p-3.5">Mạng 4G</th>
                <th className="p-3.5">Cập nhật</th>
                <th className="p-3.5 text-right">Chi tiết</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E4E9EF] text-[#16202A]">
              {loading ? (
                <tr>
                  <td colSpan={9} className="p-8 text-center text-[#98A2B3] font-mono text-sm">
                    Đang tải danh sách thiết bị...
                  </td>
                </tr>
              ) : filteredDevices.length === 0 ? (
                <tr>
                  <td colSpan={9} className="p-12 text-center text-[#98A2B3] space-y-2">
                    <CheckCircle2 className="w-8 h-8 mx-auto text-[#17B26A]/50" />
                    <p className="text-sm font-semibold text-[#16202A]">Không có thiết bị nào</p>
                  </td>
                </tr>
              ) : (
                filteredDevices.map((d) => {
                  const statusVariant = d.status === 'ONLINE' ? 'safe' : d.status === 'DEGRADED' ? 'warning' : 'critical';

                  return (
                    <tr
                      key={d.id}
                      onClick={() => setSelectedDevice(d)}
                      className="hover:bg-[#F8FAFC] cursor-pointer transition-colors"
                    >
                      <td className="p-3.5 font-semibold text-[#175CD3]">
                        {d.device_id}
                      </td>
                      <td className="p-3.5">
                        <TGVehicleBadge plateNumber={d.vehicle_id ? `Xe #${d.vehicle_id}` : 'Chưa gán xe'} />
                      </td>
                      <td className="p-3.5">
                        <TGStatusBadge variant={statusVariant} size="sm">
                          {d.status === 'ONLINE' ? 'Hoạt động' : d.status === 'DEGRADED' ? 'Suy giảm' : 'Mất tín hiệu'}
                        </TGStatusBadge>
                      </td>
                      <td className="p-3.5 text-xs">
                        <span className={d.road_camera_status === 'ONLINE' ? 'text-[#17B26A] font-medium' : 'text-[#F04438] font-medium'}>
                          {d.road_camera_status === 'ONLINE' ? 'Bình thường' : 'Lỗi'}
                        </span>
                      </td>
                      <td className="p-3.5 text-xs">
                        <span className={d.cabin_camera_status === 'ONLINE' ? 'text-[#17B26A] font-medium' : 'text-[#F79009] font-medium'}>
                          {d.cabin_camera_status === 'ONLINE' ? 'Bình thường' : 'Lỗi'}
                        </span>
                      </td>
                      <td className="p-3.5 text-xs">
                        <span className={d.gps_status === 'ONLINE' ? 'text-[#17B26A] font-medium' : 'text-[#F04438] font-medium'}>
                          {d.gps_status === 'ONLINE' ? 'Bình thường' : 'Mất GPS'}
                        </span>
                      </td>
                      <td className="p-3.5 text-xs">
                        <span className={d.network_status === 'ONLINE' ? 'text-[#17B26A] font-medium' : 'text-[#F79009] font-medium'}>
                          {d.network_status === 'ONLINE' ? '4G Tốt' : 'Yếu'}
                        </span>
                      </td>
                      <td className="p-3.5 text-xs text-[#667085]">
                        {d.seconds_since_last_seen < 60
                          ? 'Vừa xong'
                          : `${Math.floor(d.seconds_since_last_seen / 60)} phút trước`}
                      </td>
                      <td className="p-3.5 text-right">
                        <span className="text-sm text-[#175CD3] font-medium flex items-center justify-end gap-1 hover:underline">
                          Xem
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

      {/* Device Detail Drawer */}
      {selectedDevice && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end animate-in fade-in duration-200">
          <div 
            className="w-full max-w-lg bg-[#FFFFFF] h-full shadow-2xl flex flex-col border-l border-[#E4E9EF] p-5 space-y-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#E4E9EF]">
              <div className="flex items-center gap-2.5">
                <Radio className="w-5 h-5 text-[#175CD3]" />
                <div>
                  <h3 className="text-base font-bold text-[#16202A]">{selectedDevice.device_id}</h3>
                  <span className="text-xs text-[#667085] font-mono">Firmware: {selectedDevice.firmware_version}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedDevice(null)}
                className="p-1.5 text-[#667085] hover:text-[#16202A] hover:bg-[#E4E9EF] rounded-lg cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-sm">
              <div className="p-3.5 bg-[#F6F8FA] border border-[#E4E9EF] rounded-lg flex items-center justify-between">
                <span className="text-[#475467] font-medium">Trạng thái kết nối:</span>
                <TGStatusBadge 
                  variant={selectedDevice.status === 'ONLINE' ? 'safe' : selectedDevice.status === 'DEGRADED' ? 'warning' : 'critical'}
                  size="sm"
                >
                  {selectedDevice.status}
                </TGStatusBadge>
              </div>

              <div className="space-y-2">
                <h4 className="font-semibold text-[#16202A] uppercase tracking-wider text-xs">Kiểm Tra 7 Phân Hệ</h4>
                <div className="p-3 bg-white border border-[#E4E9EF] rounded-lg divide-y divide-[#E4E9EF] text-sm">
                  <div className="flex justify-between py-2.5 items-center">
                    <span className="flex items-center gap-2 text-[#475467]"><Camera className="w-4 h-4 text-[#175CD3]" /> Road Camera (Đường Lộ)</span>
                    <span className="font-mono font-semibold text-[#17B26A]">{selectedDevice.road_camera_status}</span>
                  </div>
                  <div className="flex justify-between py-2.5 items-center">
                    <span className="flex items-center gap-2 text-[#475467]"><Eye className="w-4 h-4 text-[#175CD3]" /> Cabin Camera (DMS Tài Xế)</span>
                    <span className="font-mono font-semibold text-[#17B26A]">{selectedDevice.cabin_camera_status}</span>
                  </div>
                  <div className="flex justify-between py-2.5 items-center">
                    <span className="flex items-center gap-2 text-[#475467]"><MapPin className="w-4 h-4 text-[#175CD3]" /> GPS & Định Vị GNSS</span>
                    <span className="font-mono font-semibold text-[#17B26A]">{selectedDevice.gps_status}</span>
                  </div>
                  <div className="flex justify-between py-2.5 items-center">
                    <span className="flex items-center gap-2 text-[#475467]"><Wifi className="w-4 h-4 text-[#175CD3]" /> Mạng Di Động 4G / LTE</span>
                    <span className="font-mono font-semibold text-[#17B26A]">{selectedDevice.network_status}</span>
                  </div>
                  <div className="flex justify-between py-2.5 items-center">
                    <span className="flex items-center gap-2 text-[#475467]"><Database className="w-4 h-4 text-[#175CD3]" /> Bộ Nhớ Cục Bộ (SD / SSD)</span>
                    <span className="font-mono font-semibold text-[#17B26A]">{selectedDevice.storage_status}</span>
                  </div>
                </div>
              </div>

              <div className="p-3.5 bg-[#F6F8FA] border border-[#E4E9EF] rounded-lg text-xs text-[#667085]">
                <strong className="block text-[#16202A] mb-1 font-semibold">Chính sách Offline Watchdog:</strong>
                Thiết bị tự động chuyển trạng thái OFFLINE và gửi thông báo khẩn cấp tới Dispatcher nếu mất heartbeat quá 5 phút.
              </div>
            </div>

            <div className="mt-auto pt-3 border-t border-[#E4E9EF]">
              <TGButton variant="outline" size="sm" className="w-full" onClick={() => setSelectedDevice(null)}>
                Đóng
              </TGButton>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
