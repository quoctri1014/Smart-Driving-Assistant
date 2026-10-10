"""
run_benchmark.py
----------------
Script kiểm chuẩn (Benchmark) ĐO THỰC TẾ trên video mẫu và Ground Truth JSON:
1. Đọc từng frame từ video đầu vào.
2. Chạy qua pipeline_runner (Vehicle Detection, Tracking, Speed, Sign, Collision).
3. Đo đạc chính xác:
   - FPS thực tế (thời gian CPU/GPU xử lý từng khung hình).
   - Độ trễ từng frame (latency min, max, average ms).
   - Precision, Recall, F1-Score so với ground truth thật (nếu có file json).
4. Xuất báo cáo ĐO THẬT ra output/benchmark_results.json để API /ai-status và Web UI hiển thị.

Cách dùng:
  python scripts/run_benchmark.py --video path/to/video.mp4
  python scripts/run_benchmark.py --video path/to/video.mp4 --ground-truth path/to/gt.json
"""

import argparse
import json
import time
from pathlib import Path
import cv2
import numpy as np

# Đảm bảo import được backend và ai_engine
import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ai_engine"))

from backend.app.core.pipeline_runner import PipelineSession
from ai_engine.modules.utils import iou


def evaluate_detections(pred_boxes, gt_boxes, iou_thresh=0.5):
    """
    So khớp bounding boxes dự đoán với ground truth theo IoU:
    Trả về (tp, fp, fn)
    """
    matched_gt = set()
    tp = 0
    fp = 0

    for pbox in pred_boxes:
        best_iou = 0.0
        best_gt_idx = -1
        for g_idx, gbox in enumerate(gt_boxes):
            if g_idx in matched_gt:
                continue
            cur_iou = iou(pbox, gbox)
            if cur_iou > best_iou:
                best_iou = cur_iou
                best_gt_idx = g_idx

        if best_iou >= iou_thresh:
            tp += 1
            matched_gt.add(best_gt_idx)
        else:
            fp += 1

    fn = len(gt_boxes) - len(matched_gt)
    return tp, fp, fn


def run_benchmark(video_path: str, ground_truth_path: str = None, max_frames: int = 500):
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"[ERROR] Khong tim thay file video tai: {video_path}")
        return

    # Tải ground truth nếu có
    gt_data = {}
    if ground_truth_path and Path(ground_truth_path).exists():
        with open(ground_truth_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)
        print(f"[OK] Da tai file Ground Truth: {ground_truth_path} ({len(gt_data)} frames co nhan)")
    else:
        print("[INFO] Chay che do Benchmark Runtime (Do FPS, Do tre va Tracking khong co Ground Truth)")

    cap = cv2.VideoCapture(str(video_file))
    if not cap.isOpened():
        print(f"[ERROR] Khong the mo video: {video_file}")
        return

    session = PipelineSession()
    frame_times = []
    total_tp = 0
    total_fp = 0
    total_fn = 0
    unique_ids_seen = set()
    frame_idx = 0

    print(f"[BENCHMARK] Bat dau benchmark tren '{video_file.name}'...")
    start_total_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret or frame_idx >= max_frames:
            break

        frame_idx += 1
        t_start = time.perf_counter()
        
        # Chạy inference qua pipeline
        res = session.process_frame(frame)
        
        t_elapsed = (time.perf_counter() - t_start) * 1000.0  # ms
        frame_times.append(t_elapsed)

        # Thu thập ID theo dõi
        for v in res.vehicles:
            unique_ids_seen.add(v.id)

        # Đánh giá so với ground truth nếu có
        str_idx = str(frame_idx)
        if str_idx in gt_data:
            gt_frame_boxes = gt_data[str_idx].get("boxes", [])
            pred_boxes = [(v.bbox.x1, v.bbox.y1, v.bbox.x2, v.bbox.y2) for v in res.vehicles]
            tp, fp, fn = evaluate_detections(pred_boxes, gt_frame_boxes)
            total_tp += tp
            total_fp += fp
            total_fn += fn

        if frame_idx % 30 == 0:
            avg_ms = np.mean(frame_times[-30:])
            print(f"  Frame {frame_idx}: Latency {avg_ms:.1f}ms (~{1000.0/avg_ms:.1f} FPS)")

    cap.release()
    total_duration = time.time() - start_total_time

    # Tính toán các chỉ số thực tế
    avg_latency = float(np.mean(frame_times)) if frame_times else 0.0
    min_latency = float(np.min(frame_times)) if frame_times else 0.0
    max_latency = float(np.max(frame_times)) if frame_times else 0.0
    effective_fps = float(len(frame_times) / total_duration) if total_duration > 0 else 0.0

    precision = None
    recall = None
    f1 = None
    if (total_tp + total_fp) > 0:
        precision = round(total_tp / (total_tp + total_fp) * 100.0, 2)
    if (total_tp + total_fn) > 0:
        recall = round(total_tp / (total_tp + total_fn) * 100.0, 2)
    if precision and recall and (precision + recall) > 0:
        f1 = round(2 * (precision * recall) / (precision + recall), 2)

    # Đóng gói kết quả ĐO THẬT
    results_payload = {
        "status": "completed",
        "has_real_data": True,
        "video_tested": video_file.name,
        "frames_evaluated": frame_idx,
        "total_duration_seconds": round(total_duration, 2),
        "fps_achieved": round(effective_fps, 1),
        "overall_latency_ms": round(avg_latency, 1),
        "latency_min_ms": round(min_latency, 1),
        "latency_max_ms": round(max_latency, 1),
        "unique_objects_tracked": len(unique_ids_seen),
        "evaluation_with_ground_truth": bool(gt_data),
        "metrics": {
            "precision": f"{precision}%" if precision is not None else "Cần file ground truth",
            "recall": f"{recall}%" if recall is not None else "Cần file ground truth",
            "f1_score": f"{f1}%" if f1 is not None else "Cần file ground truth",
            "true_positives": total_tp if gt_data else None,
            "false_positives": total_fp if gt_data else None,
            "false_negatives": total_fn if gt_data else None,
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("[BENCHMARK] KET QUA DO KIEM THUC TE:")
    print(f"  - Video: {video_file.name} ({frame_idx} frames)")
    print(f"  - FPS thuc te: {results_payload['fps_achieved']} FPS")
    print(f"  - Do tre trung binh: {results_payload['overall_latency_ms']} ms (Min: {results_payload['latency_min_ms']} ms | Max: {results_payload['latency_max_ms']} ms)")
    print(f"  - So doi tuong track: {results_payload['unique_objects_tracked']}")
    if gt_data:
        print(f"  - Precision: {results_payload['metrics']['precision']}")
        print(f"  - Recall: {results_payload['metrics']['recall']}")
        print(f"  - F1-score: {results_payload['metrics']['f1_score']}")
    else:
        print("  - Precision / Recall: Chua tinh vi chua cung cap file ground-truth annotations")
    print(f"  - File ket qua da ghi vao: {out_file}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy Benchmark đo lường thực tế hệ thống ADAS")
    parser.add_argument("--video", type=str, required=True, help="Đường dẫn đến file video mẫu (.mp4)")
    parser.add_argument("--ground-truth", type=str, default=None, help="Đường dẫn đến file Ground Truth JSON (nếu có)")
    parser.add_argument("--max-frames", type=int, default=500, help="Số khung hình tối đa cần test")
    args = parser.parse_args()

    run_benchmark(args.video, args.ground_truth, args.max_frames)
