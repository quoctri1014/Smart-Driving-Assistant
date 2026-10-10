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

import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

AI_ENGINE_DIR = Path(__file__).resolve().parent
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

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
from modules.speed_estimator import SpeedEstimator
from modules.safe_distance_calculator import SafeDistanceCalculator
from modules.speed_recommendation import recommend_speed
from modules.sign_detector import SignDetector
from modules.violation_manager import ViolationManager
from uuid import uuid4
from modules.utils import box_center
from ui import ADASUI, SystemState


def parse_args():
    parser = argparse.ArgumentParser(description="Smart Traffic AI - Python + YOLO")
    parser.add_argument("--source", type=str, default=config.VIDEO_SOURCE,
                         help="Đường dẫn video / chỉ số webcam / URL RTSP")
    parser.add_argument("--output", type=str, default=config.OUTPUT_VIDEO_PATH,
                         help="Đường dẫn lưu video kết quả")
    parser.add_argument("--no-display", action="store_true",
                         help="Không hiện cửa sổ preview (chạy trên server)")
    parser.add_argument("--max-frames", type=int, default=None,
                        help="Stop after N frames (for a quick smoke test)")
    parser.add_argument("--debug", action="store_true",
                        help="Show all tracks, people, zones and confidence details")
    parser.add_argument("--ego-speed", type=float, default=None,
                        help="Known ego speed in km/h for recorded-video demos; live use requires telemetry")
    parser.add_argument("--distance", type=float, default=None,
                        help="Measured distance to the warned vehicle in meters (recorded demo)")
    return parser.parse_args()


def find_rider_for_motorbike(motorbike_track, person_tracks):
    """Tìm người (person track) đang ngồi trên xe máy dựa vào tâm điểm nằm trong box xe."""
    mx1, my1, mx2, my2 = motorbike_track.current_box
    for p in person_tracks:
        cx, cy = box_center(p.current_box)
        if mx1 <= cx <= mx2 and my1 - (my2 - my1) <= cy <= my2 + (my2 - my1) * 0.3:
            return p
    return None


def detection_confidence_for_track(track, detections):
    """Match current detection confidence to a track for Debug UI only."""
    best_confidence = 0.0
    best_distance = float("inf")
    for detection in detections:
        if detection["cls_name"] != track.cls_name:
            continue
        distance = sum(
            abs(float(track.current_box[index]) - float(detection["box"][index]))
            for index in range(4)
        )
        if distance < best_distance:
            best_distance = distance
            best_confidence = float(detection["conf"])
    return best_confidence


