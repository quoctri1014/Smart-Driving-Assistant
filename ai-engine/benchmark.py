import time
import cv2
import numpy as np
from modules.detector import VehicleDetector

def run_benchmark(video_path="sample_videos/road_test.mp4", num_frames=100):
    print(f"Starting benchmark on {video_path} for {num_frames} frames...")
    detector = VehicleDetector()
    
    # Tạo frame giả nếu không có video
    dummy_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    
    start_time = time.time()
    for i in range(num_frames):
        _ = detector.detect_vehicles(dummy_frame)
    
    end_time = time.time()
    
    total_time = end_time - start_time
    fps = num_frames / total_time
    avg_latency = (total_time / num_frames) * 1000
    
    print("-" * 30)
    print("BENCHMARK RESULTS")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"FPS: {fps:.2f}")
    print(f"Avg Latency per Frame: {avg_latency:.2f} ms")
    print("-" * 30)

if __name__ == "__main__":
    run_benchmark()
