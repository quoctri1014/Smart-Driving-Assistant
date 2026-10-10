from docx.shared import Inches
from report_builder import (
    add_chapter_heading, add_section_heading, add_subsection_heading,
    add_paragraph, add_bullet_point, add_callout_box, add_formula_box,
    add_custom_table, add_image_figure
)

def build_chapter_1(doc):
    add_chapter_heading(doc, 1, "Tổng quan đề tài & Bối cảnh nghiên cứu")
    
    add_section_heading(doc, "1.1", "Đặt vấn đề và tính cấp thiết của đề tài")
    add_paragraph(doc, 
        "Giao thông vận tải đường bộ đóng vai trò huyết mạch trong nền kinh tế Việt Nam, luân chuyển hơn 75% khối lượng hàng hóa và 90% lượt hành khách cả nước. Tuy nhiên, tình hình trật tự an toàn giao thông vẫn diễn biến vô cùng phức tạp. Theo thống kê thường niên của Ủy ban An toàn Giao thông Quốc gia, mỗi năm tại Việt Nam xảy ra hàng chục nghìn vụ tai nạn giao thông, cướp đi sinh mạng của hơn 6.000 đến 8.000 người và làm bị thương hàng chục nghìn người khác. Đáng chú ý, hơn 80% nguyên nhân trực tiếp dẫn tới các vụ tai nạn thảm khốc xuất phát từ yếu tố chủ quan và trạng thái thể chất, tâm lý của người điều khiển phương tiện.")
    
    add_paragraph(doc,
        "Trong đó, ba nguyên nhân cốt lõi bao gồm: (1) Tài xế buồn ngủ hoặc mất tập trung khi lái xe đường dài, đặc biệt vào các khung giờ đêm muộn và rạng sáng; (2) Không giữ khoảng cách an toàn với xe chạy liền trước theo quy định của Thông tư 31/2019/TT-BGTVT dẫn tới các vụ đâm va dồn toa liên hoàn; (3) Vi phạm tốc độ tối đa cho phép và không tuân thủ các biển báo hạn chế, biển phụ theo giờ. Thực tế giao thông tại các đô thị lớn như Hà Nội và TP. Hồ Chí Minh còn có sự phân luồng rất phức tạp, nơi nhiều tuyến đường cấm ô tô quay đầu hoặc rẽ trái theo khung giờ cao điểm (ví dụ: cấm từ 06:00 đến 22:00), gây khó khăn cho tài xế nếu không có trợ lý nhắc nhở kịp thời.")
    
    add_callout_box(doc,
        "Nghiên cứu của Cục Đường bộ Việt Nam chỉ ra rằng, việc cảnh báo sớm nguy cơ va chạm trước chỉ 1.5 giây có thể giúp ngăn chặn tới 90% số vụ đâm va từ phía sau, và cảnh báo tài xế trước khi chợp mắt có thể loại bỏ hoàn toàn các vụ lật xe trên cao tốc.",
        "THỰC TRẠNG AN TOÀN GIAO THÔNG")

    add_section_heading(doc, "1.2", "Tổng quan các giải pháp trong và ngoài nước")
    add_paragraph(doc,
        "Trước thách thức trên, các giải pháp công nghệ hỗ trợ lái xe nâng cao (ADAS - Advanced Driver Assistance Systems) và giám sát trạng thái tài xế (DMS - Driver Monitoring System) đã và đang được phát triển mạnh mẽ trên thế giới và tại Việt Nam.")
    
    add_paragraph(doc, "Bảng so sánh chi tiết giữa các giải pháp công nghệ trên thị trường và hệ thống TrafficGuard:", "Bảng 1.1: ")
    
    headers_1_1 = ["Tiêu chí so sánh", "Giải pháp Quốc tế (Mobileye / Samsara)", "Camera Nghị định 10 tại VN", "Hệ thống TrafficGuard (Đề tài)"]
    data_1_1 = [
        ["Chi phí triển khai", "Rất cao ($1,500 - $3,000 / xe)", "Thấp đến trung bình ($100 - $200)", "Rất thấp (Tận dụng camera có sẵn / Điện thoại)"],
        ["Xử lý thời gian thực", "Có (Xử lý trên chip chuyên dụng ASIC)", "Không (Chỉ chụp ảnh tĩnh gửi về định kỳ 3-5p)", "Có (Xử lý Video Stream trực tiếp trên GPU/CPU biên)"],
        ["Độ trễ toàn trình", "< 40 ms", "Khoảng 3 - 5 phút (Delay chụp ảnh)", "< 38 ms (Thời gian thực WebSocket)"],
        ["Nhận diện biển báo VN", "Kém (Chỉ đọc chuẩn biển quốc tế / Châu Âu)", "Không hỗ trợ", "Chuyên sâu chuẩn QCVN 41:2019 và biển phụ thời gian S.508"],
        ["Nhận diện biển số xe", "Không hỗ trợ biển số chuẩn Việt Nam", "Chỉ chụp lưu hình ảnh, không OCR tự động", "Mô hình YOLOv11 + OCR chuyên biệt biển 1 dòng & 2 dòng"],
        ["Giám sát buồn ngủ DMS", "Có (Yêu cầu camera hồng ngoại đắt đỏ)", "Không hỗ trợ", "MediaPipe 468 điểm mốc (EAR, MAR, PERCLOS 60s)"],
        ["Hỗ trợ di động (HUD)", "Không (Hộp phần cứng đóng kín)", "Không", "Có ứng dụng di động Expo HUD đa nền tảng"]
    ]
    widths_1_1 = [Inches(1.5), Inches(1.8), Inches(1.6), Inches(1.8)]
    add_custom_table(doc, headers_1_1, data_1_1, widths_1_1, "Bảng 1.1: Đánh giá so sánh hệ thống TrafficGuard với các giải pháp hiện nay")

    add_section_heading(doc, "1.3", "Mục tiêu và nhiệm vụ nghiên cứu của đề tài")
    add_subsection_heading(doc, "1.3.1", "Mục tiêu tổng quát")
    add_paragraph(doc,
        "Xây dựng thành công nền tảng phần mềm 'All-in-One' kết hợp giữa Trợ lý lái xe thông minh trên phương tiện (Edge ADAS & HUD) và Hệ thống giám sát an toàn đội xe doanh nghiệp tập trung (Enterprise Fleet Management Platform), đảm bảo tính thời gian thực, độ chính xác cao và tối ưu riêng cho đặc thù hạ tầng giao thông Việt Nam.")

    add_subsection_heading(doc, "1.3.2", "Nhiệm vụ cụ thể")
    add_bullet_point(doc, "Nghiên cứu và hiện thực hóa Pipeline 12 Module AI thị giác máy tính xử lý đồng thời hai luồng camera: Road Camera (Mặt đường) và Cabin Camera (Người lái).", "Nhiệm vụ 1: ");
    add_bullet_point(doc, "Xây dựng thuật toán nhận diện biển báo QCVN 41:2019 kết hợp giải pháp cắt lát tỷ lệ cột để nhận diện biển phụ thời gian S.508 (6:00 - 22:00).", "Nhiệm vụ 2: ");
    add_bullet_point(doc, "Hiện thực hóa công thức tính khoảng cách an toàn theo Điều 11 Thông tư 31/2019/TT-BGTVT và mô hình cảnh báo va chạm sớm Time-To-Collision (TTC).", "Nhiệm vụ 3: ");
    add_bullet_point(doc, "Xây dựng máy chủ Backend FastAPI với cơ chế bảo mật JWT, phân quyền RBAC 3 vai trò, WebSocket song công toàn phần và chính sách bảo vệ dữ liệu theo Nghị định 13/2023/NĐ-CP.", "Nhiệm vụ 4: ");
    add_bullet_point(doc, "Thiết kế Web Dashboard (Next.js 14) với Canvas 60 FPS, âm thanh cảnh báo tiếng Việt và Ứng dụng di động HUD (React Native / Expo).", "Nhiệm vụ 5: ");

    add_section_heading(doc, "1.4", "Đối tượng, phạm vi nghiên cứu và phương pháp tiếp cận")
    add_paragraph(doc,
        "Đối tượng nghiên cứu: Luồng video kỹ thuật số ghi nhận từ camera hành trình giao thông đường bộ Việt Nam và camera cabin quan sát khuôn mặt tài xế; các quy định pháp luật giao thông đường bộ hiện hành (Luật GTVT 2008, Thông tư 31/2019, QCVN 41:2019).")
    add_paragraph(doc,
        "Phạm vi nghiên cứu: Tập trung vào các dòng phương tiện phổ biến tại Việt Nam (ô tô con, xe tải, xe khách, xe máy); giám sát các hành vi vi phạm có rủi ro tai nạn cao nhất (buồn ngủ, nhắm mắt kéo dài, quá tốc độ, không giữ khoảng cách, không thắt dây an toàn, không đội mũ bảo hiểm).")

    add_section_heading(doc, "1.5", "Bố cục của báo cáo đồ án")
    add_paragraph(doc,
        "Báo cáo đồ án được cấu trúc thành 9 chương nội dung chính cùng các phần mở đầu, phụ lục và tài liệu tham khảo theo đúng chuẩn mực học thuật:")
    add_bullet_point(doc, "Chương 1: Tổng quan đề tài & Bối cảnh nghiên cứu.");
    add_bullet_point(doc, "Chương 2: Cơ sở lý thuyết & Công nghệ nền tảng.");
    add_bullet_point(doc, "Chương 3: Phân tích yêu cầu & Thiết kế kiến trúc hệ thống.");
    add_bullet_point(doc, "Chương 4: Thiết kế và hiện thực hóa 12 Module Trí tuệ Nhân tạo (AI Core Pipeline).");
    add_bullet_point(doc, "Chương 5: Hiện thực hóa Máy chủ Backend & Cơ sở dữ liệu (FastAPI).");
    add_bullet_point(doc, "Chương 6: Hiện thực hóa Giao diện Web Dashboard & Trợ lý di động Mobile App.");
    add_bullet_point(doc, "Chương 7: Kiểm thử hệ thống, Đánh giá thực nghiệm & Hiệu năng.");
    add_bullet_point(doc, "Chương 8: Quy trình đóng gói, Triển khai Production & Khía cạnh Pháp lý.");
    add_bullet_point(doc, "Chương 9: Kết luận & Hướng phát triển tương lai.");

