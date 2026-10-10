# -*- coding: utf-8 -*-
"""
build_visual_deck.py
Builds the complete 28-slide visual-first, low-text presentation deck
matching 745545451-Slide-UTH.pptx for the TrafficGuard project.
"""

import os
import sys
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

sys.stdout.reconfigure(encoding='utf-8')

from slide_visual_helpers import (
    COLOR_UTH_TEAL, COLOR_UTH_RED, COLOR_DARK_TEXT, COLOR_BODY_TEXT, COLOR_MUTED_TEXT,
    COLOR_WHITE, COLOR_CARD_BG, COLOR_WARNING, COLOR_SUCCESS,
    FONT_MAIN, add_header, add_card, add_image_or_placeholder,
    add_side_card, add_kpi_strip
)

def build_presentation():
    template_path = '745545451-Slide-UTH.pptx'
    prs = pptx.Presentation(template_path)
    blank_layout = prs.slide_layouts[6]

    print("Formatting Slide 1 (Title Slide)...")
    s1 = prs.slides[0]
    for sh in s1.shapes:
        if sh.name == "Title 1":
            tf = sh.text_frame
            tf.clear()
            p1 = tf.paragraphs[0]
            p1.text = "TRƯỜNG ĐẠI HỌC GIAO THÔNG VẬN TẢI THÀNH PHỐ HỒ CHÍ MINH"
            p1.font.name = FONT_MAIN
            p1.font.size = Pt(20)
            p1.font.bold = True
            p1.font.color.rgb = COLOR_UTH_TEAL
            p1.alignment = PP_ALIGN.CENTER

            p2 = tf.add_paragraph()
            p2.text = "VIỆN CÔNG NGHỆ THÔNG TIN VÀ ĐIỆN, ĐIỆN TỬ"
            p2.font.name = FONT_MAIN
            p2.font.size = Pt(16)
            p2.font.bold = True
            p2.font.color.rgb = COLOR_UTH_RED
            p2.alignment = PP_ALIGN.CENTER

        elif sh.name == "Content Placeholder 2":
            tf = sh.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            p.text = "BÁO CÁO NGHIÊN CỨU & BẢO VỆ ĐỒ ÁN TỐT NGHIỆP"
            p.font.name = FONT_MAIN
            p.font.size = Pt(24)
            p.font.bold = True
            p.font.color.rgb = COLOR_UTH_TEAL
            p.alignment = PP_ALIGN.CENTER

        elif sh.name == "Subtitle 2" and sh.top < 3000000:
            tf = sh.text_frame
            tf.clear()
            p1 = tf.paragraphs[0]
            p1.text = "HỆ THỐNG TRỢ LÝ LÁI XE THÔNG MINH\nTÍCH HỢP NHẬN DIỆN BIỂN SỐ VÀ CẢNH BÁO VA CHẠM"
            p1.font.name = FONT_MAIN
            p1.font.size = Pt(25)
            p1.font.bold = True
            p1.font.color.rgb = COLOR_UTH_RED
            p1.alignment = PP_ALIGN.CENTER

            p2 = tf.add_paragraph()
            p2.text = "Nền tảng Giám sát An toàn Đội xe Doanh nghiệp (TrafficGuard Platform)"
            p2.font.name = FONT_MAIN
            p2.font.size = Pt(17)
            p2.font.bold = True
            p2.font.color.rgb = COLOR_DARK_TEXT
            p2.alignment = PP_ALIGN.CENTER

        elif sh.name == "Subtitle 2" and sh.top >= 3000000:
            tf = sh.text_frame
            tf.clear()
            p1 = tf.paragraphs[0]
            p1.text = "Giảng viên hướng dẫn:  ThS. HÀN TRUNG ĐỊNH"
            p1.font.name = FONT_MAIN
            p1.font.size = Pt(18)
            p1.font.bold = True
            p1.font.color.rgb = COLOR_UTH_TEAL
            p1.alignment = PP_ALIGN.CENTER

            p2 = tf.add_paragraph()
            p2.text = "Sinh viên thực hiện:     Lê Quốc Trí (MSSV: 068205011936)  —  Nguyễn Thành Hiếu (MSSV: 072205000471)  —  Phạm Trương Anh Tú (MSSV: 051205000251)"
            p2.font.name = FONT_MAIN
            p2.font.size = Pt(14)
            p2.font.bold = True
            p2.font.color.rgb = COLOR_DARK_TEXT
            p2.alignment = PP_ALIGN.CENTER

            p3 = tf.add_paragraph()
            p3.text = "Ngành: CÔNG NGHỆ THÔNG TIN  |  TP. Hồ Chí Minh, Tháng 10 Năm 2026"
            p3.font.name = FONT_MAIN
            p3.font.size = Pt(13)
            p3.font.italic = True
            p3.font.color.rgb = COLOR_BODY_TEXT
            p3.alignment = PP_ALIGN.CENTER

    print("Formatting Slide 2 (Visual Agenda)...")
    s2 = prs.slides[1]
    for sh in list(s2.shapes):
        if sh.name == "Title 1":
            sh.text_frame.text = "NỘI DUNG BÁO CÁO NGHIÊN CỨU"
            p = sh.text_frame.paragraphs[0]
            p.font.name = FONT_MAIN
            p.font.size = Pt(24)
            p.font.bold = True
            p.font.color.rgb = COLOR_UTH_TEAL
            p.alignment = PP_ALIGN.CENTER
            sh.top = Inches(0.55)
            sh.height = Inches(0.65)
        elif sh.name == "Content Placeholder 2":
            sp_elem = sh._element
            sp_elem.getparent().remove(sp_elem)

    agenda_cards = [
        ("01", "TỔNG QUAN & BỐI CẢNH", "Thực trạng TNGT Việt Nam, hạn chế giải pháp hiện hữu, mục tiêu nghiên cứu."),
        ("02", "KIẾN TRÚC HỆ THỐNG", "Mô hình 4 tầng phân lớp, luồng kép song song Road-Cabin, Load Shedder."),
        ("03", "12 MODULE & THUẬT TOÁN AI", "YOLOv8, MOT, Homography đo tốc độ, TT31, TTC, Pole Slicing, ALPR, DMS (TRỌNG TÂM)."),
        ("04", "BACKEND & CƠ SỞ DỮ LIỆU", "FastAPI ASGI Event Loop, WebSocket Full-Duplex, 15 bảng 3NF, Triệt tiêu VRAM Leak."),
        ("05", "WEB DASHBOARD & MOBILE HUD", "Next.js 14 Canvas 60 FPS, âm thanh & giọng nói tiếng Việt, Expo Mobile HUD."),
        ("06", "THỰC NGHIỆM & KẾT LUẬN", "90/90 PyTest, Benchmark mAP 94.2%, Latency 38ms, Stress Test 50 clients, Q&A.")
    ]
    card_w = Inches(5.6)
    card_h = Inches(1.5)
    for i, (num, title, desc) in enumerate(agenda_cards):
        col = i % 2
        row = i // 2
        l = Inches(0.9) if col == 0 else Inches(6.8)
        t = Inches(1.35) + row * Inches(1.68)
        add_card(s2, l, t, card_w, card_h, bg_color=COLOR_WHITE, border_color=COLOR_UTH_TEAL)

        tb = s2.shapes.add_textbox(l + Inches(0.18), t + Inches(0.14), card_w - Inches(0.36), card_h - Inches(0.28))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.text = f"PHẦN {num}: {title}"
        p1.font.name = FONT_MAIN
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_UTH_RED if "THUẬT TOÁN" in title else COLOR_UTH_TEAL

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = FONT_MAIN
        p2.font.size = Pt(11)
        p2.font.color.rgb = COLOR_BODY_TEXT

    # Remove placeholder slides from index 2 onwards
    while len(prs.slides) > 2:
        rId = prs.slides._sldIdLst[2].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[2]

    # =========================================================================
    # SLIDE 3: BỐI CẢNH & TÍNH CẤP THIẾT
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Bối cảnh Nghiên cứu & Tính cấp thiết của Hệ thống ADAS/DMS", "Phần 1: Tổng quan & Bối cảnh", 3)
    
    add_image_or_placeholder(
        s3, None, Inches(0.9), Inches(1.35), Inches(7.0), Inches(4.3),
        "ẢNH THỰC TẾ: TÌNH HUỐNG GIAO THÔNG HỖN HỢP & CAMERA HÀNH TRÌNH TẠI VIỆT NAM",
        "Chèn ảnh chụp thực tế từ camera hành trình đường phố VN (xe máy dày đặc, biển phụ giờ phức tạp)"
    )
    add_side_card(
        s3, Inches(8.1), Inches(1.35), Inches(4.3), Inches(4.3),
        "4 Thách Thức Tử Thần",
        [
            ("Ngủ gật (Microsleep)", "1-3 giây chợp mắt đủ gây đâm va trực diện khi chạy đêm.", "Nguy cấp"),
            ("Bám đuôi sát", "Không giữ cự ly an toàn theo Điều 11 Thông tư 31/2019/TT-BGTVT.", "Phổ biến"),
            ("Chạy quá tốc độ", "Tăng bình phương động năng, kéo dài quãng đường phanh.", "Trọng điểm"),
            ("Bỏ sót biển phụ giờ", "Quá tải thị giác với biển cấm P.124b kèm biển phụ S.508.", "Đặc thù VN")
        ],
        badge_color=COLOR_UTH_RED
    )
    add_kpi_strip(
        s3, Inches(0.9), Inches(5.8), Inches(11.5), Inches(0.85),
        [
            ("75% - 90%", "Tỷ trọng Vận tải Hàng hóa & Khách", COLOR_UTH_TEAL),
            ("1 - 3 Giây", "Thời gian Vi ngủ gây TNGT thảm khốc", COLOR_UTH_RED),
            ("3 - 5 Phút", "Chu kỳ chụp ảnh thụ động của Cam NĐ10", COLOR_WARNING)
        ]
    )

    # =========================================================================
    # SLIDE 4: ĐỐI CHIẾU & ĐỊNH VỊ GIẢI PHÁP
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Mục tiêu Đề tài & Ma trận Định vị Giải pháp Công nghệ", "Phần 1: Tổng quan & Bối cảnh", 4)

    # Table on Left
    table_shape = s4.shapes.add_table(5, 5, Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2))
    tbl = table_shape.table
    tbl.columns[0].width = Inches(2.0)
    tbl.columns[1].width = Inches(1.3)
    tbl.columns[2].width = Inches(1.3)
    tbl.columns[3].width = Inches(1.2)
    tbl.columns[4].width = Inches(1.4)

    headers = ["Tiêu chí Đánh giá", "Mobileye", "Samsara", "Cam NĐ10", "TRAFFICGUARD"]
    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_UTH_TEAL if j < 4 else COLOR_UTH_RED
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_MAIN
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

    row_data = [
        ("Xử lý AI Thời gian thực", "Có (<40ms)", "Cloud trễ", "Không (Ảnh tĩnh)", "Có (38ms Edge)"),
        ("Đọc Biển phụ Giờ S.508", "Không", "Không", "Không", "Có (Pole Slicing)"),
        ("ALPR Biển số Việt Nam", "Không", "US/EU", "Không", "Có (4 bước chuẩn)"),
        ("Chi phí Đầu tư Phần cứng", "Rất đắt ($2k+)", "Thuê bao cao", "Trung bình", "Tối ưu chi phí")
    ]
    for i, row in enumerate(row_data):
        for j, val in enumerate(row):
            cell = tbl.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_WHITE if (i % 2 == 0) else COLOR_CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            p.font.name = FONT_MAIN
            p.font.size = Pt(10.5)
            p.font.bold = (j == 4 or j == 0)
            p.font.color.rgb = COLOR_UTH_RED if j == 4 else COLOR_DARK_TEXT

    add_side_card(
        s4, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "3 Lợi Thế Đột Phá",
        [
            ("Make in Vietnam", "Làm chủ 100% công nghệ, tương thích hoàn hảo luật giao thông và hạ tầng xe máy tại VN.", "Độc quyền"),
            ("Độ trễ Siêu tốc (38ms)", "Xử lý trực tiếp in-memory trên thiết bị, thỏa mãn tiêu chuẩn an toàn phản xạ < 50ms.", "Thời gian thực"),
            ("Hệ sinh thái All-in-One", "Tích hợp trọn vẹn: Edge ADAS + Cabin DMS + Web Fleet Management + Mobile HUD.", "Toàn diện")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 5: KIẾN TRÚC TỔNG THỂ 4 TẦNG
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Kiến trúc Tổng thể 4 Tầng của Nền tảng TrafficGuard", "Phần 2: Kiến trúc Hệ thống", 5)

    add_image_or_placeholder(
        s5, "report_assets/fig_system_architecture.png", Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "SƠ ĐỒ KIẾN TRÚC TỔNG THỂ 4 TẦNG (SYSTEM ARCHITECTURE)",
        "Kiến trúc phân lớp sạch: Edge Sensors -> AI Core Pipeline -> Backend FastAPI & CSDL -> Web/Mobile HUD"
    )
    add_side_card(
        s5, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Đặc Tả 4 Tầng Hệ Thống",
        [
            ("Tầng 1: Sensors & Edge", "Camera hành trình (Road), Camera cabin (DMS), Telemetry GPS/Vận tốc từ OBD.", "Đầu vào"),
            ("Tầng 2: AI Core Pipeline", "12 Module AI xử lý song song; van điều tiết Load Shedder giữ độ trễ < 45ms.", "Xử lý 38ms"),
            ("Tầng 3: Backend & CSDL", "FastAPI ASGI Event Loop, JWT, RBAC 3 vai trò, CSDL PostgreSQL 15 bảng 3NF.", "Điều phối"),
            ("Tầng 4: Trình diễn (UI)", "Web Next.js 14 Canvas 60 FPS, âm thanh tiếng Việt & Ứng dụng di động HUD Expo.", "Tương tác")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 6: LUỒNG XỬ LÝ SONG SONG 2 KÊNH (DUAL STREAM)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Kiến trúc Luồng Xử lý Song song 2 Kênh Camera (Dual-Stream Pipeline)", "Phần 2: Kiến trúc Hệ thống", 6)

    add_image_or_placeholder(
        s6, "report_assets/fig_dual_stream_pipeline_pro.png", Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "SƠ ĐỒ LUỒNG XỬ LÝ SONG SONG ROAD VISION & CABIN DMS",
        "Luồng phân tích song song: Road Stream quét mặt đường & Cabin Stream quan sát người lái"
    )
    add_side_card(
        s6, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Phân Luồng & Điều Tiết",
        [
            ("Road Vision Stream", "Camera đường -> YOLOv8n -> MOT -> Homography Speed -> Sign & Slicing -> Plate ALPR -> TTC.", "Luồng 1"),
            ("Cabin DMS Stream", "Camera cabin -> MediaPipe 468 mesh -> EAR/MAR/PERCLOS -> 3D Head Pose -> Dây an toàn -> Timer 4h.", "Luồng 2"),
            ("Van Điều tiết Load Shedder", "Tự động drop frame phụ khi hàng đợi trễ > 45ms, bảo vệ cảnh báo khẩn cấp sống còn.", "Tự bảo vệ"),
            ("Kênh WebSocket Full-Duplex", "Truyền nhận JSON hai chiều, triệt tiêu overhead HTTP, trễ mạng chỉ 5-12ms.", "Độ trễ thấp")
        ],
        badge_color=COLOR_UTH_RED
    )

    # =========================================================================
    # SLIDE 7: BẢN ĐỒ 12 MODULE AI
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Bản đồ Kiến trúc 12 Module Trí tuệ Nhân tạo Thời gian thực", "Phần 3: Thuật toán AI Cốt lõi", 7)

    col_w = Inches(3.65)
    col_h = Inches(5.2)

    # Col 1: Road
    add_card(s7, Inches(0.9), Inches(1.35), col_w, col_h, bg_color=COLOR_WHITE, border_color=COLOR_UTH_TEAL)
    tb = s7.shapes.add_textbox(Inches(1.05), Inches(1.45), col_w - Inches(0.3), col_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "1. THỊ GIÁC ĐƯỜNG (ROAD)"
    p.font.name = FONT_MAIN
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_UTH_TEAL

    r_items = [
        ("load_shedder.py", "Giữ độ trễ hàng đợi < 45ms"),
        ("vehicle_detector.py", "YOLOv8n nhận diện 4 lớp xe"),
        ("multi_object_tracker.py", "Bám vết Hungarian + IoU"),
        ("speed_estimator.py", "Homography Bird's Eye View"),
        ("sign_detector.py", "Biển QCVN 41 & Pole Slicing"),
        ("plate_recognizer.py", "ALPR 4 bước Deskew + Regex")
    ]
    for fn, desc in r_items:
        p1 = tf.add_paragraph()
        p1.space_before = Pt(6)
        p1.text = f"• {fn}\n   ↳ {desc}"
        p1.font.name = FONT_MAIN
        p1.font.size = Pt(10.5)
        p1.font.color.rgb = COLOR_DARK_TEXT

    # Col 2: Decision
    add_card(s7, Inches(4.8), Inches(1.35), col_w, col_h, bg_color=COLOR_WHITE, border_color=COLOR_WARNING)
    tb2 = s7.shapes.add_textbox(Inches(4.95), Inches(1.45), col_w - Inches(0.3), col_h - Inches(0.2))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "2. AN TOÀN & RA QUYẾT ĐỊNH"
    p.font.name = FONT_MAIN
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_WARNING

    s_items = [
        ("safe_distance_calculator.py", "Khoảng cách an toàn TT 31"),
        ("collision_warning.py", "Time-To-Collision (TTC)"),
        ("helmet_checker.py", "Mũ bảo hiểm & Khử trùng lặp"),
        ("violation_manager.py", "Rolling buffer 10 frames + SHA-256"),
        ("decision_engine.py", "3 cấp ưu tiên, Debounce 3.0s")
    ]
    for fn, desc in s_items:
        p1 = tf2.add_paragraph()
        p1.space_before = Pt(8)
        p1.text = f"• {fn}\n   ↳ {desc}"
        p1.font.name = FONT_MAIN
        p1.font.size = Pt(10.5)
        p1.font.color.rgb = COLOR_DARK_TEXT

    # Col 3: Cabin DMS
    add_card(s7, Inches(8.7), Inches(1.35), col_w, col_h, bg_color=COLOR_WHITE, border_color=COLOR_UTH_RED)
    tb3 = s7.shapes.add_textbox(Inches(8.85), Inches(1.45), col_w - Inches(0.3), col_h - Inches(0.2))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "3. GIÁM SÁT CABIN (DMS)"
    p.font.name = FONT_MAIN
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_UTH_RED

    d_items = [
        ("drowsiness_detector.py", "MediaPipe 468 mesh, EAR, MAR"),
        ("sunglasses_mode.py", "Tự động chuyển tư thế đầu 3D"),
        ("head_pose_estimator.py", "cv2.solvePnP (Pitch & Yaw)"),
        ("eyes_closed_monitor.py", "Bắt vi ngủ Microsleep > 1.5s"),
        ("seatbelt_checker.py", "Vân chéo dây đai qua vai"),
        ("driving_timer.py", "Đếm thời gian lái liên tục 4h")
    ]
    for fn, desc in d_items:
        p1 = tf3.add_paragraph()
        p1.space_before = Pt(6)
        p1.text = f"• {fn}\n   ↳ {desc}"
        p1.font.name = FONT_MAIN
        p1.font.size = Pt(10.5)
        p1.font.color.rgb = COLOR_DARK_TEXT

    # =========================================================================
    # SLIDE 8: THUẬT TOÁN 1 - PHÁT HIỆN & BÁM VẾT XE (YOLOv8 + MOT)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Thuật toán 1: Phát hiện Phương tiện (YOLOv8) & Bám vết Đa đối tượng (MOT)", "Phần 3: Thuật toán AI Cốt lõi", 8)

    add_image_or_placeholder(
        s8, None, Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "ẢNH DEMO THỰC TẾ: BẢO VỆ BOUNDING BOX NHẬN DIỆN 4 LỚP XE & TRACKER ID",
        "Chèn ảnh chụp màn hình nhận diện phương tiện thực tế: ô tô, xe máy, xe buýt, xe tải kèm Bounding Box và ID"
    )
    add_side_card(
        s8, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Điểm Nhấn Thuật Toán",
        [
            ("Mô hình YOLOv8 Nano", "Phát hiện 4 lớp: car, motorcycle, bus, truck. Tốc độ suy luận chỉ 8ms.", "mAP 94.2%"),
            ("Anchor-Free Decoupled Head", "Tách riêng phân loại và hồi quy vị trí, tối ưu tỷ lệ khung hình xe đa dạng tại VN.", "Độ chính xác cao"),
            ("Hàm mất mát CIoU + DFL", "Tối ưu đồng thời IoU, khoảng cách tâm và tính nhất quán tỷ lệ hộp bao.", "L_CIoU"),
            ("Hungarian + IoU Tracking", "Cấp phát Tracker ID duy nhất; bảo lưu trạng thái 3-5 frames khi xe bị che khuất.", "MOT bền vững"),
            ("Cắt giảm ROI 30%", "Loại bỏ 30% nửa trên khung hình (bầu trời), tiết kiệm 28% thời gian tính toán.", "Tối ưu 28%")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 9: THUẬT TOÁN 2 - ĐO VẬN TỐC HOMOGRAPHY
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Thuật toán 2: Ước tính Vận tốc qua Biến đổi Phối cảnh Homography", "Phần 3: Thuật toán AI Cốt lõi", 9)

    add_image_or_placeholder(
        s9, "report_assets/fig_homography_transformation_clean.png", Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "SƠ ĐỒ BIẾN ĐỔI PHỐI CẢNH HOMOGRAPHY SANG BIRD'S EYE VIEW",
        "Ánh xạ phối cảnh từ mặt phẳng camera 2D sang mặt phẳng tọa độ thực địa mét (Bird's Eye View)"
    )
    add_side_card(
        s9, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Công Thức & Đo Đạc",
        [
            ("Bản chất hình học 2D", "Camera có hiện tượng hội tụ điểm ảo (Vanishing Point), pixel không tỷ lệ tuyến tính với mét.", "Biến dạng 2D"),
            ("Ma trận Homography H (3x3)", "Ánh xạ tọa độ pixel [u, v, 1] sang tọa độ thực phẳng [X_w, Y_w, 1] qua DLT & SVD.", "BEV Matrix"),
            ("Công thức Vận tốc (km/h)", "v = (√(ΔX_w² + ΔY_w²) / Δt) × 3.6  dựa trên độ dịch chuyển tiếp xúc bánh xe.", "± 2.5 km/h"),
            ("Bộ lọc Trung bình trượt", "Cửa sổ n = 5 frames làm mịn tín hiệu, triệt tiêu rung lắc do mặt đường gồ ghề.", "Khử rung lắc")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 10: THUẬT TOÁN 3 - KHOẢNG CÁCH AN TOÀN TT 31/2019
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Thuật toán 3: Giám sát Khoảng cách An toàn theo Thông tư 31/2019/TT-BGTVT", "Phần 3: Thuật toán AI Cốt lõi", 10)

    add_image_or_placeholder(
        s10, "report_assets/fig_safe_distance_clean.png", Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "ĐỒ THỊ QUY ĐỊNH KHOẢNG CÁCH AN TOÀN TỐI THIỂU THEO ĐIỀU 11 THÔNG TƯ 31/2019",
        "Tra cứu cự ly an toàn bắt buộc theo các dải vận tốc thực tế của phương tiện"
    )
    add_side_card(
        s10, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Quy Định Pháp Luật & Thuật Toán",
        [
            ("v ≤ 60 km/h", "Chủ động giữ cự ly an toàn theo mật độ dòng xe thực tế.", "Nội đô"),
            ("60 < v ≤ 80 km/h", "Khoảng cách an toàn tối thiểu bắt buộc d_safe ≥ 55 mét.", "d ≥ 55m"),
            ("80 < v ≤ 100 km/h", "Khoảng cách an toàn tối thiểu bắt buộc d_safe ≥ 70 mét.", "d ≥ 70m"),
            ("100 < v ≤ 120 km/h", "Khoảng cách an toàn tối thiểu bắt buộc d_safe ≥ 100 mét.", "d ≥ 100m"),
            ("Hệ số Thời tiết Xấu", "Mưa ướt, trơn trượt: nhân hệ số k = 1.3 - 1.5 (Ví dụ 80km/h: yêu cầu 70m x 1.3 = 91m).", "k = 1.3 - 1.5")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 11: THUẬT TOÁN 4 - CẢNH BÁO VA CHẠM SỚM (TTC)
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "Thuật toán 4: Mô hình Động học Va chạm Time-To-Collision (TTC)", "Phần 3: Thuật toán AI Cốt lõi", 11)

    add_image_or_placeholder(
        s11, "report_assets/fig_ttc_zones_clean.png", Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "SƠ ĐỒ PHÂN VÙNG NGUY HIỂM TIME-TO-COLLISION (TTC)",
        "3 phân vùng cảnh báo động học: Vùng An toàn -> Vùng Cảnh báo -> Vùng Nguy cấp"
    )
    add_side_card(
        s11, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Động Học & Phân Vùng Rủi Ro",
        [
            ("Công thức TTC", "TTC = (d_front - d_buffer) / (v_ego - v_lead) với d_buffer = 2.5m - 3.0m.", "Công thức vàng"),
            ("VÙNG AN TOÀN (TTC > 2.5s)", "Viền xanh lục, cự ly xe đảm bảo, trạng thái lái xe bình thường.", "An toàn"),
            ("VÙNG CẢNH BÁO (1.5s < TTC ≤ 2.5s)", "Viền vàng hổ phách, phát chuông nhắc nhở tài xế giảm chân ga.", "Chú ý"),
            ("VÙNG NGUY CẤP (TTC ≤ 1.5s)", "Viền đỏ nhấp nháy, phát còi hú 1200Hz, ngắt âm thanh để tài xế đạp phanh khẩn cấp.", "Khẩn cấp"),
            ("Cơ sở Sinh học Phản xạ", "Người lái cần 1.0s nhận thức nguy hiểm + 0.5s đạp phanh = 1.5s ngưỡng sống còn.", "1.5s Threshold")
        ],
        badge_color=COLOR_UTH_RED
    )

    # =========================================================================
    # SLIDE 12: THUẬT TOÁN 5 - BIỂN BÁO & POLE SLICING
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "Thuật toán 5: Nhận diện Biển báo QCVN 41 & Cắt lát Cột (Pole Slicing)", "Phần 3: Thuật toán AI Cốt lõi", 12)

    add_image_or_placeholder(
        s12, "report_assets/fig_pole_slicing_clean.png", Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "THUẬT TOÁN CẮT LÁT TỶ LỆ CỘT (POLE PROPORTIONAL SLICING)",
        "Bóc tách đa tầng: Biển cấm chính P.124b -> Biển phụ thời gian S.508 (06:00 - 22:00) -> Biển phụ cảnh báo"
    )
    add_side_card(
        s12, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Bài Toán & Giải Thuật",
        [
            ("Bài toán hóc búa tại VN", "Biển cấm P.124b (cấm rẽ trái/quay đầu) luôn đi kèm biển phụ S.508 '06:00 - 22:00'. Model thường bỏ sót.", "Đặc thù đô thị"),
            ("Lát cắt 1: Biển chính", "Trích xuất phần đỉnh cột, chuẩn hóa kích thước 80x80 INTER_CUBIC (bất biến tỷ lệ).", "Scale-Invariant"),
            ("Lát cắt 2: Biển phụ S.508", "Cắt ROI ở tỷ lệ 0.45 - 0.55 chiều cao cột -> EasyOCR giải mã dải giờ '06:00 - 22:00'.", "Độ chính xác 95.1%"),
            ("Lát cắt 3: Biển cảnh báo", "Định danh biển cảnh báo bổ sung W.245a dưới chân cột.", "Phân cấp"),
            ("Đối chiếu Giờ Thực", "So sánh đồng hồ xe với biển phụ; chỉ cảnh báo khi di chuyển trong khung giờ cấm.", "Chính xác tuyệt đối")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 13: THUẬT TOÁN 6 - ALPR BIỂN SỐ XE VIỆT NAM
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "Thuật toán 6: Quy trình 4 Bước Nhận dạng Biển số xe Việt Nam (ALPR)", "Phần 3: Thuật toán AI Cốt lõi", 13)

    add_image_or_placeholder(
        s13, "report_assets/fig_plate_recognition_pipeline_pro.png", Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "QUY TRÌNH 4 BƯỚC NHẬN DIỆN BIỂN SỐ XE CƠ GIỚI VIỆT NAM (ALPR PIPELINE)",
        "Định vị YOLOv11 -> Nắn thẳng Deskewing -> Cân bằng sáng CLAHE -> EasyOCR & Bộ lọc Regex Thông tư 24"
    )
    add_side_card(
        s13, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "4 Bước Xử Lý Khép Kín",
        [
            ("Bước 1: YOLOv11 Plate", "Huấn luyện trên 4.500 ảnh biển số xe VN; định vị chuẩn ROI cả biển dài và biển vuông.", "mAP 96.5%"),
            ("Bước 2: Deskewing", "Contour Detection tìm 4 góc đỉnh; warpPerspective nắn thẳng góc xiên về 240x80 px.", "Nắn thẳng"),
            ("Bước 3: Adaptive CLAHE", "Cân bằng tương phản thích ứng, khắc phục triệt để lóa đèn pha đêm và nhòe mưa gió.", "Khử lóa sáng"),
            ("Bước 4: OCR & Regex", "EasyOCR + Regex TT 24/2023/TT-BCA tự động sửa lỗi quang học: chuyển '5lH' -> '51H', 'O' -> '0'.", "Độ chính xác 93.5%"),
            ("Tương thích Toàn diện", "Hỗ trợ chuẩn xác cả biển ô tô dài 1 dòng và biển ô tô/xe máy vuông 2 dòng.", "Thông tư 24")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 14: THUẬT TOÁN 7 - GIÁM SÁT NGỦ GẬT (EAR, MAR, PERCLOS)
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    add_header(s14, "Thuật toán 7: Giám sát Trạng thái Tài xế (DMS: EAR, MAR, PERCLOS)", "Phần 3: Thuật toán AI Cốt lõi", 14)

    add_image_or_placeholder(
        s14, "report_assets/fig_ear_mar_clean.png", Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "ĐỒ THỊ BIẾN THIÊN SINH TRẮC HỌC EAR, MAR VÀ NGƯỠNG KÍCH HOẠT CẢNH BÁO DMS",
        "Đặc tả toán học giám sát trạng thái tài xế qua 468 điểm mốc Face Mesh"
    )
    add_side_card(
        s14, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "3 Chỉ Số Sinh Trắc Học Vàng",
        [
            ("MediaPipe 468 Mesh", "Dự đoán 468 điểm mốc 3D trên CPU siêu nhẹ (< 7ms), không cần GPU rời đắt đỏ.", "CPU < 7ms"),
            ("Chỉ số Mí mắt EAR", "EAR = (||p2-p6|| + ||p3-p5||) / (2·||p1-p4||). Mở 0.28-0.35 | EAR < 0.20 (>1.5s): Ngủ gật.", "Độ nhạy 96%"),
            ("Chỉ số Miệng ngáp MAR", "MAR = (||m2-m8|| + ||m3-m7|| + ||m4-m6||) / (2·||m1-m5||). MAR > 0.65 (>1.0s): Ngáp sâu.", "Cảnh báo sớm"),
            ("Tiêu chuẩn PERCLOS 60s", "Tỷ lệ mắt nhắm ≥ 80% trong cửa sổ 1.800 frames (60s ở 30 FPS). Ngưỡng mệt mỏi thể chất > 15%.", "Chuẩn NHTSA/ISO"),
            ("Chống báo động giả", "Loại bỏ hoàn toàn các trường hợp chớp mắt tự nhiên (chớp mắt chỉ mất 0.1 - 0.25 giây).", "Tin cậy")
        ],
        badge_color=COLOR_UTH_RED
    )

    # =========================================================================
    # SLIDE 15: THUẬT TOÁN 8 - TƯ THẾ ĐẦU 3D & KÍNH RÂM
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    add_header(s15, "Thuật toán 8: Ước lượng Tư thế Đầu 3D & Chế độ Kính râm Thông minh", "Phần 3: Thuật toán AI Cốt lõi", 15)

    add_image_or_placeholder(
        s15, None, Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "ẢNH THỰC TẾ: ƯỚC LƯỢNG TƯ THẾ ĐẦU 3D (cv2.solvePnP) & CHẾ ĐỘ SUNGLASSES MODE",
        "Chèn ảnh chụp webcam cabin: nhận diện khuôn mặt tài xế, góc xoay Pitch/Yaw và chế độ đeo kính râm"
    )
    add_side_card(
        s15, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Tư Thế 3D & Kính Râm",
        [
            ("Cân chỉnh Cá nhân 30s", "Ghi nhận mở mắt tự nhiên 15-30s đầu; người mắt một mí không bị báo động giả.", "Cá nhân hóa"),
            ("Chế độ Kính râm Mode", "Khi đeo kính râm che mắt: hạ trọng số EAR về 0, chuyển 100% sang tư thế đầu 3D & MAR.", "Sunglasses Mode"),
            ("Gục đầu ngủ (Pitch < -25°)", "Góc cúi đầu vượt -25° trong > 1.5s -> Cảnh báo ngủ gật nguy cấp đỏ.", "Microsleep"),
            ("Mất tập trung (Yaw > ±30°)", "Quay đầu nhìn sang hai bên hoặc nhìn điện thoại > 2.0s khi xe đang lăn bánh.", "Distraction"),
            ("Còi Hú Thức Tỉnh Tức Thì", "Kích hoạt còi hú tần số cao ngay lập tức khi phát hiện ngủ gật vi mô từ 1.5 - 2.0s.", "Thức tỉnh")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 16: THUẬT TOÁN 9 - DÂY AN TOÀN, MŨ BẢO HIỂM & ĐẾM GIỜ 4H
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    add_header(s16, "Thuật toán 9: Dây an toàn, Mũ bảo hiểm & Đếm giờ Lái xe 4 Giờ", "Phần 3: Thuật toán AI Cốt lõi", 16)

    add_image_or_placeholder(
        s16, None, Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "ẢNH THỰC TẾ: NHẬN DIỆN MŨ BẢO HIỂM XE MÁY & DÂY AN TOÀN TRONG CABIN",
        "Chèn ảnh chụp thực tế: nhận diện người điều khiển xe máy (helmet/no_helmet) và vạt chéo dây an toàn qua ngực"
    )
    add_side_card(
        s16, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "3 Chức Năng Bổ Trợ Cốt Lõi",
        [
            ("Cắt ROI Đầu Người Xe máy", "Trích xuất 25% phía trên Bounding Box xe máy để phân loại helmet / no_helmet.", "Head ROI"),
            ("Khử Trùng Lặp (Deduplication)", "Duy trì tập hợp set(Tracker ID); mỗi đối tượng vi phạm chỉ lập 1 biên bản duy nhất.", "Chống rác dữ liệu"),
            ("Kiểm tra Thắt Dây an toàn", "Nhận diện đường vân chéo dây đai; chỉ kích hoạt khi xe lăn bánh (v > 5 km/h).", "Dây an toàn"),
            ("Đồng hồ Lái xe 4 Giờ", "Điều 65 Luật GTĐB 2008: Cảnh báo nghỉ ngơi khi lái xe liên tục quá 240 phút.", "Luật định 4h"),
            ("Cơ chế Token Phiên Nghỉ", "Dừng đèn đỏ hoặc nghỉ ngắn < 15p: không reset. Chỉ nghỉ đủ ≥ 15 phút mới reset timer.", "Monotonic Timer")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 17: THUẬT TOÁN 10 - ĐỘNG CƠ RA QUYẾT ĐỊNH (DECISION ENGINE)
    # =========================================================================
    s17 = prs.slides.add_slide(blank_layout)
    add_header(s17, "Thuật toán 10: Động cơ Quyết định Cảnh báo (Decision Engine)", "Phần 3: Thuật toán AI Cốt lõi", 17)

    add_image_or_placeholder(
        s17, None, Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "SƠ ĐỒ PHÂN CẤP ƯU TIÊN & BỘ LỌC CHỐNG DỘI (DEBOUNCE FILTER 3.0s)",
        "Kiến trúc Decision Engine giải quyết triệt để hội chứng bão hòa cảnh báo (Alert Fatigue)"
    )
    add_side_card(
        s17, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Phân Tầng & Chống Bão Hòa",
        [
            ("Triệt tiêu Alert Fatigue", "Tài xế sẽ tắt thiết bị nếu bị làm phiền liên tục bởi các cảnh báo vụn vặt không quan trọng.", "Lọc nhiễu"),
            ("MỨC 1: CRITICAL (NGUY CẤP)", "Va chạm TTC ≤ 1.5s, Ngủ gật > 1.5s: Ngắt toàn bộ âm thanh, còi hú 1200Hz, viền đỏ rực.", "Ưu tiên tối cao"),
            ("MỨC 2: WARNING (CẢNH BÁO)", "Sai cự ly TT31, quá tốc độ 5-10 km/h: Viền vàng hổ phách, chuông vừa phải.", "Nhắc nhở vừa"),
            ("MỨC 3: INFO (THÔNG TIN)", "Nhắc dây an toàn khi lăn bánh, gợi ý tốc độ biển báo, nhắc nghỉ 4 giờ.", "Thông tin"),
            ("Bộ lọc Chống Dội (3.0s)", "Tuyệt đối không phát lại các cảnh báo cùng loại trong 3 giây liên tiếp.", "Debounce 3.0s")
        ],
        badge_color=COLOR_UTH_RED
    )

    # =========================================================================
    # SLIDE 18: BẢO MẬT NĐ 13/2023 & BĂM SHA-256
    # =========================================================================
    s18 = prs.slides.add_slide(blank_layout)
    add_header(s18, "Bảo vệ Dữ liệu Cá nhân (NĐ 13/2023/NĐ-CP) & Toàn vẹn Bằng chứng SHA-256", "Phần 3: Thuật toán AI Cốt lõi", 18)

    add_image_or_placeholder(
        s18, None, Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "ẢNH MINH HỌA: LÀM MỜ SELECTIVE GAUSSIAN BLUR & CHỮ KÝ SỐ SHA-256",
        "Minh họa làm mờ mặt người đi bộ và biển số xe không liên quan; lưu vết băm SHA-256 64 ký tự hex"
    )
    add_side_card(
        s18, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Pháp Lý & Kháng Giả Mạo",
        [
            ("Tuân thủ NĐ 13/2023/NĐ-CP", "Bảo vệ dữ liệu cá nhân hình ảnh người đi đường không liên quan đến hành vi vi phạm.", "Pháp lý nghiêm"),
            ("Selective Gaussian Blur", "Tự động phát hiện mặt người và biển số xe khác để làm mờ (kernel k = 31).", "Làm mờ chọn lọc"),
            ("Bảo lưu Xe Vi phạm", "Chỉ duy nhất biển số và thân xe vi phạm chính được giữ nguyên 100% làm bằng chứng.", "Chứng cứ sắc nét"),
            ("Bộ đệm Rolling Buffer", "Tự động trích xuất chuỗi bằng chứng gồm 5 frames trước + 5 frames sau thời điểm vi phạm.", "10 Frames chuỗi"),
            ("Chữ ký số SHA-256 Hash", "Mã băm 64 ký tự hex ghi vào CSDL; mọi can thiệp sửa đổi dù chỉ 1 pixel bị từ chối ngay.", "Kháng Photoshop")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 19: BACKEND FASTAPI & CƠ SỞ DỮ LIỆU
    # =========================================================================
    s19 = prs.slides.add_slide(blank_layout)
    add_header(s19, "Kiến trúc Máy chủ Backend Hiệu năng cao & Cơ sở Dữ liệu 15 Bảng", "Phần 4: Backend & CSDL", 19)

    add_image_or_placeholder(
        s19, "report_assets/fig_database_erd_schema_clean.png", Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "SƠ ĐỒ THỰC THỂ QUAN HỆ CƠ SỞ DỮ LIỆU (DATABASE ERD SCHEMA - 15 BẢNG)",
        "CSDL chuẩn hóa 3NF: vehicles, violations, driving_sessions, trip_events, drivers, organizations..."
    )
    add_side_card(
        s19, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Công Nghệ Backend Cốt Lõi",
        [
            ("FastAPI (Python 3.11)", "Kiến trúc ASGI Event Loop bất đồng bộ, xử lý hàng nghìn kết nối đồng thời với RAM tối thiểu.", "Hiệu năng cao"),
            ("In-Memory OpenCV Decode", "Giải mã luồng ảnh JPEG trực tiếp trong bộ nhớ RAM, triệt tiêu hoàn toàn nghẽn cổ chai đĩa cứng.", "In-Memory"),
            ("WebSocket Full-Duplex", "Hai kênh liên tục: /ws/driving-stream (Road) & /ws/driver-monitor (Cabin). Trễ mạng chỉ 5-12ms.", "Trễ < 12ms"),
            ("CSDL 15 Bảng Chuẩn 3NF", "Quản lý toàn diện vòng đời phương tiện, sự cố vi phạm, chấm điểm tài xế và sức khỏe thiết bị.", "PostgreSQL"),
            ("Bảo mật JWT & RBAC", "Bcrypt + Salt mật khẩu, Token JWT ký số HS256 (12h), phân quyền Admin / Dispatcher / Driver.", "Bảo mật đa lớp")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 20: TỐI ƯU VRAM & TRIỆT TIÊU MEMORY LEAK
    # =========================================================================
    s20 = prs.slides.add_slide(blank_layout)
    add_header(s20, "Tối ưu hóa GPU/RAM & Triệt tiêu Hoàn toàn Lỗi Rò rỉ Bộ nhớ (Memory Leak)", "Phần 4: Backend & CSDL", 20)

    add_image_or_placeholder(
        s20, None, Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "BIỂU ĐỒ ĐO KIỂM: VRAM GPU DUY TRÌ ỔN ĐỊNH 3.2GB SUỐT 120 PHÚT CHỊU TẢI LIÊN TỤC",
        "Minh họa cơ chế with torch.no_grad(), empty_cache() và hàng đợi Bounded Queue triệt tiêu Memory Leak"
    )
    add_side_card(
        s20, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Giải Pháp Kỹ Thuật Triệt Để",
        [
            ("Nguyên nhân VRAM Leak", "PyTorch mặc định lưu đồ thị Autograd; VRAM tăng từ 1.2GB lên > 5.5GB sau 30 phút gây CUDA OOM sập.", "Vấn đề nghiêm trọng"),
            ("Giải pháp torch.no_grad()", "Bao bọc suy luận trong with torch.no_grad() ngăn tạo đồ thị đạo hàm không cần thiết.", "Khắc phục triệt để"),
            ("Giải phóng Cache Định kỳ", "Kích hoạt torch.cuda.empty_cache() và gc.collect() sau mỗi 1.000 frames xử lý.", "VRAM = 3.2GB"),
            ("Bounded Queue (maxlen=2)", "Hàng đợi giới hạn kích thước; tự động drop frame cũ khi nghẽn mạng, không dồn tích lũy trễ.", "Chống ứ đọng"),
            ("Rate Limiting Token Bucket", "Giới hạn 60 req/phút đối với REST và 35 FPS đối với WebSocket streaming, bảo vệ máy chủ.", "An toàn DDoS")
        ],
        badge_color=COLOR_UTH_RED
    )

    # =========================================================================
    # SLIDE 21: GIAO DIỆN WEB DASHBOARD (NEXT.JS 14)
    # =========================================================================
    s21 = prs.slides.add_slide(blank_layout)
    add_header(s21, "Phân hệ Web Dashboard Quản trị Doanh nghiệp (Next.js 14)", "Phần 5: Giao diện Web & Mobile", 21)

    add_image_or_placeholder(
        s21, "report_assets/fig_violation_distribution_clean.png", Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "GIAO DIỆN WEB DASHBOARD: BIỂU ĐỒ VI PHẠM & BỘ XEM LUỒNG KÉP DUAL VIEWPORT",
        "Có thể thay bằng ảnh chụp màn hình thực tế từ Web Dashboard (/live hoặc /dashboard) của dự án"
    )
    add_side_card(
        s21, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Tính Năng Web Quản Trị",
        [
            ("Next.js 14 & Zustand", "Server Components tối ưu SEO, bảo mật; Client Components tương tác thời gian thực.", "Next.js 14"),
            ("Canvas Dựng hình 60 FPS", "HTML5 Canvas vẽ đè Bounding Box mượt mà bằng requestAnimationFrame (độ trễ đồ họa 2ms).", "60 FPS Canvas"),
            ("Dual Viewport Luồng kép", "Hiển thị đồng thời Road Camera (mặt đường) và Cabin Camera (người lái) trên 1 màn hình.", "Kép song song"),
            ("Modal Soi Bằng chứng", "Click vào vi phạm nổi modal ảnh HD, hiển thị GPS, tốc độ, mã băm SHA-256; nút Duyệt/Bác bỏ.", "Đối soát"),
            ("Âm thanh & Giọng nói VN", "Web Audio API còi hú 1200Hz 0ms trễ; Web Speech API phát giọng nói tiếng Việt tự nhiên.", "Âm thanh tiếng Việt")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 22: ỨNG DỤNG DI ĐỘNG HUD (EXPO REACT NATIVE)
    # =========================================================================
    s22 = prs.slides.add_slide(blank_layout)
    add_header(s22, "Ứng dụng Di động HUD Trợ lý Lái xe (Expo React Native)", "Phần 5: Giao diện Web & Mobile", 22)

    add_image_or_placeholder(
        s22, None, Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "ẢNH THỰC TẾ: GIAO DIỆN MOBILE HUD PHẢN QUANG TRÊN KÍNH CHẮN GIÓ BAN ĐÊM",
        "Chèn ảnh chụp màn hình ứng dụng Expo mobile HUD: nền đen OLED Black, đồng hồ số km/h lớn, viền đổi màu"
    )
    add_side_card(
        s22, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Triết Lý Thiết Kế HUD",
        [
            ("Glanceable UI Philosophy", "Tối giản thông tin, chỉ hiển thị 3 chỉ số: Vận tốc lớn, Khoảng cách xe trước và Viền màu. Liếc < 1.0s.", "Không xao nhãng"),
            ("Nền đen OLED Black", "Chuẩn tương phản WCAG 2.1 AA trên nền đen #000000: chống lóa mắt đêm, tiết kiệm pin tối đa.", "OLED Black"),
            ("Đổi màu Viền An toàn", "Xanh lục (An toàn) -> Vàng hổ phách (Chú ý) -> Đỏ nhấp nháy (Nguy cấp va chạm).", "3 Cấp màu"),
            ("Trip State Machine", "Quản lý vòng đời chuyến đi: Khởi hành -> Đang di chuyển -> Dừng nghỉ -> Hoàn thành.", "Máy trạng thái"),
            ("Chấm điểm An toàn (100)", "Thang điểm 100 xếp hạng văn hóa lái xe; rung Haptic Vibration khi phát hiện nguy cấp.", "Safety Score")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 23: MÔI TRƯỜNG THỬ NGHIỆM & DATASET
    # =========================================================================
    s23 = prs.slides.add_slide(blank_layout)
    add_header(s23, "Môi trường Thử nghiệm Chuẩn mực & Bộ Dữ liệu Thực tế Việt Nam", "Phần 6: Thực nghiệm & Đánh giá", 23)

    add_image_or_placeholder(
        s23, None, Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "ẢNH MINH HỌA: 5 KỊCH BẢN MÔI TRƯỜNG GIAO THÔNG VIỆT NAM (15.000+ FRAMES)",
        "Chèn ảnh ghép 5 kịch bản: Ban ngày nắng gắt, Hoàng hôn ngược sáng, Ban đêm thiếu sáng, Trời mưa lớn, Hầm đường bộ"
    )
    add_side_card(
        s23, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Thông Số Đo Kiểm Chuẩn Mực",
        [
            ("Cấu hình Máy chủ AI", "CPU Intel Core i7-12700H (14 cores, 20 threads), GPU NVIDIA RTX 3060 6GB VRAM, RAM 16GB.", "Phần cứng chuẩn"),
            ("Nền tảng Phần mềm", "Ubuntu 22.04 LTS & Windows 11, Python 3.11, CUDA 12.1, PyTorch 2.2, FastAPI, Next.js 14.", "Phần mềm"),
            ("Dataset 15.000+ Frames", "Thu thập từ video hành trình thực tế tại TP.HCM, Quốc lộ 1A, Cao tốc Long Thành - Dầu Giây.", "Quy mô lớn"),
            ("5 Kịch bản Khắc nghiệt", "Nắng gắt, hoàng hôn ngược sáng, đêm thiếu sáng, trời mưa lớn nhòe kính, hầm chui.", "Đa dạng điều kiện"),
            ("Biển số & Biển báo", "4.500 ảnh biển số xe máy/ô tô VN; 3.200 ảnh cụm biển báo phân luồng đô thị QCVN 41.", "Chuyên sâu VN")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 24: KẾT QUẢ BENCHMARK ĐỘ CHÍNH XÁC AI
    # =========================================================================
    s24 = prs.slides.add_slide(blank_layout)
    add_header(s24, "Kết quả Kiểm thử Tự động & Độ chính xác Mô hình AI (mAP Benchmark)", "Phần 6: Thực nghiệm & Đánh giá", 24)

    add_image_or_placeholder(
        s24, "report_assets/fig_ai_benchmark_accuracy_clean.png", Inches(0.9), Inches(1.35), Inches(7.2), Inches(5.2),
        "BIỂU ĐỒ ĐÁNH GIÁ ĐỘ CHÍNH XÁC (mAP, PRECISION, RECALL) 5 TÁC VỤ AI CỐT LÕI",
        "Số liệu thực nghiệm: Phát hiện xe, Nhận diện biển báo, Phát hiện ngủ gật, Biển số xe, Mũ bảo hiểm"
    )
    add_side_card(
        s24, Inches(8.3), Inches(1.35), Inches(4.1), Inches(5.2),
        "Kết Quả Thực Nghiệm Vượt Trội",
        [
            ("90/90 Tests Tự Động", "Vượt qua toàn bộ 90 ca kiểm thử PyTest (Unit & Integration Tests) — đạt 100% Pass Rate.", "100% Pass Rate"),
            ("Phát hiện Xe (Vehicle)", "mAP@0.5 = 94.2%, Precision = 93.8%, Recall = 92.5%. Bắt trọn 4 lớp xe trong mọi thời tiết.", "mAP 94.2%"),
            ("Nhận diện Biển báo (Sign)", "mAP@0.5 = 95.8%, Precision = 96.2%. Thuật toán Pole Slicing bóc tách biển phụ đúng 95.1%.", "mAP 95.8%"),
            ("Giám sát Buồn ngủ (DMS)", "Độ nhạy (Sensitivity) = 96.0%, Đặc hiệu = 95.2%. Phát hiện chuẩn xác 96/100 ca ngủ gật thực tế.", "Độ nhạy 96.0%"),
            ("Biển số xe Việt Nam", "Độ chính xác nhận diện ký tự = 93.5%, Biển số hoàn chỉnh = 91.2% sau khi qua bộ lọc Regex.", "ALPR 93.5%")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # =========================================================================
    # SLIDE 25: ĐỘ TRỄ 38ms & CHỊU TẢI LOCUST
    # =========================================================================
    s25 = prs.slides.add_slide(blank_layout)
    add_header(s25, "Đo kiểm Độ trễ Toàn trình 38ms & Kiểm thử Chịu tải 50 Clients (Locust)", "Phần 6: Thực nghiệm & Đánh giá", 25)

    add_image_or_placeholder(
        s25, "report_assets/fig_module_latency_clean.png", Inches(0.9), Inches(1.35), Inches(5.65), Inches(3.4),
        "BIỂU ĐỒ ĐỘ TRỄ TỪNG MODULE AI (TỔNG PIPELINE = 38ms)",
        "In-Memory (3ms) -> ROI (2ms) -> YOLOv8n (8ms) -> MOT (3ms) -> Speed (2ms) -> Slicing (6ms) -> DMS (7ms) -> Decision (2ms) -> WS (5ms)"
    )
    add_image_or_placeholder(
        s25, "report_assets/fig_locust_stress_test_clean.png", Inches(6.75), Inches(1.35), Inches(5.65), Inches(3.4),
        "BIỂU ĐỒ KIỂM THỬ TẢI LOCUST: 50 STREAM ĐỒNG THỜI TRONG 120 PHÚT",
        "Số liệu tải: 0.00% lỗi gói tin, CPU 68%, VRAM GPU ổn định 3.2GB, duy trì 28-30 FPS liên tục"
    )
    # Bottom 2 Highlight Cards
    card_w = Inches(5.65)
    card_h = Inches(1.7)
    add_card(s25, Inches(0.9), Inches(4.9), card_w, card_h, bg_color=COLOR_WHITE, border_color=COLOR_UTH_TEAL)
    tb = s25.shapes.add_textbox(Inches(1.05), Inches(4.98), card_w - Inches(0.3), card_h - Inches(0.16))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "⚡ ĐỘ TRỄ TOÀN TRÌNH: 38ms (< 50ms TIÊU CHUẨN AN TOÀN)"
    p.font.name = FONT_MAIN
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_UTH_TEAL

    p1 = tf.add_paragraph()
    p1.text = "• Tổng thời gian từ lúc nhận khung hình camera tới khi kích hoạt còi báo chỉ 38ms.\n" \
             "• Thỏa mãn xuất sắc ngưỡng phản xạ an toàn của người lái xe trong các hệ thống ADAS chuyên nghiệp."
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(10.5)
    p1.font.color.rgb = COLOR_BODY_TEXT

    add_card(s25, Inches(6.75), Inches(4.9), card_w, card_h, bg_color=COLOR_WHITE, border_color=COLOR_UTH_RED)
    tb_r = s25.shapes.add_textbox(Inches(6.9), Inches(4.98), card_w - Inches(0.3), card_h - Inches(0.16))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "🏆 ĐỘ ỔN ĐỊNH CẤP DOANH NGHIỆP: 50 CLIENTS / 120 PHÚT"
    p.font.name = FONT_MAIN
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_UTH_RED

    p1 = tf_r.add_paragraph()
    p1.text = "• Tỷ lệ rớt kết nối: 0.00%  |  CPU ổn định 68%  |  Tốc độ xử lý: 28 - 30 FPS.\n" \
             "• VRAM GPU cố định ở mức 3.2GB, chứng minh triệt tiêu 100% rò rỉ bộ nhớ dài hạn."
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(10.5)
    p1.font.color.rgb = COLOR_BODY_TEXT

    # =========================================================================
    # SLIDE 26: SO SÁNH TỔNG KẾT VỚI THỊ TRƯỜNG
    # =========================================================================
    s26 = prs.slides.add_slide(blank_layout)
    add_header(s26, "So sánh Đột phá giữa TrafficGuard và các Giải pháp Hiện hành", "Phần 6: Thực nghiệm & Đánh giá", 26)

    table_shape = s26.shapes.add_table(7, 5, Inches(0.9), Inches(1.35), Inches(11.5), Inches(5.2))
    tbl = table_shape.table
    tbl.columns[0].width = Inches(2.8)
    tbl.columns[1].width = Inches(2.1)
    tbl.columns[2].width = Inches(2.1)
    tbl.columns[3].width = Inches(2.1)
    tbl.columns[4].width = Inches(2.4)

    headers = ["Tiêu chí Kỹ thuật & Nghiệp vụ", "Mobileye Shield+", "Samsara AI Dashcam", "Camera NĐ 10/2020", "TRAFFICGUARD (ĐỀ TÀI)"]
    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_UTH_TEAL if j < 4 else COLOR_UTH_RED
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_MAIN
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

    full_matrix = [
        ("Năng lực AI Biên Thời gian thực", "Có (< 40ms, EyeQ)", "Xử lý Cloud (Trễ)", "Không có (Chụp ảnh tĩnh)", "Có (38ms - Edge AI)"),
        ("Bóc tách Biển phụ Giờ S.508", "Không hỗ trợ", "Không hỗ trợ", "Không hỗ trợ", "Có (Thuật toán Pole Slicing)"),
        ("ALPR Biển số xe máy & ô tô VN", "Không hỗ trợ", "Chỉ biển US / EU", "Không hỗ trợ", "Có (Quy trình 4 bước ALPR)"),
        ("Giám sát Buồn ngủ (DMS) & Dây an toàn", "Có (Bản mở rộng đắt)", "Có (Camera kép)", "Không có", "Có (EAR/MAR/PERCLOS 60s)"),
        ("Chi phí Đầu tư & Thuê bao", "Rất đắt ($1500 - $3000/xe)", "Thuê bao Cloud cao", "Trung bình (Camera thường)", "Tối ưu chi phí / Make in VN"),
        ("Tuân thủ Pháp luật Việt Nam", "Không tương thích TT31", "Không tương thích QCVN41", "Chỉ đáp ứng lưu ảnh", "TT31, QCVN41, NĐ13/2023")
    ]
    for i, row in enumerate(full_matrix):
        for j, val in enumerate(row):
            cell = tbl.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_WHITE if (i % 2 == 0) else COLOR_CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            p.font.name = FONT_MAIN
            p.font.size = Pt(10.5)
            p.font.bold = (j == 4 or j == 0)
            p.font.color.rgb = COLOR_UTH_RED if j == 4 else COLOR_DARK_TEXT

    # =========================================================================
    # SLIDE 27: KẾT LUẬN & ĐÓNG GÓP THỰC TIỄN
    # =========================================================================
    s27 = prs.slides.add_slide(blank_layout)
    add_header(s27, "Kết luận & Giá trị Đóng góp Thực tiễn của Đồ án Nghiên cứu", "Phần 6: Thực nghiệm & Đánh giá", 27)

    # 4 Big Result Cards (2x2 Grid)
    cw = Inches(5.65)
    ch = Inches(2.5)

    card_concl = [
        ("01. HOÀN THÀNH 100% MỤC TIÊU NGHIÊN CỨU",
         "• Xây dựng thành công hệ sinh thái Make in Vietnam hoàn chỉnh: 12 Module AI Core, máy chủ FastAPI, Web Next.js 14 Canvas 60 FPS và Mobile App Expo HUD.\n"
         "• Hoàn toàn tự chủ mã nguồn, không phụ thuộc vào nền tảng đóng kín của nước ngoài.",
         COLOR_UTH_TEAL),
        ("02. ĐÓNG GÓP HỌC THUẬT & GIẢI THUẬT NỔI BẬT",
         "• Thuật toán Pole Proportional Slicing bóc tách chính xác biển phụ thời gian S.508 trong cụm biển QCVN 41.\n"
         "• Mô hình Homography ước tính vận tốc tức thời sai số chỉ ± 2.5 km/h.\n"
         "• Giám sát DMS đa chỉ số (EAR + MAR + PERCLOS 60s) chạy mượt mà trên CPU < 7ms.",
         COLOR_UTH_RED),
        ("03. ĐỘ TIN CẬY & HIỆU NĂNG ĐẠT CHUẨN DOANH NGHIỆP",
         "• Vượt qua 90/90 kiểm thử tự động PyTest (100% Pass Rate).\n"
         "• Tổng độ trễ toàn trình đạt 38ms (thỏa mãn tiêu chuẩn an toàn phản xạ < 50ms của ADAS).\n"
         "• Kiểm thử chịu tải 50 clients trong 120 phút liên tục với 0.00% lỗi và triệt tiêu hoàn toàn VRAM leak.",
         COLOR_WARNING),
        ("04. GIÁ TRỊ ỨNG DỤNG THỰC TIỄN & XÃ HỘI",
         "• Sẵn sàng chuyển giao cho các hợp tác xã vận tải, doanh nghiệp logistics và xe khách liên tỉnh.\n"
         "• Góp phần giảm thiểu tai nạn giao thông thảm khốc do ngủ gật và không giữ khoảng cách an toàn, bảo vệ tính mạng nhân dân.",
         COLOR_SUCCESS)
    ]

    for idx, (ctitle, cdesc, ccolor) in enumerate(card_concl):
        col = idx % 2
        row = idx // 2
        l = Inches(0.9) if col == 0 else Inches(6.75)
        t = Inches(1.35) + row * Inches(2.65)

        add_card(s27, l, t, cw, ch, bg_color=COLOR_WHITE, border_color=ccolor)
        tb = s27.shapes.add_textbox(l + Inches(0.18), t + Inches(0.14), cw - Inches(0.36), ch - Inches(0.28))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p = tf.paragraphs[0]
        p.text = ctitle
        p.font.name = FONT_MAIN
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = ccolor

        p1 = tf.add_paragraph()
        p1.space_before = Pt(6)
        p1.text = cdesc
        p1.font.name = FONT_MAIN
        p1.font.size = Pt(10.5)
        p1.font.color.rgb = COLOR_BODY_TEXT

    # =========================================================================
    # SLIDE 28: HƯỚNG PHÁT TRIỂN & Q&A
    # =========================================================================
    s28 = prs.slides.add_slide(blank_layout)
    add_header(s28, "Hướng phát triển Tương lai & Phiên Hỏi đáp (Q&A)", "Lời Cảm ơn & Hỏi đáp", 28)

    # Left: Future work
    add_side_card(
        s28, Inches(0.9), Inches(1.35), Inches(5.65), Inches(5.2),
        "3 Hướng Phát Triển Mở Rộng",
        [
            ("1. Đo Nhịp tim Từ xa qua Camera (rPPG)", "Ứng dụng Remote Photoplethysmography phân tích vi biến thiên màu da mặt để phát hiện sớm kiệt sức, nhồi máu cơ tim.", "rPPG Y tế"),
            ("2. Cảnh báo Liên xe Đám mây (V2X Cloud)", "Kết nối mạng lưới xe qua MQTT/Kafka; chia sẻ tức thì xe trước phanh gấp, mặt đường sạt lở cho các xe phía sau.", "V2X Cloud"),
            ("3. Đóng gói Chip Nhúng Biên Chuyên dụng", "Biên dịch mô hình sang TensorRT và chạy trực tiếp trên kit nhúng giá rẻ như NVIDIA Jetson Orin Nano / Raspberry Pi 5.", "Edge NPU")
        ],
        badge_color=COLOR_UTH_TEAL
    )

    # Right: Thank you card
    add_card(s28, Inches(6.75), Inches(1.35), Inches(5.65), Inches(5.2), bg_color=COLOR_WHITE, border_color=COLOR_UTH_RED)
    tb_r = s28.shapes.add_textbox(Inches(6.9), Inches(1.7), Inches(5.35), Inches(4.5))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p = tf_r.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "CHÂN THÀNH CẢM ƠN QUÝ THẦY CÔ!"
    p.font.name = FONT_MAIN
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_UTH_RED

    p1 = tf_r.add_paragraph()
    p1.space_before = Pt(12)
    p1.alignment = PP_ALIGN.CENTER
    p1.text = "Tập thể nhóm tác giả xin trân trọng gửi lời tri ân sâu sắc đến ThS. Hàn Trung Định – Giảng viên hướng dẫn, cùng toàn thể quý Thầy, Cô giáo trong Hội đồng Khoa học Viện Công nghệ Thông tin và Điện, Điện tử – Trường Đại học Giao thông Vận tải TP. Hồ Chí Minh (UTH)."
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(12)
    p1.font.color.rgb = COLOR_BODY_TEXT

    p2 = tf_r.add_paragraph()
    p2.space_before = Pt(18)
    p2.alignment = PP_ALIGN.CENTER
    p2.text = "PHIÊN HỎI ĐÁP & BẢO VỆ ĐỀ TÀI\n(Q&A SESSION)"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(17)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_UTH_TEAL

    p3 = tf_r.add_paragraph()
    p3.space_before = Pt(12)
    p3.alignment = PP_ALIGN.CENTER
    p3.text = "Kính mời quý Thầy/Cô trong Hội đồng đặt câu hỏi và đóng góp ý kiến để đề tài được hoàn thiện hơn nữa!"
    p3.font.name = FONT_MAIN
    p3.font.size = Pt(12)
    p3.font.italic = True
    p3.font.color.rgb = COLOR_MUTED_TEXT

    # =========================================================================
    # SAVE FILES
    # =========================================================================
    output_filename = "Bao_Cao_Thuyet_Trinh_TrafficGuard_UTH.pptx"
    prs.save(output_filename)
    prs.save("745545451-Slide-UTH.pptx")
    print(f"Successfully generated Visual-First Presentation deck! Saved to both '{output_filename}' and '745545451-Slide-UTH.pptx'.")

if __name__ == '__main__':
    build_presentation()
