  # 📑 TÀI LIỆU MÔ TẢ PHÂN QUYỀN, VAI TRÒ & TOÀN BỘ CHỨC NĂNG DỰ ÁN
  ## HỆ THỐNG GIÁM SÁT GIAO THÔNG & TRỢ LÝ LÁI XE AN TOÀN DOANH NGHIỆP
  ### (Smart Traffic AI & Fleet Safety Platform — TRAFFICGUARD)

  ---

  ## 📌 MỤC LỤC
  1. [Tổng Quan Hệ Thống](#1-tổng-quan-hệ-thống)
  2. [Cơ Cấu Phân Quyền & Vai Trò Người Dùng (RBAC)](#2-cơ-cấu-phân-quyền--vai-trò-người-dùng-rbac)
  3. [Bảng Ma Trận Phân Quyền (Permission Matrix)](#3-bảng-ma-trận-phân-quyền-permission-matrix)
  4. [Toàn Bộ 12 Module Trí Tuệ Nhân Tạo (AI Pipeline)](#4-toàn-bộ-12-module-trí-tuệ-nhân-tạo-ai-pipeline)
  5. [Chi Tiết Chức Năng Phân Hệ Web Dashboard](#5-chi-tiết-chức-năng-phân-hệ-web-dashboard)
  6. [Chi Tiết Chức Năng Phân Hệ Mobile App](#6-chi-tiết-chức-năng-phân-hệ-mobile-app)
  7. [Kiến Trúc Dữ Liệu & Cơ Chế Lưu Trữ Thực Tế](#7-kiến-trúc-dữ-liệu--cơ-chế-lưu-trữ-thực-tế)

  ---

  ## 1. TỔNG QUAN HỆ THỐNG

  Hệ thống **Smart Driving Assistant** là giải pháp phần mềm cấp doanh nghiệp tích hợp trí tuệ nhân tạo (Computer Vision & Deep Learning) nhằm:
  * **Giám sát an toàn giao thông thời gian thực** (Real-time ADAS).
  * **Quản lý hành trình, đội xe và tài xế** cho các doanh nghiệp vận tải, logistic và tổ chức điều hành giao thông.
  * **Tự động trích xuất bằng chứng vi phạm** (vượt tốc độ, không đội mũ bảo hiểm, buồn ngủ, chưa thắt dây an toàn, không giữ khoảng cách).

  ---

  ## 2. CƠ CẤU PHÂN QUYỀN & VAI TRÒ NGƯỜI DÙNG (RBAC)

  Hệ thống phân cấp người dùng thành **3 vai trò chính** với phạm vi quyền hạn và nghiệp vụ rõ ràng:

  ```
                    ┌────────────────────────────────────────┐
                    │ 👑 QUẢN TRỊ VIÊN (Enterprise Admin)    │
                    │   Toàn quyền hệ thống & cấu hình       │
                    └───────────────────┬────────────────────┘
                                        │
                ┌───────────────────────┴───────────────────────┐
                ▼                                               ▼
  ┌───────────────────────────┐                   ┌───────────────────────────┐
  │ 📡 ĐIỀU HÀNH VIÊN         │                   │ 🚗 TÀI XẾ DOANH NGHIỆP    │
  │ (Fleet Dispatcher)        │                   │ (Fleet Driver)            │
  │ Giám sát luồng xe & sự cố │                   │ Trợ lý lái xe & HUD xe cá │
  └───────────────────────────┘                   └───────────────────────────┘
  ```

  ---

  ### 👑 VAI TRÒ 1: QUẢN TRỊ VIÊN DOANH NGHIỆP (ENTERPRISE ADMIN)
  * **Đối tượng:** Ban giám đốc, Trưởng phòng quản lý phương tiện, Quản trị viên CNTT.
  * **Mục tiêu:** Quản trị toàn bộ tổ chức, phân bổ tài nguyên, cấu hình đội xe và xuất báo cáo.
  * **Quyền hạn chi tiết:**
    1. **Quản lý nhân sự & tài xế:** Thêm, kích hoạt tài khoản tài xế / điều hành viên mới vào hệ thống.
    2. **Quản lý đội xe:** Đăng ký biển số xe mới, gán thiết bị camera cho từng phương tiện (ô tô, xe tải, xe khách).
    3. **Xem toàn bộ dữ liệu:** Truy cập dữ liệu vi phạm, hành trình, chỉ số an toàn của tất cả các xe trong doanh nghiệp.
    4. **Cấu hình tham số AI:** Thay đổi ngưỡng cảnh báo tốc độ, độ nhạy phát hiện buồn ngủ, cự ly khoảng cách an toàn.
    5. **Báo cáo tài chính & vận hành:** Xuất báo cáo tổng kết tỷ lệ tuân thủ an toàn giao thông.

  ---

  ### 📡 VAI TRÒ 2: ĐIỀU HÀNH VIÊN GIÁM SÁT (FLEET DISPATCHER / SAFETY MANAGER)
  * **Đối tượng:** Nhân viên điều hành trung tâm giám sát camera, nhân viên an toàn đội xe.
  * **Mục tiêu:** Trực phòng giám sát, theo dõi luồng camera trực tuyến, xử lý cảnh báo khẩn cấp.
  * **Quyền hạn chi tiết:**
    1. **Giám sát trực tuyến:** Mở luồng camera đường lộ (Road Camera) và cabin tài xế (DMS) của các xe đang chạy.
    2. **Kiểm tra vi phạm:** Xem danh sách vi phạm phát sinh tức thì, đối soát hình ảnh bằng chứng (biển số, mũ bảo hiểm, buồn ngủ).
    3. **Tra cứu lịch sử:** Tra cứu nhật ký hành trình theo biển số xe hoặc tên tài xế.
    4. **Theo dõi trạng thái AI:** Giám sát độ trễ, FPS và trạng thái hoạt động của 12 module AI.

  ---

  ### 🚗 VAI TRÒ 3: TÀI XẾ DOANH NGHIỆP (FLEET DRIVER)
  * **Đối tượng:** Tài xế trực tiếp điều khiển phương tiện trên đường.
  * **Mục tiêu:** Nhận cảnh báo nguy hiểm thời gian thực trên xe để phòng tránh tai nạn và lái xe an toàn.
  * **Quyền hạn chi tiết:**
    1. **Chế độ Lái xe HUD (Camera Stream):** Sử dụng camera điện thoại làm camera hành trình quét đường phía trước.
    2. **Nhận cảnh báo thời gian thực:**
      * Cảnh báo khoảng cách an toàn và nguy cơ va chạm sớm (TTC).
      * Cảnh báo phát hiện buồn ngủ / ngáp nhiều lần.
      * Cảnh báo quên thắt dây an toàn.
      * Khuyến nghị tốc độ giới hạn theo biển báo giao thông.
    3. **Xem điểm an toàn cá nhân:** Xem điểm Safety Score, tổng km đã chạy, số giờ lái xe liên tục.
    4. **Lịch sử cá nhân:** Xem lại lịch sử các chuyến đi và các cảnh báo vi phạm của riêng mình.

  ---

  ## 3. BẢNG MA TRẬN PHÂN QUYỀN (PERMISSION MATRIX)

  | Chức năng / Quyền hạn | 👑 Quản Trị Viên (Admin) | 📡 Điều Hành Viên (Dispatcher) | 🚗 Tài Xế (Driver) |
  |---|:---:|:---:|:---:|
  | **Xem Dashboard Tổng quan** | Toàn đội xe | Toàn đội xe | Cá nhân |
  | **Giám sát Live Camera AI** | Toàn quyền | Toàn quyền | Xem luồng xe mình lái |
  | **Tải Video Demo (.mp4)** | Có | Có | Có |
  | **Đăng ký / Thêm xe mới** | Có | Không | Không |
  | **Thêm / Tạo tài khoản tài xế** | Có | Không | Không |
  | **Xem toàn bộ hồ sơ vi phạm** | Tất cả xe | Tất cả xe | Chỉ xem vi phạm của mình |
  | **Xem ảnh bằng chứng vi phạm** | Có | Có | Có |
  | **Xem báo cáo & phân tích số liệu** | Toàn doanh nghiệp | Toàn doanh nghiệp | Không |
  | **Xem chẩn đoán 12 Module AI** | Có | Có | Rút gọn |
  | **Bật / Tắt giám sát buồn ngủ DMS** | Có | Có | Có |

  ---

  ## 4. TOÀN BỘ 12 MODULE TRÍ TUỆ NHÂN TẠO (AI PIPELINE)

  Hệ thống được xây dựng trên nền tảng 12 thuật toán AI phối hợp liên tục:

  | # | Tên Module AI | Thuật toán / Mô hình | Chức năng chi tiết |
  |---|---|---|---|
  | **1** | **Vehicle Detector** | YOLOv8 Nano | Phát hiện tức thì các phương tiện: ô tô con, xe máy, xe buýt, xe tải trong khung hình. |
  | **2** | **Multi-Object Tracker** | SimpleTracker / IOU Tracking | Gán ID bám vết duy nhất cho từng phương tiện, theo dõi quỹ đạo di chuyển liên tục. |
  | **3** | **Speed Estimator** | Pixel-to-Meter Homography | Ước tính vận tốc thực tế của từng xe (km/h) dựa trên độ dịch chuyển pixel giữa các frame. |
  | **4** | **Zone Traffic Manager** | Polygon Intersection | Chia khung hình thành các làn đường/vùng và đếm lưu lượng xe theo từng làn. |
  | **5** | **License Plate OCR** | YOLO + EasyOCR | Tự động phát hiện vị trí biển số xe và đọc chữ/số biển số xe vi phạm. |
  | **6** | **Helmet Checker** | Head-Crop Classification | Kiểm tra người đi xe máy có đội mũ bảo hiểm hay không, gắn vết theo từng xe. |
  | **7** | **Collision Warning** | Time-To-Collision (TTC) | Tính toán thời gian va chạm tiềm ẩn; phát cảnh báo sớm khi xe trước giảm tốc đột ngột. |
  | **8** | **Safe Distance Calculator** | Công thức Luật GTVT VN | Tính khoảng cách an toàn tối thiểu theo tốc độ thực tế (Thông tư 31/2019/TT-BGTVT). |
  | **9** | **Traffic Sign Detector** | Sign Pattern Recognition | Đọc các biển báo giao thông trên đường (tốc độ giới hạn, cấm vượt, khu dân cư). |
  | **10**| **Speed Recommendation** | Rule-Based Adaptive AI | Gợi ý tốc độ lái xe an toàn nhất dựa trên biển báo, mật độ đường và cự ly xe trước. |
  | **11**| **Drowsiness Monitor (DMS)**| MediaPipe Face Mesh (EAR/MAR)| Phân tích tỷ lệ nhắm mắt (EAR) và mở miệng ngáp (MAR) để báo động ngủ gật tức thì. |
  | **12**| **Seatbelt & Driving Timer**| Posture Check & Time Engine | Kiểm tra thắt dây an toàn qua vai và nhắc nhở nghỉ ngơi khi lái xe liên tục quá 4 giờ. |

  ---

  ## 5. CHI TIẾT CHỨC NĂNG PHÂN HỆ WEB DASHBOARD

  ### 1. Phân hệ Tổng Quan Điều Hành (`/dashboard`)
  * Bảng điều khiển trung tâm hiển thị: Chỉ số an toàn đội xe (Safety Score), Tổng số phiên hành trình, Tổng số vi phạm, Tổng giờ lái xe.
  * Danh sách cảnh báo vi phạm mới nhất và danh sách chuyến đi gần đây kết nối từ cơ sở dữ liệu thật.

  ### 2. Phân hệ Giám Sát Trực Tuyến (`/live`)
  * Hỗ trợ 2 chế độ nguồn phát: **Tải file Video (.mp4)** hoặc **Webcam máy tính**.
  * Luồng camera kép: Camera hành trình mặt đường (Road Camera) và Camera cabin tài xế (DMS).
  * Khung hiển thị CCTV Dashcam chuẩn 16:9 sắc nét, vẽ bounding box, biển số, tốc độ và khoảng cách an toàn theo thời gian thực.
  * Bảng Telemetry hiển thị mật độ xe, khoảng cách an toàn, tốc độ khuyến nghị và trạng thái tài xế.

  ### 3. Phân hệ Quản Lý Đội Xe & Thiết Bị (`/devices`)
  * Danh sách phương tiện đăng ký (Biển số xe, Loại xe: Ô tô con, Xe tải, Xe khách, Xe máy).
  * Danh sách tài xế & nhân sự trong doanh nghiệp (Họ tên, Email, Vai trò: Admin, Dispatcher, Driver).
  * Form đăng ký xe mới và thêm tài xế mới trực tiếp vào cơ sở dữ liệu.

  ### 4. Phân hệ Hồ Sơ Vi Phạm (`/violations`)
  * Danh mục toàn bộ các sự cố vi phạm được AI ghi nhận kèm thời gian, tài xế phụ trách và mức độ nghiêm trọng.
  * Bộ lọc nhanh theo loại lỗi: *Quá tốc độ, Khoảng cách an toàn, Buồn ngủ, Mũ bảo hiểm, Dây an toàn*.
  * Modal xem chi tiết **ảnh chụp bằng chứng trích xuất từ camera AI**.

  ### 5. Phân hệ Nhật Ký Hành Trình (`/journeys`)
  * Quản lý lịch sử toàn bộ các phiên lái xe: Mã phiên, Tài xế phụ trách, Thời điểm khởi hành, Thời lượng lái (phút), Trạng thái hoàn thành.

  ### 6. Phân hệ Báo Cáo & Phân Tích (`/analytics`)
  * Thống kê tỷ lệ tuân thủ an toàn giao thông toàn đội xe.
  * Biểu đồ phân bố cơ cấu các loại lỗi vi phạm trong toàn doanh nghiệp.

  ### 7. Phân hệ Chẩn Đoán 12 Module AI (`/ai-status`)
  * Bảng giám sát chi tiết tình trạng hoạt động, model sử dụng, FPS mục tiêu và độ trễ (latency ms) của toàn bộ 12 module AI.

  ---

  ## 6. CHI TIẾT CHỨC NĂNG PHÂN HỆ MOBILE APP

  Ứng dụng di động dành cho tài xế ngồi trên phương tiện:
  * **Màn hình Đăng nhập:** Giao diện tối giản, hỗ trợ đăng nhập tài khoản tài xế doanh nghiệp hoặc nút Demo 1-chạm.
  * **Màn hình Dashboard di động (`index.tsx`):** Hiển thị điểm an toàn cá nhân, số chuyến đi, tổng km, nút bắt đầu chuyến đi nhanh.
  * **Màn hình Trợ lý Lái xe HUD (`drive.tsx`):**
    * Tận dụng camera điện thoại làm mắt thần quét đường.
    * Đồng hồ tốc độ điện tử kích thước lớn.
    * Cảnh báo va chạm bằng âm thanh và đổi màu giao diện (Xanh: An toàn | Vàng: Chú ý | Đỏ: Nguy hiểm).
  * **Màn hình Tổng kết chuyến đi (`trip-summary.tsx`):** Tự động tính điểm sau khi kết thúc chuyến đi.
  * **Màn hình Lịch sử & Cài đặt (`history.tsx`, `profile.tsx`):** Xem lại các chuyến đi cá nhân và điều chỉnh độ nhạy cảnh báo.

  ---

  ## 7. KIẾN TRÚC DỮ LIỆU & CƠ CHẾ LƯU TRỮ THỰC TẾ

  1. **Cơ Sở Dữ Liệu Quan Hệ (PostgreSQL / SQLite):**
    * Quản lý dữ liệu người dùng (`drivers`), đội xe (`vehicles`), phiên lái (`driving_sessions`), nhật ký vi phạm (`violations`).
    * Cấu hình kết nối linh hoạt trong file `.env`.
  2. **Kho Lưu Trữ Bằng Chứng Ảnh (`storage/`):**
    * Tự động lưu trữ ảnh crop vi phạm độ phân giải cao tại thư mục `d:\Smart Driving Assistant\storage\`.
    * Chia sẻ công khai qua endpoint `http://localhost:8000/storage/...`.
  3. **Bảo Mật & Xác Thực (JWT & Bcrypt):**
    * Mật khẩu người dùng được băm mã hóa một chiều bằng thuật toán Bcrypt.
    * Phiên làm việc được bảo vệ bằng JSON Web Token (JWT) theo chuẩn OAuth2.

  ---

  *Tài liệu được biên soạn và cập nhật tự động đồng bộ theo mã nguồn dự án Smart Driving Assistant.*
