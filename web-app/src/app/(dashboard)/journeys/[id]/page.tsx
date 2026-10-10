'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Route,
  ArrowLeft,
  Clock,
  Car,
  User,
  ShieldCheck,
  AlertTriangle,
  Play,
  Pause,
  RotateCcw,
  MapPin,
  Gauge,
  Layers,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { apiClient } from '../../../../services/apiClient';
import { TGCard, TGCardHeader, TGCardTitle, TGCardContent } from '../../../../components/ui/TGCard';
import { TGStatusBadge } from '../../../../components/ui/TGStatusBadge';
import { TGVehicleBadge } from '../../../../components/ui/TGVehicleBadge';
import { TGButton } from '../../../../components/ui/TGButton';

export interface TripEventData {
  id: number;
  event_type: string;
  timestamp: string;
  video_offset_ms?: number | null;
  sequence_num: number;
  severity: 'CRITICAL' | 'WARNING' | 'INFO' | 'SAFE';
  latitude?: number | null;
  longitude?: number | null;
  metadata?: string | null;
  violation_id?: number | null;
}

export interface ReplayData {
  session_id: number;
  driver_id: number;
  start_time: string;
  end_time: string;
  total_minutes: number;
  safety_score: number;
  events: TripEventData[];
  telemetry_points: {
    video_offset_ms: number;
    speed_kmh: number;
    safe_distance_m: number;
    lat: number;
    lng: number;
    status: string;
  }[];
}

