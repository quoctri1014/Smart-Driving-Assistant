# Checklist Chuẩn bị Demo Mobile App

Để buổi thuyết trình bảo vệ đồ án diễn ra suôn sẻ, bạn bắt buộc phải thực hiện các bước sau trước giờ G ít nhất 15 phút. Vì chúng ta đang kết nối điện thoại thật với máy tính thông qua mạng nội bộ (LAN), việc thiết lập đúng địa chỉ IP là tối quan trọng!

## 1. Kết nối mạng
- [ ] Điện thoại và Máy tính (Laptop chạy Backend) **phải kết nối chung một mạng Wifi**.
- [ ] Khuyên dùng: Nếu Wifi trường học bị chặn (firewall mạnh), hãy dùng điện thoại **phát 4G (Hotspot)** và cho Laptop bắt sóng Wifi đó. Đây là cách ổn định nhất!

## 2. Tìm địa chỉ IP LAN của máy tính
1. Mở PowerShell trên máy tính, gõ: `ipconfig`
2. Tìm dòng `IPv4 Address`. Nó thường có dạng `192.168.x.x` hoặc `10.x.x.x`.
3. Ghi nhớ con số này (Ví dụ: `192.168.43.51`).

## 3. Cập nhật IP vào Mobile App
1. Mở file `smart-driving-assistant/mobile-app/.env` (nếu chưa có thì copy từ `.env.example`).
2. Sửa lại các đường dẫn, thay `192.168.1.100` bằng IP bạn vừa tìm được:
   ```env
   EXPO_PUBLIC_API_URL=http://192.168.43.51:8000/api/v1
   EXPO_PUBLIC_WS_URL=ws://192.168.43.51:8000/ws/v1
   ```
3. **Lưu file lại.**

## 4. Khởi động hệ thống
- [ ] Bật Backend: `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000` (Chú ý bắt buộc phải thêm `--host 0.0.0.0` để cho phép các thiết bị ngoài truy cập vào máy tính).
- [ ] Bật Mobile App: Mở terminal mới, `cd mobile-app` -> `npx expo start -c` (Thêm `-c` để xoá cache cũ, nhận IP mới).

## 5. Xử lý sự cố Tường lửa (Firewall)
Nếu bạn quét mã QR trên điện thoại, app chạy lên được nhưng báo **"Offline"** hoặc không đăng nhập được:
- Máy tính Windows của bạn đang chặn kết nối đến cổng 8000!
- Cách sửa nhanh: Vào Windows Security -> Firewall & network protection -> Allow an app through firewall -> Cho phép `python.exe` đi qua mạng Private và Public.
- Hoặc đơn giản nhất (chỉ dùng lúc demo): Tạm thời **Tắt Windows Firewall** (Turn off Windows Defender Firewall) trong 30 phút bảo vệ.

## 6. Test thực tế
- [ ] Mở ứng dụng Expo Go trên điện thoại, quét mã QR trên màn hình laptop.
- [ ] Đăng nhập bằng `demo@example.com` / `password123`.
- [ ] Cấp quyền Camera.
- [ ] Để điện thoại lên giá đỡ, nhắm mắt lại 1 giây, điện thoại phải Rung lên (Haptics) và hiện chữ "TÀI XẾ BUỒN NGỦ!".
