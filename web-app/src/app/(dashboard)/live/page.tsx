'use client';

import React, { useRef, useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { AlertBanner } from '../../../components/ui/AlertBanner';
import { useDrivingSession } from '../../../hooks/useDrivingSession';
import { DetectionCanvas } from '../../../components/driving/DetectionCanvas';
import { Car, Play, Square, Activity, AlertTriangle, User } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

export default function LiveMonitorPage() {
  const [useDriverCam, setUseDriverCam] = useState(false);
  const roadVideoRef = useRef<HTMLVideoElement>(null);
  const driverVideoRef = useRef<HTMLVideoElement>(null);
  
  const {
    sessionState,
    uiState,
    startSession,
    stopSession,
    roadSocket,
    driverSocket
  } = useDrivingSession({ useDriverCamera: useDriverCam });

  // Access user's webcam for real live monitoring
  useEffect(() => {
    let roadStream: MediaStream | null = null;
    let driverStream: MediaStream | null = null;

    if (sessionState === 'PREPARING' || sessionState === 'STREAMING') {
      navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
        .then(stream => {
          roadStream = stream;
          if (roadVideoRef.current) {
            roadVideoRef.current.srcObject = stream;
            roadVideoRef.current.play();
          }
        })
        .catch(err => console.error("Could not access road camera:", err));

      if (useDriverCam) {
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
          .then(stream => {
            driverStream = stream;
            if (driverVideoRef.current) {
              driverVideoRef.current.srcObject = stream;
              driverVideoRef.current.play();
            }
          })
          .catch(err => console.error("Could not access driver camera:", err));
      }
    }

    return () => {
      if (roadStream) roadStream.getTracks().forEach(t => t.stop());
      if (driverStream) driverStream.getTracks().forEach(t => t.stop());
    };
  }, [sessionState, useDriverCam]);

  // Frame sending for Road Camera
  useEffect(() => {
    if (sessionState !== 'STREAMING' || roadSocket.status !== 'CONNECTED' || !roadVideoRef.current) return;

    let isRunning = true;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    const captureAndSend = () => {
      if (!isRunning) return;
      if (ctx && roadVideoRef.current?.videoWidth) {
        canvas.width = 640;
        canvas.height = 360;
        ctx.drawImage(roadVideoRef.current, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(blob => {
          if (blob && isRunning) roadSocket.sendFrame(blob);
        }, 'image/jpeg', 0.7);
      }
      setTimeout(captureAndSend, 100); 
    };

    captureAndSend();

    return () => { isRunning = false; };
  }, [sessionState, roadSocket]);

  // Frame sending for Driver Camera
  useEffect(() => {
    if (sessionState !== 'STREAMING' || !useDriverCam || driverSocket.status !== 'CONNECTED' || !driverVideoRef.current) return;

    let isRunning = true;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    const captureAndSend = () => {
      if (!isRunning) return;
      if (ctx && driverVideoRef.current?.videoWidth) {
        canvas.width = 640;
        canvas.height = 360;
        ctx.drawImage(driverVideoRef.current, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(blob => {
          if (blob && isRunning) driverSocket.sendFrame(blob);
        }, 'image/jpeg', 0.7);
      }
      setTimeout(captureAndSend, 100); 
    };

    captureAndSend();

    return () => { isRunning = false; };
  }, [sessionState, useDriverCam, driverSocket]);

  return (
    <div className="flex flex-col h-full gap-4 relative">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-adas-text-primary">Live Monitor</h1>
          <p className="text-adas-text-secondary text-sm">Realtime telemetry and video streams</p>
        </div>
        <div className="flex items-center gap-3">
          {sessionState === 'IDLE' || sessionState === 'ENDED' ? (
            <Button variant="success" onClick={startSession}>
              <Play className="w-4 h-4 mr-2" /> Start Live Session
            </Button>
          ) : (
            <Button variant="danger" onClick={stopSession}>
              <Square className="w-4 h-4 mr-2" /> End Session
            </Button>
          )}
        </div>
      </div>

      <div className="flex gap-4">
        <label className="flex items-center gap-2 text-adas-text-secondary cursor-pointer">
          <input 
            type="checkbox" 
            checked={useDriverCam} 
            onChange={(e) => setUseDriverCam(e.target.checked)}
            disabled={sessionState !== 'IDLE'}
            className="rounded border-adas-border bg-adas-surface text-adas-primary"
          />
          Enable Driver Camera (DMS)
        </label>
      </div>

      {uiState.priority !== 'NORMAL' && uiState.priority !== 'UNAVAILABLE' && (
        <AlertBanner 
          variant={
            uiState.priority === 'COLLISION_DANGER' ? 'danger' : 
            uiState.priority === 'DROWSINESS' ? 'danger' :
            uiState.priority === 'COLLISION_CAUTION' || uiState.priority === 'SPEED_WARNING' ? 'warning' : 'info'
          }
          title={uiState.message}
          className="shrink-0"
        />
      )}

      <div className="flex flex-1 gap-6 min-h-0">
        {/* Left Col: Cameras */}
        <div className="flex-1 flex flex-col gap-4">
          <Card className="flex-[2] overflow-hidden relative bg-black flex flex-col">
            <div className="absolute top-4 left-4 z-10 flex gap-2">
               <Badge variant={roadSocket.status === 'CONNECTED' ? 'success' : 'default'}>Road: {roadSocket.status}</Badge>
            </div>
            <div className="flex-1 relative">
              <video 
                ref={roadVideoRef}
                className="w-full h-full object-contain"
                muted
                playsInline
              />
              <DetectionCanvas 
                videoRef={roadVideoRef} 
                result={roadSocket.result} 
              />
            </div>
          </Card>

          {useDriverCam && (
            <Card className="flex-1 overflow-hidden relative bg-black flex flex-col">
              <div className="absolute top-4 left-4 z-10 flex gap-2">
                 <Badge variant={driverSocket.status === 'CONNECTED' ? 'success' : 'default'}>DMS: {driverSocket.status}</Badge>
              </div>
              <div className="flex-1 relative">
                <video 
                  ref={driverVideoRef}
                  className="w-full h-full object-contain"
                  muted
                  playsInline
                />
                {/* Note: In a real app you might draw facial landmarks here if your driver result includes them */}
              </div>
            </Card>
          )}
        </div>

        {/* Right Col: Telemetry */}
        <div className="w-80 shrink-0 flex flex-col gap-4 overflow-y-auto custom-scrollbar">
          <Card>
            <CardHeader>
              <CardTitle>Road Telemetry</CardTitle>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-adas-text-secondary">Vehicle Count</span>
                <span className="font-bold text-adas-text-primary">
                  {roadSocket.result?.vehicles?.length || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-adas-text-secondary">Safe Distance</span>
                <span className="font-bold text-adas-text-primary">
                  {uiState.safeDistance ? `${uiState.safeDistance.toFixed(1)}m` : '-'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-adas-text-secondary">Speed Advice</span>
                <span className="font-bold text-adas-text-primary">
                  {uiState.recommendedSpeed ? `${uiState.recommendedSpeed} km/h` : '-'}
                </span>
              </div>
            </CardContent>
          </Card>

          {useDriverCam && (
            <Card>
              <CardHeader>
                <CardTitle>Driver Status</CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-adas-text-secondary">Drowsiness</span>
                  {driverSocket.result?.drowsiness?.is_drowsy ? (
                    <Badge variant="danger">Detected</Badge>
                  ) : (
                    <Badge variant="success">Normal</Badge>
                  )}
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-adas-text-secondary">EAR Value</span>
                  <span className="font-bold text-adas-text-primary">
                    {driverSocket.result?.drowsiness?.ear_value?.toFixed(2) || '-'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-adas-text-secondary">Seatbelt</span>
                  {driverSocket.result?.seatbelt?.seatbelt_on ? (
                    <Badge variant="success">Fastened</Badge>
                  ) : driverSocket.result ? (
                    <Badge variant="danger">Unfastened</Badge>
                  ) : (
                    <span className="text-adas-text-muted">-</span>
                  )}
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-adas-text-secondary">Driving Time</span>
                  <span className="font-bold text-adas-text-primary">
                    {driverSocket.result?.driving_time?.continuous_minutes?.toFixed(0) || 0} mins
                  </span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
