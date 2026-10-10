import os
import sys
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCX_OUT = Path("docs/reports/BAO_CAO_DO_AN_TRAFFICGUARD_90_TRANG.docx")
ASSETS_DIR = Path("report_assets")
DOCX_OUT.parent.mkdir(parents=True, exist_ok=True)

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_title_page(doc):
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_inst = p_inst.add_run("BỘ GIÁO DỤC VÀ ĐÀO TẠO\nTRƯỜNG ĐẠI HỌC BÁCH KHOA / CÔNG NGHỆ THÔNG TIN\nKHOA KHOA HỌC & KỸ THUẬT MÁY TÍNH\n***")
    r_inst.font.name = "Times New Roman"
    r_inst.font.size = Pt(13)
    r_inst.font.bold = True
    r_inst.font.color.rgb = RGBColor(15, 23, 42)
    p_inst.paragraph_format.space_after = Pt(40)
    
    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_title.add_run("BÁO CÁO ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC\n\n")
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(16)
    r_sub.font.bold = True
    r_sub.font.color.rgb = RGBColor(30, 58, 138)
    
    r_main = p_title.add_run("NGHIÊN CỨU, THIẾT KẾ VÀ HIỆN THỰC HÓA HỆ THỐNG TRỢ LÝ LÁI XE THÔNG MINH VÀ GIÁM SÁT AN TOÀN ĐỘI XE TÍCH HỢP TRÍ TUỆ NHÂN TẠO\n(TRAFFICGUARD PLATFORM)")
    r_main.font.name = "Times New Roman"
    r_main.font.size = Pt(18)
    r_main.font.bold = True
    r_main.font.color.rgb = RGBColor(15, 44, 89)
    p_title.paragraph_format.space_after = Pt(60)
    
    # Info box
    p_info = doc.add_paragraph()
    p_info.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_info.paragraph_format.left_indent = Inches(1.5)
    
    runs_info = [
        ("Chuyên ngành:", " Công nghệ Phần mềm & Trí tuệ Nhân tạo\n"),
        ("Giảng viên hướng dẫn:", " TS. Nguyễn Văn A\n"),
        ("Sinh viên thực hiện:", " Nguyễn Quốc Trí\n"),
        ("Mã số sinh viên:", " 2020xxxx\n"),
        ("Lớp khóa học:", " Khoa học Máy tính K65\n"),
        ("Niên khóa:", " 2022 - 2026\n")
    ]
    for label, val in runs_info:
        r1 = p_info.add_run(label)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(12)
        r1.font.bold = True
        r2 = p_info.add_run(val)
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(12)
        
    p_info.paragraph_format.space_after = Pt(80)
    
    # Date
    p_date = doc.add_paragraph()
    p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_date = p_date.add_run("TP. HỒ CHÍ MINH — NĂM 2026")
    r_date.font.name = "Times New Roman"
    r_date.font.size = Pt(12)
    r_date.font.bold = True
    
    doc.add_page_break()

def add_preface(doc):
    # Cam doan
    h_cd = doc.add_paragraph()
    r_cd = h_cd.add_run("LỜI CAM ĐOAN")
    r_cd.font.name = "Times New Roman"
    r_cd.font.size = Pt(16)
    r_cd.font.bold = True
    r_cd.font.color.rgb = RGBColor(15, 44, 89)
    h_cd.paragraph_format.space_after = Pt(12)
    
    p = doc.add_paragraph()
    p.add_run("Tôi xin cam đoan đây là công trình nghiên cứu và phát triển phần mềm độc lập do chính tôi thực hiện dưới sự hướng dẫn khoa học của Giảng viên hướng dẫn. Toàn bộ các số liệu, giải thuật, kết quả phân tích trong báo cáo là trung thực, phản ánh đúng mã nguồn thực tế của hệ thống TrafficGuard. Các nội dung tham khảo từ các tài liệu khoa học, luật giao thông đường bộ và các thư viện mã nguồn mở đều được trích dẫn nguồn đầy đủ theo đúng quy định học thuật.")
    p.paragraph_format.space_after = Pt(18)
    
    # Cam on
    h_co = doc.add_paragraph()
    r_co = h_co.add_run("LỜI CẢM ƠN")
    r_co.font.name = "Times New Roman"
    r_co.font.size = Pt(16)
    r_co.font.bold = True
    r_co.font.color.rgb = RGBColor(15, 44, 89)
    h_co.paragraph_format.space_after = Pt(12)
    
    p2 = doc.add_paragraph()
    p2.add_run("Lời đầu tiên, em xin bày tỏ lòng biết ơn sâu sắc nhất tới toàn thể các Thầy Cô giáo trong Khoa Công nghệ Thông tin đã tận tình truyền đạt những kiến thức quý báu và rèn luyện tư duy nghiên cứu cho em trong suốt những năm tháng học tập tại trường.\n\nĐặc biệt, em xin gửi lời cảm ơn chân thành và sâu sắc nhất tới Thầy hướng dẫn đã luôn định hướng, tận tình chỉ bảo, động viên và góp ý những ý kiến chuyên môn sâu sắc giúp em hoàn thiện đồ án này.\n\nSau cùng, con xin gửi lời cảm ơn vô hạn tới gia đình và bạn bè đã luôn là điểm tựa vững chắc, đồng hành và ủng hộ con trong suốt quá trình hoàn thành chương trình đại học.")
    p2.paragraph_format.space_after = Pt(18)
    
    doc.add_page_break()

