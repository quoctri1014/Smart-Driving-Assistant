# 📚 TỔNG HỢP LÝ THUYẾT CỐT LÕI & CẨM NANG BẢO VỆ ĐỒ ÁN
### HỆ THỐNG HỖ TRỢ LÁI XE THÔNG MINH — SMART DRIVING ASSISTANT (ADAS & DMS)

> 📌 **File Word (.docx) được tạo tại:** [`LY_THUYET_COT_LOI_TRA_LOI_PHAN_BIEN.docx`](../LY_THUYET_COT_LOI_TRA_LOI_PHAN_BIEN.docx)

---

## 1. NHẬN DIỆN VẬT THỂ — KIẾN TRÚC VÀ TỐI ƯU HÓA YOLOV8
### ❓ Câu hỏi hội đồng hay chất vấn:
> *"Tại sao nhóm chọn YOLOv8 mà không dùng Faster R-CNN hay SSD? Kiến trúc và các hàm mất mát (Loss Function) hoạt động như thế nào?"*

### 💡 Trả lời:
1. **Lý do chọn YOLOv8 (Anchor-free One-stage Detector):**
   - **Tốc độ thời gian thực:** Đạt 30-45 FPS trên GPU thông thường và 20-30 FPS trên CPU/Edge, trong khi Faster R-CNN (Two-stage) chỉ đạt 8-15 FPS, không thể đáp ứng yêu cầu khắt khe của hệ thống cảnh báo va chạm ADAS.
   - **Cơ chế Anchor-free:** Loại bỏ việc cấu hình cố định kích thước Anchor boxes (vốn rất khó tối ưu trong giao thông Việt Nam nơi xe máy, xe đạp và ô tô có tỉ lệ khung hình chênh lệch cực lớn). YOLOv8 dự đoán trực tiếp khoảng cách từ tâm đến 4 cạnh của vật thể, giúp phát hiện vật thể đa kích thước vượt trội.
2. **Kiến trúc 3 tầng:**
   - **Backbone (CSPDarknet + C2f):** Module C2f chia tách dòng dữ liệu thành các nhánh gradient song song, tăng cường khả năng học đặc trưng phong phú mà giảm được 20% chi phí tính toán.
   - **Neck (PANet):** Kết hợp luồng đặc trưng từ trên xuống (Top-down) và từ dưới lên (Bottom-up), giúp bảo toàn độ chi tiết cho các vật thể nhỏ (biển số xe, nón bảo hiểm, đầu người).
   - **Decoupled Head:** Tách riêng nhánh phân loại (Classification) và nhánh định vị hộp bao (Bounding Box Regression), giải quyết triệt để sự xung đột nhiệm vụ.
3. **Các hàm mất mát kết hợp:**
   $$\mathcal{L}_{total} = \lambda_{cls} \mathcal{L}_{VFL} + \lambda_{box} \mathcal{L}_{CIoU} + \lambda_{dfl} \mathcal{L}_{DFL}$$
   - **Varifocal Loss (VFL):** Xử lý triệt để hiện tượng mất cân bằng mẫu âm/dương trong giao thông.
   - **Complete IoU Loss (CIoU):** Đo lường diện tích trùng lặp, khoảng cách giữa 2 tâm box, và sự sai lệch về tỉ lệ khung hình.
   - **Distribution Focal Loss (DFL):** Dự đoán vị trí biên vật thể dưới dạng một phân phối xác suất liên tục, giúp biên hộp bám sát viền xe ngay cả khi rung lắc.

---

## 2. THEO VẾT ĐA ĐỐI TƯỢNG (MOT) — BYTETRACK & BỘ LỌC KALMAN
### ❓ Câu hỏi hội đồng hay chất vấn:
> *"Làm sao hệ thống phân biệt được từng xe khi chúng đi sát nhau hoặc bị che khuất (Occlusion)?"*

