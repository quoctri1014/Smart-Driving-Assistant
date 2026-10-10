import sys
import os
import time
import cv2
import numpy as np

# Ensure ai_engine is in sys.path
sys.path.insert(0, os.path.abspath("ai_engine"))
sys.path.insert(0, os.path.abspath("."))

from ai_engine.modules.image_quality_gate import ImageQualityGate
from ai_engine.modules.detector import VehicleDetector
from ai_engine.modules.tracker import SimpleTracker
from ai_engine.modules.lane_detector import LaneDetector
from ai_engine.modules.speed_estimator import SpeedEstimator

def profile():
    frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

    gate = ImageQualityGate()
    det = VehicleDetector()
    tracker = SimpleTracker()
    lane = LaneDetector()
    speed = SpeedEstimator()

    # Warmup
    raw_dets = det.detect(frame)

    # 1. ImageQualityGate
    t0 = time.perf_counter()
    N = 10
    for _ in range(N):
        q_report, proc_frame = gate.assess_frame(frame)
    t_gate = (time.perf_counter() - t0) / N * 1000

    q_info = {"glare_ratio": q_report.glare_ratio}

    # 2. YOLOv8n detector
    t0 = time.perf_counter()
    N_det = 5
    for _ in range(N_det):
        dets = det.detect(frame, quality_info=q_info)
    t_det = (time.perf_counter() - t0) / N_det * 1000

    det_pairs = [(d["box"], d["cls_name"], d["conf"]) for d in dets]

    # 3. Tracker
    t0 = time.perf_counter()
    for i in range(N):
        tracker.update(det_pairs, frame_idx=i, frame=frame)
    t_trk = (time.perf_counter() - t0) / N * 1000

    # 4. LaneDetector
    t0 = time.perf_counter()
    for _ in range(N):
        lane_info = lane.detect_ego_lane(frame)
    t_lane = (time.perf_counter() - t0) / N * 1000

    # 5. SpeedEstimator
    t0 = time.perf_counter()
    for i in range(N):
        _ = speed.update(tracker.tracks, frame_idx=i)
    t_spd = (time.perf_counter() - t0) / N * 1000

    total_ms = t_gate + t_det + t_trk + t_lane + t_spd
    fps = 1000.0 / total_ms if total_ms > 0 else 0

    print("=== PROFILER RESULTS (1280x720 CPU) ===")
    print(f"1. ImageQualityGate:          {t_gate:6.2f} ms ({t_gate/total_ms*100:4.1f}%)")
    print(f"2. YOLOv8n VehicleDetector:   {t_det:6.2f} ms ({t_det/total_ms*100:4.1f}%)")
    print(f"3. SimpleTracker (ByteTrack): {t_trk:6.2f} ms ({t_trk/total_ms*100:4.1f}%)")
    print(f"4. LaneDetector (Hough/HSV):  {t_lane:6.2f} ms ({t_lane/total_ms*100:4.1f}%)")
    print(f"5. SpeedEstimator:            {t_spd:6.2f} ms ({t_spd/total_ms*100:4.1f}%)")
    print("---------------------------------------")
    print(f"Total per-frame latency:      {total_ms:6.2f} ms")
    print(f"Real CPU Processing Throughput: ~{fps:.1f} FPS")

if __name__ == "__main__":
    profile()
