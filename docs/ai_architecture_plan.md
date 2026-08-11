# AI Architecture Plan — Smart Driving Assistant

> **Tài liệu kế hoạch kiến trúc AI** cho dự án Hệ thống Trợ lý Lái xe Thông minh.
> Phiên bản: 1.0 | Người thực hiện: Thành viên 1 (AI/CV Engineer)

---

## 1. Tổng Quan Kiến Trúc AI 2 Luồng Camera

Hệ thống AI xử lý **2 luồng camera độc lập** theo thời gian thực:

```
┌─────────────────────────────────────────────────────────┐
│                  SMART DRIVING ASSISTANT                │
│                  AI PIPELINE ARCHITECTURE               │
├────────────────────────┬────────────────────────────────┤
│   ROAD-FACING CAMERA   │    DRIVER-FACING CAMERA        │
│   (WebSocket Stream 1) │    (WebSocket Stream 2)        │
│   /ws/v1/stream        │    /ws/v1/driver-stream        │
├────────────────────────┼────────────────────────────────┤
│ • Vehicle Detection    │ • Face Landmark Detection      │
│ • Object Tracking      │ • Drowsiness Detection (EAR)   │
│ • Collision Warning    │ • Yawn Detection (MAR)         │
│ • Speed Advisor        │ • Seatbelt Detection           │
│ • Sign Recognition     │ • Continuous Drive Time Track  │
│ • Plate Reader         │                                │
│ • Helmet Check         │                                │
└────────────────────────┴────────────────────────────────┘
```

---

## 2. Luồng Road-Facing Camera

### 2.1 Module: Vehicle Detection & Tracking
- **Model**: YOLOv8n (COCO pretrained) — `ai_engine/yolov8n.pt`
- **Framework**: `ultralytics`
- **Các lớp quan tâm**: car (2), motorcycle (3), bus (5), truck (7), person (0)
- **Ngưỡng confidence**: 0.35
- **Tracking**: SimpleTracker (IoU-based) — `modules/tracker.py`
- **Input**: Frame JPEG nhị phân qua WebSocket
- **Output**: List `VehicleDetection` với `id`, `bbox`, `class`, `zone`

### 2.2 Module: Zone Counting
- **File**: `modules/zone_manager.py`
- **Mô tả**: Phân chia khung hình thành 3 vùng (Zone 1/2/3) bằng polygon đa giác
- **Tọa độ zone**: dạng tỷ lệ % (0.0 – 1.0) không phụ thuộc độ phân giải
- **Config**: `config.py → ZONES`

### 2.3 Module: Collision Warning
- **File**: `modules/collision_warning.py`
- **Thuật toán**: Theo dõi tốc độ tăng diện tích bounding box theo thời gian (Growth Rate)
- **Ngưỡng cảnh báo**:
  - `growth_rate > 0.05 / giây` → `level = "warning"`
  - `growth_rate > 0.15 / giây` → `level = "danger"`
- **Output Schema**: `CollisionWarning { level, distance_estimate }`

### 2.4 Module: Speed Advisor
- **File**: `modules/speed_advisor.py`
- **Input**: `vehicle_speed` (km/h) từ metadata JSON gửi kèm frame
- **Logic**: So sánh tốc độ hiện tại với mật độ giao thông phát hiện được
- **Output Schema**: `SpeedAdvice { current_speed, recommended_speed, reason }`

### 2.5 Module: Sign Recognition
- **File**: `modules/sign_recognition.py`
- **Model**: YOLOv8n fine-tuned trên GTSRB + custom VN dataset
- **Dataset**: GTSRB (German Traffic Sign Recognition Benchmark) — 43 lớp
- **Model path**: `models/sign_yolov8.pt` *(cần train — xem Dataset Catalog)*
- **Output Schema**: `TrafficSign { sign_type, speed_limit }`

### 2.6 Module: Plate Reader
- **File**: `modules/plate_reader.py`
- **Framework**: EasyOCR (`languages=["en"]`)
- **Tối ưu**: Chỉ chạy OCR mỗi N frame (`PLATE_OCR_INTERVAL = 1`)
- **Output Schema**: `PlateDetection { plate_text, bbox, confidence }`

### 2.7 Module: Helmet Detection
- **File**: `modules/helmet_checker.py`
- **Model**: YOLOv8n fine-tuned — `models/helmet_yolov8.pt`
- **Trạng thái hiện tại**: ⚠️ **Model chưa có** — feature tự động tắt
- **Dataset**: Roboflow Universe "helmet detection yolov8" (2 lớp: helmet / no-helmet)
- **Hướng dẫn train**: Xem `docs/dataset_catalog.md` → Mục 3

---

## 3. Luồng Driver-Facing Camera

### 3.1 Module: Drowsiness Detection
- **File**: `modules/driver_monitor.py → DrowsinessDetector`
- **Framework**: MediaPipe Face Mesh (468 landmarks)
- **Thuật toán EAR (Eye Aspect Ratio)**:
  ```
  EAR = (|p2-p6| + |p3-p5|) / (2 × |p1-p4|)
  ```
  - `EAR < 0.25` trong **15 frames liên tiếp** → `is_drowsy = True`
  - `alert_level = "drowsy"` → kích hoạt cảnh báo
