'use client';

import React, { memo, useState, useRef } from 'react';
import {
  Video,
  Cpu,
  Radio,
  Maximize2,
  Upload,
  Play,
  Pause,
  Film,
  Layers,
  Eye,
  EyeOff,
  Camera,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { DetectionCanvas } from '../driving/DetectionCanvas';
import { DetectionResult, isValidConfirmedPlate } from '../../types/detection';

import { TGButton } from '../ui/TGButton';
import { ZoneStatus, TrackedVehicle } from '../../hooks/useTrafficDistanceEngine';

export interface RoadCameraViewportProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  videoSrc?: string | null;
  videoFileName?: string;
  detectionResult: DetectionResult | null;
  isStreaming: boolean;
  isPaused?: boolean;
  isScanningFrame?: boolean;
  hasCollisionWarning: boolean;
  collisionLevel?: 'none' | 'warning' | 'danger';
  speedLimit?: number | null;
  currentSpeed?: number | null;
  processingTimeMs?: number | null;
  sourceMode?: 'video' | 'webcam' | 'image';
  activeTab?: 'plates' | 'traffic' | 'signs' | 'helmets';
  zoneLeft?: ZoneStatus;
  zoneFront?: ZoneStatus;
  zoneRight?: ZoneStatus;
  alertBanner?: { text: string; lvl: 1 | 2 } | null;
  warnThreshold?: number;
  dangerThreshold?: number;
  focalLength?: number;
  showDistanceZones?: boolean;
  trackedVehicles?: TrackedVehicle[];
  onFullscreen?: () => void;
  onUploadClick?: () => void;
  onSelectSample?: (url: string, name: string) => void;
  onStartStreaming?: () => void;
  onUseWebcam?: () => void;
  onResume?: () => void;
  onScanCurrentFrame?: () => void;
  onPauseAndScan?: () => void;
  onManualSelectPlateRoi?: (cropBlob: Blob, displayBbox: { x1: number; y1: number; x2: number; y2: number }) => Promise<any>;
  onManualSelectSignRoi?: (cropBlob: Blob, displayBbox: { x1: number; y1: number; x2: number; y2: number }) => Promise<any>;
}

