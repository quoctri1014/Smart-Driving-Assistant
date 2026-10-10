#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HỆ THỐNG THEO DÕI GIAO THÔNG, ĐO TỐC ĐỘ (KM/H) & ĐẾM PHƯƠNG TIỆN QUA VẠCH (LINE CROSSING)
========================================================================================
Tính năng:
- YOLOv8 / YOLO11 Detection: car, motorcycle, bus, truck, person
- ByteTrack Object Tracking: gán ID ổn định theo thời gian
- Speed Estimation: ước lượng tốc độ di chuyển thực tế (km/h) dựa trên phối cảnh & thời gian
- Virtual Line Crossing: vạch ảo kiểm soát xe ra vào (IN / OUT)
- Counter & Per-Class Breakdown: đếm chi tiết số lượng từng loại đối tượng (motor, people, car, truck, bus)
- HUD Overlay Realtime: giao diện hiển thị chuyên nghiệp với thông số trực quan
"""

import argparse
import os
import sys
import time
from collections import defaultdict, deque
import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    print("[ERROR] Chưa cài đặt thư viện 'ultralytics'. Vui lòng chạy: pip install ultralytics")
    sys.exit(1)


# Bảng ánh xạ nhãn COCO chuẩn
COCO_CLASSES = {
    0: "person",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# Tên viết gọn hiển thị giao diện
CLASS_DISPLAY = {
    "person": "people",
    "motorcycle": "motor",
    "car": "car",
    "bus": "bus",
    "truck": "truck",
}

# Màu sắc hiển thị (BGR)
COLORS = {
    "car": (255, 140, 0),        # Deep sky blue / Orange
    "motor": (0, 215, 255),      # Gold / Yellow
    "people": (255, 105, 180),   # Hot pink / Purple
    "bus": (50, 205, 50),        # Lime green
    "truck": (180, 105, 255),    # Pink / Violet
}


class SpeedAndLineCrossingTracker:
    def __init__(
        self,
        line_y: int = 500,
        real_distance_m: float = 10.0,
        fps_target: float = 30.0,
        buffer_size: int = 15,
    ):
        self.line_y = line_y
        self.real_distance_m = real_distance_m
        self.fps_target = fps_target
        self.buffer_size = buffer_size

        # Lưu vết vị trí: track_id -> deque of (cx, cy, timestamp)
        self.tracks = defaultdict(lambda: deque(maxlen=self.buffer_size))
        # Tốc độ làm mịn: track_id -> km/h
        self.speeds = {}
        # Hướng di chuyển: track_id -> 'IN' | 'OUT' | 'IDLE'
        self.directions = {}
        # Lớp đối tượng: track_id -> class_name
        self.classes = {}

        # Bộ đếm qua vạch
        self.in_count = 0
        self.out_count = 0
        self.crossed_in_ids = set()
        self.crossed_out_ids = set()

        self.in_by_class = defaultdict(int)
        self.out_by_class = defaultdict(int)

        # Lịch sử các xe vừa qua vạch gần nhất
        self.recent_crossings = deque(maxlen=6)

    def update(self, track_id: int, cls_name: str, bbox: tuple, current_time: float) -> dict:
        x1, y1, x2, y2 = bbox
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        h = max(1, y2 - y1)

        display_cls = CLASS_DISPLAY.get(cls_name, cls_name)
        self.classes[track_id] = display_cls

        history = self.tracks[track_id]

        prev_y = history[-1][1] if history else cy
        history.append((cx, cy, current_time))

        # 1. Tính toán vận tốc (km/h)
        speed_kmh = self._estimate_speed(track_id, h)
        self.speeds[track_id] = speed_kmh

        # 2. Xác định hướng di chuyển
        direction = "IDLE"
        if len(history) >= 3:
            dy = history[-1][1] - history[0][1]
            if dy > 6:
                direction = "IN"   # Đi xuống phía dưới màn hình (gần camera hơn)
            elif dy < -6:
                direction = "OUT"  # Đi lên phía trên màn hình (xa camera)
        self.directions[track_id] = direction

        # 3. Kiểm tra cắt vạch ảo (Virtual Line Crossing)
        if prev_y < self.line_y <= cy:
            # Cắt từ trên xuống dưới -> TIẾN VÀO (IN)
            if track_id not in self.crossed_in_ids:
                self.crossed_in_ids.add(track_id)
                self.in_count += 1
                self.in_by_class[display_cls] += 1
                self.recent_crossings.append({
                    "id": track_id,
                    "class": display_cls,
                    "direction": "IN",
                    "speed_kmh": round(speed_kmh),
                    "time": time.strftime("%H:%M:%S"),
                })
        elif prev_y > self.line_y >= cy:
            # Cắt từ dưới lên trên -> RỜI ĐI (OUT)
            if track_id not in self.crossed_out_ids:
                self.crossed_out_ids.add(track_id)
                self.out_count += 1
                self.out_by_class[display_cls] += 1
                self.recent_crossings.append({
                    "id": track_id,
                    "class": display_cls,
                    "direction": "OUT",
                    "speed_kmh": round(speed_kmh),
                    "time": time.strftime("%H:%M:%S"),
                })

        return {
            "id": track_id,
            "class": display_cls,
            "cx": cx,
            "cy": cy,
            "speed_kmh": speed_kmh,
            "direction": direction,
        }

    def _estimate_speed(self, track_id: int, box_height: int) -> float:
        history = self.tracks[track_id]
        if len(history) < 4:
            return self.speeds.get(track_id, 0.0)

        # Lấy điểm đầu và điểm cuối trong cửa sổ quan sát
        p_first = history[0]
        p_last = history[-1]

        dt = p_last[2] - p_first[2]
        if dt <= 0.05:
            return self.speeds.get(track_id, 0.0)

        dy = abs(p_last[1] - p_first[1])
        dx = abs(p_last[0] - p_first[0])
        dist_px = np.sqrt(dx ** 2 + dy ** 2)

        # Tỷ lệ mét/pixel phụ thuộc chiều cao bounding box (hiệu ứng phối cảnh)
        # Đối tượng càng ở xa (box_height nhỏ), 1 pixel đại diện cho khoảng cách lớn hơn
        ppm = max(5.0, box_height * 0.45)
        dist_m = dist_px / ppm

        inst_speed = (dist_m / dt) * 3.6  # m/s -> km/h

        # Lọc nhiễu bằng Exponential Moving Average (EMA)
        old_speed = self.speeds.get(track_id, inst_speed)
        smooth_speed = 0.65 * old_speed + 0.35 * inst_speed

        # Giới hạn ngưỡng thực tế
        return float(np.clip(smooth_speed, 0.0, 140.0))


def draw_hud(frame: np.ndarray, tracker: SpeedAndLineCrossingTracker, fps: float):
    """Vẽ giao diện bảng điều khiển HUD lên góc frame video."""
    h_frame, w_frame = frame.shape[:2]

    # 1. Vẽ vạch ảo Virtual Line
    line_y = tracker.line_y
    cv2.line(frame, (0, line_y), (w_frame, line_y), (0, 255, 255), 2, cv2.LINE_AA)
    cv2.line(frame, (0, line_y - 2), (w_frame, line_y - 2), (0, 140, 255), 1, cv2.LINE_AA)

    # Nhãn trên vạch ảo
    cv2.putText(
        frame,
        f"--- VIRTUAL LINE CROSSING (Y={line_y}) [IN: DOWN / OUT: UP] ---",
        (15, line_y - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )

    # 2. Vẽ bảng HUD đen mờ bên góc trái (Glassmorphism card)
    overlay = frame.copy()
    hud_w, hud_h = 320, 390
    cv2.rectangle(overlay, (15, 15), (15 + hud_w, 15 + hud_h), (15, 18, 24), -1)
    cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)
    cv2.rectangle(frame, (15, 15), (15 + hud_w, 15 + hud_h), (80, 90, 105), 1)

    y_off = 38
    # Tiêu đề
    cv2.putText(frame, "TRAFFIC SPEED & COUNT", (28, y_off), cv2.FONT_HERSHEY_DUPLEX, 0.58, (56, 189, 248), 1, cv2.LINE_AA)
    y_off += 24

    # Danh sách tốc độ các xe đang theo dõi (Live Speeds)
    # Hiển thị kiểu: car 55 km/h, motor 31 km/h, people 15 km/h
    active_items = []
    for tid, speed in tracker.speeds.items():
        if tid in tracker.classes and speed > 0:
            cls = tracker.classes[tid]
            active_items.append((cls, tid, speed))

    # Lấy tối đa 5 xe đang chạy
    active_items.sort(key=lambda x: x[2], reverse=True)
    for cls, tid, speed in active_items[:5]:
        line_txt = f"{cls.upper():<6} #{tid:<3}  {round(speed):>3} km/h"
        color = COLORS.get(cls, (220, 220, 220))
        cv2.putText(frame, line_txt, (28, y_off), cv2.FONT_HERSHEY_SIMPLEX, 0.48, color, 1, cv2.LINE_AA)
        y_off += 20

    if not active_items:
        cv2.putText(frame, "Tracking objects...", (28, y_off), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (140, 150, 160), 1, cv2.LINE_AA)
        y_off += 20

    # Phân cách
    y_off += 6
    cv2.line(frame, (28, y_off), (hud_w, y_off), (60, 70, 85), 1)
    y_off += 20

    # Số lượng IN / OUT
    cv2.putText(frame, f"IN : {tracker.in_count}", (28, y_off), cv2.FONT_HERSHEY_DUPLEX, 0.58, (52, 211, 153), 2, cv2.LINE_AA)
    cv2.putText(frame, f"OUT: {tracker.out_count}", (180, y_off), cv2.FONT_HERSHEY_DUPLEX, 0.58, (96, 165, 250), 2, cv2.LINE_AA)
    y_off += 24

    # Phân loại Line Crossings: Out & In
    cv2.putText(frame, "Line Crossings (OUT / IN):", (28, y_off), cv2.FONT_HERSHEY_DUPLEX, 0.48, (251, 191, 36), 1, cv2.LINE_AA)
    y_off += 20

    categories = ["car", "motor", "people", "truck", "bus"]
    for cat in categories:
        out_c = tracker.out_by_class.get(cat, 0)
        in_c = tracker.in_by_class.get(cat, 0)
        row_txt = f"  {cat:<7} :  OUT {out_c:>2}  |  IN {in_c:>2}"
        cv2.putText(frame, row_txt, (28, y_off), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (200, 210, 220), 1, cv2.LINE_AA)
        y_off += 18

    # Phân cách & FPS
    y_off += 6
    cv2.line(frame, (28, y_off), (hud_w, y_off), (60, 70, 85), 1)
    y_off += 18
    cv2.putText(frame, f"FPS: {fps:.1f} | Total Crossed: {tracker.in_count + tracker.out_count}", (28, y_off), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (150, 160, 175), 1, cv2.LINE_AA)


def run_pipeline(
    model_path: str = "yolov8n.pt",
    video_source: str = "0",
    line_y: int = 500,
    real_distance_m: float = 10.0,
    conf_thresh: float = 0.35,
    save_output: str = None,
):
    print("=" * 65)
    print(" KHỞI ĐỘNG HỆ THỐNG GIÁM SÁT GIAO THÔNG VÀ TỐC ĐỘ XE THỜI GIAN THỰC")
    print("=" * 65)
    print(f"[*] Model:          {model_path}")
    print(f"[*] Video Source:   {video_source}")
    print(f"[*] Line Y:         {line_y}")
    print(f"[*] Conf Threshold: {conf_thresh}")
    print("=" * 65)

    # 1. Khởi tạo YOLO model
    if not os.path.exists(model_path) and not model_path.endswith(".pt"):
        print(f"[WARN] File weights '{model_path}' không tồn tại. Tự động tải yolov8n.pt...")
        model_path = "yolov8n.pt"

    model = YOLO(model_path)

    # 2. Mở nguồn Video / Webcam
    source = int(video_source) if video_source.isdigit() else video_source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Không thể mở nguồn video: {video_source}")
        return

    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
    fps_in = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # Nếu line_y vượt quá chiều cao frame, chuẩn hóa về 60% chiều cao
    if line_y >= frame_h or line_y <= 0:
        line_y = int(frame_h * 0.60)
        print(f"[*] Điều chỉnh Line Y tự động = {line_y} (60% chiều cao frame)")

    tracker = SpeedAndLineCrossingTracker(
        line_y=line_y,
        real_distance_m=real_distance_m,
        fps_target=fps_in,
    )

    # Chuẩn bị VideoWriter nếu cần lưu
    writer = None
    if save_output:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(save_output, fourcc, fps_in, (frame_w, frame_h))

    prev_time = time.time()
    frame_count = 0
    fps_display = 30.0

    # Danh sách class COCO quan tâm: person(0), car(2), motorcycle(3), bus(5), truck(7)
    target_classes = list(COCO_CLASSES.keys())

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[*] Đã duyệt hết video hoặc camera ngắt kết nối.")
                break

            current_time = time.time()
            frame_count += 1
            if frame_count % 5 == 0:
                fps_display = 5 / max(0.001, current_time - prev_time)
                prev_time = current_time

            # 3. Chạy YOLO Tracking với ByteTrack
            results = model.track(
                source=frame,
                persist=True,
                tracker="bytetrack.yaml",
                classes=target_classes,
                conf=conf_thresh,
                verbose=False,
            )

            # 4. Trích xuất bounding boxes và track IDs
            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                for box in boxes:
                    if box.id is None:
                        continue

                    track_id = int(box.id[0].item())
                    cls_id = int(box.cls[0].item())
                    cls_name = COCO_CLASSES.get(cls_id, "car")
                    xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = map(int, xyxy)

                    # Cập nhật tracker
                    info = tracker.update(
                        track_id=track_id,
                        cls_name=cls_name,
                        bbox=(x1, y1, x2, y2),
                        current_time=current_time,
                    )

                    speed_kmh = info["speed_kmh"]
                    direction = info["direction"]
                    display_cls = info["class"]

                    # 5. Vẽ Bounding Box & Nhãn tốc độ lên frame
                    box_color = COLORS.get(display_cls, (0, 255, 0))
                    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

                    # Nhãn: "car #12 47 km/h [IN]"
                    dir_tag = f" [{direction}]" if direction != "IDLE" else ""
                    label_str = f"{display_cls} #{track_id} {round(speed_kmh)} km/h{dir_tag}"

                    (tw, th), _ = cv2.getTextSize(label_str, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                    cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 6, y1), box_color, -1)
                    cv2.putText(
                        frame,
                        label_str,
                        (x1 + 3, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (15, 18, 24),
                        2,
                        cv2.LINE_AA,
                    )

            # 6. Vẽ bảng thông số HUD tổng hợp
            draw_hud(frame, tracker, fps_display)

            # 7. Hiển thị ra cửa sổ OpenCV
            cv2.imshow("Smart Driving Assistant - Traffic Speed & Line Crossing", frame)

            if writer:
                writer.write(frame)

            # Nhấn phím 'q' để dừng, 'r' để reset bộ đếm
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                tracker.in_count = 0
                tracker.out_count = 0
                tracker.crossed_in_ids.clear()
                tracker.crossed_out_ids.clear()
                tracker.in_by_class.clear()
                tracker.out_by_class.clear()
                print("[*] Đã đặt lại toàn bộ bộ đếm Line Crossing.")

    finally:
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()

        print("\n" + "=" * 65)
        print(" TỔNG KẾT PHIÊN THEO DÕI GIAO THÔNG")
        print("=" * 65)
        print(f"Tổng lượt xe IN  (Tiến vào): {tracker.in_count}")
        print(f"Tổng lượt xe OUT (Rời đi)  : {tracker.out_count}")
        print(f"Tổng lượt qua vạch         : {tracker.in_count + tracker.out_count}")
        print("\nChi tiết qua vạch (OUT):")
        for k, v in tracker.out_by_class.items():
            print(f"  - {k:<10}: {v}")
        print("\nChi tiết qua vạch (IN):")
        for k, v in tracker.in_by_class.items():
            print(f"  - {k:<10}: {v}")
        print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLO Traffic Speed & Line Crossing Tracker")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Đường dẫn file trọng số YOLO (.pt)")
    parser.add_argument("--source", type=str, default="0", help="Nguồn video (0 cho webcam, hoặc đường dẫn file .mp4)")
    parser.add_argument("--line-y", type=int, default=500, help="Tọa độ Y của vạch ảo Virtual Line")
    parser.add_argument("--distance-m", type=float, default=10.0, help="Khoảng cách thực tế tham chiếu (mét)")
    parser.add_argument("--conf", type=float, default=0.35, help="Ngưỡng tin cậy phát hiện (Confidence)")
    parser.add_argument("--save", type=str, default=None, help="Đường dẫn lưu video kết quả (vd: output.mp4)")

    args = parser.parse_args()

    run_pipeline(
        model_path=args.model,
        video_source=args.source,
        line_y=args.line_y,
        real_distance_m=args.distance_m,
        conf_thresh=args.conf,
        save_output=args.save,
    )
