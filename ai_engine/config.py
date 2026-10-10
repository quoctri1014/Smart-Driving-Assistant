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
VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "0")

# Ghi video kết quả ra file (None nếu không muốn ghi)
OUTPUT_VIDEO_PATH = "output/result.mp4"

# Thu nhỏ khung hình để xử lý nhanh hơn (None = giữ nguyên)
RESIZE_WIDTH = None

# ============================================================
# 2) MODEL YOLO
# ============================================================
# Model phát hiện phương tiện / người (COCO pretrained)
VEHICLE_MODEL_PATH = "models/yolov8n.pt" if os.path.exists("models/yolov8n.pt") else "yolov8n.pt"
ROAD_MODEL_SHARED_CLASSES = False  # True khi model có cả person/vehicle/helmet/no_helmet/license_plate/speed_limit_N
PLATE_MODEL_PATH = "models/license_plate.pt"

# Model phát hiện mũ bảo hiểm (tự động nạp weights .pt hoặc .onnx có sẵn trong dự án)
_HELMET_CANDIDATES = [
    "models/helmet_yolov8.pt",
    "models/helmet.onnx",
    "web-app/public/models/helmet.onnx",
]
HELMET_MODEL_PATH = next((p for p in _HELMET_CANDIDATES if os.path.exists(p)), "models/helmet.onnx")

# Ngưỡng tin cậy (confidence) khi phát hiện
CONF_VEHICLE = 0.20               # Hạ từ 0.35 xuống 0.20 để bắt trọn xe máy/ô tô bị che khuất
CONF_HELMET = 0.4
CONF_PLATE = 0.05
# Ngưỡng thấp để YOLO sinh proposal và chuyển qua OCR
CONF_PLATE_DETECTION = 0.10      # Hạ từ 0.15 xuống 0.10 để bắt biển số ở xa
PLATE_CONF_THRESHOLD = 0.15      # Hạ từ 0.20 xuống 0.15 để tăng độ nhạy ALPR

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
COLLISION_GROWTH_RATE_THRESHOLD = 0.30  # giảm từ 0.35→0.30 để cảnh báo sớm hơn
# Số khung hình tối thiểu để tính tốc độ tăng trưởng ổn định
COLLISION_MIN_TRACK_LEN = 6  # tăng từ 5→6 để ổn định hơn
# Số frame liên tiếp phải kích hoạt trước khi hiển thị cảnh báo (tránh flickering)
COLLISION_SMOOTHING_FRAMES = 3
# Sau bao nhiêu frame không có cảnh báo thì xóa trạng thái warning
COLLISION_CLEAR_FRAMES = 8

# ============================================================
# 6) NHẬN DIỆN BIỂN SỐ
# ============================================================
OCR_LANGUAGES = ["en"]     # EasyOCR ngôn ngữ đọc ký tự biển số
PLATE_OCR_USE_GPU = True
PLATE_OCR_INTERVAL = 2     # Tăng tần suất quét (2 frames) để phản hồi nhanh như app thị trường
PLATE_IMAGE_SIZE = 640     # Độ phân giải chuẩn native của YOLOv8n để phát hiện chính xác nhất
PLATE_OCR_MIN_VOTES = 1     # Cập nhật kết quả ngay khi đọc được OCR
PLATE_CONFIRM_MIN_RATIO = 0.50

# Lọc proposal trước OCR
PLATE_ASSOC_PADDING_RATIO = 0.35  # Mở rộng vùng liên kết xe máy / ô tô
PLATE_MIN_VEHICLE_OVERLAP = 0.15
PLATE_MIN_PADDED_OVERLAP = 0.10
PLATE_MIN_ASPECT_RATIO = 0.85     # Hỗ trợ biển số xe máy 2 dòng vuông (1.1 - 1.4)
PLATE_MAX_ASPECT_RATIO = 7.00
PLATE_MIN_WIDTH = 12             # Bắt được cả biển nhỏ ở xa
PLATE_MIN_HEIGHT = 6
PLATE_MIN_AREA = 60
PLATE_MAX_VEHICLE_AREA_RATIO = 0.50

# Bộ nhớ crop theo chính Track ID của vehicle tracker hiện tại
PLATE_CROP_BUFFER_SIZE = 16
PLATE_TOP_CROPS = 4
PLATE_MIN_CROPS_FOR_OCR = 1  # OCR ngay từ crop đầu tiên
PLATE_TRACK_TTL_FRAMES = 120

