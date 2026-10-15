# 🚗 KỊCH BẢN THUYẾT TRÌNH & DEMO DỰ ÁN (5 PHÚT)
### HỆ THỐNG HỖ TRỢ LÁI XE THÔNG MINH — SMART DRIVING ASSISTANT (ADAS & DMS)

> 📌 **File Word (.docx) đã được tạo sẵn tại:** [`KICH_BAN_DEMO_5_PHUT_SMART_DRIVING_ASSISTANT.docx`](../KICH_BAN_DEMO_5_PHUT_SMART_DRIVING_ASSISTANT.docx)

---

## 1. ✅ CHECKLIST CHUẨN BỊ TRƯỚC KHI BẮT ĐẦU (30 GIÂY)
1. **Khởi động hệ thống:** Nhấp đúp file [`start_project.bat`](../start_project.bat) (Backend port `8000` + Frontend port `3000`). Chờ dòng `Application startup complete`.
2. **Mở sẵn trang Live:** Mở trình duyệt vào [`http://localhost:3000/live`](http://localhost:3000/live), nhấn **F11** để vào chế độ toàn màn hình chuyên nghiệp.
3. **Bật loa ngoài:** Kiểm tra âm lượng máy tính để hội đồng/người xem nghe rõ giọng đọc cảnh báo tiếng Việt của trợ lý AI.
4. **Chuẩn bị 2 file video mẫu:**
   - `bien_bao_hanoi_01.mp4`: Nhận diện biển báo, cự ly an toàn, vạch đường.
   - `dong_xe_may_hanoi_01.mp4`: Nhận diện xe máy, phát hiện không đội mũ bảo hiểm và quét biển số xe.

---

## 2. ⏱️ PHÂN BỔ THỜI GIAN THEO TỪNG GIAI ĐOẠN (TIMELINE)

| Thời gian | Nội dung trọng tâm | Mục tiêu đạt được |
|---|---|---|
| **0:00 – 0:45** *(45 giây)* | **Phần 1:** Giới thiệu & Bức tranh tổng quan | Nêu bật tính mới: Tích hợp cùng lúc 2 luồng Camera (Road ADAS + Cabin DMS) |
| **0:45 – 2:00** *(75 giây)* | **Phần 2:** Camera đường — Biển báo & Cự ly an toàn | Biển báo QCVN 41 kèm tra cứu mức phạt NĐ 100/123 + Radar 3D chống va chạm |
| **2:00 – 3:15** *(75 giây)* | **Phần 3:** Đột phá vi phạm — Không đội mũ bảo hiểm | Phát hiện người đi xe máy không mũ, đối soát biển số xe, mở modal in biên bản phạt |
| **3:15 – 4:15** *(60 giây)* | **Phần 4:** Camera Cabin — Giám sát tài xế DMS | Phát hiện buồn ngủ nhắm mắt (EAR) & ngáp (MAR), phát âm thanh cảnh báo tiếng Việt |
| **4:15 – 5:00** *(45 giây)* | **Phần 5:** Quản lý biên bản & Kết luận | Trang quản lý vi phạm tập trung, tổng kết giá trị ứng dụng thực tiễn |

---

## 3. 🎙️ CHI TIẾT THAO TÁC & LỜI THOẠI TỪNG PHÚT

### 🔹 PHẦN 1: MỞ ĐẦU & BỨC TRANH TỔNG QUAN (0:00 – 0:45)
* 🖱️ **Thao tác:** Đang đứng ở màn hình chính trang `http://localhost:3000/live`. Màn hình chia rõ 2 khu vực: Camera đường (trái) và Camera cabin (phải).
* 🎙️ **Lời thoại mẫu:**
> *"Kính chào thầy cô và các bạn! Hôm nay em xin đại diện nhóm trình bày dự án **'Smart Driving Assistant'** — Hệ thống trợ lý hỗ trợ lái xe thông minh thời gian thực kết hợp giám sát an toàn giao thông.  
> Điểm khác biệt lớn nhất của dự án là không chỉ ghi hình đơn thuần như các camera hành trình truyền thống, mà hệ thống ứng dụng mô hình Deep Learning để xử lý đồng thời 2 góc nhìn:  
> 1. **Camera phía trước (Road Camera):** Hỗ trợ lái xe ADAS, cảnh báo cự ly va chạm, nhận diện biển báo và phát hiện vi phạm giao thông theo luật Việt Nam.  
> 2. **Camera trong buồng lái (Cabin DMS):** Giám sát tài xế, phát hiện ngủ gật, mất tập trung và cảnh báo bằng giọng nói tiếng Việt tức thì."*

---

### 🔹 PHẦN 2: CAMERA ĐƯỜNG — BIỂN BÁO & CỰ LY ADAS (0:45 – 2:00)
* 🖱️ **Thao tác:** 
  1. Nhấn nút **"Tải video hành trình"** chọn file `bien_bao_hanoi_01.mp4`.
  2. Bấm vào Tab **"Biển báo giao thông"** (`signs`).
  3. Sau đó chuyển nhanh sang Tab **"Mật độ & Cự ly"** (`traffic`) để chiếu Radar cự ly 3D.
* 🎙️ **Lời thoại mẫu:**
> *"Đầu tiên là tính năng Hỗ trợ lái xe ADAS trên Camera đường:  
> - **Nhận diện Biển báo QCVN 41:** Khi xe lưu thông, hệ thống nhận diện tức thì các biển báo giao thông: biển giới hạn tốc độ, biển cấm rẽ, cấm quay đầu... Đặc biệt, hệ thống tích hợp sẵn cơ sở dữ liệu Nghị định 100/2019 và Nghị định 123/2021: Ngay dưới mỗi biển báo, tài xế sẽ thấy được mức phạt tài chính nếu vi phạm hiệu lệnh của biển đó.  
> - **Cảnh báo cự ly an toàn & Ngăn ngừa va chạm:** Chuyển sang tab Cự ly, hệ thống sử dụng thuật toán tính toán khoảng cách 3D với phương tiện phía trước. Dựa trên vận tốc hiện tại và Thông tư 31 của Bộ Giao thông Vận tải, hệ thống tự động đưa ra cảnh báo: 'Bám quá gần, hãy giữ khoảng cách an toàn!' để tài xế kịp thời phanh giảm tốc."*

---

### 🔹 PHẦN 3: ĐỘT PHÁ VI PHẠM — KHÔNG ĐỘI MŨ BẢO HIỂM & BIÊN BẢN (2:00 – 3:15)
* 🖱️ **Thao tác:**
  1. Chuyển sang Tab **"Mũ bảo hiểm"** (`helmets`).
  2. Cho chạy đoạn video xe máy đông đúc (`dong_xe_may_hanoi_01.mp4`).
  3. Khi xuất hiện thẻ vi phạm viền đỏ nổi bật, chỉ vào thông tin đối soát biển số và mức phạt 400k-600k.
  4. Click vào ảnh bằng chứng hoặc nút **"Chi tiết vi phạm"** để mở Cửa sổ Modal Trích xuất bằng chứng.
* 🎙️ **Lời thoại mẫu:**
> *"Tiếp theo là tính năng hỗ trợ xử lý vi phạm đặc thù tại Việt Nam: **Phát hiện người đi xe máy không đội mũ bảo hiểm**:  
> - AI tự động bóc tách người lái xe mô tô, nhận diện trạng thái đầu trần hoặc đội mũ không đạt chuẩn quy chuẩn QCVN 2:2008.  
> - Mỗi đối tượng được AI theo dõi qua từng khung hình (tracking ID), kèm việc liên kết biển số xe máy tương ứng.  
> - Hệ thống tự động trích dẫn căn cứ pháp lý: **Điểm b Khoản 4 Điều 2 Nghị định 123/2021 (sửa đổi Nghị định 100)**, áp dụng mức xử phạt **400.000đ – 600.000đ**.  
> - Khi cơ quan chức năng hoặc cảnh sát giao thông cần xác minh, chỉ cần nhấp vào **'Chi tiết vi phạm'** — Một bộ hồ sơ điện tử kèm ảnh chụp phóng to, mã hồ sơ và nút **'In phiếu ghi nhận'** sẵn sàng phục vụ xử phạt nguội ngay lập tức."*

---

### 🔹 PHẦN 4: CAMERA BUỒNG LÁI (DMS) — CHỐNG BUỒNG NGỦ & LÁI QUÁ GIỜ (3:15 – 4:15)
* 🖱️ **Thao tác:**
  1. Chỉ chuột sang góc **Camera Cabin DMS** bên phải.
  2. Bật webcam hoặc video tài xế.
  3. Thao tác mô phỏng thực tế: **Nhắm mắt trong 2 - 3 giây** hoặc **há to miệng ngáp**.
  4. Để hệ thống kích hoạt chuông cảnh báo đỏ và loa phát giọng đọc cảnh báo.
* 🎙️ **Lời thoại mẫu:**
> *"Bên cạnh việc nhìn ra ngoài đường, hệ thống bảo vệ an toàn cho chính người lái qua **Camera Cabin DMS**:  
> - Thuật toán bóc tách điểm mốc khuôn mặt tính toán chỉ số nhắm mắt EAR và mở miệng ngáp MAR.  
> - Khi tài xế nhắm mắt quá ngưỡng quy định (dấu hiệu ngủ gật) hoặc ngáp liên tục vì kiệt sức, chuông báo động đỏ lập tức kích hoạt cùng giọng nói nhắc nhở: *'Cảnh báo nguy hiểm! Tài xế có dấu hiệu buồn ngủ, vui lòng dừng xe nghỉ ngơi!'*.  
> - Ngoài ra, thanh giám sát phía dưới tự động tính toán thời gian lái xe liên tục theo **Nghị định 10**, tự động cảnh báo khi tài xế lái liên tục sắp chạm mốc 4 giờ."*

---

### 🔹 PHẦN 5: TRUNG TÂM QUẢN LÝ DỮ LIỆU & TỔNG KẾT (4:15 – 5:00)
* 🖱️ **Thao tác:** Nhấp nhanh sang menu `/violations` hoặc `/dashboard` để chiếu giao diện danh sách các biên bản vi phạm đã được ghi nhận tự động vào cơ sở dữ liệu.
* 🎙️ **Lời thoại mẫu:**
> *"Cuối cùng, mọi dữ liệu vi phạm và thông số hành trình đều được đồng bộ về Trung tâm điều hành tại trang Quản lý Vi phạm. Tại đây có thể lọc theo loại vi phạm, biển số xe, ngày giờ và xuất báo cáo thống kê.  
> **Tổng kết lại**, Smart Driving Assistant là giải pháp 2 trong 1: Vừa là trợ lý đồng hành bảo vệ mạng sống cho tài xế trên từng cây số, vừa là công cụ số hóa đắc lực giúp lực lượng chức năng giám sát trật tự an toàn giao thông theo đúng luật pháp Việt Nam.  
> Em xin chân thành cảm ơn thầy cô và các bạn đã theo dõi! Sau đây em xin mời thầy cô đặt câu hỏi ạ."*

---

## 4. 💡 BÍ KÍP & PHÍM TẮT ĐẠT ĐIỂM TỐI ĐA
- **Phím Space (Cách):** Tạm dừng / Tiếp tục video đang phát để dừng đúng khung hình nét giải thích chi tiết.
- **Phím Tab / Click icon:** Đổi nhanh giữa 4 tab (Biển số `🪪`, Biển báo `⛔`, Cự ly `🚗`, Mũ bảo hiểm `🪖`).
- **Chế độ Offline 100%:** Nhấn mạnh với hội đồng hệ thống hoàn toàn có thể chạy cục bộ không cần Internet, phù hợp xe di chuyển trên vùng sóng yếu.
- **Xử lý câu hỏi về độ trễ (Latency):** Hệ thống đạt từ 25 - 35 FPS trên máy tính thông thường nhờ tối ưu hóa mô hình YOLO và Web Worker.
