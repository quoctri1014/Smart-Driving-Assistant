'use client';

import React, { useRef, useState, useEffect, useMemo, useCallback } from 'react';
import Script from 'next/script';
import { useSearchParams } from 'next/navigation';
import { useDrivingSession } from '../../../hooks/useDrivingSession';
import { useClientTrafficAI } from '../../../hooks/useClientTrafficAI';
import { useAuthStore } from '../../../stores/authStore';
import { soundEngine } from '../../../lib/soundEngine';
import { violationService } from '../../../services/violationService';

import { SystemHealthBanner } from '../../../components/live/SystemHealthBanner';
import { LiveHeader, LiveViewMode } from '../../../components/live/LiveHeader';
import { PriorityAlertBar } from '../../../components/live/PriorityAlertBar';
import { RoadCameraViewport } from '../../../components/live/RoadCameraViewport';
import { UnifiedTelemetryStrip } from '../../../components/live/UnifiedTelemetryStrip';
import { DetectionTabsPanel, DetectionTabType } from '../../../components/live/DetectionTabsPanel';
import { CabinCameraViewport } from '../../../components/live/CabinCameraViewport';
import { RealtimeEventTimeline, TimelineEventItem } from '../../../components/live/RealtimeEventTimeline';
import { AIDiagnosticsPanel } from '../../../components/live/AIDiagnosticsPanel';
import { DetectionResult, isValidConfirmedPlate } from '../../../types/detection';
import { useTrafficDistanceEngine } from '../../../hooks/useTrafficDistanceEngine';
import { deriveDrivingUIState } from '../../../lib/driving/alert-engine';

type SourceMode = 'video' | 'webcam' | 'image';

