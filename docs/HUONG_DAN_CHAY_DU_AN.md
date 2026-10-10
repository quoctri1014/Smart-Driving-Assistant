# HƯỚNG DẪN KHỞI CHẠY DỰ ÁN SMART DRIVING ASSISTANT

Tài liệu hướng dẫn các câu lệnh chạy trực tiếp trên Terminal (PowerShell / Command Prompt) cho từng thành phần của hệ thống trên Windows.

---

## ⚡ CÁC CÂU LỆNH CHẠY NHANH (MỞ 3 TERMINAL RIÊNG BIỆT)

### TERMINAL 1: BACKEND API & AI ENGINE (FastAPI)
Chạy trực tiếp bằng Python trong venv (không lo lỗi thiếu thư viện hay ExecutionPolicy):

```powershell
cd "d:\Smart Driving Assistant"
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
- Địa chỉ API: http://localhost:8000
- Tài liệu Swagger: http://localhost:8000/docs
- Kiểm tra trạng thái: http://localhost:8000/health

---

### TERMINAL 2: WEB DASHBOARD (Next.js)

```powershell
cd "d:\Smart Driving Assistant\web-app"
npm run dev
```
- Mở trình duyệt: http://localhost:3000 (sẽ tự động vào thẳng trang Đăng nhập)
- Chọn nhanh vai trò trên giao diện: **Quản trị viên** (`admin@vinafleet.com`), **Điều độ viên** (`dispatcher@vinafleet.com`), hoặc **Tài xế** (`driver1@example.com`) / Mật khẩu: `password123`

---

### TERMINAL 3: MOBILE APP (Expo / React Native)

```powershell
cd "d:\Smart Driving Assistant\mobile-app"
npx expo start -c
```
- Nhấn phím `w` để mở giao diện Web trên trình duyệt máy tính.
- Hoặc dùng app **Expo Go** trên điện thoại quét mã QR (điện thoại và máy tính cùng mạng Wi-Fi).

---

### TERMINAL 4 (TÙY CHỌN): CHẠY TEST AI ENGINE ĐỘC LẬP (OpenCV)

```powershell
cd "d:\Smart Driving Assistant\ai_engine"
..\venv\Scripts\python.exe main.py --source 0
```
- Chạy với webcam: `..\venv\Scripts\python.exe main.py --source 0`
- Chạy với file video: `..\venv\Scripts\python.exe main.py --source "../demo.mp4"`
- Bấm phím `q` trên cửa sổ video để tắt.

---

## 📌 HƯỚNG DẪN CHI TIẾT TỪNG PHẦN

### 1. Chi tiết Backend API (FastAPI)
Thư mục: `d:\Smart Driving Assistant`

1. Di chuyển vào thư mục dự án:
```powershell
cd "d:\Smart Driving Assistant"
```

2. Khởi động server FastAPI:
```powershell
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

*(Lưu ý: Sử dụng đường dẫn thẳng `.\venv\Scripts\python.exe` giúp chạy đúng phiên bản Python đã cài đầy đủ thư viện của dự án).*

---

### 2. Chi tiết Web Dashboard (Next.js)
Thư mục: `d:\Smart Driving Assistant\web-app`

1. Di chuyển vào thư mục web-app:
```powershell
cd "d:\Smart Driving Assistant\web-app"
```

2. Khởi chạy máy chủ phát triển:
```powershell
npm run dev
```

3. Truy cập http://localhost:3000 trên trình duyệt.

#### Cách tải video demo trực tiếp trên Web:
1. Đăng nhập vào Web và vào mục **Giám Sát Trực Tiếp** (`/live`).
2. Chọn chế độ **"Tải file Video (.mp4)"**.
3. Bấm **"Chọn Video Đường Đi (.mp4)"** và chọn file video giao thông (`.mp4`, `.webm`, `.avi`).
4. (Tùy chọn) Bật camera cabin nếu muốn kiểm tra buồn ngủ/dây an toàn.
5. Bấm **"Bắt đầu phân tích AI"** để hệ thống tự động phân tích và phát hiện vi phạm.

---

### 3. Chi tiết Mobile App (React Native / Expo)
Thư mục: `d:\Smart Driving Assistant\mobile-app`

1. Di chuyển vào thư mục mobile-app:
```powershell
cd "d:\Smart Driving Assistant\mobile-app"
```

2. Khởi chạy Expo:
```powershell
npx expo start -c
```

3. Nhấn `w` để xem ngay trên trình duyệt web, hoặc quét mã QR bằng app Expo Go.

---

## 🛠️ XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

### 1. Lỗi cổng 8000 đang bị chiếm dụng (Port already in use)
Chạy lệnh sau trên PowerShell để giải phóng cổng 8000:
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

### 2. Lỗi cổng 3000 đang bị chiếm dụng
Chạy lệnh sau trên PowerShell:
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force
```

### 3. Điện thoại không kết nối được tới Backend API
- Xem địa chỉ IP của máy tính bằng lệnh: `ipconfig` (tìm dòng IPv4 Address, ví dụ `192.168.1.15`).
- Mở file `d:\Smart Driving Assistant\mobile-app\.env` và cập nhật:
```env
EXPO_PUBLIC_API_URL=http://192.168.1.15:8000/api/v1
```
- Cho phép cổng 8000 qua Windows Firewall:
```powershell
netsh advfirewall firewall add rule name="FastAPI 8000" dir=in action=allow protocol=TCP localport=8000
```
