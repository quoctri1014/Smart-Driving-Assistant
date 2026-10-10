'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  Shield,
  Layers,
  ArrowLeft,
  Volume2,
  VolumeX,
  Play,
  Pause,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Info,
} from 'lucide-react';

import { SystemHealthBanner } from '../../../components/live/SystemHealthBanner';
import { PriorityAlertBar } from '../../../components/live/PriorityAlertBar';
import { UnifiedTelemetryStrip } from '../../../components/live/UnifiedTelemetryStrip';
import { DetectionTabsPanel, DetectionTabType } from '../../../components/live/DetectionTabsPanel';
import { CabinCameraViewport } from '../../../components/live/CabinCameraViewport';
import { RealtimeEventTimeline, TimelineEventItem } from '../../../components/live/RealtimeEventTimeline';
import { AIDiagnosticsPanel } from '../../../components/live/AIDiagnosticsPanel';
import { AlertPriority } from '../../../lib/driving/alert-engine';
import { DetectionResult, DriverMonitorResult } from '../../../types/detection';

export default function ComponentShowcasePage() {
  // Interactive Showcase States
  const [healthSocketStatus, setHealthSocketStatus] = useState<'CONNECTED' | 'CONNECTING' | 'DISCONNECTED'>('CONNECTED');
  const [healthProcessingMs, setHealthProcessingMs] = useState<number | null>(24);

  const [alertPriority, setAlertPriority] = useState<AlertPriority>('COLLISION_DANGER');
  const [alertMuted, setAlertMuted] = useState(false);

  const [activeTab, setActiveTab] = useState<DetectionTabType>('plates');

  const [events, setEvents] = useState<TimelineEventItem[]>([
    {
      id: 'demo-1',
      timestamp: '10:45:12',
      level: 'critical',
      title: 'Nguy cơ va chạm phía trước (Khẩn cấp)',
      details: 'Cự ly ước tính: 4.8m • TTC: 0.9s • Xe máy tạt đầu khẩn cấp',
      status: 'pending',
    },
    {
      id: 'demo-2',
      timestamp: '10:43:05',
      level: 'warning',
      title: 'Tài xế mất tập trung (PERCLOS 42%)',
      details: 'Phát hiện nhắm mắt > 1.8 giây • Cảnh báo âm thanh giọng nói',
      status: 'confirmed',
    },
    {
      id: 'demo-3',
      timestamp: '10:40:22',
      level: 'info',
      title: 'Nhận diện biển báo giới hạn tốc độ',
      details: 'Biển P.127: Tối đa 60 km/h trên tuyến đường hiện tại',
      status: 'confirmed',
    },
  ]);

  // Demo Mock Detections (Explicitly Labeled DEMO)
  const mockDetectionResult: DetectionResult = {
    frame_id: 1204,
    timestamp: Date.now(),
    vehicles: [
      { id: 1, class: 'car', bbox: { x1: 120, y1: 150, x2: 240, y2: 290 }, speed_kmh: 58 },
      { id: 2, class: 'truck', bbox: { x1: 300, y1: 140, x2: 480, y2: 320 }, speed_kmh: 45 },
      { id: 3, class: 'motorbike', bbox: { x1: 210, y1: 190, x2: 280, y2: 270 }, speed_kmh: 35 },
    ],
    plates: [
      {
        plate_text: '29A-888.88',
        confidence: 0.95,
        bbox: { x1: 140, y1: 260, x2: 220, y2: 285 },
      },
      {
        plate_text: '51C-734.12',
        confidence: 0.89,
        bbox: { x1: 320, y1: 290, x2: 410, y2: 315 },
      },
    ],
    traffic_signs: [
      {
        sign_type: 'P.127: Tốc độ tối đa 60 km/h',
        speed_limit: 60,
      },
    ],
    helmet_violations: [
      {
        track_id: 42,
        plate_text: '29M1-234.56',
        bbox: { x1: 215, y1: 195, x2: 245, y2: 230 },
      },
    ],
    collision_warning: {
      level: 'danger',
      distance_estimate: 4.8,
      recommended_distance_m: 25.0,
      recommended_speed_kmh: 50,
    },
    speed_advice: {
      current_speed: 68,
      recommended_speed: 50,
      reason: 'Đoạn đường đông đúc & vượt biển 60 km/h',
    },
    processing_time_ms: 24,
  };

  const mockDriverResult: DriverMonitorResult = {
    frame_id: 1024,
    timestamp: Date.now(),
    drowsiness: {
      is_drowsy: false,
      available: true,
      face_detected: true,
      ear_value: 0.31,
      yawn_count: 0,
      alert_level: 'normal',
    },
    seatbelt: {
      seatbelt_on: true,
      confidence: 0.95,
    },
    driving_time: {
      continuous_minutes: 135,
      should_rest: false,
      message: 'Thời gian lái xe an toàn liên tục dưới 4 giờ',
    },
    processing_time_ms: 12,
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] py-8 px-4 sm:px-6 lg:px-8 select-none">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Navigation & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E4E9EF] pb-5">
          <div className="space-y-1">
            <Link
              href="/live"
              className="inline-flex items-center gap-1.5 text-xs font-bold text-[#175CD3] hover:underline"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Quay lại trang Giám sát trực tiếp (/live)</span>
            </Link>
            <h1 className="text-xl sm:text-2xl font-black text-[#16202A] flex items-center gap-2">
              Bảng Kiểm Thử Nghiệm Thu Thành Phần Giao Diện (UI Showcase)
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-[#EFF8FF] text-[#175CD3] border border-[#B2DDFF]">
                ENTERPRISE DESIGN SYSTEM
              </span>
            </h1>
            <p className="text-xs text-[#667085]">
              Môi trường kiểm thử độc lập cho từng thành phần giao diện TrafficGuard theo tiêu chuẩn Doanh nghiệp.
            </p>
          </div>
        </div>

        {/* ── 1. SYSTEM HEALTH BANNER ── */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-[#16202A] flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#175CD3]" />
              1. System Health Banner (Dải Trạng Thái & Sức Khỏe Toàn Trình)
            </h2>
            <div className="flex items-center gap-2 text-xs">
              <button
                onClick={() => setHealthSocketStatus('CONNECTED')}
                className={`px-2 py-1 rounded font-semibold ${
                  healthSocketStatus === 'CONNECTED' ? 'bg-[#067647] text-white' : 'bg-white border text-[#344054]'
                }`}
              >
                Online (10 FPS)
              </button>
              <button
                onClick={() => setHealthSocketStatus('CONNECTING')}
                className={`px-2 py-1 rounded font-semibold ${
                  healthSocketStatus === 'CONNECTING' ? 'bg-[#B54708] text-white' : 'bg-white border text-[#344054]'
                }`}
              >
                Reconnecting
              </button>
              <button
                onClick={() => setHealthSocketStatus('DISCONNECTED')}
                className={`px-2 py-1 rounded font-semibold ${
                  healthSocketStatus === 'DISCONNECTED' ? 'bg-[#B42318] text-white' : 'bg-white border text-[#344054]'
                }`}
              >
                Disconnected
              </button>
            </div>
          </div>
          <SystemHealthBanner
            roadStatus="online"
            cabinStatus="online"
            socketStatus={healthSocketStatus}
            processingTimeMs={healthProcessingMs}
          />
        </section>

        {/* ── 2. PRIORITY ALERT BAR ── */}
        <section className="space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h2 className="text-sm font-bold text-[#16202A] flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#F04438]" />
              2. Priority Alert Bar (Thanh Cảnh Báo An Toàn Quyết Định Ưu Tiên)
            </h2>
            <div className="flex items-center gap-2 text-xs">
              <button
                onClick={() => setAlertPriority('NORMAL')}
                className={`px-2 py-1 rounded font-semibold ${
                  alertPriority === 'NORMAL' ? 'bg-[#067647] text-white' : 'bg-white border text-[#344054]'
                }`}
              >
                Xanh (Bình thường)
              </button>
              <button
                onClick={() => setAlertPriority('COLLISION_CAUTION')}
                className={`px-2 py-1 rounded font-semibold ${
                  alertPriority === 'COLLISION_CAUTION' ? 'bg-[#B54708] text-white' : 'bg-white border text-[#344054]'
                }`}
              >
                Vàng (Cảnh báo)
              </button>
              <button
                onClick={() => setAlertPriority('COLLISION_DANGER')}
                className={`px-2 py-1 rounded font-semibold ${
                  alertPriority === 'COLLISION_DANGER' ? 'bg-[#B42318] text-white' : 'bg-white border text-[#344054]'
                }`}
              >
                Đỏ (Khẩn cấp va chạm)
              </button>
            </div>
          </div>
          <PriorityAlertBar
            priority={alertPriority}
            message={
              alertPriority === 'COLLISION_DANGER'
                ? 'NGUY CƠ VA CHẠM PHÍA TRƯỚC! GIẢM TỐC ĐỘ GẤP!'
                : alertPriority === 'COLLISION_CAUTION'
                ? 'Cảnh báo: Khoảng cách xe phía trước đang thu hẹp!'
                : 'Trạng thái an toàn. Tốc độ ổn định, giữ khoảng cách.'
            }
            isMuted={alertMuted}
            onToggleMute={() => setAlertMuted(!alertMuted)}
            safeDistance={alertPriority === 'COLLISION_DANGER' ? 4.8 : 28.5}
            recommendedSpeed={50}
          />
        </section>

        {/* ── 3. UNIFIED TELEMETRY STRIP ── */}
        <section className="space-y-3">
          <h2 className="text-sm font-bold text-[#16202A] flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#12B76A]" />
            3. Unified Telemetry Strip (Dải Telemetry Gộp 1 Hàng Ngang - Bước 2)
          </h2>
          <UnifiedTelemetryStrip
            currentSpeed={68}
            speedLimit={60}
            safeDistance={18.5}
            recommendedDistance={25.0}
            collisionLevel="warning"
            vehicleDensityCount={5}
            processingTimeMs={24}
            isStreaming={true}
          />
        </section>

        {/* ── 4. DETECTION TABS PANEL ── */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-[#16202A] flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#7A5AF8]" />
              4. Detection Tabs Panel (Khu Vực C: Biển Số, Biển Báo, Mũ Bảo Hiểm)
            </h2>
            <div className="flex items-center gap-2 text-xs">
              <button
                onClick={() => setActiveTab('plates')}
                className={`px-2 py-1 rounded font-semibold ${
                  activeTab === 'plates' ? 'bg-[#175CD3] text-white' : 'bg-white border text-[#344054]'
                }`}
              >
                Biển số [1]
              </button>
              <button
                onClick={() => setActiveTab('signs')}
                className={`px-2 py-1 rounded font-semibold ${
                  activeTab === 'signs' ? 'bg-[#F79009] text-white' : 'bg-white border text-[#344054]'
                }`}
              >
                Biển báo [2]
              </button>
              <button
                onClick={() => setActiveTab('helmets')}
                className={`px-2 py-1 rounded font-semibold ${
                  activeTab === 'helmets' ? 'bg-[#F04438] text-white' : 'bg-white border text-[#344054]'
                }`}
              >
                Mũ BH [3]
              </button>
            </div>
          </div>
          <DetectionTabsPanel
            plates={mockDetectionResult.plates}
            vehicles={mockDetectionResult.vehicles}
            signs={mockDetectionResult.traffic_signs}
            helmetViolations={mockDetectionResult.helmet_violations}
            isStreaming={true}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
        </section>

        {/* ── 5. CABIN CAMERA & REALTIME EVENT TIMELINE ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Cabin DMS */}
          <section className="space-y-3">
            <h2 className="text-sm font-bold text-[#16202A] flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#F79009]" />
              5. Cabin Camera Viewport (Khu Vực B: Tài Xế DMS & Nghị Định 10)
            </h2>
            <CabinCameraViewport
              videoRef={{ current: null }}
              driverResult={mockDriverResult}
              isStreaming={true}
              driverName="Nguyễn Văn An"
              driverId={1}
              driverPhone="0912 345 678"
              safetyScore={94}
              continuousMinutes={135}
            />
          </section>

          {/* Event Timeline */}
          <section className="space-y-3">
            <h2 className="text-sm font-bold text-[#16202A] flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#175CD3]" />
              6. Realtime Event Timeline (Khu Vực D: Luồng Sự Kiện Cho Quản Trị Viên)
            </h2>
            <RealtimeEventTimeline
              events={events}
              onConfirmEvent={(id) =>
                setEvents((prev) => prev.map((e) => (e.id === id ? { ...e, status: 'confirmed' } : e)))
              }
              onRejectEvent={(id) =>
                setEvents((prev) => prev.map((e) => (e.id === id ? { ...e, status: 'rejected' } : e)))
              }
            />
          </section>
        </div>

        {/* ── 6. TECHNICAL AI DIAGNOSTICS ── */}
        <section className="space-y-3">
          <h2 className="text-sm font-bold text-[#16202A] flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#067647]" />
            7. AI Technical Diagnostics Panel (Bảng Chẩn Đoán Kỹ Thuật Độ Trễ)
          </h2>
          <AIDiagnosticsPanel
            detectionResult={mockDetectionResult}
            processingTimeMs={24}
            isStreaming={true}
            socketStatus="CONNECTED"
          />
        </section>
      </div>
    </div>
  );
}