export const RoadCameraViewport = memo(function RoadCameraViewport({
  videoRef,
  videoSrc,
  videoFileName,
  detectionResult,
  isStreaming,
  isPaused = false,
  isScanningFrame = false,
  hasCollisionWarning,
  collisionLevel = 'none',
  speedLimit = null,
  currentSpeed = null,
  processingTimeMs = null,
  sourceMode = 'video',
  activeTab,
  zoneLeft,
  zoneFront,
  zoneRight,
  alertBanner,
  warnThreshold = 8,
  dangerThreshold = 4,
  focalLength = 520,
  showDistanceZones = true,
  trackedVehicles = [],
  onFullscreen,
  onUploadClick,
  onSelectSample,
  onStartStreaming,
  onUseWebcam,
  onResume,
  onScanCurrentFrame,
  onPauseAndScan,
  onManualSelectPlateRoi,
  onManualSelectSignRoi,
}: RoadCameraViewportProps) {
  const [showBoxes, setShowBoxes] = useState(true);
  const [showLanes, setShowLanes] = useState(true);
  const [showDistance, setShowDistance] = useState(true);
  const [showLayerMenu, setShowLayerMenu] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  // Vùng chọn thủ công biển số xe / biển báo (Manual ROI) khi dừng video hoặc ảnh tĩnh
  const isManualRoiActive = (isPaused || sourceMode === 'image') && (activeTab === 'plates' || activeTab === 'signs');
  const [selection, setSelection] = useState<{ startX: number; startY: number; currentX: number; currentY: number } | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const [manualScanStatus, setManualScanStatus] = useState<{
    state: 'idle' | 'scanning' | 'success' | 'failed';
    message?: string;
    box?: { x: number; y: number; w: number; h: number };
  }>({ state: 'idle' });

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isManualRoiActive) return;
    if (e.button !== 0) return;
    if (!containerRef.current) return;

    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setIsSelecting(true);
    setSelection({ startX: x, startY: y, currentX: x, currentY: y });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isSelecting || !selection || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    const y = Math.max(0, Math.min(rect.height, e.clientY - rect.top));
    setSelection(prev => prev ? { ...prev, currentX: x, currentY: y } : null);
  };

  const handleMouseUp = async () => {
    if (!isSelecting || !selection || !containerRef.current) {
      setIsSelecting(false);
      return;
    }

    setIsSelecting(false);

    const media = (sourceMode === 'image' ? imageRef.current : videoRef.current) as (HTMLVideoElement | HTMLImageElement | null);
    if (!media) {
      setSelection(null);
      return;
    }

    const mWidth = (media as HTMLVideoElement).videoWidth || (media as HTMLImageElement).naturalWidth || detectionResult?.frame_width || 1280;
    const mHeight = (media as HTMLVideoElement).videoHeight || (media as HTMLImageElement).naturalHeight || detectionResult?.frame_height || 720;
    if (!mWidth || !mHeight) {
      setSelection(null);
      return;
    }

    const containerRect = containerRef.current.getBoundingClientRect();
    const videoRatio = mWidth / mHeight;
    const elementRatio = containerRect.width / (containerRect.height || 1);

    let renderWidth = containerRect.width;
    let renderHeight = containerRect.height;
    let offsetX = 0;
    let offsetY = 0;

    if (elementRatio > videoRatio) {
      renderWidth = containerRect.height * videoRatio;
      offsetX = (containerRect.width - renderWidth) / 2;
    } else {
      renderHeight = containerRect.width / videoRatio;
      offsetY = (containerRect.height - renderHeight) / 2;
    }

    const toNative = (screenX: number, screenY: number) => {
      const rx = Math.max(0, Math.min(renderWidth, screenX - offsetX));
      const ry = Math.max(0, Math.min(renderHeight, screenY - offsetY));
      return {
        x: Math.max(0, Math.min(mWidth, Math.round((rx / renderWidth) * mWidth))),
        y: Math.max(0, Math.min(mHeight, Math.round((ry / renderHeight) * mHeight))),
      };
    };

    const toScreen = (nativeX: number, nativeY: number) => {
      return {
        x: offsetX + (nativeX / mWidth) * renderWidth,
        y: offsetY + (nativeY / mHeight) * renderHeight,
      };
    };

    const selX1 = Math.min(selection.startX, selection.currentX);
    const selY1 = Math.min(selection.startY, selection.currentY);
    const selX2 = Math.max(selection.startX, selection.currentX);
    const selY2 = Math.max(selection.startY, selection.currentY);
    const dragW = selX2 - selX1;
    const dragH = selY2 - selY1;

    setSelection(null);

    let vx1 = 0;
    let vy1 = 0;
    let vx2 = 0;
    let vy2 = 0;

    if (dragW < 12 || dragH < 10) {
      // Người dùng CLICK ĐIỂM trên biển số / biển báo: Tạo vùng ROI thông minh quanh điểm click
      const clickPoint = toNative(selX1, selY1);
      const isSignTab = activeTab === 'signs';
      const autoBoxW = isSignTab ? Math.round(mWidth * 0.14) : Math.round(mWidth * 0.18);
      const autoBoxH = isSignTab ? Math.round(mWidth * 0.14) : Math.round(mHeight * 0.12);
      vx1 = Math.max(0, Math.round(clickPoint.x - autoBoxW / 2));
      vy1 = Math.max(0, Math.round(clickPoint.y - autoBoxH / 2));
      vx2 = Math.min(mWidth, vx1 + autoBoxW);
      vy2 = Math.min(mHeight, vy1 + autoBoxH);
    } else {
      // Người dùng KÉO KHOANH VÙNG chữ nhật:
      const p1 = toNative(selX1, selY1);
      const p2 = toNative(selX2, selY2);
      const rawW = p2.x - p1.x;
      const rawH = p2.y - p1.y;
      const padX = Math.round(rawW * 0.05);
      const padY = Math.round(rawH * 0.05);
      vx1 = Math.max(0, p1.x - padX);
      vy1 = Math.max(0, p1.y - padY);
      vx2 = Math.min(mWidth, p2.x + padX);
      vy2 = Math.min(mHeight, p2.y + padY);
    }

    const cropW = vx2 - vx1;
    const cropH = vy2 - vy1;
    if (cropW < 20 || cropH < 12) return;

    // Hiển thị khung chờ quét trực quan ngay trên màn hình
    const scrP1 = toScreen(vx1, vy1);
    const scrP2 = toScreen(vx2, vy2);
    setManualScanStatus({
      state: 'scanning',
      message: activeTab === 'signs' ? 'Đang nhận diện biển báo...' : 'Đang đọc biển số...',
      box: {
        x: scrP1.x,
        y: scrP1.y,
        w: scrP2.x - scrP1.x,
        h: scrP2.y - scrP1.y,
      },
    });

    try {
      const canvas = document.createElement('canvas');
      canvas.width = cropW;
      canvas.height = cropH;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        setManualScanStatus({ state: 'idle' });
        return;
      }
      ctx.drawImage(media, vx1, vy1, cropW, cropH, 0, 0, cropW, cropH);

      canvas.toBlob(async (blob) => {
        if (!blob) {
          setManualScanStatus({ state: 'idle' });
          return;
        }

        if (activeTab === 'signs') {
          if (onManualSelectSignRoi) {
            try {
              const detected = await onManualSelectSignRoi(blob, { x1: vx1, y1: vy1, x2: vx2, y2: vy2 });
              if (detected && detected.sign_type) {
                setManualScanStatus({
                  state: 'success',
                  message: `Biển báo: ${detected.name || detected.sign_type}`,
                  box: {
                    x: scrP1.x,
                    y: scrP1.y,
                    w: scrP2.x - scrP1.x,
                    h: scrP2.y - scrP1.y,
                  },
                });
                setTimeout(() => {
                  setManualScanStatus((curr) => curr.state === 'success' ? { state: 'idle' } : curr);
                }, 4000);
              } else {
                setManualScanStatus({
                  state: 'failed',
                  message: 'Không nhận diện được biển báo. Vui lòng khoanh sát hơn',
                  box: {
                    x: scrP1.x,
                    y: scrP1.y,
                    w: scrP2.x - scrP1.x,
                    h: scrP2.y - scrP1.y,
                  },
                });
                setTimeout(() => {
                  setManualScanStatus((curr) => curr.state === 'failed' ? { state: 'idle' } : curr);
                }, 3500);
              }
            } catch (err) {
              setManualScanStatus({
                state: 'failed',
                message: 'Lỗi nhận diện biển báo',
              });
              setTimeout(() => {
                setManualScanStatus({ state: 'idle' });
              }, 3000);
            }
          }
        } else if (onManualSelectPlateRoi) {
          try {
            const detected = await onManualSelectPlateRoi(blob, { x1: vx1, y1: vy1, x2: vx2, y2: vy2 });
            if (detected && detected.plate_text) {
              setManualScanStatus({
                state: 'success',
                message: `Đã nhận diện: ${detected.plate_text}`,
                box: {
                  x: scrP1.x,
                  y: scrP1.y,
                  w: scrP2.x - scrP1.x,
                  h: scrP2.y - scrP1.y,
                },
              });
              setTimeout(() => {
                setManualScanStatus((curr) => curr.state === 'success' ? { state: 'idle' } : curr);
              }, 4000);
            } else {
              setManualScanStatus({
                state: 'failed',
                message: 'Không tìm thấy biển số. Vui lòng khoanh sát hơn',
                box: {
                  x: scrP1.x,
                  y: scrP1.y,
                  w: scrP2.x - scrP1.x,
                  h: scrP2.y - scrP1.y,
                },
              });
              setTimeout(() => {
                setManualScanStatus((curr) => curr.state === 'failed' ? { state: 'idle' } : curr);
              }, 3500);
            }
          } catch (err) {
            setManualScanStatus({
              state: 'failed',
              message: 'Lỗi kết nối OCR',
            });
            setTimeout(() => {
              setManualScanStatus({ state: 'idle' });
            }, 3000);
          }
        }
      }, 'image/jpeg', 0.92);
    } catch (err) {
      console.warn('Manual crop failed:', err);
      setManualScanStatus({ state: 'idle' });
    }
  };

  const isCritical = collisionLevel === 'danger';
  const isWarning = collisionLevel === 'warning';

  const detectedVehiclesCount = detectionResult?.vehicles?.length || trackedVehicles?.length || 0;
  const detectedSigns = detectionResult?.traffic_signs || [];

  const isTrafficTab = activeTab === 'traffic';
  const hasMedia = !!videoSrc || sourceMode === 'image';
  const densityStatus = detectedVehiclesCount > 5 ? 'Đông đúc' : detectedVehiclesCount > 2 ? 'Bình thường' : 'Thông thoáng';
  const leadDist = zoneFront?.dist ?? (detectionResult?.collision_warning?.distance_estimate ?? null);

  return (
    <div className="relative w-full rounded-[10px] overflow-hidden bg-[#0C111D] border border-white/10 shadow-md flex flex-col">
      {/* ── 1. MAIN CAMERA VIEWPORT (OPTIMIZED BALANCED SIZING) ── */}
      <div
        ref={containerRef}
        className={`relative w-full aspect-[16/9.2] min-h-[300px] sm:min-h-[360px] lg:min-h-[400px] xl:min-h-[450px] 2xl:min-h-[490px] max-h-[520px] bg-[#0A0D14] overflow-hidden flex items-center justify-center ${
          isManualRoiActive ? 'cursor-crosshair select-none' : ''
        }`}
      >
      {/* Video or Image Element */}
      {sourceMode === 'image' ? (
        <img
          ref={imageRef}
          src={videoSrc || undefined}
          alt="Road Snapshot"
          className="w-full h-full object-contain bg-[#0A0D14]"
        />
      ) : (
        <video
          ref={videoRef}
          src={videoSrc || undefined}
          playsInline
          muted
          loop
          onClick={() => {
            if (isStreaming && onPauseAndScan) {
              onPauseAndScan();
            } else if (isPaused && onResume) {
              // Ở chế độ biển số / biển báo khi dừng video: ưu tiên click để chọn ROI thủ công, không tự resume
              if (activeTab !== 'plates' && activeTab !== 'signs') {
                onResume();
              }
            }
          }}
          className={`w-full h-full object-contain bg-[#0A0D14] ${isManualRoiActive ? 'cursor-crosshair' : 'cursor-pointer'}`}
          title={isStreaming ? "Nhấp chuột để tạm dừng & quét" : isPaused ? (isManualRoiActive ? (activeTab === 'signs' ? "Kéo khoanh vùng hoặc nhấp để chọn biển báo" : "Kéo khoanh vùng hoặc nhấp để chọn biển số") : "Nhấp chuột để tiếp tục phát") : undefined}
        />
      )}

      {/* AI Bounding Box Canvas Overlay */}
      <DetectionCanvas
        result={detectionResult}
        videoRef={videoRef}
        mediaRef={sourceMode === 'image' ? imageRef : videoRef}
        showBoxes={(isStreaming || isPaused || sourceMode === 'image') && showBoxes}
        activeTab={activeTab}
        sourceMode={sourceMode}
        showDistanceZones={showLanes && showDistance}
        warnThreshold={warnThreshold}
        dangerThreshold={dangerThreshold}
        focalLength={focalLength}
        zoneLeft={zoneLeft}
        zoneFront={zoneFront}
        zoneRight={zoneRight}
        trackedVehicles={trackedVehicles}
        className="absolute inset-0 pointer-events-none"
      />

      {/* ── PERIPHERAL VISION EDGE GLOW OVERLAYS TRÊN VIDEO (CẢNH BÁO XE ÁP SÁT 2 BÊN & PHÍA TRƯỚC) ── */}
      {hasMedia && showDistance && isTrafficTab && (
        <>
          {/* Vùng Trái: Cảnh báo xe áp sát bên trái */}
          <div
            className={`absolute left-0 top-0 bottom-0 w-[14%] sm:w-[12%] pointer-events-none transition-opacity duration-150 z-20 ${
              zoneLeft?.lvl === 2
                ? 'opacity-100 bg-gradient-to-r from-[rgba(239,68,68,0.75)] to-transparent animate-pulse'
                : zoneLeft?.lvl === 1
                ? 'opacity-85 bg-gradient-to-r from-[rgba(245,158,11,0.55)] to-transparent'
                : 'opacity-0'
            }`}
          />
          {/* Phía Trước: Cảnh báo xe phía trước quá gần */}
          <div
            className={`absolute left-0 right-0 top-0 h-[14%] sm:h-[12%] pointer-events-none transition-opacity duration-150 z-20 ${
              zoneFront?.lvl === 2
                ? 'opacity-100 bg-gradient-to-b from-[rgba(239,68,68,0.75)] to-transparent animate-pulse'
                : zoneFront?.lvl === 1
                ? 'opacity-85 bg-gradient-to-b from-[rgba(245,158,11,0.55)] to-transparent'
                : 'opacity-0'
            }`}
          />
          {/* Vùng Phải: Cảnh báo xe áp sát bên phải */}
          <div
            className={`absolute right-0 top-0 bottom-0 w-[14%] sm:w-[12%] pointer-events-none transition-opacity duration-150 z-20 ${
              zoneRight?.lvl === 2
                ? 'opacity-100 bg-gradient-to-l from-[rgba(239,68,68,0.75)] to-transparent animate-pulse'
                : zoneRight?.lvl === 1
                ? 'opacity-85 bg-gradient-to-l from-[rgba(245,158,11,0.55)] to-transparent'
                : 'opacity-0'
            }`}
          />
        </>
      )}

      {/* ── 3-ZONE LIVE ADAS HUD OVERLAY & THẺ MẬT ĐỘ / CỰ LY XE (CHỈ HIỂN THỊ KHI Ở CHẾ ĐỘ MẬT ĐỘ & CỰ LY XE) ── */}
      {hasMedia && showDistance && isTrafficTab && (isStreaming || isPaused || sourceMode === 'image') && (
        <div className="absolute top-12 sm:top-14 left-1/2 -translate-x-1/2 z-30 pointer-events-auto select-none max-w-[96%] w-auto animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex flex-col items-center gap-1.5 px-3 py-1.5 rounded-[12px] bg-[#0C111D]/90 backdrop-blur-xl border border-white/20 shadow-[0_8px_32px_rgba(0,0,0,0.6)] text-white">
            
            {/* HÀNG 1: THẺ MẬT ĐỘ GIAO THÔNG VÀ CỰ LY XE PHÍA TRƯỚC */}
            <div className="flex items-center justify-between w-full gap-4 pb-1 border-b border-white/15 text-[11px] font-mono">
              <div className="flex items-center gap-1.5">
                <span>🚗</span>
                <span className="text-white/70 font-semibold text-[10px] uppercase tracking-wider">Mật độ:</span>
                <span
                  className={`px-1.5 py-0.2 rounded text-[10px] font-bold border ${
                    detectedVehiclesCount > 5
                      ? 'bg-red-500/80 text-white border-red-400'
                      : detectedVehiclesCount > 2
                      ? 'bg-amber-500/80 text-white border-amber-400'
                      : 'bg-emerald-500/80 text-white border-emerald-400'
                  }`}
                >
                  {densityStatus} ({detectedVehiclesCount} xe)
                </span>
              </div>

              <div className="flex items-center gap-1.5">
                <span className="text-white/70 font-semibold text-[10px] uppercase tracking-wider">Xe trước:</span>
                <span
                  className={`font-black text-xs ${
                    zoneFront?.lvl === 2 ? 'text-red-400' : zoneFront?.lvl === 1 ? 'text-amber-400' : 'text-emerald-400'
                  }`}
                >
                  {leadDist ? `${leadDist.toFixed(1)}m` : 'Thông thoáng'}
                </span>
                {leadDist && (
                  <span
                    className={`text-[9px] font-extrabold px-1 rounded ${
                      zoneFront?.lvl === 2
                        ? 'bg-red-600 text-white animate-pulse'
                        : zoneFront?.lvl === 1
                        ? 'bg-amber-600 text-white'
                        : 'bg-emerald-600 text-white'
                    }`}
                  >
                    {zoneFront?.lvl === 2 ? '🚨 NGUY HIỂM' : zoneFront?.lvl === 1 ? '⚠ CẬN AN TOÀN' : '✓ AN TOÀN'}
                  </span>
                )}
              </div>
            </div>

            {/* HÀNG 2: 3 VÙNG CỰ LY ADAS (VÙNG TRÁI • PHÍA TRƯỚC • VÙNG PHẢI) */}
            <div className="flex items-center gap-1 sm:gap-2">
              {/* 1. VÙNG TRÁI */}
              <div
                className={`flex items-center gap-1.5 sm:gap-2 px-2.5 py-1 rounded-[8px] border transition-all ${
                  zoneLeft?.lvl === 2
                    ? 'bg-red-950/85 border-red-500 text-red-100 shadow-[0_0_12px_rgba(239,68,68,0.5)] animate-pulse'
                    : zoneLeft?.lvl === 1
                    ? 'bg-amber-950/75 border-amber-500 text-amber-100 shadow-[0_0_8px_rgba(245,158,11,0.3)]'
                    : 'bg-emerald-950/45 border-emerald-500/40 text-emerald-200'
                }`}
              >
                <span className="text-sm sm:text-base font-bold">⬅</span>
                <div className="flex flex-col text-left">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-white/70 leading-tight">
                    Vùng trái
                  </span>
                  <div className="flex items-baseline gap-1 mt-0.5">
                    <span className="text-xs sm:text-sm font-extrabold font-mono text-white leading-none">
                      {zoneLeft?.dist ? `${zoneLeft.dist.toFixed(1)}m` : 'An toàn'}
                    </span>
                    {zoneLeft?.lvl === 2 ? (
                      <span className="text-[9px] font-black px-1 rounded bg-red-600 text-white animate-bounce">
                        NGUY HIỂM
                      </span>
                    ) : zoneLeft?.lvl === 1 ? (
                      <span className="text-[9px] font-bold px-1 rounded bg-amber-600 text-white">
                        CHÚ Ý
                      </span>
                    ) : null}
                  </div>
                </div>
              </div>

              {/* PHÂN CÁCH TRÁI - TRƯỚC */}
              <div className="w-px h-6 bg-white/20 hidden sm:block" />

              {/* 2. PHÍA TRƯỚC */}
              <div
                className={`flex items-center gap-2 px-3 py-1 rounded-[8px] border transition-all ${
                  zoneFront?.lvl === 2
                    ? 'bg-red-950/90 border-red-500 text-red-50 shadow-[0_0_20px_rgba(239,68,68,0.6)] animate-pulse ring-2 ring-red-500/50'
                    : zoneFront?.lvl === 1
                    ? 'bg-amber-950/80 border-amber-500 text-amber-50 shadow-[0_0_12px_rgba(245,158,11,0.4)]'
                    : 'bg-emerald-950/55 border-emerald-500/50 text-emerald-100'
                }`}
              >
                <div className="flex flex-col items-center sm:items-start min-w-[95px] sm:min-w-[120px]">
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-white/80">▲</span>
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-white/80 leading-tight">
                      Phía trước
                    </span>
                  </div>
                  <div className="flex items-baseline gap-1.5 mt-0.5">
                    <span className="text-sm sm:text-base font-black font-mono tracking-tight text-white leading-none">
                      {zoneFront?.dist ? `${zoneFront.dist.toFixed(1)}m` : 'An toàn'}
                    </span>
                    {zoneFront?.lvl === 2 ? (
                      <span className="text-[10px] font-black px-1.5 py-0.5 rounded bg-red-600 text-white animate-bounce shadow-md">
                        🚨 PHANH GẤP
                      </span>
                    ) : zoneFront?.lvl === 1 ? (
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-600 text-white animate-pulse">
                        ⚠ CẬN AN TOÀN
                      </span>
                    ) : (
                      <span className="text-[10px] font-semibold text-emerald-400">
                        ✓ An toàn
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* PHÂN CÁCH TRƯỚC - PHẢI */}
              <div className="w-px h-6 bg-white/20 hidden sm:block" />

              {/* 3. VÙNG PHẢI */}
              <div
                className={`flex items-center gap-1.5 sm:gap-2 px-2.5 py-1 rounded-[8px] border transition-all ${
                  zoneRight?.lvl === 2
                    ? 'bg-red-950/85 border-red-500 text-red-100 shadow-[0_0_12px_rgba(239,68,68,0.5)] animate-pulse'
                    : zoneRight?.lvl === 1
                    ? 'bg-amber-950/75 border-amber-500 text-amber-100 shadow-[0_0_8px_rgba(245,158,11,0.3)]'
                    : 'bg-emerald-950/45 border-emerald-500/40 text-emerald-200'
                }`}
              >
                <div className="flex flex-col text-right">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-white/70 leading-tight">
                    Vùng phải
                  </span>
                  <div className="flex items-baseline justify-end gap-1 mt-0.5">
                    {zoneRight?.lvl === 2 ? (
                      <span className="text-[9px] font-black px-1 rounded bg-red-600 text-white animate-bounce">
                        NGUY HIỂM
                      </span>
                    ) : zoneRight?.lvl === 1 ? (
                      <span className="text-[9px] font-bold px-1 rounded bg-amber-600 text-white">
                        CHÚ Ý
                      </span>
                    ) : null}
                    <span className="text-xs sm:text-sm font-extrabold font-mono text-white leading-none">
                      {zoneRight?.dist ? `${zoneRight.dist.toFixed(1)}m` : 'An toàn'}
                    </span>
                  </div>
                </div>
                <span className="text-sm sm:text-base font-bold">➡</span>
              </div>
            </div>

          </div>
        </div>
      )}

      {/* ── CẢNH BÁO KHOẢNG CÁCH NỔI TRÊN VIDEO KHI CÓ BANNER ── */}
      {isTrafficTab && (isStreaming || isPaused) && videoSrc && alertBanner ? (
        <div
          className={`absolute left-1/2 top-24 sm:top-28 -translate-x-1/2 px-4 py-1.5 rounded-[8px] font-bold text-xs sm:text-sm text-white shadow-2xl z-40 whitespace-nowrap pointer-events-none transition-all duration-150 flex items-center gap-2 ${
            alertBanner.lvl === 2
              ? 'bg-[#B91C1C] border border-red-400 animate-pulse'
              : 'bg-[#B45309] border border-amber-400'
          }`}
        >
          {alertBanner.text}
        </div>
      ) : null}

      {/* ── TOP HUD OVERLAYS ── */}
      <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none select-none z-30">
        {/* Top-Left: AI Diagnostics HUD */}
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-[6px] bg-[#0C111D]/85 backdrop-blur-md border border-white/10 text-white text-[11px] font-mono shadow-sm">
          <Cpu className="w-3.5 h-3.5 text-[#3B82F6]" />
          <span>YOLOv8 Nano</span>
          <span className="text-white/30">•</span>
          <span className="text-[#10B981] font-semibold">
            {processingTimeMs !== null && processingTimeMs !== undefined ? `${processingTimeMs.toFixed(1)}ms` : '—'}
          </span>
          <span className="text-white/30">•</span>
          <span>{sourceMode === 'image' ? 'Ảnh Tĩnh (Đã Quét)' : isStreaming ? 'AI Active' : isPaused ? 'Đã tạm dừng' : 'Chờ phân tích'}</span>
          <span className="text-white/30">•</span>
          <span className="text-white/80">
            {activeTab === 'signs'
              ? `${detectedSigns.length} biển báo phát hiện`
              : activeTab === 'plates'
              ? `${detectionResult?.plates?.length || 0} biển số phát hiện`
              : activeTab === 'helmets'
              ? `${detectionResult?.helmet_violations?.length || 0} vi phạm mũ BH`
              : `${detectedVehiclesCount} xe phát hiện`}
          </span>
        </div>

        {/* Top-Right: Layer Toggles, Pause & Scan, Live Indicator & Fullscreen */}
        <div className="flex items-center gap-2 pointer-events-auto">
          {/* Pause & Scan Frame Quick Button (CHỈ HIỆN KHI PHÁT VIDEO, KHÔNG HIỆN TRÊN ẢNH TĨNH) */}
          {sourceMode !== 'image' && isStreaming && onPauseAndScan && (
            <button
              onClick={onPauseAndScan}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] bg-[#175CD3]/90 hover:bg-[#175CD3] backdrop-blur-md border border-[#53B1FD]/40 text-white text-xs font-semibold shadow-md transition-all cursor-pointer hover:scale-102"
              title="Tạm dừng video và quét chuyên sâu trên khung hình này"
            >
              <Pause className="w-3.5 h-3.5" />
              <span>Tạm dừng & Quét</span>
            </button>
          )}

          {/* Layer Selector Pill */}
          <div className="relative">
            <button
              onClick={() => setShowLayerMenu(!showLayerMenu)}
              className="flex items-center gap-1.5 px-2 py-1 rounded-[6px] bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/10 text-white/80 text-xs transition-colors cursor-pointer"
              title="Bật/tắt các lớp hiển thị overlay"
            >
              <Layers className="w-3.5 h-3.5 text-[#53B1FD]" />
              <span className="hidden sm:inline">Lớp AI</span>
            </button>

            {showLayerMenu && (
              <div className="absolute right-0 top-8 w-44 bg-[#0C111D]/95 backdrop-blur-md border border-white/15 rounded-[8px] p-2 text-xs text-white shadow-xl z-20 space-y-1.5 animate-in fade-in zoom-in-95">
                <div className="text-[10px] uppercase font-bold text-white/50 px-1 pb-1 border-b border-white/10">
                  Lớp Hiển Thị Overlay
                </div>
                <label className="flex items-center justify-between px-1 py-0.5 hover:bg-white/10 rounded cursor-pointer">
                  <span>Bounding Box</span>
                  <input
                    type="checkbox"
                    checked={showBoxes}
                    onChange={(e) => setShowBoxes(e.target.checked)}
                    className="rounded accent-[#175CD3]"
                  />
                </label>
                <label className="flex items-center justify-between px-1 py-0.5 hover:bg-white/10 rounded cursor-pointer">
                  <span>Vạch làn đường</span>
                  <input
                    type="checkbox"
                    checked={showLanes}
                    onChange={(e) => setShowLanes(e.target.checked)}
                    className="rounded accent-[#175CD3]"
                  />
                </label>
                <label className="flex items-center justify-between px-1 py-0.5 hover:bg-white/10 rounded cursor-pointer">
                  <span>3 Vùng Cự Ly (HUD)</span>
                  <input
                    type="checkbox"
                    checked={showDistance}
                    onChange={(e) => setShowDistance(e.target.checked)}
                    className="rounded accent-[#175CD3]"
                  />
                </label>
              </div>
            )}
          </div>

          {/* Live / Paused / Image Indicator Badge */}
          {sourceMode === 'image' ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] bg-[#ECFDF3]/90 backdrop-blur-md border border-[#A6F4C5] text-[#027A48] text-xs font-bold shadow-sm">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#12B76A]" />
              <span>ẢNH TĨNH</span>
            </div>
          ) : isStreaming ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] bg-[#FEF3F2]/90 backdrop-blur-md border border-[#FECDCA] text-[#B42318] text-xs font-bold shadow-sm">
              <span className="w-2 h-2 rounded-full bg-[#F04438] animate-ping" />
              <span>TRỰC TIẾP</span>
            </div>
          ) : isPaused ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] bg-[#FEF0C7]/90 backdrop-blur-md border border-[#FEDF89] text-[#B54708] text-xs font-bold shadow-sm">
              <span className="w-2 h-2 rounded-full bg-[#F79009]" />
              <span>TẠM DỪNG</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] bg-black/60 backdrop-blur-md border border-white/10 text-white/70 text-xs">
              <Radio className="w-3.5 h-3.5" />
              <span>{videoSrc ? 'ĐÃ NẠP' : 'SẴN SÀNG'}</span>
            </div>
          )}

          {onFullscreen && (
            <button
              onClick={onFullscreen}
              className="p-1.5 rounded-[6px] bg-black/60 hover:bg-black/80 text-white/80 border border-white/10 transition-colors cursor-pointer"
              aria-label="Toàn màn hình"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* ── BOTTOM HUD OVERLAYS ── */}
      <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between pointer-events-none select-none">
        {/* Bottom-Left: Traffic Sign Indicator */}
        <div className="flex items-center gap-2">
          {activeTab !== 'plates' && speedLimit !== null && speedLimit !== undefined && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-[8px] bg-white/95 backdrop-blur-md border border-[#E4E9EF] shadow-lg text-[#16202A]">
              <div className="w-6 h-6 rounded-full border-2 border-[#F04438] bg-white flex items-center justify-center font-bold text-[11px] text-[#16202A]">
                {speedLimit}
              </div>
              <div className="text-xs">
                <span className="block font-bold text-[#16202A]">Tốc Độ Tối Đa</span>
                <span className="block text-[10px] text-[#667085]">Biển báo phát hiện</span>
              </div>
            </div>
          )}
        </div>

        {/* Bottom-Right: Ego Vehicle Speedometer HUD */}
        {sourceMode !== 'image' && activeTab !== 'plates' && activeTab !== 'signs' && currentSpeed !== null && currentSpeed !== undefined && (
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-[8px] bg-[#0C111D]/85 backdrop-blur-md border border-white/10 text-white shadow-lg">
            <div>
              <span className="text-[10px] uppercase text-white/60 block leading-none">
                Tốc Độ Đo Được
              </span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="text-2xl font-black tracking-tight text-white font-mono tabular-nums">
                  {Math.round(currentSpeed)}
                </span>
                <span className="text-[11px] text-white/70">km/h</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── INTERACTIVE EMPTY / OFFLINE OVERLAY ── */}
      {!videoSrc && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#0C111D]/90 backdrop-blur-sm text-white select-none p-6 text-center z-10">
          <div className="w-12 h-12 rounded-[12px] bg-[#175CD3]/10 border border-[#175CD3]/30 flex items-center justify-center text-[#53B1FD] mb-3">
            <Video className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold tracking-tight text-white">Chưa Có Luồng Video Đường Lộ</h3>
          <p className="text-xs text-white/70 max-w-md mt-1 mb-5 leading-relaxed">
            Hệ thống ADAS cần luồng video camera phía trước để nhận diện phương tiện, đo khoảng cách an toàn và đọc biển báo giao thông.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            {onUploadClick && (
              <TGButton
                variant="primary"
                size="md"
                onClick={onUploadClick}
                leftIcon={<Upload className="w-4 h-4" />}
                className="text-xs sm:text-sm font-semibold cursor-pointer bg-[#175CD3] hover:bg-[#154fc1] border-none text-white px-5 py-2.5 shadow-lg shadow-[#175CD3]/20"
              >
                Tải video / hình ảnh từ máy tính
              </TGButton>
            )}

            {onUseWebcam && (
              <TGButton
                variant="secondary"
                size="md"
                onClick={onUseWebcam}
                leftIcon={<Camera className="w-4 h-4" />}
                className="text-xs sm:text-sm font-semibold cursor-pointer bg-white/10 hover:bg-white/20 border-white/20 text-white px-4 py-2.5"
              >
                Dùng webcam / camera xe
              </TGButton>
            )}
          </div>
        </div>
      )}

      {/* Screen when video is loaded but stream is NOT started (only when idle or ended, KHÔNG HIỆN TRÊN ẢNH) */}
      {videoSrc && sourceMode !== 'image' && !isStreaming && !isPaused && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#0C111D]/70 backdrop-blur-[2px] text-white select-none p-6 text-center z-10 pointer-events-auto">
          <div className="px-4 py-3 rounded-[10px] bg-[#0C111D]/90 border border-white/15 max-w-sm w-full space-y-3 shadow-2xl">
            <div className="flex items-center justify-center gap-2 text-xs text-[#53B1FD] font-semibold">
              <Film className="w-4 h-4" />
              <span className="truncate max-w-[260px]">{videoFileName || 'Đã sẵn sàng phân tích'}</span>
            </div>
            <p className="text-[11px] text-white/70">
              Video đã sẵn sàng. Nhấn nút bên dưới để mở luồng xử lý AI nhận diện xe máy, ô tô và khoảng cách an toàn.
            </p>
            {onStartStreaming && (
              <TGButton
                variant="primary"
                size="sm"
                onClick={onStartStreaming}
                leftIcon={<Play className="w-3.5 h-3.5 fill-current" />}
                className="w-full text-xs font-bold justify-center cursor-pointer"
              >
                Bắt đầu phân tích AI
              </TGButton>
            )}
          </div>
        </div>
      )}

      {/* ── MANUAL PLATE ROI INTERACTION LAYER (DRAG & CLICK SELECTION WHEN PAUSED / IMAGE) ── */}
      {isManualRoiActive && (
        <div
          className="absolute inset-0 z-20 cursor-crosshair select-none"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={() => {
            if (isSelecting) {
              setIsSelecting(false);
              setSelection(null);
            }
          }}
        >
          {/* Active Drag-To-Select Bounding Box */}
          {selection && isSelecting && (
            <div
              className="absolute border-2 border-dashed border-[#53B1FD] bg-[#175CD3]/25 pointer-events-none rounded-[4px] shadow-[0_0_15px_rgba(83,177,253,0.5)] flex items-start justify-end p-1"
              style={{
                left: Math.min(selection.startX, selection.currentX),
                top: Math.min(selection.startY, selection.currentY),
                width: Math.max(1, Math.abs(selection.currentX - selection.startX)),
                height: Math.max(1, Math.abs(selection.currentY - selection.startY)),
              }}
            >
              <div className="absolute -top-1 -left-1 w-2.5 h-2.5 border-t-2 border-l-2 border-[#53B1FD]" />
              <div className="absolute -top-1 -right-1 w-2.5 h-2.5 border-t-2 border-r-2 border-[#53B1FD]" />
              <div className="absolute -bottom-1 -left-1 w-2.5 h-2.5 border-b-2 border-l-2 border-[#53B1FD]" />
              <div className="absolute -bottom-1 -right-1 w-2.5 h-2.5 border-b-2 border-r-2 border-[#53B1FD]" />
              {Math.abs(selection.currentX - selection.startX) > 40 && Math.abs(selection.currentY - selection.startY) > 20 && (
                <span className="text-[10px] font-mono text-white bg-[#0C111D]/90 px-1.5 py-0.5 rounded shadow border border-white/20">
                  {Math.round(Math.abs(selection.currentX - selection.startX))} × {Math.round(Math.abs(selection.currentY - selection.startY))}px
                </span>
              )}
            </div>
          )}

          {/* Manual OCR Scanning & Result Box Overlay */}
          {manualScanStatus.box && manualScanStatus.state !== 'idle' && (
            <div
              className={`absolute rounded-[4px] pointer-events-none transition-all duration-150 border-2 ${
                manualScanStatus.state === 'scanning'
                  ? 'border-[#53B1FD] bg-[#175CD3]/20 animate-pulse shadow-[0_0_15px_rgba(83,177,253,0.5)]'
                  : manualScanStatus.state === 'success'
                  ? 'border-[#10B981] bg-[#10B981]/20 shadow-[0_0_15px_rgba(16,185,129,0.5)]'
                  : 'border-[#F04438] bg-[#F04438]/20 shadow-[0_0_15px_rgba(240,68,56,0.5)]'
              }`}
              style={{
                left: manualScanStatus.box.x,
                top: manualScanStatus.box.y,
                width: manualScanStatus.box.w,
                height: manualScanStatus.box.h,
              }}
            >
              <div
                className={`absolute -top-7 left-0 px-2.5 py-0.5 rounded-[5px] text-[11px] font-bold whitespace-nowrap shadow-lg flex items-center gap-1.5 ${
                  manualScanStatus.state === 'scanning'
                    ? 'bg-[#175CD3] text-white'
                    : manualScanStatus.state === 'success'
                    ? 'bg-[#10B981] text-white'
                    : 'bg-[#F04438] text-white'
                }`}
              >
                {manualScanStatus.state === 'scanning' && <RefreshCw className="w-3 h-3 animate-spin text-white" />}
                {manualScanStatus.state === 'success' && <CheckCircle2 className="w-3.5 h-3.5 text-white" />}
                {manualScanStatus.state === 'failed' && <AlertCircle className="w-3.5 h-3.5 text-white" />}
                <span>{manualScanStatus.message}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Floating Prompt Pill: Nhắc người dùng khoanh vùng biển số thủ công */}
      {isManualRoiActive && manualScanStatus.state === 'idle' && (
        <div className="absolute top-12 left-1/2 -translate-x-1/2 px-3.5 py-1.5 rounded-full bg-[#0C111D]/90 backdrop-blur-md border border-[#53B1FD]/50 text-white text-xs font-semibold shadow-xl z-25 flex items-center gap-2 pointer-events-none animate-in fade-in slide-in-from-top-2">
          <span className="w-2 h-2 rounded-full bg-[#53B1FD] animate-ping" />
          <Search className="w-3.5 h-3.5 text-[#53B1FD]" />
          <span>
            {activeTab === 'signs'
              ? 'Kéo khoanh vùng hoặc nhấp vào biển báo để nhận diện thủ công'
              : 'Kéo khoanh vùng hoặc nhấp vào biển số trên xe để nhận diện thủ công'}
          </span>
        </div>
      )}
      </div>

      {/* ── 2. DEDICATED SNAPSHOT & PAUSED FRAME INSPECTOR STRIP (NẰM DƯỚI KHUNG HÌNH - TUYỆT ĐỐI KHÔNG CHE ẢNH / VIDEO) ── */}
      {(sourceMode === 'image' || isPaused) && (
        <div className="w-full px-4 py-2.5 bg-[#080B11] border-t border-white/10 flex flex-wrap items-center justify-between gap-3 text-xs text-white z-10 select-none">
          {/* Left: Status and Findings */}
          <div className="flex items-center gap-2.5 min-w-0 flex-1 flex-wrap">
            {isScanningFrame ? (
              <div className="flex items-center gap-2 text-[#53B1FD] font-semibold animate-pulse">
                <RefreshCw className="w-4 h-4 animate-spin text-[#53B1FD]" />
                <span>
                  {activeTab === 'signs'
                    ? 'Đang đối soát biển báo chuẩn QCVN 41:2019/BGTVT...'
                    : activeTab === 'helmets'
                    ? 'Đang phân tích tuân thủ đội mũ bảo hiểm...'
                    : activeTab === 'traffic'
                    ? 'Đang đo cự ly xe và mật độ giao thông...'
                    : 'Đang phân tích khung hình & đọc biển số xe...'}
                </span>
              </div>
            ) : activeTab === 'signs' ? (
              detectionResult?.traffic_signs && detectionResult.traffic_signs.length > 0 ? (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="flex items-center gap-1 font-bold text-[#10B981]">
                    <CheckCircle2 className="w-4 h-4" />
                    Biển báo:
                  </span>
                  <span className="font-mono font-extrabold text-xs text-[#FDB022] bg-white/10 px-2 py-0.5 rounded border border-[#FDB022]/40">
                    {detectionResult.traffic_signs[0].sign_type}
                  </span>
                  <span className="text-white/90 font-medium">
                    {detectionResult.traffic_signs[0].name}
                  </span>
                  {detectionResult.traffic_signs.length > 1 && (
                    <span className="text-white/60 text-[11px]">
                      (+{detectionResult.traffic_signs.length - 1} biển khác)
                    </span>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-2 text-white/80">
                  <AlertCircle className="w-4 h-4 text-[#F79009] shrink-0" />
                  <span>
                    Không phát hiện biển báo giao thông trong {sourceMode === 'image' ? 'ảnh' : 'khung hình'} này (Đã lọc bỏ các vật thể không rõ nét hoặc ở quá xa)
                  </span>
                </div>
              )
            ) : activeTab === 'helmets' ? (
              detectionResult?.helmet_violations && detectionResult.helmet_violations.length > 0 ? (
                <div className="flex items-center gap-2 text-[#F04438] font-bold">
                  <AlertCircle className="w-4 h-4 shrink-0 text-[#F04438]" />
                  <span>Phát hiện {detectionResult.helmet_violations.length} người đi xe máy không đội mũ bảo hiểm</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-[#10B981] font-semibold">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-[#10B981]" />
                  <span>Không phát hiện vi phạm mũ bảo hiểm trong {sourceMode === 'image' ? 'ảnh' : 'khung hình'} này</span>
                </div>
              )
            ) : activeTab === 'traffic' ? (
              detectedVehiclesCount > 0 ? (
                <div className="flex items-center gap-2 text-white/90">
                  <CheckCircle2 className="w-4 h-4 text-[#10B981] shrink-0" />
                  <span>
                    Phát hiện <strong>{detectedVehiclesCount} xe</strong> • Cự ly an toàn:{' '}
                    <strong className="text-[#53B1FD]">
                      {detectionResult?.collision_warning?.distance_estimate
                        ? `${detectionResult.collision_warning.distance_estimate.toFixed(1)}m`
                        : 'Đảm bảo'}
                    </strong>
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-white/80">
                  <CheckCircle2 className="w-4 h-4 text-[#10B981] shrink-0" />
                  <span>Đường thông thoáng • Không phát hiện phương tiện phía trước</span>
                </div>
              )
            ) : detectionResult?.plates && detectionResult.plates.length > 0 && isValidConfirmedPlate(detectionResult.plates[0].plate_text) ? (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="flex items-center gap-1 font-bold text-[#10B981]">
                  <CheckCircle2 className="w-4 h-4" />
                  Đã nhận diện:
                </span>
                <span className="font-mono font-extrabold text-xs text-[#FDB022] bg-white/10 px-2 py-0.5 rounded border border-[#FDB022]/40">
                  {detectionResult.plates[0].plate_text}
                </span>
                {detectionResult.plates[0].province && (
                  <span className="text-white/80">({detectionResult.plates[0].province})</span>
                )}
                {detectionResult.plates[0].vehicle_type && (
                  <span className="text-white/60 text-[11px]">• {detectionResult.plates[0].vehicle_type}</span>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2 text-white/80">
                <AlertCircle className="w-4 h-4 text-[#F79009] shrink-0" />
                <span>
                  Không có biển số xe hợp lệ trong {sourceMode === 'image' ? 'ảnh' : 'khung hình'} này (Kéo khoanh vùng hoặc nhấp trên xe để nhận diện thủ công)
                </span>
              </div>
            )}
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-2 shrink-0">
            {onScanCurrentFrame && !isScanningFrame && (
              <button
                onClick={onScanCurrentFrame}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] bg-white/10 hover:bg-white/20 text-white font-medium transition-colors cursor-pointer text-xs shadow-xs"
                title={sourceMode === 'image' ? "Quét lại ảnh này" : "Chụp lại khung hình hiện tại và quét lại"}
              >
                <Search className="w-3.5 h-3.5 text-[#53B1FD]" />
                <span>Quét lại</span>
              </button>
            )}
            {sourceMode !== 'image' && onResume && (
              <button
                onClick={onResume}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-[6px] bg-[#175CD3] hover:bg-[#154fc1] text-white font-bold transition-all shadow cursor-pointer text-xs"
                title="Tiếp tục phát video [Space]"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Tiếp tục [Space]</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
});