### 💡 Trả lời:
1. **Bộ lọc Kalman 2D (State Estimation):**
   Mỗi đối tượng được biểu diễn bằng vector trạng thái 7 chiều:
   $$\mathbf{x} = [u, v, s, r, \dot{u}, \dot{v}, \dot{s}]^T$$
   (Tọa độ tâm $u, v$, diện tích $s$, tỉ lệ khung hình $r$ và các vận tốc biến thiên theo thời gian). Khi xe di chuyển, Kalman Filter dự đoán vị trí ở khung hình tiếp theo.
2. **Thuật toán Hungarian (Bipartite Matching):**
   Tính toán ma trận khoảng cách IoU giữa các bounding box phát hiện mới và các vị trí dự đoán từ Kalman Filter, sau đó giải bài toán ghép cặp tối ưu cực tiểu hóa chi phí.
3. **Cơ chế ByteTrack đột phá chống mất dấu:**
   - Các thuật toán cũ (SORT, DeepSORT) thường bỏ qua tất cả các box có điểm số thấp ($< 0.5$).
   - ByteTrack chia thành 2 vòng ghép: Vòng 1 ghép các box điểm cao ($> 0.6$). Vòng 2 tiếp tục ghép các box điểm thấp ($0.1 - 0.5$) với các track chưa được gán. Nhờ vậy, khi xe máy bị xe buýt che khuất 1 nửa hoặc đi vào bóng râm, hệ thống vẫn duy trì đúng Track ID, không bị đứt đoạn hay nhảy ID.

---

## 3. GIÁM SÁT TÀI XẾ BUỒNG LÁI (DMS) — BUỒN NGỦ, NGÁP VÀ MẤT TẬP TRUNG
### ❓ Câu hỏi hội đồng hay chất vấn:
> *"Nguyên lý tính chỉ số buồn ngủ và ngáp là gì? Khi tài xế đeo kính hoặc khẩu trang thì xử lý như thế nào?"*

### 💡 Trả lời:
1. **Chỉ số mở mắt EAR (Eye Aspect Ratio — Soukupová & Čech 2016):**
   $$EAR = \frac{||p_2 - p_6|| + ||p_3 - p_5||}{2 \cdot ||p_1 - p_4||}$$
   - Mắt mở bình thường: $EAR \approx 0.28 – 0.35$.
   - Mắt nhắm ngủ gật: $EAR < 0.20$ (ngưỡng hệ thống cài đặt: 0.18 - 0.20).
   - Chống báo nháy mắt sinh lý: Chỉ kích hoạt cảnh báo khi $EAR < 0.20$ kéo dài liên tục qua ít nhất 15-20 frames (~1.5 đến 2 giây).
2. **Chỉ số ngáp miệng MAR (Mouth Aspect Ratio):**
   $$MAR = \frac{||p_{top} - p_{bottom}||}{||p_{left} - p_{right}||}$$
   - Ngáp do kiệt sức: $MAR > 0.60$ kéo dài liên tục trên 1.5 - 2.0 giây.
3. **Tiêu chuẩn PERCLOS (NHTSA / ISO 15007):**
   Đo tỷ lệ phần trăm thời gian mắt nhắm từ 80% trở lên trong cửa sổ trượt 60 giây. Nếu $PERCLOS > 0.15$ (tài xế nhắm mắt quá 15% thời gian trong 1 phút), hệ thống lập tức phát cảnh báo khẩn cấp CRITICAL bằng giọng nói.
4. **Ước lượng tư thế đầu 3D (Head Pose via `cv2.solvePnP`):**
   Giải hệ phương trình tìm ma trận quay Euler (Pitch, Yaw, Roll):
   - **Góc Pitch $<-25^\circ$:** Tài xế gục đầu ngủ gật xuống vô lăng.
   - **Góc Yaw $> 30^\circ$ hoặc $<-30^\circ$:** Tài xế quay mặt sang hai bên nghe điện thoại / mất tập trung quan sát.
5. **Xử lý ngoại lệ thực tế:**
   - **Kính râm:** Chuyển sang Sunglasses Mode (dựa chủ yếu vào góc cúi đầu Pitch của Head Pose).
   - **Loại trừ người ngồi ghế phụ:** Chỉ chọn khuôn mặt nằm trong Vùng không gian ghế lái (Driver RoI Box).

---