def build_chapter_2(doc):
    add_chapter_heading(doc, 2, "Cơ sở lý thuyết & Công nghệ nền tảng")
    
    add_section_heading(doc, "2.1", "Thị giác máy tính và Mạng nơ-ron tích chập (CNN)")
    add_paragraph(doc,
        "Thị giác máy tính (Computer Vision) kết hợp với Học sâu (Deep Learning) đã tạo ra bước đột phá vượt bậc trong các hệ thống tự hành và trợ lý lái xe. Trọng tâm của bài toán phát hiện đối tượng thời gian thực là kiến trúc mạng nơ-ron tích chập một giai đoạn (One-Stage Detector), tiêu biểu là họ mô hình YOLO (You Only Look Once).")
    
    add_paragraph(doc,
        "Trong dự án TrafficGuard, mô hình YOLOv8 Nano và YOLOv11 được ứng dụng làm xương sống cho tác vụ phát hiện phương tiện và biển báo. YOLOv8 sử dụng kiến trúc không neo (Anchor-free), loại bỏ sự phụ thuộc vào các Anchor box định sẵn, từ đó giảm đáng kể số lượng tham số cần huấn luyện và tối ưu hóa tốc độ suy luận (Inference time). Hàm mất mát của YOLOv8 kết hợp giữa Complete IoU Loss (CIoU) để định vị hộp bao và Distribution Focal Loss (DFL) để dự đoán tọa độ ranh giới chính xác đến từng pixel:")
    
    add_formula_box(doc,
        "L_CIoU = 1 - IoU + (ρ²(b, b^gt) / c²) + α * v",
        "2.1",
        "ρ là khoảng cách Euclidean giữa tâm hai hộp; c là đường chéo của hộp bao nhỏ nhất chứa cả hai hộp; v đo lường sự nhất quán về tỷ lệ khung hình; α là tham số cân bằng."
    )
    
    add_section_heading(doc, "2.2", "Các chỉ số sinh trắc học và thuật toán giám sát người lái (DMS)")
    add_paragraph(doc,
        "Hệ thống giám sát trạng thái tài xế (Driver Monitoring System - DMS) khai thác mô hình MediaPipe Face Mesh để phát hiện 468 điểm mốc 3D (Landmarks) trên khuôn mặt với tốc độ vượt trội trên CPU mà không đòi hỏi phần cứng GPU rời đắt tiền.")
    
    add_subsection_heading(doc, "2.2.1", "Chỉ số tỷ lệ co giãn mí mắt (Eye Aspect Ratio - EAR)")
    add_paragraph(doc,
        "EAR là đại lượng đặc trưng hình học dùng để định lượng mức độ mở của mí mắt. Với mỗi mắt được mô tả bởi 6 điểm mốc p1, p2, p3, p4, p5, p6 (trong đó p1 và p4 là hai khóe mắt ngang; p2, p3, p5, p6 là các điểm viền mí trên và dưới):")
    
    add_formula_box(doc,
        "EAR = ( ||p2 - p6|| + ||p3 - p5|| ) / ( 2 * ||p1 - p4|| )",
        "2.2",
        "Khi mắt mở bình thường, EAR dao động trong khoảng 0.28 - 0.35. Khi tài xế nhắm mắt hoặc chớp mắt, khoảng cách thẳng đứng giảm mạnh làm EAR tụt xuống dưới ngưỡng 0.20."
    )
    
    add_subsection_heading(doc, "2.2.2", "Chỉ số mở miệng ngáp (Mouth Aspect Ratio - MAR)")
    add_paragraph(doc,
        "Tương tự EAR, MAR phản ánh tỷ lệ độ mở dọc của khoang miệng so với chiều rộng mép môi:")
    
    add_formula_box(doc,
        "MAR = ( ||m2 - m8|| + ||m3 - m7|| + ||m4 - m6|| ) / ( 2 * ||m1 - m5|| )",
        "2.3",
        "Trạng thái ngáp ngủ được kích hoạt khi MAR vượt qua ngưỡng 0.65 và duy trì trong hơn 30 khung hình liên tiếp."
    )
    
    add_subsection_heading(doc, "2.2.3", "Tiêu chuẩn PERCLOS (Percentage of Eye Closure)")
    add_paragraph(doc,
        "PERCLOS là tiêu chuẩn vàng của Cơ quan An toàn Giao thông Quốc gia Hoa Kỳ (NHTSA) dùng để đánh giá mức độ mệt mỏi và ngủ gật của lái xe. PERCLOS được định nghĩa là tỷ lệ phần trăm thời gian mà mí mắt che khuất ít nhất 80% con ngươi trong một cửa sổ quan sát trượt thời gian t = 60 giây:")
    
    add_formula_box(doc,
        "PERCLOS = ( ∑ t_closed ) / T_window * 100%",
        "2.4",
        "Hệ thống TrafficGuard kích hoạt cảnh báo nguy cấp độ 2 khi chỉ số PERCLOS vượt quá 15% (0.15)."
    )
    
    # Insert chart EAR MAR
    add_image_figure(doc, "report_assets/fig_ear_mar_clean.png", "Hình 2.1: Biến thiên sinh trắc học EAR và MAR theo thời gian cùng các ngưỡng kích hoạt cảnh báo DMS", 6.2)

    add_section_heading(doc, "2.3", "Toán học biến đổi phối cảnh Homography và mô hình Time-To-Collision")
    add_subsection_heading(doc, "2.3.1", "Biến đổi phối cảnh phẳng (Perspective Homography Transformation)")
    add_paragraph(doc,
        "Camera hành trình ghi hình không gian 3 chiều qua phép chiếu phối cảnh (Perspective Projection), khiến cho các vật thể ở xa trông nhỏ hơn và các đường song song hội tụ tại một điểm ảo (Vanishing Point). Để đo khoảng cách vật lý thực tế tính bằng mét và vận tốc xe chạy (km/h) từ ảnh 2D, hệ thống sử dụng ma trận Homography H kích thước 3x3 để nắn chỉnh góc nhìn camera nghiêng thành góc nhìn thẳng từ trên xuống (Bird's Eye View - BEV):")
    
    add_formula_box(doc,
        "[ Xw, Yw, 1 ]^T = H * [ u, v, 1 ]^T",
        "2.5",
        "Trong đó (u, v) là tọa độ pixel điểm tiếp xúc mặt đường của đáy bánh xe, (Xw, Yw) là tọa độ thế giới thực trên mặt đường (mét)."
    )

    add_image_figure(doc, "report_assets/fig_homography_transformation_clean.png", "Hình 2.4: Toán học Biến đổi Phối cảnh (Homography) để Đo Khoảng cách & Vận tốc", 6.2)

    add_subsection_heading(doc, "2.3.2", "Mô hình thời gian va chạm tiềm ẩn (Time-To-Collision - TTC)")
    add_paragraph(doc,
        "Thời gian va chạm tiềm ẩn TTC là đại lượng vật lý quan trọng nhất để đánh giá mức độ cấp bách của cảnh báo đâm va phía trước (FCW):")
    
    add_formula_box(doc,
        "TTC = d_rel / v_rel = ( d_front - d_buffer ) / ( v_ego - v_lead )",
        "2.6",
        "Nếu v_ego <= v_lead (xe mình chạy chậm hơn xe trước), khoảng cách đang nới rộng và không có nguy cơ đâm va. Nếu v_ego > v_lead, TTC < 1.5s sẽ lập tức kích hoạt chuông báo động khẩn cấp."
    )

    add_image_figure(doc, "report_assets/fig_safe_distance_clean.png", "Hình 2.2: Đồ thị quy định khoảng cách an toàn tối thiểu theo Điều 11 Thông tư 31/2019/TT-BGTVT", 6.0)

    add_section_heading(doc, "2.4", "Công nghệ nhận diện ký tự quang học (OCR) Biển số xe Việt Nam")
    add_paragraph(doc,
        "Biển số xe cơ giới tại Việt Nam tuân theo quy định nghiêm ngặt tại Thông tư 24/2023/TT-BCA của Bộ Công an, bao gồm mã tỉnh thành (2 chữ số), seri đăng ký (1 chữ cái + 1 chữ số), và dãy số thứ tự đăng ký (5 chữ số với dấu chấm phân tách). Biển số ô tô bao gồm hai dạng: biển dài (1 hàng) và biển vuông (2 hàng); xe máy sử dụng biển vuông 2 hàng.")
    add_paragraph(doc,
        "Hệ thống ứng dụng quy trình OCR 3 giai đoạn: (1) Cắt vùng quan tâm (ROI Bounding box) từ YOLO; (2) Tiền xử lý xoay nắn thẳng (Deskewing) và cân bằng sáng CLAHE; (3) Nhận diện ký tự và khớp cú pháp (Regular Expression Matching) để tự động sửa các lỗi nhầm lẫn phổ biến giữa số 0 và chữ O, số 1 và chữ I, số 8 và chữ B.")

    add_section_heading(doc, "2.5", "Kiến trúc Client-Server & Công nghệ phát triển Full-Stack")
    add_paragraph(doc,
        "Nhằm đáp ứng yêu cầu xử lý thời gian thực với độ trễ siêu thấp và khả năng mở rộng cho hàng nghìn xe, hệ thống áp dụng kiến trúc tách biệt máy chủ AI/API và giao diện người dùng:")
    add_bullet_point(doc, "FastAPI (Python 3.11): Framework bất đồng bộ (Asynchronous ASGI) hiệu năng hàng đầu hiện nay, hỗ trợ tự động sinh tài liệu Swagger/OpenAPI và tích hợp trực tiếp với các thư viện Deep Learning (PyTorch, OpenCV, MediaPipe).", "Backend Server: ");
    add_bullet_point(doc, "Next.js 14 App Router (React 18 & TypeScript): Nền tảng Web hiện đại hỗ trợ Server-Side Rendering và Client-Side Rendering, quản lý trạng thái tập trung với Zustand Store và vẽ đè đồ họa Canvas ở tần số 60 FPS.", "Web Dashboard: ");
    add_bullet_point(doc, "Expo & React Native: Nền tảng ứng dụng di động đa nền tảng (iOS / Android), tối ưu hóa để trở thành trợ lý HUD hiển thị phản quang trên kính lái ô tô.", "Mobile App: ");
    add_bullet_point(doc, "Giao thức WebSocket: Thiết lập kênh truyền thông hai chiều (Full-Duplex) liên tục giữa client và server, loại bỏ hoàn toàn chi phí overhead của cơ chế Polling HTTP truyền thống.", "Realtime Protocol: ");