export default function LiveMonitorPage() {
  const { user } = useAuthStore();
  const searchParams = useSearchParams();
  const requestedPlate = searchParams?.get('plate') || '29A-888.88';

  const [viewMode, setViewMode] = useState<LiveViewMode>('matrix');
  const [activeTab, setActiveTab] = useState<DetectionTabType>('plates');
  const [sourceMode, setSourceMode] = useState<SourceMode>('video');
  const [roadVideoUrl, setRoadVideoUrl] = useState<string | null>(null);
  const [roadVideoFileName, setRoadVideoFileName] = useState<string>('');
  const [durationSeconds, setDurationSeconds] = useState<number>(0);
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(false);
  const [sidebarView, setSidebarView] = useState<'all' | 'dms' | 'events'>('all');
  const [events, setEvents] = useState<TimelineEventItem[]>([]);

  // Toast Notification khi chuyển chế độ & khi tự động dừng nhận diện biển số
  const [tabToast, setTabToast] = useState<{ message: string; subtext: string; icon: string } | null>(null);
  const tabToastTimerRef = useRef<NodeJS.Timeout | null>(null);
  const scanCurrentFrameRef = useRef<() => Promise<any>>(async () => []);
  const uploadedImageFileRef = useRef<File | null>(null);

  const [isCabinWebcamActive, setIsCabinWebcamActive] = useState<boolean>(false);
  const cabinStreamRef = useRef<MediaStream | null>(null);
  const roadStreamRef = useRef<MediaStream | null>(null);

  const roadVideoRef = useRef<HTMLVideoElement>(null);
  const driverVideoRef = useRef<HTMLVideoElement>(null);
  const roadFileInputRef = useRef<HTMLInputElement>(null);

  // Session & WebSocket Hooks (Admin has full access to both cameras)
  const {
    sessionState,
    uiState,
    startSession,
    pauseSession,
    resumeSession,
    stopSession,
    roadSocket,
    driverSocket,
  } = useDrivingSession({ useDriverCamera: true });

  const sendRoadFrameRef = useRef(roadSocket.sendFrame);
  useEffect(() => {
    sendRoadFrameRef.current = roadSocket.sendFrame;
  }, [roadSocket.sendFrame]);

  const sendDriverFrameRef = useRef(driverSocket.sendFrame);
  useEffect(() => {
    sendDriverFrameRef.current = driverSocket.sendFrame;
  }, [driverSocket.sendFrame]);


  // Xử lý tự động dừng video khi phát hiện biển số xe (Auto-Pause on Plate Detection với cơ chế chống bắt sai chữ/intro)
  const handleAutoPausePlate = useCallback(async (leadPlate: any) => {
    if (sourceMode !== 'video' || sessionState !== 'STREAMING') return;
    pauseSession();
    if (roadVideoRef.current) {
      roadVideoRef.current.pause();
    }

    // Quét đối soát tức thì với backend OCR
    const detected = await scanCurrentFrameRef.current();
    const confirmedPlates = (detected || []).filter((p: any) => isValidConfirmedPlate(p.plate_text));

    if (confirmedPlates.length === 0) {
      // Nếu là chữ banner, quảng cáo, intro video không phải biển số thật -> TỰ ĐỘNG TIẾP TỤC PHÁT
      resumeSession();
      if (roadVideoRef.current) {
        roadVideoRef.current.play().catch(() => {});
      }
      return;
    }

    const firstValid = confirmedPlates[0];
    const plateLabel = firstValid?.plate_text ? ` [${firstValid.plate_text}]` : '';
    setTabToast({
      message: `Đã phát hiện biển số xe${plateLabel}`,
      subtext: 'Tự động dừng video để chụp khung hình nét & nhận diện OCR [Nhấn Space để tiếp tục]',
      icon: '⏸️',
    });
    if (tabToastTimerRef.current) clearTimeout(tabToastTimerRef.current);
    tabToastTimerRef.current = setTimeout(() => {
      setTabToast(null);
    }, 4500);
  }, [sourceMode, sessionState, pauseSession, resumeSession]);

  // Dedicated In-Browser AI Engine (YOLOv8 Plate, Traffic Sign, Helmet & OCR)
  const {
    detectionResult: clientDetectionResult,
    cumulativePlates,
    cumulativeSigns,
    cumulativeHelmets,
    modelsLoaded,
    aiPerformance,
    recognizePlateFromFile,
    recognizeSignsFromFile,
    recognizeHelmetsFromFile,
    detectTrafficDensityFromFile,
    scanCurrentFrame,
    scanManualPlateCrop,
    scanManualSignCrop,
    isScanningFrame,
    setIsScanningFrame,
    resetHistory,
  } = useClientTrafficAI({
    videoRef: roadVideoRef,
    isStreaming: sessionState === 'STREAMING',
    activeTab,
    sourceMode,
    onAutoPausePlate: handleAutoPausePlate,
  });

  scanCurrentFrameRef.current = scanCurrentFrame;

  // Xử lý chuyển chế độ: Tự động chạy lại video & hiển thị thông báo chuyển tab
  const handleTabChange = useCallback((newTab: DetectionTabType) => {
    setActiveTab(newTab);
    const tabInfoMap: Record<DetectionTabType, { message: string; subtext: string; icon: string }> = {
      plates: {
        message: 'Chế độ Biển Số Xe',
        subtext: 'Tự động phát hiện & tạm dừng video nhận diện OCR chuẩn xác',
        icon: '🪪',
      },
      signs: {
        message: 'Chế độ Biển Báo Giao Thông',
        subtext: 'Tự động phát hiện biển cấm, cảnh báo & hiệu lệnh QCVN 41',
        icon: '⛔',
      },
      traffic: {
        message: 'Chế độ Mật Độ & Cự Ly',
        subtext: 'Giám sát khoảng cách an toàn phương tiện & cảnh báo va chạm ADAS',
        icon: '🚗',
      },
      helmets: {
        message: 'Chế độ Mũ Bảo Hiểm',
        subtext: 'Phát hiện vi phạm không đội mũ bảo hiểm xe máy theo NĐ 100',
        icon: '🪖',
      },
    };

    setTabToast(tabInfoMap[newTab]);
    if (tabToastTimerRef.current) clearTimeout(tabToastTimerRef.current);
    tabToastTimerRef.current = setTimeout(() => {
      setTabToast(null);
    }, 3500);

    // TỰ ĐỘNG CHẠY LẠI VIDEO & TIẾP TỤC SESSION KHI CHUYỂN TAB
    if (sourceMode === 'video' || sourceMode === 'webcam') {
      if (sessionState === 'PAUSED' || roadVideoRef.current?.paused) {
        resumeSession();
        if (roadVideoRef.current) {
          roadVideoRef.current.play().catch(() => {});
        }
      }
    } else if (sourceMode === 'image' && uploadedImageFileRef.current) {
      // Khi đang xem ảnh tĩnh và người dùng đổi tab: nạp dữ liệu tức thì cho tab mới
      const file = uploadedImageFileRef.current;
      if (newTab === 'signs') {
        recognizeSignsFromFile(file, false).catch(() => {});
      } else if (newTab === 'helmets') {
        recognizeHelmetsFromFile(file, false).catch(() => {});
      } else if (newTab === 'traffic') {
        detectTrafficDensityFromFile(file).catch(() => {});
      } else {
        recognizePlateFromFile(file, false).catch(() => {});
      }
    }
  }, [sourceMode, sessionState, resumeSession, recognizeSignsFromFile, recognizeHelmetsFromFile, detectTrafficDensityFromFile, recognizePlateFromFile]);

  // Trip Duration Timer
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    if (sessionState === 'STREAMING') {
      timer = setInterval(() => {
        setDurationSeconds((prev) => prev + 1);
      }, 1000);
    } else if (sessionState === 'IDLE' || sessionState === 'ENDED') {
      setDurationSeconds(0);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [sessionState]);

  const durationFormatted = useMemo(() => {
    const hours = Math.floor(durationSeconds / 3600);
    const minutes = Math.floor((durationSeconds % 3600) / 60);
    const seconds = durationSeconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }, [durationSeconds]);

  // Audio Mute Toggle
  const handleToggleMute = useCallback(() => {
    const nextState = soundEngine.toggleMuted();
    setIsAudioMuted(nextState);
    if (!nextState) {
      soundEngine.testVoice();
    } else {
      soundEngine.speak('Đã tắt cảnh báo âm thanh', 'normal');
    }
  }, []);

  // Road Camera: Use Webcam / Dashcam directly in-browser
  const handleUseRoadWebcam = useCallback(async () => {
    try {
      if (roadStreamRef.current) {
        roadStreamRef.current.getTracks().forEach((t) => t.stop());
        roadStreamRef.current = null;
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: 1280, height: 720 },
      });
      roadStreamRef.current = stream;
      setRoadVideoUrl('webcam');
      setRoadVideoFileName('Camera Trước / Webcam Xe (Trực tiếp)');
      setSourceMode('webcam');
      resetHistory();
      if (roadVideoRef.current) {
        roadVideoRef.current.src = '';
        roadVideoRef.current.srcObject = stream;
        roadVideoRef.current.play().catch(() => {});
      }
      startSession();
    } catch (err: any) {
      console.warn('Cannot open road webcam:', err);
      alert('Không thể mở camera trước / webcam: ' + (err?.message || 'Vui lòng cho phép truy cập camera trong trình duyệt'));
    }
  }, [resetHistory, startSession]);

  // Handle Road Video/Image File Upload
  const handleRoadFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (roadStreamRef.current) {
        roadStreamRef.current.getTracks().forEach((t) => t.stop());
        roadStreamRef.current = null;
      }
      if (roadVideoUrl && roadVideoUrl.startsWith('blob:')) URL.revokeObjectURL(roadVideoUrl);
      const url = URL.createObjectURL(file);
      setRoadVideoFileName(file.name);
      resetHistory();
      setEvents([]);

      if (file.type.startsWith('image/')) {
        uploadedImageFileRef.current = file;
        setSourceMode('image');
        setRoadVideoUrl(url);
        stopSession(); // Đưa session về IDLE, tuyệt đối không gọi pauseSession() để tránh dính cờ isPaused

        // QUÉT TỨC THÌ CHO ẢNH TĨNH THEO TAB ĐANG CHỌN:
        const scanImageInstant = async () => {
          setIsScanningFrame(true);
          try {
            if (activeTab === 'signs') {
              await recognizeSignsFromFile(file, true);
            } else if (activeTab === 'helmets') {
              await recognizeHelmetsFromFile(file, true);
            } else if (activeTab === 'traffic') {
              await detectTrafficDensityFromFile(file);
            } else {
              await recognizePlateFromFile(file, true);
            }
          } catch (err) {
            console.warn('Lỗi quét ảnh tức thì:', err);
          } finally {
            setIsScanningFrame(false);
          }
        };
        scanImageInstant();
      } else {
        setSourceMode('video');
        setRoadVideoUrl(url);
        if (roadVideoRef.current) {
          roadVideoRef.current.srcObject = null;
          roadVideoRef.current.src = url;
          roadVideoRef.current.load();
          roadVideoRef.current.play().catch(() => {});
        }
        // Tự động phát video và kích hoạt nhận diện AI tức thì
        startSession();
      }
    }
  };

  // Handle Preset Sample Video Selection (Direct hardware streaming without downloading 50MB into JS memory)
  const handleSelectSample = useCallback((url: string, name: string) => {
    soundEngine.unlockAudio();
    if (roadStreamRef.current) {
      roadStreamRef.current.getTracks().forEach((t) => t.stop());
      roadStreamRef.current = null;
    }
    resetHistory();
    setEvents([]);
    setRoadVideoFileName(name);
    setSourceMode('video');
    setRoadVideoUrl(url);
    if (roadVideoRef.current) {
      roadVideoRef.current.srcObject = null;
      roadVideoRef.current.src = url;
      roadVideoRef.current.load();
      roadVideoRef.current.play().catch(() => {});
    }
    soundEngine.speak('Bắt đầu giám sát hành trình. Trợ lý lái xe AI đã kích hoạt.', 'normal');
    startSession();
  }, [resetHistory, startSession]);

  // Clean up streams on unmount
  useEffect(() => {
    return () => {
      if (roadStreamRef.current) {
        roadStreamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  // Unified Start Handler: Prompt file picker if user hasn't selected a media file yet
  const handleStartSession = useCallback(async () => {
    soundEngine.unlockAudio();
    if (!roadVideoUrl && sourceMode === 'video') {
      roadFileInputRef.current?.click();
      return;
    }
    soundEngine.speak('Bắt đầu giám sát hành trình. Trợ lý lái xe AI đã kích hoạt.', 'normal');
    startSession();
  }, [roadVideoUrl, sourceMode, startSession]);

  // Tạm dừng video và tự động trích xuất khung hình hiện tại để quét toàn diện theo tab đang chọn
  const handlePauseAndScan = useCallback(async () => {
    pauseSession();
    if (roadVideoRef.current) {
      roadVideoRef.current.pause();
    }
    await scanCurrentFrame();
  }, [pauseSession, scanCurrentFrame]);

  // Quét lại khung hình hiện tại (cho video tạm dừng) hoặc quét lại file ảnh (cho ảnh tĩnh)
  const handleScanCurrentFrame = useCallback(async () => {
    if (sourceMode === 'image' && uploadedImageFileRef.current) {
      const file = uploadedImageFileRef.current;
      setIsScanningFrame(true);
      try {
        if (activeTab === 'signs') {
          await recognizeSignsFromFile(file, true);
        } else if (activeTab === 'helmets') {
          await recognizeHelmetsFromFile(file, true);
        } else if (activeTab === 'traffic') {
          await detectTrafficDensityFromFile(file);
        } else {
          await recognizePlateFromFile(file, true);
        }
      } catch (err) {
        console.warn('Lỗi quét lại ảnh:', err);
      } finally {
        setIsScanningFrame(false);
      }
    } else {
      await scanCurrentFrame();
    }
  }, [
    sourceMode,
    activeTab,
    scanCurrentFrame,
    recognizeSignsFromFile,
    recognizeHelmetsFromFile,
    detectTrafficDensityFromFile,
    recognizePlateFromFile,
    setIsScanningFrame,
  ]);

  // Keyboard Shortcuts: Space (Play/Pause & Scan), M (Mute Voice), H (Toggle HUD), 1/2/3 (Tabs), F (Fullscreen)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'TEXTAREA'
      ) {
        return;
      }

      if (e.code === 'Space') {
        e.preventDefault();
        if (sessionState === 'STREAMING') {
          handlePauseAndScan();
        } else if (sessionState === 'PAUSED') {
          resumeSession();
        } else if (sessionState === 'IDLE' || sessionState === 'ENDED') {
          handleStartSession();
        }
      } else if (e.code === 'KeyM') {
        e.preventDefault();
        handleToggleMute();
      } else if (e.code === 'KeyH') {
        e.preventDefault();
        setViewMode((prev) => (prev === 'hud' ? 'matrix' : 'hud'));
      } else if (e.code === 'Digit1') {
        e.preventDefault();
        handleTabChange('plates');
      } else if (e.code === 'Digit2') {
        e.preventDefault();
        handleTabChange('traffic');
      } else if (e.code === 'Digit3') {
        e.preventDefault();
        handleTabChange('signs');
      } else if (e.code === 'Digit4') {
        e.preventDefault();
        handleTabChange('helmets');
      } else if (e.code === 'KeyF') {
        e.preventDefault();
        if (roadVideoRef.current) {
          if (!document.fullscreenElement) {
            roadVideoRef.current.requestFullscreen?.().catch(() => {});
          } else {
            document.exitFullscreen?.().catch(() => {});
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [sessionState, handlePauseAndScan, resumeSession, handleStartSession, handleToggleMute]);

  // Cabin Webcam Toggle Handler (Laptop camera dedicated for Driver DMS)
  const handleToggleCabinWebcam = useCallback(async () => {
    if (isCabinWebcamActive) {
      if (cabinStreamRef.current) {
        cabinStreamRef.current.getTracks().forEach((t) => t.stop());
        cabinStreamRef.current = null;
      }
      if (driverVideoRef.current) {
        driverVideoRef.current.srcObject = null;
      }
      setIsCabinWebcamActive(false);
      driverSocket.disconnect();
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, frameRate: 15 },
        });
        cabinStreamRef.current = stream;
        setIsCabinWebcamActive(true);
        if (driverVideoRef.current) {
          driverVideoRef.current.srcObject = stream;
          driverVideoRef.current.play().catch(() => {});
        }
        if (driverSocket.status !== 'CONNECTED' && driverSocket.status !== 'CONNECTING') {
          driverSocket.connect();
        }
      } catch (err) {
        console.warn('Cannot access cabin webcam:', err);
        alert('Không thể mở webcam buồng lái. Vui lòng cấp quyền truy cập camera trong trình duyệt.');
      }
    }
  }, [isCabinWebcamActive, driverSocket]);

  // Clean up cabin stream on unmount
  useEffect(() => {
    return () => {
      if (cabinStreamRef.current) {
        cabinStreamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  // Road Video Stream Lifecycle (Road Camera only plays video file/sample - never laptop webcam)
  useEffect(() => {
    if (sessionState === 'STREAMING') {
      if (roadVideoRef.current && roadVideoUrl) {
        roadVideoRef.current.play().catch(() => {});
      }
    } else if (sessionState === 'PAUSED' || sessionState === 'IDLE' || sessionState === 'ENDED') {
      if (roadVideoRef.current) {
        roadVideoRef.current.pause();
      }
    }
  }, [sessionState, roadVideoUrl]);

  // Frame streaming loop for Road Camera to AI Backend over roadSocket
  useEffect(() => {
    if (sessionState !== 'STREAMING' || roadSocket.status !== 'CONNECTED' || !roadVideoRef.current)
      return;

    let isRunning = true;
    const video = roadVideoRef.current;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    const captureAndSend = () => {
      if (!isRunning) return;
      if (!video || video.paused || video.ended || !video.videoWidth || !video.videoHeight) {
        if (isRunning) setTimeout(captureAndSend, 100);
        return;
      }

      if (ctx) {
        canvas.width = 640;
        canvas.height = 360;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(
          (blob) => {
            if (blob && isRunning) {
              sendRoadFrameRef.current(blob);
            }
          },
          'image/jpeg',
          0.7
        );
      }

      setTimeout(captureAndSend, 100);
    };

    captureAndSend();

    return () => {
      isRunning = false;
    };
  }, [sessionState, roadSocket.status]);

  // Frame streaming loop for Cabin/Driver Camera to AI Backend over driverSocket
  useEffect(() => {
    if (driverSocket.status !== 'CONNECTED' || !isCabinWebcamActive || !driverVideoRef.current)
      return;

    let isRunning = true;
    const video = driverVideoRef.current;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    const captureAndSend = () => {
      if (!isRunning) return;
      if (!video || video.paused || video.ended || !video.videoWidth || !video.videoHeight) {
        if (isRunning) setTimeout(captureAndSend, 120);
        return;
      }

      if (ctx) {
        canvas.width = 320;
        canvas.height = 240;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(
          (blob) => {
            if (blob && isRunning) {
              sendDriverFrameRef.current(blob);
            }
          },
          'image/jpeg',
          0.65
        );
      }

      setTimeout(captureAndSend, 120);
    };

    captureAndSend();

    return () => {
      isRunning = false;
    };
  }, [driverSocket.status, isCabinWebcamActive]);

  // HỢP NHẤT TOÀN DIỆN DỮ LIỆU AI (UNIFIED REALTIME MULTI-AI DETECTION PIPELINE)
  // Giữ trọn vẹn toàn bộ các kênh dữ liệu để các bộ xử lý ADAS & cảnh báo giọng nói luôn hoạt động
  const detectionResult = useMemo<DetectionResult | null>(() => {
    if (!clientDetectionResult && !roadSocket.result) return null;
    const merged = {
      ...(roadSocket.result || {}),
      ...(clientDetectionResult || {}),
      frame_id: clientDetectionResult?.frame_id ?? roadSocket.result?.frame_id ?? 0,
      timestamp: clientDetectionResult?.timestamp ?? roadSocket.result?.timestamp ?? Date.now(),
      processing_time_ms: clientDetectionResult?.processing_time_ms ?? roadSocket.result?.processing_time_ms ?? 0,
    };

    const clientVehs = clientDetectionResult?.vehicles;
    const sockVehs = roadSocket.result?.vehicles;
    const rawVehicles = clientVehs && clientVehs.length > 0 ? clientVehs : (sockVehs || []);

    const targetW = merged.frame_width || 1280;
    const targetH = merged.frame_height || 720;
    const sockW = roadSocket.result?.frame_width || 640;
    const sockH = roadSocket.result?.frame_height || 360;

    const normalizedVehicles = rawVehicles.map((v) => {
      if (clientVehs && clientVehs.length > 0) return v;
      if (sockW === targetW && sockH === targetH) return v;
      const sx = targetW / sockW;
      const sy = targetH / sockH;
      return {
        ...v,
        bbox: {
          x1: Math.round(v.bbox.x1 * sx),
          y1: Math.round(v.bbox.y1 * sy),
          x2: Math.round(v.bbox.x2 * sx),
          y2: Math.round(v.bbox.y2 * sy),
        },
      };
    });

    const plates = clientDetectionResult?.plates?.length
      ? clientDetectionResult.plates
      : (roadSocket.result?.plates || []);

    const traffic_signs = clientDetectionResult?.traffic_signs?.length
      ? clientDetectionResult.traffic_signs
      : (roadSocket.result?.traffic_signs || []);

    const helmet_violations = clientDetectionResult?.helmet_violations?.length
      ? clientDetectionResult.helmet_violations
      : (roadSocket.result?.helmet_violations || []);

    const collision_warning = clientDetectionResult?.collision_warning || roadSocket.result?.collision_warning;
    const speed_advice = clientDetectionResult?.speed_advice || roadSocket.result?.speed_advice;
    const line_crossings = clientDetectionResult?.line_crossings || roadSocket.result?.line_crossings;

    return {
      ...merged,
      plates,
      traffic_signs,
      helmet_violations,
      vehicles: normalizedVehicles,
      collision_warning,
      speed_advice,
      line_crossings,
    };
  }, [clientDetectionResult, roadSocket.result]);
  const driverResult = driverSocket.result;

  const isImageMode = sourceMode === 'image';
  const currentSpeed = isImageMode ? null : (detectionResult?.speed_advice?.current_speed ?? null);
  const detectedSpeedLimit = detectionResult?.traffic_signs?.find((s) => s.speed_limit != null)?.speed_limit ?? null;
  const speedLimit = isImageMode ? detectedSpeedLimit : (detectedSpeedLimit ?? 50);

  // Dedicated Traffic Distance Engine (3-Zone Perspective & Simulation Fallback matching "Cảnh báo khoảng cách xe")
  const trafficEngine = useTrafficDistanceEngine({
    realVehicles: detectionResult?.vehicles,
    frameWidth: detectionResult?.frame_width || (roadVideoRef.current?.videoWidth || 1280),
    frameHeight: detectionResult?.frame_height || (roadVideoRef.current?.videoHeight || 720),
    isStreaming: sessionState === 'STREAMING',
    isPaused: sessionState === 'PAUSED',
    sourceMode,
    serverLineCrossings: detectionResult?.line_crossings,
  });

  const safeDistance = detectionResult?.collision_warning?.distance_estimate ?? (trafficEngine?.zoneFront?.dist ?? null);
  const recommendedDistance = detectionResult?.collision_warning?.recommended_distance_m ?? 20;
  const recommendedSpeed = isImageMode ? null : (detectionResult?.speed_advice?.recommended_speed ?? null);
  const vehicleDensityCount = detectionResult?.vehicles?.length ?? 0;

  const trafficZoneLvl =
    trafficEngine.zoneFront.lvl === 2 || trafficEngine.zoneLeft.lvl === 2 || trafficEngine.zoneRight.lvl === 2
      ? 'danger'
      : trafficEngine.zoneFront.lvl === 1 || trafficEngine.zoneLeft.lvl === 1 || trafficEngine.zoneRight.lvl === 1
      ? 'warning'
      : 'none';

  const collisionLevel = isImageMode
    ? 'none'
    : (trafficZoneLvl !== 'none' ? trafficZoneLvl : (detectionResult?.collision_warning?.level || 'none'));

  // Đồng bộ trạng thái cảnh báo giao diện (UI State) chuẩn xác theo dữ liệu đã hợp nhất
  const activeUiState = useMemo(() => {
    return deriveDrivingUIState(
      detectionResult,
      driverResult,
      roadSocket.isStale,
      driverSocket.isStale,
      {
        sourceMode,
        currentSpeed,
        speedLimit,
        safeDistance,
        collisionLevel,
      }
    );
  }, [
    detectionResult,
    driverResult,
    roadSocket.isStale,
    driverSocket.isStale,
    sourceMode,
    currentSpeed,
    speedLimit,
    safeDistance,
    collisionLevel,
  ]);

  // Bộ điều phối giọng đọc thông minh & chống spam lặp (Voice Alert Arbiter with Strict Throttling)
  const spokenThrottleRef = useRef<Map<string, number>>(new Map());
  const speakAlertWithThrottle = useCallback(
    (
      key: string,
      text: string,
      soundType?: 'alarm_critical' | 'chime',
      priority: 'normal' | 'critical' = 'normal',
      cooldownMs = 5000
    ) => {
      const now = Date.now();
      const last = spokenThrottleRef.current.get(key) || 0;
      if (now - last < cooldownMs) {
        return;
      }
      spokenThrottleRef.current.set(key, now);
      if (soundType) {
        soundEngine.playSound(soundType);
      }
      soundEngine.speak(text, priority);
    },
    []
  );

  // Trích xuất khung hình từ camera (Road hoặc Cabin) dạng Base64
  const captureSnapshotBase64 = useCallback((type: 'road' | 'cabin' = 'road'): string | null => {
    try {
      const video = type === 'cabin' ? driverVideoRef.current : roadVideoRef.current;
      if (!video || video.videoWidth === 0 || video.videoHeight === 0) return null;
      const canvas = document.createElement('canvas');
      canvas.width = Math.min(video.videoWidth, 800);
      canvas.height = Math.min(video.videoHeight, 450);
      const ctx = canvas.getContext('2d');
      if (!ctx) return null;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      return canvas.toDataURL('image/jpeg', 0.82);
    } catch {
      return null;
    }
  }, []);

  // Tự động đồng bộ và lưu hồ sơ sự cố vi phạm vào Database Backend
  const violationRecordThrottleRef = useRef<Map<string, number>>(new Map());
  const recordViolationSafely = useCallback((payload: {
    violation_type: string;
    severity?: 'INFO' | 'WARNING' | 'CRITICAL';
    confidence?: number;
    source_module?: string;
    speed_kph?: number;
    speed_limit_kph?: number;
    notes?: string;
    cameraSource?: 'road' | 'cabin';
  }) => {
    const now = Date.now();
    const lastTime = violationRecordThrottleRef.current.get(payload.violation_type) || 0;
    // Giãn cách ít nhất 15s giữa các lần lưu cùng 1 loại sự cố để chống trùng lặp
    if (now - lastTime < 15000) return;
    violationRecordThrottleRef.current.set(payload.violation_type, now);

    const snapshotBase64 = captureSnapshotBase64(payload.cameraSource || 'road');

    violationService.recordViolation({
      violation_type: payload.violation_type,
      severity: payload.severity || 'WARNING',
      confidence: payload.confidence || 0.94,
      source_module: payload.source_module || 'dms_cabin_monitor',
      speed_kph: payload.speed_kph !== undefined ? payload.speed_kph : (currentSpeed ? Math.round(currentSpeed) : 52),
      speed_limit_kph: payload.speed_limit_kph !== undefined ? payload.speed_limit_kph : (speedLimit ? Math.round(speedLimit) : 50),
      latitude: 10.762622,
      longitude: 106.660172,
      location_name: 'Đại lộ Võ Văn Kiệt, Quận 1, TP. Hồ Chí Minh',
      image_base64: snapshotBase64 || undefined,
      notes: payload.notes || `Sự cố an toàn ghi nhận lúc ${new Date().toLocaleTimeString('vi-VN')}`
    }).then(() => {
      console.log(`[Safety Guard] Đã ghi nhận hồ sơ sự cố: ${payload.violation_type}`);
    }).catch((err) => {
      console.warn('[Safety Guard Record Notice]', err);
    });
  }, [captureSnapshotBase64, currentSpeed, speedLimit]);

  // Local In-Browser DMS Event Handler (Dual-layer guarantee with backend DMS)
  const handleClientDmsEvent = useCallback(
    (event: { type: string; level: 'warning' | 'critical'; closedDuration: number; ear: number }) => {
      const nowStr = new Date().toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });

      if (event.level === 'critical') {
        const eventId = `dms-crit-${Date.now()}`;
        setEvents((prev) => {
          if (
            prev.length > 0 &&
            prev[0].title.includes('Nhắm mắt') &&
            Date.now() - parseInt(prev[0].id.split('-')[2] || '0') < 4000
          ) {
            return prev;
          }
          return [
            {
              id: eventId,
              timestamp: nowStr,
              level: 'critical',
              title: 'Nguy hiểm: Tài xế nhắm mắt quá 5 giây (DMS)',
              details: `Thời gian nhắm: ${event.closedDuration.toFixed(1)}s • EAR: ${event.ear.toFixed(
                2
              )} • Trạng thái: Cảnh báo ngủ gật khẩn cấp!`,
              status: 'pending',
            },
            ...prev.slice(0, 49),
          ];
        });
        speakAlertWithThrottle('dms_sleep', 'Cảnh báo ngủ gật! Dừng xe nghỉ ngay!', 'alarm_critical', 'critical', 5000);
        recordViolationSafely({
          violation_type: 'drowsy',
          severity: 'CRITICAL',
          confidence: 0.95,
          source_module: 'dms_cabin_monitor',
          cameraSource: 'cabin',
          notes: 'Phát hiện tài xế nhắm mắt quá 5 giây (Ngủ gật khẩn cấp)'
        });
      } else if (event.level === 'warning') {
        const eventId = `dms-warn-${Date.now()}`;
        setEvents((prev) => {
          if (
            prev.length > 0 &&
            prev[0].title.includes('nhắm mắt') &&
            Date.now() - parseInt(prev[0].id.split('-')[2] || '0') < 3000
          ) {
            return prev;
          }
          return [
            {
              id: eventId,
              timestamp: nowStr,
              level: 'warning',
              title: 'Cảnh báo: Tài xế đang nhắm mắt',
              details: `Thời gian nhắm: ${event.closedDuration.toFixed(1)}s / 5.0s • EAR: ${event.ear.toFixed(2)}`,
              status: 'pending',
            },
            ...prev.slice(0, 49),
          ];
        });
        speakAlertWithThrottle('dms_warn', 'Cảnh báo! Bạn đang có dấu hiệu buồn ngủ!', 'chime', 'normal', 4000);
      }
    },
    [speakAlertWithThrottle, recordViolationSafely]
  );

  // Dynamic Event Stream Synchronizer (Road AI + Cabin DMS)
  useEffect(() => {
    const nowStr = new Date().toLocaleTimeString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });

    // 1. Collision Hazard Event
    if (detectionResult && (collisionLevel === 'danger' || collisionLevel === 'warning')) {
      const isDanger = collisionLevel === 'danger';
      const eventId = `col-${Date.now()}`;
      setEvents((prev) => {
        if (prev.length > 0 && prev[0].title.includes('va chạm') && Date.now() - parseInt(prev[0].id.split('-')[1] || '0') < 3000) {
          return prev;
        }
        return [
          {
            id: eventId,
            timestamp: nowStr,
            level: isDanger ? 'critical' : 'warning',
            title: isDanger ? 'Nguy cơ va chạm phía trước (Khẩn cấp)' : 'Khoảng cách xe trước cận an toàn',
            details: `Cự ly ước tính: ${safeDistance !== null ? safeDistance.toFixed(1) : '—'}m • TTC: ${
              safeDistance !== null && currentSpeed ? (safeDistance / (currentSpeed * (1000 / 3600))).toFixed(1) : '—'
            }s`,
            status: 'pending',
          },
          ...prev.slice(0, 49),
        ];
      });

      // Phát âm thanh và giọng đọc tiếng Việt có giãn cách (Throttle)
      if (isDanger) {
        speakAlertWithThrottle('col_danger', 'Nguy hiểm! Phanh gấp, nguy cơ va chạm!', 'alarm_critical', 'critical', 4000);
        recordViolationSafely({
          violation_type: 'collision_danger',
          severity: 'CRITICAL',
          confidence: 0.92,
          source_module: 'adas_collision_radar',
          cameraSource: 'road',
          notes: 'Khoảng cách phương tiện phía trước ở mức nguy hiểm, cảnh báo va chạm khẩn cấp'
        });
      } else {
        const distStr = safeDistance !== null ? Math.round(safeDistance) : 20;
        speakAlertWithThrottle('col_warn', `Bám quá gần! Giữ khoảng cách ${distStr} mét!`, 'chime', 'normal', 5000);
      }
    }

    // 2. Speeding Violation Event (Tuân thủ dung sai 5 km/h theo Nghị định 100/2019/NĐ-CP)
    if (detectionResult && currentSpeed !== null && speedLimit !== null && currentSpeed > speedLimit + 5) {
      const isExtremeSpeed = currentSpeed > speedLimit + 20;
      const eventId = `spd-${Date.now()}`;
      setEvents((prev) => {
        if (prev.length > 0 && prev[0].title.includes('tốc độ') && Date.now() - parseInt(prev[0].id.split('-')[1] || '0') < 5000) {
          return prev;
        }
        return [
          {
            id: eventId,
            timestamp: nowStr,
            level: 'critical',
            title: isExtremeSpeed ? 'NGUY HIỂM: Chạy quá tốc độ nghiêm trọng (>20 km/h)' : 'Chạy quá tốc độ quy định',
            details: `Tốc độ đo được: ${Math.round(currentSpeed)} km/h • Giới hạn quy định: ${speedLimit} km/h (+${Math.round(currentSpeed - speedLimit)} km/h)`,
            status: 'pending',
          },
          ...prev.slice(0, 49),
        ];
      });

      if (isExtremeSpeed) {
        speakAlertWithThrottle(
          'spd_danger',
          `Nguy hiểm! Vận tốc ${Math.round(currentSpeed)} vượt tốc độ quy định ${Math.round(speedLimit)}! Giảm ga ngay!`,
          'alarm_critical',
          'critical',
          8000
        );
      } else {
        speakAlertWithThrottle(
          'spd_warn',
          `Quá tốc độ! Giới hạn ${Math.round(speedLimit)} ki-lô-mét một giờ!`,
          'alarm_critical',
          'normal',
          8000
        );
      }

      recordViolationSafely({
        violation_type: 'speed_limit',
        severity: isExtremeSpeed ? 'CRITICAL' : 'WARNING',
        confidence: 0.96,
        source_module: 'speed_sentinel_yolo',
        cameraSource: 'road',
        speed_kph: Math.round(currentSpeed),
        speed_limit_kph: Math.round(speedLimit),
        notes: `Vận tốc ${Math.round(currentSpeed)} km/h vượt giới hạn ${Math.round(speedLimit)} km/h (+${Math.round(currentSpeed - speedLimit)} km/h)`
      });
    }

    // 3. Traffic Sign Detected Event
    if (detectionResult && detectionResult.traffic_signs && detectionResult.traffic_signs.length > 0) {
      const sign = detectionResult.traffic_signs[0];
      const eventId = `sign-${Date.now()}`;
      let isNewSign = false;
      setEvents((prev) => {
        if (prev.some((p) => p.title.includes('Biển báo') && Date.now() - parseInt(p.id.split('-')[1] || '0') < 10000)) {
          return prev;
        }
        isNewSign = true;
        return [
          {
            id: eventId,
            timestamp: nowStr,
            level: 'info',
            title: `Biển báo: ${sign.sign_type || 'Giao thông'} - ${sign.name || 'Hiệu lực'}`,
            details: sign.speed_limit
              ? `Biển giới hạn tốc độ: ${sign.speed_limit} km/h (QCVN 41:2019)`
              : (sign.action_required || sign.name || 'Tuân thủ hiệu lệnh quy định theo QCVN 41:2019/BGTVT'),
            status: 'confirmed',
          },
          ...prev.slice(0, 49),
        ];
      });

      if (isNewSign) {
        if (sign.speed_limit) {
          speakAlertWithThrottle(`sign_${sign.sign_type || 'spd'}`, `Biển báo giới hạn tốc độ ${Math.round(sign.speed_limit)}.`, 'chime', 'normal', 10000);
        } else {
          speakAlertWithThrottle(`sign_${sign.sign_type || 'std'}`, `Chú ý biển báo ${sign.name || 'phía trước'}.`, 'chime', 'normal', 10000);
        }
      }
    }

    // 4. Cabin DMS: Prolonged Eye Closure (>= 5s) or Drowsiness
    const closedDur = driverResult?.drowsiness?.closed_duration_s ?? 0;
    const alertLevel = driverResult?.drowsiness?.alert_level;
    const eyeState = driverResult?.drowsiness?.eye_state;
    const isCriticalDms = closedDur >= 5.0 || eyeState === 'CLOSED_CRITICAL' || alertLevel === 'critical';
    const isWarningDms = !isCriticalDms && (closedDur >= 2.0 || eyeState === 'CLOSED_WARN' || alertLevel === 'warning');

    if (isCriticalDms) {
      const eventId = `dms-${Date.now()}`;
      setEvents((prev) => {
        if (prev.length > 0 && prev[0].title.includes('Nhắm mắt') && Date.now() - parseInt(prev[0].id.split('-')[1] || '0') < 4000) {
          return prev;
        }
        return [
          {
            id: eventId,
            timestamp: nowStr,
            level: 'critical',
            title: 'Nguy hiểm: Tài xế nhắm mắt quá 5 giây (DMS)',
            details: `Thời gian nhắm: ${closedDur > 0 ? closedDur.toFixed(1) : '>5.0'}s • EAR: ${
              driverResult?.drowsiness?.ear_value?.toFixed(2) ?? '—'
            } • Tình trạng: Nguy cơ ngủ gật cực kỳ nguy hiểm`,
            status: 'pending',
          },
          ...prev.slice(0, 49),
        ];
      });

      speakAlertWithThrottle('dms_sleep', 'Cảnh báo ngủ gật! Dừng xe nghỉ ngay!', 'alarm_critical', 'critical', 5000);
      recordViolationSafely({
        violation_type: 'drowsy',
        severity: 'CRITICAL',
        confidence: 0.95,
        source_module: 'dms_cabin_monitor',
        cameraSource: 'cabin',
        notes: 'Phát hiện tài xế nhắm mắt quá 5 giây (Ngủ gật khẩn cấp)'
      });
    } else if (isWarningDms) {
      const eventId = `dms-warn-${Date.now()}`;
      setEvents((prev) => {
        if (prev.length > 0 && prev[0].title.includes('nhắm mắt') && Date.now() - parseInt(prev[0].id.split('-')[1] || '0') < 3000) {
          return prev;
        }
        return [
          {
            id: eventId,
            timestamp: nowStr,
            level: 'warning',
            title: 'Cảnh báo: Tài xế đang nhắm mắt',
            details: `Thời gian nhắm: ${closedDur.toFixed(1)}s / 5.0s • EAR: ${
              driverResult?.drowsiness?.ear_value?.toFixed(2) ?? '—'
            }`,
            status: 'pending',
          },
          ...prev.slice(0, 49),
        ];
      });

      speakAlertWithThrottle('dms_warn', 'Cảnh báo! Bạn đang có dấu hiệu buồn ngủ!', 'chime', 'normal', 4000);
    }

    // 5. Cabin Seatbelt Violation Event
    if (driverResult?.seatbelt?.seatbelt_on === false) {
      const eventId = `belt-${Date.now()}`;
      let isNewBelt = false;
      setEvents((prev) => {
        if (prev.length > 0 && prev[0].title.includes('dây an toàn') && Date.now() - parseInt(prev[0].id.split('-')[1] || '0') < 8000) {
          return prev;
        }
        isNewBelt = true;
        return [
          {
            id: eventId,
            timestamp: nowStr,
            level: 'warning',
            title: 'Tài xế chưa cài dây an toàn',
            details: `Độ tin cậy: ${Math.round((driverResult.seatbelt.confidence || 0.8) * 100)}% (Nghị định 100/2019/NĐ-CP)`,
            status: 'pending',
          },
          ...prev.slice(0, 49),
        ];
      });

      if (isNewBelt) {
        speakAlertWithThrottle('seatbelt', 'Cảnh báo! Hãy cài dây an toàn ngay!', 'chime', 'normal', 8000);
        recordViolationSafely({
          violation_type: 'no_seatbelt',
          severity: 'WARNING',
          confidence: 0.89,
          source_module: 'dms_cabin_monitor',
          cameraSource: 'cabin',
          notes: 'Tài xế chưa cài dây an toàn khi điều khiển xe'
        });
      }
    }

    // 6. Helmet Violation Event
    if (detectionResult && detectionResult.helmet_violations && detectionResult.helmet_violations.length > 0) {
      const eventId = `helmet-${Date.now()}`;
      let isNewHelmet = false;
      setEvents((prev) => {
        if (prev.some((p) => p.title.includes('mũ bảo hiểm') && Date.now() - parseInt(p.id.split('-')[1] || '0') < 8000)) {
          return prev;
        }
        isNewHelmet = true;
        return [
          {
            id: eventId,
            timestamp: nowStr,
            level: 'warning',
            title: 'Vi phạm: Không đội mũ bảo hiểm',
            details: 'Phát hiện người điều khiển phương tiện không đội mũ bảo hiểm theo NĐ 100/2019/NĐ-CP',
            status: 'confirmed',
          },
          ...prev.slice(0, 49),
        ];
      });

      if (isNewHelmet) {
        speakAlertWithThrottle('helmet', 'Chú ý! Người lái xe không đội mũ bảo hiểm!', 'chime', 'normal', 8000);
        recordViolationSafely({
          violation_type: 'helmet_violation',
          severity: 'WARNING',
          confidence: 0.93,
          source_module: 'yolo_helmet_detector',
          cameraSource: 'road',
          notes: 'Phát hiện người điều khiển phương tiện không đội mũ bảo hiểm'
        });
      }
    }
  }, [detectionResult, driverResult, collisionLevel, safeDistance, currentSpeed, speedLimit, speakAlertWithThrottle, recordViolationSafely]);

  // Event Timeline Actions (Admin Confirm/Reject)
  const handleConfirmEvent = useCallback((id: string) => {
    setEvents((prev) =>
      prev.map((e) => (e.id === id ? { ...e, status: 'confirmed' } : e))
    );
  }, []);

  const handleRejectEvent = useCallback((id: string) => {
    setEvents((prev) =>
      prev.map((e) => (e.id === id ? { ...e, status: 'rejected' } : e))
    );
  }, []);

  return (
    <div className="space-y-4 w-full max-w-[1720px] mx-auto select-none relative px-1 sm:px-2">
      {/* ── MODE CHANGE & AUTO-PAUSE HUD TOAST NOTIFICATION ── */}
      {tabToast && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 pointer-events-none animate-in fade-in slide-in-from-top-3 duration-250">
          <div className="flex items-center gap-3 px-5 py-2.5 rounded-full bg-[#0C111D]/95 backdrop-blur-xl border border-[#3B82F6]/60 shadow-2xl text-white">
            <span className="text-xl">{tabToast.icon}</span>
            <div>
              <div className="text-xs font-bold text-white tracking-wide flex items-center gap-2">
                <span>{tabToast.message}</span>
                <span className="w-2 h-2 rounded-full bg-[#10B981] animate-ping" />
              </div>
              <div className="text-[11px] text-white/70 font-medium">{tabToast.subtext}</div>
            </div>
          </div>
        </div>
      )}

      {/* Load in-browser AI engines: ONNX Runtime Web & Tesseract OCR */}
      <Script src="https://cdn.jsdelivr.net/npm/onnxruntime-web@1.18.0/dist/ort.min.js" strategy="afterInteractive" />
      <Script src="https://cdn.jsdelivr.net/npm/tesseract.js@5.1.0/dist/tesseract.min.js" strategy="afterInteractive" />

      {/* Hidden File Upload Input */}
      <input
        type="file"
        ref={roadFileInputRef}
        onChange={handleRoadFileChange}
        accept="video/*,image/*"
        className="hidden"
      />

      {/* ── 1. SYSTEM HEALTH BANNER ── */}
      <SystemHealthBanner
        roadStatus={roadVideoUrl ? 'online' : 'waiting'}
        cabinStatus={isCabinWebcamActive || driverResult?.drowsiness ? 'online' : 'offline'}
        socketStatus={roadSocket.status}
        processingTimeMs={detectionResult?.processing_time_ms ?? null}
      />

      {/* ── 2. HEADER TOOLBAR ── */}
      <LiveHeader
        plateNumber={requestedPlate || '29A-888.88'}
        driverName={user?.full_name || 'Người Lái Xe'}
        sessionState={sessionState}
        connectionStatus={
          roadSocket.status === 'CONNECTED'
            ? 'online'
            : roadSocket.status === 'CONNECTING' || roadSocket.status === 'RECONNECTING'
            ? 'reconnecting'
            : 'offline'
        }
        durationFormatted={durationFormatted}
        sourceMode={sourceMode}
        onSourceModeChange={setSourceMode}
        onStart={handleStartSession}
        onPause={handlePauseAndScan}
        onResume={resumeSession}
        onStop={stopSession}
        onUploadClick={() => roadFileInputRef.current?.click()}
        videoFileName={roadVideoFileName}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {/* ── 3. PRIORITY ALERT BAR (TOP OF VIDEO - DYNAMIC 3 COLORS) ── */}
      <PriorityAlertBar
        priority={activeUiState.priority}
        message={activeUiState.message}
        isMuted={isAudioMuted}
        onToggleMute={handleToggleMute}
        safeDistance={safeDistance}
        recommendedSpeed={activeUiState.recommendedSpeed}
        speedLimit={activeUiState.speedLimit}
        currentSpeed={activeUiState.currentSpeed}
      />

      {/* ── 4. VIEW MODE CONDITIONAL CONTENT ── */}
      {viewMode === 'hud' ? (
        /* DRIVER HUD FOCUSED COCKPIT VIEW */
        <div className="space-y-3">
          <RoadCameraViewport
            videoRef={roadVideoRef}
            videoSrc={roadVideoUrl}
            videoFileName={roadVideoFileName}
            sourceMode={sourceMode}
            detectionResult={detectionResult}
            activeTab={activeTab}
            isStreaming={sessionState === 'STREAMING'}
            isPaused={sessionState === 'PAUSED'}
            isScanningFrame={isScanningFrame}
            hasCollisionWarning={collisionLevel !== 'none'}
            collisionLevel={collisionLevel}
            speedLimit={speedLimit}
            currentSpeed={currentSpeed}
            processingTimeMs={detectionResult?.processing_time_ms ?? null}
            zoneLeft={trafficEngine.zoneLeft}
            zoneFront={trafficEngine.zoneFront}
            zoneRight={trafficEngine.zoneRight}
            alertBanner={trafficEngine.alertBanner}
            warnThreshold={trafficEngine.warnThreshold}
            dangerThreshold={trafficEngine.dangerThreshold}
            focalLength={trafficEngine.focalLength}
            showDistanceZones={trafficEngine.showZones}
            trackedVehicles={trafficEngine.trackedVehicles}
            onUploadClick={() => roadFileInputRef.current?.click()}
            onUseWebcam={handleUseRoadWebcam}
            onSelectSample={handleSelectSample}
            onStartStreaming={handleStartSession}
            onResume={resumeSession}
            onScanCurrentFrame={handleScanCurrentFrame}
            onPauseAndScan={handlePauseAndScan}
            onManualSelectPlateRoi={scanManualPlateCrop}
            onManualSelectSignRoi={scanManualSignCrop}
          />

          <UnifiedTelemetryStrip
            currentSpeed={currentSpeed}
            speedLimit={speedLimit}
            safeDistance={safeDistance}
            recommendedDistance={recommendedDistance}
            collisionLevel={collisionLevel}
            vehicleDensityCount={vehicleDensityCount}
            processingTimeMs={detectionResult?.processing_time_ms ?? null}
            isStreaming={sessionState === 'STREAMING'}
            sourceMode={sourceMode}
          />

          {/* Compact Driver DMS Cockpit Strip */}
          <div className="rounded-[10px] bg-[#0C111D] border border-white/10 p-3 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-3">
              <span className="font-bold text-white/90">GIÁM SÁT BUỒNG LÁI HUD:</span>
              <span className="text-[#53B1FD] font-semibold">{user?.full_name || 'Nguyễn Văn An'}</span>
              <span className="text-white/40">•</span>
              <span className="text-white/70">
                Trạng thái:{' '}
                <strong className={driverResult?.drowsiness?.is_drowsy ? 'text-[#F04438]' : 'text-[#12B76A]'}>
                  {driverResult?.drowsiness?.is_drowsy
                    ? 'Buồn ngủ khẩn cấp'
                    : driverResult?.drowsiness
                    ? 'Tỉnh táo & Tập trung'
                    : 'Chờ tín hiệu DMS'}
                </strong>
              </span>
              <span className="text-white/40">•</span>
              <span className="text-white/70">
                EAR:{' '}
                <strong className="text-white font-mono">
                  {driverResult?.drowsiness?.ear_value !== undefined
                    ? driverResult.drowsiness.ear_value.toFixed(2)
                    : '—'}
                </strong>
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-white/60">Nghị định 10 (4h):</span>
              <span className="font-mono font-bold text-[#12B76A]">{Math.floor(durationSeconds / 60)}/240 phút</span>
              <button
                onClick={() => setViewMode('matrix')}
                className="ml-2 px-2 py-0.5 rounded bg-white/10 hover:bg-white/20 text-white font-medium cursor-pointer"
              >
                Trở về Toàn cảnh [H]
              </button>
            </div>
          </div>
        </div>
      ) : viewMode === 'diagnostics' ? (
        /* AI TECHNICAL DIAGNOSTICS VIEW */
        <div className="space-y-4">
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 items-start">
            <div className="xl:col-span-8 2xl:col-span-9 space-y-3.5">
              <RoadCameraViewport
                videoRef={roadVideoRef}
                videoSrc={roadVideoUrl}
                videoFileName={roadVideoFileName}
                sourceMode={sourceMode}
                detectionResult={detectionResult}
                activeTab={activeTab}
                isStreaming={sessionState === 'STREAMING'}
                isPaused={sessionState === 'PAUSED'}
                isScanningFrame={isScanningFrame}
                hasCollisionWarning={collisionLevel !== 'none'}
                collisionLevel={collisionLevel}
                speedLimit={speedLimit}
                currentSpeed={currentSpeed}
                processingTimeMs={detectionResult?.processing_time_ms ?? null}
                zoneLeft={trafficEngine.zoneLeft}
                zoneFront={trafficEngine.zoneFront}
                zoneRight={trafficEngine.zoneRight}
                alertBanner={trafficEngine.alertBanner}
                warnThreshold={trafficEngine.warnThreshold}
                dangerThreshold={trafficEngine.dangerThreshold}
                focalLength={trafficEngine.focalLength}
                showDistanceZones={trafficEngine.showZones}
                trackedVehicles={trafficEngine.trackedVehicles}
                onUploadClick={() => roadFileInputRef.current?.click()}
                onUseWebcam={handleUseRoadWebcam}
                onSelectSample={handleSelectSample}
                onStartStreaming={handleStartSession}
                onResume={resumeSession}
                onScanCurrentFrame={handleScanCurrentFrame}
                onPauseAndScan={handlePauseAndScan}
                onManualSelectPlateRoi={scanManualPlateCrop}
                onManualSelectSignRoi={scanManualSignCrop}
              />
              <UnifiedTelemetryStrip
                currentSpeed={currentSpeed}
                speedLimit={speedLimit}
                safeDistance={safeDistance}
                recommendedDistance={recommendedDistance}
                collisionLevel={collisionLevel}
                vehicleDensityCount={vehicleDensityCount}
                processingTimeMs={detectionResult?.processing_time_ms ?? null}
                isStreaming={sessionState === 'STREAMING'}
                sourceMode={sourceMode}
                activeTab={activeTab}
                plates={cumulativePlates.length > 0 ? cumulativePlates : (detectionResult?.plates || [])}
                signs={cumulativeSigns.length > 0 ? cumulativeSigns : (detectionResult?.traffic_signs || [])}
                helmets={cumulativeHelmets.length > 0 ? cumulativeHelmets : (detectionResult?.helmet_violations || [])}
              />
            </div>
            <div className="xl:col-span-4 2xl:col-span-3 space-y-3.5">
              <CabinCameraViewport
                videoRef={driverVideoRef}
                driverResult={driverResult}
                isStreaming={sessionState === 'STREAMING'}
                isWebcamActive={isCabinWebcamActive}
                onToggleWebcam={handleToggleCabinWebcam}
                driverName={user?.full_name || 'Người Lái Xe'}
                driverId={user?.id || 1}
                driverPhone={user?.phone_number || '0901 234 567'}
                safetyScore={user?.safety_score ?? null}
                continuousMinutes={Math.floor(durationSeconds / 60)}
                onDmsEvent={handleClientDmsEvent}
              />
            </div>
          </div>

          {/* Dedicated AI Pipeline & Latency Diagnostics Panel */}
          <AIDiagnosticsPanel
            detectionResult={detectionResult}
            processingTimeMs={detectionResult?.processing_time_ms ?? null}
            isStreaming={sessionState === 'STREAMING'}
            socketStatus={roadSocket.status}
          />
        </div>
      ) : (
        /* DEFAULT 4-ZONE EXPANDED MONITORING MATRIX VIEW */
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 items-start">
          {/* LEFT COLUMN (8-9 COLS): KHU VỰC CAMERA ROAD LỚN, TELEMETRY & TABS */}
          <div className="xl:col-span-8 2xl:col-span-9 space-y-3.5 flex flex-col">
            <RoadCameraViewport
              videoRef={roadVideoRef}
              videoSrc={roadVideoUrl}
              videoFileName={roadVideoFileName}
              sourceMode={sourceMode}
              detectionResult={detectionResult}
              activeTab={activeTab}
              isStreaming={sessionState === 'STREAMING'}
              isPaused={sessionState === 'PAUSED'}
              isScanningFrame={isScanningFrame}
              hasCollisionWarning={collisionLevel !== 'none'}
              collisionLevel={collisionLevel}
              speedLimit={speedLimit}
              currentSpeed={currentSpeed}
              processingTimeMs={detectionResult?.processing_time_ms ?? null}
              zoneLeft={trafficEngine.zoneLeft}
              zoneFront={trafficEngine.zoneFront}
              zoneRight={trafficEngine.zoneRight}
              alertBanner={trafficEngine.alertBanner}
              warnThreshold={trafficEngine.warnThreshold}
              dangerThreshold={trafficEngine.dangerThreshold}
              focalLength={trafficEngine.focalLength}
              showDistanceZones={trafficEngine.showZones}
              trackedVehicles={trafficEngine.trackedVehicles}
              onUploadClick={() => roadFileInputRef.current?.click()}
              onUseWebcam={handleUseRoadWebcam}
              onSelectSample={handleSelectSample}
              onStartStreaming={handleStartSession}
              onResume={resumeSession}
              onScanCurrentFrame={handleScanCurrentFrame}
              onPauseAndScan={handlePauseAndScan}
              onManualSelectPlateRoi={scanManualPlateCrop}
              onManualSelectSignRoi={scanManualSignCrop}
            />

            <UnifiedTelemetryStrip
              currentSpeed={currentSpeed}
              speedLimit={speedLimit}
              safeDistance={safeDistance}
              recommendedDistance={recommendedDistance}
              collisionLevel={collisionLevel}
              vehicleDensityCount={vehicleDensityCount}
              processingTimeMs={detectionResult?.processing_time_ms ?? null}
              isStreaming={sessionState === 'STREAMING'}
              sourceMode={sourceMode}
              activeTab={activeTab}
              plates={cumulativePlates.length > 0 ? cumulativePlates : (detectionResult?.plates || [])}
              signs={cumulativeSigns.length > 0 ? cumulativeSigns : (detectionResult?.traffic_signs || [])}
              helmets={cumulativeHelmets.length > 0 ? cumulativeHelmets : (detectionResult?.helmet_violations || [])}
            />

            <DetectionTabsPanel
              plates={cumulativePlates.length > 0 ? cumulativePlates : (detectionResult?.plates || [])}
              vehicles={detectionResult?.vehicles || []}
              signs={cumulativeSigns.length > 0 ? cumulativeSigns : (detectionResult?.traffic_signs || [])}
              helmetViolations={cumulativeHelmets.length > 0 ? cumulativeHelmets : (detectionResult?.helmet_violations || [])}
              safeDistance={safeDistance}
              recommendedDistance={recommendedDistance}
              collisionLevel={collisionLevel}
              currentSpeed={currentSpeed}
              isStreaming={sessionState === 'STREAMING'}
              isImageMode={isImageMode}
              activeTab={activeTab}
              onTabChange={handleTabChange}
              lineCrossings={detectionResult?.line_crossings || trafficEngine.lineCrossings}
              onResetLineCrossings={trafficEngine.resetLineCrossings}
              trafficEngine={trafficEngine}
            />
          </div>

          {/* RIGHT COLUMN (3-4 COLS): KHU VỰC B (TÀI XẾ/CABIN DMS) & KHU VỰC D (TIMELINE SỰ KIỆN) */}
          <div className="xl:col-span-4 2xl:col-span-3 space-y-3 flex flex-col h-full">
            {/* Multi-View Observation Switcher */}
            <div className="flex items-center justify-between bg-[#F2F4F7] p-1 rounded-lg text-xs font-semibold">
              <button
                onClick={() => setSidebarView('all')}
                className={`flex-1 py-1 px-2 rounded-md transition-all cursor-pointer text-center ${
                  sidebarView === 'all'
                    ? 'bg-white text-[#175CD3] shadow-xs font-bold'
                    : 'text-[#667085] hover:text-[#16202A]'
                }`}
              >
                Toàn cảnh
              </button>
              <button
                onClick={() => setSidebarView('dms')}
                className={`flex-1 py-1 px-2 rounded-md transition-all cursor-pointer text-center ${
                  sidebarView === 'dms'
                    ? 'bg-white text-[#175CD3] shadow-xs font-bold'
                    : 'text-[#667085] hover:text-[#16202A]'
                }`}
              >
                Cabin DMS
              </button>
              <button
                onClick={() => setSidebarView('events')}
                className={`flex-1 py-1 px-2 rounded-md transition-all cursor-pointer text-center flex items-center justify-center gap-1.5 ${
                  sidebarView === 'events'
                    ? 'bg-white text-[#175CD3] shadow-xs font-bold'
                    : 'text-[#667085] hover:text-[#16202A]'
                }`}
              >
                <span>Sự kiện</span>
                {events.length > 0 && (
                  <span className="px-1.5 py-0.2 rounded-full bg-[#175CD3] text-white text-[10px] font-mono">
                    {events.length}
                  </span>
                )}
              </button>
            </div>

            {(sidebarView === 'all' || sidebarView === 'dms') && (
              <CabinCameraViewport
                videoRef={driverVideoRef}
                driverResult={driverResult}
                isStreaming={sessionState === 'STREAMING'}
                isWebcamActive={isCabinWebcamActive}
                onToggleWebcam={handleToggleCabinWebcam}
                driverName={user?.full_name || 'Người Lái Xe'}
                driverId={user?.id || 1}
                driverPhone={user?.phone_number || '0901 234 567'}
                safetyScore={user?.safety_score ?? null}
                continuousMinutes={Math.floor(durationSeconds / 60)}
                onDmsEvent={handleClientDmsEvent}
              />
            )}

            {(sidebarView === 'all' || sidebarView === 'events') && (
              <RealtimeEventTimeline
                events={events}
                onConfirmEvent={handleConfirmEvent}
                onRejectEvent={handleRejectEvent}
                className={sidebarView === 'events' ? 'min-h-[520px]' : 'flex-1 min-h-[300px] xl:min-h-[360px]'}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