def add_abstracts(doc):
    # VN
    h_vn = doc.add_paragraph()
    r_vn = h_vn.add_run("TÓM TẮT ĐỀ TÀI")
    r_vn.font.name = "Times New Roman"
    r_vn.font.size = Pt(16)
    r_vn.font.bold = True
    r_vn.font.color.rgb = RGBColor(15, 44, 89)
    
    p_vn = doc.add_paragraph()
    p_vn.add_run("Tai nạn giao thông đường bộ tại Việt Nam vẫn đang là vấn đề nhức nhối với tỷ lệ tử vong cao mà nguyên nhân chính xuất phát từ hành vi chủ quan của người lái xe như: ngủ gật khi lái xe đường dài/ban đêm, không giữ cự ly an toàn theo Thông tư 31/2019/TT-BGTVT, vi phạm tốc độ và không chấp hành biển báo giao thông phụ theo khung giờ. Nhằm giải quyết các bài toán trên một cách toàn diện và chi phí thấp, đề tài này tập trung nghiên cứu, thiết kế và hiện thực hóa Hệ thống trợ lý lái xe thông minh và giám sát an toàn đội xe tích hợp Trí tuệ Nhân tạo (TrafficGuard).\n\n"
                 "Hệ thống bao gồm 4 phân hệ chính: (1) Lõi xử lý AI thời gian thực tích hợp 12 module phân tích song song luồng camera mặt đường (Road Vision) và camera cabin (DMS), có khả năng bám vết phương tiện, đo vận tốc qua ma trận Homography, kiểm tra khoảng cách an toàn, nhận diện biển báo QCVN 41:2019 (kèm biển phụ theo giờ S.508), nhận diện biển số xe cơ giới Việt Nam, phát hiện ngủ gật qua MediaPipe Face Mesh (EAR, MAR, PERCLOS) và kiểm tra thắt dây an toàn; (2) Máy chủ Backend doanh nghiệp hiệu năng cao viết bằng FastAPI với cơ chế xác thực JWT, phân quyền RBAC 3 vai trò (Quản trị viên, Điều độ viên, Tài xế) và truyền phát WebSocket độ trễ thấp; (3) Giao diện Web Dashboard quản trị trung tâm xây dựng trên Next.js 14 với Canvas hiển thị 60 FPS, hệ thống âm thanh còi báo và giọng nói tiếng Việt chuẩn tự nhiên; (4) Ứng dụng di động HUD (Expo React Native) hỗ trợ tài xế lái xe an toàn trên đường.\n\n"
                 "Kết quả thực nghiệm trên môi trường thử nghiệm cho thấy toàn bộ hệ thống vượt qua 90/90 kiểm thử tự động (100% pass rate), đạt độ chính xác phát hiện phương tiện 94.2%, nhận diện biển báo 95.8%, độ nhạy ngủ gật 96.0% với độ trễ toàn trình chỉ 38ms (thỏa mãn yêu cầu khắt khe < 50ms của hệ thống an toàn giao thông). Đề tài mang lại giải pháp công nghệ có tính ứng dụng thực tiễn cao cho các doanh nghiệp logistic, vận tải hành khách và cơ quan quản lý giao thông tại Việt Nam.")
    p_vn.paragraph_format.space_after = Pt(20)
    
    # EN
    h_en = doc.add_paragraph()
    r_en = h_en.add_run("ABSTRACT")
    r_en.font.name = "Times New Roman"
    r_en.font.size = Pt(16)
    r_en.font.bold = True
    r_en.font.color.rgb = RGBColor(15, 44, 89)
    
    p_en = doc.add_paragraph()
    p_en.add_run("Road traffic accidents in Vietnam continue to pose severe social and economic challenges, primarily caused by subjective driver errors such as micro-sleep during nighttime trips, failure to maintain safe headways pursuant to Circular 31/2019/TT-BGTVT, speeding, and ignoring time-restricted auxiliary signs. To address these problems through an integrated, low-cost platform, this thesis presents the research, design, and implementation of the 'Smart Driving Assistant and Enterprise Fleet Safety Platform' (TrafficGuard).\n\n"
                 "The platform comprises four major subsystems: (1) A real-time AI core pipeline featuring 12 modules processing synchronized road camera and cabin DMS streams—capable of multi-object tracking, homography-based vehicle speed estimation, safe following distance calculation, Vietnamese QCVN 41:2019 traffic sign recognition (including auxiliary time sign S.508), Vietnamese license plate OCR, drowsiness monitoring via MediaPipe Face Mesh (EAR, MAR, PERCLOS), and seatbelt posture verification; (2) An enterprise-grade asynchronous backend powered by FastAPI, featuring JWT authentication, role-based access control (RBAC with Admin, Dispatcher, Driver roles), and low-latency WebSocket event streaming; (3) A Next.js 14 web monitoring dashboard equipped with 60 FPS Canvas overlay, acoustic alarms, and natural Vietnamese speech synthesis; and (4) An Expo React Native HUD mobile assistant for drivers.\n\n"
                 "Empirical testing verifies that the system passes 100% of automated unit and regression tests (90/90 cases), achieving 94.2% vehicle detection mAP, 95.8% sign recognition accuracy, 96.0% drowsiness sensitivity, and an end-to-end latency of only 38 ms (<50 ms threshold). TrafficGuard offers a robust, cost-effective, and regulation-compliant solution for commercial logistics fleets and public transportation authorities in Vietnam.")
    
    doc.add_page_break()

