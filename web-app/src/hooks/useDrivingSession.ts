import { useState, useCallback, useEffect } from 'react';
import { useRoadDrivingSocket } from './useRoadDrivingSocket';
import { useDriverMonitorSocket } from './useDriverMonitorSocket';
import { deriveDrivingUIState, DrivingUIState } from '../lib/driving/alert-engine';

export type SessionState = 'IDLE' | 'PREPARING' | 'CONNECTING' | 'STREAMING' | 'PAUSED' | 'STOPPING' | 'ENDED' | 'ERROR';

interface UseDrivingSessionProps {
  useDriverCamera: boolean;
}

export function useDrivingSession({ useDriverCamera }: UseDrivingSessionProps) {
  const [sessionState, setSessionState] = useState<SessionState>('IDLE');
  
  const roadSocket = useRoadDrivingSocket();
  const driverSocket = useDriverMonitorSocket();

  const [uiState, setUiState] = useState<DrivingUIState>({
    priority: 'NORMAL',
    message: 'Safe Driving',
    recommendedSpeed: null,
    safeDistance: null
  });

  // Calculate UI State every time results or stale flags change
  useEffect(() => {
    const nextState = deriveDrivingUIState(
      roadSocket.result,
      driverSocket.result,
      roadSocket.isStale,
      useDriverCamera ? driverSocket.isStale : false
    );
    setUiState(nextState);
  }, [
    roadSocket.result, 
    driverSocket.result, 
    roadSocket.isStale, 
    driverSocket.isStale,
    useDriverCamera
  ]);

  const startSession = useCallback(async () => {
    setSessionState('PREPARING');
    // Simulate permission request or initialization delay
    await new Promise(r => setTimeout(r, 500));
    
    setSessionState('CONNECTING');
    roadSocket.connect();
    if (useDriverCamera) {
      driverSocket.connect();
    }
    
    setSessionState('STREAMING');
  }, [roadSocket, driverSocket, useDriverCamera]);

  const pauseSession = useCallback(() => {
    setSessionState('PAUSED');
  }, []);

  const resumeSession = useCallback(() => {
    setSessionState('STREAMING');
  }, []);

  const stopSession = useCallback(() => {
    setSessionState('STOPPING');
    roadSocket.disconnect();
    driverSocket.disconnect();
    setSessionState('ENDED');
  }, [roadSocket, driverSocket]);

  return {
    sessionState,
    uiState,
    startSession,
    pauseSession,
    resumeSession,
    stopSession,
    roadSocket,
    driverSocket
  };
}
