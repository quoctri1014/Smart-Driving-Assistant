from docx.shared import Inches
from report_builder import (
    add_chapter_heading, add_section_heading, add_subsection_heading,
    add_paragraph, add_bullet_point, add_callout_box, add_formula_box,
    add_custom_table, add_image_figure
)

def build_chapter_3(doc):
    add_chapter_heading(doc, 3, "Phân tích yêu cầu & Thiết kế kiến trúc hệ thống")
    
    add_section_heading(doc, "3.1", "Phân tích yêu cầu hệ thống")
    add_subsection_heading(doc, "3.1.1", "Yêu cầu chức năng (Functional Requirements)")
    add_bullet_point(doc, "Tự động nhận diện và phân loại phương tiện (ô tô, xe máy, xe buýt, xe tải), bám vết liên tục và ước tính vận tốc tức thời theo km/h.", "F1 - Nhận diện & Bám vết: ");
    add_bullet_point(doc, "Tính toán cự ly an toàn theo tốc độ và thời tiết (Thông tư 31/2019/TT-BGTVT); tính chỉ số TTC và phát cảnh báo va chạm sớm.", "F2 - Khoảng cách & Va chạm: ");
    add_bullet_point(doc, "Nhận diện biển báo giao thông Việt Nam theo QCVN 41:2019 (biển cấm, biển cảnh báo, biển hiệu lệnh) và bóc tách biển phụ thời gian S.508.", "F3 - Biển báo QCVN 41: ");
    add_bullet_point(doc, "Tự động phát hiện vị trí biển số xe và nhận dạng ký tự (OCR) biển số phương tiện vi phạm quy tắc an toàn.", "F4 - Biển số xe OCR: ");
    add_bullet_point(doc, "Phát hiện người điều khiển xe máy không đội mũ bảo hiểm với thuật toán khử trùng lặp cảnh báo theo Tracker ID.", "F5 - Mũ bảo hiểm: ");
    add_bullet_point(doc, "Giám sát trạng thái tài xế qua camera cabin: phát hiện ngủ gật (EAR/PERCLOS 60s), ngáp ngủ (MAR), nhắm mắt quá 1.5s, quên thắt dây an toàn và lái xe liên tục quá 4 giờ.", "F6 - Giám sát Cabin DMS: ");
    add_bullet_point(doc, "Chụp ảnh trích xuất bằng chứng vi phạm, mã hóa chữ ký số SHA-256 chống làm giả và lưu trữ an toàn.", "F7 - Hồ sơ bằng chứng: ");
    add_bullet_point(doc, "Quản trị phân quyền đa cấp RBAC (Quản trị viên, Điều độ viên, Tài xế); quản lý đội xe, hồ sơ tài xế và chấm điểm an toàn (Safety Score).", "F8 - Quản trị doanh nghiệp: ");

    add_subsection_heading(doc, "3.1.2", "Yêu cầu phi chức năng (Non-Functional Requirements)")
    add_bullet_point(doc, "Độ trễ toàn trình từ lúc camera thu nhận khung hình đến khi hiển thị cảnh báo lên màn hình người dùng không vượt quá 50ms (thực tế đo đạc: 38ms). Tốc độ xử lý đạt tối thiểu 25 FPS.", "N1 - Hiệu năng & Độ trễ: ");
    add_bullet_point(doc, "Hệ thống có cơ chế tự động điều tiết tải (Load Shedding), tự động bỏ bớt khung hình khi CPU/GPU quá tải để duy trì tính thời gian thực.", "N2 - Tính sẵn sàng & Ổn định: ");
    add_bullet_point(doc, "Mã hóa mật khẩu bằng thuật toán Bcrypt với Salt ngẫu nhiên, xác thực phiên qua JWT; tuân thủ Nghị định 13/2023/NĐ-CP về làm mờ khuôn mặt người đi bộ bên ngoài xe.", "N3 - Bảo mật & Riêng tư: ");

    add_section_heading(doc, "3.2", "Mô hình ca sử dụng (Use-Case) và Cơ chế phân quyền RBAC")
    add_paragraph(doc,
        "Hệ thống phân cấp người dùng thành 3 vai trò (Roles) với phạm vi nghiệp vụ được cô lập hoàn toàn:")
    add_bullet_point(doc, "Ban giám đốc, Trưởng phòng vận tải: Toàn quyền cấu hình tham số AI, quản lý danh mục xe, tài xế, xem báo cáo tổng thể toàn doanh nghiệp.", "1. Quản trị viên (Enterprise Admin): ");
    add_bullet_point(doc, "Nhân viên trực trung tâm điều hành: Giám sát luồng Live CCTV, tiếp nhận cảnh báo khẩn cấp, đối soát và phê duyệt hồ sơ vi phạm.", "2. Điều hành viên (Fleet Dispatcher): ");
    add_bullet_point(doc, "Người trực tiếp điều khiển xe: Sử dụng chế độ HUD cảnh báo trên xe, nghe giọng nói trợ lý và xem điểm an toàn cá nhân.", "3. Tài xế doanh nghiệp (Fleet Driver): ");

    headers_3_1 = ["Chức năng / Quyền hạn hệ thống", "Admin Doanh nghiệp", "Điều hành viên", "Tài xế lái xe"]
    data_3_1 = [
        ["Xem Dashboard Tổng quan", "Toàn đội xe", "Toàn đội xe", "Chỉ số cá nhân"],
        ["Giám sát Live Camera AI (Dual Stream)", "Toàn quyền", "Toàn quyền", "Chỉ xem xe mình lái"],
        ["Tải video demo phân tích (.mp4)", "Có", "Có", "Có"],
        ["Thêm / Chỉnh sửa / Xóa xe & Thiết bị", "Có", "Không có quyền", "Không có quyền"],
        ["Thêm / Phân quyền tài xế", "Có", "Không có quyền", "Không có quyền"],
        ["Duyệt / Bác bỏ hồ sơ vi phạm", "Có", "Có", "Không có quyền"],
        ["Xem ảnh bằng chứng & Tải biên bản", "Toàn bộ", "Toàn bộ", "Chỉ xem của bản thân"],
        ["Xuất báo cáo phân tích số liệu", "Có", "Có", "Không có quyền"],
        ["Cấu hình tham số ngưỡng AI & Còi", "Có", "Không có quyền", "Điều chỉnh âm lượng"]
    ]
    widths_3_1 = [Inches(2.5), Inches(1.3), Inches(1.4), Inches(1.3)]
    add_custom_table(doc, headers_3_1, data_3_1, widths_3_1, "Bảng 3.1: Ma trận phân quyền kiểm soát truy cập (RBAC Matrix)")

    add_section_heading(doc, "3.3", "Thiết kế kiến trúc tổng thể 4 tầng (System Architecture)")
    add_paragraph(doc,
        "Hệ thống TrafficGuard được thiết kế theo mô hình kiến trúc phân tầng (Layered Architecture) chuẩn doanh nghiệp gồm 4 tầng độc lập:")
    
    add_image_figure(doc, "report_assets/fig_system_architecture.png", "Hình 3.1: Sơ đồ kiến trúc tổng thể 4 tầng của nền tảng TrafficGuard", 6.2)

    add_paragraph(doc,
        "Chi tiết chức năng của 4 tầng kiến trúc:")
    add_bullet_point(doc, "Tiếp nhận luồng video RTSP/HTTP từ camera hành trình góc rộng (Road Camera), camera góc hẹp trong cabin (Cabin DMS) hoặc tải file video MP4 trực tiếp trên trình duyệt.", "Tầng 1 - Thiết bị & Thu thập dữ liệu: ");
    add_bullet_point(doc, "Tập hợp 12 module AI Deep Learning xử lý song song, có bộ điều phối tải Load Shedder và bộ lọc nhiễu Decision Engine.", "Tầng 2 - Lõi xử lý Trí tuệ Nhân tạo: ");
    add_bullet_point(doc, "Máy chủ FastAPI điều phối luồng dữ liệu, xác thực JWT, tương tác với 15 bảng trong CSDL SQLite/PostgreSQL qua SQLAlchemy ORM và lưu trữ tệp bằng chứng tại /storage/.", "Tầng 3 - Máy chủ Backend & Dữ liệu: ");
    add_bullet_point(doc, "Giao diện Web Next.js 14 hiển thị Canvas 60 FPS, âm thanh báo động và Mobile App Expo HUD dành cho tài xế.", "Tầng 4 - Giao diện Người dùng: ");

    add_section_heading(doc, "3.4", "Thiết kế cơ sở dữ liệu quan hệ (ERD & Database Schema)")
    add_paragraph(doc,
        "Cơ sở dữ liệu của hệ thống được thiết kế chuẩn hóa mức 3NF với 15 bảng dữ liệu liên kết chặt chẽ (định nghĩa tại backend/app/models_db/):")
    
    headers_3_2 = ["Tên bảng trong CSDL", "Khóa chính", "Các khóa ngoại (Foreign Keys)", "Mô tả nghiệp vụ lưu trữ"]
    data_3_2 = [
        ["organizations", "id (Integer)", "None", "Lưu thông tin doanh nghiệp vận tải, tên công ty, gói dịch vụ"],
        ["organization_structures", "id (Integer)", "organization_id", "Phòng ban, chi nhánh và cơ cấu đội xe trực thuộc"],
        ["users", "id (Integer)", "organization_id", "Tài khoản người dùng, email, mật khẩu băm Bcrypt, vai trò (role)"],
        ["drivers", "id (Integer)", "user_id, organization_id", "Hồ sơ tài xế, số GPLX, thâm niên, điểm an toàn tích lũy"],
        ["vehicles", "id (Integer)", "organization_id, driver_id", "Phương tiện vận tải, biển số đăng ký, loại xe, mã thiết bị camera"],
        ["driving_sessions", "id (Integer)", "vehicle_id, driver_id", "Phiên hành trình, thời gian bắt đầu/kết thúc, số km, trạng thái"],
        ["violations", "id (Integer)", "session_id, vehicle_id", "Nhật ký vi phạm: loại lỗi, vận tốc vi phạm, đường dẫn ảnh, SHA-256"],
        ["violation_reviews", "id (Integer)", "violation_id, reviewer_id", "Trạng thái duyệt biên bản (Pending, Approved, Rejected) và lý do"],
        ["trip_events", "id (Integer)", "session_id", "Chuỗi sự kiện telemetry diễn ra trong chuyến đi (phanh gấp, chệch làn)"],
        ["coaching_records", "id (Integer)", "driver_id, violation_id", "Hồ sơ đào tạo, nhắc nhở tài xế cải thiện kỹ năng lái an toàn"],
        ["device_health", "id (Integer)", "vehicle_id", "Theo dõi trạng thái phần cứng camera, FPS, nhiệt độ và nhịp tim IoT"],
        ["audit_logs", "id (Integer)", "user_id", "Nhật ký kiểm toán hệ thống ghi lại mọi hành động thay đổi dữ liệu"],
        ["ai_configs", "id (Integer)", "organization_id", "Lưu trữ tham số cấu hình ngưỡng AI riêng của từng doanh nghiệp"],
        ["notifications", "id (Integer)", "user_id", "Thông báo cảnh báo gửi đến hộp thư điều hành viên và tài xế"]
    ]
    widths_3_2 = [Inches(1.8), Inches(1.1), Inches(1.6), Inches(2.2)]
    add_custom_table(doc, headers_3_2, data_3_2, widths_3_2, "Bảng 3.2: Danh mục 14 bảng dữ liệu cốt lõi trong cơ sở dữ liệu hệ thống")