## 4. ƯỚC LƯỢNG KHOẢNG CÁCH (1 CAMERA) & CẢNH BÁO VA CHẠM (FCW & TTC)
### ❓ Câu hỏi hội đồng hay chất vấn:
> *"Chỉ dùng 1 Camera đơn, không có Lidar hay Radar, làm sao đo được khoảng cách (mét) và cảnh báo va chạm?"*

### 💡 Trả lời:
1. **Mô hình Quang học Camera lỗ kim (Pinhole Optics Geometry):**
   $$D = \frac{W_{real} \cdot f}{W_{bbox}}$$
   - $f$: Tiêu cự camera tính theo pixel (được hiệu chuẩn trước).
   - $W_{bbox}$: Chiều rộng hộp bao của xe đo được trên ảnh (pixels).
   - $W_{real}$: Chiều rộng vật lý trung bình theo quy chuẩn đăng kiểm (Ô tô con: 1.8m, Xe buýt: 2.55m, Xe tải: 2.5m, Xe máy: 0.8m).
2. **Thời gian sắp va chạm TTC (Time-To-Collision):**
   $$TTC = \frac{D}{|v_{rel}|} = \frac{D}{|\frac{dD}{dt}|}$$
   - Vận tốc tương đối $v_{rel}$ được làm mượt qua Bộ lọc Kalman 2D để tránh sai số tức thời do mặt đường rung lắc.
   - **Phân cấp an toàn:** $TTC \le 2.5\text{s}$ (Warning - Vàng), $TTC \le 1.5\text{s}$ (Critical - Đỏ, yêu cầu phanh gấp).
3. **Lọc theo làn xe chủ (Ego-Lane Corridor):**
   Tạo đa giác hình thang chiếu của làn xe hiện tại. Chỉ những xe có tâm đáy nằm trong hành lang này mới kích hoạt cảnh báo, loại bỏ triệt để việc báo nhầm xe làn bên cạnh.

---

## 5. NHẬN DIỆN BIỂN SỐ XE (ALPR) & MŨ BẢO HIỂM THEO ĐẶC THÙ VIỆT NAM
### ❓ Câu hỏi hội đồng hay chất vấn:
> *"Tại sao EasyOCR hay đọc nhầm ký tự và hệ thống giải quyết bài toán biển số cong, biển số mờ nhòe như thế nào?"*

### 💡 Trả lời:
1. **Pipeline 3 cấp nhận diện biển số xe:**
   - **Bước 1 - Định vị:** YOLOv8 crop chính xác vùng biển số xe.
   - **Bước 2 - Tiền xử lý hình ảnh:** Sử dụng thuật toán **CLAHE** (cân bằng sáng cục bộ thích ứng) để làm nổi bật nét chữ biển số trong điều kiện ngược sáng hoặc trời tối, kết hợp thuật toán xoay chỉnh góc xiên (**Deskewing**).
   - **Bước 3 - OCR & Khử nhầm lẫn ký tự theo quy tắc Cảnh sát Giao thông:**
     - Ký tự 1-2 bắt buộc là số tỉnh thành (tự động sửa O, D thành 0; I, L thành 1; B thành 8).
     - Ký tự 3 bắt buộc là chữ cái seri (tự động sửa 4 thành A; 8 thành B; 0 thành D).
     - Bộ lọc loại bỏ số điện thoại taxi hoặc chữ quảng cáo giả biển số (`is_phone_or_garbage`).
2. **Cơ chế Bỏ phiếu đa khung hình (Temporal Multi-frame Voting):**
   Lưu bộ đệm 5 khung hình liên tiếp của cùng 1 xe (Track ID) và chọn kết quả OCR có độ tin cậy cộng dồn cao nhất, triệt tiêu sai số do rung lắc.
3. **Phát hiện Mũ bảo hiểm & Phân tích bề mặt vật liệu:**
   - Tách 40% phần trên của bounding box người lái xe máy.
   - Phân tích độ phản xạ gương (**Specular Highlights** với điểm sáng $gray > 220$ của vỏ nhựa ABS mũ bảo hiểm cứng).
   - Phân tích độ nhám vi phân (**Laplacian Gradient**) để phân biệt nếp gấp vải mềm của áo mưa trùm đầu / nón lá / nón vải với mũ bảo hiểm chuẩn.