# Quality scoring và các biến thể preprocessing cho EasyOCR
PLATE_MIN_SHARPNESS = 5.0     # Chấp nhận thêm trường hợp video mờ/chuyển động
PLATE_MIN_BRIGHTNESS = 10.0
PLATE_MAX_BRIGHTNESS = 250.0
PLATE_MIN_CONTRAST = 5.0
PLATE_MIN_QUALITY_SCORE = 0.15
PLATE_SHARPNESS_REFERENCE = 1000.0
PLATE_SIZE_REFERENCE = 50.0
PLATE_RESIZE_SCALE = 3.0
PLATE_TARGET_OCR_WIDTH = 320   # Đưa biển số về độ rộng tối ưu 280-360px
PLATE_DESKEW_ENABLED = True    # Bật tự động nắn thẳng phối cảnh góc nghiêng
PLATE_CLAHE_CLIP_LIMIT = 2.5
PLATE_THRESHOLD_MIN_STD = 10.0
PLATE_CONFIRM_MIN_VOTES = 2    # Số lần nhận diện ổn định để chốt biển số chính thức

# ============================================================
# 7) HIỂN THỊ
# ============================================================
SHOW_WINDOW = True         # Hiện cửa sổ preview khi chạy (tắt nếu chạy trên server không màn hình)
DEBUG_MODE = False         # Có thể bật bằng config hoặc tham số dòng lệnh --debug
PREVIEW_MAX_WIDTH = 1280   # chỉ thu nhỏ cửa sổ xem, không làm giảm chất lượng xử lý/output
PREVIEW_MAX_HEIGHT = 720
FONT_SCALE = 0.5
LINE_THICKNESS = 2

# Giao dien ADAS (chi anh huong lop hien thi, khong thay doi pipeline AI)
UI_WIDTH = 1440
UI_HEIGHT = 810
UI_HEADER_HEIGHT = 64
UI_TAB_HEIGHT = 60
UI_MARGIN = 14
UI_SIDEBAR_RATIO = 0.25
UI_HISTORY_LIMIT = 300
UI_PLATE_HISTORY_LIMIT = 60
# Nguong phan cap DANGER tren UI so voi nguong canh bao cua collision module.
UI_DANGER_RATE_MULTIPLIER = 1.75

os.makedirs("output", exist_ok=True)
os.makedirs("models", exist_ok=True)

# ============================================================
# 8) DRIVER MONITOR (DMS)
# ============================================================
EAR_THRESHOLD = 0.25           # ngưỡng Eye Aspect Ratio để coi là mắt nhắm
EAR_CLOSED_FRAMES_CRITICAL = 15  # số frame liên tiếp mắt nhắm để báo ngủ gật
EAR_CLOSED_FRAMES_WARNING = 8    # số frame để báo nguy hiểm mức cảnh báo
YAWN_THRESHOLD = 0.55          # giảm nhẹ từ 0.6→0.55 để phát hiện ngáp sớm hơn
YAWN_COUNT_WARNING = 2         # số lần ngáp trước khi cảnh báo
YAWN_COUNT_CRITICAL = 4        # số lần ngáp để cảnh báo nghiêm trọng
MAX_CONTINUOUS_DRIVING_MINUTES = 240   # 4 giờ theo yêu cầu hệ thống
REST_REQUIRED_MINUTES = 15.0         # Ngưỡng nghỉ của ứng dụng, có thể cấu hình
REST_REMINDER_INTERVAL = 10    # nhắc nghỉ sớm hơn (15→10 phút trước khi hết limit)

# ============================================================
# 9) SPEED ESTIMATOR — Ước lượng tốc độ xe (#5)
# ============================================================
# Số pixel tương đương 1 mét trong frame.
# Giá trị này cần căn chỉnh theo camera thực tế của bạn:
#   Cách đo: đặt vật thể biết kích thước (vd: xe dài 4.5m) vào frame,
#   đo số pixel chiều dài → SPEED_PIXELS_PER_METER = pixel_length / 4.5
SPEED_PIXELS_PER_METER = None  # Chỉ đặt sau khi đo trên camera cố định
SPEED_CAMERA_MODE = "moving"  # "fixed" cho camera đã calibration; dashcam dùng GPS
SIGN_MODEL_PATH = None
SIGN_SPEED_LABELS = {}  # Ví dụ {"speed_limit_50": 50}; phải khớp nhãn model
SEATBELT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "seatbelt.pt")
FACE_LANDMARKER_PATH = os.path.join(os.path.dirname(__file__), "models", "face_landmarker.task")
YAWN_WINDOW_SECONDS = 60.0

# Số frame dùng để trung bình hoá tốc độ (giảm noise)
SPEED_SMOOTH_FRAMES = 10

# Tốc độ tối đa hợp lý (km/h) — lọc nhiễu phép tính
SPEED_MAX_REASONABLE = 200.0
