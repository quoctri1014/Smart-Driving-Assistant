import { useState, useEffect, useCallback, useRef } from 'react';
import { DriverMonitorResult } from '../types/detection';
import { soundEngine } from '../lib/soundEngine';

export type SocketStatus = 'IDLE' | 'CONNECTING' | 'CONNECTED' | 'RECONNECTING' | 'DISCONNECTED' | 'ERROR';

export function useDriverMonitorSocket() {
  const [status, setStatus] = useState<SocketStatus>('IDLE');
  const [result, setResult] = useState<DriverMonitorResult | null>(null);
  const [isStale, setIsStale] = useState(false);
  
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const staleTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const isIntentionallyClosed = useRef(false);

  const getWsUrl = () => {
    const wsBase = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const token = localStorage.getItem('access_token') || 'demo';
    const timerToken = sessionStorage.getItem('driver_timer_token');
    return `${wsBase}/ws/v1/driver-stream?token=${encodeURIComponent(token || '')}&timer_token=${encodeURIComponent(timerToken || '')}`;
  };

  const markStale = useCallback(() => {
    setIsStale(true);
  }, []);

  const resetStaleTimer = useCallback(() => {
    setIsStale(false);
    if (staleTimeoutRef.current) clearTimeout(staleTimeoutRef.current);
    staleTimeoutRef.current = setTimeout(markStale, 2500); // 2.5s for stale data
  }, [markStale]);

  const connect = useCallback(function doConnect() {
    if (socketRef.current?.readyState === WebSocket.OPEN) return;

    isIntentionallyClosed.current = false;
    setStatus(reconnectAttempts.current > 0 ? 'RECONNECTING' : 'CONNECTING');

    const ws = new WebSocket(getWsUrl());
    socketRef.current = ws;

    ws.onopen = () => {
      setStatus('CONNECTED');
      reconnectAttempts.current = 0;
      resetStaleTimer();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'error') {
          console.error('Driver WebSocket Error from server:', data.message);
          return;
        }
        if (data.type === 'driver_session') {
          sessionStorage.setItem('driver_timer_token', data.timer_token);
        } else if (data.type === 'driver_monitor_result') {
          const res = data.data as DriverMonitorResult;
          setResult(res);
          resetStaleTimer();
          if (res.sound_alert || res.speech_prompt) {
            soundEngine.handleDecisionAudio(res.sound_alert, res.speech_prompt);
          }
        } else if (data.type === 'break_status') {
          setResult(previous => previous ? { ...previous, driving_time: data.data } : previous);
        }
      } catch (e) {
        console.error('Failed to parse Driver WebSocket message', e);
      }
    };

    ws.onerror = (e) => {
      console.error('Driver WebSocket Error:', e);
      setStatus('ERROR');
    };

    ws.onclose = () => {
      if (socketRef.current === ws) {
        socketRef.current = null;
      }
      
      if (!isIntentionallyClosed.current) {
        setStatus('DISCONNECTED');
        setIsStale(true);
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 8000);
        reconnectAttempts.current += 1;
        
        reconnectTimeoutRef.current = setTimeout(() => {
          doConnect();
        }, delay);
      } else {
        setStatus('IDLE');
        setIsStale(true);
      }
    };
  }, [resetStaleTimer]);

  const disconnect = useCallback(() => {
    isIntentionallyClosed.current = true;
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    if (staleTimeoutRef.current) clearTimeout(staleTimeoutRef.current);
    
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    setStatus('IDLE');
    setIsStale(true);
    reconnectAttempts.current = 0;
  }, []);

  const sendFrame = useCallback((frameBlob: Blob) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(frameBlob);
    }
  }, []);

  const setResting = useCallback((resting: boolean) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: resting ? 'break_started' : 'break_ended' }));
    }
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    status,
    result,
    isStale,
    connect,
    disconnect,
    sendFrame,
    setResting
  };
}
