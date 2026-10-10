# 🎨 SỔ TAY TOÀN BỘ HÌNH ẢNH, SƠ ĐỒ & MÃ NGUỒN VẼ DIAGRAM (BÁO CÁO 90 TRANG)
## DỰ ÁN: HỆ THỐNG TRỢ LÝ LÁI XE THÔNG MINH VÀ GIÁM SÁT AN TOÀN ĐỘI XE — TRAFFICGUARD

> **TÀI LIỆU DÀNH CHO TÁC GIẢ BÁO CÁO ĐỒ ÁN / KHÓA LUẬN:**
> * Tất cả sơ đồ kiến trúc, luồng xử lý, sequence, ERD, máy trạng thái đều được cung cấp **MÃ NGUỒN MERMAID / DRAW.IO CHUẨN**. Bạn chỉ cần sao chép mã và dán vào [draw.io](https://app.diagrams.net/) (chọn *Arrange -> Insert -> Advanced -> Mermaid*) hoặc trang [mermaid.live](https://mermaid.live/) là xuất được ảnh SVG/PNG vector sắc nét 100%.
> * Tất cả hình ảnh chụp màn hình, ảnh crop AI đều đi kèm **QUY TẮC BỐ CỤC CHỐNG CHE KHUẤT (Non-Obscuring Annotation Guidelines)**: nhãn đặt bên ngoài vùng quan sát, đường dẫn mũi tên thanh mảnh, hộp thoại phụ trợ nằm ở góc thoáng, đảm bảo người đọc thấy rõ toàn cảnh đối tượng (xe, biển báo, biển số, mặt người).

---

## 📑 MỤC LỤC DANH MỤC HÌNH ẢNH (35 HÌNH TOÀN KHÓA LUẬN)

* [CHƯƠNG 1: TỔNG QUAN & BỐI CẢNH](#chương-1-tổng-quan--bối-cảnh) (Hình 1.1 -> 1.2)
* [CHƯƠNG 2: CƠ SỞ LÝ THUYẾT & CÔNG NGHỆ](#chương-2-cơ-sở-lý-thuyết--công-nghệ) (Hình 2.1 -> 2.7)
* [CHƯƠNG 3: PHÂN TÍCH YÊU CẦU & KIẾN TRÚC](#chương-3-phân-tích-yêu-cầu--kiến-trúc) (Hình 3.1 -> 3.4)
* [CHƯƠNG 4: 12 MODULE TRÍ TUỆ NHÂN TẠO (AI PIPELINE)](#chương-4-12-module-trí-tuệ-nhân-tạo-ai-pipeline) (Hình 4.1 -> 4.10)
* [CHƯƠNG 5: MÁY CHỦ BACKEND & CSDL FASTAPI](#chương-5-máy-chủ-backend--csdl-fastapi) (Hình 5.1 -> 5.5)
* [CHƯƠNG 6: GIAO DIỆN WEB DASHBOARD & MOBILE APP](#chương-6-giao-diện-web-dashboard--mobile-app) (Hình 6.1 -> 6.7)
* [CHƯƠNG 7: KIỂM THỬ, THỰC NGHIỆM & HIỆU NĂNG](#chương-7-kiểm-thử-thực-nghiệm--hiệu-năng) (Hình 7.1 -> 7.3)
* [CHƯƠNG 8: TRIỂN KHAI PRODUCTION & PHÁP LÝ](#chương-8-triển-khai-production--pháp-lý) (Hình 8.1 -> 8.2)

---

# CHI TIẾT TỪNG HÌNH ẢNH, SƠ ĐỒ VÀ MÃ DIAGRAM

---

## CHƯƠNG 1: TỔNG QUAN & BỐI CẢNH

### 🖼️ Hình 1.1: Sơ đồ Ma trận Định vị và So sánh Tính năng TrafficGuard với Thị trường
* **Vị trí trong báo cáo:** Mục 1.2 (Tổng quan các giải pháp trong và ngoài nước).
* **Mô tả nội dung:** Biểu đồ so sánh 3 trục hoặc dạng lưới định vị giải pháp: So sánh TrafficGuard với các giải pháp quốc tế đắt tiền (Mobileye, Samsara) và các giải pháp nội địa hiện hành (Camera Nghị định 10). Thể hiện rõ TrafficGuard tối ưu chi phí thấp nhưng có tính thời gian thực cao và chuyên biệt hóa cho giao thông Việt Nam.
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
quadrantChart
    title Ma trận Định vị Giải pháp Công nghệ Giám sát Giao thông
    x-axis "Chi phí Triển khai Cao" --> "Chi phí Tối ưu / Thấp"
    y-axis "Xử lý Chậm / Thụ động" --> "Thời gian thực Siêu tốc (< 40ms)"
    quadrant-1 "TrafficGuard (Tối ưu & Thời gian thực)"
    quadrant-2 "Mobileye / Samsara (Đắt đỏ & Thời gian thực)"
    quadrant-3 "Camera Nghị định 10 (Chụp ảnh định kỳ 3-5p)"
    quadrant-4 "GPS Tracking cơ bản (Chỉ đo tốc độ)"
    "TrafficGuard Platform": [0.85, 0.90]
    "Mobileye 8 Connect": [0.20, 0.88]
    "Samsara AI Dashcam": [0.25, 0.85]
    "Camera NĐ 10/2020": [0.70, 0.25]
    "Định vị GPS truyền thống": [0.80, 0.15]
```
* **Quy tắc chú thích không che khuất:** Để nhãn điểm nằm bên phải các chấm tròn, giãn cách tối thiểu 15px so với các trục tọa độ.

---

### 🖼️ Hình 1.2: Sơ đồ Phương pháp luận Nghiên cứu và Lộ trình Triển khai Dự án
* **Vị trí trong báo cáo:** Mục 1.4 (Phương pháp tiếp cận nghiên cứu).
* **Mô tả nội dung:** Lưu đồ khối các giai đoạn: Khảo sát luật giao thông $\rightarrow$ Thu thập dữ liệu video $\rightarrow$ Huấn luyện mô hình AI $\rightarrow$ Xây dựng Backend/Frontend $\rightarrow$ Kiểm thử 90/90 bài test $\rightarrow$ Đóng gói triển khai.
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart TD
    A["Giai đoạn 1: Khảo sát & Pháp lý\n(Luật GTVT, TT 31/2019, QCVN 41:2019)"] --> B["Giai đoạn 2: Thu thập & Chuẩn hóa Dữ liệu\n(Video Dashcam VN, Ảnh Biển số, Mẫu Biển báo)"]
    B --> C["Giai đoạn 3: Huấn luyện & Tối ưu AI Core\n(YOLOv8, YOLOv11, MediaPipe 468 mesh, OCR)"]
    C --> D["Giai đoạn 4: Phát triển Backend & CSDL\n(FastAPI ASGI, 15 Bảng SQLAlchemy, WebSocket)"]
    D --> E["Giai đoạn 5: Phát triển Dashboard & Mobile\n(Next.js 14 Canvas 60fps, Expo HUD, Voice VN)"]
    E --> F["Giai đoạn 6: Kiểm thử Toàn diện & Nghiệm thu\n(PyTest 90/90 Pass, Benchmark mAP & Latency 38ms)"]
    F --> G["Giai đoạn 7: Đóng gói & Triển khai Production\n(Script 1-chạm, Clean Architecture, Docker)"]

    style A fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px;
    style C fill:#ECFDF5,stroke:#10B981,stroke-width:2px;
    style D fill:#FAF5FF,stroke:#8B5CF6,stroke-width:2px;
    style E fill:#FFFBEB,stroke:#F59E0B,stroke-width:2px;
    style F fill:#FEF2F2,stroke:#EF4444,stroke-width:2px;
    style G fill:#F8FAFC,stroke:#475569,stroke-width:2px;
```

---

## CHƯƠNG 2: CƠ SỞ LÝ THUYẾT & CÔNG NGHỆ

### 🖼️ Hình 2.1: Kiến trúc Mạng Nơ-ron Phát hiện Vật thể YOLOv8
* **Vị trí trong báo cáo:** Mục 2.1 (Mạng nơ-ron tích chập và mô hình YOLO).
* **Mô tả nội dung:** Sơ đồ 3 phần của YOLOv8: Backbone (CSPDarknet/C2f trích xuất đặc trưng đa tầng) $\rightarrow$ Neck (Path Aggregation Network - PANet kết hợp thông tin không gian và ngữ nghĩa) $\rightarrow$ Head (Anchor-Free Decoupled Head phân loại và hồi quy hộp bao).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart LR
    subgraph BACKBONE["BACKBONE (Trích xuất đặc trưng)"]
        In["Khung hình đầu vào\n(640x640x3)"] --> C1["Conv P1\n(320x320)"]
        C1 --> C2["C2f Block P2\n(160x160)"]
        C2 --> C3["C2f Block P3\n(80x80)"]
        C3 --> C4["C2f Block P4\n(40x40)"]
        C4 --> C5["SPPF Block P5\n(20x20)"]
    end

    subgraph NECK["NECK (PANet Feature Fusion)"]
        C5 --> N1["Upsample & Concat P4"]
        N1 --> N2["Upsample & Concat P3"]
        N2 --> N3["Downsample & Concat P4"]
        N3 --> N4["Downsample & Concat P5"]
    end

    subgraph HEAD["HEAD (Anchor-Free Decoupled Head)"]
        N2 --> H1["Detection Head P3 (Vật thể nhỏ)"]
        N3 --> H2["Detection Head P4 (Vật thể vừa)"]
        N4 --> H3["Detection Head P5 (Vật thể lớn)"]
        H1 & H2 & H3 --> Out["Hộp bao Bounding Box\n+ Độ tin cậy + Phân lớp"]
    end

    style BACKBONE fill:#EFF6FF,stroke:#3B82F6;
    style NECK fill:#F0FDF4,stroke:#10B981;
    style HEAD fill:#FEF2F2,stroke:#EF4444;
```

---

### 🖼️ Hình 2.2: Sơ đồ 468 Điểm mốc 3D Khuôn mặt MediaPipe Face Mesh & Tọa độ Mắt/Miệng
* **Vị trí trong báo cáo:** Mục 2.2 (Chỉ số sinh trắc học và thuật toán DMS).
* **Mô tả nội dung:** Bản vẽ cấu trúc 468 điểm mốc trên khuôn mặt tài xế, phóng to chi tiết 6 điểm mốc của mắt trái (p1, p2, p3, p4, p5, p6) dùng tính EAR và 8 điểm mốc môi (m1 đến m8) dùng tính MAR.
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart TD
    subgraph EYE["CẤU TRÚC 6 ĐIỂM TÍNH EAR (Eye Aspect Ratio)"]
        p1["p1 (Khóe mắt ngoài)"] --- p2["p2 (Mí trên đỉnh trái)"]
        p2 --- p3["p3 (Mí trên đỉnh phải)"]
        p3 --- p4["p4 (Khóe mắt trong)"]
        p4 --- p5["p5 (Mí dưới đáy phải)"]
        p5 --- p6["p6 (Mí dưới đáy trái)"]
        p6 --- p1
        d_v1["Khoảng cách dọc 1: ||p2 - p6||"] -.-> p2 & p6
        d_v2["Khoảng cách dọc 2: ||p3 - p5||"] -.-> p3 & p5
        d_h["Khoảng cách ngang: ||p1 - p4||"] -.-> p1 & p4
    end

    subgraph MOUTH["CẤU TRÚC 8 ĐIỂM TÍNH MAR (Mouth Aspect Ratio)"]
        m1["m1 (Mép trái)"] --- m2["m2"] --- m3["m3 (Môi trên giữa)"] --- m4["m4"] --- m5["m5 (Mép phải)"]
        m5 --- m6["m6"] --- m7["m7 (Môi dưới giữa)"] --- m8["m8"] --- m1
        d_mv["Độ mở dọc: ||m3 - m7||"] -.-> m3 & m7
    end

    style EYE fill:#EFF6FF,stroke:#2563EB,stroke-width:2px;
    style MOUTH fill:#FFFBEB,stroke:#D97706,stroke-width:2px;
```
* **Quy tắc chú thích không che khuất:** Các đường kích thước (||p2-p6||, ||p1-p4||) đặt nét đứt và nằm bên ngoài đường bao của mắt, các điểm số p1..p6 đặt lệch góc 45 độ, không đè lên con ngươi.

---

### 🖼️ Hình 2.3: Đồ thị Sinh trắc học Biến thiên EAR và MAR theo Thời gian
* **Tệp ảnh đã tạo:** `report_assets/fig_ear_mar_clean.png` (sắc nét, không che chữ).
* **Mô tả nội dung:** Biểu đồ sóng 2 hàng song song. Hàng 1 thể hiện chỉ số mở mắt EAR tụt xuống dưới ngưỡng 0.20 khi nhắm mắt $> 1.5$s. Hàng 2 thể hiện chỉ số MAR vượt ngưỡng 0.65 khi ngáp ngủ.
* **Quy tắc chú thích:** Hộp cảnh báo đặt ở góc trái/phải thoáng, mũi tên chỉ dẫn màu đỏ trỏ đúng vào đáy sóng mà không đè lên các điểm dữ liệu.

---

### 🖼️ Hình 2.4: Sơ đồ Biến đổi Phối cảnh Homography chuyển ảnh 2D sang Mặt đường 3D
* **Vị trí trong báo cáo:** Mục 2.3 (Biến đổi phối cảnh phẳng).
* **Mô tả nội dung:** Trực quan hóa góc nhìn phối cảnh camera nghiêng trên kính lái (Perspective View) với 4 điểm neo trên làn đường biến đổi thành góc nhìn thẳng từ trên xuống (Bird's Eye View - BEV) bằng ma trận $H_{3 \times 3}$.
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart LR
    subgraph CAM["KHUNG ẢNH 2D (Perspective View)"]
        A["Điểm tiếp xúc bánh xe\nTọa độ pixel: (u, v)"]
        L1["Vạch làn trái (Hội tụ)"]
        L2["Vạch làn phải (Hội tụ)"]
        VP["Điểm ảo chân trời (Vanishing Point)"]
    end

    H["MA TRẬN HOMOGRAPHY H\n[Xw, Yw, 1]^T = H * [u, v, 1]^T\n(Ground Calibration Matrix)"]

    subgraph WORLD["MẶT ĐƯỜNG THỰC TẾ 3D (Bird's Eye View)"]
        W1["Tọa độ thực: (X_mét, Y_mét)"]
        P1["Hai vạch kẻ đường song song thực tế"]
        P2["Đo cự ly thực tế tới xe trước (mét)"]
        P3["Đo độ dịch chuyển Δd / Δt -> Vận tốc (km/h)"]
    end

    CAM --> H --> WORLD
    style CAM fill:#EFF6FF,stroke:#3B82F6;
    style H fill:#FEF3C7,stroke:#D97706,stroke-width:2px;
    style WORLD fill:#ECFDF5,stroke:#059669;
```

---

### 🖼️ Hình 2.5: Đồ thị Phân vùng Thời gian Va chạm Tiềm ẩn (TTC Dynamic Safety Zones)
* **Tệp ảnh đã tạo:** `report_assets/fig_ttc_zones_clean.png`.
* **Mô tả nội dung:** Đồ thị quan hệ giữa khoảng cách tới xe trước ($d$) và thời gian va chạm ước tính ($TTC = d / \Delta v$). Phân rõ 3 vùng màu: Đỏ (Nguy cấp $TTC \le 1.5$s), Vàng (Chú ý $1.5 < TTC \le 3.0$s), Xanh lá (An toàn $TTC > 3.0$s).

---

### 🖼️ Hình 2.6: Đồ thị Quy định Khoảng cách An toàn theo Thông tư 31/2019/TT-BGTVT
* **Tệp ảnh đã tạo:** `report_assets/fig_safe_distance_clean.png`.
* **Mô tả nội dung:** Đồ thị bậc thang thể hiện cự ly tối thiểu bắt buộc ứng với các dải tốc độ: $\le 60\text{km/h}$ (chủ động $\ge 35$m), $60-80\text{km/h}$ (55m), $80-100\text{km/h}$ (70m), $100-120\text{km/h}$ (100m). Đường nét đứt màu đỏ thể hiện hệ số $1.30\times$ khi trời mưa đường trơn.

---

### 🖼️ Hình 2.7: Quy chuẩn Cấu trúc Biển số xe Việt Nam (Thông tư 24/2023/TT-BCA)
* **Vị trí trong báo cáo:** Mục 2.4 (Quy chuẩn biển số xe cơ giới).
* **Mô tả nội dung:** Bản vẽ phân giải cấu trúc 2 định dạng biển số xe: Biển ô tô dài (1 hàng) và Biển ô tô vuông / xe máy (2 hàng).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart TD
    subgraph OTO_DAI["BIỂN DÀI Ô TÔ (1 Hàng chữ số)"]
        D1["51H (2 số tỉnh + 1 chữ seri)"] --- D2["- (Gạch ngang)"] --- D3["982.45 (5 số thứ tự + Dấu chấm)"]
    end

    subgraph OTO_VUONG["BIỂN VUÔNG Ô TÔ & XE MÁY (2 Hàng chữ số)"]
        H1["Hàng trên: 59-X3 (Mã địa phương + Seri)"]
        H2["Hàng dưới: 456.78 (Dãy số đăng ký phương tiện)"]
        H1 --- H2
    end

    subgraph REGEX["LUẬT KIỂM CHUẨN CÚ PHÁP (Regex Pattern)"]
        R1["Ô tô: ^[0-9]{2}[A-Z]{1,2}-[0-9]{3}\.[0-9]{2}$"]
        R2["Xe máy: ^[0-9]{2}-[A-Z0-9]{2}\n[0-9]{3}\.[0-9]{2}$"]
    end

    style OTO_DAI fill:#EFF6FF,stroke:#2563EB;
    style OTO_VUONG fill:#FFFBEB,stroke:#D97706;
    style REGEX fill:#ECFDF5,stroke:#059669;
```

---

## CHƯƠNG 3: PHÂN TÍCH YÊU CẦU & KIẾN TRÚC

### 🖼️ Hình 3.1: Sơ đồ Kiến trúc Tổng thể 4 Tầng của Nền tảng TrafficGuard
* **Tệp ảnh đã tạo:** `report_assets/fig_system_architecture.png`.
* **Mã nguồn vẽ lại vector trên draw.io / Mermaid (Cực kỳ sắc nét):**
```mermaid
flowchart TD
    subgraph T1["TẦNG 1: THIẾT BỊ BIÊN & THU THẬP DỮ LIỆU (EDGE DATA ACQUISITION)"]
        C1["IP Dashcam Góc rộng\n(Road 1080p @ 30fps)"]
        C2["Cabin Camera Góc hẹp\n(DMS Face Sensor)"]
        C3["Điện thoại Di động\n(Expo Camera Stream)"]
        C4["Tệp Video Demo (.mp4)\n(Giả lập tải trực tiếp)"]
    end

    subgraph T2["TẦNG 2: LÕI XỬ LÝ TRÍ TUỆ NHÂN TẠO 12 MODULE (AI CORE PIPELINE)"]
        direction TB
        subgraph ROAD["Nhánh Thị giác Mặt đường"]
            M1["1. Vehicle Detector (YOLOv8)"] --> M2["2. MOT Tracker"]
            M2 --> M3["3. Speed Estimator"]
            M3 --> M4["4. Safe Distance & TTC"]
            M4 --> M5["5. Sign QCVN 41 & S.508"]
            M5 --> M6["6. Plate OCR & Helmet"]
        end
        subgraph CABIN["Nhánh Giám sát Người lái DMS"]
            M7["7. MediaPipe 468 Face Mesh"] --> M8["8. EAR/MAR & PERCLOS 60s"]
            M8 --> M9["9. Head Pose (Pitch/Yaw)"]
            M9 --> M10["10. Eyes Closed Alarm"]
            M10 --> M11["11. Seatbelt & Driving Timer"]
        end
        SHED["Load Shedder (Điều tiết tải động) & Quality Gate"] --> ROAD & CABIN
    end

    subgraph T3["TẦNG 3: MÁY CHỦ DOANH NGHIỆP & CƠ SỞ DỮ LIỆU (BACKEND & DATABASE)"]
        API["FastAPI RESTful Service\n(13 Routers, 30+ Endpoints)"]
        WS["WebSocket Server Dispatcher\n(Song công độ trễ < 38ms)"]
        DEC["Decision Engine\n(Lọc nhiễu & Phân cấp ưu tiên)"]
        ANON["Privacy Anonymizer\n(Làm mờ NĐ 13/2023 & SHA-256)"]
        DB[("Cơ sở dữ liệu Quan hệ\n15 Bảng SQLAlchemy (SQLite/Postgres)")]
        STORE[("Kho lưu trữ Ảnh bằng chứng\nLocal Object Storage (/storage/)")]
        API & WS --- DEC --- DB & STORE
    end

    subgraph T4["TẦNG 4: GIAO DIỆN NGƯỜI DÙNG & ĐIỀU HÀNH (PRESENTATION LAYER)"]
        WEB["Web Dashboard (Next.js 14 App Router)\n• Canvas 60 FPS Bounding Box\n• Giám sát Live CCTV kép\n• Duyệt vi phạm & Báo cáo"]
        MOB["Mobile App HUD (Expo React Native)\n• Đồng hồ tốc độ HUD trên kính lái\n• Mắt thần quét đường & Còi báo"]
        VOICE["Động cơ Âm thanh & Giọng nói tiếng Việt\n(Web Audio Bíp tần số cao & Web Speech API)"]
    end

    T1 ==> T2 ==> T3 ==> T4

    style T1 fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px;
    style T2 fill:#ECFDF5,stroke:#10B981,stroke-width:2px;
    style T3 fill:#FAF5FF,stroke:#8B5CF6,stroke-width:2px;
    style T4 fill:#FFFBEB,stroke:#F59E0B,stroke-width:2px;
```

---

### 🖼️ Hình 3.2: Sơ đồ Ca sử dụng Tổng thể (Use-Case Diagram)
* **Vị trí trong báo cáo:** Mục 3.2 (Mô hình ca sử dụng).
* **Mô tả nội dung:** 3 tác nhân (Admin Doanh nghiệp, Điều độ viên, Tài xế) tương tác với các Use-Case của hệ thống.
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart LR
    Admin((Quản trị viên\nAdmin))
    Disp((Điều độ viên\nDispatcher))
    Driver((Tài xế\nDriver))

    subgraph UC_SYS["HỆ THỐNG TRAFFICGUARD"]
        UC1["UC1: Đăng nhập & Xác thực JWT"]
        UC2["UC2: Xem Dashboard & KPI An toàn"]
        UC3["UC3: Giám sát Live Camera AI luồng kép"]
        UC4["UC4: Quản lý Danh mục Xe & Gán Tài xế"]
        UC5["UC5: Quản lý Nhân sự & Phân quyền"]
        UC6["UC6: Tra cứu & Duyệt Biên bản Vi phạm"]
        UC7["UC7: Xem Ảnh Bằng chứng & Tải Biên bản"]
        UC8["UC8: Xuất Báo cáo Thống kê & Phân tích"]
        UC9["UC9: Chế độ Lái xe HUD trên Kính lái"]
        UC10["UC10: Nhận Cảnh báo Giọng nói Tiếng Việt"]
        UC11["UC11: Xem Điểm An toàn Cá nhân (Safety Score)"]
        UC12["UC12: Cấu hình Ngưỡng Cảnh báo AI"]
    end

    Admin --> UC1 & UC2 & UC3 & UC4 & UC5 & UC6 & UC7 & UC8 & UC12
    Disp --> UC1 & UC2 & UC3 & UC6 & UC7 & UC8
    Driver --> UC1 & UC9 & UC10 & UC11

    style Admin fill:#FEF2F2,stroke:#DC2626;
    style Disp fill:#EFF6FF,stroke:#2563EB;
    style Driver fill:#ECFDF5,stroke:#059669;
```

---

### 🖼️ Hình 3.3: Sơ đồ Luồng Dữ liệu (Data Flow Diagram - DFD Cấp 1)
* **Vị trí trong báo cáo:** Mục 3.3 (Luồng dữ liệu hệ thống).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart TD
    CAM["Camera Hành trình / Mobile"] -->|"1. Khung hình Frame (JPEG/Base64)"| P1["1.0 Tiếp nhận & Điều tiết Tải\n(Load Shedder & Quality Gate)"]
    P1 -->|"2. Frame Hợp lệ"| P2["2.0 Phân tích AI Song song\n(Road AI + Cabin DMS)"]
    P2 -->|"3. Tọa độ Box, Tốc độ, Cự ly, EAR"| P3["3.0 Động cơ Ra Quyết định\n(Decision Engine & Lọc nhiễu)"]
    P3 -->|"4. Gói tin Telemetry thời gian thực"| P4["4.0 Phát truyền WebSocket\n(/ws/driving-stream)"]
    P4 -->|"5. Hiển thị tức thời < 38ms"| UI["Canvas Web Dashboard & Mobile HUD"]
    P3 -->|"6. Sự cố Vi phạm (TTC < 1.5s, Ngủ gật)"| P5["5.0 Đóng gói Bằng chứng & Ẩn danh\n(Gaussian Blur & SHA-256)"]
    P5 -->|"7. Lưu bản ghi Vi phạm"| DB[("CSDL Quan hệ & Storage")]

    style P2 fill:#ECFDF5,stroke:#10B981;
    style P3 fill:#FAF5FF,stroke:#8B5CF6;
    style DB fill:#FFFBEB,stroke:#F59E0B;
```

---

### 🖼️ Hình 3.4: Sơ đồ Quan hệ Thực thể Cơ sở Dữ liệu (ERD - 15 Bảng)
* **Vị trí trong báo cáo:** Mục 3.4 (Thiết kế cơ sở dữ liệu quan hệ).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
erDiagram
    organizations ||--o{ organization_structures : has
    organizations ||--o{ users : employs
    organizations ||--o{ vehicles : owns
    organizations ||--o{ ai_configs : configures
    users ||--o| drivers : profile
    users ||--o{ audit_logs : generates
    users ||--o{ notifications : receives
    vehicles ||--o{ driving_sessions : tracks
    vehicles ||--o{ device_health : monitors
    drivers ||--o{ driving_sessions : operates
    drivers ||--o{ coaching_records : coached
    driving_sessions ||--o{ violations : records
    driving_sessions ||--o{ trip_events : logs
    violations ||--o| violation_reviews : reviewed
    violations ||--o{ coaching_records : triggers

    organizations {
        int id PK
        string name
        string tax_code
        string plan_tier
    }
    users {
        int id PK
        string email
        string hashed_password
        string role
        int organization_id FK
    }
    drivers {
        int id PK
        int user_id FK
        string license_number
        float safety_score
    }
    vehicles {
        int id PK
        string plate_number
        string vehicle_type
        int driver_id FK
    }
    driving_sessions {
        int id PK
        int vehicle_id FK
        int driver_id FK
        datetime started_at
        datetime ended_at
        float total_km
    }
    violations {
        int id PK
        int session_id FK
        string violation_type
        float speed_kmh
        float distance_m
        string evidence_image_path
        string evidence_hash_sha256
    }
    violation_reviews {
        int id PK
        int violation_id FK
        string status
        string review_notes
    }
```

---

## CHƯƠNG 4: 12 MODULE TRÍ TUỆ NHÂN TẠO (AI PIPELINE)

### 🖼️ Hình 4.1: Sơ đồ Luồng Xử lý Song song 2 Nhánh (Dual-Stream Pipeline)
* **Vị trí trong báo cáo:** Mục 4.1 (Kiến trúc tổng thể Pipeline AI).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart TD
    In[("Luồng Video Khung hình Đầu vào\n(Dual RTSP / Webcam / File MP4)")] --> Split{"Bộ phân tách luồng\n(Stream Dispatcher)"}
    
    subgraph ROAD["NHÁNH 1: ROAD VISION (Mặt đường)"]
        Split -->|"Luồng Mặt đường"| VDet["Module 1: Vehicle Detector (YOLOv8)"]
        VDet --> MOT["Module 2: Multi-Object Tracker (MOT)"]
        MOT --> Speed["Module 3: Speed Estimator (Homography)"]
        Speed --> SafeDist["Module 8: Safe Distance (Thông tư 31)"]
        SafeDist --> TTC["Module 7: Collision Warning (TTC)"]
        MOT --> Lane["Module 4: Lane & LDWS Manager"]
        VDet --> Sign["Module 9: Sign QCVN 41 & Biển phụ S.508"]
        Sign --> SpeedRec["Module 10: Speed Recommendation"]
        VDet --> Plate["Module 5: Plate OCR (YOLOv11+OCR)"]
        VDet --> Helmet["Module 6: Helmet Checker (Deduplication)"]
    end

    subgraph CABIN["NHÁNH 2: CABIN DMS (Người lái)"]
        Split -->|"Luồng Cabin"| Mesh["Module 11: MediaPipe 468 Face Mesh"]
        Mesh --> Bio["Tính toán EAR, MAR & Head Pose 3D"]
        Bio --> EyeMon["Eyes Closed Monitor (Nhắm mắt > 1.5s)"]
        Bio --> Perclos["PERCLOS 60s (Ngủ gật) & Ngáp ngủ"]
        Mesh --> Belt["Module 12: Seatbelt & Driving Timer (4 Giờ)"]
    end

    ROAD & CABIN --> Fusion["Bộ hợp nhất Sự kiện (Sensor Fusion Engine)"]
    Fusion --> VMan["Violation Manager (Đóng gói Bằng chứng & Cảnh báo)"]

    style ROAD fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px;
    style CABIN fill:#FFFBEB,stroke:#D97706,stroke-width:2px;
    style Fusion fill:#ECFDF5,stroke:#059669,stroke-width:2px;
```

---

### 🖼️ Hình 4.2: Sơ đồ Thuật toán Bám vết Đa đối tượng (MOT IoU + Hungarian)
* **Vị trí trong báo cáo:** Mục 4.2.2 (Module bám vết đa đối tượng).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart TD
    D["Danh sách Bounding Boxes phát hiện tại Frame t"] --> Mat["Xây dựng Ma trận Chi phí IoU (Cost Matrix)"]
    T["Danh sách Tracks đang theo dõi từ Frame t-1"] --> Mat
    Mat --> Hung["Giải thuật Tối ưu Hungarian Matching"]
    Hung --> Matched{"Kết quả Ghép cặp?"}
    Matched -->|"Khớp IoU ≥ 0.45"| Upd["Cập nhật vị trí Track & Duy trì Tracker ID"]
    Matched -->|"Chưa khớp trong Tracks"| Miss["Tăng biến đếm Mất dấu (Missing Count)"]
    Matched -->|"Hộp bao mới hoàn toàn"| NewT["Khởi tạo Track mới & Cấp ID mới"]
    Miss --> DelCheck{"Missing > 5 Frames?"}
    DelCheck -->|"Đúng"| Delete["Xóa Track khỏi bộ nhớ"]
    DelCheck -->|"Sai"| Keep["Bảo lưu quỹ đạo (Chờ bù che khuất)"]

    style Hung fill:#FEF3C7,stroke:#D97706;
    style Upd fill:#ECFDF5,stroke:#059669;
    style NewT fill:#EFF6FF,stroke:#2563EB;
```

---

### 🖼️ Hình 4.3: Sơ đồ Thuật toán Ước tính Vận tốc Xe qua Ma trận Homography
* **Vị trí trong báo cáo:** Mục 4.2.3 (Module ước tính vận tốc).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart LR
    BBox["Bounding Box Xe tại Frame t & Frame t-1"] --> Foot["Xác định tâm điểm đáy tiếp xúc mặt đường:\nu = (x1 + x2)/2, v = y2"]
    Foot --> HMat["Nhân Ma trận Homography H:\n[X_w, Y_w, 1]^T = H * [u, v, 1]^T"]
    HMat --> Delta["Tính khoảng cách dịch chuyển vật lý:\nΔd = √[(X_t - X_{t-1})² + (Y_t - Y_{t-1})²] (mét)"]
    Delta --> Vel["Vận tốc tức thời:\nv_inst = (Δd / Δt) * 3.6 (km/h)"]
    Vel --> Filter["Bộ lọc Trung bình trượt (Moving Average N=5):\nv_smooth = 1/5 * ∑ v_inst"]
    Filter --> Out["Vận tốc Ổn định Hiển thị trên Canvas"]

    style HMat fill:#FAF5FF,stroke:#8B5CF6;
    style Filter fill:#ECFDF5,stroke:#059669;
```

---

### 🖼️ Hình 4.4: Sơ đồ Quy trình 3 Giai đoạn Nhận diện Biển số xe Việt Nam
* **Vị trí trong báo cáo:** Mục 4.2.5 (Module nhận diện biển số xe).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart TD
    F["Khung hình xe vi phạm"] --> D1["Giai đoạn 1: YOLOv11 License Plate Detection\n(Cắt vùng hộp bao biển số ROI)"]
    D1 --> P2["Giai đoạn 2: Tiền xử lý Hình ảnh Chuyên sâu"]
    subgraph PREP["Tiền xử lý Rectification"]
        P2 --> P21["Xoay nắn góc nghiêng phẳng (Perspective Transform)"]
        P21 --> P22["Cân bằng sáng thích ứng CLAHE"]
        P22 --> P23["Nhị phân hóa thích ứng Otsu / Adaptive Threshold"]
    end
    PREP --> O3["Giai đoạn 3: Nhận diện Ký tự & Chuẩn hóa"]
    subgraph OCR_STEP["OCR & Regex Matching"]
        O3 --> O31["Phân đoạn 1 hàng hoặc 2 hàng biển số"]
        O31 --> O32["EasyOCR đọc các ký tự chữ và số"]
        O32 --> O33["Bộ lọc quy chuẩn cú pháp Thông tư 24/2023/TT-BCA\n(Khử nhầm '0'/'O', '1'/'I', chèn dấu chấm phân tách)"]
    end
    OCR_STEP --> Out["Biển số xe Việt Nam Chuẩn\n(Ví dụ: 51H-982.45)"]

    style D1 fill:#EFF6FF,stroke:#3B82F6;
    style PREP fill:#FFFBEB,stroke:#F59E0B;
    style OCR_STEP fill:#ECFDF5,stroke:#10B981;
```

---

### 🖼️ Hình 4.5: Sơ đồ Thuật toán Khử trùng lặp Cảnh báo Mũ bảo hiểm (Deduplication)
* **Vị trí trong báo cáo:** Mục 4.2.6 (Module kiểm tra mũ bảo hiểm).
* **Mô tả:** Giữ cho hệ thống không bị bắn lặp lại hàng trăm cảnh báo cho cùng 1 người đi xe máy.
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart TD
    Det["Phát hiện đối tượng Motorcycle + Người lái"] --> Head["Cắt vùng đầu người lái (Head ROI)"]
    Head --> Classify{"Có đội mũ bảo hiểm?"}
    Classify -->|"Có đội"| OK["Trạng thái An toàn -> Bỏ qua"]
    Classify -->|"Không đội"| CheckTable{"Tracker ID này đã bị ghi nhận vi phạm trong bảng tạm chưa?"}
    CheckTable -->|"Đã có trong bảng"| Ignore["Bỏ qua cảnh báo lặp (Suppress Alert)"]
    CheckTable -->|"Chưa có"| Alert["1. Kích hoạt Cảnh báo Vi phạm Mũ bảo hiểm\n2. Đưa Tracker ID vào bảng đã phạt\n3. Chụp ảnh bằng chứng lưu CSDL"]

    style CheckTable fill:#FEF3C7,stroke:#D97706;
    style Alert fill:#FEE2E2,stroke:#DC2626,stroke-width:2px;
    style Ignore fill:#F1F5F9,stroke:#64748B;
```

---

### 🖼️ Hình 4.6: Sơ đồ Thuật toán Cắt lát Tỷ lệ Cột Biển báo (Pole Proportional Slicing)
* **Tệp ảnh đã tạo:** `report_assets/fig_pole_slicing_clean.png`.
* **Mô tả chi tiết & Quy tắc không che khuất:** 
  - Ảnh minh họa cột biển báo có 3 biển đặt dọc: Biển chính $P.124b$ (trên cùng), Biển phụ $S.508$ (giữa), Biển cảnh báo $W.245a$ (dưới cùng).
  - **Quy tắc chú thích:** 3 hộp mô tả giải thuật được kéo hẳn sang vùng nền trắng phía bên phải (`x = 48..96`), sử dụng 3 đường mũi tên chỉ sang 3 biển báo bên trái. **Tuyệt đối không đè chữ lên mặt biển báo!**

---

### 🖼️ Hình 4.7: Mẫu Bộ Dữ liệu Biển báo Giao thông QCVN 41:2019
* **Tệp ảnh đã tạo:** `report_assets/fig_qcvn_signs_sample.png`.
* **Mô tả nội dung:** Lưới $2 \times 4$ hiển thị 8 mẫu biển báo giao thông sắc nét chuẩn QCVN 41: $P.101$ (Đường cấm), $P.102$ (Cấm đi ngược chiều), $P.103a$ (Cấm ô tô), $P.104$ (Cấm mô tô), $P.105$ (Cấm ô tô và mô tô), $DP.135$ (Hết mọi lệnh cấm), $I.401$ (Bắt đầu đường ưu tiên), $I.402$ (Hết đường ưu tiên).

---

### 🖼️ Hình 4.8: Sơ đồ Máy Trạng thái Giám sát Ngủ gật Cabin (DMS State Machine)
* **Vị trí trong báo cáo:** Mục 4.4.1 & 4.4.2 (Giám sát buồn ngủ & nhắm mắt kéo dài).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
stateDiagram-v2
    [*] --> KhoiHanh: Khởi động xe
    KhoiHanh --> CanChinhDong: Thu thập baseline mở mắt 15-30s đầu
    CanChinhDong --> BinhThuong: Đã có ngưỡng EAR/MAR cá nhân hóa

    state BinhThuong {
        [*] --> MatMo: EAR >= 0.20 & MAR <= 0.65
    }

    BinhThuong --> ChuY: MAR > 0.65 (Ngáp ngủ) hoặc PERCLOS 60s > 10%
    ChuY --> BinhThuong: Tài xế ngậm miệng, tỉnh táo trở lại
    
    BinhThuong --> BaoDongKhanCap: EAR < 0.20 liên tục vượt quá 1.5 giây (Microsleep)
    ChuY --> BaoDongKhanCap: EAR < 0.20 liên tục vượt quá 1.5 giây
    
    state BaoDongKhanCap {
        [*] --> PhatCoiHu: Phát âm thanh còi tần số cao 1200Hz
        PhatCoiHu --> PhatGiongNoi: Voice: "Cảnh báo: Tài xế đang buồn ngủ!"
        PhatGiongNoi --> GhiNhanViPham: Chụp ảnh bằng chứng & Gửi tín hiệu về trung tâm
    }

    BaoDongKhanCap --> BinhThuong: Tài xế mở mắt to trở lại (EAR >= 0.25)
```

---

### 🖼️ Hình 4.9: Sơ đồ Bộ đệm Khung hình Trượt (Rolling Buffer) & Đóng gói Bằng chứng
* **Vị trí trong báo cáo:** Mục 4.4.4 (Module quản lý lưu vết vi phạm).
* **Mô tả:** Cơ chế lưu 5 frames trước và 5 frames sau thời điểm xảy ra sự cố vi phạm.
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart LR
    subgraph ROLLING["BỘ ĐỆM KHUNG HÌNH TRƯỢT (Circular Buffer N=10)"]
        F1["Frame t-5"] --- F2["Frame t-4"] --- F3["Frame t-3"] --- F4["Frame t-2"] --- F5["Frame t-1"]
        F_EV["FRAME t\n(THỜI ĐIỂM VI PHẠM PHÁT SINH)"]
        F6["Frame t+1"] --- F7["Frame t+2"] --- F8["Frame t+3"] --- F9["Frame t+4"] --- F10["Frame t+5"]
        F5 --- F_EV --- F6
    end

    F_EV --> Trigger{"Kích hoạt Vi phạm\n(TTC ≤ 1.5s / Ngủ gật / Biển cấm)"}
    Trigger --> Pack["ĐÓNG GÓI HỒ SƠ BẰNG CHỨNG (Evidence Package):\n1. Khung hình Frame t nét nhất\n2. Bounding Box & Tọa độ\n3. Vận tốc xe + Cự ly khoảng cách mét\n4. Mã băm SHA-256 chống giả mạo\n5. Timestamp ISO 8601"]
    Pack --> DB[("Lưu vào Cơ sở dữ liệu & /storage/")]

    style F_EV fill:#FEE2E2,stroke:#DC2626,stroke-width:2px;
    style Pack fill:#EFF6FF,stroke:#2563EB;
```

---

## CHƯƠNG 5: MÁY CHỦ BACKEND & CSDL FASTAPI

### 🖼️ Hình 5.1: Sơ đồ Tuần tự (Sequence Diagram): Xác thực JWT & Phân quyền RBAC
* **Vị trí trong báo cáo:** Mục 5.2 (Xác thực và phân quyền RBAC).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng (Admin / Driver)
    participant Web as Web Dashboard / Mobile
    participant AuthAPI as Auth Router (/api/auth)
    participant Sec as Security Service (Bcrypt/JWT)
    participant DB as CSDL SQLAlchemy

    User->>Web: Nhập Email & Mật khẩu
    Web->>AuthAPI: POST /api/auth/login {email, password}
    AuthAPI->>DB: Truy vấn user theo email
    DB-->>AuthAPI: Trả về User Record & Hashed Password
    AuthAPI->>Sec: verify_password(password, hashed_password)
    Sec-->>AuthAPI: Mật khẩu chính xác (True)
    AuthAPI->>Sec: create_access_token(user_id, role, scopes)
    Sec-->>AuthAPI: Access Token (JWT HS256)
    AuthAPI-->>Web: Trả về JSON {token, user_info, role}
    Web->>Web: Lưu token vào Store / LocalStorage

    Note over Web,AuthAPI: Các yêu cầu tiếp theo
    Web->>AuthAPI: GET /api/fleet/vehicles (Header: Bearer Token)
    AuthAPI->>Sec: decode_token & require_role(["admin", "dispatcher"])
    Sec-->>AuthAPI: Quyền hợp lệ (Authorized)
    AuthAPI->>DB: Lấy danh sách xe của doanh nghiệp
    DB-->>AuthAPI: Trả về dữ liệu xe
    AuthAPI-->>Web: Trả về JSON 200 OK
```

---

### 🖼️ Hình 5.2: Sơ đồ Tuần tự: Truyền thông WebSocket Streaming Thời gian thực
* **Vị trí trong báo cáo:** Mục 5.4 (Giao thức truyền thông WebSocket).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
sequenceDiagram
    autonumber
    actor Driver as Tài xế / Camera Stream
    participant Client as Web Canvas / Mobile App
    participant WS as WebSocket Endpoint (/ws/driving-stream)
    participant AI as AI Core Pipeline (12 Modules)
    participant DB as Database & Storage

    Client->>WS: Bắt tay kết nối: ws://localhost:8000/ws/driving-stream
    WS-->>Client: 101 Switching Protocols (Kết nối thành công)
    
    loop Mỗi chu kỳ khung hình (30 FPS)
        Client->>WS: Gửi khung hình Binary JPEG / Base64
        WS->>AI: Giải mã In-Memory & Chạy 12 Module AI
        AI-->>WS: Kết quả: Bounding Boxes, Tốc độ, Cự ly, Cờ FCW
        WS-->>Client: Phản hồi gói tin JSON Telemetry (Độ trễ ~38ms)
        Client->>Client: Vẽ đè Bounding Boxes lên HTML5 Canvas ở 60 FPS
        opt Khi phát hiện Vi phạm An toàn
            AI->>DB: Tự động ghi bản ghi vi phạm & Lưu ảnh bằng chứng
            WS-->>Client: Gửi cờ Cảnh báo Khẩn cấp (CRITICAL ALERT)
            Client->>Client: Phát còi hú Web Audio & Giọng nói tiếng Việt
        end
    end
```

---

### 🖼️ Hình 5.3: Sơ đồ Cây Phân cấp Ưu tiên Cảnh báo (Decision Engine)
* **Vị trí trong báo cáo:** Mục 5.5.1 (Động cơ ra quyết định cảnh báo).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart TD
    In["Sự kiện Cảnh báo phát sinh từ 12 Module AI"] --> Engine{"Động cơ Ra Quyết định\n(Decision Engine)"}
    
    Engine --> P1["MỨC 1: CRITICAL (Khẩn cấp cao nhất)\n• Nguy cơ va chạm sớm (TTC ≤ 1.5s)\n• Ngủ gật / Nhắm mắt > 1.5s\n--> CHIẾM QUYỀN: Bật còi hú + Giọng nói báo động"]
    
    Engine --> P2["MỨC 2: WARNING (Cảnh báo quan trọng)\n• Không giữ cự ly an toàn (TT 31/2019)\n• Quá tốc độ tối đa cho phép\n• Chệch làn đường (LDWS)\n--> Đổi viền màn hình sang màu Đỏ/Cam + Tiếng bíp"]
    
    Engine --> P3["MỨC 3: INFO (Nhắc nhở hỗ trợ)\n• Quên thắt dây an toàn khi khởi hành\n• Gợi ý tốc độ theo biển báo\n• Nhắc dừng nghỉ ngơi sau 4 giờ lái xe\n--> Hiển thị biểu ngữ nhắc nhở trên thanh trạng thái"]

    Debounce["Bộ lọc Chống dội (Debounce Filter Δt < 3s):\nTriệt tiêu cảnh báo trùng lặp liên tục"] -.-> Engine

    style P1 fill:#FEE2E2,stroke:#DC2626,stroke-width:2px;
    style P2 fill:#FEF3C7,stroke:#D97706,stroke-width:1.5px;
    style P3 fill:#EFF6FF,stroke:#2563EB,stroke-width:1.5px;
```

---

### 🖼️ Hình 5.4: Sơ đồ Quy trình Làm mờ Ẩn danh & Tạo Chữ ký Băm SHA-256 (NĐ 13/2023)
* **Vị trí trong báo cáo:** Mục 5.5.2 (Bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart LR
    Raw["Ảnh Bằng chứng Gốc\n(Chụp lúc xe vi phạm)"] --> Detect["Phát hiện vùng nhạy cảm:\n1. Mặt người đi bộ xung quanh\n2. Biển số xe khác không vi phạm"]
    Detect --> Blur["Áp dụng Gaussian Blur (k=31)\nLàm mờ hoàn toàn vùng nhạy cảm\n(Tuân thủ NĐ 13/2023/NĐ-CP)"]
    Blur --> AnonImg["Ảnh Bằng chứng Đã Ẩn danh"]
    AnonImg --> SHA["Thuật toán Băm Mật mã SHA-256\nhash = sha256(anon_image_bytes)"]
    SHA --> HashCode["Mã băm SHA-256 (Tamper-proof hash)\nVí dụ: 8f4e2...a9b1"]
    AnonImg --> Store[("/storage/evidence_xyz.jpg")]
    HashCode --> DB[("CSDL: Bảng violations\n(Lưu trường evidence_hash_sha256)")]

    style Blur fill:#FEF3C7,stroke:#D97706;
    style SHA fill:#ECFDF5,stroke:#059669;
```

---

## CHƯƠNG 6: GIAO DIỆN WEB DASHBOARD & MOBILE APP

### 🖼️ Hình 6.1: Bản vẽ Bố cục Giao diện Trung tâm Điều hành (`/dashboard`)
* **Vị trí trong báo cáo:** Mục 6.2.2 (Màn hình trung tâm điều hành).
* **Mô tả cấu trúc bố cục (Wireframe):**
  - **Hàng 1 (Header):** Logo TrafficGuard, Bộ chọn chi nhánh đội xe, Thông tin tài khoản đăng nhập.
  - **Hàng 2 (4 Thẻ KPI Metric):** 
    - Thẻ 1: *Fleet Safety Score* (Điểm trung bình an toàn toàn đội xe: 92/100, viền xanh).
    - Thẻ 2: *Active Journeys* (Số xe đang chạy trực tuyến: 14 xe).
    - Thẻ 3: *Total Violations* (Số vi phạm hôm nay: 8 vụ).
    - Thẻ 4: *Operating Hours* (Tổng giờ vận hành an toàn: 156 giờ).
  - **Hàng 3 (Hai cột chính):**
    - Cột trái (60%): Biểu đồ diện tích xu hướng vi phạm theo 24 giờ trong ngày.
    - Cột phải (40%): Danh sách các cảnh báo vi phạm khẩn cấp mới nhất kèm ảnh chụp thu nhỏ.

---

### 🖼️ Hình 6.2: Bản vẽ Bố cục Màn hình Giám sát Trực tuyến Live Camera Kép (`/live`)
* **Vị trí trong báo cáo:** Mục 6.2.3 (Màn hình giám sát trực tuyến).
* **Mô tả cấu trúc bố cục & Quy tắc chống che khuất:**
  - **Khung xem chính (Road Camera Viewport 16:9):** Hiển thị video mặt đường.
    - *Vị trí Bounding Box:* Vẽ đường viền 2px ôm sát xe. 
    - *Vị trí Nhãn thông tin:* Đặt ở góc trên bên trái của Bounding Box (ví dụ: `Xe con #4 | 54 km/h | 28m`), nền bán trong suốt để không che lấp vạch kẻ đường bên dưới.
    - *Thanh Telemetry (Dưới chân video):* Cố định ở đáy video, hiển thị Tốc độ hiện tại ($52\text{ km/h}$), Cự ly an toàn khuyến nghị ($35\text{m}$), Biển báo tốc độ giới hạn ($60\text{ km/h}$).
  - **Khung phụ góc trên bên phải (Cabin DMS Viewport 4:3):** Hiển thị khuôn mặt tài xế.
    - 468 điểm mốc hiển thị dạng chấm xanh mờ (alpha = 0.4), không che mắt tài xế.
    - Góc trên khung hình cabin hiển thị chỉ số: `EAR: 0.31 | MAR: 0.14 | Tỉnh táo`.
  - **Thanh cảnh báo nguy cấp (Critical Alert Bar):** Nằm ở phía trên cùng của trang web, chỉ xuất hiện khi có sự cố, không chèn đè lên video.

---

### 🖼️ Hình 6.3: Biểu đồ Cơ cấu Các loại Lỗi Vi phạm An toàn Giao thông Toàn Đội xe
* **Tệp ảnh đã tạo:** `report_assets/fig_violation_distribution_clean.png`.
* **Mô tả:** Biểu đồ tròn Donut Chart với chú giải (legend) được xếp ngay ngắn ở cột bên phải ngoài biểu đồ, không có nhãn chữ đè lên các lát cắt.

---

### 🖼️ Hình 6.4: Bản vẽ Bố cục Modal Soi Ảnh Bằng chứng Vi phạm Chi tiết (`/violations`)
* **Vị trí trong báo cáo:** Mục 6.2.4 (Màn hình quản lý hồ sơ vi phạm).
* **Mô tả:** Khi bấm vào 1 bản ghi vi phạm trong danh sách, modal hiện lên chia làm 2 cột:
  - Cột trái: Ảnh chụp bằng chứng độ phân giải cao trích xuất từ AI, hiển thị rõ biển số xe và cự ly đo đạc lúc vi phạm.
  - Cột phải: Bảng thông số chi tiết (Thời gian, Vận tốc lúc vi phạm, Loại lỗi, Tài xế phụ trách, Mã băm SHA-256) cùng hai nút bấm lớn: *Phê duyệt biên bản* (Xanh) và *Bác bỏ cảnh báo* (Xám).

---

### 🖼️ Hình 6.5: Bản vẽ Bố cục Màn hình Chẩn đoán Hiệu năng 12 Module AI (`/ai-status`)
* **Vị trí trong báo cáo:** Mục 6.2.8 (Màn hình chẩn đoán 12 module AI).
* **Mô tả:** Bảng lưới giám sát 12 thẻ (Grid 3x4). Mỗi thẻ đại diện cho 1 module AI hiển thị: Tên module, Tên model sử dụng, Trạng thái hoạt động (Active - Xanh lá), Tốc độ FPS thực tế (28 - 32 FPS), và Độ trễ tính toán (ms).

---

### 🖼️ Hình 6.6: Bản vẽ Bố cục Màn hình Lái xe HUD trên Điện thoại (`mobile-app/app/drive.tsx`)
* **Vị trí trong báo cáo:** Mục 6.4 (Hiện thực hóa ứng dụng di động).
* **Mô tả giao diện:**
  - Nền đen hoàn toàn (AMOLED Black) giúp hiển thị tương phản cao phản quang lên kính lái xe ban đêm.
  - Đồng hồ số lớn ở trung tâm: Hiển thị vận tốc thực tế (`68 km/h`).
  - Phía trên đồng hồ: Icon biển báo tốc độ giới hạn hiện tại (`80 km/h`).
  - Phía dưới đồng hồ: Thanh chỉ báo cự ly an toàn (`Khoảng cách: 58m | AN TOÀN`).
  - Viền ngoài toàn màn hình: Đổi màu theo trạng thái (Xanh lá: An toàn, Vàng: Chú ý, Đỏ nhấp nháy: Nguy hiểm).

---

### 🖼️ Hình 6.7: Sơ đồ Máy Trạng thái Hành trình Di động (tripStateMachine.ts)
* **Vị trí trong báo cáo:** Mục 6.4 (Quản lý vòng đời chuyến đi trên di động).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
stateDiagram-v2
    [*] --> ChoKhoiHanh: Tài xế mở màn hình Drive
    ChoKhoiHanh --> DangDiChuyen: Vận tốc v > 5 km/h trong 5 giây
    DangDiChuyen --> TamDungDoXe: Vận tốc v = 0 km/h kéo dài > 3 phút
    TamDungDoXe --> DangDiChuyen: Xe lăn bánh trở lại (v > 5 km/h)
    TamDungDoXe --> KetThucChuyenDi: Tài xế bấm nút "Kết thúc chuyến"
    DangDiChuyen --> KetThucChuyenDi: Tài xế bấm nút "Kết thúc chuyến"
    KetThucChuyenDi --> ManHinhTongKet: Chuyển sang trip-summary.tsx
    ManHinhTongKet --> [*]: Tính điểm an toàn & Lưu vào CSDL
```

---

## CHƯƠNG 7: KIỂM THỬ, THỰC NGHIỆM & HIỆU NĂNG

### 🖼️ Hình 7.1: Biểu đồ Đánh giá Độ chính xác 5 Tác vụ AI Cốt lõi
* **Tệp ảnh đã tạo:** `report_assets/fig_ai_benchmark_accuracy_clean.png`.
* **Mô tả:** Biểu đồ cột nhóm so sánh mAP@0.5, Precision, Recall cho 5 tác vụ AI: Phát hiện xe (94.2%), Biển báo QCVN (95.8%), Biển số xe OCR (91.5%), Giám sát ngủ gật (96.0%), Mũ bảo hiểm (93.8%). Các nhãn số nằm thoải mái phía trên cột, không bị che khuất.

---

### 🖼️ Hình 7.2: Biểu đồ Đo lường Độ trễ Suy luận Từng Module AI
* **Tệp ảnh đã tạo:** `report_assets/fig_module_latency_clean.png`.
* **Mô tả:** Biểu đồ thanh ngang thể hiện thời gian thực thi (ms) của từng module, tổng thời gian toàn bộ pipeline đạt 38ms, thỏa mãn tiêu chuẩn an toàn giao thông $< 50$ms.

---

### 🖼️ Hình 7.3: Ảnh Chụp Thực nghiệm Kết quả Nhận diện Cụm 3 Biển báo trên Cột
* **Tệp ảnh đã tạo:** `report_assets/fig_pole_slicing_clean.png`.
* **Mô tả chi tiết:** Minh họa kết quả nhận diện chính xác 3 biển báo trên cùng 1 cột trong ảnh camera hành trình thực tế: Biển cấm quay đầu và rẽ trái $P.124b$ (98%), Biển phụ thời gian $S.508$ từ 6h-22h (95%), và Biển cảnh báo đi chậm $W.245a$ (94%).

---

## CHƯƠNG 8: TRIỂN KHAI PRODUCTION & PHÁP LÝ

### 🖼️ Hình 8.1: Sơ đồ Luồng Khởi chạy Tự động hóa bằng Script 1-Chạm (`start_project.bat`)
* **Vị trí trong báo cáo:** Mục 8.1 (Quy trình đóng gói và triển khai).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart TD
    User["Người dùng Kích đúp tệp:\nstart_project.bat"] --> Split{"Script tự động tách\n2 Luồng Tiến trình"}
    
    Split -->|"Cửa sổ CMD 1"| B1["Kích hoạt môi trường ảo Python:\n.\\venv\\Scripts\\python.exe"]
    B1 --> B2["Khởi chạy Máy chủ Uvicorn FastAPI:\nuvicorn backend.app.main:app --port 8000"]
    B2 --> B3["Máy chủ API & AI sẵn sàng tại:\nhttp://localhost:8000 (Swagger: /docs)"]
    
    Split -->|"Cửa sổ CMD 2"| F1["Di chuyển vào thư mục web-app:\ncd web-app"]
    F1 --> F2["Khởi chạy Máy chủ Next.js 14:\nnpm run dev (Port 3000)"]
    F2 --> F3["Giao diện Web sẵn sàng tại:\nhttp://localhost:3000"]

    B3 & F3 --> Ready["HỆ THỐNG TRAFFICGUARD HOẠT ĐỘNG HOÀN TOÀN\n(Đồng bộ dữ liệu thời gian thực qua WebSocket)"]

    style User fill:#FEF3C7,stroke:#D97706,stroke-width:2px;
    style B3 fill:#EFF6FF,stroke:#2563EB;
    style F3 fill:#ECFDF5,stroke:#059669;
    style Ready fill:#FAF5FF,stroke:#8B5CF6,stroke-width:2px;
```

---

### 🖼️ Hình 8.2: Sơ đồ Cấu trúc Cây Thư mục Dự án Sau khi Dọn dẹp Sạch Chuẩn Công nghiệp
* **Vị trí trong báo cáo:** Mục 8.2 (Chiến lược dọn dẹp Clean Architecture).
* **Mã nguồn vẽ trên draw.io / Mermaid:**
```mermaid
flowchart TD
    Root["d:\\Smart Driving Assistant (Thư mục Gốc)"]
    
    Root --> BE["backend/\n• app/ (api, core, crud, models_db, schemas, services)\n• tests/ (Kiểm thử API & WebSocket)"]
    Root --> AI["ai_engine/\n• modules/ (12 Modules AI độc lập)\n• models/ (Checkpoints YOLO & MediaPipe)\n• plate/ (Nhận diện biển số xe VN)"]
    Root --> WEB["web-app/\n• src/app/ (9 Trang Dashboard Next.js 14)\n• src/components/ (Dual Camera Canvas, Alert Bar)\n• src/hooks/ (WebSocket driving streams)"]
    Root --> MOB["mobile-app/\n• app/ (Màn hình HUD drive.tsx & trip-summary)\n• lib/ (Còi báo động & State machine)"]
    Root --> BAT["start_project.bat (Launcher 1-chạm)"]
    Root --> TESTS["tests/\n• unit/ (Kiểm thử tự động PyTest 90/90)\n• verify_*.py (Bộ kiểm thử hồi quy nghiệp vụ)"]

    style Root fill:#F8FAFC,stroke:#334155,stroke-width:2px;
    style BE fill:#EFF6FF,stroke:#3B82F6;
    style AI fill:#ECFDF5,stroke:#10B981;
    style WEB fill:#FFFBEB,stroke:#F59E0B;
    style MOB fill:#FAF5FF,stroke:#8B5CF6;
```

---

# 📌 TÓM TẮT HƯỚNG DẪN SỬ DỤNG CHO BÁO CÁO 90 TRANG

1. **Cách vẽ sơ đồ Diagram trong 10 giây:**
   - Truy cập [https://app.diagrams.net/](https://app.diagrams.net/).
   - Chọn menu: `Arrange` $\rightarrow$ `Insert` $\rightarrow$ `Advanced` $\rightarrow$ `Mermaid`.
   - Dán toàn bộ khối mã code Mermaid tương ứng ở trên vào và bấm **Insert**.
   - Sơ đồ sẽ được vẽ tự động với các khối màu sắc hài hòa, đường nét vuông vức, không bao giờ bị đè chữ. Sau đó bạn chọn `File -> Export as -> PNG (hoặc SVG)` để chèn vào báo cáo.
2. **Cách chèn các biểu đồ số liệu thực nghiệm:**
   - Toàn bộ 7 biểu đồ số liệu đã được tự động sinh sẵn với độ phân giải cao 300 DPI trong thư mục:
     `d:\Smart Driving Assistant\report_assets\`
   - Bạn chỉ cần chèn trực tiếp các tệp ảnh `.png` sạch sẽ này vào đúng các mục tương ứng trong báo cáo.
3. **Cách bố trí ảnh chụp màn hình chống che khuất:**
   - Giữ nguyên tỷ lệ 16:9 của khung video camera.
   - Luôn đặt bảng số liệu (Telemetry) cố định ở thanh đáy hoặc thanh đỉnh của khung hình, không để trôi nổi vào giữa làn đường hoặc tâm xe.
