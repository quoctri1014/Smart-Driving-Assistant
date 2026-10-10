# 🚗 Smart Driving Assistant — Hướng Dẫn Chạy Dự Án

> Hệ thống hỗ trợ lái xe thông minh (ADAS) thời gian thực: nhận diện biển báo, cảnh báo va chạm, giám sát tài xế buồn ngủ và trợ lý lái xe AI.

---

## ✅ Yêu cầu cài đặt trước khi chạy

| Phần mềm | Phiên bản tối thiểu | Kiểm tra bằng lệnh |
|---|---|---|
| **Python** | >= 3.10 | `python --version` |
| **Node.js** | >= 18 | `node --version` |
| **npm** | >= 9 | `npm --version` |
| **Docker Desktop** | Mới nhất | *(Chỉ cần nếu muốn lưu dữ liệu / đăng nhập)* |

---

## ⚙️ Bước 0 — Chuẩn bị lần đầu khi mới tải về (chỉ làm 1 lần)

### 0.1 — Tạo file cấu hình môi trường

```powershell
copy .env.example .env
```

> File `.env` chứa thông tin kết nối database và JWT key.  
> Nếu chỉ chạy demo AI (không cần đăng nhập hay lưu lịch sử), **bỏ qua bước 0.4**.

---

### 0.2 — Cài thư viện Python cho Backend & AI

```powershell
# Tạo môi trường ảo venv và cài đặt các thư viện cần thiết
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

---

### 0.3 — Cài thư viện cho Web Dashboard

```powershell
cd web-app
npm install
cd ..
```

---

### 0.4 — Khởi động database PostgreSQL *(không bắt buộc)*

> Cần thiết nếu muốn dùng tính năng: Đăng nhập, Lịch sử hành trình, Danh sách vi phạm.

```powershell
# Yêu cầu Docker Desktop đang chạy
docker compose up -d postgres
```

---

## 🚀 Cách 1 — Chạy tự động (1 click, khuyên dùng)

> Phù hợp cho người muốn khởi động nhanh, không cần mở Terminal thủ công.

**👇 Nhấp đúp chuột vào file này trong thư mục dự án:**

```
📁 Smart Driving Assistant\
└── 🖱️ start_project.bat    ← Nhấp đúp vào đây
```

Hệ thống sẽ **tự động mở 2 cửa sổ Terminal**:

| Cửa sổ | Nội dung | Truy cập tại |
|---|---|---|
| Terminal 1 *(nền xanh)* | Backend FastAPI + AI Engine | http://localhost:8000 |
| Terminal 2 | Web Dashboard Next.js | http://localhost:3000 |

**Sau khi cả 2 terminal hiển thị "started"**, mở trình duyệt và vào:

```
🌐 http://localhost:3000
```

> ⚠️ **Lưu ý:** Chờ Terminal 1 hiển thị dòng `Application startup complete` trước khi thao tác trên web.  
> ⏳ Lần đầu chạy có thể mất **30–60 giây** để load các mô hình AI.

---

## 🛠️ Cách 2 — Chạy thủ công từng bước (qua Terminal)

> Phù hợp khi muốn kiểm soát chi tiết hoặc debug lỗi.

---

### Terminal 1 — Khởi động Backend (FastAPI + AI)

Mở **PowerShell** tại thư mục gốc dự án, chạy lệnh:

```powershell
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**✅ Thành công khi thấy:**

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

> ⏳ Lần đầu mất **30–60 giây** để load mô hình AI (YOLOv8, MediaPipe, EasyOCR).  
> ℹ️ Cảnh báo `[HelmetChecker] model not found` là **bình thường**, không ảnh hưởng demo.

**Kiểm tra nhanh backend:**

```powershell
curl http://localhost:8000/health
# Trả về: {"status":"ok"}
```

---

### Terminal 2 — Khởi động Web Dashboard (Next.js)

Mở **cửa sổ PowerShell mới**, chạy:

```powershell
cd web-app
npm run dev
```

**✅ Thành công khi thấy:**

```
✓ Ready - started server on http://localhost:3000
```

Mở trình duyệt → vào: **http://localhost:3000**

---

### Terminal 3 — Khởi động Mobile App *(tuỳ chọn)*

Mở **cửa sổ PowerShell mới**, chạy:

```powershell
cd mobile-app
npx expo start
```

- **Điện thoại thật:** Tải app **Expo Go** (Android/iOS) → quét mã QR hiện trong Terminal.
- **Máy ảo Android:** Nhấn phím `a` trong Terminal.

> ⚠️ Khi dùng điện thoại thật qua Wi-Fi, mở file `mobile-app/.env.local` và thay `localhost` bằng **IP LAN của máy tính** (xem bằng lệnh `ipconfig`):
>
> ```env
> EXPO_PUBLIC_API_URL=http://192.168.x.x:8000/api/v1
> EXPO_PUBLIC_WS_URL=ws://192.168.x.x:8000
> ```

---

## 📋 Các địa chỉ truy cập sau khi chạy

| Tính năng | Đường dẫn |
|---|---|
| 🏠 Trang chủ Web | http://localhost:3000 |
| 🤖 Trợ lý Lái xe (AI Camera Live) | http://localhost:3000/live |
| 📊 Bảng điều khiển cá nhân | http://localhost:3000/dashboard |
| 🗺️ Nhật ký hành trình | http://localhost:3000/journeys |
| ⚠️ Cảnh báo & Vi phạm | http://localhost:3000/violations |
| 🔧 Trạng thái 12 Module AI | http://localhost:3000/ai-status |
| 📡 Tài liệu API (Swagger UI) | http://localhost:8000/docs |
| ❤️ Kiểm tra server (Health Check) | http://localhost:8000/health |

---

## 📁 Cấu trúc thư mục dự án

```
Smart Driving Assistant/
├── backend/            FastAPI + WebSocket + AI pipeline
├── web-app/            Next.js dashboard (Web)
├── mobile-app/         React Native / Expo (Điện thoại)
├── ai_engine/          YOLOv8, EasyOCR, MediaPipe models
├── docs/               Tài liệu hệ thống
├── docker-compose.yml  Cài đặt PostgreSQL bằng Docker
├── start_project.bat   ← Khởi động tự động (1 click)
└── .env.example        Mẫu cấu hình môi trường
```

---

## 📚 Tài liệu thêm

- [Đối chiếu 12 tính năng AI](docs/feature-alignment-review.md)
- [Kiến trúc hệ thống](docs/architecture.md)
- [Đặc tả API](docs/api-spec.md)
