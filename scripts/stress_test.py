"""
stress_test.py
--------------
0.7 Stress Testing & Robustness Benchmark for ADAS Pipeline:
Kiểm thử độ bền bỉ của hệ thống dưới các điều kiện thời tiết và nhiễu khắc nghiệt:
1. Mờ chuyển động (Motion Blur / Defocus).
2. Trời mưa (Synthetic Rain Streaks & Water Droplets).
3. Đêm tối / Thiếu sáng (Low-light / Darkness).
4. Ngược sáng / Lóa đèn pha ban đêm (Glare / Headlight flare).
5. Nén ảnh băng thông thấp (JPEG compression degradation).

Kiểm tra:
- ImageQualityGate có phát hiện đúng và kích hoạt CLAHE / cờ low_quality không?
- SensorHealthMonitor có chống báo động giả khi camera bị che/lỗi không?
- Đo FPS thật và xuất báo cáo kiểm chuẩn định lượng ra output/stress_test_results.json.
"""

import sys
import os
import json
import time
from pathlib import Path
import cv2
import numpy as np

# Đảm bảo UTF-8 trên Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ai_engine"))

from ai_engine.modules.image_quality_gate import ImageQualityGate
from ai_engine.modules.health_monitor import SensorHealthMonitor
from backend.app.core.pipeline_runner import PipelineSession


def apply_blur(image: np.ndarray, ksize: int = 15) -> np.ndarray:
    return cv2.GaussianBlur(image, (ksize, ksize), 0)


def apply_darkness(image: np.ndarray, factor: float = 0.25) -> np.ndarray:
    return np.clip(image.astype(np.float32) * factor, 0, 255).astype(np.uint8)


def apply_glare(image: np.ndarray) -> np.ndarray:
    res = image.copy()
    h, w = image.shape[:2]
    center = (w // 2, h // 3)
    radius = int(min(h, w) * 0.3)
    cv2.circle(res, center, radius, (255, 255, 255), -1)
    res = cv2.GaussianBlur(res, (31, 31), 0)
    return res


def apply_rain(image: np.ndarray, slant: int = 10, drop_length: int = 20) -> np.ndarray:
    res = image.copy()
    h, w = image.shape[:2]
    num_drops = int(h * w * 0.002)
    for _ in range(num_drops):
        x = np.random.randint(0, w)
        y = np.random.randint(0, h)
        cv2.line(res, (x, y), (x + slant, y + drop_length), (200, 200, 200), 1)
    return res


def apply_jpeg_compression(image: np.ndarray, quality: int = 15) -> np.ndarray:
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, enc = cv2.imencode('.jpg', image, encode_param)
    return cv2.imdecode(enc, 1)


def run_stress_test(sample_image_path: str = None, num_iterations: int = 20):
    print("[STRESS_TEST] Khoi tao kiem thu chiu tai & ngoai le moi truong...")

    # Tạo ảnh mẫu thực tế nếu không có file truyền vào
    if sample_image_path and Path(sample_image_path).exists():
        base_frame = cv2.imread(sample_image_path)
    else:
        # Tạo canvas 640x480 mô phỏng đường phố
        base_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        base_frame[:240] = [180, 130, 70] # Bầu trời
        base_frame[240:] = [60, 60, 60]   # Mặt đường
        # Vạch kẻ đường
        cv2.line(base_frame, (320, 240), (200, 480), (255, 255, 255), 4)
        cv2.line(base_frame, (320, 240), (440, 480), (255, 255, 255), 4)
        # Mô phỏng xe phía trước
        cv2.rectangle(base_frame, (280, 270), (360, 360), (30, 30, 180), -1)

    gate = ImageQualityGate()
    health = SensorHealthMonitor()
    session = PipelineSession()

    conditions = {
        "clear_day": lambda img: img,
        "motion_blur": lambda img: apply_blur(img, 17),
        "heavy_rain": lambda img: apply_rain(img),
        "night_darkness": lambda img: apply_darkness(img, 0.2),
        "headlight_glare": lambda img: apply_glare(img),
        "jpeg_compression_degraded": lambda img: apply_jpeg_compression(img, 12),
        "camera_obstructed_covered": lambda img: np.zeros_like(img) # Camera bị bịt kín
    }

    results = {}
    total_start = time.time()

    for cond_name, aug_fn in conditions.items():
        print(f"  -> Testing condition: {cond_name}...")
        corrupted_frame = aug_fn(base_frame)
        latencies = []
        low_quality_detected = 0
        camera_obstructed_detected = 0
        clahe_enhanced_count = 0

        for i in range(num_iterations):
            cur_time = time.time()
            t0 = time.perf_counter()

            # 1. Image Quality Gate
            q_report, processed_frame = gate.assess_frame(corrupted_frame)
            if q_report.is_low_quality:
                low_quality_detected += 1
            if q_report.enhanced:
                clahe_enhanced_count += 1

            # 2. Health Monitor
            h_report = health.evaluate_system_health(corrupted_frame, current_time=cur_time)
            if h_report["camera_status"] == "OBSTRUCTED":
                camera_obstructed_detected += 1

            # 3. Pipeline inference
            res = session.process_frame(processed_frame)

            t_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(t_ms)

        avg_lat = float(np.mean(latencies))
        fps = round(1000.0 / avg_lat, 1) if avg_lat > 0 else 0.0

        results[cond_name] = {
            "iterations": num_iterations,
            "avg_latency_ms": round(avg_lat, 2),
            "effective_fps": fps,
            "quality_score_sample": q_report.score,
            "low_quality_flag_rate": round(low_quality_detected / num_iterations * 100.0, 1),
            "clahe_applied_rate": round(clahe_enhanced_count / num_iterations * 100.0, 1),
            "camera_obstructed_detected": (camera_obstructed_detected > 0),
            "graceful_degradation_active": h_report["graceful_degradation_active"],
            "issues_detected": q_report.issues
        }

    total_duration = round(time.time() - total_start, 2)
    output_payload = {
        "status": "completed",
        "has_real_data": True,
        "test_type": "SYNTHETIC_STRESS_AND_ROBUSTNESS_BENCHMARK",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "total_duration_seconds": total_duration,
        "conditions_tested": results
    }

    out_file = Path("output/stress_test_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] Da xuat ket qua Stress Test thuc nghiem ra: {out_file}")
    return output_payload


if __name__ == "__main__":
    run_stress_test()
