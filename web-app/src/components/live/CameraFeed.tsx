"use client";
import { useEffect, useRef } from 'react';

interface CameraFeedProps {
    videoRef: React.RefObject<HTMLVideoElement | null>;
    children?: React.ReactNode;
}

export default function CameraFeed({ videoRef, children }: CameraFeedProps) {
    
    // Request webcam access
    useEffect(() => {
        async function setupCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 640, height: 480, facingMode: "user" },
                    audio: false
                });
                
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                }
            } catch (err) {
                console.error("Error accessing webcam:", err);
            }
        }
        setupCamera();

        return () => {
            // Cleanup stream
            if (videoRef.current && videoRef.current.srcObject) {
                const stream = videoRef.current.srcObject as MediaStream;
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, [videoRef]);

    return (
        <div className="relative w-full aspect-[3/4] bg-gray-900 overflow-hidden flex-shrink-0">
            {/* The actual video feed */}
            <video 
                ref={videoRef} 
                autoPlay 
                playsInline 
                muted 
                className="w-full h-full object-cover"
            />
            
            {/* Overlay Layer for Bounding Boxes or UI elements */}
            <div className="absolute inset-0 pointer-events-none">
                {children}
            </div>
        </div>
    );
}
