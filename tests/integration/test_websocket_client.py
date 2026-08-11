import asyncio
import websockets
import cv2
import json
import time

async def test_client():
    uri = "ws://localhost:8000/ws/v1/stream"
    video_path = "ai_engine/sample_videos/traffic.mp4"
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Could not open video.")
        return

    async with websockets.connect(uri) as websocket:
        # Send metadata
        await websocket.send(json.dumps({"type": "metadata", "vehicle_speed": 40.0}))
        
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            if frame_count > 30: # Limit testing to 30 frames
                break
                
            # Encode frame
            _, buffer = cv2.imencode('.jpg', frame)
            
            # Send binary frame
            await websocket.send(buffer.tobytes())
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            
            print(f"Frame {frame_count}: processing_time={data.get('data', {}).get('processing_time_ms', 0):.1f}ms, vehicles={len(data.get('data', {}).get('vehicles', []))}")
            
            # Throttle fps
            time.sleep(0.1)

    cap.release()

if __name__ == "__main__":
    asyncio.run(test_client())
