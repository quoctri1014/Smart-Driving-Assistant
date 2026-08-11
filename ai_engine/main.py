"""
main.py
-------
HỆ THỐNG GIÁM SÁT GIAO THÔNG THÔNG MINH (Smart Traffic AI)
Gộp 4 tính năng thường thấy trong các project Python + YOLO về giao thông:

  1. Đếm phương tiện theo vùng (Zone counting)
  2. Nhận diện biển số xe (License Plate Recognition)
  3. Phát hiện không đội mũ bảo hiểm (Helmet Detection)
  4. Cảnh báo va chạm / tiến lại gần nhanh (Collision Warning)

Chạy:
    python main.py
    python main.py --source 0                     # dùng webcam
    python main.py --source path/to/video.mp4
    python main.py --no-display                   # chạy ẩn, chỉ ghi file output

Tất cả cấu hình khác (model, ngưỡng, vùng zone...) chỉnh trong config.py
"""

import argparse
import time
import cv2

import config
from modules.detector import VehicleDetector
from modules.tracker import SimpleTracker
from modules.zone_manager import ZoneManager
from modules.plate_reader import PlateReader
from modules.helmet_checker import HelmetChecker
from modules.collision_warning import CollisionWarning
from modules.utils import draw_box, box_center


def parse_args():
    parser = argparse.ArgumentParser(description="Smart Traffic AI - Python + YOLO")
    parser.add_argument("--source", type=str, default=config.VIDEO_SOURCE,
                         help="Đường dẫn video / chỉ số webcam / URL RTSP")
    parser.add_argument("--output", type=str, default=config.OUTPUT_VIDEO_PATH,
                         help="Đường dẫn lưu video kết quả")
    parser.add_argument("--no-display", action="store_true",
                         help="Không hiện cửa sổ preview (chạy trên server)")
    return parser.parse_args()


def find_rider_for_motorbike(motorbike_track, person_tracks):
    """Tìm người (person track) đang ngồi trên xe máy dựa vào tâm điểm nằm trong box xe."""
    mx1, my1, mx2, my2 = motorbike_track.current_box
    for p in person_tracks:
        cx, cy = box_center(p.current_box)
        if mx1 <= cx <= mx2 and my1 <= cy <= my2 + (my2 - my1) * 0.3:
            return p
    return None


def main():
    args = parse_args()
    source = int(args.source) if str(args.source).isdigit() else args.source

    print("[Init] Đang tải model YOLO phương tiện...")
    detector = VehicleDetector()
    tracker = SimpleTracker()
    zone_manager = ZoneManager() if config.ENABLE_ZONE_COUNTING else None
    plate_reader = PlateReader() if config.ENABLE_LICENSE_PLATE else None
    helmet_checker = HelmetChecker() if config.ENABLE_HELMET_CHECK else None
    collision_warning = CollisionWarning() if config.ENABLE_COLLISION_WARNING else None

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Không mở được nguồn video: {source}")

    fps_in = cap.get(cv2.CAP_PROP_FPS) or 25
    writer = None
    frame_idx = 0
    t_start = time.time()

    print("[Run] Bắt đầu xử lý... (nhấn 'q' để thoát nếu có cửa sổ preview)")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1

        if config.RESIZE_WIDTH:
            h, w = frame.shape[:2]
            scale = config.RESIZE_WIDTH / w
            frame = cv2.resize(frame, (config.RESIZE_WIDTH, int(h * scale)))

        frame_h, frame_w = frame.shape[:2]

        # ---- 1) Phát hiện đối tượng ----
        detections = detector.detect(frame)
        det_pairs = [(d["box"], d["cls_name"]) for d in detections]

        # ---- 2) Theo dõi (gán ID bền vững) ----
        tracks = tracker.update(det_pairs, frame_idx)
        vehicle_tracks = [t for t in tracks if t.cls_name != "person"]
        person_tracks = [t for t in tracks if t.cls_name == "person"]

        # ---- 3) Đếm theo Zone ----
        if zone_manager:
            zone_manager.draw(frame)
            zone_manager.update(vehicle_tracks + person_tracks, frame_w, frame_h)

        # ---- 4) Vùng làn đường cho cảnh báo va chạm ----
        if collision_warning:
            collision_warning.draw_lane(frame)
            warnings = collision_warning.check(vehicle_tracks, frame_w, frame_h)
            warned_ids = {t.id for t, _ in warnings}
            if warnings:
                cv2.putText(frame, "!!! CANH BAO: XE PHIA TRUOC QUA GAN !!!",
                            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
        else:
            warned_ids = set()

        # ---- 5) Nhận diện biển số (chỉ cho xe, chạy cách quãng theo track) ----
        if plate_reader:
            for t in vehicle_tracks:
                if t.cls_name == "person":
                    continue
                need_ocr = (t.plate_text is None) and (frame_idx % config.PLATE_OCR_INTERVAL == 0)
                if need_ocr:
                    plate = plate_reader.read_plate(frame, t.current_box)
                    if plate:
                        t.plate_text = plate

        # ---- 6) Phát hiện mũ bảo hiểm cho xe máy ----
        if helmet_checker and helmet_checker.enabled:
            for t in vehicle_tracks:
                if t.cls_name != "motorbike":
                    continue
                rider = find_rider_for_motorbike(t, person_tracks)
                if rider is not None and rider.helmet_status is None:
                    rider.helmet_status = helmet_checker.check(frame, rider.current_box)

        # ---- 7) Vẽ kết quả lên khung hình ----
        for t in vehicle_tracks:
            color = (0, 0, 255) if t.id in warned_ids else (0, 200, 255)
            label = f"{t.cls_name} #{t.id}"
            if t.plate_text:
                label += f" [{t.plate_text}]"
            draw_box(frame, t.current_box, color, label,
                     config.LINE_THICKNESS, config.FONT_SCALE)

        for p in person_tracks:
            if p.helmet_status is False:
                color, label = (0, 0, 255), f"KHONG DOI MU #{p.id}"
            elif p.helmet_status is True:
                color, label = (0, 255, 0), f"co mu #{p.id}"
            else:
                color, label = (200, 200, 200), f"person #{p.id}"
            draw_box(frame, p.current_box, color, label,
                     config.LINE_THICKNESS, config.FONT_SCALE)

        # ---- 8) Thanh thông tin tổng quan ----
        elapsed = time.time() - t_start
        fps_proc = frame_idx / elapsed if elapsed > 0 else 0
        info = f"Frame {frame_idx} | FPS xu ly: {fps_proc:.1f}"
        cv2.putText(frame, info, (20, frame_h - 15), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 255, 255), 1, cv2.LINE_AA)

        # ---- 9) Ghi video output ----
        if args.output:
            if writer is None:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(args.output, fourcc, fps_in, (frame_w, frame_h))
            writer.write(frame)

        # ---- 10) Hiển thị ----
        if config.SHOW_WINDOW and not args.no_display:
            cv2.imshow("Smart Traffic AI - Python + YOLO", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

    print("\n===== KET QUA =====")
    if zone_manager:
        for zone, count in zone_manager.counts.items():
            print(f"{zone}: {count} phuong tien/nguoi di qua")
    print(f"Da xu ly {frame_idx} khung hinh trong {time.time() - t_start:.1f}s")
    if args.output:
        print(f"Video ket qua da luu tai: {args.output}")


if __name__ == "__main__":
    main()
