import { useState, useEffect, useRef, useCallback } from 'react';
import { Platform } from 'react-native';
import { base64ToArrayBuffer } from './buffer-util';
import { getToken } from './auth';
import { mobileSpeechService } from './speechService';

export type SocketStatus = 'IDLE' | 'CONNECTING' | 'CONNECTED' | 'RECONNECTING' | 'DISCONNECTED' | 'ERROR';

export function useDrivingSocket() {
  const [status, setStatus] = useState<SocketStatus>('IDLE');
  const [result, setResult] = useState<any>(null);
  const [isStale, setIsStale] = useState(false);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const staleTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);
  const isIntentionallyClosed = useRef(false);

  // Allow override via EXPO_PUBLIC_WS_URL, fallback to emulator 10.0.2.2 or localhost
  const getWsUrl = async () => {
    let wsBase = process.env.EXPO_PUBLIC_WS_URL;
    if (!wsBase) {
       wsBase = Platform.OS === 'android' ? 'ws://10.0.2.2:8000' : 'ws://localhost:8000';
    }
    const token = await getToken();
    if (!token) throw new Error('Authentication required');
    return `${wsBase}/ws/v1/stream?token=${encodeURIComponent(token)}`;
  };

  const markStale = useCallback(() => {
    setIsStale(true);
  }, []);

  const resetStaleTimer = useCallback(() => {
    setIsStale(false);
    if (staleTimeoutRef.current) clearTimeout(staleTimeoutRef.current);
    // Mark data as stale if no update for 2.5 seconds (Phase J)
    staleTimeoutRef.current = setTimeout(markStale, 2500);
  }, [markStale]);

  const connect = useCallback(async () => {
    if (socketRef.current?.readyState === WebSocket.OPEN) return;

    isIntentionallyClosed.current = false;
    setStatus(reconnectAttempts.current > 0 ? 'RECONNECTING' : 'CONNECTING');

    let url: string;
    try { url = await getWsUrl(); } catch { setStatus('ERROR'); return; }
    if (isIntentionallyClosed.current) return;
    const ws = new WebSocket(url);
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
          console.error('Road WS Error:', data.message);
          return;
        }
        if (data.type === 'detection_result' || data.data) {
          const res = data.data || data;
          setResult(res);
          resetStaleTimer();

          // Phát giọng đọc tiếng Việt theo Decision Engine
          if (res?.sound_alert || res?.speech_prompt) {
            mobileSpeechService.handleDecisionAudio(res.sound_alert, res.speech_prompt);
          }
        }
      } catch (e) {
        console.error('WS Parse Error', e);
      }
    };

    ws.onerror = () => setStatus('ERROR');
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

  const sendFrame = useCallback(async (base64Data: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      try {
        const buffer = base64ToArrayBuffer(base64Data);
        // WebSocket on React Native accepts ArrayBuffer/ArrayBufferView directly
        socketRef.current.send(buffer);
      } catch (e) {
        console.error('Failed to send frame buffer', e);
      }
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

  useEffect(() => {
    return () => disconnect();
  }, [disconnect]);

  return { status, result, isStale, connect, disconnect, sendFrame, sendMetadata };
}