def add_abbreviations(doc):
    h = doc.add_paragraph()
    r = h.add_run("DANH MỤC CÁC TỪ VIẾT TẮT")
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.color.rgb = RGBColor(15, 44, 89)
    h.paragraph_format.space_after = Pt(14)
    
    abbrs = [
        ("ADAS", "Advanced Driver Assistance Systems", "Hệ thống hỗ trợ người lái xe nâng cao"),
        ("DMS", "Driver Monitoring System", "Hệ thống giám sát trạng thái tài xế trong cabin"),
        ("FCW", "Forward Collision Warning", "Hệ thống cảnh báo nguy cơ va chạm phía trước"),
        ("LDWS", "Lane Departure Warning System", "Hệ thống cảnh báo chệch làn đường"),
        ("TTC", "Time-To-Collision", "Thời gian ước tính tới điểm va chạm tiềm ẩn"),
        ("EAR", "Eye Aspect Ratio", "Tỷ lệ co giãn mở mí mắt dựa trên điểm mốc hình học"),
        ("MAR", "Mouth Aspect Ratio", "Tỷ lệ mở miệng (phát hiện ngáp ngủ)"),
        ("PERCLOS", "Percentage of Eye Closure", "Tỷ lệ phần trăm thời gian nhắm mắt trong cửa sổ trượt 60 giây"),
        ("YOLO", "You Only Look Once", "Họ mô hình phát hiện vật thể học sâu tốc độ thời gian thực"),
        ("OCR", "Optical Character Recognition", "Nhận dạng ký tự quang học"),
        ("MOT", "Multi-Object Tracking", "Bám vết đa đối tượng chuyển động liên tục"),
        ("RBAC", "Role-Based Access Control", "Kiểm soát truy cập dựa trên vai trò người dùng"),
        ("FPS", "Frames Per Second", "Số khung hình xử lý được trong một giây"),
        ("IoU", "Intersection over Union", "Tỷ số diện tích giao trên diện tích hợp"),
        ("mAP", "mean Average Precision", "Độ chính xác trung bình trung bình của mô hình phát hiện"),
        ("CLAHE", "Contrast Limited Adaptive Histogram Equalization", "Cân bằng sáng thích ứng giới hạn tương phản"),
        ("QCVN", "Quy chuẩn Việt Nam", "Quy chuẩn kỹ thuật quốc gia (QCVN 41:2019/BGTVT)")
    ]
    
    table = doc.add_table(rows=len(abbrs) + 1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    headers = ["Ký hiệu viết tắt", "Thuật ngữ Tiếng Anh", "Ý nghĩa / Giải thích Tiếng Việt"]
    widths = [Inches(1.2), Inches(2.3), Inches(3.0)]
    
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "1E3A8A")
        set_cell_margins(hdr_cells[i], 120, 120, 150, 150)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(10.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            
    for row_idx, data in enumerate(abbrs):
        row_cells = table.rows[row_idx + 1].cells
        bg_col = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(data):
            row_cells[col_idx].text = text
            set_cell_background(row_cells[col_idx], bg_col)
            set_cell_margins(row_cells[col_idx], 80, 80, 120, 120)
            p = row_cells[col_idx].paragraphs[0]
            if col_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(10)
                if col_idx == 0:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(30, 58, 138)
                    
    doc.add_page_break()

print("Common front matter generated.")
