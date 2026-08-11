'use client';

import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { AlertBanner } from '../../../components/ui/AlertBanner';
import { useDrivingSession } from '../../../hooks/useDrivingSession';
import { DetectionCanvas } from '../../../components/driving/DetectionCanvas';
import { Car, Play, Square, Pause, AlertTriangle, Monitor, Upload, Settings } from 'lucide-react';

export default function SimulatorPage() {
  const [speed, setSpeed] = useState<number>(50);
  const [videoSrc, setVideoSrc] = useState<string>('');
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const {
    sessionState,
    uiState,
    startSession,
    pauseSession,
    resumeSession,
    stopSession,
    roadSocket
  } = useDrivingSession({ useDriverCamera: false }); // Simulator focusing on Road for now

  // Frame sending loop
  useEffect(() => {
    if (sessionState !== 'STREAMING' || roadSocket.status !== 'CONNECTED' || !videoRef.current) return;

    let isRunning = true;
    const video = videoRef.current;
    
    // Create an offscreen canvas for frame capture
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    const captureAndSend = () => {
      if (!isRunning || video.paused || video.ended) return;

      if (ctx) {
        // Limit resolution to save bandwidth (e.g., 640x360)
        canvas.width = 640;
        canvas.height = 360;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob(
          (blob) => {
            if (blob && isRunning) {
              roadSocket.sendFrame(blob);
            }
          },
          'image/jpeg',
          0.7
        );
      }
      
      // Throttle to roughly 10-15 FPS to avoid flooding (FIX P)
      setTimeout(captureAndSend, 100); 
    };

    captureAndSend();

    return () => {
      isRunning = false;
    };
  }, [sessionState, roadSocket]);

  // Speed metadata sender (FIX G)
  useEffect(() => {
    if (sessionState === 'STREAMING' && roadSocket.status === 'CONNECTED') {
      roadSocket.sendMetadata({ vehicle_speed: speed });
    }
  }, [speed, sessionState, roadSocket.status, roadSocket]);

  const handleVideoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setVideoSrc(url);
    }
  };

  const handleStart = async () => {
    if (videoRef.current) {
      videoRef.current.play();
    }
    await startSession();
  };

  const handleStop = () => {
    if (videoRef.current) {
      videoRef.current.pause();
    }
    stopSession();
  };

  return (
    <div className="flex flex-col h-full gap-4 relative">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-adas-text-primary">Simulator Mode</h1>
          <p className="text-adas-text-secondary text-sm">Test AI Engine with video files and simulated speed</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={roadSocket.status === 'CONNECTED' ? 'success' : 'warning'}>
            Road AI: {roadSocket.status}
          </Badge>
          <Badge variant={sessionState === 'STREAMING' ? 'success' : 'default'}>
            Session: {sessionState}
          </Badge>
        </div>
      </div>

      {uiState.priority !== 'NORMAL' && uiState.priority !== 'UNAVAILABLE' && (
        <AlertBanner 
          variant={
            uiState.priority === 'COLLISION_DANGER' ? 'danger' : 
            uiState.priority === 'COLLISION_CAUTION' || uiState.priority === 'SPEED_WARNING' ? 'warning' : 'info'
          }
          title={uiState.message}
          className="shrink-0"
        >
          {uiState.safeDistance && <p>Distance: {uiState.safeDistance.toFixed(1)}m</p>}
        </AlertBanner>
      )}

      {uiState.priority === 'UNAVAILABLE' && sessionState === 'STREAMING' && (
        <AlertBanner variant="warning" title={uiState.message} className="shrink-0">
          Waiting for AI inference results...
        </AlertBanner>
      )}

      <div className="flex flex-1 gap-6 min-h-0">
        {/* Main Road View */}
        <div className="flex-1 flex flex-col gap-4">
          <Card className="flex-1 overflow-hidden relative bg-black border-2 border-adas-border flex flex-col">
            <div className="flex-1 relative">
              {!videoSrc ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-adas-text-muted">
                  <Monitor className="w-16 h-16 mb-4 opacity-50" />
                  <p>Upload a video to start simulation</p>
                  <label className="mt-4 cursor-pointer">
                    <span className="bg-adas-surface hover:bg-adas-elevated border border-adas-border px-4 py-2 rounded-xl text-adas-text-primary text-sm flex items-center gap-2">
                      <Upload className="w-4 h-4" /> Select Video
                    </span>
                    <input type="file" accept="video/*" className="hidden" onChange={handleVideoUpload} />
                  </label>
                </div>
              ) : (
                <>
                  <video 
                    ref={videoRef}
                    src={videoSrc}
                    className="w-full h-full object-contain"
                    loop
                    muted
                    playsInline
                  />
                  <DetectionCanvas 
                    videoRef={videoRef} 
                    result={roadSocket.result} 
                    showBoxes={true}
                  />
                  
                  {/* Takeover UI for Collision */}
                  {uiState.priority === 'COLLISION_DANGER' && (
                    <div className="absolute inset-0 pointer-events-none bg-adas-danger/20 flex flex-col items-center justify-center">
                      {/* Using subtle pulse instead of rapid flashing as per FIX I */}
                      <div className="bg-adas-danger/90 text-white px-8 py-6 rounded-3xl animate-pulse shadow-[0_0_40px_rgba(239,68,68,0.6)] text-center">
                        <AlertTriangle className="w-20 h-20 mx-auto mb-2" />
                        <h2 className="text-4xl font-black tracking-wider">BRAKE NOW</h2>
                        <p className="text-xl font-bold mt-2">COLLISION RISK</p>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </Card>
        </div>

        {/* Sidebar Controls */}
        <div className="w-80 shrink-0 flex flex-col gap-4 overflow-y-auto custom-scrollbar">
          <Card>
            <CardContent className="p-5 flex flex-col gap-6">
              <div>
                <h3 className="font-semibold text-adas-text-primary mb-4 flex items-center gap-2">
                  <Settings className="w-4 h-4 text-adas-text-muted" /> Simulator Controls
                </h3>
                
                <div className="flex gap-2">
                  {sessionState === 'IDLE' || sessionState === 'ENDED' ? (
                    <Button 
                      className="flex-1" 
                      variant="success" 
                      onClick={handleStart}
                      disabled={!videoSrc}
                    >
                      <Play className="w-4 h-4 mr-2" /> Start
                    </Button>
                  ) : (
                    <Button className="flex-1" variant="danger" onClick={handleStop}>
                      <Square className="w-4 h-4 mr-2" /> Stop
                    </Button>
                  )}
                </div>
              </div>

              <div>
                <div className="flex justify-between items-end mb-2">
                  <label className="text-sm text-adas-text-secondary">Vehicle Speed</label>
                  <span className="text-xl font-bold text-adas-text-primary">{speed} <span className="text-sm font-normal text-adas-text-muted">km/h</span></span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="120" 
                  value={speed}
                  onChange={(e) => setSpeed(parseInt(e.target.value))}
                  className="w-full accent-adas-primary"
                />
              </div>

            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <h3 className="font-semibold text-adas-text-primary mb-4">AI Metrics</h3>
              
              <div className="space-y-4">
                <div className="flex justify-between items-center pb-3 border-b border-adas-border/50">
                  <span className="text-sm text-adas-text-secondary">Recommended</span>
                  <span className="font-bold text-adas-text-primary">
                    {uiState.recommendedSpeed ? `${uiState.recommendedSpeed} km/h` : '-'}
                  </span>
                </div>
                
                <div className="flex justify-between items-center pb-3 border-b border-adas-border/50">
                  <span className="text-sm text-adas-text-secondary">Safe Distance</span>
                  <span className="font-bold text-adas-text-primary">
                    {uiState.safeDistance ? `${uiState.safeDistance.toFixed(1)} m` : '-'}
                  </span>
                </div>

                <div className="flex justify-between items-center pb-3 border-b border-adas-border/50">
                  <span className="text-sm text-adas-text-secondary">Est. Throughput</span>
                  <span className="font-bold text-adas-text-primary">
                    {roadSocket.result?.processing_time_ms ? 
                      `${(1000 / roadSocket.result.processing_time_ms).toFixed(1)} FPS` 
                      : '-'}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-adas-text-secondary">Latency</span>
                  <span className="font-bold text-adas-text-primary">
                    {roadSocket.result?.processing_time_ms ? 
                      `${Math.round(roadSocket.result.processing_time_ms)} ms` 
                      : '-'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
