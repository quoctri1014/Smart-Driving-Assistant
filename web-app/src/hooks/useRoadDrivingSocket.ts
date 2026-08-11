import { useState, useEffect, useCallback, useRef } from 'react';
import { DetectionResult } from '../types/detection';

export type SocketStatus = 'IDLE' | 'CONNECTING' | 'CONNECTED' | 'RECONNECTING' | 'DISCONNECTED' | 'ERROR';

export function useRoadDrivingSocket() {
  const [status, setStatus] = useState<SocketStatus>('IDLE');
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [isStale, setIsStale] = useState(false);
  
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const staleTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const isIntentionallyClosed = useRef(false);

  const getWsUrl = () => {
    const wsBase = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const token = localStorage.getItem('access_token');
    return `${wsBase}/ws/v1/stream?token=${token || ''}`;
  };

  const markStale = useCallback(() => {
    setIsStale(true);
  }, []);

  const resetStaleTimer = useCallback(() => {
    setIsStale(false);
    if (staleTimeoutRef.current) clearTimeout(staleTimeoutRef.current);
    // Mark data as stale if no update for 2.5 seconds (FIX H)
    staleTimeoutRef.current = setTimeout(markStale, 2500);
  }, [markStale]);

  const connect = useCallback(() => {
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
          console.error('Road WebSocket Error from server:', data.message);
          return;
        }
        setResult(data as DetectionResult);
        resetStaleTimer();
      } catch (e) {
        console.error('Failed to parse Road WebSocket message', e);
      }
    };

    ws.onerror = (e) => {
      console.error('Road WebSocket Error:', e);
      setStatus('ERROR');
    };

    ws.onclose = () => {
      if (socketRef.current === ws) {
        socketRef.current = null;
      }
      
      if (!isIntentionallyClosed.current) {
        setStatus('DISCONNECTED');
        setIsStale(true);
        // Exponential backoff
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 8000);
        reconnectAttempts.current += 1;
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
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

  const sendMetadata = useCallback((metadata: { vehicle_speed?: number }) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'metadata',
        ...metadata
      }));
    }
  }, []);

  // Cleanup on unmount
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
    sendMetadata
  };
}
