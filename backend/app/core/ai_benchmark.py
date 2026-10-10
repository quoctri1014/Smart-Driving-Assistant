"""
ai_benchmark.py
---------------
Quản lý dữ liệu kiểm chuẩn AI thực tế.
Chỉ trả về kết quả ĐO THẬT nếu đã chạy script benchmark trên video mẫu.
Mặc định trả về "Chưa có dữ liệu đánh giá" nếu chưa có dữ liệu đo kiểm thực tế.
"""

from pathlib import Path
import json
from typing import Dict, Any, Optional

BENCHMARK_RESULT_FILE = Path("output/benchmark_results.json")
STRESS_TEST_FILE = Path("output/stress_test_results.json")


def get_ai_benchmark_summary() -> Dict[str, Any]:
    """
    Đọc kết quả kiểm chuẩn thực tế từ file output/benchmark_results.json và output/stress_test_results.json.
    Nếu chưa có, trả về trạng thái Chưa có dữ liệu đánh giá.
    """
    stress_data = None
    if STRESS_TEST_FILE.exists():
        try:
            with open(STRESS_TEST_FILE, "r", encoding="utf-8") as f:
                stress_data = json.load(f)
        except Exception:
            pass

    if BENCHMARK_RESULT_FILE.exists():
        try:
            with open(BENCHMARK_RESULT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if stress_data:
                    data["stress_test"] = stress_data
                return data
        except Exception:
            pass

    if stress_data:
        # Lấy latency và FPS từ điều kiện clear_day đo thật
        clear_stats = stress_data.get("conditions_tested", {}).get("clear_day", {})
        return {
            "status": "completed_stress_test",
            "has_real_data": True,
            "fps_achieved": clear_stats.get("effective_fps"),
            "overall_latency_ms": clear_stats.get("avg_latency_ms"),
            "test_type": "SYNTHETIC_STRESS_AND_ROBUSTNESS_BENCHMARK",
            "timestamp": stress_data.get("timestamp"),
            "stress_test": stress_data
        }

    return {
        "status": "pending_evaluation",
        "has_real_data": False,
        "message": "Chưa có dữ liệu đánh giá thực tế (Cần chạy script benchmark trên video mẫu)",
        "modules_evaluated": 0,
        "results": []
    }
