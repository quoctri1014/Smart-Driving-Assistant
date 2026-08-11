# Dataset Catalog — Smart Driving Assistant

> **Danh mục Dataset** cho các module AI trong dự án.
> Phiên bản: 1.0 | Người thực hiện: Thành viên 1 (AI/CV Engineer)

---

## 1. Vehicle Detection (Đã có — COCO Pretrained)

| Thông tin | Chi tiết |
|---|---|
| **Dataset** | MS COCO 2017 |
| **Số lượng** | 118,287 ảnh train, 5,000 val |
| **Lớp sử dụng** | car (2), motorcycle (3), bus (5), truck (7), person (0) |
| **Model** | `yolov8n.pt` — tự động tải khi chạy lần đầu |
| **Trạng thái** | ✅ Không cần train thêm |
| **Nguồn** | Ultralytics (tải tự động) |

---

## 2. Traffic Sign Recognition (Cần train)

### 2a. Dataset Quốc Tế — GTSRB
| Thông tin | Chi tiết |
|---|---|
| **Dataset** | German Traffic Sign Recognition Benchmark (GTSRB) |
| **Số lượng** | 51,839 ảnh, 43 lớp biển báo |
| **Format** | PNG + CSV annotations |
| **Tải về** | https://benchmark.ini.rub.de/gtsrb_dataset.html |
| **Kaggle** | https://www.kaggle.com/datasets/meowmeowmeowmeowmeow/gtsrb-german-traffic-sign |

### 2b. Dataset Việt Nam — Tự thu thập
| Thông tin | Chi tiết |
|---|---|
| **Biển báo tốc độ** | 50 ảnh/biển × các mức 40/60/80/100 km/h |
| **Biển cấm** | 200 ảnh biển cấm phổ biến VN |
| **Biển hiệu lệnh** | 150 ảnh |
| **Phương pháp** | Script crawl Google Images + annotation bằng LabelImg |
| **Script** | `ai-engine/train.py` |

### Hướng dẫn train Sign Recognition
```bash
cd ai-engine

# 1. Chuẩn bị dataset theo cấu trúc YOLOv8
#    datasets/signs/images/train/  &  datasets/signs/labels/train/

# 2. Tạo file cấu hình
#    datasets/signs.yaml

# 3. Train
python train.py --task sign --epochs 100 --imgsz 640

# 4. Model output
#    runs/detect/sign_train/weights/best.pt
#    → copy vào models/sign_yolov8.pt
```

**Model path**: `ai-engine/models/sign_yolov8.pt`  
**Trạng thái**: ⚠️ Chưa có — cần thu thập dataset và train

---

## 3. Helmet Detection (Cần train)

### Dataset từ Roboflow Universe
| Thông tin | Chi tiết |
|---|---|
| **Dataset đề xuất** | "Helmet Detection" trên Roboflow Universe |
| **URL** | https://universe.roboflow.com/search?q=helmet+detection+yolov8 |
| **Số lượng** | ~5,000 ảnh (tùy dataset chọn) |
| **Lớp** | 2 lớp: `helmet` (0), `no-helmet` (1) |
| **Format** | YOLOv8 (download trực tiếp từ Roboflow) |

### Dataset thay thế
| Dataset | URL | Ghi chú |
|---|---|---|
| Safety Helmet Detection | https://www.kaggle.com/datasets/vodan37/safety-helmet-detection | ~7,000 ảnh |
| Hardhat Workers | https://universe.roboflow.com/joseph-nelson/hard-hat-workers | 5,000 ảnh |

### Hướng dẫn train Helmet Detection
```bash
cd ai-engine

# 1. Download dataset từ Roboflow (format YOLOv8)
#    Hoặc dùng Roboflow Python API:
pip install roboflow
# python -c "from roboflow import Roboflow; rf = Roboflow(api_key='YOUR_KEY'); ..."

# 2. Train
python train.py --task helmet --epochs 80 --imgsz 416

# 3. Model output → copy vào
#    models/helmet_yolov8.pt
```

**Model path**: `ai-engine/models/helmet_yolov8.pt`  
**Trạng thái**: ⚠️ Chưa có — module tự động tắt khi thiếu model

---

## 4. Seatbelt Detection (Cần train)

| Thông tin | Chi tiết |
|---|---|
| **Dataset đề xuất 1** | https://universe.roboflow.com/seatbelt-detection |
| **Dataset đề xuất 2** | https://www.kaggle.com/datasets/dasmehdixtr/seatbelt-dataset |
| **Số lượng** | ~3,000 ảnh |
| **Lớp** | 2 lớp: `seatbelt` (0), `no-seatbelt` (1) |

**Model path**: `ai-engine/models/seatbelt_yolov8.pt`  
**Trạng thái**: ⚠️ Chưa có — fallback: giả định `seatbelt_on = True`

---

## 5. Driver Monitoring — Drowsiness (Không cần train riêng)

| Thông tin | Chi tiết |
|---|---|
| **Framework** | MediaPipe Face Mesh |
| **Phương pháp** | Rule-based (EAR < 0.25, MAR > 0.6) |
| **Dataset** | Không cần — dùng 468 landmark tính sẵn của MediaPipe |
| **Trạng thái** | ✅ Hoạt động ngay, không cần train |

Nếu muốn nâng cấp bằng Deep Learning:
- Dataset: **YawDD** (Yawning Detection Dataset): http://www.site.uottawa.ca/~shervin/yawning/
- Dataset: **NTHU-DDD** (NTHU Drowsy Driver): có trên GitHub

---

## 6. License Plate OCR (Đã có — EasyOCR)

| Thông tin | Chi tiết |
|---|---|
| **Framework** | EasyOCR |
| **Ngôn ngữ** | `["en"]` — ký tự Latin |
| **Dataset** | Pretrained — không cần train thêm |
| **Trạng thái** | ✅ Hoạt động ngay |
| **Giới hạn** | Độ chính xác giảm với biển số có font đặc biệt hoặc bị che khuất |

---

## 7. Tổng Kết Trạng Thái Dataset

| Module | Dataset | Trạng thái | Ưu tiên |
|---|---|---|---|
| Vehicle Detection | MS COCO (tự tải) | ✅ Sẵn sàng | — |
| Driver Drowsiness | MediaPipe (built-in) | ✅ Sẵn sàng | — |
| License Plate OCR | EasyOCR (built-in) | ✅ Sẵn sàng | — |
| Traffic Sign (quốc tế) | GTSRB | ⚠️ Cần tải + train | 🔴 Cao |
| Traffic Sign (VN) | Tự thu thập | ⚠️ Cần thu thập | 🔴 Cao |
| Helmet Detection | Roboflow Universe | ⚠️ Cần tải + train | 🟡 Trung bình |
| Seatbelt Detection | Roboflow Universe | ⚠️ Cần tải + train | 🟡 Trung bình |
