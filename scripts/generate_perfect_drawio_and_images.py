import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DIR = Path("report_assets")
OUT_DIR.mkdir(exist_ok=True)

# ==============================================================================
# 1. DRAW.IO NATIVE XML (TỐI ƯU TUYỆT ĐỐI CHO APP.DIAGRAMS.NET)
# ==============================================================================

def create_drawio_file(filename, diagram_id, diagram_name, cells_xml, width=1350, height=750):
    xml_content = f"""<mxfile host="app.diagrams.net" modified="2026-10-03T12:00:00.000Z" agent="TrafficGuard" version="24.0.0" type="device">
  <diagram id="{diagram_id}" name="{diagram_name}">
    <mxGraphModel dx="{width}" dy="{height}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{width}" pageHeight="{height}" background="#F8FAFC" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
{cells_xml}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
    out_path = OUT_DIR / filename
    out_path.write_text(xml_content, encoding="utf-8")
    print(f"Generated Draw.io: {out_path}")

# --- HÌNH 3.2: DUAL STREAM PIPELINE (DRAW.IO) ---
def gen_drawio_3_2():
    cells = """
        <!-- Title & Subtitle -->
        <mxCell id="title" value="&lt;b&gt;&lt;font style=&quot;font-size: 20px; color: #0F172A;&quot;&gt;SƠ ĐỒ LUỒNG XỬ LÝ SONG SONG 2 KÊNH CAMERA (DUAL-STREAM PIPELINE)&lt;/font&gt;&lt;/b&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="150" y="25" width="1000" height="40" as="geometry" />
        </mxCell>
        <mxCell id="subtitle" value="&lt;font style=&quot;font-size: 13px; color: #64748B;&quot;&gt;Hệ thống hỗ trợ lái xe an toàn TrafficGuard - Xử lý đa luồng phân tán thời gian thực (&amp;lt; 100ms)&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="250" y="65" width="800" height="25" as="geometry" />
        </mxCell>

        <!-- Column 1: Road-Facing -->
        <mxCell id="hdr_road" value="&lt;b&gt;&lt;font style=&quot;font-size: 15px; color: #FFFFFF;&quot;&gt;LUỒNG ROAD-FACING (MẶT ĐƯỜNG)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#2563EB;strokeColor=#1D4ED8;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="115" width="360" height="45" as="geometry" />
        </mxCell>
        <mxCell id="box_road" value="&lt;div style=&quot;text-align: left; line-height: 190%; font-size: 12.5px; color: #1E293B;&quot;&gt;&lt;b&gt;1. Thu nhận Frame:&lt;/b&gt; 1080p @ 30 FPS qua RTSP/WebRTC&lt;br&gt;&lt;b&gt;2. ROI Dynamic Crop:&lt;/b&gt; Loại bỏ 30% vùng trời nhiễu sáng&lt;br&gt;&lt;b&gt;3. Object Detection:&lt;/b&gt; YOLOv8x nhận diện Xe &amp;amp; Người đi bộ&lt;br&gt;&lt;b&gt;4. Multi-Object Tracking:&lt;/b&gt; ByteTrack gán ID quỹ đạo ổn định&lt;br&gt;&lt;b&gt;5. Homography Mapping:&lt;/b&gt; Chiếu BEV tính Vận tốc thực tế&lt;br&gt;&lt;b&gt;6. Traffic Sign Recognition:&lt;/b&gt; Biển báo QCVN 41 &amp;amp; S.508&lt;br&gt;&lt;b&gt;7. Safety Metrics:&lt;/b&gt; Cự ly an toàn (TT31) &amp;amp; Tính thời gian TTC&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2563EB;strokeWidth=2;align=left;spacingLeft=18;spacingRight=15;verticalAlign=top;spacingTop=16;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="60" y="165" width="360" height="260" as="geometry" />
        </mxCell>

        <!-- Column 2: FastAPI Core -->
        <mxCell id="hdr_core" value="&lt;b&gt;&lt;font style=&quot;font-size: 15px; color: #FFFFFF;&quot;&gt;FASTAPI BACKEND CORE ENGINE&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#16A34A;strokeColor=#15803D;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="470" y="115" width="360" height="45" as="geometry" />
        </mxCell>
        <mxCell id="box_core" value="&lt;div style=&quot;text-align: left; line-height: 180%; font-size: 12px; color: #0F172A;&quot;&gt;&lt;b&gt;• WebSocket Pipeline:&lt;/b&gt; In-Memory Non-blocking AsyncIO&lt;br&gt;&lt;b&gt;• Priority Decision Engine (Cơ chế phân cấp):&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;&lt;span style=&quot;color: #DC2626;&quot;&gt;&lt;b&gt;[MỨC 1 - NGUY HIỂM]:&lt;/b&gt; TTC va chạm &amp;lt; 1.5s, Ngủ gật nhắm mắt&lt;/span&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;&lt;span style=&quot;color: #EA580C;&quot;&gt;&lt;b&gt;[MỨC 2 - CẢNH BÁO]:&lt;/b&gt; Vượt quá tốc độ, Bám sát cự ly&lt;/span&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;&lt;span style=&quot;color: #2563EB;&quot;&gt;&lt;b&gt;[MỨC 3 - THÔNG BÁO]:&lt;/b&gt; Không thắt dây đai, Lái liên tục &amp;gt; 4h&lt;/span&gt;&lt;br&gt;&lt;b&gt;• Debounce &amp;amp; Hysteresis:&lt;/b&gt; Chống dội &amp;amp; triệt tiêu cảnh báo giả&lt;br&gt;&lt;b&gt;• Data Privacy Guard:&lt;/b&gt; Blur mặt/biển số xe + Băm SHA-256&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#F0FDF4;strokeColor=#16A34A;strokeWidth=2;align=left;spacingLeft=18;spacingRight=15;verticalAlign=top;spacingTop=16;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="470" y="165" width="360" height="260" as="geometry" />
        </mxCell>

        <!-- Column 3: Cabin DMS -->
        <mxCell id="hdr_cabin" value="&lt;b&gt;&lt;font style=&quot;font-size: 15px; color: #FFFFFF;&quot;&gt;LUỒNG DRIVER-FACING (CABIN DMS)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#7C3AED;strokeColor=#6D28D9;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="880" y="115" width="360" height="45" as="geometry" />
        </mxCell>
        <mxCell id="box_cabin" value="&lt;div style=&quot;text-align: left; line-height: 190%; font-size: 12.5px; color: #1E293B;&quot;&gt;&lt;b&gt;1. Thu nhận Frame IR:&lt;/b&gt; Cảm biến hồng ngoại cabin lái xe&lt;br&gt;&lt;b&gt;2. MediaPipe Landmark:&lt;/b&gt; Trích xuất 468 điểm tọa độ khuôn mặt 3D&lt;br&gt;&lt;b&gt;3. Dynamic Calibration:&lt;/b&gt; Hiệu chuẩn cá nhân hóa EAR/MAR&lt;br&gt;&lt;b&gt;4. Eye &amp;amp; Mouth Analysis:&lt;/b&gt; Tỷ lệ chớp mắt EAR &amp;amp; ngáp ngủ MAR&lt;br&gt;&lt;b&gt;5. Sliding Window PERCLOS:&lt;/b&gt; Tỷ lệ mắt nhắm trong 60 giây&lt;br&gt;&lt;b&gt;6. 3D Head Pose (solvePnP):&lt;/b&gt; Góc quay đầu (Yaw/Pitch) lơ đãng&lt;br&gt;&lt;b&gt;7. An toàn Vận tải:&lt;/b&gt; Giám sát dây đai &amp;amp; Đếm ca lái liên tục 4h&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7C3AED;strokeWidth=2;align=left;spacingLeft=18;spacingRight=15;verticalAlign=top;spacingTop=16;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="880" y="165" width="360" height="260" as="geometry" />
        </mxCell>

        <!-- Arrows -->
        <mxCell id="arr_road_core" value="&lt;b&gt;Frame Stream&lt;/b&gt;" style="endArrow=classic;html=1;rounded=0;strokeColor=#2563EB;strokeWidth=2.5;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;labelBackgroundColor=#F8FAFC;fontColor=#2563EB;" edge="1" parent="1" source="box_road" target="box_core">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="arr_cabin_core" value="&lt;b&gt;DMS Stream&lt;/b&gt;" style="endArrow=classic;html=1;rounded=0;strokeColor=#7C3AED;strokeWidth=2.5;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;labelBackgroundColor=#F8FAFC;fontColor=#7C3AED;" edge="1" parent="1" source="box_cabin" target="box_core">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Bottom Banner Output -->
        <mxCell id="hdr_out" value="&lt;b&gt;&lt;font style=&quot;font-size: 15px; color: #92400E;&quot;&gt;ĐỒNG BỘ ĐẦU RA ĐA KÊNH THỜI GIAN THỰC (REAL-TIME MULTI-CHANNEL OUTPUT)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#F59E0B;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="475" width="1180" height="38" as="geometry" />
        </mxCell>
        <mxCell id="out_web" value="&lt;b&gt;Web Admin Dashboard&lt;/b&gt;&lt;br&gt;Canvas 2D HUD 60 FPS, Giám sát bản đồ GPS trực tiếp &amp;amp; Quản trị vi phạm" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F59E0B;strokeWidth=1.5;align=center;fontSize=11.5;fontColor=#1E293B;" vertex="1" parent="1">
          <mxGeometry x="70" y="520" width="370" height="55" as="geometry" />
        </mxCell>
        <mxCell id="out_app" value="&lt;b&gt;Mobile App Driver HUD&lt;/b&gt;&lt;br&gt;Giao diện hỗ trợ lái xe trên kính lái, hiển thị tốc độ &amp;amp; cảnh báo khẩn cấp" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F59E0B;strokeWidth=1.5;align=center;fontSize=11.5;fontColor=#1E293B;" vertex="1" parent="1">
          <mxGeometry x="465" y="520" width="370" height="55" as="geometry" />
        </mxCell>
        <mxCell id="out_voice" value="&lt;b&gt;Web Audio &amp;amp; TTS Tiếng Việt&lt;/b&gt;&lt;br&gt;Còi bíp cảnh báo đa tần số (500Hz - 2500Hz) &amp;amp; Giọng nói cảnh báo tức thời" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#F59E0B;strokeWidth=1.5;align=center;fontSize=11.5;fontColor=#1E293B;" vertex="1" parent="1">
          <mxGeometry x="860" y="520" width="370" height="55" as="geometry" />
        </mxCell>

        <!-- Arrow Core to Output -->
        <mxCell id="arr_core_out" value="&lt;b&gt;Đồng bộ tín hiệu &amp;lt; 100ms&lt;/b&gt;" style="endArrow=classic;html=1;rounded=0;strokeColor=#F59E0B;strokeWidth=2.5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;labelBackgroundColor=#F8FAFC;fontColor=#D97706;" edge="1" parent="1" source="box_core" target="hdr_out">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
    """
    create_drawio_file("hinh_3_2_dual_stream_pipeline_pro.drawio", "diag_3_2", "Hình 3.2 Dual Stream Pipeline", cells, width=1300, height=620)

# --- HÌNH 3.3: DATABASE ERD SCHEMA (DRAW.IO) ---
def gen_drawio_3_3():
    cells = """
        <mxCell id="title" value="&lt;b&gt;&lt;font style=&quot;font-size: 20px; color: #0F172A;&quot;&gt;SƠ ĐỒ QUAN HỆ THỰC THỂ CƠ SỞ DỮ LIỆU (DATABASE ERD SCHEMA - 15 BẢNG)&lt;/font&gt;&lt;/b&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="150" y="20" width="1000" height="40" as="geometry" />
        </mxCell>
        <mxCell id="subtitle" value="&lt;font style=&quot;font-size: 13px; color: #64748B;&quot;&gt;Kiến trúc PostgreSQL phân vùng tối ưu: Quản trị doanh nghiệp - Hành trình vận hành - Giám sát an toàn &amp;amp; Vi phạm&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="250" y="55" width="800" height="25" as="geometry" />
        </mxCell>

        <!-- Column 1 -->
        <mxCell id="h_org" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot; style=&quot;font-size: 13px;&quot;&gt;organizations&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#1D4ED8;strokeColor=#1D4ED8;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="95" width="310" height="32" as="geometry" />
        </mxCell>
        <mxCell id="b_org" value="&lt;div style=&quot;line-height: 160%; font-size: 11.5px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : UUID&lt;br&gt;&lt;b&gt;• name&lt;/b&gt; : VARCHAR(255)&lt;br&gt;&lt;b&gt;• code&lt;/b&gt; : VARCHAR(50) [UNIQUE]&lt;br&gt;&lt;b&gt;• plan_tier&lt;/b&gt; : VARCHAR(50) (Standard/Pro/Fleet)&lt;br&gt;&lt;b&gt;• created_at&lt;/b&gt; : TIMESTAMP WITH TIME ZONE&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D4ED8;strokeWidth=1.8;align=left;spacingLeft=14;verticalAlign=top;spacingTop=8;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="60" y="127" width="310" height="100" as="geometry" />
        </mxCell>

        <mxCell id="h_usr" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot; style=&quot;font-size: 13px;&quot;&gt;users&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#1D4ED8;strokeColor=#1D4ED8;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="270" width="310" height="32" as="geometry" />
        </mxCell>
        <mxCell id="b_usr" value="&lt;div style=&quot;line-height: 160%; font-size: 11.5px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : UUID&lt;br&gt;&lt;b&gt;FK org_id&lt;/b&gt; : UUID [-&amp;gt; organizations.id]&lt;br&gt;&lt;b&gt;• email&lt;/b&gt; : VARCHAR(255) [UNIQUE]&lt;br&gt;&lt;b&gt;• hashed_pwd&lt;/b&gt; : VARCHAR(255) (Bcrypt)&lt;br&gt;&lt;b&gt;• role&lt;/b&gt; : VARCHAR(50) (Admin / Manager / Driver)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D4ED8;strokeWidth=1.8;align=left;spacingLeft=14;verticalAlign=top;spacingTop=8;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="60" y="302" width="310" height="100" as="geometry" />
        </mxCell>

        <mxCell id="h_drv" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot; style=&quot;font-size: 13px;&quot;&gt;drivers&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#15803D;strokeColor=#15803D;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="445" width="310" height="32" as="geometry" />
        </mxCell>
        <mxCell id="b_drv" value="&lt;div style=&quot;line-height: 160%; font-size: 11.5px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : UUID&lt;br&gt;&lt;b&gt;FK user_id&lt;/b&gt; : UUID [-&amp;gt; users.id]&lt;br&gt;&lt;b&gt;• license_no&lt;/b&gt; : VARCHAR(50) (B2 / C / FC / FE)&lt;br&gt;&lt;b&gt;• safety_score&lt;/b&gt; : FLOAT (Điểm lái xe 0-100)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#15803D;strokeWidth=1.8;align=left;spacingLeft=14;verticalAlign=top;spacingTop=8;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="60" y="477" width="310" height="90" as="geometry" />
        </mxCell>

        <!-- Column 2 -->
        <mxCell id="h_veh" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot; style=&quot;font-size: 13px;&quot;&gt;vehicles&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#EA580C;strokeColor=#EA580C;align=center;" vertex="1" parent="1">
          <mxGeometry x="470" y="95" width="310" height="32" as="geometry" />
        </mxCell>
        <mxCell id="b_veh" value="&lt;div style=&quot;line-height: 160%; font-size: 11.5px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : UUID&lt;br&gt;&lt;b&gt;FK org_id&lt;/b&gt; : UUID [-&amp;gt; organizations.id]&lt;br&gt;&lt;b&gt;• plate_number&lt;/b&gt; : VARCHAR(20) [UNIQUE]&lt;br&gt;&lt;b&gt;• model&lt;/b&gt; : VARCHAR(100)&lt;br&gt;&lt;b&gt;• camera_id&lt;/b&gt; : VARCHAR(100) (Dual Stream RTSP)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#EA580C;strokeWidth=1.8;align=left;spacingLeft=14;verticalAlign=top;spacingTop=8;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="470" y="127" width="310" height="100" as="geometry" />
        </mxCell>

        <mxCell id="h_ses" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot; style=&quot;font-size: 13px;&quot;&gt;driving_sessions&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#EA580C;strokeColor=#EA580C;align=center;" vertex="1" parent="1">
          <mxGeometry x="470" y="270" width="310" height="32" as="geometry" />
        </mxCell>
        <mxCell id="b_ses" value="&lt;div style=&quot;line-height: 160%; font-size: 11.5px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : UUID&lt;br&gt;&lt;b&gt;FK vehicle_id&lt;/b&gt; : UUID [-&amp;gt; vehicles.id]&lt;br&gt;&lt;b&gt;FK driver_id&lt;/b&gt; : UUID [-&amp;gt; drivers.id]&lt;br&gt;&lt;b&gt;• start_time&lt;/b&gt; : TIMESTAMP&lt;br&gt;&lt;b&gt;• distance_km&lt;/b&gt; : FLOAT (Tổng quãng đường)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#EA580C;strokeWidth=1.8;align=left;spacingLeft=14;verticalAlign=top;spacingTop=8;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="470" y="302" width="310" height="100" as="geometry" />
        </mxCell>

        <mxCell id="h_trip" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot; style=&quot;font-size: 13px;&quot;&gt;trip_events&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#7C3AED;strokeColor=#7C3AED;align=center;" vertex="1" parent="1">
          <mxGeometry x="470" y="445" width="310" height="32" as="geometry" />
        </mxCell>
        <mxCell id="b_trip" value="&lt;div style=&quot;line-height: 160%; font-size: 11.5px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : UUID&lt;br&gt;&lt;b&gt;FK session_id&lt;/b&gt; : UUID [-&amp;gt; driving_sessions.id]&lt;br&gt;&lt;b&gt;• event_type&lt;/b&gt; : VARCHAR(50) (GPS, Accel, Turn)&lt;br&gt;&lt;b&gt;• speed&lt;/b&gt; : FLOAT (km/h)&lt;br&gt;&lt;b&gt;• timestamp&lt;/b&gt; : TIMESTAMP WITH TIME ZONE&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7C3AED;strokeWidth=1.8;align=left;spacingLeft=14;verticalAlign=top;spacingTop=8;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="470" y="477" width="310" height="95" as="geometry" />
        </mxCell>

        <!-- Column 3 -->
        <mxCell id="h_vio" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot; style=&quot;font-size: 13px;&quot;&gt;violations&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#DC2626;strokeColor=#DC2626;align=center;" vertex="1" parent="1">
          <mxGeometry x="880" y="95" width="310" height="32" as="geometry" />
        </mxCell>
        <mxCell id="b_vio" value="&lt;div style=&quot;line-height: 160%; font-size: 11.5px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : UUID&lt;br&gt;&lt;b&gt;FK session_id&lt;/b&gt; : UUID [-&amp;gt; driving_sessions.id]&lt;br&gt;&lt;b&gt;• type&lt;/b&gt; : VARCHAR(50) (Speed, Drowsy, Dist)&lt;br&gt;&lt;b&gt;• evidence_url&lt;/b&gt; : TEXT (MinIO S3 Snapshot)&lt;br&gt;&lt;b&gt;• sha256_hash&lt;/b&gt; : VARCHAR(64) (Chống giả mạo)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#DC2626;strokeWidth=1.8;align=left;spacingLeft=14;verticalAlign=top;spacingTop=8;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="880" y="127" width="310" height="100" as="geometry" />
        </mxCell>

        <mxCell id="h_rev" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot; style=&quot;font-size: 13px;&quot;&gt;violation_reviews&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#DC2626;strokeColor=#DC2626;align=center;" vertex="1" parent="1">
          <mxGeometry x="880" y="270" width="310" height="32" as="geometry" />
        </mxCell>
        <mxCell id="b_rev" value="&lt;div style=&quot;line-height: 160%; font-size: 11.5px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : UUID&lt;br&gt;&lt;b&gt;FK violation_id&lt;/b&gt; : UUID [-&amp;gt; violations.id]&lt;br&gt;&lt;b&gt;FK reviewer_id&lt;/b&gt; : UUID [-&amp;gt; users.id]&lt;br&gt;&lt;b&gt;• status&lt;/b&gt; : VARCHAR(30) (Pending, Verified)&lt;br&gt;&lt;b&gt;• notes&lt;/b&gt; : TEXT (Lý do phê duyệt/bác bỏ)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#DC2626;strokeWidth=1.8;align=left;spacingLeft=14;verticalAlign=top;spacingTop=8;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="880" y="302" width="310" height="100" as="geometry" />
        </mxCell>

        <mxCell id="h_dev" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot; style=&quot;font-size: 13px;&quot;&gt;device_health&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#78350F;strokeColor=#78350F;align=center;" vertex="1" parent="1">
          <mxGeometry x="880" y="445" width="310" height="32" as="geometry" />
        </mxCell>
        <mxCell id="b_dev" value="&lt;div style=&quot;line-height: 160%; font-size: 11.5px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : UUID&lt;br&gt;&lt;b&gt;FK vehicle_id&lt;/b&gt; : UUID [-&amp;gt; vehicles.id]&lt;br&gt;&lt;b&gt;• fps&lt;/b&gt; : FLOAT (Tốc độ khung hình thực tế)&lt;br&gt;&lt;b&gt;• gpu_temp&lt;/b&gt; : FLOAT (°C Nhiệt độ vi xử lý AI)&lt;br&gt;&lt;b&gt;• ping_ms&lt;/b&gt; : INT (Độ trễ truyền mạng IoT)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#78350F;strokeWidth=1.8;align=left;spacingLeft=14;verticalAlign=top;spacingTop=8;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="880" y="477" width="310" height="95" as="geometry" />
        </mxCell>

        <!-- Orthogonal Arrows -->
        <mxCell id="rel_org_usr" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#2563EB;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;fontColor=#2563EB;" edge="1" parent="1" source="b_org" target="h_usr">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="rel_usr_drv" value="1 : 1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#2563EB;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;fontColor=#2563EB;" edge="1" parent="1" source="b_usr" target="h_drv">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="rel_org_veh" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#EA580C;strokeWidth=1.8;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;fontColor=#EA580C;" edge="1" parent="1" source="b_org" target="b_veh">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="rel_veh_ses" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#EA580C;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;fontColor=#EA580C;" edge="1" parent="1" source="b_veh" target="h_ses">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="rel_drv_ses" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#15803D;strokeWidth=1.8;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.7;entryDx=0;entryDy=0;fontColor=#15803D;" edge="1" parent="1" source="b_drv" target="b_ses">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="rel_ses_trip" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#7C3AED;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;fontColor=#7C3AED;" edge="1" parent="1" source="b_ses" target="h_trip">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="rel_ses_vio" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#DC2626;strokeWidth=1.8;exitX=1;exitY=0.3;exitDx=0;exitDy=0;entryX=0;entryY=0.7;entryDx=0;entryDy=0;fontColor=#DC2626;" edge="1" parent="1" source="b_ses" target="b_vio">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="rel_vio_rev" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#DC2626;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;fontColor=#DC2626;" edge="1" parent="1" source="b_vio" target="h_rev">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="rel_veh_dev" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#78350F;strokeWidth=1.8;exitX=1;exitY=0.8;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;fontColor=#78350F;" edge="1" parent="1" source="b_veh" target="b_dev">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="830" y="207" />
              <mxPoint x="830" y="524" />
            </Array>
          </mxGeometry>
        </mxCell>
    """
    create_drawio_file("hinh_3_3_database_erd_schema_pro.drawio", "diag_3_3", "Hình 3.3 Database ERD Schema", cells, width=1300, height=620)

# --- HÌNH 4.1: QUY TRÌNH BIỂN SỐ XE (DRAW.IO) ---
def gen_drawio_4_1():
    cells = """
        <mxCell id="title" value="&lt;b&gt;&lt;font style=&quot;font-size: 20px; color: #0F172A;&quot;&gt;QUY TRÌNH 5 BƯỚC NHẬN DẠNG BIỂN SỐ XE VIỆT NAM (ALPR PIPELINE)&lt;/font&gt;&lt;/b&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="150" y="25" width="1000" height="40" as="geometry" />
        </mxCell>
        <mxCell id="subtitle" value="&lt;font style=&quot;font-size: 13px; color: #64748B;&quot;&gt;YOLOv11 Detector -&amp;gt; Perspective Deskew -&amp;gt; Tăng tương phản CLAHE -&amp;gt; EasyOCR Engine -&amp;gt; Regex Chuẩn hóa TCVN&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="200" y="65" width="900" height="25" as="geometry" />
        </mxCell>

        <!-- STEP 1 -->
        <mxCell id="b1_hdr" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;BƯỚC 1&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#2563EB;strokeColor=#1D4ED8;align=center;" vertex="1" parent="1">
          <mxGeometry x="40" y="115" width="220" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b1_body" value="&lt;b&gt;&lt;font color=&quot;#1D4ED8&quot; style=&quot;font-size: 13px;&quot;&gt;Input Frame&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#64748B&quot;&gt;(1080p Stream)&lt;/font&gt;&lt;hr&gt;&lt;div style=&quot;text-align: left; font-size: 11.5px; line-height: 150%;&quot;&gt;• Camera hành trình&lt;br&gt;• Độ phân giải 1920x1080&lt;br&gt;• Tần số 30 FPS&lt;br&gt;• Định dạng BGR/RGB&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2563EB;strokeWidth=2;align=center;verticalAlign=top;spacingTop=10;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="40" y="145" width="220" height="150" as="geometry" />
        </mxCell>

        <!-- STEP 2 -->
        <mxCell id="b2_hdr" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;BƯỚC 2&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#16A34A;strokeColor=#15803D;align=center;" vertex="1" parent="1">
          <mxGeometry x="290" y="115" width="220" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b2_body" value="&lt;b&gt;&lt;font color=&quot;#15803D&quot; style=&quot;font-size: 13px;&quot;&gt;YOLOv11 Detector&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#64748B&quot;&gt;(Plate ROI Detection)&lt;/font&gt;&lt;hr&gt;&lt;div style=&quot;text-align: left; font-size: 11.5px; line-height: 150%;&quot;&gt;• Định vị hộp biển số&lt;br&gt;• Cắt ROI biển vuông/dài&lt;br&gt;• Độ trễ xử lý ~14ms&lt;br&gt;• Ngưỡng tin cậy &amp;gt; 0.50&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#16A34A;strokeWidth=2;align=center;verticalAlign=top;spacingTop=10;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="290" y="145" width="220" height="150" as="geometry" />
        </mxCell>

        <!-- STEP 3 -->
        <mxCell id="b3_hdr" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;BƯỚC 3&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#EA580C;strokeColor=#C2410C;align=center;" vertex="1" parent="1">
          <mxGeometry x="540" y="115" width="220" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b3_body" value="&lt;b&gt;&lt;font color=&quot;#C2410C&quot; style=&quot;font-size: 13px;&quot;&gt;Preprocessing&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#64748B&quot;&gt;(Perspective &amp;amp; CLAHE)&lt;/font&gt;&lt;hr&gt;&lt;div style=&quot;text-align: left; font-size: 11.5px; line-height: 150%;&quot;&gt;• Nắn thẳng góc nghiêng&lt;br&gt;• Biến đổi phối cảnh 4 góc&lt;br&gt;• Tăng tương phản CLAHE&lt;br&gt;• Lọc bóng lóa &amp;amp; nhiễu mờ&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#EA580C;strokeWidth=2;align=center;verticalAlign=top;spacingTop=10;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="540" y="145" width="220" height="150" as="geometry" />
        </mxCell>

        <!-- STEP 4 -->
        <mxCell id="b4_hdr" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;BƯỚC 4&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#7C3AED;strokeColor=#6D28D9;align=center;" vertex="1" parent="1">
          <mxGeometry x="790" y="115" width="220" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b4_body" value="&lt;b&gt;&lt;font color=&quot;#6D28D9&quot; style=&quot;font-size: 13px;&quot;&gt;EasyOCR Engine&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#64748B&quot;&gt;(Character Recog)&lt;/font&gt;&lt;hr&gt;&lt;div style=&quot;text-align: left; font-size: 11.5px; line-height: 150%;&quot;&gt;• Tách ký tự quang học&lt;br&gt;• Nhận diện số &amp;amp; chữ cái&lt;br&gt;• Hỗ trợ biển 1 hàng / 2 hàng&lt;br&gt;• Xuất chuỗi raw text&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7C3AED;strokeWidth=2;align=center;verticalAlign=top;spacingTop=10;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="790" y="145" width="220" height="150" as="geometry" />
        </mxCell>

        <!-- STEP 5 -->
        <mxCell id="b5_hdr" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;BƯỚC 5&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#D97706;strokeColor=#B45309;align=center;" vertex="1" parent="1">
          <mxGeometry x="1040" y="115" width="220" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b5_body" value="&lt;b&gt;&lt;font color=&quot;#B45309&quot; style=&quot;font-size: 13px;&quot;&gt;Regex Matcher&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#16A34A;&quot;&gt;&lt;b&gt;51H-982.45&lt;/b&gt;&lt;/font&gt;&lt;hr&gt;&lt;div style=&quot;text-align: left; font-size: 11.5px; line-height: 150%;&quot;&gt;• Chuẩn hóa regex TCVN&lt;br&gt;• Sửa lỗi nhầm 0/O, 1/I, 8/B&lt;br&gt;• Format biển xe Việt Nam&lt;br&gt;• Lưu biên bản vi phạm&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D97706;strokeWidth=2;align=center;verticalAlign=top;spacingTop=10;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="1040" y="145" width="220" height="150" as="geometry" />
        </mxCell>

        <!-- Connectors -->
        <mxCell id="a1_2" value="" style="endArrow=classic;html=1;rounded=0;strokeColor=#64748B;strokeWidth=2.5;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="b1_body" target="b2_body">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a2_3" value="" style="endArrow=classic;html=1;rounded=0;strokeColor=#64748B;strokeWidth=2.5;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="b2_body" target="b3_body">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a3_4" value="" style="endArrow=classic;html=1;rounded=0;strokeColor=#64748B;strokeWidth=2.5;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="b3_body" target="b4_body">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a4_5" value="" style="endArrow=classic;html=1;rounded=0;strokeColor=#64748B;strokeWidth=2.5;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="b4_body" target="b5_body">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
    """
    create_drawio_file("hinh_4_1_plate_recognition_pipeline_pro.drawio", "diag_4_1", "Hình 4.1 Plate ALPR Pipeline", cells, width=1300, height=340)

# ==============================================================================
# 2. XUẤT ẢNH PNG HOÀN HẢO (KHÔNG DÙNG EMOJI ĐỂ TRÁNH LỖI FONT DEJAVU)
# ==============================================================================

def render_all_pngs_clean():
    plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 9.5

    # --- 1. HÌNH 3.2 PNG ---
    fig, ax = plt.subplots(figsize=(14.5, 7.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    bg = patches.Rectangle((0, 0), 100, 100, facecolor='#F8FAFC', zorder=0)
    ax.add_patch(bg)

    ax.text(50, 96, "SO DO LUONG XU LY SONG SONG 2 KENH CAMERA (DUAL-STREAM PIPELINE)",
            fontsize=13.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(50, 92.5, "Kien truc xu ly da luong phan tan thoi gian thuc (< 100ms) cua TrafficGuard",
            fontsize=9.5, ha='center', color='#64748B')

    # Card 1: Road (Left)
    ax.add_patch(patches.FancyBboxPatch((4, 34), 28, 52, boxstyle="round,pad=0.5,rounding_size=1.5",
                                        facecolor='#FFFFFF', edgecolor='#2563EB', linewidth=2, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((4, 79.5), 28, 6.5, boxstyle="round,pad=0.2,rounding_size=1.0",
                                        facecolor='#2563EB', edgecolor='#1D4ED8', linewidth=1.5, zorder=3))
    ax.text(18, 83, "[LUONG ROAD-FACING]", fontsize=10.5, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
    road_text = (
        "1. Thu nhan Frame: 1080p @ 30 FPS\n\n"
        "2. ROI Crop: Loai bo 30% vung troi\n\n"
        "3. YOLOv8x: Nhan dien Xe & Nguoi\n\n"
        "4. ByteTrack: Gan ID quy dao on dinh\n\n"
        "5. Homography: Chieu BEV tinh Van toc\n\n"
        "6. Bien bao: QCVN 41 & Bien phu S.508\n\n"
        "7. Cu ly an toan (TT31) & Tinh thoi gian TTC"
    )
    ax.text(6.5, 76, road_text, fontsize=8.6, color='#1E293B', linespacing=1.2, va='top', zorder=4)

    # Card 2: Core (Center)
    ax.add_patch(patches.FancyBboxPatch((36, 34), 28, 52, boxstyle="round,pad=0.5,rounding_size=1.5",
                                        facecolor='#F0FDF4', edgecolor='#16A34A', linewidth=2.2, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((36, 79.5), 28, 6.5, boxstyle="round,pad=0.2,rounding_size=1.0",
                                        facecolor='#16A34A', edgecolor='#15803D', linewidth=1.5, zorder=3))
    ax.text(50, 83, "[FASTAPI BACKEND CORE]", fontsize=10.5, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
    core_text = (
        "- WebSocket Server: In-Memory AsyncIO\n\n"
        "- Priority Decision Engine (3 Cap):\n"
        "   + CAP 1 (NGUY HIEM): TTC < 1.5s, Ngu gat\n"
        "   + CAP 2 (CANH BAO): Qua toc do, Cu ly gan\n"
        "   + CAP 3 (THONG BAO): Day an toan, Nghi 4h\n\n"
        "- Debounce Filter: Chong doi canh bao gia\n\n"
        "- Privacy Blur: Lam mo Mat & Bien so xe\n\n"
        "- SHA-256 Hash: Bao toan bang chung vi pham"
    )
    ax.text(38.5, 76, core_text, fontsize=8.3, color='#0F172A', linespacing=1.15, va='top', zorder=4)

    # Card 3: Cabin (Right)
    ax.add_patch(patches.FancyBboxPatch((68, 34), 28, 52, boxstyle="round,pad=0.5,rounding_size=1.5",
                                        facecolor='#FFFFFF', edgecolor='#7C3AED', linewidth=2, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((68, 79.5), 28, 6.5, boxstyle="round,pad=0.2,rounding_size=1.0",
                                        facecolor='#7C3AED', edgecolor='#6D28D9', linewidth=1.5, zorder=3))
    ax.text(82, 83, "[LUONG CABIN DMS]", fontsize=10.5, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
    cabin_text = (
        "1. Thu nhan Frame IR hong ngoai cabin\n\n"
        "2. MediaPipe Face Mesh: 468 toa do 3D\n\n"
        "3. Dynamic Calibration: Nguong ca nhan\n\n"
        "4. Ty le mat EAR & ngap mieng MAR\n\n"
        "5. Cua so PERCLOS 60s phat hien ngu gat\n\n"
        "6. 3D Head Pose (solvePnP): Mat tap trung\n\n"
        "7. Giam sat day an toan & Gioi han 4h lai"
    )
    ax.text(70.5, 76, cabin_text, fontsize=8.6, color='#1E293B', linespacing=1.2, va='top', zorder=4)

    # Arrows
    ax.annotate('Frame Stream', xy=(36, 60), xytext=(32, 60),
                arrowprops=dict(arrowstyle="-|>", color='#2563EB', lw=2.5, mutation_scale=16),
                fontsize=8.5, fontweight='bold', color='#2563EB', ha='center', va='bottom')
    ax.annotate('DMS Stream', xy=(64, 60), xytext=(68, 60),
                arrowprops=dict(arrowstyle="-|>", color='#7C3AED', lw=2.5, mutation_scale=16),
                fontsize=8.5, fontweight='bold', color='#7C3AED', ha='center', va='bottom')

    # Bottom Banner (Outputs)
    ax.add_patch(patches.FancyBboxPatch((4, 13), 92, 14, boxstyle="round,pad=0.5,rounding_size=1.2",
                                        facecolor='#FFFBEB', edgecolor='#F59E0B', linewidth=2, zorder=2))
    ax.text(50, 23.5, "DONG BO DAU RA DA KENH THOI GIAN THUC (< 100ms)",
            fontsize=10.2, fontweight='bold', ha='center', color='#B45309', zorder=3)
    ax.text(18, 17.5, "Web Admin Dashboard\nCanvas 2D HUD 60 FPS & GPS", fontsize=8.4, fontweight='bold', ha='center', color='#1E293B', zorder=3)
    ax.text(50, 17.5, "Mobile Driver App HUD\nGiao dien kinh lai tuc thoi", fontsize=8.4, fontweight='bold', ha='center', color='#1E293B', zorder=3)
    ax.text(82, 17.5, "Web Audio & Voice TTS\nCoi bip da tan & Giong noi Viet", fontsize=8.4, fontweight='bold', ha='center', color='#1E293B', zorder=3)

    # Arrow from Core to Bottom
    ax.annotate('', xy=(50, 27.5), xytext=(50, 34),
                arrowprops=dict(arrowstyle="-|>", color='#F59E0B', lw=2.5, mutation_scale=18))

    # Caption
    ax.text(50, 2.5, "Hinh 3.2: So do luong xu ly song song 2 kenh camera (Dual Stream Pipeline)",
            fontsize=10.5, style='italic', fontweight='bold', ha='center', color='#1E293B')

    plt.tight_layout()
    p1 = OUT_DIR / "fig_dual_stream_pipeline_pro.png"
    fig.savefig(p1, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Generated Clean Image: {p1}")

    # --- 2. HÌNH 3.3 PNG (ERD) ---
    fig, ax = plt.subplots(figsize=(14.5, 8.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    bg = patches.Rectangle((0, 0), 100, 100, facecolor='#F8FAFC', zorder=0)
    ax.add_patch(bg)

    ax.text(50, 96.5, "SO DO QUAN HE THUC THE CO SO DU LIEU (DATABASE ERD SCHEMA - 15 BANG)",
            fontsize=13, fontweight='bold', ha='center', color='#0F172A')
    ax.text(50, 93.5, "Mo hinh quan he du lieu chuan hoa PostgreSQL phuc vu giam sat va luu tru bang chung",
            fontsize=9.2, ha='center', color='#64748B')

    def draw_erd_box(x, y, w, h, title, fields, color_hdr):
        ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.0",
                                            facecolor='#FFFFFF', edgecolor=color_hdr, linewidth=1.8, zorder=2))
        ax.add_patch(patches.FancyBboxPatch((x, y + h - 5.5), w, 5.5, boxstyle="round,pad=0.1,rounding_size=0.8",
                                            facecolor=color_hdr, edgecolor=color_hdr, linewidth=1.5, zorder=3))
        ax.text(x + w/2, y + h - 2.8, title, fontsize=9.2, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
        ax.text(x + 1.8, y + h - 7.5, "\n".join(fields), fontsize=7.6, color='#1E293B', va='top', linespacing=1.35, zorder=4)

    # Col 1
    draw_erd_box(5, 68, 27, 21, "organizations",
                 ["PK id : UUID", "- name : VARCHAR(255)", "- code : VARCHAR(50) [UNIQUE]", "- plan_tier : VARCHAR(50)", "- created_at : TIMESTAMP"], "#1D4ED8")
    draw_erd_box(5, 38, 27, 21, "users",
                 ["PK id : UUID", "FK org_id : UUID [-> org.id]", "- email : VARCHAR(255) [UNIQUE]", "- hashed_pwd : VARCHAR(255)", "- role : VARCHAR(50) (Admin/Driver)"], "#1D4ED8")
    draw_erd_box(5, 8, 27, 21, "drivers",
                 ["PK id : UUID", "FK user_id : UUID [-> users.id]", "- license_no : VARCHAR(50) [B2/C/FC]", "- safety_score : FLOAT [0-100]"], "#15803D")

    # Col 2
    draw_erd_box(37, 68, 27, 21, "vehicles",
                 ["PK id : UUID", "FK org_id : UUID [-> org.id]", "- plate_number : VARCHAR(20) [UNIQUE]", "- model : VARCHAR(100)", "- camera_id : VARCHAR(100)"], "#EA580C")
    draw_erd_box(37, 38, 27, 21, "driving_sessions",
                 ["PK id : UUID", "FK vehicle_id : UUID [-> veh.id]", "FK driver_id : UUID [-> drv.id]", "- start_time : TIMESTAMP", "- distance_km : FLOAT"], "#EA580C")
    draw_erd_box(37, 8, 27, 21, "trip_events",
                 ["PK id : UUID", "FK session_id : UUID [-> ses.id]", "- event_type : VARCHAR(50)", "- speed : FLOAT (km/h)", "- timestamp : TIMESTAMP"], "#7C3AED")

    # Col 3
    draw_erd_box(69, 68, 27, 21, "violations",
                 ["PK id : UUID", "FK session_id : UUID [-> ses.id]", "- type : VARCHAR(50) (Speed/Dist)", "- evidence_url : TEXT (MinIO S3)", "- sha256_hash : VARCHAR(64)"], "#DC2626")
    draw_erd_box(69, 38, 27, 21, "violation_reviews",
                 ["PK id : UUID", "FK violation_id : UUID [-> vio.id]", "FK reviewer_id : UUID [-> users.id]", "- status : VARCHAR(30) (Verified)", "- notes : TEXT"], "#DC2626")
    draw_erd_box(69, 8, 27, 21, "device_health",
                 ["PK id : UUID", "FK vehicle_id : UUID [-> veh.id]", "- fps : FLOAT (Toc do khung)", "- gpu_temp : FLOAT (Nhiet do C)", "- ping_ms : INT (Do tre IoT)"], "#78350F")

    # Connectors
    ax.annotate('1:N', xy=(18.5, 59), xytext=(18.5, 68), arrowprops=dict(arrowstyle="-|>", color='#1D4ED8', lw=1.8), fontsize=7.5, color='#1D4ED8', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:1', xy=(18.5, 29), xytext=(18.5, 38), arrowprops=dict(arrowstyle="-|>", color='#1D4ED8', lw=1.8), fontsize=7.5, color='#1D4ED8', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(37, 78.5), xytext=(32, 78.5), arrowprops=dict(arrowstyle="-|>", color='#EA580C', lw=1.8), fontsize=7.5, color='#EA580C', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(50.5, 59), xytext=(50.5, 68), arrowprops=dict(arrowstyle="-|>", color='#EA580C', lw=1.8), fontsize=7.5, color='#EA580C', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(37, 44), xytext=(32, 20), arrowprops=dict(arrowstyle="-|>", color='#15803D', lw=1.8, connectionstyle="angle,angleA=0,angleB=90,rad=5"), fontsize=7.5, color='#15803D', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(50.5, 29), xytext=(50.5, 38), arrowprops=dict(arrowstyle="-|>", color='#7C3AED', lw=1.8), fontsize=7.5, color='#7C3AED', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(69, 74), xytext=(64, 52), arrowprops=dict(arrowstyle="-|>", color='#DC2626', lw=1.8, connectionstyle="angle,angleA=0,angleB=90,rad=5"), fontsize=7.5, color='#DC2626', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(82.5, 59), xytext=(82.5, 68), arrowprops=dict(arrowstyle="-|>", color='#DC2626', lw=1.8), fontsize=7.5, color='#DC2626', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(69, 18), xytext=(64, 75), arrowprops=dict(arrowstyle="-|>", color='#78350F', lw=1.8, connectionstyle="angle,angleA=0,angleB=90,rad=5"), fontsize=7.5, color='#78350F', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))

    ax.text(50, 2.5, "Hinh 3.3: So do quan he thuc the co so du lieu (Database ERD Schema - 15 Bang)",
            fontsize=10.5, style='italic', fontweight='bold', ha='center', color='#1E293B')

    plt.tight_layout()
    p2 = OUT_DIR / "fig_database_erd_schema_pro.png"
    fig.savefig(p2, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Generated Clean Image: {p2}")

    # --- 3. HÌNH 4.1 PNG (ALPR) ---
    fig, ax = plt.subplots(figsize=(14, 4.4), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    bg = patches.Rectangle((0, 0), 100, 100, facecolor='#F8FAFC', zorder=0)
    ax.add_patch(bg)

    ax.text(50, 93, "QUY TRINH 5 BUOC NHAN DANG BIEN SO XE VIET NAM (ALPR PIPELINE)",
            fontsize=12.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(50, 86, "YOLOv11 Detector -> Perspective Deskew -> Can bang sang CLAHE -> EasyOCR -> Regex Chuan hoa TCVN",
            fontsize=9.0, ha='center', color='#64748B')

    steps_data = [
        ("BUOC 1", "Input Frame", "1080p RTSP Stream", ["- Camera hanh trinh", "- Do phan giai 1080p", "- Tan so 30 FPS", "- He mau BGR/RGB"], "#2563EB"),
        ("BUOC 2", "YOLOv11 Detector", "Plate ROI Detection", ["- Dinh vi bien so xe", "- Cat ROI chu nhat", "- Do tre xu ly ~14ms", "- Do tin cay > 0.50"], "#16A34A"),
        ("BUOC 3", "Preprocessing", "Perspective & CLAHE", ["- Nan thang goc nghieng", "- Chieu phoi canh 4 diem", "- Tang tuong phan CLAHE", "- Khu loa & mo nhieu"], "#EA580C"),
        ("BUOC 4", "EasyOCR Engine", "Character Recognition", ["- Tach ky tu quang hoc", "- Nhan dien so & chu", "- Bien 1 hang / 2 hang", "- Xuat chuoi raw text"], "#7C3AED"),
        ("BUOC 5", "Regex Matcher", "51H-982.45", ["- Chuan hoa regex TCVN", "- Sua nham O/0, I/1, B/8", "- Format bien Viet Nam", "- Luu bien ban vi pham"], "#D97706")
    ]

    bw = 17.2
    bh = 54.0
    gap = 2.2
    sx = 3.6
    y = 20.0

    for i, (b_badge, b_title, b_sub, b_items, color_main) in enumerate(steps_data):
        x = sx + i * (bw + gap)
        ax.add_patch(patches.FancyBboxPatch((x, y), bw, bh, boxstyle="round,pad=0.3,rounding_size=1.2",
                                            facecolor='#FFFFFF', edgecolor=color_main, linewidth=2.0, zorder=2))
        ax.add_patch(patches.FancyBboxPatch((x, y + bh - 7.5), bw, 7.5, boxstyle="round,pad=0.1,rounding_size=0.8",
                                            facecolor=color_main, edgecolor=color_main, linewidth=1.5, zorder=3))
        ax.text(x + bw/2, y + bh - 3.8, b_badge, fontsize=8.8, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)

        ax.text(x + bw/2, y + bh - 11.5, b_title, fontsize=8.8, fontweight='bold', ha='center', color=color_main, zorder=4)
        ax.text(x + bw/2, y + bh - 15.5, b_sub, fontsize=7.2, style='italic', ha='center', color='#64748B', zorder=4)

        ax.plot([x + 1.5, x + bw - 1.5], [y + bh - 18, y + bh - 18], color='#CBD5E1', lw=1.0, zorder=4)
        ax.text(x + 1.8, y + bh - 22.0, "\n\n".join(b_items), fontsize=7.4, color='#1E293B', va='top', linespacing=1.1, zorder=4)

        if i < len(steps_data) - 1:
            arr_x = x + bw
            ax.annotate('', xy=(arr_x + gap, y + bh/2), xytext=(arr_x, y + bh/2),
                        arrowprops=dict(arrowstyle="-|>", color='#64748B', lw=2.2, mutation_scale=16))

    ax.text(50, 6, "Hinh 4.1: Quy trinh 5 buoc nhan dang bien so xe Viet Nam (YOLOv11 + CLAHE + EasyOCR + Regex)",
            fontsize=10.5, style='italic', fontweight='bold', ha='center', color='#1E293B')

    plt.tight_layout()
    p3 = OUT_DIR / "fig_plate_recognition_pipeline_pro.png"
    fig.savefig(p3, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Generated Clean Image: {p3}")

if __name__ == '__main__':
    gen_drawio_3_2()
    gen_drawio_3_3()
    gen_drawio_4_1()
    render_all_pngs_clean()
