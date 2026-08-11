import React, { useEffect, useRef } from 'react';
import { DetectionResult, BoundingBox } from '../../types/detection';

interface DetectionCanvasProps {
  result: DetectionResult | null;
  videoRef: React.RefObject<HTMLVideoElement | null>;
  showBoxes?: boolean;
  className?: string;
}

export function DetectionCanvas({ result, videoRef, showBoxes = true, className = '' }: DetectionCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Animation frame for smooth rendering without React state overhead
    let animationFrameId: number;

    const render = () => {
      // 1. Match Canvas logical size to Video element physical size
      const rect = video.getBoundingClientRect();
      if (canvas.width !== rect.width || canvas.height !== rect.height) {
        canvas.width = rect.width;
        canvas.height = rect.height;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (!result || !showBoxes) {
        animationFrameId = requestAnimationFrame(render);
        return;
      }

      // 2. Calculate scaling assuming object-fit: contain
      const videoRatio = video.videoWidth / video.videoHeight;
      const elementRatio = rect.width / rect.height;
      
      let renderWidth = rect.width;
      let renderHeight = rect.height;
      let offsetX = 0;
      let offsetY = 0;

      if (!isNaN(videoRatio)) {
        if (elementRatio > videoRatio) {
          // container is wider than video -> pillarboxed
          renderWidth = rect.height * videoRatio;
          offsetX = (rect.width - renderWidth) / 2;
        } else {
          // container is taller than video -> letterboxed
          renderHeight = rect.width / videoRatio;
          offsetY = (rect.height - renderHeight) / 2;
        }
      }

      const scaleX = renderWidth / (video.videoWidth || 1);
      const scaleY = renderHeight / (video.videoHeight || 1);

      const drawBox = (bbox: BoundingBox, color: string, label?: string) => {
        const x = offsetX + bbox.x1 * scaleX;
        const y = offsetY + bbox.y1 * scaleY;
        const w = (bbox.x2 - bbox.x1) * scaleX;
        const h = (bbox.y2 - bbox.y1) * scaleY;

        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, w, h);

        if (label) {
          ctx.fillStyle = color;
          ctx.font = '12px var(--font-sans)';
          const textWidth = ctx.measureText(label).width;
          ctx.fillRect(x, y - 20, textWidth + 8, 20);
          ctx.fillStyle = '#fff';
          ctx.fillText(label, x + 4, y - 5);
        }
      };

      // Draw Vehicles
      result.vehicles?.forEach(v => drawBox(v.bbox, '#5B8CFF', v.class));
      // Draw Plates
      result.plates?.forEach(p => drawBox(p.bbox, '#22C55E', p.plate_text));
      // Draw Helmet Violations
      result.helmet_violations?.forEach(h => drawBox(h.bbox, '#EF4444', 'No Helmet'));
      // Draw Traffic Signs
      result.traffic_signs?.forEach(t => {
        // Mocking bbox for traffic signs if backend doesn't provide it yet (assuming it will)
        // If no bbox, we skip drawing it on canvas and rely on UI alert
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [result, showBoxes, videoRef]);

  return (
    <canvas 
      ref={canvasRef} 
      className={`absolute top-0 left-0 w-full h-full pointer-events-none ${className}`} 
    />
  );
}
