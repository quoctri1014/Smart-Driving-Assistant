import sys
import time
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

OUT_DOCX = Path("docs/reports/SO_TAY_TAT_CA_HINH_ANH_VA_SO_DO_DO_AN.docx")
ASSETS_DIR = Path("report_assets")
OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_code_box(doc, code_str, title="MÃ NGUỒN VẼ TRÊN DRAW.IO / MERMAID"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.rows[0].cells[0]
    cell.width = Inches(6.5)
    set_cell_background(cell, "F1F5F9")
    set_cell_margins(cell, top=120, bottom=120, left=160, right=160)
    
    p = cell.paragraphs[0]
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(2)
    
    r_ti = p.add_run(f"💻 {title}:\n")
    r_ti.font.name = "Times New Roman"
    r_ti.font.size = Pt(10)
    r_ti.font.bold = True
    r_ti.font.color.rgb = RGBColor(30, 58, 138)
    
    r_co = p.add_run(code_str)
    r_co.font.name = "Consolas"
    r_co.font.size = Pt(8.5)
    r_co.font.color.rgb = RGBColor(15, 23, 42)
    
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_after = Pt(4)

def add_image_item(doc, img_path, caption, description, rules, code_str=None):
    # Caption / Title
    p_ti = doc.add_paragraph()
    p_ti.paragraph_format.space_before = Pt(14)
    p_ti.paragraph_format.space_after = Pt(4)
    p_ti.paragraph_format.keep_with_next = True
    
    r_ti = p_ti.add_run(caption)
    r_ti.font.name = "Times New Roman"
    r_ti.font.size = Pt(12.5)
    r_ti.font.bold = True
    r_ti.font.color.rgb = RGBColor(15, 44, 89)
    
    # Description
    p_desc = doc.add_paragraph()
    p_desc.paragraph_format.line_spacing = 1.2
    p_desc.paragraph_format.space_after = Pt(4)
    r_d1 = p_desc.add_run("• Mô tả nội dung hình ảnh: ")
    r_d1.font.bold = True
    p_desc.add_run(description)
    
    # Rules
    p_rule = doc.add_paragraph()
    p_rule.paragraph_format.line_spacing = 1.2
    p_rule.paragraph_format.space_after = Pt(6)
    r_r1 = p_rule.add_run("• Quy tắc chống che khuất (Non-Obscuring): ")
    r_r1.font.bold = True
    r_r1.font.color.rgb = RGBColor(180, 83, 9)
    p_rule.add_run(rules)
    
    # Image if exists
    if img_path and Path(img_path).exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(8)
        run_img = p_img.add_run()
        run_img.add_picture(str(img_path), width=Inches(6.0))
        
    # Code box if diagram
    if code_str:
        add_code_box(doc, code_str)

def main():
    print("Tao tai lieu Word chuyen biet ve hinh anh va so do...")
    doc = Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.79)
        section.bottom_margin = Inches(0.79)
        section.left_margin = Inches(1.18)
        section.right_margin = Inches(0.79)
        
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("TRAFFICGUARD | SỔ TAY TOÀN BỘ HÌNH ẢNH & SƠ ĐỒ ĐỒ ÁN 90 TRANG")
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(100, 116, 139)
        hrun.font.italic = True

    # Title
    p_main = doc.add_paragraph()
    p_main.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p_main.add_run("SỔ TAY TOÀN BỘ HÌNH ẢNH, SƠ ĐỒ & MÃ DIAGRAM\n")
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(16)
    r1.font.bold = True
    r1.font.color.rgb = RGBColor(30, 58, 138)
    
    r2 = p_main.add_run("BÁO CÁO ĐỒ ÁN TỐT NGHIỆP: HỆ THỐNG TRỢ LÝ LÁI XE THÔNG MINH TRAFFICGUARD\n")
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(13)
    r2.font.bold = True
    r2.font.color.rgb = RGBColor(15, 44, 89)
    p_main.paragraph_format.space_after = Pt(20)

    # 1. Safe distance clean
    add_image_item(
        doc,
        "report_assets/fig_safe_distance_clean.png",
        "Hình 2.6: Đồ thị Quy định Khoảng cách An toàn theo Thông tư 31/2019/TT-BGTVT",
        "Biểu đồ đường bậc thang thể hiện cự ly an toàn tối thiểu theo luật Việt Nam ở điều kiện đường khô và trời mưa trơn trượt (hệ số x1.30).",
        "Khoảng cách đệm và nhãn chú thích được đưa lên các vùng trống ở góc trên, có đường dẫn mũi tên thanh mảnh trỏ vào bậc thang, tuyệt đối không đè lên đường đồ thị."
    )

    # 2. Accuracy clean
    add_image_item(
        doc,
        "report_assets/fig_ai_benchmark_accuracy_clean.png",
        "Hình 7.1: Biểu đồ Đánh giá Độ chính xác 5 Tác vụ AI Cốt lõi",
        "Biểu đồ cột nhóm so sánh chỉ số mAP@0.5, Precision và Recall của 5 tác vụ: Phát hiện xe, Biển báo QCVN 41, Biển số xe OCR, Giám sát ngủ gật và Mũ bảo hiểm.",
        "Trần đồ thị nâng lên mức 104% để toàn bộ số liệu phần trăm nằm ngay ngắn phía trên cột mà không bị chạm khung hoặc đè lên chú giải."
    )

    # 3. Latency clean
    add_image_item(
        doc,
        "report_assets/fig_module_latency_clean.png",
        "Hình 7.2: Biểu đồ Đo lường Độ trễ Suy luận Từng Module AI (Tổng Pipeline = 38ms)",
        "Biểu đồ thanh ngang thể hiện thời gian thực thi (ms) của 10 module, chứng minh tổng độ trễ toàn trình đạt 38ms (thỏa mãn yêu cầu khắt khe < 50ms của hệ thống an toàn giao thông).",
        "Các nhãn thời gian đặt bên ngoài đầu mút của thanh ngang với khoảng cách 5px, không bị chèn vào nền màu."
    )

    # 4. Violation distribution clean
    add_image_item(
        doc,
        "report_assets/fig_violation_distribution_clean.png",
        "Hình 6.3: Biểu đồ Cơ cấu Các loại Lỗi Vi phạm An toàn Giao thông Toàn Đội xe",
        "Biểu đồ hình vành khuyên (Donut Chart) thể hiện cơ cấu 5 lỗi vi phạm giao thông ghi nhận từ dữ liệu telemetry.",
        "Toàn bộ nhãn tên lỗi dài được tách riêng sang bảng Chú giải (Legend) ở cột bên phải ngoài biểu đồ, trên các lát cắt chỉ để số phần trăm màu trắng tương phản cao."
    )

    # 5. EAR MAR clean
    add_image_item(
        doc,
        "report_assets/fig_ear_mar_clean.png",
        "Hình 2.3: Đồ thị Sinh trắc học Biến thiên EAR và MAR theo Thời gian",
        "Hai đồ thị sóng song song thể hiện chỉ số mở mắt EAR tụt xuống dưới ngưỡng 0.20 khi nhắm mắt và chỉ số MAR vượt ngưỡng 0.65 khi ngáp ngủ.",
        "Các hộp thông báo báo động đặt lệch ở góc thoáng, mũi tên chỉ dẫn trỏ chính xác vào đáy sóng mà không che khuất dữ liệu."
    )

    # 5b. Homography clean (Hình người dùng yêu cầu)
    add_image_item(
        doc,
        "report_assets/fig_homography_transformation_clean.png",
        "Hình 2.4: Toán học Biến đổi Phối cảnh (Homography) để Đo Khoảng cách & Vận tốc",
        "Sơ đồ trực quan hóa quá trình ánh xạ từ Góc nhìn phối cảnh camera 2D (Hình thang, điểm ảnh u, v) sang Mặt phẳng đường từ trên cao Bird's Eye View (Hình chữ nhật, kích thước thực tế L = 20.0m, W = 3.5m) thông qua Ma trận Homography H (3x3).",
        "Toàn bộ khối văn bản bên trong hình thang và hình chữ nhật được căn giữa cách đều các cạnh, hoàn toàn không bị đè lên đường viền hay che các điểm góc."
    )

    # 6. TTC Zones
    add_image_item(
        doc,
        "report_assets/fig_ttc_zones_clean.png",
        "Hình 2.5: Đồ thị Phân vùng Thời gian Va chạm Tiềm ẩn (Time-To-Collision - TTC)",
        "Đồ thị đường cong TTC theo khoảng cách xe và vận tốc tương đối, phân chia 3 vùng an toàn: Đỏ (Nguy cấp TTC <= 1.5s), Vàng (Chú ý 1.5s - 3.0s), Xanh lá (An toàn > 3.0s).",
        "Các vùng an toàn được tô màu nền pastel trong suốt, đường đồ thị có độ dày 2.4px nổi bật rõ ràng."
    )

    # 7. Pole slicing clean
    add_image_item(
        doc,
        "report_assets/fig_pole_slicing_clean.png",
        "Hình 4.6: Sơ đồ Thuật toán Cắt lát Tỷ lệ Cột Biển báo (Pole Proportional Slicing)",
        "Minh họa bóc tách cụm 3 biển báo trên cùng 1 cột: Biển cấm quay đầu và rẽ trái P.124b, Biển phụ thời gian cấm 6:00-22:00 S.508 và Biển cảnh báo W.245a.",
        "Toàn bộ 3 hộp giải thích thuật toán được kéo hẳn sang nửa bên phải của hình ảnh, dùng 3 mũi tên trỏ sang cột biển báo bên trái, không đè chữ lên mặt biển."
    )

    # 8. QCVN signs sample
    add_image_item(
        doc,
        "report_assets/fig_qcvn_signs_sample.png",
        "Hình 4.7: Mẫu Bộ Dữ liệu Biển báo Giao thông QCVN 41:2019/BGTVT Đã Huấn luyện",
        "Lưới 2x4 hiển thị 8 mẫu biển báo giao thông sắc nét chuẩn QCVN 41: P.101, P.102, P.103a, P.104, P.105, DP.135, I.401, I.402.",
        "Mỗi biển báo có tiêu đề và mã số đặt ngay ngắn ở phía trên, khoảng cách giữa các ô là 15px không bị dính vào nhau."
    )

    # 9. Architecture diagram with Mermaid code
    code_arch = """flowchart TD
    subgraph T1["TẦNG 1: THU THẬP DỮ LIỆU & THIẾT BỊ BIÊN"]
        C1["IP Dashcam 1080p"] & C2["Cabin Camera DMS"] & C3["Mobile App Stream"]
    end
    subgraph T2["TẦNG 2: LÕI AI 12 MODULE PIPELINE"]
        ROAD["Road Vision: YOLOv8, MOT, Homography Speed, Safe Distance TT31, Sign QCVN 41"]
        CABIN["Cabin DMS: MediaPipe 468 mesh, EAR/MAR, PERCLOS 60s, Eyes Closed"]
        SHED["Load Shedder & Image Quality Gate"] --> ROAD & CABIN
    end
    subgraph T3["TẦNG 3: MÁY CHỦ BACKEND & CSDL (FASTAPI)"]
        API["FastAPI REST (13 Routers)"] & WS["WebSocket Dispatcher (< 38ms)"]
        DEC["Decision Engine"] & ANON["Privacy Blur & SHA-256"]
        DB[("15 Bảng SQLAlchemy")] & STORE[("/storage/")]
        API & WS --- DEC --- DB & STORE
    end
    subgraph T4["TẦNG 4: GIAO DIỆN & TRỢ LÝ ĐIỀU HÀNH"]
        WEB["Next.js 14 Web Canvas 60fps"] & MOB["Expo HUD Speedometer"] & VOICE["Web Speech Tiếng Việt"]
    end
    T1 ==> T2 ==> T3 ==> T4"""
    
    add_image_item(
        doc,
        "report_assets/fig_system_architecture.png",
        "Hình 3.1: Sơ đồ Kiến trúc Tổng thể 4 Tầng của Nền tảng TrafficGuard",
        "Kiến trúc phân tầng chuẩn doanh nghiệp kết nối từ thiết bị camera biên, qua lõi AI 12 module, máy chủ FastAPI và giao diện Web/Mobile.",
        "Các khối tầng được phân biệt bằng màu sắc riêng biệt (Xanh dương, Xanh lá, Tím, Vàng), luồng dữ liệu biểu thị bằng mũi tên to rõ ràng.",
        code_arch
    )

    # 10. Sequence diagram WS code
    code_ws = """sequenceDiagram
    autonumber
    Client as Web Canvas / Mobile App
    WS as WebSocket Endpoint (/ws/driving-stream)
    AI as 12 Module AI Pipeline
    DB as Database & Evidence Storage

    Client->>WS: Bắt tay kết nối (101 Switching Protocols)
    loop Mỗi khung hình (30 FPS)
        Client->>WS: Gửi Binary JPEG Frame
        WS->>AI: Giải mã In-Memory & Chạy 12 Module
        AI-->>WS: Kết quả: Bounding Boxes, Tốc độ, Cự ly, FCW Alert
        WS-->>Client: Phản hồi JSON Telemetry (Độ trễ ~38ms)
        Client->>Client: Vẽ đè Bounding Boxes lên Canvas 60 FPS
        opt Khi phát hiện Vi phạm
            AI->>DB: Ghi bản ghi vi phạm & Lưu ảnh băm SHA-256
            WS-->>Client: Kích hoạt cờ CRITICAL ALERT
            Client->>Client: Phát còi hú & Giọng nói tiếng Việt
        end
    end"""

    add_image_item(
        doc,
        None,
        "Hình 5.2: Sơ đồ Tuần tự (Sequence Diagram): Luồng Truyền phát WebSocket Song công Toàn phần",
        "Thể hiện chu trình xử lý khung hình liên tục trong vòng lặp bất đồng bộ với độ trễ 38ms giữa Client, WebSocket Server và AI Core.",
        "Vẽ dạng biểu đồ tuần tự (Sequence Diagram) chuẩn UML, các mũi tên có đánh số thứ tự từ 1 đến 8 rõ ràng, không bị chồng chéo đường truyền.",
        code_ws
    )

    # 11. ERD code
    code_erd = """erDiagram
    organizations ||--o{ users : employs
    organizations ||--o{ vehicles : owns
    users ||--o| drivers : profile
    vehicles ||--o{ driving_sessions : tracks
    drivers ||--o{ driving_sessions : operates
    driving_sessions ||--o{ violations : records
    violations ||--o| violation_reviews : reviewed

    organizations { int id PK, string name, string tax_code }
    users { int id PK, string email, string role, int organization_id FK }
    drivers { int id PK, int user_id FK, float safety_score }
    vehicles { int id PK, string plate_number, string vehicle_type }
    driving_sessions { int id PK, int vehicle_id FK, int driver_id FK, float total_km }
    violations { int id PK, int session_id FK, string violation_type, float speed_kmh, string evidence_hash_sha256 }"""

    add_image_item(
        doc,
        None,
        "Hình 3.4: Sơ đồ Thực thể Quan hệ Cơ sở Dữ liệu (ERD - Database Schema)",
        "Sơ đồ quan hệ thực thể mức khái niệm và mức vật lý liên kết giữa các bảng quản trị doanh nghiệp, tài xế, phương tiện, phiên hành trình và biên bản vi phạm.",
        "Mỗi thực thể được đóng khung chữ nhật, liệt kê khóa chính (PK) và khóa ngoại (FK), các đường quan hệ 1-Nhiều vẽ vuông góc không cắt chéo thân bảng.",
        code_erd
    )

    try:
        print(f"Luu tai lieu tai: {OUT_DOCX}...")
        doc.save(str(OUT_DOCX))
        print(f"Xuat ban thanh cong: {OUT_DOCX.resolve()} ({OUT_DOCX.stat().st_size / 1024:.1f} KB)")
    except PermissionError:
        fallback_path = Path("docs/reports/SO_TAY_HINH_ANH_VA_SO_DO_TRAFFICGUARD_CLEAN.docx")
        print(f"File {OUT_DOCX} dang duoc mo trong Word. Luu sang file moi: {fallback_path}...")
        doc.save(str(fallback_path))
        print(f"Xuat ban thanh cong: {fallback_path.resolve()} ({fallback_path.stat().st_size / 1024:.1f} KB)")

if __name__ == '__main__':
    main()
