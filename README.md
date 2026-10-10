# Smart Driving Assistant System

Hệ thống ADAS (Advanced Driver Assistance System) thời gian thực, gồm AI nhận diện biển báo, cảnh báo va chạm, giám sát tài xế và trợ lý lái xe thông minh.

## Architecture

```
backend/            FastAPI + WebSocket AI pipeline (uvicorn)
web-app/            Next.js dashboard + Simulator + Live Monitor
mobile-app/         React Native (Expo) mobile driving mode
ai_engine/          YOLOv8 + EasyOCR + MediaPipe AI modules
docs/               API specification and demo checklist
docker-compose.yml  PostgreSQL database setup
```

---

## WebSocket Endpoints

| Mục đích | Địa chỉ kết nối |
|---|---|
| Road AI (phát hiện xe, tốc độ, va chạm) | `ws://localhost:8000/ws/v1/stream` |
| Driver Monitor (buồn ngủ, dây an toàn) | `ws://localhost:8000/ws/v1/driver-stream` |

---

## REST Endpoints (cần PostgreSQL)

| Method | Path | Mô tả |
|---|---|---|
| GET | `/health` | Kiểm tra server (không cần DB) |
| POST | `/api/v1/auth/register` | Đăng ký tài khoản |
| POST | `/api/v1/auth/login` | Đăng nhập → nhận JWT token |
| GET | `/api/v1/violations` | Danh sách vi phạm (cần token) |
| GET | `/api/v1/sessions` | Danh sách phiên lái (cần token) |

---

# HƯỚNG DẪN CHẠY DỰ ÁN

## ✅ Yêu cầu cài đặt trước

| Phần mềm | Phiên bản | Kiểm tra |
|---|---|---|
| **Python** | >= 3.10 | `python --version` |
| **Node.js** | >= 18 | `node --version` |
| **npm** | >= 9 | `npm --version` |
| **Docker Desktop** | Mới nhất | Chỉ cần nếu dùng PostgreSQL |

---

## BƯỚC 0 — Chuẩn bị (Chỉ làm 1 lần đầu tiên)

### 0.1. Tạo file cấu hình môi trường

```powershell
copy .env.example .env
```

> Nội dung mặc định của `.env` đã khớp với `docker-compose.yml`, không cần sửa gì thêm.
> Nếu chỉ muốn chạy demo WebSocket (không cần đăng nhập/lưu dữ liệu), **bỏ qua bước này**.

### 0.2. Khởi động PostgreSQL (nếu cần đăng nhập / lưu lịch sử)

```powershell
# Yêu cầu Docker Desktop đang chạy
docker compose up -d postgres
```

> Kết nối thành công khi `localhost:5432` phản hồi với user `smartuser`, pass `smartpassword`, db `traffic_db`.

### 0.3. Cài thư viện Web App (chỉ làm 1 lần nếu chưa có `node_modules`)

```powershell
cd web-app
npm install
cd ..
```

---

## 🚀 CÁCH 1 — CHẠY TỰ ĐỘNG (Khuyên dùng, chỉ 1 click)

> Dành cho người muốn khởi động hệ thống nhanh nhất mà không cần mở nhiều Terminal thủ công.

**Nhấp đúp chuột vào file trong thư mục dự án:**

```
📁 Smart Driving Assistant\
└── 🖱️ start_project.bat   ← Nhấp đúp vào đây
```

File này **tự động mở 2 cửa sổ Terminal** riêng biệt:

| Cửa sổ | Vai trò | Địa chỉ |
|---|---|---|
| Terminal 1 (nền xanh) | Backend FastAPI + AI Engine | http://localhost:8000 |
| Terminal 2 | Web Dashboard Next.js | http://localhost:3000 |

**Sau khi cả 2 terminal báo chạy xong**, mở trình duyệt:

```
🌐 http://localhost:3000
```

> ⚠️ Chờ Terminal 1 hiển thị `Application startup complete` trước khi dùng Web App.

---

## 🛠️ CÁCH 2 — CHẠY THỦ CÔNG TỪNG BƯỚC (Qua Terminal)

> Dành cho người muốn kiểm soát từng bước hoặc debug lỗi.

### TERMINAL 1 — Khởi động Backend (FastAPI + AI Engine)

Mở **PowerShell** tại thư mục gốc dự án, chạy:

```powershell
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Đợi đến khi thấy:**

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

> ⏳ Lần đầu mất khoảng **30–60 giây** để load các mô hình AI (YOLOv8, MediaPipe, EasyOCR).
> ℹ️ Thông báo `[HelmetChecker] model not found` là **bình thường**, không ảnh hưởng tới demo.

**Kiểm tra nhanh:**

```powershell
curl http://localhost:8000/health
# Kết quả mong muốn: {"status":"ok"}
```

Xem tài liệu API tự động (Swagger UI): **http://localhost:8000/docs**

---

### TERMINAL 2 — Khởi động Web Dashboard (Next.js)

Mở một cửa sổ **PowerShell mới**, chạy:

```powershell
cd web-app
npm run dev
```

**Đợi đến khi thấy:**

```
✓ Ready - started server on http://localhost:3000
```

Mở trình duyệt và vào: **http://localhost:3000**

---

### TERMINAL 3 — Khởi động Mobile App Expo (Tùy chọn, không bắt buộc)

Mở thêm một cửa sổ **PowerShell mới**, chạy:

```powershell
cd mobile-app
npx expo start
```

- **Điện thoại thật:** Quét mã QR bằng app **Expo Go** (Android/iOS).
- **Máy ảo Android:** Nhấn phím `a` trong Terminal sau khi Expo khởi động.

> ⚠️ Khi dùng điện thoại thật trên cùng mạng Wi-Fi, sửa `mobile-app/.env.local`:
>
> ```env
> EXPO_PUBLIC_API_URL=http://192.168.x.x:8000/api/v1
> EXPO_PUBLIC_WS_URL=ws://192.168.x.x:8000
> ```
>
> Thay `192.168.x.x` bằng **địa chỉ IP LAN của máy tính** (xem bằng lệnh `ipconfig`).

---

## 📋 Bảng địa chỉ truy cập hệ thống

| Chức năng | Địa chỉ |
|---|---|
| 🌐 Web Dashboard (Trang chủ) | http://localhost:3000 |
| 🤖 Trợ lý Lái xe Live (AI Camera) | http://localhost:3000/live |
| 📊 Bảng điều khiển cá nhân | http://localhost:3000/dashboard |
| 🗺️ Nhật ký hành trình | http://localhost:3000/journeys |
| ⚠️ Cảnh báo an toàn & Vi phạm | http://localhost:3000/violations |
| 🔧 Trạng thái 12 Module AI | http://localhost:3000/ai-status |
| 📡 Swagger API Docs (tài liệu API) | http://localhost:8000/docs |
| ❤️ Health Check (kiểm tra backend) | http://localhost:8000/health |

---

## Đối chiếu chức năng & Tài liệu hệ thống

- **Đối chiếu 12 tính năng**: [feature-alignment-review.md](docs/feature-alignment-review.md)
- **Hướng dẫn chạy dự án chi tiết**: [HUONG_DAN_CHAY_DU_AN.md](docs/HUONG_DAN_CHAY_DU_AN.md)
- **Quyền và chức năng hệ thống**: [DOCS_QUYEN_VA_CHUC_NANG_HE_THONG.md](docs/DOCS_QUYEN_VA_CHUC_NANG_HE_THONG.md)
- **Kiến trúc hệ thống**: [architecture.md](docs/architecture.md)
