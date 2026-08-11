import { useState, useEffect, useRef, useCallback } from 'react';
import { DetectionResult, DriverMonitorResult } from '../types/detection';

// Trong Expo, ta truyền ref của CameraView vào đây
type StreamMode = 'road' | 'driver';

export function useWebSocketStream(mode: StreamMode, cameraRef: any) {
    const [isConnected, setIsConnected] = useState(false);
    const [latestRoadResult, setLatestRoadResult] = useState<DetectionResult | null>(null);
    const [latestDriverResult, setLatestDriverResult] = useState<DriverMonitorResult | null>(null);
    
    const wsRef = useRef<WebSocket | null>(null);
    const isProcessingRef = useRef(false);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const WS_URL = process.env.EXPO_PUBLIC_WS_URL || "ws://192.168.1.100:8000/ws/v1";

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;
        
        const endpoint = mode === 'road' ? `${WS_URL}/stream` : `${WS_URL}/driver-stream`;
        const ws = new WebSocket(endpoint);

        ws.onopen = () => {
            console.log(`Connected to ${endpoint}`);
            setIsConnected(true);
        };

        ws.onclose = () => {
            console.log("Disconnected from WebSocket");
            setIsConnected(false);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "detection_result") {
                    setLatestRoadResult(data.data as DetectionResult);
                } else if (data.type === "driver_monitor_result") {
                    setLatestDriverResult(data.data as DriverMonitorResult);
                }
            } catch (error) {
                console.log("Failed to parse message", error);
            }
        };

        wsRef.current = ws;
    }, [mode, WS_URL]);

    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    }, []);

    useEffect(() => {
        const captureAndSend = async () => {
            if (isConnected && wsRef.current?.readyState === WebSocket.OPEN && cameraRef.current) {
                if (isProcessingRef.current) return;
                
                try {
                    isProcessingRef.current = true;
                    // Lấy ảnh từ expo-camera, chất lượng siêu thấp để truyền nhanh
                    const photo = await cameraRef.current.takePictureAsync({ 
                        quality: 0.1, 
                        base64: true,
                        scale: 0.5
                    });
                    
                    if (photo && photo.base64 && wsRef.current?.readyState === WebSocket.OPEN) {
                        // Chuyển base64 sang binary buffer (FastAPI websocket đang đọc bytes)
                        // Trong RN, gửi base64 qua WebSocket nếu server cấu hình hỗ trợ,
                        // hoặc gửi String để backend tự decode.
                        // Do backend FastAPI đang nhận "bytes", ta có thể gửi chuỗi base64 qua Blob hoặc ArrayBuffer, 
                        // Tuy nhiên react-native websocket hỗ trợ truyền ArrayBuffer, ta phải bọc lại.
                        
                        // Để đơn giản, ta convert base64 thành binary qua Buffer (hoặc gửi object Text)
                        // Ở đây sử dụng fetch tạm để tạo blob (trick trên RN)
                        const response = await fetch(photo.uri);
                        const blob = await response.blob();
                        wsRef.current.send(blob);
                    }
                } catch (err) {
                    // Ignore capture errors when unmounting
                } finally {
                    isProcessingRef.current = false;
                }
            }
        };

        if (isConnected) {
            intervalRef.current = setInterval(captureAndSend, 300); // 300ms
        }

        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, [isConnected, cameraRef]);

    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return { 
        isConnected, 
        latestRoadResult, 
        latestDriverResult 
    };
}
