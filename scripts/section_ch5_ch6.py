from docx.shared import Inches
from report_builder import (
    add_chapter_heading, add_section_heading, add_subsection_heading,
    add_paragraph, add_bullet_point, add_callout_box, add_formula_box,
    add_custom_table, add_image_figure
)

def build_chapter_5(doc):
    add_chapter_heading(doc, 5, "Hiện thực hóa Máy chủ Backend & Cơ sở dữ liệu (FastAPI)")
    
    add_section_heading(doc, "5.1", "Cấu trúc dự án Backend & Quản lý vòng đời dịch vụ")
    add_paragraph(doc,
        "Hệ thống máy chủ được xây dựng trên nền tảng FastAPI (Python 3.11), tận dụng tối đa cơ chế bất đồng bộ Asynchronous I/O (ASGI Event Loop) giúp xử lý hàng nghìn kết nối đồng thời với mức tiêu hao tài nguyên bộ nhớ tối thiểu. Toàn bộ mã nguồn backend được tổ chức theo kiến trúc phân lớp sạch (Clean Architecture) trong thư mục backend/app/:")
    add_bullet_point(doc, "Tập trung toàn bộ 13 router nghiệp vụ phân tán theo domain chức năng.", "backend/app/api/: ");
    add_bullet_point(doc, "Cấu hình hệ thống, bảo mật mã hóa, kết nối cơ sở dữ liệu, bộ lọc nhiễu và bảo vệ riêng tư.", "backend/app/core/: ");
    add_bullet_point(doc, "Các hàm thao tác cơ sở dữ liệu trừu tượng hóa (Create, Read, Update, Delete) theo từng thực thể.", "backend/app/crud/: ");
    add_bullet_point(doc, "Định nghĩa cấu trúc 15 bảng cơ sở dữ liệu thông qua SQLAlchemy ORM Declarative Base.", "backend/app/models_db/: ");
    add_bullet_point(doc, "Định nghĩa lược đồ xác thực dữ liệu đầu vào/đầu ra với Pydantic v2 (Data Validation & Serialization).", "backend/app/schemas/: ");
    add_bullet_point(doc, "Các dịch vụ xử lý nền, điều phối luồng video, tạo giọng nói và tích hợp AI.", "backend/app/services/: ");

    add_section_heading(doc, "5.2", "Cơ chế Xác thực JWT & Phân quyền RBAC nâng cao")
    add_paragraph(doc,
        "Bảo mật và an toàn dữ liệu được đặt lên hàng đầu trong thiết kế của TrafficGuard:")
    add_bullet_point(doc, "Mật khẩu người dùng được băm một chiều với thuật toán Bcrypt và Salt ngẫu nhiên (backend/app/core/security.py).", "1. Mã hóa mật khẩu an toàn: ");
    add_bullet_point(doc, "Sau khi đăng nhập thành công qua endpoint /api/auth/login, máy chủ cấp Access Token chuẩn JSON Web Token (JWT) được ký số bằng khóa bí mật bí mật (HS256). Token chứa thông tin User ID, Organization ID và Danh sách Scopes quyền hạn.", "2. Chứng thực phiên bằng JWT: ");
    add_bullet_point(doc, "Khai thác cơ chế Dependency Injection của FastAPI để kiểm tra quyền hạn trước khi thực thi endpoint. Ví dụ: hàm require_role(['admin', 'dispatcher']) sẽ tự động từ chối yêu cầu (HTTP 403 Forbidden) nếu người dùng không đủ thẩm quyền.", "3. Phân quyền RBAC qua Dependency: ");

    add_section_heading(doc, "5.3", "Hiện thực hóa 13 Router và hơn 30 API Endpoints")
    add_paragraph(doc,
        "Hệ thống cung cấp giao diện lập trình ứng dụng RESTful đầy đủ để phục vụ cho cả Web Dashboard và Mobile App:")
    
    headers_5_1 = ["Tên Router (File)", "Tiền tố URL (Prefix)", "Phương thức HTTP", "Mô tả chức năng nghiệp vụ"]
    data_5_1 = [
        ["auth_routes.py", "/api/auth", "POST /login, GET /me", "Đăng nhập, xác thực danh tính, lấy thông tin phiên làm việc"],
        ["fleet_routes.py", "/api/fleet", "GET, POST, PUT /vehicles", "Quản lý danh sách phương tiện, phân bổ xe cho tài xế"],
        ["journey_routes.py", "/api/journeys", "GET, POST /start, /end", "Khởi tạo hành trình, kết thúc chuyến đi, lấy timeline sự kiện"],
        ["violation_routes.py", "/api/violations", "GET, POST, PUT /reviews", "Tiếp nhận vi phạm từ AI, lọc hồ sơ, duyệt/hủy biên bản vi phạm"],
        ["license_plate_routes.py", "/api/license-plates", "POST /recognize", "Tiếp nhận ảnh chụp và trả về kết quả đọc biển số xe"],
        ["helmet_routes.py", "/api/helmets", "POST /check", "Kiểm tra và lưu biên bản vi phạm không đội mũ bảo hiểm"],
        ["traffic_sign_routes.py", "/api/traffic-signs", "POST /detect", "Phân tích ảnh biển báo, trích xuất biển chính và biển phụ theo giờ"],
        ["traffic_density_routes.py", "/api/traffic-density", "GET /lanes", "Báo cáo mật độ xe và lưu lượng phương tiện theo làn"],
        ["coaching_routes.py", "/api/coaching", "GET, POST /records", "Quản lý hồ sơ đào tạo an toàn và chấm điểm hành vi tài xế"],
        ["report_routes.py", "/api/reports", "GET /summary, /export", "Xuất báo cáo tổng hợp tỷ lệ tuân thủ và vi phạm an toàn"],
        ["organization_routes.py", "/api/organizations", "GET, PUT /settings", "Quản lý thông tin doanh nghiệp và cơ cấu phòng ban đội xe"],
        ["session_routes.py", "/api/sessions", "GET /active", "Quản lý các phiên giám sát camera đang hoạt động"],
        ["system_routes.py", "/api/system", "GET /health, /metrics", "Kiểm tra sức khỏe hệ thống, đo FPS và mức sử dụng tài nguyên"]
    ]
    widths_5_1 = [Inches(1.8), Inches(1.4), Inches(1.6), Inches(2.2)]
    add_custom_table(doc, headers_5_1, data_5_1, widths_5_1, "Bảng 5.1: Danh mục 13 Router RESTful API cốt lõi của hệ thống Backend")

    add_section_heading(doc, "5.4", "Giao thức truyền thông thời gian thực WebSocket Streaming")
    add_paragraph(doc,
        "Bên cạnh giao thức RESTful cho các tác vụ quản trị, hệ thống thiết lập hai kênh WebSocket song công toàn phần (Full-Duplex): /ws/driving-stream (dành cho Road Camera) và /ws/driver-monitor (dành cho Cabin Camera).")
    add_paragraph(doc,
        "Quy trình xử lý khung hình trong vòng lặp bất đồng bộ WebSocket:")
    add_bullet_point(doc, "Trình duyệt hoặc điện thoại gửi chuỗi nhị phân (Binary JPEG) hoặc chuỗi Base64 của khung hình trực tiếp qua WebSocket.", "Bước 1 (Gửi khung hình): ");
    add_bullet_point(doc, "Máy chủ giải mã ảnh bằng OpenCV không chạm đĩa cứng (In-Memory Decoding), chuyển qua Pipeline 12 Module AI.", "Bước 2 (Xử lý AI In-Memory): ");
    add_bullet_point(doc, "Máy chủ đóng gói kết quả bao gồm danh sách Bounding Boxes, nhãn nhận diện, cự ly khoảng cách mét, vận tốc và cờ cảnh báo khẩn cấp vào gói tin JSON gửi ngược lại Client trong vòng 35-40ms.", "Bước 3 (Phản hồi tức thì): ");

    add_section_heading(doc, "5.5", "Động cơ Ra quyết định Cảnh báo & Tuân thủ Nghị định 13/2023/NĐ-CP")
    add_subsection_heading(doc, "5.5.1", "Động cơ ra quyết định cảnh báo (backend/app/core/decision_engine.py)")
    add_paragraph(doc,
        "Nhằm ngăn ngừa hiện tượng tài xế bị phân tâm do quá nhiều cảnh báo dồn dập (Alert Fatigue), Decision Engine áp dụng thuật toán hàng đợi ưu tiên 3 cấp:")
    add_bullet_point(doc, "Nguy cơ va chạm sớm (TTC <= 1.5s), Ngủ gật/nhắm mắt > 1.5s. Cảnh báo này chiếm quyền ưu tiên tuyệt đối, ngắt các thông báo khác để phát còi hú và giọng nói khẩn cấp.", "Mức 1 - CRITICAL (Khẩn cấp): ");
    add_bullet_point(doc, "Khoảng cách xe không an toàn, Quá tốc độ tối đa cho phép, Lệch làn đường.", "Mức 2 - WARNING (Cảnh báo): ");
    add_bullet_point(doc, "Nhắc thắt dây an toàn, Gợi ý tốc độ theo biển báo, Nhắc nghỉ ngơi sau 4 giờ.", "Mức 3 - INFO (Thông tin): ");
    add_paragraph(doc,
        "Bộ lọc chống dội (Debounce Filter): Ngăn chặn việc bắn nhiều cảnh báo giống nhau cho cùng một sự kiện trong khoảng thời gian Δt < 3 giây.")

    add_subsection_heading(doc, "5.5.2", "Bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP (privacy_anonymizer.py)")
    add_paragraph(doc,
        "Hệ thống tích hợp module bảo vệ quyền riêng tư tự động:")
    add_bullet_point(doc, "Khi ảnh bằng chứng vi phạm được trích xuất để lưu trữ hoặc xuất báo cáo, module tự động áp dụng Gaussian Blur (kernel = 31) để làm mờ khuôn mặt của người đi bộ xung quanh và biển số của các phương tiện không liên quan.", "1. Làm mờ ẩn danh (Blur ROI): ");
    add_bullet_point(doc, "Mỗi tệp ảnh bằng chứng vi phạm được băm bằng thuật toán SHA-256 (Tamper-proof evidence hash) và lưu mã băm này vào cơ sở dữ liệu. Mọi hành vi can thiệp, chỉnh sửa ảnh sau đó sẽ làm sai lệch mã băm và bị phát hiện ngay lập tức.", "2. Chữ ký số chống giả mạo bằng chứng: ");