def build_chapter_4(doc):
    add_chapter_heading(doc, 4, "Thiết kế & Hiện thực hóa 12 Module Trí tuệ Nhân tạo (AI Pipeline)")
    
    add_section_heading(doc, "4.1", "Kiến trúc tổng thể Pipeline xử lý AI thời gian thực")
    add_paragraph(doc,
        "Lõi Trí tuệ Nhân tạo (AI Core Pipeline) là trái tim của hệ thống TrafficGuard. Toàn bộ các thuật toán được cấu trúc dạng module độc lập (nằm trong thư mục ai_engine/modules/), giao tiếp qua cấu trúc dữ liệu gói tin tiêu chuẩn và được điều phối bằng luồng đa nhiệm.")
    add_paragraph(doc,
        "Để đảm bảo tốc độ đáp ứng thời gian thực < 50ms, hệ thống trang bị hai cơ chế bảo vệ tiền xử lý:")
    add_bullet_point(doc, "Module load_shedder.py: Liên tục đo đạc thời gian trễ của hàng đợi xử lý. Khi độ trễ vượt quá ngưỡng an toàn (ví dụ: > 45ms), module sẽ tự động kích hoạt chế độ cắt giảm tải: chỉ chạy các tác vụ nguy cấp (Phát hiện xe va chạm, Buồn ngủ) và tạm thời bỏ qua các tác vụ phụ (Đếm lưu lượng làn đường, OCR biển số xe không vi phạm).", "1. Bộ điều tiết tải động (Load Shedder): ");
    add_bullet_point(doc, "Module image_quality_gate.py: Đánh giá chất lượng khung hình đầu vào qua phương sai toán tử Laplacian (Var_Laplacian < 100 báo hiệu ảnh bị mờ rung lắc) và phân tích độ sáng Histogram (để nhận diện lóa đèn ban đêm hoặc quá tối).", "2. Cổng kiểm định chất lượng ảnh (Quality Gate): ");

    add_section_heading(doc, "4.2", "Nhóm Module Thị giác Mặt đường (Road Vision Modules)")
    
    add_subsection_heading(doc, "4.2.1", "Module Phát hiện và Phân loại Phương tiện (vehicle_detector.py)")
    add_paragraph(doc,
        "Sử dụng mô hình YOLOv8 Nano tối ưu hóa cấu trúc trọng số. Mô hình nhận diện 4 lớp đối tượng phương tiện chính: car (ô tô con), motorcycle (xe máy), bus (xe buýt), và truck (xe tải).")
    add_paragraph(doc,
        "Khu vực quan tâm (Region of Interest - ROI) được áp dụng để loại bỏ 30% nửa trên khung hình (khu vực bầu trời và nhà cao tầng), giúp giảm 28% khối lượng tính toán và tránh các báo động giả từ các vật thể không nằm trên mặt đường.")

    add_subsection_heading(doc, "4.2.2", "Module Bám vết Đa đối tượng (multi_object_tracker.py)")
    add_paragraph(doc,
        "Phương tiện sau khi được phát hiện sẽ được cấp một Tracker ID duy nhất để theo dõi hành trình di chuyển liên tục giữa các khung hình liên tiếp.")
    add_paragraph(doc,
        "Thuật toán kết hợp giữa tính toán chỉ số giao diện tích (IoU) và ma trận liên kết Hungarian. Khi một phương tiện bị che khuất tạm thời (Occlusion) trong 3-5 khung hình (ví dụ: bị xe buýt che lấp một phần), Tracker vẫn bảo lưu quỹ đạo để không cấp trùng lặp ID mới khi phương tiện xuất hiện trở lại.")

    add_subsection_heading(doc, "4.2.3", "Module Ước tính Vận tốc Phương tiện (speed_estimator.py)")
    add_paragraph(doc,
        "Vận tốc của từng phương tiện xung quanh được tính toán dựa trên độ dịch chuyển thực tế tính bằng mét trên mặt đường qua ma trận Homography:")
    add_formula_box(doc,
        "v = ( √[ (X_t - X_{t-1})² + (Y_t - Y_{t-1})² ] / Δt ) * 3.6  (km/h)",
        "4.1",
        "Trong đó (X, Y) là tọa độ vật lý tại chân tiếp xúc bánh xe, Δt là khoảng thời gian trôi qua giữa hai khung hình (giây)."
    )
    add_paragraph(doc,
        "Hệ thống áp dụng bộ lọc trung bình trượt cửa sổ n = 5 khung hình để triệt tiêu các dao động nhiễu do rung lắc camera hành trình khi xe đi qua gờ giảm tốc.")

    add_subsection_heading(doc, "4.2.4", "Module Quản lý Làn đường & Cảnh báo Chệch làn (lane_detector.py, zone_manager.py)")
    add_paragraph(doc,
        "Phát hiện các vạch kẻ phân làn (vạch trắng, vạch vàng, vạch đứt và vạch liền) bằng cách kết hợp bộ lọc cạnh Canny và biến đổi Hough Lines Transform.")
    add_paragraph(doc,
        "Chức năng Cảnh báo Chệch làn đường (LDWS): Theo dõi vị trí tâm mũi xe so với hai vạch phân làn. Khi tâm xe lệch quá 30cm về một phía mà không có tín hiệu chuyển làn, hệ thống sẽ kích hoạt cảnh báo nhắc nhở tài xế.")

    add_subsection_heading(doc, "4.2.5", "Module Nhận diện Biển số xe Việt Nam (plate_recognizer.py)")
    add_paragraph(doc,
        "Được huấn luyện chuyên biệt trên tập dữ liệu biển số xe cơ giới Việt Nam:")
    add_bullet_point(doc, "Mô hình YOLOv11 phát hiện chính xác vị trí khung biển số (cả dạng biển vuông 2 dòng và biển dài 1 dòng).", "Giai đoạn 1 (Detection): ");
    add_bullet_point(doc, "Sử dụng phép biến đổi hình học (cv2.getPerspectiveTransform) để xoay nắn thẳng khung biển số bị nghiêng góc và khử nhiễu sáng.", "Giai đoạn 2 (Rectification): ");
    add_bullet_point(doc, "Áp dụng EasyOCR với từ điển ký tự tùy chỉnh tiếng Việt; lọc bỏ dấu chấm và ghép chuẩn theo mẫu: [Mã tỉnh][Ký hiệu]-[Số thứ tự] (Ví dụ: 51H-982.45).", "Giai đoạn 3 (Recognition & Regex): ");

    add_subsection_heading(doc, "4.2.6", "Module Kiểm tra Mũ bảo hiểm (helmet_checker.py)")
    add_paragraph(doc,
        "Khi phát hiện đối tượng là xe máy (motorcycle), module sẽ tự động cắt vùng đầu người lái (Head ROI) dựa trên tỷ lệ giải phẫu học cơ thể người.")
    add_paragraph(doc,
        "Cơ chế khử trùng lặp cảnh báo (Deduplication): Hệ thống duy trì một bảng trạng thái vi phạm theo Tracker ID. Khi một người đi xe máy không đội mũ bảo hiểm bị phát hiện, hệ thống chỉ kích hoạt ghi nhận vi phạm một lần duy nhất trong suốt thời gian phương tiện đó nằm trong tầm quan sát của camera, ngăn ngừa tình trạng spam hàng chục biên bản vi phạm cho cùng một đối tượng.")

    add_section_heading(doc, "4.3", "Nhóm Module An toàn & Cảnh báo Sớm (Safety & Decision Modules)")
    
    add_subsection_heading(doc, "4.3.1", "Module Tính Khoảng cách An toàn theo Luật Việt Nam (safe_distance_calculator.py)")
    add_paragraph(doc,
        "Hiện thực hóa nghiêm ngặt Điều 11 Thông tư số 31/2019/TT-BGTVT ngày 29/08/2019 của Bộ Giao thông Vận tải:")
    
    headers_4_1 = ["Dải vận tốc xe chạy (km/h)", "Cự ly an toàn đường khô (m)", "Cự ly khi trời mưa/trơn trượt (x1.30)", "Căn cứ pháp lý"]
    data_4_1 = [
        ["V <= 60 km/h", "Chủ động (Khuyến nghị >= 35m)", ">= 45.5 mét", "Khoản 2 Điều 11 TT 31/2019/TT-BGTVT"],
        ["60 < V <= 80 km/h", "Tối thiểu 55 mét", "Tối thiểu 71.5 mét", "Khoản 1 Điều 11 TT 31/2019/TT-BGTVT"],
        ["80 < V <= 100 km/h", "Tối thiểu 70 mét", "Tối thiểu 91.0 mét", "Khoản 1 Điều 11 TT 31/2019/TT-BGTVT"],
        ["100 < V <= 120 km/h", "Tối thiểu 100 mét", "Tối thiểu 130.0 mét", "Khoản 1 Điều 11 TT 31/2019/TT-BGTVT"]
    ]
    widths_4_1 = [Inches(1.8), Inches(1.8), Inches(1.8), Inches(1.6)]
    add_custom_table(doc, headers_4_1, data_4_1, widths_4_1, "Bảng 4.1: Bảng tra cứu khoảng cách an toàn tối thiểu theo luật Việt Nam")

    add_subsection_heading(doc, "4.3.2", "Module Cảnh báo Va chạm Sớm (collision_warning.py)")
    add_paragraph(doc,
        "Tính toán chỉ số thời gian va chạm tiềm ẩn (TTC) và phân cấp thành 3 mức độ cảnh báo:")
    add_bullet_point(doc, "TTC > 3.0s — Hiển thị màu xanh lá cây trên màn hình.", "Mức 1 (An toàn): ");
    add_bullet_point(doc, "2.0s < TTC <= 3.0s — Hiển thị màu vàng, phát âm thanh cảnh báo ngắn.", "Mức 2 (Chú ý - Warning): ");
    add_bullet_point(doc, "TTC <= 1.5s — Hiển thị màu đỏ nhấp nháy, phát còi báo động khẩn cấp và giọng nói: 'Nguy hiểm: Giữ khoảng cách an toàn!'.", "Mức 3 (Nguy cấp - Critical FCW): ");

    add_subsection_heading(doc, "4.3.3", "Module Nhận diện Biển báo QCVN 41:2019 & Biển phụ theo giờ (sign_detector.py)")
    add_paragraph(doc,
        "Quy trình nhận diện biển báo giao thông Việt Nam bao gồm hai giai đoạn phân cấp (Hierarchical Classification):")
    add_paragraph(doc,
        "Đặc biệt, hệ thống đã giải quyết thành công bài toán nhận diện cụm biển báo phức hợp trên cùng một cột bằng thuật toán cắt lát tỷ lệ cột (Pole Proportional Slicing):")
    add_bullet_point(doc, "Biển cấm chính phía trên (Ví dụ: P.124b cấm ô tô quay đầu và rẽ trái) được chuẩn hóa về kích thước 80x80 với phép nội suy INTER_CUBIC để đảm bảo phân loại bất biến tỷ lệ (Scale-Invariant), khắc phục lỗi nhận diện sai khi ở khoảng cách xa.", "Cắt lớp 1 (Biển chính): ");
    add_bullet_point(doc, "Phần biển phụ phía dưới (S.508) nằm trong tỷ lệ 0.45 đến 0.55 chiều cao biển chính được bóc tách và chuyển qua module OCR tiếng Việt để giải mã khung giờ cấm: '06:00 - 22:00'.", "Cắt lớp 2 (Biển phụ thời gian): ");
    add_bullet_point(doc, "Biển cảnh báo phụ đặt phía dưới cùng (như W.245a) tiếp tục được định danh chính xác.", "Cắt lớp 3 (Biển cảnh báo phụ): ");

    add_image_figure(doc, "report_assets/fig_qcvn_signs_sample.png", "Hình 4.1: Một số mẫu biển báo giao thông QCVN 41:2019/BGTVT trong cơ sở dữ liệu hệ thống", 6.2)

    add_subsection_heading(doc, "4.3.4", "Module Khuyến nghị Tốc độ An toàn (speed_recommendation.py)")
    add_paragraph(doc,
        "Động cơ phân tích luật chuyên gia (Rule-based Adaptive Engine) tự động tổng hợp dữ liệu từ: (1) Biển báo tốc độ tối đa cho phép trên tuyến đường; (2) Mật độ phương tiện phía trước; (3) Cự ly an toàn thực tế; để đưa ra vận tốc khuyến nghị tối ưu nhất hiển thị trên màn hình người lái.")

    add_section_heading(doc, "4.4", "Nhóm Module Giám sát Người lái trong Cabin (DMS Modules)")
    
    add_subsection_heading(doc, "4.4.1", "Module Giám sát Trạng thái Buồn ngủ & Mất tập trung (drowsiness_detector.py)")
    add_paragraph(doc,
        "Khai thác MediaPipe Face Landmarker với 468 điểm mốc 3D. Cơ chế hoạt động bao gồm:")
    add_bullet_point(doc, "Trong 15-30 giây đầu khi khởi hành, hệ thống ghi nhận giá trị mở mắt tự nhiên của tài xế để thiết lập ngưỡng EAR cá nhân hóa (người mắt một mí hoặc mắt sâu không bị báo động giả).", "1. Cân chỉnh động cá nhân (Dynamic Calibration): ");
    add_bullet_point(doc, "Khi phát hiện tài xế đeo kính râm che khuất mắt, hệ thống tự động chuyển sang chế độ Sunglasses Mode, hạ độ tin cậy EAR và chuyển trọng số sang ước lượng tư thế đầu 3D (Head Pose via cv2.solvePnP).", "2. Chế độ Kính râm (Sunglasses Mode): ");
    add_bullet_point(doc, "Gục đầu ngủ (Pitch < -25°), quay đầu mất tập trung sang hai bên (Yaw > 30° hoặc Yaw < -30°).", "3. Ước lượng tư thế đầu 3D: ");

    add_subsection_heading(doc, "4.4.2", "Module Giám sát Mắt nhắm Kéo dài (eyes_closed_monitor.py)")
    add_paragraph(doc,
        "Được thiết kế để ngăn chặn hiện tượng vi ngủ (Microsleep). Khi tài xế nhắm mắt liên tục vượt ngưỡng 1.5 đến 2.0 giây, hệ thống sẽ kích hoạt chuông báo thức tần số cao và còi hú khẩn cấp cho tới khi tài xế mở mắt trở lại.")

    add_subsection_heading(doc, "4.4.3", "Module Dây an toàn & Đếm giờ Lái xe (seatbelt_checker.py, driving_timer.py)")
    add_paragraph(doc,
        "Kiểm tra dây an toàn qua phân tích kết cấu và đường chéo vắt qua vai người lái. Module driving_timer.py theo dõi liên tục tổng thời gian xe chạy và phát cảnh báo nhắc nhở dừng xe nghỉ ngơi khi tài xế lái liên tục quá 4 giờ (theo Điều 65 Luật Giao thông đường bộ 2008).")

    add_subsection_heading(doc, "4.4.4", "Module Quản lý Lưu vết Vi phạm (violation_manager.py)")
    add_paragraph(doc,
        "Khi sự cố vi phạm xảy ra, module sẽ kích hoạt bộ đệm khung hình trượt (Rolling Buffer) để lưu 5 khung hình trước và 5 khung hình sau thời điểm vi phạm, đóng gói đầy đủ metadata (thời gian, tọa độ GPS, biển số, tốc độ) và chuyển về máy chủ lưu trữ.")
