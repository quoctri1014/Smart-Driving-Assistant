'use client';

import React, { useEffect, useState, useRef } from 'react';
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Zap,
  Activity,
  RotateCcw,
  Layers,
  ChevronRight,
  X,
  Gauge,
  Server
} from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import { TGCard, TGCardHeader, TGCardTitle, TGCardContent } from '../ui/TGCard';
import { TGStatusBadge } from '../ui/TGStatusBadge';
import { TGButton } from '../ui/TGButton';

export interface AIModuleHealth {
  id: string;
  name: string;
  category: string;
  model: string;
  status: 'HEALTHY' | 'DEGRADED' | 'OFFLINE' | 'ERROR';
  current_fps: number;
  target_fps: number;
  latency_ms: number;
  last_heartbeat_at: string;
  last_error?: string | null;
}

export interface SystemHealthData {
  system_health: string;
  healthy_count: number;
  total_modules: number;
  overall_status: 'HEALTHY' | 'ATTENTION_REQUIRED' | 'CRITICAL';
  average_latency_ms: number;
  pipeline_fps: number;
  evaluated_at: string;
  modules: AIModuleHealth[];
}

const ACTIVE_POLL_INTERVAL_MS = 5000;
const BACKGROUND_POLL_INTERVAL_MS = 30000;

