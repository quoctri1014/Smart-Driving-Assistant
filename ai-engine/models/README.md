# Hướng Dẫn Cài Đặt Custom AI Models

Thư mục `models/` chứa các file model YOLOv8 **đã fine-tune** cho các tính năng đặc thù.
Các file này **không được commit** lên Git vì dung lượng lớn.

## Danh Sách Model Cần Có

| File | Tính năng | Trạng thái |
|---|---|---|
| `helmet_yolov8.pt` | Phát hiện không đội mũ bảo hiểm | ⚠️ Chưa có |
| `sign_yolov8.pt` | Nhận diện biển báo giao thông | ⚠️ Chưa có |
| `seatbelt_yolov8.pt` | Phát hiện không thắt dây an toàn | ⚠️ Chưa có |

> Khi thiếu model, module tương ứng tự động **tắt** và pipeline vẫn chạy bình thường với các tính năng còn lại.

---

## Cách Tải / Train Helmet Model

### Cách 1: Tải model có sẵn (nhanh nhất)

Tìm và tải model YOLOv8 phát hiện mũ bảo hiểm từ Roboflow Universe:
https://universe.roboflow.com/search?q=helmet+detection+yolov8

Sau khi tải về, đặt file vào đây:
```
ai-engine/models/helmet_yolov8.pt
```

### Cách 2: Train từ đầu

```bash
# Cài Roboflow CLI để tải dataset
pip install roboflow

# Xem hướng dẫn chi tiết
# docs/dataset_catalog.md → Mục 3
```

---

## Cách Tải / Train Sign Recognition Model

```bash
# Tải GTSRB dataset từ Kaggle
# https://www.kaggle.com/datasets/meowmeowmeowmeowmeow/gtsrb-german-traffic-sign

# Train
cd ai-engine
python train.py --task sign --epochs 100 --imgsz 640

# Copy model output
# runs/detect/sign_train/weights/best.pt → models/sign_yolov8.pt
```

---

## Ghi Chú .gitignore

File `.gitignore` tại project root nên có dòng:
```
ai-engine/models/*.pt
```
để tránh commit model nặng lên repository.
