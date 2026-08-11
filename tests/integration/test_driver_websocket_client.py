import asyncio
import websockets
import cv2
import json
import time

async def test_driver_client():
    uri = "ws://localhost:8000/ws/v1/driver-stream"
    
    # Sử dụng webcam (0) hoặc thay bằng một đoạn video quay mặt
    video_source = 0
    cap = cv2.VideoCapture(video_source)
    
    if not cap.isOpened():
        print("Could not open camera or video.")
        return

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")
        
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            if frame_count > 100: # Giới hạn test 100 khung hình
                break
                
            # Resize để truyền nhanh hơn qua websocket nếu cần
            frame = cv2.resize(frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', frame)
            
            # Gửi frame binary
            await websocket.send(buffer.tobytes())
            
            # Chờ kết quả phản hồi
            response = await websocket.recv()
            data = json.loads(response)
            
            result = data.get("data", {})
            drowsiness = result.get("drowsiness", {})
            seatbelt = result.get("seatbelt", {})
            
            print(f"Frame {frame_count}: EAR={drowsiness.get('ear_value', 0):.2f}, "
                  f"Yawn={drowsiness.get('yawn_count', 0)}, "
                  f"Alert={drowsiness.get('alert_level', 'normal')}, "
                  f"Seatbelt={seatbelt.get('seatbelt_on', False)}")
            
            # Throttle FPS
            time.sleep(0.05)

    cap.release()
    print("Test completed.")

if __name__ == "__main__":
    asyncio.run(test_driver_client())
