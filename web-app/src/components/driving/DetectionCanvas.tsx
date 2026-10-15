import React, { useEffect, useRef } from 'react';
import { DetectionResult, BoundingBox, sanitizeVietnamesePlate } from '../../types/detection';

interface DetectionCanvasProps {
  result: DetectionResult | null;
  videoRef?: React.RefObject<HTMLVideoElement | null>;
  mediaRef?: React.RefObject<HTMLElement | null>;
  showBoxes?: boolean;
  activeTab?: 'plates' | 'traffic' | 'signs' | 'helmets';
  sourceMode?: 'video' | 'camera' | 'webcam' | 'image';
  className?: string;
  showDistanceZones?: boolean;
  warnThreshold?: number;
  dangerThreshold?: number;
  focalLength?: number;
  zoneLeft?: any;
  zoneFront?: any;
  zoneRight?: any;
  trackedVehicles?: any[];
  activeZones?: { L: boolean; F: boolean; R: boolean };
}

export function DetectionCanvas({
  result,
  videoRef,
  mediaRef,
  showBoxes = true,
  activeTab,
  sourceMode,
  className = '',
  showDistanceZones = true,
  warnThreshold = 8,
  dangerThreshold = 4,
  focalLength = 520,
  zoneLeft,
  zoneFront,
  zoneRight,
  trackedVehicles = [],
  activeZones = { L: true, F: true, R: true },
}: DetectionCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const media = (mediaRef?.current || videoRef?.current) as (HTMLVideoElement | HTMLImageElement | null);
    if (!canvas || !media) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;

    const render = () => {
      // 1. Match Canvas logical size to Media element physical bounding rect
      const rect = media.getBoundingClientRect();
      if (canvas.width !== rect.width || canvas.height !== rect.height) {
        canvas.width = rect.width;
        canvas.height = rect.height;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const mWidth = (media as HTMLVideoElement).videoWidth || (media as HTMLImageElement).naturalWidth || result?.frame_width || 0;
      const mHeight = (media as HTMLVideoElement).videoHeight || (media as HTMLImageElement).naturalHeight || result?.frame_height || 0;

      if (!result || !showBoxes || (!mWidth && !mHeight)) {
        animationFrameId = requestAnimationFrame(render);
        return;
      }

      // 2. Calculate scaling assuming object-fit: contain
      const videoRatio = (mWidth && mHeight) ? (mWidth / mHeight) : (16 / 9);
      const elementRatio = rect.width / (rect.height || 1);

      let renderWidth = rect.width;
      let renderHeight = rect.height;
      let offsetX = 0;
      let offsetY = 0;

      if (!isNaN(videoRatio) && videoRatio > 0) {
        if (elementRatio > videoRatio) {
          // Container is wider than video -> pillarboxed (black bars left & right)
          renderWidth = rect.height * videoRatio;
          offsetX = (rect.width - renderWidth) / 2;
        } else {
          // Container is taller than video -> letterboxed (black bars top & bottom)
          renderHeight = rect.width / videoRatio;
          offsetY = (rect.height - renderHeight) / 2;
        }
      }

      // Use the exact dimensions processed by the server, including resizing.
      const srcW = result.frame_width || mWidth || 640;
      const srcH = result.frame_height || mHeight || 360;

      const scaleX = renderWidth / srcW;
      const scaleY = renderHeight / srcH;

      const drawReticleBox = (
        bbox: BoundingBox,
        theme: {
          stroke: string;
          glow: string;
          fill: string;
          badgeBg: string;
          badgeText: string;
        },
        options: {
          icon?: string;
          title: string;
          subtitle?: string;
          plateText?: string | null;
          isPlateConfirmed?: boolean;
          isPlateBox?: boolean;
        }
      ) => {
        if (!bbox) return;

        const x = offsetX + bbox.x1 * scaleX;
        const y = offsetY + bbox.y1 * scaleY;
        const w = (bbox.x2 - bbox.x1) * scaleX;
        const h = (bbox.y2 - bbox.y1) * scaleY;

        if (w <= 0 || h <= 0) return;

        ctx.save();

        // 1. Box outline & subtle futuristic gradient fill
        ctx.strokeStyle = theme.stroke;
        ctx.lineWidth = options.isPlateBox ? 2 : 1.5;
        ctx.strokeRect(x, y, w, h);

        ctx.fillStyle = theme.fill;
        ctx.fillRect(x, y, w, h);

        // 2. Futuristic Corner Reticles
        const cornerLen = Math.min(12, w / 3, h / 3);
        ctx.lineWidth = 3;
        ctx.strokeStyle = theme.glow;
        ctx.lineCap = 'round';

        // Top-left
        ctx.beginPath();
        ctx.moveTo(x, y + cornerLen);
        ctx.lineTo(x, y);
        ctx.lineTo(x + cornerLen, y);
        ctx.stroke();

        // Top-right
        ctx.beginPath();
        ctx.moveTo(x + w - cornerLen, y);
        ctx.lineTo(x + w, y);
        ctx.lineTo(x + w, y + cornerLen);
        ctx.stroke();

        // Bottom-left
        ctx.beginPath();
        ctx.moveTo(x, y + h - cornerLen);
        ctx.lineTo(x, y + h);
        ctx.lineTo(x + cornerLen, y + h);
        ctx.stroke();

        // Bottom-right
        ctx.beginPath();
        ctx.moveTo(x + w - cornerLen, y + h);
        ctx.lineTo(x + w, y + h);
        ctx.lineTo(x + w, y + h - cornerLen);
        ctx.stroke();

        // 3. Modern Glassmorphism Pill Badges
        const hasPlate = !!options.plateText;
        const mainText = `${options.icon ? options.icon + ' ' : ''}${options.title}${options.subtitle ? ' • ' + options.subtitle : ''}`;

        ctx.font = '600 11px Inter, system-ui, -apple-system, sans-serif';
        const mainWidth = ctx.measureText(mainText).width;

        let plateWidth = 0;
        let plateLabel = '';
        if (hasPlate) {
          ctx.font = 'bold 11px monospace, Inter';
          plateLabel = `🪪 ${options.plateText}${options.isPlateConfirmed === false ? ' (Đang quét...)' : ''}`;
          plateWidth = ctx.measureText(plateLabel).width;
        }

        const badgeHeight = 22;
        const plateBadgeHeight = 18;
        const totalHeight = hasPlate && !options.isPlateBox ? badgeHeight + plateBadgeHeight + 3 : badgeHeight;
        const badgeY = y >= totalHeight + 4 ? y - totalHeight - 4 : y + 4;

        // Draw Main Vehicle Pill Badge
        const mainPillW = mainWidth + 14;
        ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
        ctx.strokeStyle = theme.stroke;
        ctx.lineWidth = 1;

        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(x, badgeY, mainPillW, badgeHeight, 5);
        } else {
          ctx.rect(x, badgeY, mainPillW, badgeHeight);
        }
        ctx.fill();
        ctx.stroke();

        // Little status indicator light
        ctx.fillStyle = theme.glow;
        ctx.beginPath();
        ctx.arc(x + 7, badgeY + badgeHeight / 2, 2.5, 0, Math.PI * 2);
        ctx.fill();

        // Main Text
        ctx.font = '600 11px Inter, system-ui, -apple-system, sans-serif';
        ctx.fillStyle = '#F8FAFC';
        ctx.textBaseline = 'middle';
        ctx.fillText(mainText, x + 13, badgeY + badgeHeight / 2);

        // Draw Secondary Plate Badge (Pinned directly below or beside)
        if (hasPlate && !options.isPlateBox) {
          const platePillW = plateWidth + 12;
          const plateY = badgeY + badgeHeight + 2;
          const isConfirmed = options.isPlateConfirmed !== false;

          ctx.fillStyle = isConfirmed ? 'rgba(6, 78, 59, 0.95)' : 'rgba(120, 53, 15, 0.95)';
          ctx.strokeStyle = isConfirmed ? '#10B981' : '#F59E0B';
          ctx.lineWidth = 1.2;

          ctx.beginPath();
          if (ctx.roundRect) {
            ctx.roundRect(x, plateY, platePillW, plateBadgeHeight, 4);
          } else {
            ctx.rect(x, plateY, platePillW, plateBadgeHeight);
          }
          ctx.fill();
          ctx.stroke();

          ctx.font = 'bold 11px monospace, Inter';
          ctx.fillStyle = '#FFFFFF';
          ctx.textBaseline = 'middle';
          ctx.fillText(plateLabel, x + 6, plateY + plateBadgeHeight / 2);
        }

        ctx.restore();
      };



      // 0. Draw Perspective 3-Zone ADAS Highway Corridor & Distance Guide Lines
      if (showDistanceZones && (!activeTab || activeTab === 'traffic')) {
        ctx.save();
        const HZ = offsetY + renderHeight * 0.46;
        const CX = offsetX + renderWidth * 0.50;
        const CAMH = 1.3;
        const F0 = (focalLength || 520) * (renderHeight / 720.0);

        const project = (X: number, Z: number): [number, number] => {
          const px = CX + (F0 * X) / Z;
          const py = HZ + (F0 * CAMH) / Z;
          return [px, py];
        };

        const zMin = 3.2;
        const zMax = 28.0;

        const isLeftOn = activeZones.L !== false;
        const isFrontOn = activeZones.F !== false;
        const isRightOn = activeZones.R !== false;

        // Vạch phân vùng làn đường phối cảnh (tự động mờ khi tắt vùng)
        const laneBoundaries = [
          { X: -3.8, stroke: isLeftOn ? 'rgba(245, 158, 11, 0.45)' : 'rgba(148, 163, 184, 0.15)', dash: [6, 6] },
          { X: -1.35, stroke: (isLeftOn || isFrontOn) ? 'rgba(59, 130, 246, 0.70)' : 'rgba(148, 163, 184, 0.15)', dash: [8, 6] },
          { X: 1.35, stroke: (isRightOn || isFrontOn) ? 'rgba(59, 130, 246, 0.70)' : 'rgba(148, 163, 184, 0.15)', dash: [8, 6] },
          { X: 3.8, stroke: isRightOn ? 'rgba(16, 185, 129, 0.45)' : 'rgba(148, 163, 184, 0.15)', dash: [6, 6] },
        ];

        laneBoundaries.forEach((lb) => {
          ctx.strokeStyle = lb.stroke;
          ctx.lineWidth = 1.8;
          ctx.setLineDash(lb.dash);
          ctx.beginPath();
          const pStart = project(lb.X, zMin);
          const pEnd = project(lb.X, zMax);
          ctx.moveTo(pStart[0], Math.min(offsetY + renderHeight, pStart[1]));
          ctx.lineTo(pEnd[0], pEnd[1]);
          ctx.stroke();
        });

        // Vạch cự ly nguy hiểm cắt ngang đường (dangerThreshold) - chỉ sáng khi vùng trước bật
        const dZ = dangerThreshold || 4.0;
        const pRedL = project(-1.35, dZ);
        const pRedR = project(1.35, dZ);
        ctx.setLineDash([]);
        ctx.strokeStyle = isFrontOn ? 'rgba(239, 68, 68, 0.90)' : 'rgba(148, 163, 184, 0.25)';
        ctx.lineWidth = isFrontOn ? 2.5 : 1.5;
        ctx.beginPath();
        ctx.moveTo(pRedL[0], pRedL[1]);
        ctx.lineTo(pRedR[0], pRedR[1]);
        ctx.stroke();

        ctx.font = 'bold 10px monospace, Inter';
        ctx.fillStyle = isFrontOn ? '#EF4444' : 'rgba(148, 163, 184, 0.4)';
        ctx.fillText(`${isFrontOn ? '🚨 ' : ''}${dZ}m`, pRedR[0] + 6, pRedR[1] + 3);

        // Vạch cự ly cảnh báo cắt ngang đường (warnThreshold)
        const wZ = warnThreshold || 8.5;
        const pWarnL = project(-1.35, wZ);
        const pWarnR = project(1.35, wZ);
        ctx.strokeStyle = isFrontOn ? 'rgba(245, 158, 11, 0.80)' : 'rgba(148, 163, 184, 0.20)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(pWarnL[0], pWarnL[1]);
        ctx.lineTo(pWarnR[0], pWarnR[1]);
        ctx.stroke();

        ctx.fillStyle = isFrontOn ? '#F59E0B' : 'rgba(148, 163, 184, 0.4)';
        ctx.fillText(`${isFrontOn ? '⚠ ' : ''}${wZ}m`, pWarnR[0] + 6, pWarnR[1] + 3);

        // Vạch cự ly an toàn (16m)
        const sZ = 16.0;
        const pSafeL = project(-1.35, sZ);
        const pSafeR = project(1.35, sZ);
        ctx.strokeStyle = isFrontOn ? 'rgba(16, 185, 129, 0.65)' : 'rgba(148, 163, 184, 0.20)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(pSafeL[0], pSafeL[1]);
        ctx.lineTo(pSafeR[0], pSafeR[1]);
        ctx.stroke();

        ctx.fillStyle = isFrontOn ? '#10B981' : 'rgba(148, 163, 184, 0.4)';
        ctx.fillText(`✓ 16m`, pSafeR[0] + 6, pSafeR[1] + 3);

        // Nhãn tên vùng phối cảnh trên mặt đường
        ctx.font = 'bold 10px Inter, sans-serif';
        const pLeftTag = project(-2.5, 6.5);
        ctx.fillStyle = isLeftOn ? 'rgba(245, 158, 11, 0.85)' : 'rgba(148, 163, 184, 0.40)';
        ctx.fillText(isLeftOn ? 'VÙNG TRÁI' : 'TRÁI (TẮT)', pLeftTag[0] - 25, pLeftTag[1]);

        const pFrontTag = project(0, 10.5);
        ctx.fillStyle = isFrontOn ? 'rgba(59, 130, 246, 0.90)' : 'rgba(148, 163, 184, 0.40)';
        ctx.fillText(isFrontOn ? 'PHÍA TRƯỚC' : 'TRƯỚC (TẮT)', pFrontTag[0] - 28, pFrontTag[1]);

        const pRightTag = project(2.5, 6.5);
        ctx.fillStyle = isRightOn ? 'rgba(16, 185, 129, 0.85)' : 'rgba(148, 163, 184, 0.40)';
        ctx.fillText(isRightOn ? 'VÙNG PHẢI' : 'PHẢI (TẮT)', pRightTag[0] - 25, pRightTag[1]);

        ctx.restore();
      }

      // 0b. Draw Virtual Line Crossing Counting Line on Road Video Overlay (IN / OUT)
      if (activeTab === 'traffic') {
        ctx.save();
        const lineY = offsetY + renderHeight * 0.60;
        const lineX1 = offsetX + renderWidth * 0.08;
        const lineX2 = offsetX + renderWidth * 0.92;

        ctx.strokeStyle = '#06B6D4';
        ctx.lineWidth = 2;
        ctx.setLineDash([8, 6]);
        ctx.beginPath();
        ctx.moveTo(lineX1, lineY);
        ctx.lineTo(lineX2, lineY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Badge on left
        const inCount = result.line_crossings?.in_count || 0;
        const outCount = result.line_crossings?.out_count || 0;
        const tagText = `━━━ LINE CROSSING ━━━ IN: ${inCount} ⬇ | OUT: ${outCount} ⬆`;
        ctx.font = 'bold 10px monospace, Inter';
        ctx.fillStyle = 'rgba(12, 17, 29, 0.88)';
        const tagW = ctx.measureText(tagText).width + 12;
        if (ctx.roundRect) {
          ctx.beginPath();
          ctx.roundRect(lineX1, lineY - 18, tagW, 16, 4);
          ctx.fill();
          ctx.stroke();
        } else {
          ctx.fillRect(lineX1, lineY - 18, tagW, 16);
          ctx.strokeRect(lineX1, lineY - 18, tagW, 16);
        }
        ctx.fillStyle = '#22D3EE';
        ctx.fillText(tagText, lineX1 + 6, lineY - 6);
        ctx.restore();
      }

      // 1. Draw Vehicles (Multi-Vehicle simultaneous rendering)
      // CHỈ vẽ phương tiện khi ở tab 'traffic' (Mật độ giao thông) hoặc không chỉ định tab
      // Khi ở tab 'signs' (Biển báo), 'plates' (Biển số), 'helmets' (Mũ bảo hiểm) -> TUYỆT ĐỐI KHÔNG VẼ XE!
      if (!activeTab || activeTab === 'traffic') {
        result.vehicles?.forEach((v) => {
          const clsName = ((v as any).class_name || (v as any).class || 'Xe').toLowerCase();
          let displayLabel = 'Phương tiện';
          let icon = '🚗';
          let theme = {
            stroke: '#06B6D4', // Neon Cyan
            glow: '#22D3EE',
            fill: 'rgba(6, 182, 212, 0.08)',
            badgeBg: 'rgba(15, 23, 42, 0.90)',
            badgeText: '#F8FAFC',
          };

          if (clsName === 'car') {
            displayLabel = 'Ô tô';
            icon = '🚗';
            theme = {
              stroke: '#06B6D4',
              glow: '#00F2FE',
              fill: 'rgba(6, 182, 212, 0.08)',
              badgeBg: 'rgba(15, 23, 42, 0.90)',
              badgeText: '#F8FAFC',
            };
          } else if (clsName === 'truck') {
            displayLabel = 'Xe tải';
            icon = '🚚';
            theme = {
              stroke: '#38BDF8',
              glow: '#60A5FA',
              fill: 'rgba(56, 189, 248, 0.08)',
              badgeBg: 'rgba(15, 23, 42, 0.90)',
              badgeText: '#F8FAFC',
            };
          } else if (clsName === 'bus') {
            displayLabel = 'Xe buýt';
            icon = '🚌';
            theme = {
              stroke: '#818CF8',
              glow: '#A5B4FC',
              fill: 'rgba(129, 140, 248, 0.08)',
              badgeBg: 'rgba(15, 23, 42, 0.90)',
              badgeText: '#F8FAFC',
            };
          } else if (clsName === 'motorbike' || clsName === 'motorcycle') {
            displayLabel = 'Xe máy';
            icon = '🏍️';
            theme = {
              stroke: '#C084FC', // Neon Purple
              glow: '#E879F9',
              fill: 'rgba(192, 132, 252, 0.08)',
              badgeBg: 'rgba(15, 23, 42, 0.90)',
              badgeText: '#F8FAFC',
            };
          } else if (clsName === 'bicycle') {
            displayLabel = 'Xe đạp';
            icon = '🚲';
            theme = {
              stroke: '#34D399',
              glow: '#6EE7B7',
              fill: 'rgba(52, 211, 153, 0.08)',
              badgeBg: 'rgba(15, 23, 42, 0.90)',
              badgeText: '#F8FAFC',
            };
          } else if (clsName === 'person') {
            displayLabel = 'Người đi bộ';
            icon = '🚶';
            theme = {
              stroke: '#FBBF24', // Neon Amber
              glow: '#FDE68A',
              fill: 'rgba(251, 191, 36, 0.08)',
              badgeBg: 'rgba(15, 23, 42, 0.90)',
              badgeText: '#F8FAFC',
            };
          }

          // Lấy thông tin mở rộng từ Radar Engine (TTC, Cự ly lọc mượt EMA, Tạt đầu)
          const matchTrk = trackedVehicles?.find((t: any) => t.id === v.id);
          const effectiveDist = matchTrk?.dist ?? v.distance_m;
          const trkLvl = matchTrk?.lvl;
          const ttc = matchTrk?.ttc ?? (v as any).ttc;
          const approachState = matchTrk?.approachState ?? (v as any).approachState;
          const approachDesc = matchTrk?.approachDesc ?? (v as any).approachDesc;

          // Đổi màu cảnh báo cự ly an toàn (ADAS Collision & Distance Reticle)
          const isDanger =
            trkLvl === 2 ||
            v.distance_status === 'NGUY_HIEM' ||
            (effectiveDist != null && effectiveDist < 4.5) ||
            (ttc != null && ttc <= 1.8) ||
            approachState === 'CUT_IN';

          const isWarning =
            !isDanger &&
            (trkLvl === 1 ||
              v.distance_status === 'CHU_Y' ||
              (effectiveDist != null && effectiveDist < 10.0) ||
              (ttc != null && ttc <= 3.2));

          if (isDanger) {
            theme = {
              stroke: '#EF4444',
              glow: '#F87171',
              fill: 'rgba(239, 68, 68, 0.18)',
              badgeBg: '#DC2626',
              badgeText: '#FFFFFF',
            };
          } else if (isWarning) {
            theme = {
              stroke: '#F59E0B',
              glow: '#FBBF24',
              fill: 'rgba(245, 158, 11, 0.15)',
              badgeBg: '#D97706',
              badgeText: '#FFFFFF',
            };
          }

          const isStaticImage = sourceMode === 'image' || (media && media.tagName === 'IMG');
          const isVideo = !isStaticImage;

          const title = v.id ? `${displayLabel} #${v.id}` : displayLabel;
          // Hiển thị cự ly đo được chuẩn xác (qua bộ lọc mượt nếu có)
          const distLabel = effectiveDist != null ? `Cự ly: ${effectiveDist.toFixed(1)}m` : undefined;
          // TUYỆT ĐỐI KHÔNG HIỂN THỊ TỐC ĐỘ TRÊN ẢNH TĨNH! Vận tốc chỉ đo trên video/camera thời gian thực.
          const speedLabel = isVideo && v.speed_kmh && v.speed_kmh > 0 ? `${Math.round(v.speed_kmh)} km/h` : undefined;
          const dirTag = v.direction === 'IN' ? '⬇ IN' : v.direction === 'OUT' ? '⬆ OUT' : '';
          const ttcLabel = isVideo && ttc != null && ttc > 0 && ttc <= 6.0 ? `TTC: ${ttc.toFixed(1)}s` : undefined;
          const cutInLabel = approachState === 'CUT_IN' ? '🚨 TẠT ĐẦU' : undefined;
          const approachTag = cutInLabel || (isVideo && approachDesc ? approachDesc : undefined);

          const parts = [distLabel, speedLabel, dirTag, ttcLabel, approachTag].filter(Boolean);
          const subtitle = parts.length > 0 ? parts.join(' • ') : undefined;

          // Ở tab 'traffic', TUYỆT ĐỐI KHÔNG hiển thị biển số xe để giữ giao diện tách biệt hoàn toàn!
          const rawPlate = activeTab === 'traffic' ? undefined : ((v as any).plate_text || (v as any).license_plate);
          const plate = rawPlate ? sanitizeVietnamesePlate(rawPlate) : undefined;
          const isConfirmed = (v as any).plate_status === 'CONFIRMED' || !(v as any).plate_status;

          drawReticleBox(v.bbox, theme, {
            icon,
            title,
            subtitle,
            plateText: plate,
            isPlateConfirmed: isConfirmed,
          });
        });
      }

      // 2. Draw Active Realtime Plates
      if (!activeTab || activeTab === 'plates') {
        result.plates?.forEach((p) => {
          if (!p.plate_text) return;
          const cleanPlate = sanitizeVietnamesePlate(p.plate_text);
          const isScanning = (p as any).status === 'UNCERTAIN' || (p.confidence !== undefined && p.confidence > 0 && p.confidence < 0.65);
          const theme = isScanning
            ? {
                stroke: '#F59E0B',
                glow: '#FBBF24',
                fill: 'rgba(245, 158, 11, 0.15)',
                badgeBg: '#D97706',
                badgeText: '#FFFFFF',
              }
            : {
                stroke: '#10B981',
                glow: '#34D399',
                fill: 'rgba(16, 185, 129, 0.18)',
                badgeBg: '#059669',
                badgeText: '#FFFFFF',
              };

          drawReticleBox(p.bbox, theme, {
            icon: '🪪',
            title: cleanPlate,
            subtitle: isScanning ? 'Đang quét...' : undefined,
            isPlateBox: true,
          });
        });
      }

      // 3. Draw Traffic Signs (Vẽ biển báo giao thông phát hiện được)
      if (!activeTab || activeTab === 'signs') {
        result.traffic_signs?.forEach((s) => {
          if (!s.bbox) return;
          const code = s.sign_type || 'Biển báo';
          const name = s.name ? `${code} • ${s.name}` : code;
          const isAuxiliary = code.startsWith('S.') || code.startsWith('S') || s.category === 'BIỂN PHỤ';
          const isProhibitory = code.startsWith('P.') || code.startsWith('P') || s.category === 'CẤM';
          const isWarning = code.startsWith('W.') || code.startsWith('W') || s.category === 'CẢNH BÁO';
          const isMandatory = code.startsWith('R.') || code.startsWith('R') || code.startsWith('DP') || s.category === 'HIỆU LỆNH';

          const theme = isAuxiliary
            ? {
                stroke: '#8B5CF6',
                glow: '#A78BFA',
                fill: 'rgba(139, 92, 246, 0.18)',
                badgeBg: '#7C3AED',
                badgeText: '#FFFFFF',
              }
            : isProhibitory
            ? {
                stroke: '#EF4444',
                glow: '#F87171',
                fill: 'rgba(239, 68, 68, 0.15)',
                badgeBg: '#DC2626',
                badgeText: '#FFFFFF',
              }
            : isWarning
            ? {
                stroke: '#F59E0B',
                glow: '#FBBF24',
                fill: 'rgba(245, 158, 11, 0.15)',
                badgeBg: '#D97706',
                badgeText: '#FFFFFF',
              }
            : isMandatory
            ? {
                stroke: '#0284C7',
                glow: '#38BDF8',
                fill: 'rgba(2, 132, 199, 0.15)',
                badgeBg: '#0369A1',
                badgeText: '#FFFFFF',
              }
            : {
                stroke: '#10B981',
                glow: '#34D399',
                fill: 'rgba(16, 185, 129, 0.15)',
                badgeBg: '#059669',
                badgeText: '#FFFFFF',
              };

          const subtitle = s.time_window
            ? `Giờ cấm: ${s.time_window}`
            : s.speed_limit
            ? `Tối đa ${s.speed_limit} km/h`
            : (s.action_required ? s.action_required.slice(0, 36) : undefined);

          drawReticleBox(s.bbox, theme, {
            icon: isAuxiliary ? '⏱️' : isProhibitory ? '⛔' : isWarning ? '⚠️' : isMandatory ? 'ℹ️' : '🛣️',
            title: isAuxiliary ? `${code} • ${s.name || 'Biển phụ'}` : name,
            subtitle,
          });
        });
      }

      // 4. Draw Helmet Violations
      if (!activeTab || activeTab === 'helmets') {
        result.helmet_violations?.forEach((h) => {
          const title = h.plate_text ? `Không mũ: ${h.plate_text}` : 'Không đội mũ bảo hiểm';
          const theme = {
            stroke: '#EF4444',
            glow: '#F87171',
            fill: 'rgba(239, 68, 68, 0.18)',
            badgeBg: '#DC2626',
            badgeText: '#FFFFFF',
          };

          drawReticleBox(h.bbox, theme, {
            icon: '⚠',
            title,
          });
        });
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [
    result,
    showBoxes,
    videoRef,
    mediaRef,
    activeTab,
    showDistanceZones,
    warnThreshold,
    dangerThreshold,
    focalLength,
    zoneLeft,
    zoneFront,
    zoneRight,
    trackedVehicles,
  ]);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 w-full h-full pointer-events-none ${className}`}
    />
  );
}