def main():
    args = parse_args()
    source = int(args.source) if str(args.source).isdigit() else args.source
    debug_mode = args.debug or config.DEBUG_MODE
    ui = ADASUI(debug_mode=debug_mode)
    system_state = SystemState(source)

    print("[Init] Đang tải model YOLO phương tiện...")
    detector = VehicleDetector()
    tracker = SimpleTracker()
    zone_manager = ZoneManager() if config.ENABLE_ZONE_COUNTING else None
    plate_reader = PlateReader(debug=debug_mode) if config.ENABLE_LICENSE_PLATE else None
    helmet_checker = HelmetChecker() if config.ENABLE_HELMET_CHECK else None
    collision_warning = CollisionWarning() if config.ENABLE_COLLISION_WARNING else None

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        system_state.set_offline()
        raise RuntimeError(f"Không mở được nguồn video: {source}")

    fps_in = cap.get(cv2.CAP_PROP_FPS) or 25
    speed_estimator = SpeedEstimator(fps=fps_in, pixels_per_meter=config.SPEED_PIXELS_PER_METER if config.SPEED_CAMERA_MODE == "fixed" else None)
    safe_distance_calc = SafeDistanceCalculator()
    sign_detector = SignDetector(config.SIGN_MODEL_PATH)
    violation_manager = ViolationManager(export_path=f"output/violations-{uuid4().hex}.csv")
    last_speed_limit = None
    writer = None
    frame_idx = 0
    t_start = time.time()

    print("[Run] Bắt đầu xử lý... (nhấn 'q' để thoát nếu có cửa sổ preview)")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if args.max_frames is not None and frame_idx >= args.max_frames:
            break
        frame_idx += 1
        if plate_reader:
            plate_reader.debug = ui.debug_mode

        if config.RESIZE_WIDTH:
            h, w = frame.shape[:2]
            scale = config.RESIZE_WIDTH / w
            frame = cv2.resize(frame, (config.RESIZE_WIDTH, int(h * scale)))
            if speed_estimator.pixels_per_meter is not None:
                speed_estimator.pixels_per_meter = config.SPEED_PIXELS_PER_METER * scale

        frame_h, frame_w = frame.shape[:2]

        # ---- 1) Phát hiện đối tượng ----
        detections = detector.detect(frame)
        det_pairs = [(d["box"], d["cls_name"]) for d in detections
                     if d["cls_name"] in ("person", "car", "motorbike", "truck", "bus", "bicycle")]

        # ---- 2) Theo dõi (gán ID bền vững) ----
        timestamp = frame_idx / fps_in if isinstance(source, str) and not source.startswith(("rtsp:", "http:", "https:")) else time.monotonic()
        tracks = tracker.update(det_pairs, frame_idx, timestamp=timestamp)
        vehicle_tracks = [t for t in tracks if t.cls_name != "person"]
        person_tracks = [t for t in tracks if t.cls_name == "person"]

        # ---- 3) Đếm theo Zone ----
        if zone_manager:
            zone_manager.update(vehicle_tracks + person_tracks, frame_w, frame_h)

        # ---- 4) Vùng làn đường cho cảnh báo va chạm ----
        if collision_warning:
            warnings = collision_warning.check(vehicle_tracks, frame_w, frame_h)
            warned_ids = {t.id for t, _ in warnings}
        else:
            warnings = []
            warned_ids = set()

        # ---- 6) Phát hiện mũ bảo hiểm cho xe máy ----
        if helmet_checker:
            for t in vehicle_tracks:
                if t.cls_name != "motorbike":
                    continue
                rider = find_rider_for_motorbike(t, person_tracks)
                if rider is not None:
                    rider.helmet_status = helmet_checker.check(frame, rider.current_box, detections)

        # Nhóm A: speed, violations, sign and advice all consume the same tracks.
        # Localize once, then prioritize OCR for confirmed helmet violations.
        force_ids = {bike.id for bike in vehicle_tracks
                     if bike.cls_name == "motorbike"
                     and (rider := find_rider_for_motorbike(bike, person_tracks)) is not None
                     and rider.helmet_status is False}
        plate_detections = []
        if plate_reader:
            plate_detections = plate_reader.process_tracks(
                frame, vehicle_tracks, frame_idx, force_ids=force_ids,
                shared_detections=detections if config.ROAD_MODEL_SHARED_CLASSES else None,
            )
            for plate in plate_detections:
                if plate["accepted"] and plate["track"] is not None:
                    system_state.record_plate(
                        track_id=plate["track"].id, text=plate["text"],
                        confidence=plate["ocr_confidence"], status=plate["status"], crop=plate["crop"],
                    )

        speed_map = speed_estimator.update(vehicle_tracks, frame_idx, timestamp=timestamp)
        violation_manager.process_frame(vehicle_tracks, person_tracks, frame_idx,
                                        frame=frame)
        sign = sign_detector.detect(frame, detections)
        if sign.get("speed_limit") is not None:
            last_speed_limit = sign["speed_limit"]
        safe_distance = safe_distance_calc.calculate(warnings, speed_map, ego_speed_kmh=args.ego_speed, estimated_distance_m=args.distance)
        advice = recommend_speed(
            current_speed=args.ego_speed or 0.0,
            vehicle_count_in_zone=sum(zone_manager.vehicle_occupancy.values()) if zone_manager else len(vehicle_tracks),
            sign_speed_limit=last_speed_limit,
            safe_distance_speed=safe_distance["recommended_speed_kmh"] if safe_distance else None,
            has_collision_warning=bool(warnings),
        )

        # ---- 7) Chuyển kết quả AI sang state chỉ dành cho UI ----
        elapsed = time.time() - t_start
        fps_proc = frame_idx / elapsed if elapsed > 0 else 0
        system_state.update_frame(vehicle_tracks, warnings, fps_proc, frame_idx)
        frame_result = {
            "vehicles": [
                {
                    "id": track.id,
                    "class": track.cls_name,
                    "box": track.current_box,
                    "confidence": detection_confidence_for_track(track, detections),
                }
                for track in vehicle_tracks
            ],
            "people": [
                {
                    "id": track.id,
                    "box": track.current_box,
                    "helmet_status": track.helmet_status,
                }
                for track in person_tracks
            ],
            "plates": plate_detections,
            "warned_ids": warned_ids,
        }

        # Zone/lane are debug presentation layers; update/check always run above.
        # AI đã xử lý xong frame; render trực tiếp để tránh copy toàn khung hình.
        camera_frame = frame
        if ui.debug_mode:
            if zone_manager:
                zone_manager.draw(camera_frame)
            if collision_warning:
                collision_warning.draw_lane(camera_frame)
        ui.render_camera(camera_frame, frame_result, system_state)
        for track in vehicle_tracks:
            if track.id in speed_map:
                x, y = map(int, track.current_box[:2])
                cv2.putText(camera_frame, f"{speed_map[track.id]:.1f} km/h", (x, max(18, y - 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        lines = []
        if last_speed_limit is not None:
            lines.append(f"Speed limit: {last_speed_limit} km/h")
        if advice["recommended_speed"] is not None:
            lines.append(f"Suggested max: {advice['recommended_speed']:.0f} km/h")
        if safe_distance:
            lines.append(f"Suggested gap: {safe_distance['recommended_distance_m']:.0f} m")
        for index, line in enumerate(lines):
            cv2.putText(camera_frame, line, (15, 35 + index * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # ---- 8) Ghi video output ----
        if args.output:
            if writer is None:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(args.output, fourcc, fps_in, (frame_w, frame_h))
            writer.write(camera_frame)

        # ---- 9) Hiển thị dashboard ADAS ----
        if config.SHOW_WINDOW and not args.no_display:
            ui.initialize_window()
            dashboard = ui.compose(camera_frame, system_state)
            cv2.imshow(ui.WINDOW_NAME, dashboard)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            ui.handle_key(key)

    cap.release()
    if writer:
        writer.release()
    system_state.set_offline()
    cv2.destroyAllWindows()

    if plate_reader:
        plate_reader.print_debug_summary()

    print("\n===== KET QUA =====")
    if zone_manager:
        for zone, count in zone_manager.counts.items():
            print(f"{zone}: {count} phuong tien/nguoi di qua")
    print(f"Da xu ly {frame_idx} khung hinh trong {time.time() - t_start:.1f}s")
    if args.output:
        print(f"Video ket qua da luu tai: {args.output}")


if __name__ == "__main__":
    main()