- **Thuật toán MAR (Mouth Aspect Ratio)**: Phát hiện ngáp
  - `MAR > 0.6` → tăng `yawn_count`

### 3.2 Module: Seatbelt Detection
- **File**: `modules/driver_monitor.py → SeatbeltDetector`
- **Model**: YOLOv8n fine-tuned `models/seatbelt_yolov8.pt`
- **Trạng thái**: ⚠️ Model chưa có — fallback: `seatbelt_on = True` (giả định)

### 3.3 Module: Continuous Drive Time
- **File**: `modules/driver_monitor.py`
- **Logic**: Đếm thời gian lái xe liên tục
  - `> 240 phút` → cảnh báo nghỉ ngơi
  - Nhắc lại mỗi 15 phút

---

## 4. Luồng Xử Lý Server — FastAPI

```
Client (Web/Mobile)
    │
    │ (1) Binary JPEG frame  →  WebSocket
    │ (2) JSON metadata      →  { "type": "metadata", "vehicle_speed": 60 }
    ▼
FastAPI WebSocket Handler (stream_handler.py)
    │
    ├── cv2.imdecode(bytes) → frame (numpy array)
    │
    ├── asyncio.to_thread(session.process_frame, frame, speed)
    │       │
    │       ├── VehicleDetector.detect()
    │       ├── SimpleTracker.update()
    │       ├── CollisionWarning.update()
    │       ├── SpeedAdvisor.suggest()
    │       ├── SignRecognition.detect()
    │       └── PlateReader.read()
    │
    ├── DetectionResult.model_dump() → JSON
    │
    ├── [Async Task] save violation image → image_storage
    ├── [Async Task] create_violation() → PostgreSQL
    │
    └── websocket.send_json({"type": "detection_result", "data": ...})
```

---

## 5. Schema Đầu Ra

### DetectionResult (Road)
```json
{
  "frame_id": 42,
  "timestamp": 1690000000.123,
  "vehicles": [
    { "id": 1, "bbox": {"x1": 10, "y1": 20, "x2": 100, "y2": 150}, "class": "car", "zone": "Zone 2" }
  ],
  "plates": [{ "plate_text": "51A-12345", "bbox": {...}, "confidence": 0.92 }],
  "helmet_violations": [],
  "collision_warning": { "level": "warning", "distance_estimate": 12.5 },
  "speed_advice": { "current_speed": 65, "recommended_speed": 50, "reason": "speed_limit_exceeded" },
  "traffic_signs": [{ "sign_type": "stop", "speed_limit": null }],
  "processing_time_ms": 38.4
}
```

### DriverMonitorResult (Driver)
```json
{
  "frame_id": 10,
  "timestamp": 1690000010.0,
  "drowsiness": { "is_drowsy": false, "ear_value": 0.31, "yawn_count": 1, "alert_level": "normal" },
  "seatbelt": { "seatbelt_on": true, "confidence": 0.95 },
  "driving_time": { "continuous_minutes": 45.2, "should_rest": false, "message": "OK" },
  "processing_time_ms": 12.1
}
```

---

## 6. Trạng Thái Hiện Tại Các Module

| Module | File | Model | Trạng thái |
|---|---|---|---|
| Vehicle Detection | `detector.py` | `yolov8n.pt` | ✅ ACTIVE |
| Object Tracker | `tracker.py` | — | ✅ ACTIVE |
| Zone Manager | `zone_manager.py` | — | ✅ ACTIVE |
| Collision Warning | `collision_warning.py` | — | ✅ ACTIVE |
| Speed Advisor | `speed_advisor.py` | — | ✅ ACTIVE |
| Sign Recognition | `sign_recognition.py` | `models/sign_yolov8.pt` | ⚠️ Cần model |
| Plate Reader | `plate_reader.py` | EasyOCR | ✅ ACTIVE |
| Helmet Checker | `helmet_checker.py` | `models/helmet_yolov8.pt` | ⚠️ Cần model |
| Drowsiness (EAR) | `driver_monitor.py` | MediaPipe | ✅ ACTIVE |
| Seatbelt | `driver_monitor.py` | `models/seatbelt_yolov8.pt` | ⚠️ Cần model |

---

## 7. Thông Số Hiệu Năng (Benchmark)

| Thông số | CPU (không GPU) | GPU (CUDA) |
|---|---|---|
| Vehicle Detection | ~80ms/frame | ~15ms/frame |
| MediaPipe Face Mesh | ~20ms/frame | ~8ms/frame |
| EasyOCR (plate) | ~200ms/plate | ~50ms/plate |
| End-to-end latency | ~150-300ms | ~30-50ms |
| FPS (Road stream) | ~5-8 FPS | ~20-30 FPS |

> Hiện tại hệ thống chạy trên **CPU** (không có GPU). EasyOCR thông báo: *"Neither CUDA nor MPS are available – defaulting to CPU"*.