export default function TripReplayPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;

  const [replay, setReplay] = useState<ReplayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeOffsetMs, setActiveOffsetMs] = useState<number>(0);
  const [selectedEvent, setSelectedEvent] = useState<TripEventData | null>(null);

  useEffect(() => {
    async function loadReplay() {
      setLoading(true);
      try {
        const data = await apiClient.get<ReplayData>(`/api/v1/sessions/${sessionId}/replay`);
        if (data) {
          setReplay(data);
          if (data.events && data.events.length > 0) {
            setSelectedEvent(data.events[0]);
            setActiveOffsetMs(data.events[0].video_offset_ms || 0);
          }
        }
      } catch (e) {
        console.warn('Load replay error', e);
      } finally {
        setLoading(false);
      }
    }
    if (sessionId) loadReplay();
  }, [sessionId]);

  const handleEventClick = (event: TripEventData) => {
    setSelectedEvent(event);
    if (event.video_offset_ms !== undefined && event.video_offset_ms !== null) {
      setActiveOffsetMs(event.video_offset_ms);
    }
  };

  // Find nearest telemetry point based on active offset
  const currentTelemetry = replay?.telemetry_points?.reduce((prev, curr) => {
    return Math.abs(curr.video_offset_ms - activeOffsetMs) < Math.abs(prev.video_offset_ms - activeOffsetMs) ? curr : prev;
  }, replay.telemetry_points[0]) || {
    video_offset_ms: 0,
    speed_kmh: 58.0,
    safe_distance_m: 18.4,
    lat: 21.0285,
    lng: 105.8542,
    status: 'normal'
  };

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push('/journeys')}
            className="p-2 text-[#667085] hover:text-[#16202A] hover:bg-[#F1F4F7] rounded-lg border border-[#E4E9EF] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-[#16202A]">Safety Timeline & Replay #TRIP-{sessionId}</h1>
              <TGStatusBadge variant="safe" size="sm">Hoàn thành</TGStatusBadge>
            </div>
            <p className="text-[#667085] text-xs mt-0.5">
              Đồng bộ dòng thời gian sự cố an toàn, video offset và tọa độ GPS
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 bg-white border border-[#E4E9EF] rounded-lg text-xs font-mono">
            <span className="text-[#667085]">Safety Score: </span>
            <strong className="text-[#17B26A] text-sm">{replay?.safety_score || 94} / 100</strong>
          </div>
        </div>
      </div>

      {/* Main Grid: Replay Viewport & Map / Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left / Center Viewport (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Synchronized Visual Viewport */}
          <div className="relative aspect-video rounded-xl bg-[#16202A] overflow-hidden border border-[#E4E9EF] flex items-center justify-center">
            <div className="text-center p-6 space-y-2 text-white/80">
              <Sparkles className="w-8 h-8 mx-auto text-[#175CD3]" />
              <p className="text-sm font-bold text-white">Chế Độ Mô Phỏng Hành Trình An Toàn</p>
              <p className="text-xs text-[#98A2B3] max-w-sm mx-auto font-mono">
                Offset: {Math.floor(activeOffsetMs / 1000)}s • Tốc độ: {currentTelemetry.speed_kmh} km/h • Cự ly: {currentTelemetry.safe_distance_m}m
              </p>
            </div>

            {/* Bottom HUD Overlay */}
            <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between p-2.5 bg-black/70 backdrop-blur-md rounded-lg text-white text-xs font-mono">
              <div className="flex items-center gap-2">
                <Gauge className="w-4 h-4 text-[#17B26A]" />
                <span>{currentTelemetry.speed_kmh} km/h</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-[#2E90FA]" />
                <span>{currentTelemetry.lat.toFixed(4)}, {currentTelemetry.lng.toFixed(4)}</span>
              </div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-[#17B26A]" />
                <span>Cự ly: {currentTelemetry.safe_distance_m}m</span>
              </div>
            </div>
          </div>

          {/* Selected Event Context Card */}
          {selectedEvent && (
            <TGCard variant="default" className="p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#16202A] flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-[#175CD3]" />
                  Chi Tiết Sự Kiện An Toàn Đang Chọn
                </span>
                <TGStatusBadge 
                  variant={selectedEvent.severity === 'CRITICAL' ? 'critical' : selectedEvent.severity === 'WARNING' ? 'warning' : 'safe'}
                  size="sm"
                >
                  {selectedEvent.severity}
                </TGStatusBadge>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs pt-1">
                <div>
                  <span className="text-[#667085] block">Loại sự kiện:</span>
                  <strong className="text-[#16202A] font-mono">{selectedEvent.event_type}</strong>
                </div>
                <div>
                  <span className="text-[#667085] block">Thời điểm:</span>
                  <span className="text-[#16202A] font-mono">{selectedEvent.timestamp?.split('T')[1]?.substring(0, 8)}</span>
                </div>
                <div>
                  <span className="text-[#667085] block">Video Offset:</span>
                  <span className="text-[#175CD3] font-mono font-bold">{(selectedEvent.video_offset_ms || 0) / 1000}s</span>
                </div>
                <div>
                  <span className="text-[#667085] block">Hồ sơ vi phạm:</span>
                  {selectedEvent.violation_id ? (
                    <button 
                      onClick={() => router.push('/violations')}
                      className="text-[#175CD3] font-bold underline flex items-center gap-1"
                    >
                      #VIOL-{selectedEvent.violation_id}
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  ) : (
                    <span className="text-[#98A2B3]">Không</span>
                  )}
                </div>
              </div>
            </TGCard>
          )}
        </div>

        {/* Right Interactive Safety Timeline Rail (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <TGCard variant="default" className="p-4 h-full flex flex-col">
            <TGCardHeader className="p-0 pb-3 border-b border-[#E4E9EF] flex items-center justify-between">
              <TGCardTitle className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                <Route className="w-4 h-4 text-[#175CD3]" />
                Safety Timeline Rail ({replay?.events?.length || 0} Sự Kiện)
              </TGCardTitle>
              <span className="text-[10px] text-[#667085] font-mono">Semantic Pins</span>
            </TGCardHeader>

            <div className="flex-1 overflow-y-auto space-y-2 py-3">
              {(!replay?.events || replay.events.length === 0) ? (
                <div className="text-center p-6 text-xs text-[#98A2B3]">
                  Chuyến đi hoàn toàn an toàn, không có sự kiện vi phạm nào.
                </div>
              ) : (
                replay.events.map((e) => {
                  const isSelected = selectedEvent?.id === e.id;
                  const pinColor = e.severity === 'CRITICAL' ? 'bg-[#F04438]' : e.severity === 'WARNING' ? 'bg-[#F79009]' : e.severity === 'SAFE' ? 'bg-[#17B26A]' : 'bg-[#175CD3]';

                  return (
                    <div
                      key={e.id}
                      onClick={() => handleEventClick(e)}
                      className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-[#175CD3]/[0.05] border-[#175CD3] ring-1 ring-[#175CD3]'
                          : 'bg-[#FFFFFF] border-[#E4E9EF] hover:border-[#98A2B3]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className={`w-2.5 h-2.5 rounded-full ${pinColor}`} />
                          <strong className="text-[#16202A] font-semibold">{e.event_type}</strong>
                        </div>
                        <span className="font-mono text-[10px] text-[#667085]">
                          +{(e.video_offset_ms || 0) / 1000}s
                        </span>
                      </div>

                      <div className="flex items-center justify-between mt-1 text-[11px] text-[#667085]">
                        <span>Thời gian: {e.timestamp?.split('T')[1]?.substring(0, 8)}</span>
                        {e.violation_id && (
                          <span className="text-[#F04438] font-semibold">Liên kết Vi phạm</span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </TGCard>
        </div>
      </div>
    </div>
  );
}
