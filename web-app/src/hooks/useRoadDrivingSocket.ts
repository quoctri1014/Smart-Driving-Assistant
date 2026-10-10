import { useState, useEffect, useCallback, useRef } from 'react';
import { DetectionResult } from '../types/detection';
import { soundEngine } from '../lib/soundEngine';

export type SocketStatus = 'IDLE' | 'CONNECTING' | 'CONNECTED' | 'RECONNECTING' | 'DISCONNECTED' | 'ERROR';

export function useRoadDrivingSocket() {
  const [status, setStatus] = useState<SocketStatus>('IDLE');
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [isStale, setIsStale] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const ready = useRef(false);
  const inFlight = useRef(false);
  const sentAt = useRef(0);
  const timeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const staleTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const disconnect = useCallback(() => {
    if (timeout.current) clearTimeout(timeout.current);
    if (staleTimeout.current) clearTimeout(staleTimeout.current);
    const socket = socketRef.current;
    socketRef.current = null;
    ready.current = false;
    inFlight.current = false;
    if (socket) socket.close();
    setStatus('IDLE');
    setIsStale(true);
    setResult(null);
  }, []);

  const connect = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState < WebSocket.CLOSING) return;
    const token = localStorage.getItem('access_token') || 'demo';
    setResult(null);
    setError(null);
    setIsStale(true);
    setStatus('CONNECTING');
    ready.current = false;
    inFlight.current = false;
    const base = process.env.NEXT_PUBLIC_WS_URL || `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.hostname}:8000`;
    const url = new URL(base);
    url.pathname = '/ws/v1/stream';
    url.search = '';
    url.searchParams.set('token', token);
    const ws = new WebSocket(url.toString());
    socketRef.current = ws;
    timeout.current = setTimeout(() => {
      if (socketRef.current !== ws) return;
      // Graceful timeout: do not block UI with hard error, allow in-browser local AI fallback
      console.warn('Road socket standby: relying on in-browser client AI engine');
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        setStatus('CONNECTED');
        ready.current = true;
      } else {
        setStatus('IDLE');
      }
      if (timeout.current) clearTimeout(timeout.current);
    }, 5000);
    ws.onopen = () => {
      if (socketRef.current !== ws) return;
      ready.current = true;
      if (timeout.current) clearTimeout(timeout.current);
      setStatus('CONNECTED');
    };
    ws.onmessage = event => {
      if (socketRef.current !== ws) return;
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'session_started' || message.type === 'detection_result') {
          ready.current = true;
          if (timeout.current) clearTimeout(timeout.current);
          setStatus('CONNECTED');
        }
        if (message.type === 'error') {
          inFlight.current = false;
          setIsStale(true);
          setError(`${message.code || 'AI_ERROR'}: ${message.message || 'Backend could not process the frame.'}`);
          return;
        }
        if (message.type !== 'detection_result') return;
        inFlight.current = false;
        setResult(message.data);
        setError(null);
        setIsStale(false);
        if (staleTimeout.current) clearTimeout(staleTimeout.current);
        staleTimeout.current = setTimeout(() => setIsStale(true), 5000);

        // Phát âm thanh cảnh báo & giọng đọc tiếng Việt theo Decision Engine
        if (message.data?.sound_alert || message.data?.speech_prompt) {
          soundEngine.handleDecisionAudio(message.data.sound_alert, message.data.speech_prompt);
        }
      } catch {
        inFlight.current = false;
        setError('Invalid AI response received.');
      }
    };
    ws.onerror = () => {
      if (socketRef.current === ws) setError('Cannot connect to AI backend. Check server address and sign-in session.');
    };
    ws.onclose = event => {
      if (socketRef.current !== ws) return;
      socketRef.current = null;
      ready.current = false;
      inFlight.current = false;
      if (timeout.current) clearTimeout(timeout.current);
      setStatus('ERROR');
      setIsStale(true);
      setError(event.code === 1008 ? 'Session rejected. Sign in again.' : event.code === 1013 ? 'AI server is busy. Retry shortly.' : 'AI connection closed. Check backend and retry.');
    };
  }, []);

  const sendFrame = useCallback((frame: Blob) => {
    const socket = socketRef.current;
    if (!ready.current || socket?.readyState !== WebSocket.OPEN) return;
    if (inFlight.current) {
      if (Date.now() - sentAt.current > 30000) {
        setError('AI has not returned a result for 30 seconds. Stop and restart the session.');
        setIsStale(true);
      }
      return;
    }
    if (socket.bufferedAmount > 0) return;
    inFlight.current = true;
    sentAt.current = Date.now();
    socket.send(frame);
  }, []);

  const sendMetadata = useCallback((metadata: { vehicle_speed?: number | null }) => {
    if (socketRef.current?.readyState === WebSocket.OPEN && ready.current) {
      socketRef.current.send(JSON.stringify({ type: 'metadata', ...metadata }));
    }
  }, []);
  useEffect(() => disconnect, [disconnect]);
  return { status, result, isStale, error, connect, disconnect, sendFrame, sendMetadata };
}
