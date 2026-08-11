"""
config.py
---------
Cấu hình trung tâm cho hệ thống Smart Traffic AI.
Chỉnh sửa các giá trị dưới đây để phù hợp với video / camera của bạn,
KHÔNG cần sửa code bên trong các module.
"""

import os

# ============================================================
# 1) NGUỒN VIDEO
# ============================================================
# Có thể là: đường dẫn file video, chỉ số webcam (0, 1, ...),
# hoặc URL luồng RTSP/HTTP của camera IP.
VIDEO_SOURCE = "sample_videos/traffic.mp4"

# Ghi video kết quả ra file (None nếu không muốn ghi)
OUTPUT_VIDEO_PATH = "output/result.mp4"

# Thu nhỏ khung hình để xử lý nhanh hơn (None = giữ nguyên)
RESIZE_WIDTH = 960

# ============================================================
# 2) MODEL YOLO
# ============================================================
# Model phát hiện phương tiện / người (COCO pretrained, tự tải về)
VEHICLE_MODEL_PATH = "yolov8n.pt"

# Model phát hiện mũ bảo hiểm (bạn cần tự train hoặc tải model
# đã fine-tune trên tập dữ liệu helmet, xem README phần "Huấn luyện thêm")
HELMET_MODEL_PATH = "models/helmet_yolov8.pt"

# Ngưỡng tin cậy (confidence) khi phát hiện
CONF_VEHICLE = 0.35
CONF_HELMET = 0.4
CONF_PLATE = 0.35

# Các lớp (class) quan tâm trong model COCO gốc của YOLO
# 0: person, 1: bicycle, 2: car, 3: motorcycle, 5: bus, 7: truck
COCO_VEHICLE_CLASSES = [2, 3, 5, 7]
COCO_PERSON_CLASS = 0
COCO_MOTORBIKE_CLASS = 3

# ============================================================
# 3) BẬT / TẮT TỪNG TÍNH NĂNG
# ============================================================
ENABLE_ZONE_COUNTING = True       # Đếm xe theo vùng (Zone 1/2/3)
ENABLE_LICENSE_PLATE = True       # Nhận diện biển số
ENABLE_HELMET_CHECK = True        # Phát hiện không đội mũ bảo hiểm
ENABLE_COLLISION_WARNING = True   # Cảnh báo khoảng cách / va chạm gần

# ============================================================
# 4) ZONE COUNTING - toạ độ vùng đếm (theo % chiều rộng/cao khung hình
#    để không phụ thuộc độ phân giải video, giá trị 0.0 - 1.0)
# ============================================================
ZONES = {
    "Zone 1": [(0.05, 0.55), (0.35, 0.55), (0.30, 0.95), (0.02, 0.95)],
    "Zone 2": [(0.38, 0.55), (0.62, 0.55), (0.65, 0.95), (0.33, 0.95)],
    "Zone 3": [(0.65, 0.55), (0.98, 0.55), (0.98, 0.95), (0.68, 0.95)],
}

# ============================================================
# 5) CẢNH BÁO VA CHẠM
# ============================================================
# Vùng "làn đường phía trước" nơi ta theo dõi tốc độ tiến lại gần
# (toạ độ % giống ZONES ở trên)
COLLISION_LANE_POLYGON = [(0.30, 0.55), (0.70, 0.55), (0.95, 0.98), (0.05, 0.98)]

# Tốc độ tăng kích thước bounding box (theo % mỗi giây) để coi là "đang tới gần nhanh"
COLLISION_GROWTH_RATE_THRESHOLD = 0.05
# Số khung hình tối thiểu để tính tốc độ tăng trưởng ổn định
COLLISION_MIN_TRACK_LEN = 5

# ============================================================
# 6) NHẬN DIỆN BIỂN SỐ
# ============================================================
OCR_LANGUAGES = ["en"]     # EasyOCR ngôn ngữ đọc ký tự biển số
PLATE_OCR_INTERVAL = 1     # chỉ chạy OCR mỗi N khung hình / mỗi track để tiết kiệm CPU/GPU

# ============================================================
# 7) HIỂN THỊ
# ============================================================
SHOW_WINDOW = True         # Hiện cửa sổ preview khi chạy (tắt nếu chạy trên server không màn hình)
FONT_SCALE = 0.5
LINE_THICKNESS = 2

os.makedirs("output", exist_ok=True)
os.makedirs("models", exist_ok=True)

# ============================================================
# 8) DRIVER MONITOR (DMS)
# ============================================================
EAR_THRESHOLD = 0.25
YAWN_THRESHOLD = 0.6
MAX_CONTINUOUS_DRIVING_MINUTES = 240
REST_REMINDER_INTERVAL = 15