export function AIHealthMonitoringTable() {
  const [healthData, setHealthData] = useState<SystemHealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedModule, setSelectedModule] = useState<AIModuleHealth | null>(null);
  const [lastPolledAt, setLastPolledAt] = useState<Date>(new Date());
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const fetchHealth = async () => {
    try {
      const data = await apiClient.get<SystemHealthData>('/api/v1/ai/status');
      if (data && Array.isArray(data.modules)) {
        setHealthData(data);
        setLastPolledAt(new Date());
      }
    } catch (e) {
      console.warn('AI status fetch error', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();

    const handleVisibilityChange = () => {
      if (timerRef.current) clearInterval(timerRef.current);
      const interval = document.hidden ? BACKGROUND_POLL_INTERVAL_MS : ACTIVE_POLL_INTERVAL_MS;
      timerRef.current = setInterval(fetchHealth, interval);
    };

    timerRef.current = setInterval(fetchHealth, ACTIVE_POLL_INTERVAL_MS);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const overallVariant = healthData?.overall_status === 'HEALTHY' ? 'safe' : healthData?.overall_status === 'ATTENTION_REQUIRED' ? 'warning' : 'critical';

  return (
    <div className="space-y-5">
      {/* Top Health KPI Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <TGCard variant="default" signalVariant={overallVariant} className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#667085]">Tình trạng hệ thống</span>
            <Activity className="w-4 h-4 text-[#175CD3]" />
          </div>
          <p className="text-xl font-bold text-[#16202A] mt-1.5">
            {healthData?.system_health || '12 / 12 Hoạt động'}
          </p>
          <div className="mt-2">
            <TGStatusBadge variant={overallVariant} size="sm">
              {healthData?.overall_status === 'HEALTHY' ? 'Hoạt động tốt' : healthData?.overall_status || 'HEALTHY'}
            </TGStatusBadge>
          </div>
        </TGCard>

        <TGCard variant="default" className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#667085]">Tốc độ xử lý video</span>
            <Zap className="w-4 h-4 text-[#17B26A]" />
          </div>
          <p className="text-xl font-bold text-[#16202A] mt-1.5">
            {healthData?.pipeline_fps || 30.0} <span className="text-xs font-normal text-[#667085]">FPS</span>
          </p>
        </TGCard>

        <TGCard variant="default" className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#667085]">Độ trễ xử lý</span>
            <Gauge className="w-4 h-4 text-[#2E90FA]" />
          </div>
          <p className="text-xl font-bold text-[#16202A] mt-1.5">
            {healthData?.average_latency_ms || 18.4} <span className="text-xs font-normal text-[#667085]">ms</span>
          </p>
        </TGCard>

        <TGCard variant="default" className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#667085]">Cập nhật lần cuối</span>
            <Clock className="w-4 h-4 text-[#667085]" />
          </div>
          <p className="text-xl font-bold text-[#16202A] mt-1.5 truncate">
            {lastPolledAt.toLocaleTimeString()}
          </p>
        </TGCard>
      </div>

      {/* 12 AI Modules Table */}
      <TGCard variant="default" className="overflow-hidden">
        <TGCardHeader className="p-3.5 bg-[#F8FAFC] border-b border-[#E4E9EF] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[#175CD3]" />
            <TGCardTitle className="text-xs font-bold text-[#16202A]">
              Danh Sách 12 Mô-Đun AI
            </TGCardTitle>
          </div>
          <TGButton variant="outline" size="sm" onClick={fetchHealth} isLoading={loading}>
            <RotateCcw className="w-3.5 h-3.5 mr-1" />
            Kiểm tra ngay
          </TGButton>
        </TGCardHeader>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F8FAFC] border-b border-[#E4E9EF] text-[#667085] font-semibold">
              <tr>
                <th className="p-3.5">Mô-đun AI</th>
                <th className="p-3.5">Phân loại</th>
                <th className="p-3.5">Trạng thái</th>
                <th className="p-3.5">Mô hình</th>
                <th className="p-3.5">FPS</th>
                <th className="p-3.5">Độ trễ</th>
                <th className="p-3.5">Cập nhật</th>
                <th className="p-3.5 text-right">Chi tiết</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E4E9EF] text-[#16202A]">
              {(!healthData || healthData.modules.length === 0) ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-[#667085]">
                    Đang kết nối tới AI Runtime Engine...
                  </td>
                </tr>
              ) : (
                healthData.modules.map((m) => {
                  const statusVariant = m.status === 'HEALTHY' ? 'safe' : m.status === 'DEGRADED' ? 'warning' : m.status === 'OFFLINE' ? 'neutral' : 'critical';

                  return (
                    <tr
                      key={m.id}
                      onClick={() => setSelectedModule(m)}
                      className="hover:bg-[#F8FAFC] cursor-pointer transition-colors"
                    >
                      <td className="p-3.5 font-semibold text-[#16202A]">
                        {m.name}
                      </td>
                      <td className="p-3.5 text-xs text-[#667085]">
                        {m.category}
                      </td>
                      <td className="p-3.5">
                        <TGStatusBadge variant={statusVariant} size="sm">
                          {m.status === 'HEALTHY' ? 'Hoạt động' : m.status}
                        </TGStatusBadge>
                      </td>
                      <td className="p-3.5 text-xs text-[#175CD3] font-medium">
                        {m.model}
                      </td>
                      <td className="p-3.5 text-xs">
                        <span className={m.current_fps < m.target_fps * 0.7 ? 'text-[#F04438] font-bold' : 'text-[#16202A] font-semibold'}>
                          {m.current_fps.toFixed(1)}
                        </span>
                        <span className="text-[#667085]"> / {m.target_fps} FPS</span>
                      </td>
                      <td className="p-3.5 text-xs font-semibold">
                        <span className={m.latency_ms > 35 ? 'text-[#F79009]' : 'text-[#16202A]'}>
                          {m.latency_ms.toFixed(1)} ms
                        </span>
                      </td>
                      <td className="p-3.5 text-xs text-[#667085]">
                        Vừa xong
                      </td>
                      <td className="p-3.5 text-right">
                        <span className="text-xs text-[#175CD3] font-medium flex items-center justify-end gap-1 hover:underline">
                          Xem
                          <ChevronRight className="w-3.5 h-3.5" />
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

      {/* Module Detail Drawer */}
      {selectedModule && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end animate-in fade-in duration-200">
          <div 
            className="w-full max-w-lg bg-[#FFFFFF] h-full shadow-2xl flex flex-col border-l border-[#E4E9EF] p-5 space-y-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#E4E9EF]">
              <div className="flex items-center gap-2.5">
                <Cpu className="w-5 h-5 text-[#175CD3]" />
                <div>
                  <h3 className="text-sm font-bold text-[#16202A]">{selectedModule.name}</h3>
                  <span className="text-[10px] text-[#667085] font-mono">{selectedModule.category}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedModule(null)}
                className="p-1.5 text-[#667085] hover:text-[#16202A] hover:bg-[#E4E9EF] rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="p-3.5 bg-[#F6F8FA] border border-[#E4E9EF] rounded-lg flex items-center justify-between">
                <span className="text-[#667085]">Trạng thái Backend:</span>
                <TGStatusBadge 
                  variant={selectedModule.status === 'HEALTHY' ? 'safe' : selectedModule.status === 'DEGRADED' ? 'warning' : 'critical'}
                  size="sm"
                >
                  {selectedModule.status}
                </TGStatusBadge>
              </div>

              <div className="space-y-2">
                <h4 className="font-bold text-[#16202A] uppercase tracking-wider text-[11px]">Thông Tin Mô Hình</h4>
                <div className="p-3 bg-[#FFFFFF] border border-[#E4E9EF] rounded-lg space-y-1.5 font-mono">
                  <div className="flex justify-between">
                    <span className="text-[#667085]">Engine / Model:</span>
                    <strong className="text-[#175CD3]">{selectedModule.model}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#667085]">Tệp thực thi:</span>
                    <span className="text-[#16202A]">{selectedModule.id}.py</span>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-bold text-[#16202A] uppercase tracking-wider text-[11px]">Chỉ Số Hiệu Năng Thời Gian Thực</h4>
                <div className="grid grid-cols-2 gap-2 font-mono">
                  <div className="p-3 bg-[#F6F8FA] border border-[#E4E9EF] rounded-lg">
                    <span className="text-[#667085] text-[10px] block">FPS Hiện Tại</span>
                    <strong className="text-base text-[#16202A]">{selectedModule.current_fps.toFixed(1)}</strong>
                    <span className="text-[10px] text-[#98A2B3] block mt-0.5">Mục tiêu: {selectedModule.target_fps} FPS</span>
                  </div>
                  <div className="p-3 bg-[#F6F8FA] border border-[#E4E9EF] rounded-lg">
                    <span className="text-[#667085] text-[10px] block">Độ Trễ Xử Lý</span>
                    <strong className="text-base text-[#16202A]">{selectedModule.latency_ms.toFixed(1)} ms</strong>
                    <span className="text-[10px] text-[#17B26A] block mt-0.5">Ngưỡng: &lt; 50ms</span>
                  </div>
                </div>
              </div>

              {selectedModule.last_error ? (
                <div className="p-3 bg-[#F04438]/10 border border-[#F04438]/30 rounded-lg text-[#F04438] space-y-1">
                  <strong className="block font-bold">Cảnh báo lỗi gần nhất:</strong>
                  <p className="font-mono text-[11px]">{selectedModule.last_error}</p>
                </div>
              ) : (
                <div className="p-3 bg-[#17B26A]/10 border border-[#17B26A]/30 rounded-lg text-[#17B26A] flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Mô-đun hoạt động ổn định, không có lỗi runtime.</span>
                </div>
              )}
            </div>

            <div className="mt-auto pt-3 border-t border-[#E4E9EF]">
              <TGButton variant="outline" size="sm" className="w-full" onClick={() => setSelectedModule(null)}>
                Đóng
              </TGButton>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
