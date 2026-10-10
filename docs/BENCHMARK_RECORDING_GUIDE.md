# HƯỚNG DẪN QUAY VIDEO DỮ LIỆU THỰC TẾ CHO BENCHMARK ADAS & DMS
**Dự án:** Hệ thống Trợ lý Lái xe An toàn Thông minh (Smart Driving Assistant)  
**Tài liệu:** Kịch bản thu thập dữ liệu tự quay bổ sung (DMS, Dây an toàn, Mũ bảo hiểm góc gần)  
**Ngày lập:** 28/09/2026  

---

## 1. TỔNG QUAN PHẦN CÒN THIẾU
Hệ thống đã thu thập và chuẩn hóa thành công **17 video dashcam thật ngoài đường** cho các bài toán nhận dạng ngoại cảnh (xe máy đông đúc, ban ngày, ban đêm, trời mưa, ngược sáng, biển báo QCVN 41:2019).  

Để đưa toàn bộ 12 module AI lên mức thương mại hoàn chỉnh, hiện còn thiếu **3 nhóm dữ liệu buồng lái và góc gần** bắt buộc phải tự quay trên xe thật:
1. **DMS (Driver Monitoring System - Module M11):** Theo dõi trạng thái tài xế (buồn ngủ, ngáp, mất tập trung, kính râm).
2. **Dây an toàn (Seatbelt):** Kiểm tra cài chốt và vắt dây qua vai tài xế.
3. **Mũ bảo hiểm góc gần (Helmet - Module M6):** Cận cảnh phân biệt mũ thật, mũ lưỡi trai, trùm áo mưa cánh dơi.

---

## 2. KỊCH BẢN QUAY CHI TIẾT

### PHẦN A: DMS - GIÁM SÁT TÀI XẾ (CABIN)
- **Thiết bị:** Điện thoại (iPhone / Android) hoặc Action Cam (GoPro) có độ phân giải tối thiểu $1080\text{p} @ 30\text{ fps}$.
- **Vị trí gắn camera:** Gắn giá hút chân không tại **cột chữ A (A-pillar) bên trái tài xế** hoặc trên **táp-lô chính diện vô lăng**, chếch góc $15^\circ - 20^\circ$ nhìn rõ khuôn mặt và mắt tài xế. Khoảng cách từ thấu kính đến mặt: $60 - 90\text{ cm}$.

| Mã kịch bản | Tên kịch bản | Thời lượng | Điều kiện ánh sáng | Hành vi tài xế cần diễn | Tiêu chí đánh giá AI |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **DMS-01** | Lái xe bình thường | 60 giây | Ban ngày, nắng nhẹ | Nhìn thẳng đường, thỉnh thoảng liếc gương chiếu hậu, chớp mắt tự nhiên ($0.2 - 0.4\text{s}$). | Baseline chuẩn: Không báo động, PERCLOS $< 0.15$. |
| **DMS-02** | Buồn ngủ nhắm mắt lâu | 90 giây | Ban ngày | Nhắm mắt từ từ, giữ nhắm mắt liên tục $2.5 - 4.0$ giây rồi giật mình mở to mắt (lặp lại 3 - 4 lần trong clip). | M11 phải kích hoạt cảnh báo `DROWSINESS_ALERT` cấp độ Warning/Critical khi nhắm mắt $> 2.0\text{s}$. |
| **DMS-03** | Ngáp sâu liên tục | 60 giây | Ban ngày | Há to miệng ngáp sâu kéo dài $3 - 5$ giây, mắt nheo lại (lặp lại 3 lần). | Kích hoạt cảnh báo ngáp buồn ngủ (`YAWN_DETECTED`). |
| **DMS-04** | Cúi đầu dùng điện thoại | 60 giây | Ban ngày | Cúi gập đầu xuống đùi ($Pitch < -20^\circ$) liên tục trong $3 - 5$ giây để xem điện thoại, sau đó ngẩng lên. | Kích hoạt cảnh báo mất tập trung (`DISTRACTION_HEAD_DOWN`). |
| **DMS-05** | Quay mặt sang bên | 60 giây | Ban ngày | Quay hẳn mặt sang ghế phụ hoặc nhìn sang cửa sổ ($Yaw > 30^\circ$) trong $4 - 6$ giây. | Kích hoạt cảnh báo mất tập trung (`DISTRACTION_LOOKING_AWAY`). |
| **DMS-06** | Đeo kính râm thời trang | 90 giây | Nắng gắt | Đeo kính mát đen che kín mắt; thực hiện cúi đầu, quay đầu và ngáp. | Kiểm thử chế độ `sunglasses_mode`: chuyển sang ước lượng góc nghiêng đầu 3D (`solvePnP`). |
| **DMS-07** | Cabin ban đêm | 90 giây | Ban đêm trong phố | Bật đèn táp-lô xe, lái xe ban đêm, ánh sáng đèn đường lướt qua mặt. | Kiểm thử độ nhạy cảm biến ánh sáng yếu, đo nhiễu ISO camera. |
| **DMS-08** | Che khuất một phần | 60 giây | Ban ngày | Đưa tay lên gãi cằm, chỉnh kính, uống nước bằng chai che khuất miệng. | Không được báo động nhầm là ngáp hoặc buồn ngủ. |