---

## 6. CƠ SỞ PHÁP LÝ & QUY CHUẨN KỸ THUẬT VIỆT NAM
### ❓ Câu hỏi hội đồng hay chất vấn:
> *"Hệ thống có tuân thủ quy chuẩn và luật giao thông thực tế tại Việt Nam không?"*

### 💡 Trả lời:
1. **Nghị định 123/2021/NĐ-CP (Sửa đổi, bổ sung NĐ 100/2019/NĐ-CP):**
   - Điểm b Khoản 4 Điều 2 NĐ 123 quy định mức phạt tiền từ **400.000đ đến 600.000đ** đối với hành vi người điều khiển xe mô tô, xe gắn máy không đội mũ bảo hiểm hoặc đội mũ bảo hiểm không cài quai đúng quy cách.
   - Tích hợp phân cấp mức phạt vi phạm chạy quá tốc độ (vượt 5-10 km/h, vượt 10-20 km/h, vượt >20 km/h).
2. **Quy chuẩn QCVN 41:2019/BGTVT:**
   Phân loại đầy đủ 154 biển báo giao thông Việt Nam theo đúng 4 nhóm chuẩn: Nhóm P (Biển cấm), Nhóm W (Cảnh báo nguy hiểm), Nhóm R (Biển hiệu lệnh) và Nhóm I (Biển chỉ dẫn).
3. **Thông tư 31/2019/TT-BGTVT:**
   Quy định khoảng cách an toàn tối thiểu theo tốc độ lưu thông ($v \le 60\text{ km/h}: 35\text{m}$; $60 < v \le 80\text{ km/h}: 55\text{m}$; $80 < v \le 100\text{ km/h}: 70\text{m}$; $v > 100\text{ km/h}: 100\text{m}$).
4. **Nghị định 10/2020/NĐ-CP:**
   Quy định thời gian lái xe liên tục của tài xế xe kinh doanh vận tải không được vượt quá **4 giờ liên tục** và không quá 10 giờ trong một ngày. Hệ thống tự động đếm giờ và cảnh báo nghỉ ngơi trước 15 phút.

---

## 7. BẢNG TRA CỨU TỪ KHÓA VÀNG (CHEAT-SHEET ĐẠT ĐIỂM TỐI ĐA)

| Chủ đề | Từ khóa thuật toán & Công nghệ | Điểm nhấn giá trị kỹ thuật |
|---|---|---|
| **Nhận diện (Detection)** | YOLOv8, C2f Module, Decoupled Head, Anchor-free | Real-time >30 FPS, nhận diện tốt vật thể nhỏ tại Việt Nam |
| **Bám đuôi (Tracking)** | Kalman Filter 2D, Hungarian Algorithm, ByteTrack | Không bị mất dấu hay nhảy ID khi xe máy bị che khuất |
| **Buồn ngủ (DMS)** | MediaPipe Face Mesh, EAR, MAR, PERCLOS (ISO 15007) | Cửa sổ trượt 60 giây, loại trừ nháy mắt sinh lý |
| **Tư thế đầu (Pose)** | Head Pose, cv2.solvePnP, Euler angles (Pitch/Yaw/Roll) | Phát hiện gục đầu ngủ gật (< -25°) và mất tập trung quay ngang |
| **Cự ly & Va chạm** | Pinhole Optics, TTC, Bộ lọc Kalman 2D, Ego-Lane Corridor | Cảnh báo trước 2.5s, không báo nhầm làn bên cạnh |
| **Biển số xe (ALPR)** | CLAHE, Deskewing, EasyOCR, Multi-frame Voting | Tự động sửa nhầm lẫn ký tự theo cấu trúc 63 tỉnh thành |
| **Pháp luật Việt Nam** | NĐ 100/2019, NĐ 123/2021, QCVN 41:2019, TT 31/2019 | Tự động tra cứu mức phạt tiền và xuất phiếu biên bản vi phạm |