def build_chapter_6(doc):
    add_chapter_heading(doc, 6, "Hiện thực hóa Giao diện Web Dashboard & Trợ lý di động Mobile App")
    
    add_section_heading(doc, "6.1", "Kiến trúc phân hệ Web Dashboard (Next.js 14)")
    add_paragraph(doc,
        "Giao diện Web Dashboard được xây dựng trên nền tảng Next.js 14 App Router kết hợp TypeScript và Tailwind CSS. Kiến trúc giao diện áp dụng mô hình phân tách rõ ràng giữa Server Components (tối ưu hóa SEO và bảo mật dữ liệu) và Client Components (xử lý tương tác thời gian thực, Canvas 60 FPS và WebSockets).")
    add_paragraph(doc,
        "Quản lý trạng thái toàn cục bằng thư viện Zustand Store (authStore.ts), đồng bộ phiên làm việc của người dùng và tự động gắn kèm Bearer JWT vào mọi yêu cầu gọi API thông qua Axios Interceptor.")

    add_section_heading(doc, "6.2", "Chi tiết 9 Màn hình Quản trị & Giám sát Trực tuyến")
    
    add_subsection_heading(doc, "6.2.1", "Màn hình Đăng nhập & Điều hướng Phân quyền (/login)")
    add_paragraph(doc,
        "Giao diện đăng nhập hiện đại với cơ chế chọn nhanh vai trò demo (Quản trị viên: admin@vinafleet.com, Điều độ viên: dispatcher@vinafleet.com, Tài xế: driver1@example.com). Hệ thống kiểm tra quyền hạn và tự động chuyển hướng người dùng đến đúng bảng điều khiển tương ứng.")

    add_subsection_heading(doc, "6.2.2", "Màn hình Trung tâm Điều hành Tổng quan (/dashboard)")
    add_paragraph(doc,
        "Bảng điều khiển trung tâm hiển thị trực quan các chỉ số an toàn cốt lõi toàn doanh nghiệp:")
    add_bullet_point(doc, "Điểm an toàn đội xe (Fleet Safety Score - thang điểm 100).", "Chỉ số 1: ");
    add_bullet_point(doc, "Tổng số phiên hành trình đang vận hành trong ngày.", "Chỉ số 2: ");
    add_bullet_point(doc, "Tổng số sự cố vi phạm an toàn phát sinh theo thời gian thực.", "Chỉ số 3: ");
    add_bullet_point(doc, "Biểu đồ xu hướng vi phạm theo từng mốc thời gian và danh sách vi phạm khẩn cấp gần nhất.", "Chỉ số 4: ");

    add_image_figure(doc, "report_assets/fig_violation_distribution_clean.png", "Hình 6.1: Biểu đồ cơ cấu các loại lỗi vi phạm an toàn giao thông trên Web Dashboard", 5.5)

    add_subsection_heading(doc, "6.2.3", "Màn hình Giám sát Trực tuyến Live Camera AI (/live)")
    add_paragraph(doc,
        "Đây là phân hệ phức tạp và quan trọng nhất của Web Dashboard:")
    add_bullet_point(doc, "Hỗ trợ 2 chế độ nguồn: Tải tệp Video MP4 (kéo thả video có sẵn) hoặc Mở luồng trực tiếp từ Webcam máy tính.", "1. Nguồn phát linh hoạt: ");
    add_bullet_point(doc, "Hiển thị song song hai khung hình: RoadCameraViewport.tsx (Camera góc rộng quét mặt đường) và CabinCameraViewport.tsx (Camera góc hẹp quan sát gương mặt tài xế).", "2. Bộ xem luồng kép (Dual Viewport): ");
    add_bullet_point(doc, "Sử dụng HTML5 Canvas vẽ đè các Bounding Box với tần số 60 FPS mượt mà; hộp màu tự động đổi sang Đỏ khi có nguy cơ va chạm và Xanh khi an toàn; hiển thị nhãn loại xe, biển số xe và cự ly khoảng cách mét.", "3. Canvas thời gian thực (DetectionCanvas.tsx): ");
    add_bullet_point(doc, "Dải thông tin hợp nhất (UnifiedTelemetryStrip.tsx) hiển thị tốc độ thực tế (km/h), cự ly an toàn tối thiểu, giới hạn tốc độ khuyến nghị và trạng thái tỉnh táo của tài xế.", "4. Băng dải Telemetry: ");
    add_bullet_point(doc, "Thanh báo động ưu tiên (PriorityAlertBar.tsx) và Biểu ngữ cảnh báo nguy cấp (CriticalAlertBanner.tsx) nhấp nháy nổi bật khi phát hiện sự cố.", "5. Cảnh báo trực quan: ");

    add_subsection_heading(doc, "6.2.4", "Màn hình Quản lý Hồ sơ Vi phạm (/violations)")
    add_paragraph(doc,
        "Danh mục toàn bộ các sự cố vi phạm được AI ghi nhận. Hỗ trợ bộ lọc nhanh theo 5 loại lỗi chính: Quá tốc độ, Khoảng cách an toàn, Buồn ngủ, Mũ bảo hiểm, Dây an toàn.")
    add_paragraph(doc,
        "Modal soi ảnh bằng chứng: Khi click vào một sự cố, modal nổi lên hiển thị ảnh chụp độ phân giải cao trích xuất từ camera AI, hiển thị vận tốc lúc vi phạm, tọa độ GPS, thời gian chính xác và hai nút hành động: 'Phê duyệt biên bản' hoặc 'Bác bỏ cảnh báo'.")

    add_subsection_heading(doc, "6.2.5", "Các Màn hình Quản trị Bổ trợ (/journeys, /devices, /analytics, /ai-status, /simulator)")
    add_bullet_point(doc, "Quản lý lịch sử các chuyến đi; xem chi tiết lộ trình và Timeline các sự kiện diễn ra trên đường.", "Màn hình /journeys: ");
    add_bullet_point(doc, "Quản lý danh mục phương tiện (biển số, loại xe), gán tài xế và trạng thái thiết bị.", "Màn hình /devices: ");
    add_bullet_point(doc, "Thống kê tỷ lệ tuân thủ an toàn theo tháng, xếp hạng điểm an toàn của từng tài xế.", "Màn hình /analytics: ");
    add_bullet_point(doc, "Bảng chẩn đoán trực tiếp tình trạng hoạt động, model sử dụng, FPS thực tế và độ trễ của 12 module AI.", "Màn hình /ai-status: ");
    add_bullet_point(doc, "Môi trường Sandbox cho phép kích hoạt các tình huống giả lập để kiểm thử phản ứng của hệ thống cảnh báo.", "Màn hình /simulator: ");

    add_section_heading(doc, "6.3", "Động cơ Phát âm thanh & Giọng nói Cảnh báo Tiếng Việt (soundEngine.ts)")
    add_paragraph(doc,
        "Hệ thống phát cảnh báo âm thanh đa tầng được tích hợp trực tiếp trên Web Dashboard:")
    add_bullet_point(doc, "Tạo các xung sóng âm thanh Sine tần số cao (880Hz, 1200Hz) cảnh báo tức thì với độ trễ 0ms mà không cần tải file âm thanh ngoài.", "1. Web Audio API (Còi báo động): ");
    add_bullet_point(doc, "Tự động tổng hợp và phát giọng nói tiếng Việt chuẩn tự nhiên qua loa thiết bị với các thông điệp nghiệp vụ:", "2. Web Speech API (Giọng nói tiếng Việt): ");
    add_bullet_point(doc, "• 'Chú ý: Giảm tốc độ xe!'\n• 'Nguy hiểm: Giữ khoảng cách an toàn!'\n• 'Cảnh báo: Tài xế đang buồn ngủ, vui lòng nghỉ ngơi!'\n• 'Nhắc nhở: Vui lòng thắt dây an toàn trước khi khởi hành!'", "Các câu lệnh mẫu: ");

    add_section_heading(doc, "6.4", "Hiện thực hóa Ứng dụng Di động Trợ lý Lái xe (Mobile App - Expo)")
    add_paragraph(doc,
        "Ứng dụng di động được xây dựng bằng React Native trên nền tảng Expo, cho phép biến chiếc điện thoại thông minh của tài xế thành một thiết bị HUD trợ lý lái xe chuyên nghiệp:")
    add_bullet_point(doc, "Giao diện tối màu tương phản cao (High-Contrast HUD Mode) giúp tài xế quan sát rõ nét ngay cả khi đặt điện thoại dưới kính chắn gió ô tô.", "1. Màn hình Lái xe HUD (drive.tsx): ");
    add_bullet_point(doc, "Đồng hồ hiển thị vận tốc điện tử cỡ lớn (Digital HUD Speedometer) lấy dữ liệu thời gian thực.", "2. Đồng hồ tốc độ điện tử: ");
    add_bullet_point(doc, "Toàn bộ viền màn hình tự động đổi màu theo 3 cấp độ an toàn (Xanh: An toàn | Vàng: Chú ý | Đỏ: Nguy hiểm va chạm).", "3. Đổi màu trạng thái viền: ");
    add_bullet_point(doc, "Quản lý vòng đời chuyến đi: Khởi hành -> Đang di chuyển -> Dừng nghỉ -> Hoàn thành chuyến đi.", "4. Máy trạng thái hành trình (tripStateMachine.ts): ");
    add_bullet_point(doc, "Tự động tổng kết số km đã đi, thời gian lái và tính điểm an toàn (Safety Score) của tài xế.", "5. Màn hình Tổng kết chuyến đi (trip-summary.tsx): ");