---

### PHẦN B: DÂY AN TOÀN (SEATBELT)
- **Vị trí gắn camera:** Gắn trên kính lái góc trung tâm nhìn xuống vùng ngực và vai trái của tài xế.

| Mã kịch bản | Tên kịch bản | Thời lượng | Trang phục diễn | Hành vi | Tiêu chí đánh giá AI |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **SB-01** | Cài dây đúng chuẩn | 45 giây | Áo sáng màu (trắng/xanh nhạt) | Thắt dây an toàn chuẩn, dây vắt chéo qua xương đòn xuống ngực. | Nhận diện có thắt dây (`SEATBELT_ON`, conf $> 0.85$). |
| **SB-02** | Áo cùng màu dây (Ca khó) | 45 giây | Áo thun đen hoặc áo khoác tối màu | Thắt dây an toàn màu đen trên nền áo đen. | Kiểm thử độ tương phản viền gờ nổi của dây (`Sobel gradient`). |
| **SB-03** | Không thắt dây an toàn | 45 giây | Áo thường | Ngồi lái hoàn toàn không cài dây, buông thõng dây trên trụ B. | Kích hoạt cảnh báo `NO_SEATBELT_WARNING`. |
| **SB-04** | Cài dây sau lưng | 45 giây | Áo thường | Kéo dây an toàn cài vào chốt nhưng luồn ra sau lưng người lái. | Kiểm tra phát hiện vùng ngực không có dây vắt qua vai. |

---

### PHẦN C: MŨ BẢO HIỂM GÓC GẦN (HELMET - NGOẠI CẢNH)
- **Vị trí gắn camera:** Camera hành trình gắn kính lái trước ô tô, bắt cận cảnh người điều khiển xe máy ở cự ly $3 - 10\text{ mét}$.

| Mã kịch bản | Tên kịch bản | Số lượng mẫu | Đặc điểm đối tượng | Tiêu chí đánh giá AI |
| :--- | :--- | :---: | :--- | :--- |
| **HM-01** | Đội mũ bảo hiểm chuẩn | 20 mẫu | Mũ nửa đầu hoặc mũ 3/4 đầu có kính chắn gió, có quai cài rõ ràng. | Nhãn `HELMET_COMPLIANT`. |
| **HM-02** | Không đội mũ bảo hiểm | 15 mẫu | Đầu trần, tóc ngắn hoặc tóc dài bay trong gió. | Nhãn `NO_HELMET_VIOLATION`. |
| **HM-03** | Đội mũ lưỡi trai / Mũ vải | 15 mẫu | Đội mũ kết, mũ len hoặc mũ vành (không phải mũ bảo hiểm). | Phân biệt kết cấu nón vải vs nón nhựa cứng bảo hiểm. |
| **HM-04** | Trùm áo mưa cánh dơi | 20 mẫu | Trời mưa, tài xế trùm nón áo mưa mỏng bọc ngoài mũ bảo hiểm. | Kiểm thử hàm `analyze_head_texture_and_poncho` không bắt phạt nhầm. |
| **HM-05** | Ninja Lead trùm kín đầu | 15 mẫu | Đeo khẩu trang vải lớn, áo chống nắng trùm kín tai và cổ. | Không bắt nhầm khi góc nhìn chỉ thấy vải trùm. |

---

## 3. QUY TRÌNH BÀN GIAO & TÍCH HỢP SAU KHI QUAY
1. Lưu các file video đã quay theo đúng quy ước:  
   `dms_{kịch_bản}_{tên_tài_xế}.mp4` (vd: `dms_02_buon_ngu_tri.mp4`, `seatbelt_02_ao_den.mp4`).
2. Chép toàn bộ file vào thư mục:  
   `d:\Smart Driving Assistant\tests\benchmark\videos_user_recorded\`
3. Chạy script chuẩn hóa tự động:  
   ```powershell
   python scripts/standardize_benchmark_videos.py --user-input
   ```
4. Hệ thống sẽ tự động gán nhãn sơ bộ, đưa vào danh sách kiểm duyệt và chạy đối soát số liệu chuẩn.
