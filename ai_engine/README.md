# 🚦 Smart Traffic AI — Python + YOLO

**Cập nhật 12 chức năng:** xem [đối chiếu triển khai và cấu hình](../docs/feature-alignment-review.md). Bảng bốn chức năng dưới đây là nền tảng ban đầu; `main.py` đã nối nhóm A, nhóm B chạy độc lập qua backend. Chế độ một YOLO yêu cầu model đa lớp đã huấn luyện, không phải COCO mặc định.

Dự án giám sát giao thông thông minh, gộp **4 tính năng** phổ biến trong các
project Python + YOLO về giao thông (giống loại clip demo trên TikTok/Youtube):

| # | Tính năng | Mô tả |
|---|-----------|-------|
| 1 | **Zone Counting** | Chia khung hình thành các vùng (Zone 1, 2, 3...), đếm số xe/người đi qua từng vùng |
| 2 | **License Plate Recognition** | Nhận diện & đọc biển số xe bằng OCR |
| 3 | **Helmet Detection** | Phát hiện người lái xe máy có đội mũ bảo hiểm hay không |
| 4 | **Collision Warning** | Cảnh báo khi xe phía trước đang tiến lại gần quá nhanh |

Tất cả chạy trên **cùng 1 pipeline**, dùng chung 1 model YOLO phát hiện
phương tiện để tối ưu tốc độ xử lý.

---

## 📁 Cấu trúc dự án

```
traffic_ai_project/
├── main.py                    # Điểm chạy chính, điều phối toàn bộ pipeline
├── config.py                  # Cấu hình: nguồn video, model, ngưỡng, toạ độ zone...
├── requirements.txt
├── modules/
│   ├── detector.py            # Phát hiện phương tiện/người (YOLOv8 COCO)
│   ├── tracker.py             # Theo dõi đối tượng (gán ID bền vững, IoU tracker)
│   ├── zone_manager.py        # Quản lý & đếm theo vùng (zone)
│   ├── plate_reader.py        # Đọc biển số (EasyOCR)
│   ├── helmet_checker.py      # Phát hiện mũ bảo hiểm (cần model tự train)
│   ├── collision_warning.py   # Cảnh báo va chạm dựa trên tốc độ tăng bbox
│   └── utils.py                # Hàm dùng chung (vẽ, hình học)
├── models/                    # Nơi đặt model .pt tự train (helmet...)
├── sample_videos/             # Đặt video mẫu của bạn ở đây
└── output/                    # Video kết quả sẽ lưu ở đây
```

---

## ⚙️ Cài đặt

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

> Lần chạy đầu tiên, `ultralytics` sẽ tự động tải model `yolov8n.pt` (~6MB).
> `easyocr` cũng sẽ tự tải model nhận dạng ký tự trong lần chạy đầu.

---

## ▶️ Chạy thử

```bash
# Dùng video mẫu (sửa đường dẫn trong config.py hoặc truyền --source)
python main.py --source sample_videos/traffic.mp4

# Dùng webcam
python main.py --source 0

# Dùng luồng camera IP (RTSP)
python main.py --source rtsp://user:pass@192.168.1.10:554/stream

# Chạy ẩn (không hiện cửa sổ, ví dụ chạy trên server)
python main.py --source video.mp4 --no-display
```

Nhấn `q` trong cửa sổ preview để dừng. Video kết quả (có vẽ zone, bounding
box, biển số, cảnh báo...) sẽ được lưu vào `output/result.mp4`.

---

## 🔧 Tuỳ chỉnh nhanh (trong `config.py`)

- **Bật/tắt từng tính năng riêng lẻ**: `ENABLE_ZONE_COUNTING`,
  `ENABLE_LICENSE_PLATE`, `ENABLE_HELMET_CHECK`, `ENABLE_COLLISION_WARNING`
- **Toạ độ vùng đếm (Zone)**: sửa `ZONES` — toạ độ tính theo % chiều
  rộng/cao khung hình (0.0–1.0) nên không phụ thuộc độ phân giải video.
  Cách nhanh nhất để lấy toạ độ đúng ý bạn: chụp 1 khung hình từ video,
  mở bằng Paint/GIMP, ước lượng vị trí góc vùng theo tỉ lệ % rồi điền vào.
- **Ngưỡng cảnh báo va chạm**: `COLLISION_GROWTH_RATE_THRESHOLD` (giá trị
  càng nhỏ càng nhạy — dễ cảnh báo hơn).
- **Độ phân giải xử lý**: `RESIZE_WIDTH` — giảm xuống (vd 640) nếu máy yếu
  để tăng tốc độ xử lý (FPS).

---

## 🧠 Nâng cấp / huấn luyện thêm

### 1) Model phát hiện mũ bảo hiểm (Helmet Detection)
Model YOLO gốc (COCO) không có sẵn lớp "helmet". Bạn cần fine-tune riêng:

1. Tải 1 dataset mũ bảo hiểm có sẵn từ [Roboflow Universe](https://universe.roboflow.com)
   (tìm từ khoá "helmet detection yolov8"), export theo format YOLOv8.
2. Train:
   ```bash
   yolo task=detect mode=train data=helmet_dataset/data.yaml model=yolov8n.pt epochs=50 imgsz=640
   ```
3. Copy file `best.pt` vừa train vào `models/helmet_yolov8.pt` (đúng đường
   dẫn khai báo trong `config.py`).
4. Chạy lại `main.py` — tính năng helmet sẽ tự động kích hoạt.

### 2) Cải thiện độ chính xác biển số
Hiện tại `plate_reader.py` chạy OCR trực tiếp trên toàn bộ vùng ảnh xe rồi
lọc theo regex. Để chính xác hơn, bạn có thể:
- Train thêm 1 model YOLO nhỏ chuyên phát hiện **vị trí biển số** (dataset
  "license plate detection" trên Roboflow), crop đúng vùng biển số trước
  khi đưa vào EasyOCR.
- Áp dụng tiền xử lý ảnh (khử nhiễu, làm nét, chuyển ảnh xám + threshold)
  trước khi OCR để tăng độ chính xác trong điều kiện thiếu sáng.

### 3) Tracking chính xác hơn
Tracker hiện tại (`SimpleTracker`) dùng IoU đơn giản, đủ cho demo. Với
video có nhiều xe/che khuất nhiều, nên thay bằng **ByteTrack** hoặc
**DeepSORT** (đã có sẵn tích hợp trong `ultralytics`: dùng
`model.track(source=..., tracker="bytetrack.yaml")`).

---

## ⚠️ Lưu ý

- Đây là dự án mang tính **học tập / demo**, cảnh báo va chạm dùng heuristic
  (tốc độ tăng bounding box), KHÔNG thay thế được cảm biến radar/lidar
  trong hệ thống ADAS thực tế — không dùng để đưa ra quyết định an toàn
  thực sự khi lái xe.
- Nhận diện biển số/mũ bảo hiểm liên quan đến dữ liệu cá nhân — nếu triển
  khai thực tế (camera công cộng...), cần tuân thủ quy định pháp luật về
  bảo vệ dữ liệu cá nhân tại địa phương bạn.
