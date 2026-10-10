import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DIR = Path("report_assets")
OUT_DIR.mkdir(exist_ok=True)

# ==============================================================================
# HÀM TẠO FILE DRAW.IO NATIVE XML (CHỈ CẦN DOUBLE-CLICK HOẶC MỞ TRỰC TIẾP)
# ==============================================================================
def create_drawio_file(filename, diagram_id, diagram_name, cells_xml, width=1300, height=750):
    xml_content = f"""<mxfile host="app.diagrams.net" modified="2026-10-10T14:40:00.000Z" agent="TrafficGuard" version="24.0.0" type="device">
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
    print(f"[OK] Generated Draw.io: {out_path}")

# ==============================================================================
# 1. HÌNH 3.2a: PHÂN LUỒNG CẢM BIẾN & XỬ LÝ THỊ GIÁC KÉP TẠI BIÊN
# ==============================================================================
def gen_drawio_3_2a():
    cells = """
        <mxCell id="title" value="&lt;b&gt;&lt;font style=&quot;font-size: 20px; color: #0F172A;&quot;&gt;HÌNH 3.2a: PHÂN LUỒNG CẢM BIẾN &amp;amp; XỬ LÝ THỊ GIÁC KÉP TẠI BIÊN (EDGE AI PERCEPTION)&lt;/font&gt;&lt;/b&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="100" y="25" width="1100" height="40" as="geometry" />
        </mxCell>
        <mxCell id="subtitle" value="&lt;font style=&quot;font-size: 13px; color: #64748B;&quot;&gt;Thu nhận song song 2 kênh camera 1080p @ 30 FPS và trích xuất chỉ số động học mặt đường &amp;amp; sinh trắc khoang lái&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="200" y="65" width="900" height="25" as="geometry" />
        </mxCell>

        <!-- Column 1: Road-Facing ADAS -->
        <mxCell id="hdr_road" value="&lt;b&gt;&lt;font style=&quot;font-size: 15px; color: #FFFFFF;&quot;&gt;KÊNH 1: ROAD-FACING ADAS PIPELINE (MẶT ĐƯỜNG PHÍA TRƯỚC)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#0284C7;strokeColor=#0369A1;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="115" width="560" height="42" as="geometry" />
        </mxCell>
        <mxCell id="box_road" value="&lt;div style=&quot;text-align: left; line-height: 190%; font-size: 12.5px; color: #1E293B;&quot;&gt;&lt;b&gt;1. Thu nhận Frame:&lt;/b&gt; Camera hành trình góc rộng 1080p @ 30 FPS&lt;br&gt;&lt;b&gt;2. Tiền xử lý &amp;amp; Dynamic ROI:&lt;/b&gt; Loại bỏ 30% vùng trời nhiễu sáng + Tăng tương phản CLAHE&lt;br&gt;&lt;b&gt;3. Object Detection:&lt;/b&gt; YOLOv8x nhận diện Xe ô tô, Xe máy, Xe tải &amp;amp; Người đi bộ&lt;br&gt;&lt;b&gt;4. Traffic Sign Recognition:&lt;/b&gt; Nhận diện biển báo giới hạn tốc độ chuẩn QCVN 41:2019&lt;br&gt;&lt;b&gt;5. Multi-Object Tracking:&lt;/b&gt; ByteTrack gán ID quỹ đạo ổn định, chống nhảy ID khi bị che khuất&lt;br&gt;&lt;b&gt;6. Homography Bird's Eye View (BEV):&lt;/b&gt; Biến đổi phối cảnh chiếu phẳng mặt đường đo khoảng cách thực (m)&lt;br&gt;&lt;b&gt;7. Phân tích Va chạm &amp;amp; Luật:&lt;/b&gt; Tính toán thời gian va chạm TTC &amp;amp; Cự ly an toàn theo TT 31/2019&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#F0F9FF;strokeColor=#0284C7;strokeWidth=2;align=left;spacingLeft=18;spacingRight=15;verticalAlign=top;spacingTop=16;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="60" y="165" width="560" height="300" as="geometry" />
        </mxCell>
        <mxCell id="out_road" value="&lt;b&gt;&lt;font color=&quot;#0369A1&quot; style=&quot;font-size: 13px;&quot;&gt;ROAD TELEMETRY JSON&lt;/font&gt;&lt;/b&gt;&lt;br&gt;TTC (s), Khoảng cách xe trước (m), Vận tốc tương đối (km/h), Biển báo tốc độ QCVN 41" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#E0F2FE;strokeColor=#0284C7;strokeWidth=1.8;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="485" width="560" height="55" as="geometry" />
        </mxCell>
        <mxCell id="arr_road" style="endArrow=classic;html=1;rounded=0;strokeColor=#0284C7;strokeWidth=2.5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="box_road" target="out_road">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Column 2: Driver-Facing DMS -->
        <mxCell id="hdr_dms" value="&lt;b&gt;&lt;font style=&quot;font-size: 15px; color: #FFFFFF;&quot;&gt;KÊNH 2: DRIVER-FACING DMS PIPELINE (KHOANG LÁI &amp;amp; TÀI XẾ)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#D97706;strokeColor=#B45309;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="680" y="115" width="560" height="42" as="geometry" />
        </mxCell>
        <mxCell id="box_dms" value="&lt;div style=&quot;text-align: left; line-height: 190%; font-size: 12.5px; color: #1E293B;&quot;&gt;&lt;b&gt;1. Thu nhận Frame IR:&lt;/b&gt; Camera hồng ngoại cabin góc nhìn tài xế, chiếu sáng ban đêm chống chói&lt;br&gt;&lt;b&gt;2. MediaPipe Face Mesh:&lt;/b&gt; Trích xuất 468 mốc tọa độ 3D khuôn mặt thời gian thực (&amp;lt; 15ms)&lt;br&gt;&lt;b&gt;3. Dynamic Calibration:&lt;/b&gt; Hiệu chuẩn cá nhân hóa ngưỡng mở mắt/ngáp theo từng người lái&lt;br&gt;&lt;b&gt;4. 3D Head Pose (solvePnP):&lt;/b&gt; Ước lượng góc nghiêng đầu Pitch, Yaw, Roll phát hiện lơ đãng quay mặt&lt;br&gt;&lt;b&gt;5. Chỉ số Sinh trắc học Mắt &amp;amp; Miệng:&lt;/b&gt; Tính toán tỷ lệ mắt mở EAR &amp;amp; tần suất ngáp miệng MAR&lt;br&gt;&lt;b&gt;6. Sliding Window PERCLOS:&lt;/b&gt; Tỷ lệ thời gian mắt nhắm trong cửa sổ trượt 60 giây (ngưỡng 15%)&lt;br&gt;&lt;b&gt;7. Dây an toàn &amp;amp; Ca lái:&lt;/b&gt; Kiểm tra thắt dây đai Seatbelt &amp;amp; Bộ đếm thời gian lái xe liên tục (&amp;gt; 4 giờ)&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#D97706;strokeWidth=2;align=left;spacingLeft=18;spacingRight=15;verticalAlign=top;spacingTop=16;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="680" y="165" width="560" height="300" as="geometry" />
        </mxCell>
        <mxCell id="out_dms" value="&lt;b&gt;&lt;font color=&quot;#B45309&quot; style=&quot;font-size: 13px;&quot;&gt;DMS TELEMETRY JSON&lt;/font&gt;&lt;/b&gt;&lt;br&gt;Trạng thái ngủ gật (EAR/PERCLOS), Ngáp ngủ (MAR), Góc quay đầu (Head Pose), Dây đai an toàn, Timer ca lái" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#D97706;strokeWidth=1.8;align=center;" vertex="1" parent="1">
          <mxGeometry x="680" y="485" width="560" height="55" as="geometry" />
        </mxCell>
        <mxCell id="arr_dms" style="endArrow=classic;html=1;rounded=0;strokeColor=#D97706;strokeWidth=2.5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="box_dms" target="out_dms">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
    """
    create_drawio_file("hinh_3_2a_dual_stream_edge_ai.drawio", "diag_3_2a", "Hình 3.2a Edge AI Perception", cells, width=1300, height=600)

# ==============================================================================
# 2. HÌNH 3.2b: TRUNG TÂM ĐIỀU PHỐI QUYẾT ĐỊNH FASTAPI CORE ENGINE
# ==============================================================================
def gen_drawio_3_2b():
    cells = """
        <mxCell id="title" value="&lt;b&gt;&lt;font style=&quot;font-size: 20px; color: #0F172A;&quot;&gt;HÌNH 3.2b: TRUNG TÂM ĐIỀU PHỐI QUYẾT ĐỊNH FASTAPI CORE ENGINE&lt;/font&gt;&lt;/b&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="100" y="20" width="1100" height="40" as="geometry" />
        </mxCell>
        <mxCell id="subtitle" value="&lt;font style=&quot;font-size: 13px; color: #64748B;&quot;&gt;Bộ đệm bất đồng bộ, Bộ lọc nhiễu temporal debounce, Cây quyết định ưu tiên 3 cấp &amp;amp; Bảo mật ẩn danh Nghị định 13/2023&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="150" y="58" width="1000" height="25" as="geometry" />
        </mxCell>

        <!-- Top Ingestion -->
        <mxCell id="in_ws" value="&lt;b&gt;&lt;font style=&quot;font-size: 14px; color: #FFFFFF;&quot;&gt;1. CỔNG TIẾP NHẬN BẤT ĐỒNG BỘ: WEBSOCKET ASYNC INGESTION &amp;amp; LOAD SHEDDER&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size: 11.5px; color: #E2E8F0;&quot;&gt;Tiếp nhận song song Road Telemetry &amp;amp; DMS Telemetry qua WebSocket. Cơ chế Load Shedder loại bỏ frame trễ &amp;gt; 45ms&lt;/font&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#1E293B;strokeColor=#0F172A;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="80" y="95" width="1140" height="50" as="geometry" />
        </mxCell>

        <mxCell id="in_debounce" value="&lt;b&gt;&lt;font style=&quot;font-size: 13px; color: #1E3A8A;&quot;&gt;2. BỘ LỌC CHỐNG NHIỄU THỜI GIAN: TEMPORAL PERSISTENCE FILTER (DEBOUNCE 3 - 8 FRAMES)&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size: 11.5px; color: #334155;&quot;&gt;Duy trì trạng thái bất thường liên tục qua 3-8 khung hình để triệt tiêu chớp mắt sinh lý, bóng râm mặt đường hoặc camera rung lắc&lt;/font&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#DBEAFE;strokeColor=#3B82F6;strokeWidth=1.8;align=center;" vertex="1" parent="1">
          <mxGeometry x="80" y="165" width="1140" height="45" as="geometry" />
        </mxCell>
        <mxCell id="arr_in1" style="endArrow=classic;html=1;rounded=0;strokeColor=#3B82F6;strokeWidth=2.2;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="in_ws" target="in_debounce">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- 3 Priority Levels -->
        <!-- Level 1 -->
        <mxCell id="h_l1" value="&lt;b&gt;&lt;font style=&quot;font-size: 13.5px; color: #FFFFFF;&quot;&gt;CẤP 1: CRITICAL (KHẨN CẤP)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#DC2626;strokeColor=#B91C1C;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="80" y="240" width="360" height="35" as="geometry" />
        </mxCell>
        <mxCell id="b_l1" value="&lt;div style=&quot;text-align: left; line-height: 180%; font-size: 12px; color: #7F1D1D;&quot;&gt;&lt;b&gt;• Điều kiện kích hoạt:&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Va chạm cực gần: TTC &amp;le; 1.5s&lt;br&gt;&amp;nbsp;&amp;nbsp;- Ngủ gật nguy hiểm: Nhắm mắt &amp;gt; 5.0s&lt;br&gt;&lt;b&gt;• Cơ chế xử lý:&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Chiếm quyền kênh phát (Preemption)&lt;br&gt;&amp;nbsp;&amp;nbsp;- Còi hú báo động âm tần cao tức thì&lt;br&gt;&amp;nbsp;&amp;nbsp;- Kích hoạt cảnh báo đỏ trên Kính lái HUD&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#DC2626;strokeWidth=2;align=left;spacingLeft=14;verticalAlign=top;spacingTop=10;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="80" y="275" width="360" height="155" as="geometry" />
        </mxCell>

        <!-- Level 2 -->
        <mxCell id="h_l2" value="&lt;b&gt;&lt;font style=&quot;font-size: 13.5px; color: #FFFFFF;&quot;&gt;CẤP 2: WARNING (CẢNH BÁO CAO)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#D97706;strokeColor=#B45309;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="470" y="240" width="360" height="35" as="geometry" />
        </mxCell>
        <mxCell id="b_l2" value="&lt;div style=&quot;text-align: left; line-height: 180%; font-size: 12px; color: #78350F;&quot;&gt;&lt;b&gt;• Điều kiện kích hoạt:&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Vượt tốc độ giới hạn (QCVN 41:2019)&lt;br&gt;&amp;nbsp;&amp;nbsp;- Vi phạm cự ly an toàn (TT 31/2019)&lt;br&gt;&amp;nbsp;&amp;nbsp;- Mệt mỏi giai đoạn sớm: PERCLOS &amp;gt; 15%&lt;br&gt;&amp;nbsp;&amp;nbsp;- Lái xe liên tục vượt quá 4 giờ quy định&lt;br&gt;&lt;b&gt;• Cơ chế xử lý:&lt;/b&gt; Voice TTS cảnh báo + HUD vàng&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#D97706;strokeWidth=2;align=left;spacingLeft=14;verticalAlign=top;spacingTop=10;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="470" y="275" width="360" height="155" as="geometry" />
        </mxCell>

        <!-- Level 3 -->
        <mxCell id="h_l3" value="&lt;b&gt;&lt;font style=&quot;font-size: 13.5px; color: #FFFFFF;&quot;&gt;CẤP 3: CAUTION (NHẮC NHỞ)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#2563EB;strokeColor=#1D4ED8;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="860" y="240" width="360" height="35" as="geometry" />
        </mxCell>
        <mxCell id="b_l3" value="&lt;div style=&quot;text-align: left; line-height: 180%; font-size: 12px; color: #1E3A8A;&quot;&gt;&lt;b&gt;• Điều kiện kích hoạt:&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Chưa thắt dây an toàn (No Seatbelt)&lt;br&gt;&amp;nbsp;&amp;nbsp;- Biển báo sắp vào khu đông dân cư&lt;br&gt;&amp;nbsp;&amp;nbsp;- Biển báo đường cong gấp nguy hiểm&lt;br&gt;&lt;b&gt;• Cơ chế xử lý:&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Nhắc nhở âm lượng êm dịu, icon xanh&lt;br&gt;&amp;nbsp;&amp;nbsp;- Không gây giật mình tài xế&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#EFF6FF;strokeColor=#2563EB;strokeWidth=2;align=left;spacingLeft=14;verticalAlign=top;spacingTop=10;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="860" y="275" width="360" height="155" as="geometry" />
        </mxCell>

        <mxCell id="arr_l1" style="endArrow=classic;html=1;rounded=0;strokeColor=#DC2626;strokeWidth=2;exitX=0.2;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="in_debounce" target="h_l1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="arr_l2" style="endArrow=classic;html=1;rounded=0;strokeColor=#D97706;strokeWidth=2;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="in_debounce" target="h_l2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="arr_l3" style="endArrow=classic;html=1;rounded=0;strokeColor=#2563EB;strokeWidth=2;exitX=0.8;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="in_debounce" target="h_l3">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Security & Dispatcher Bottom -->
        <mxCell id="box_sec" value="&lt;b&gt;&lt;font style=&quot;font-size: 13.5px; color: #581C87;&quot;&gt;3. BẢO VỆ DỮ LIỆU CÁ NHÂN &amp;amp; BĂM TOÀN VẸN BẰNG CHỨNG (PRIVACY &amp;amp; SHA-256 INTEGRITY)&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size: 11.5px; color: #3B0764;&quot;&gt;• Tự động làm mờ khuôn mặt người đi đường &amp;amp; tài xế trong snapshot vi phạm theo Nghị định 13/2023/NĐ-CP&lt;br&gt;• Sinh mã băm SHA-256 cho từng file ảnh bằng chứng để bảo đảm tính toàn vẹn pháp lý, chống sửa đổi&lt;/font&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FAF5FF;strokeColor=#9333EA;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="80" y="460" width="1140" height="60" as="geometry" />
        </mxCell>
        <mxCell id="arr_sec1" style="endArrow=classic;html=1;rounded=0;strokeColor=#6B21A8;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.2;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_l1" target="box_sec">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="arr_sec2" style="endArrow=classic;html=1;rounded=0;strokeColor=#6B21A8;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_l2" target="box_sec">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="arr_sec3" style="endArrow=classic;html=1;rounded=0;strokeColor=#6B21A8;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.8;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_l3" target="box_sec">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Final Output -->
        <mxCell id="box_dispatch" value="&lt;b&gt;&lt;font style=&quot;font-size: 13.5px; color: #065F46;&quot;&gt;4. REALTIME EVENT DISPATCHER (BỘ PHÂN PHỐI SỰ KIỆN ĐA KÊNH &amp;lt; 100ms)&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size: 11.5px; color: #047857;&quot;&gt;Đóng gói Payload cảnh báo kèm mức ưu tiên và đẩy tức thì tới Audio/TTS, Mobile HUD và Web Fleet Dashboard&lt;/font&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#ECFDF5;strokeColor=#059669;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="80" y="550" width="1140" height="50" as="geometry" />
        </mxCell>
        <mxCell id="arr_disp" style="endArrow=classic;html=1;rounded=0;strokeColor=#059669;strokeWidth=2.5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="box_sec" target="box_dispatch">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
    """
    create_drawio_file("hinh_3_2b_fastapi_decision_core.drawio", "diag_3_2b", "Hình 3.2b FastAPI Decision Core", cells, width=1300, height=650)

# ==============================================================================
# 3. HÌNH 3.2c: ĐỒNG BỘ ĐẦU RA ĐA KÊNH THỜI GIAN THỰC (< 100ms)
# ==============================================================================
def gen_drawio_3_2c():
    cells = """
        <mxCell id="title" value="&lt;b&gt;&lt;font style=&quot;font-size: 20px; color: #0F172A;&quot;&gt;HÌNH 3.2c: ĐỒNG BỘ ĐẦU RA ĐA KÊNH THỜI GIAN THỰC (REAL-TIME MULTI-CHANNEL OUTPUT &amp;lt; 100ms)&lt;/font&gt;&lt;/b&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="100" y="25" width="1100" height="40" as="geometry" />
        </mxCell>
        <mxCell id="subtitle" value="&lt;font style=&quot;font-size: 13px; color: #64748B;&quot;&gt;Phân phối đồng thời tín hiệu cảnh báo tới Âm thanh/Giọng nói trong khoang xe, Màn hình kính lái và Bảng điều phối hạm đội&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="150" y="65" width="1000" height="25" as="geometry" />
        </mxCell>

        <!-- Top Dispatcher -->
        <mxCell id="top_bus" value="&lt;b&gt;&lt;font style=&quot;font-size: 14.5px; color: #FFFFFF;&quot;&gt;FASTAPI REALTIME BROADCAST BUS (ĐỘ TRỄ PHÂN PHỐI &amp;lt; 100ms)&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size: 11.5px; color: #E0E7FF;&quot;&gt;Truyền thông điệp bất đồng bộ tới các thiết bị thụ hưởng theo kênh ưu tiên&lt;/font&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#4F46E5;strokeColor=#3730A3;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="80" y="110" width="1140" height="50" as="geometry" />
        </mxCell>

        <!-- Channel 1: Audio / TTS -->
        <mxCell id="h_c1" value="&lt;b&gt;&lt;font style=&quot;font-size: 14px; color: #FFFFFF;&quot;&gt;KÊNH 1: AUDIO &amp;amp; TTS TIẾNG VIỆT (TRONG XE)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#DC2626;strokeColor=#B91C1C;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="80" y="195" width="360" height="38" as="geometry" />
        </mxCell>
        <mxCell id="b_c1" value="&lt;div style=&quot;text-align: left; line-height: 185%; font-size: 12px; color: #1E293B;&quot;&gt;&lt;b&gt;• Đối tượng:&lt;/b&gt; Tài xế đang điều khiển phương tiện&lt;br&gt;&lt;b&gt;• Còi Beeper khẩn cấp:&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Phát xung đa tần số (500Hz - 2500Hz)&lt;br&gt;&amp;nbsp;&amp;nbsp;- Đánh thức tài xế trong 0.2s khi ngủ gật/va chạm&lt;br&gt;&lt;b&gt;• Giọng nói Tiếng Việt tổng hợp TTS:&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Phát các khẩu lệnh súc tích &amp;le; 8 từ&lt;br&gt;&amp;nbsp;&amp;nbsp;- Ví dụ: &lt;i&gt;&quot;Nguy hiểm! Giảm tốc độ ngay!&quot;&lt;/i&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Ví dụ: &lt;i&gt;&quot;Tài xế tập trung lái xe!&quot;&lt;/i&gt;&lt;br&gt;&lt;b&gt;• Thời gian phản xạ:&lt;/b&gt; Rút ngắn còn 0.3s - 0.5s&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#DC2626;strokeWidth=1.8;align=left;spacingLeft=14;verticalAlign=top;spacingTop=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="80" y="233" width="360" height="260" as="geometry" />
        </mxCell>

        <!-- Channel 2: Mobile HUD -->
        <mxCell id="h_c2" value="&lt;b&gt;&lt;font style=&quot;font-size: 14px; color: #FFFFFF;&quot;&gt;KÊNH 2: MOBILE DRIVER HUD GLASS (KÍNH LÁI)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#D97706;strokeColor=#B45309;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="470" y="195" width="360" height="38" as="geometry" />
        </mxCell>
        <mxCell id="b_c2" value="&lt;div style=&quot;text-align: left; line-height: 185%; font-size: 12px; color: #1E293B;&quot;&gt;&lt;b&gt;• Nền tảng:&lt;/b&gt; React Native App đặt trên taplo&lt;br&gt;&lt;b&gt;• Chế độ Head-Up Display (HUD):&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Chiếu ngược hình ảnh lên kính lái ban đêm&lt;br&gt;&amp;nbsp;&amp;nbsp;- Nền đen OLED thuần túy, tương phản cao&lt;br&gt;&lt;b&gt;• Thông số hiển thị trực quan:&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Đồng hồ tốc độ GPS chữ số khổ lớn (60pt)&lt;br&gt;&amp;nbsp;&amp;nbsp;- Khoảng cách xe trước và giới hạn tốc độ đường&lt;br&gt;&amp;nbsp;&amp;nbsp;- Viền màn hình đổi màu: Xanh $\to$ Vàng $\to$ Đỏ chớp&lt;br&gt;&lt;b&gt;• An toàn:&lt;/b&gt; Không gây phân tâm tầm nhìn lái&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#D97706;strokeWidth=1.8;align=left;spacingLeft=14;verticalAlign=top;spacingTop=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="470" y="233" width="360" height="260" as="geometry" />
        </mxCell>

        <!-- Channel 3: Web Dashboard -->
        <mxCell id="h_c3" value="&lt;b&gt;&lt;font style=&quot;font-size: 14px; color: #FFFFFF;&quot;&gt;KÊNH 3: WEB FLEET DASHBOARD (ĐIỀU HÀNH)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#0284C7;strokeColor=#0369A1;strokeWidth=2;align=center;" vertex="1" parent="1">
          <mxGeometry x="860" y="195" width="360" height="38" as="geometry" />
        </mxCell>
        <mxCell id="b_c3" value="&lt;div style=&quot;text-align: left; line-height: 185%; font-size: 12px; color: #1E293B;&quot;&gt;&lt;b&gt;• Nền tảng:&lt;/b&gt; Next.js 14 Web Portal Điều hành viên&lt;br&gt;&lt;b&gt;• Hiệu năng đồ họa Canvas 2D 60 FPS:&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Render mượt mà dữ liệu video và viễn trắc&lt;br&gt;&lt;b&gt;• Bản đồ số GIS GPS Realtime:&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Giám sát vị trí toàn bộ đoàn xe theo thời gian thực&lt;br&gt;&lt;b&gt;• Tương tác khẩn cấp Điều hành viên:&lt;/b&gt;&lt;br&gt;&amp;nbsp;&amp;nbsp;- Popup thông báo đỏ nhấp nháy khi có Cấp 1&lt;br&gt;&amp;nbsp;&amp;nbsp;- Xem ảnh snapshot đã làm mờ &amp;amp; gọi điện hỗ trợ tài xế&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#F0F9FF;strokeColor=#0284C7;strokeWidth=1.8;align=left;spacingLeft=14;verticalAlign=top;spacingTop=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="860" y="233" width="360" height="260" as="geometry" />
        </mxCell>

        <!-- Connectors -->
        <mxCell id="arr_c1" style="endArrow=classic;html=1;rounded=0;strokeColor=#DC2626;strokeWidth=2.2;exitX=0.2;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="top_bus" target="h_c1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="arr_c2" style="endArrow=classic;html=1;rounded=0;strokeColor=#D97706;strokeWidth=2.2;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="top_bus" target="h_c2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="arr_c3" style="endArrow=classic;html=1;rounded=0;strokeColor=#0284C7;strokeWidth=2.2;exitX=0.8;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="top_bus" target="h_c3">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
    """
    create_drawio_file("hinh_3_2c_realtime_output_sync.drawio", "diag_3_2c", "Hình 3.2c Realtime Output Sync", cells, width=1300, height=550)

# ==============================================================================
# 4. HÌNH 3.3a: ERD PHÂN HỆ QUẢN TRỊ TỔ CHỨC ĐA CẤP & PHÂN QUYỀN RBAC
# ==============================================================================
def gen_drawio_3_3a():
    cells = """
        <mxCell id="title" value="&lt;b&gt;&lt;font style=&quot;font-size: 20px; color: #0F172A;&quot;&gt;HÌNH 3.3a: ERD PHÂN HỆ QUẢN TRỊ TỔ CHỨC ĐA CẤP &amp;amp; PHÂN QUYỀN RBAC&lt;/font&gt;&lt;/b&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="100" y="20" width="1100" height="40" as="geometry" />
        </mxCell>
        <mxCell id="subtitle" value="&lt;font style=&quot;font-size: 13px; color: #64748B;&quot;&gt;Kiến trúc dữ liệu Multi-tenancy phân cấp (Tổ chức &amp;gt; Chi nhánh &amp;gt; Đội xe), Tài khoản xác thực &amp;amp; Ma trận phân quyền RBAC&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="150" y="55" width="1000" height="25" as="geometry" />
        </mxCell>

        <!-- organizations -->
        <mxCell id="h_org" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;organizations&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#1D4ED8;strokeColor=#1D4ED8;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="95" width="260" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_org" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;• name&lt;/b&gt; : VARCHAR(200)&lt;br&gt;&lt;b&gt;• code&lt;/b&gt; : VARCHAR(50) [UNIQUE]&lt;br&gt;&lt;b&gt;• tax_code&lt;/b&gt; : VARCHAR(50)&lt;br&gt;&lt;b&gt;• is_active&lt;/b&gt; : BOOLEAN&lt;br&gt;&lt;b&gt;• created_at&lt;/b&gt; : DATETIME&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D4ED8;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="60" y="125" width="260" height="110" as="geometry" />
        </mxCell>

        <!-- branches -->
        <mxCell id="h_bra" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;branches&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#1D4ED8;strokeColor=#1D4ED8;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="275" width="260" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_bra" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK company_id&lt;/b&gt; : INT [-&amp;gt; org.id]&lt;br&gt;&lt;b&gt;• name&lt;/b&gt; : VARCHAR(200)&lt;br&gt;&lt;b&gt;• code&lt;/b&gt; : VARCHAR(50)&lt;br&gt;&lt;b&gt;• status&lt;/b&gt; : VARCHAR(20) (active)&lt;br&gt;&lt;b&gt;• created_at&lt;/b&gt; : DATETIME&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D4ED8;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="60" y="305" width="260" height="110" as="geometry" />
        </mxCell>

        <!-- fleets -->
        <mxCell id="h_fle" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;fleets&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#1D4ED8;strokeColor=#1D4ED8;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="455" width="260" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_fle" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK company_id&lt;/b&gt; : INT [-&amp;gt; org.id]&lt;br&gt;&lt;b&gt;FK branch_id&lt;/b&gt; : INT [-&amp;gt; bra.id]&lt;br&gt;&lt;b&gt;• name&lt;/b&gt; : VARCHAR(200)&lt;br&gt;&lt;b&gt;• code&lt;/b&gt; : VARCHAR(50)&lt;br&gt;&lt;b&gt;• status&lt;/b&gt; : VARCHAR(20)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D4ED8;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="60" y="485" width="260" height="110" as="geometry" />
        </mxCell>

        <!-- drivers (Users) -->
        <mxCell id="h_drv" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;drivers (Users / Accounts)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#059669;strokeColor=#059669;align=center;" vertex="1" parent="1">
          <mxGeometry x="470" y="95" width="310" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_drv" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK company_id&lt;/b&gt; : INT [-&amp;gt; org.id]&lt;br&gt;&lt;b&gt;FK branch_id&lt;/b&gt; : INT [-&amp;gt; bra.id]&lt;br&gt;&lt;b&gt;FK role_id&lt;/b&gt; : INT [-&amp;gt; roles.id]&lt;br&gt;&lt;b&gt;• email&lt;/b&gt; : VARCHAR [UNIQUE]&lt;br&gt;&lt;b&gt;• password_hash&lt;/b&gt; : VARCHAR (Bcrypt)&lt;br&gt;&lt;b&gt;• full_name&lt;/b&gt; : VARCHAR&lt;br&gt;&lt;b&gt;• role&lt;/b&gt; : VARCHAR (ADMIN/DISPATCHER/DRIVER)&lt;br&gt;&lt;b&gt;• safety_score&lt;/b&gt; : FLOAT (Default 100.0)&lt;br&gt;&lt;b&gt;• is_active&lt;/b&gt; : BOOLEAN&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#059669;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="470" y="125" width="310" height="180" as="geometry" />
        </mxCell>

        <!-- audit_logs -->
        <mxCell id="h_aud" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;audit_logs&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#64748B;strokeColor=#64748B;align=center;" vertex="1" parent="1">
          <mxGeometry x="470" y="375" width="310" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_aud" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK company_id&lt;/b&gt; : INT [-&amp;gt; org.id]&lt;br&gt;&lt;b&gt;FK user_id&lt;/b&gt; : INT [-&amp;gt; drivers.id]&lt;br&gt;&lt;b&gt;• action&lt;/b&gt; : VARCHAR (CREATE/UPDATE/DELETE)&lt;br&gt;&lt;b&gt;• resource&lt;/b&gt; : VARCHAR&lt;br&gt;&lt;b&gt;• ip_address&lt;/b&gt; : VARCHAR&lt;br&gt;&lt;b&gt;• timestamp&lt;/b&gt; : DATETIME&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#64748B;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="470" y="405" width="310" height="135" as="geometry" />
        </mxCell>

        <!-- roles -->
        <mxCell id="h_rol" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;roles&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#7C3AED;strokeColor=#7C3AED;align=center;" vertex="1" parent="1">
          <mxGeometry x="910" y="95" width="270" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_rol" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;• code&lt;/b&gt; : VARCHAR(50) [UNIQUE]&lt;br&gt;&lt;b&gt;• name&lt;/b&gt; : VARCHAR(100)&lt;br&gt;&lt;b&gt;• default_scope&lt;/b&gt; : VARCHAR(50)&lt;br&gt;&lt;b&gt;• description&lt;/b&gt; : VARCHAR(500)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7C3AED;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="910" y="125" width="270" height="95" as="geometry" />
        </mxCell>

        <!-- role_permissions -->
        <mxCell id="h_rp" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;role_permissions (N:N)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#7C3AED;strokeColor=#7C3AED;align=center;" vertex="1" parent="1">
          <mxGeometry x="910" y="265" width="270" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_rp" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK,FK role_id&lt;/b&gt; : INT [-&amp;gt; roles.id]&lt;br&gt;&lt;b&gt;PK,FK permission_id&lt;/b&gt; : INT [-&amp;gt; perms.id]&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7C3AED;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="910" y="295" width="270" height="60" as="geometry" />
        </mxCell>

        <!-- permissions -->
        <mxCell id="h_per" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;permissions&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#7C3AED;strokeColor=#7C3AED;align=center;" vertex="1" parent="1">
          <mxGeometry x="910" y="405" width="270" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_per" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;• code&lt;/b&gt; : VARCHAR(100) [UNIQUE]&lt;br&gt;&lt;b&gt;• name&lt;/b&gt; : VARCHAR(200)&lt;br&gt;&lt;b&gt;• module&lt;/b&gt; : VARCHAR(100)&lt;br&gt;&lt;b&gt;• description&lt;/b&gt; : VARCHAR(500)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7C3AED;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="910" y="435" width="270" height="95" as="geometry" />
        </mxCell>

        <!-- Arrows -->
        <mxCell id="r_org_bra" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#1D4ED8;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_org" target="h_bra">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="r_bra_fle" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#1D4ED8;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_bra" target="h_fle">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="r_org_drv" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#059669;strokeWidth=1.8;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_org" target="b_drv">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="r_drv_aud" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#64748B;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_drv" target="h_aud">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="r_rol_drv" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#7C3AED;strokeWidth=1.8;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.3;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_rol" target="b_drv">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="r_rol_rp" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#7C3AED;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_rol" target="h_rp">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="r_rp_per" value="N : 1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#7C3AED;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_rp" target="h_per">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
    """
    create_drawio_file("hinh_3_3a_erd_org_rbac.drawio", "diag_3_3a", "Hình 3.3a ERD Org & RBAC", cells, width=1300, height=620)

# ==============================================================================
# 5. HÌNH 3.3b: ERD PHÂN HỆ PHƯƠNG TIỆN, THIẾT BỊ CẢM BIẾN & HÀNH TRÌNH
# ==============================================================================
def gen_drawio_3_3b():
    cells = """
        <mxCell id="title" value="&lt;b&gt;&lt;font style=&quot;font-size: 20px; color: #0F172A;&quot;&gt;HÌNH 3.3b: ERD PHÂN HỆ PHƯƠNG TIỆN, THIẾT BỊ CẢM BIẾN &amp;amp; HÀNH TRÌNH LÁI XE&lt;/font&gt;&lt;/b&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="100" y="20" width="1100" height="40" as="geometry" />
        </mxCell>
        <mxCell id="subtitle" value="&lt;font style=&quot;font-size: 13px; color: #64748B;&quot;&gt;Quản lý tài sản xe, Lịch sử bàn giao tài xế, Tình trạng 7 cảm biến Edge AI &amp;amp; Chuỗi viễn trắc hành trình GPS&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="150" y="55" width="1000" height="25" as="geometry" />
        </mxCell>

        <!-- vehicles -->
        <mxCell id="h_veh" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;vehicles&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#EA580C;strokeColor=#EA580C;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="95" width="280" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_veh" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK company_id&lt;/b&gt; : INT [-&amp;gt; org.id]&lt;br&gt;&lt;b&gt;FK branch_id&lt;/b&gt; : INT [-&amp;gt; bra.id]&lt;br&gt;&lt;b&gt;FK fleet_id&lt;/b&gt; : INT [-&amp;gt; fleets.id]&lt;br&gt;&lt;b&gt;• license_plate&lt;/b&gt; : VARCHAR(50) [UNIQUE]&lt;br&gt;&lt;b&gt;• vehicle_type&lt;/b&gt; : VARCHAR(50) (car/truck)&lt;br&gt;&lt;b&gt;• status&lt;/b&gt; : VARCHAR(30) (active/maintenance)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#EA580C;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="60" y="125" width="280" height="135" as="geometry" />
        </mxCell>

        <!-- vehicle_assignments -->
        <mxCell id="h_asg" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;vehicle_assignments&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#EA580C;strokeColor=#EA580C;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="315" width="280" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_asg" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK company_id&lt;/b&gt; : INT [-&amp;gt; org.id]&lt;br&gt;&lt;b&gt;FK vehicle_id&lt;/b&gt; : INT [-&amp;gt; veh.id]&lt;br&gt;&lt;b&gt;FK driver_id&lt;/b&gt; : INT [-&amp;gt; drivers.id]&lt;br&gt;&lt;b&gt;• assigned_from&lt;/b&gt; : DATETIME&lt;br&gt;&lt;b&gt;• assigned_to&lt;/b&gt; : DATETIME&lt;br&gt;&lt;b&gt;FK assigned_by&lt;/b&gt; : INT (Dispatcher)&lt;br&gt;&lt;b&gt;• status&lt;/b&gt; : VARCHAR(30) (active/ended)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#EA580C;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="60" y="345" width="280" height="150" as="geometry" />
        </mxCell>

        <!-- device_health -->
        <mxCell id="h_dev" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;device_health (7 Cảm biến Edge)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#78350F;strokeColor=#78350F;align=center;" vertex="1" parent="1">
          <mxGeometry x="470" y="95" width="310" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_dev" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;UK device_id&lt;/b&gt; : VARCHAR(100)&lt;br&gt;&lt;b&gt;FK vehicle_id&lt;/b&gt; : INT [-&amp;gt; veh.id]&lt;br&gt;&lt;b&gt;• status&lt;/b&gt; : VARCHAR(50) (ONLINE/OFFLINE)&lt;br&gt;&lt;b&gt;• road_camera_status&lt;/b&gt; : VARCHAR(50)&lt;br&gt;&lt;b&gt;• cabin_camera_status&lt;/b&gt; : VARCHAR(50)&lt;br&gt;&lt;b&gt;• gps_status&lt;/b&gt; : VARCHAR(50)&lt;br&gt;&lt;b&gt;• dms_status&lt;/b&gt; : VARCHAR(50)&lt;br&gt;&lt;b&gt;• firmware_version&lt;/b&gt; : VARCHAR(50) (v2.4.1)&lt;br&gt;&lt;b&gt;• last_heartbeat_at&lt;/b&gt; : DATETIME&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#78350F;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="470" y="125" width="310" height="180" as="geometry" />
        </mxCell>

        <!-- device_heartbeats -->
        <mxCell id="h_hb" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;device_heartbeats&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#78350F;strokeColor=#78350F;align=center;" vertex="1" parent="1">
          <mxGeometry x="470" y="355" width="310" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_hb" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK device_id&lt;/b&gt; : VARCHAR [-&amp;gt; dev.device_id]&lt;br&gt;&lt;b&gt;• heartbeat_at&lt;/b&gt; : DATETIME&lt;br&gt;&lt;b&gt;• metrics_json&lt;/b&gt; : TEXT (CPU, GPU Temp, FPS)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#78350F;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="470" y="385" width="310" height="85" as="geometry" />
        </mxCell>

        <!-- driving_sessions -->
        <mxCell id="h_ses" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;driving_sessions&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#2563EB;strokeColor=#2563EB;align=center;" vertex="1" parent="1">
          <mxGeometry x="910" y="95" width="280" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_ses" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK company_id&lt;/b&gt; : INT [-&amp;gt; org.id]&lt;br&gt;&lt;b&gt;FK driver_id&lt;/b&gt; : INT [-&amp;gt; drivers.id]&lt;br&gt;&lt;b&gt;• start_time&lt;/b&gt; : DATETIME&lt;br&gt;&lt;b&gt;• end_time&lt;/b&gt; : DATETIME&lt;br&gt;&lt;b&gt;• total_minutes&lt;/b&gt; : FLOAT&lt;br&gt;&lt;i&gt;[Invariant: 1 Active Session / Driver]&lt;/i&gt;&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2563EB;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="910" y="125" width="280" height="135" as="geometry" />
        </mxCell>

        <!-- trip_events -->
        <mxCell id="h_tri" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;trip_events&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#2563EB;strokeColor=#2563EB;align=center;" vertex="1" parent="1">
          <mxGeometry x="910" y="315" width="280" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_tri" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK session_id&lt;/b&gt; : INT [-&amp;gt; ses.id]&lt;br&gt;&lt;b&gt;• event_type&lt;/b&gt; : VARCHAR(50) (GPS/BRAKE)&lt;br&gt;&lt;b&gt;• timestamp&lt;/b&gt; : DATETIME&lt;br&gt;&lt;b&gt;• latitude&lt;/b&gt; : FLOAT&lt;br&gt;&lt;b&gt;• longitude&lt;/b&gt; : FLOAT&lt;br&gt;&lt;b&gt;• speed_kmh&lt;/b&gt; : FLOAT&lt;br&gt;&lt;b&gt;• metadata_json&lt;/b&gt; : TEXT&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2563EB;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="910" y="345" width="280" height="150" as="geometry" />
        </mxCell>

        <!-- Arrows -->
        <mxCell id="r_veh_asg" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#EA580C;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_veh" target="h_asg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="r_veh_dev" value="1 : 1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#78350F;strokeWidth=1.8;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_veh" target="b_dev">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="r_dev_hb" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#78350F;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_dev" target="h_hb">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="r_ses_tri" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#2563EB;strokeWidth=1.8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_ses" target="h_tri">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
    """
    create_drawio_file("hinh_3_3b_erd_vehicles_sessions.drawio", "diag_3_3b", "Hình 3.3b ERD Vehicles & Sessions", cells, width=1300, height=600)

# ==============================================================================
# 6. HÌNH 3.3c: ERD PHÂN HỆ GIÁM SÁT VI PHẠM, BẰNG CHỨNG & HUẤN LUYỆN
# ==============================================================================
def gen_drawio_3_3c():
    cells = """
        <mxCell id="title" value="&lt;b&gt;&lt;font style=&quot;font-size: 20px; color: #0F172A;&quot;&gt;HÌNH 3.3c: ERD PHÂN HỆ GIÁM SÁT VI PHẠM, BẰNG CHỨNG AN NINH &amp;amp; ĐÀO TẠO AN TOÀN&lt;/font&gt;&lt;/b&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="100" y="20" width="1100" height="40" as="geometry" />
        </mxCell>
        <mxCell id="subtitle" value="&lt;font style=&quot;font-size: 13px; color: #64748B;&quot;&gt;Chu trình khép kín: Ghi nhận vi phạm AI &amp;gt; Ẩn danh ảnh SHA-256 &amp;gt; Thẩm định 2 bước Điều hành viên &amp;gt; Giao khóa huấn luyện phục hồi điểm&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="150" y="55" width="1000" height="25" as="geometry" />
        </mxCell>

        <!-- violations -->
        <mxCell id="h_vio" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;violations (Sự cố AI phát hiện)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#DC2626;strokeColor=#DC2626;align=center;" vertex="1" parent="1">
          <mxGeometry x="60" y="95" width="340" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_vio" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK company_id&lt;/b&gt; : INT [-&amp;gt; org.id]&lt;br&gt;&lt;b&gt;FK fleet_id&lt;/b&gt; : INT [-&amp;gt; fleets.id]&lt;br&gt;&lt;b&gt;FK driver_id&lt;/b&gt; : INT [-&amp;gt; drivers.id]&lt;br&gt;&lt;b&gt;FK vehicle_id&lt;/b&gt; : INT [-&amp;gt; vehicles.id]&lt;br&gt;&lt;b&gt;FK session_id&lt;/b&gt; : INT [-&amp;gt; sessions.id]&lt;br&gt;&lt;b&gt;• violation_type&lt;/b&gt; : VARCHAR(100) (drowsy/speed/seatbelt)&lt;br&gt;&lt;b&gt;• severity&lt;/b&gt; : VARCHAR(50) (INFO/WARNING/CRITICAL)&lt;br&gt;&lt;b&gt;• review_status&lt;/b&gt; : VARCHAR(50) (PENDING_REVIEW/CONFIRMED)&lt;br&gt;&lt;b&gt;• confidence&lt;/b&gt; : FLOAT (0.0 - 1.0)&lt;br&gt;&lt;b&gt;• speed_kph / limit_kph&lt;/b&gt; : FLOAT&lt;br&gt;&lt;b&gt;• image_path&lt;/b&gt; : VARCHAR(500) (Đã làm mờ mặt NĐ13)&lt;br&gt;&lt;b&gt;• detected_at&lt;/b&gt; : DATETIME&lt;br&gt;&lt;b&gt;• version&lt;/b&gt; : INT (Optimistic Concurrency Control)&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#DC2626;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="60" y="125" width="340" height="240" as="geometry" />
        </mxCell>

        <!-- violation_reviews -->
        <mxCell id="h_rev" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;violation_reviews (Thẩm định Điều hành)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#DC2626;strokeColor=#DC2626;align=center;" vertex="1" parent="1">
          <mxGeometry x="470" y="95" width="330" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_rev" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK violation_id&lt;/b&gt; : INT [-&amp;gt; violations.id]&lt;br&gt;&lt;b&gt;FK reviewer_id&lt;/b&gt; : INT [-&amp;gt; drivers.id]&lt;br&gt;&lt;b&gt;• action&lt;/b&gt; : VARCHAR(50) (CONFIRM/FALSE_POSITIVE)&lt;br&gt;&lt;b&gt;• old_review_status&lt;/b&gt; : VARCHAR(50)&lt;br&gt;&lt;b&gt;• new_review_status&lt;/b&gt; : VARCHAR(50)&lt;br&gt;&lt;b&gt;• note&lt;/b&gt; : TEXT (Bắt buộc giải trình &amp;ge; 5 ký tự)&lt;br&gt;&lt;b&gt;• created_at&lt;/b&gt; : DATETIME&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#DC2626;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="470" y="125" width="330" height="150" as="geometry" />
        </mxCell>

        <!-- coaching_assignments -->
        <mxCell id="h_coa" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;coaching_assignments (Huấn luyện)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#059669;strokeColor=#059669;align=center;" vertex="1" parent="1">
          <mxGeometry x="870" y="95" width="330" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_coa" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK company_id&lt;/b&gt; : INT [-&amp;gt; org.id]&lt;br&gt;&lt;b&gt;FK driver_id&lt;/b&gt; : INT [-&amp;gt; drivers.id]&lt;br&gt;&lt;b&gt;FK assigned_by&lt;/b&gt; : INT (Dispatcher)&lt;br&gt;&lt;b&gt;FK violation_id&lt;/b&gt; : INT [-&amp;gt; violations.id]&lt;br&gt;&lt;b&gt;• title&lt;/b&gt; : VARCHAR(255)&lt;br&gt;&lt;b&gt;• module_type&lt;/b&gt; : VARCHAR(50) (DMS/SPEED/SEATBELT)&lt;br&gt;&lt;b&gt;• status&lt;/b&gt; : VARCHAR(30) (ASSIGNED/COMPLETED)&lt;br&gt;&lt;b&gt;• score_restored&lt;/b&gt; : FLOAT (Phục hồi điểm an toàn)&lt;br&gt;&lt;b&gt;• completed_at&lt;/b&gt; : DATETIME&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#059669;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="870" y="125" width="330" height="180" as="geometry" />
        </mxCell>

        <!-- notifications -->
        <mxCell id="h_not" value="&lt;b&gt;&lt;font color=&quot;#ffffff&quot;&gt;notifications (Thông báo cảnh báo)&lt;/font&gt;&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#7C3AED;strokeColor=#7C3AED;align=center;" vertex="1" parent="1">
          <mxGeometry x="470" y="345" width="330" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_not" value="&lt;div style=&quot;line-height: 160%; font-size: 11px;&quot;&gt;&lt;b&gt;PK id&lt;/b&gt; : INT&lt;br&gt;&lt;b&gt;FK company_id&lt;/b&gt; : INT [-&amp;gt; org.id]&lt;br&gt;&lt;b&gt;FK user_id&lt;/b&gt; : INT [-&amp;gt; drivers.id]&lt;br&gt;&lt;b&gt;FK violation_id&lt;/b&gt; : INT [-&amp;gt; violations.id]&lt;br&gt;&lt;b&gt;• channel&lt;/b&gt; : VARCHAR(50) (WEBSOCKET/PUSH/SMS)&lt;br&gt;&lt;b&gt;• status&lt;/b&gt; : VARCHAR(30) (DELIVERED/READ)&lt;br&gt;&lt;b&gt;• sent_at&lt;/b&gt; : DATETIME&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7C3AED;strokeWidth=1.8;align=left;spacingLeft=12;verticalAlign=top;spacingTop=6;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="470" y="375" width="330" height="130" as="geometry" />
        </mxCell>

        <!-- Arrows -->
        <mxCell id="r_vio_rev" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#DC2626;strokeWidth=1.8;exitX=1;exitY=0.3;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_vio" target="b_rev">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="r_vio_coa" value="1 : 1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#059669;strokeWidth=1.8;exitX=1;exitY=0.1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_vio" target="b_coa">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="430" y="149" />
              <mxPoint x="430" y="80" />
              <mxPoint x="840" y="80" />
              <mxPoint x="840" y="215" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="r_vio_not" value="1 : N" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#7C3AED;strokeWidth=1.8;exitX=1;exitY=0.8;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="b_vio" target="b_not">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
    """
    create_drawio_file("hinh_3_3c_erd_violations_coaching.drawio", "diag_3_3c", "Hình 3.3c ERD Violations & Coaching", cells, width=1300, height=580)


# ==============================================================================
# HÀM XUẤT 6 ẢNH PNG ĐỘ NÉT CAO (300 DPI) CHO WORD
# ==============================================================================
def render_all_6_png_images():
    plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
    
    # -------------------------------------------------------------
    # 1. FIG 3.2a PNG
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14.5, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.add_patch(patches.Rectangle((0, 0), 100, 100, facecolor='#F8FAFC', zorder=0))

    ax.text(50, 96, "HINH 3.2a: PHAN LUONG CAM BIEN & XU LY THI GIAC KEP TAI BIEN (EDGE AI)",
            fontsize=13, fontweight='bold', ha='center', color='#0F172A')
    ax.text(50, 92.5, "Perception song song: Road-Facing ADAS mat duong & Driver-Facing DMS khoang lai tai xe",
            fontsize=9.2, ha='center', color='#64748B')

    # Road Box
    ax.add_patch(patches.FancyBboxPatch((4, 20), 44, 68, boxstyle="round,pad=0.5,rounding_size=1.5",
                                        facecolor='#FFFFFF', edgecolor='#0284C7', linewidth=2, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((4, 82), 44, 6, boxstyle="round,pad=0.2,rounding_size=0.8",
                                        facecolor='#0284C7', edgecolor='#0369A1', linewidth=1.5, zorder=3))
    ax.text(26, 85, "[KENH 1: ROAD-FACING ADAS PIPELINE]", fontsize=10, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
    road_desc = (
        "1. Thu nhan Frame: 1080p @ 30 FPS qua RTSP/WebRTC\n\n"
        "2. Dynamic ROI: Loai bo 30% vung troi, can bang sang CLAHE\n\n"
        "3. YOLOv8x: Nhan dien O to, Xe may, Xe tai & Nguoi di bo\n\n"
        "4. Bien bao QCVN 41:2019: Phat hien bien gioi han toc do\n\n"
        "5. ByteTrack: Gan ID quy dao on dinh, chong nhay ID\n\n"
        "6. Homography BEV: Chieu phang mat duong do khoang cach thuc (m)\n\n"
        "7. Tinh toan Thoi gian va cham TTC & Cu ly an toan TT 31/2019"
    )
    ax.text(6.5, 78, road_desc, fontsize=8.4, color='#1E293B', linespacing=1.25, va='top', zorder=4)

    # Road Output
    ax.add_patch(patches.FancyBboxPatch((4, 8), 44, 9, boxstyle="round,pad=0.3,rounding_size=1.0",
                                        facecolor='#E0F2FE', edgecolor='#0284C7', linewidth=1.8, zorder=2))
    ax.text(26, 12.5, "ROAD TELEMETRY JSON\nTTC (s), Khoang cach xe truoc (m), Van toc thuc, Bien bao QCVN 41",
            fontsize=8.2, fontweight='bold', ha='center', va='center', color='#0369A1', zorder=3)
    ax.annotate('', xy=(26, 17), xytext=(26, 20),
                arrowprops=dict(arrowstyle="-|>", color='#0284C7', lw=2.2, mutation_scale=15))

    # DMS Box
    ax.add_patch(patches.FancyBboxPatch((52, 20), 44, 68, boxstyle="round,pad=0.5,rounding_size=1.5",
                                        facecolor='#FFFFFF', edgecolor='#D97706', linewidth=2, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((52, 82), 44, 6, boxstyle="round,pad=0.2,rounding_size=0.8",
                                        facecolor='#D97706', edgecolor='#B45309', linewidth=1.5, zorder=3))
    ax.text(74, 85, "[KENH 2: DRIVER-FACING DMS PIPELINE]", fontsize=10, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
    dms_desc = (
        "1. Thu nhan Frame IR: Camera hong ngoai cabin chong choi dem\n\n"
        "2. MediaPipe Face Mesh: Trich xuat 468 moc toa do 3D (< 15ms)\n\n"
        "3. Dynamic Calibration: Hieu chuan ca nhan nguong mat mo/ngap\n\n"
        "4. 3D Head Pose (solvePnP): Tinh goc quay Pitch, Yaw, Roll\n\n"
        "5. Sinh trac hoc: Ty le mat mo EAR & tan suat ngap mieng MAR\n\n"
        "6. Sliding Window PERCLOS: Ty le nham mat trong cua so 60s (>15%)\n\n"
        "7. An toan: Giam sat that day an toan Seatbelt & Bo dem lai > 4h"
    )
    ax.text(54.5, 78, dms_desc, fontsize=8.4, color='#1E293B', linespacing=1.25, va='top', zorder=4)

    # DMS Output
    ax.add_patch(patches.FancyBboxPatch((52, 8), 44, 9, boxstyle="round,pad=0.3,rounding_size=1.0",
                                        facecolor='#FEF3C7', edgecolor='#D97706', linewidth=1.8, zorder=2))
    ax.text(74, 12.5, "DMS TELEMETRY JSON\nNgu gat (EAR/PERCLOS), Ngap (MAR), Goc quay dau, Day dai, Ca lai >4h",
            fontsize=8.2, fontweight='bold', ha='center', va='center', color='#92400E', zorder=3)
    ax.annotate('', xy=(74, 17), xytext=(74, 20),
                arrowprops=dict(arrowstyle="-|>", color='#D97706', lw=2.2, mutation_scale=15))

    ax.text(50, 2.5, "Hinh 3.2a: So do phan luong thu nhan & tien xu ly thi giac kep tai bien",
            fontsize=10, style='italic', fontweight='bold', ha='center', color='#1E293B')

    plt.tight_layout()
    p_32a = OUT_DIR / "fig_dual_stream_3_2a_edge_ai.png"
    fig.savefig(p_32a, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[OK] Generated PNG: {p_32a}")

    # -------------------------------------------------------------
    # 2. FIG 3.2b PNG
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14.5, 7.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.add_patch(patches.Rectangle((0, 0), 100, 100, facecolor='#F8FAFC', zorder=0))

    ax.text(50, 96, "HINH 3.2b: TRUNG TAM DIEU PHOI QUYET DINH FASTAPI CORE ENGINE",
            fontsize=13, fontweight='bold', ha='center', color='#0F172A')
    ax.text(50, 92.5, "Hang doi bat dong bo, Loc nhieu lien khung, Trong tai 3 cap uu tien & An danh Nghi dinh 13/2023",
            fontsize=9.2, ha='center', color='#64748B')

    # Top Ingestion
    ax.add_patch(patches.FancyBboxPatch((5, 81), 90, 8, boxstyle="round,pad=0.3,rounding_size=1.0",
                                        facecolor='#1E293B', edgecolor='#0F172A', linewidth=2, zorder=2))
    ax.text(50, 85, "1. WEBSOCKET ASYNC INGESTION & LOAD SHEDDER (Budget < 45ms)\nDong thoi tiep nhan Road Telemetry & DMS Telemetry - Bo qua frame tre > 45ms",
            fontsize=8.5, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=3)

    # Debounce
    ax.add_patch(patches.FancyBboxPatch((5, 68), 90, 8, boxstyle="round,pad=0.3,rounding_size=1.0",
                                        facecolor='#DBEAFE', edgecolor='#3B82F6', linewidth=1.8, zorder=2))
    ax.text(50, 72, "2. TEMPORAL PERSISTENCE FILTER (DEBOUNCE 3 - 8 FRAMES)\nDuy tri trang thai bat thuong qua 3-8 khung hinh de triet tieu chop mat sinh ly va nhieu cam bien",
            fontsize=8.5, fontweight='bold', ha='center', va='center', color='#1E3A8A', zorder=3)
    ax.annotate('', xy=(50, 76), xytext=(50, 81),
                arrowprops=dict(arrowstyle="-|>", color='#3B82F6', lw=2, mutation_scale=14))

    # 3 Priority Boxes
    # L1
    ax.add_patch(patches.FancyBboxPatch((5, 34), 28, 28, boxstyle="round,pad=0.4,rounding_size=1.2",
                                        facecolor='#FEF2F2', edgecolor='#DC2626', linewidth=2, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((5, 57.5), 28, 4.5, boxstyle="round,pad=0.1,rounding_size=0.6",
                                        facecolor='#DC2626', edgecolor='#B91C1C', linewidth=1.5, zorder=3))
    ax.text(19, 59.8, "CAP 1: CRITICAL (KHAN CAP)", fontsize=8.8, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
    l1_text = (
        "- TTC <= 1.5s (Va cham cuc gan)\n\n"
        "- Ngu gat nham mat > 5.0s\n\n"
        "==> Chiem quyen uu tien phat\n\n"
        "==> Coi hu bao dong am tan cao"
    )
    ax.text(7, 54, l1_text, fontsize=8.0, color='#7F1D1D', linespacing=1.2, va='top', zorder=4)

    # L2
    ax.add_patch(patches.FancyBboxPatch((36, 34), 28, 28, boxstyle="round,pad=0.4,rounding_size=1.2",
                                        facecolor='#FFFBEB', edgecolor='#D97706', linewidth=2, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((36, 57.5), 28, 4.5, boxstyle="round,pad=0.1,rounding_size=0.6",
                                        facecolor='#D97706', edgecolor='#B45309', linewidth=1.5, zorder=3))
    ax.text(50, 59.8, "CAP 2: WARNING (CANH BAO)", fontsize=8.8, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
    l2_text = (
        "- Chay qua toc do QCVN 41\n\n"
        "- Vi pham cu ly an toan TT 31\n\n"
        "- Met moi PERCLOS > 15%\n\n"
        "- Lai xe lien tuc vuot qua 4h"
    )
    ax.text(38, 54, l2_text, fontsize=8.0, color='#78350F', linespacing=1.2, va='top', zorder=4)

    # L3
    ax.add_patch(patches.FancyBboxPatch((67, 34), 28, 28, boxstyle="round,pad=0.4,rounding_size=1.2",
                                        facecolor='#EFF6FF', edgecolor='#2563EB', linewidth=2, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((67, 57.5), 28, 4.5, boxstyle="round,pad=0.1,rounding_size=0.6",
                                        facecolor='#2563EB', edgecolor='#1D4ED8', linewidth=1.5, zorder=3))
    ax.text(81, 59.8, "CAP 3: CAUTION (NHAC NHO)", fontsize=8.8, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
    l3_text = (
        "- Quen that day an toan Seatbelt\n\n"
        "- Bien bao khu dan cu\n\n"
        "- Bien bao duong cong nguy hiem\n\n"
        "==> Nhac nho nhe nhang, icon xanh"
    )
    ax.text(69, 54, l3_text, fontsize=8.0, color='#1E3A8A', linespacing=1.2, va='top', zorder=4)

    # Arrows to Levels
    ax.annotate('', xy=(19, 62), xytext=(25, 68), arrowprops=dict(arrowstyle="-|>", color='#DC2626', lw=1.8))
    ax.annotate('', xy=(50, 62), xytext=(50, 68), arrowprops=dict(arrowstyle="-|>", color='#D97706', lw=1.8))
    ax.annotate('', xy=(81, 62), xytext=(75, 68), arrowprops=dict(arrowstyle="-|>", color='#2563EB', lw=1.8))

    # Security Box
    ax.add_patch(patches.FancyBboxPatch((5, 19), 90, 10, boxstyle="round,pad=0.3,rounding_size=1.0",
                                        facecolor='#FAF5FF', edgecolor='#9333EA', linewidth=2, zorder=2))
    ax.text(50, 24, "3. PRIVACY ANONYMIZER & INTEGRITY GUARD (Nghi dinh 13/2023/ND-CP)\nChe mo khuon mat nguoi di duong & tai xe trong snapshot + Tao ma bam SHA-256 bao toan bang chung phap ly",
            fontsize=8.3, fontweight='bold', ha='center', va='center', color='#581C87', zorder=3)

    ax.annotate('', xy=(20, 29), xytext=(19, 34), arrowprops=dict(arrowstyle="-|>", color='#9333EA', lw=1.5))
    ax.annotate('', xy=(50, 29), xytext=(50, 34), arrowprops=dict(arrowstyle="-|>", color='#9333EA', lw=1.5))
    ax.annotate('', xy=(80, 29), xytext=(81, 34), arrowprops=dict(arrowstyle="-|>", color='#9333EA', lw=1.5))

    # Dispatcher Bottom
    ax.add_patch(patches.FancyBboxPatch((5, 7.5), 90, 7.5, boxstyle="round,pad=0.3,rounding_size=1.0",
                                        facecolor='#ECFDF5', edgecolor='#059669', linewidth=2, zorder=2))
    ax.text(50, 11.2, "4. REALTIME EVENT DISPATCHER (< 100ms)\nDong goi Payload canh bao va day dong thoi toi Audio TTS, Mobile HUD & Web Dashboard",
            fontsize=8.5, fontweight='bold', ha='center', va='center', color='#065F46', zorder=3)
    ax.annotate('', xy=(50, 15), xytext=(50, 19), arrowprops=dict(arrowstyle="-|>", color='#059669', lw=2.2, mutation_scale=14))

    ax.text(50, 2.5, "Hinh 3.2b: So do trung tam dieu phoi quyet dinh FastAPI Core Engine",
            fontsize=10, style='italic', fontweight='bold', ha='center', color='#1E293B')

    plt.tight_layout()
    p_32b = OUT_DIR / "fig_dual_stream_3_2b_decision_core.png"
    fig.savefig(p_32b, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[OK] Generated PNG: {p_32b}")

    # -------------------------------------------------------------
    # 3. FIG 3.2c PNG
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14.5, 7.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.add_patch(patches.Rectangle((0, 0), 100, 100, facecolor='#F8FAFC', zorder=0))

    ax.text(50, 96, "HINH 3.2c: DONG BO DAU RA DA KENH THOI GIAN THUC (< 100ms)",
            fontsize=13, fontweight='bold', ha='center', color='#0F172A')
    ax.text(50, 92.5, "Dong bo phan hoi tuc thoi: Coi bao & TTS tieng Viet trong xe, Kinh lai Mobile HUD & Web Dashboard",
            fontsize=9.2, ha='center', color='#64748B')

    # Top Bus
    ax.add_patch(patches.FancyBboxPatch((5, 80), 90, 8.5, boxstyle="round,pad=0.3,rounding_size=1.0",
                                        facecolor='#4F46E5', edgecolor='#3730A3', linewidth=2, zorder=2))
    ax.text(50, 84.2, "FASTAPI REALTIME BROADCAST BUS (DO TRE PHAN PHOI < 100ms)\nDay tin hieu dong bo da kenh toi cac thiet bi thu huong theo muc uu tien",
            fontsize=8.8, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=3)

    # 3 Channel Cards
    # Channel 1: Audio / TTS
    ax.add_patch(patches.FancyBboxPatch((5, 12), 28, 59, boxstyle="round,pad=0.4,rounding_size=1.2",
                                        facecolor='#FEF2F2', edgecolor='#DC2626', linewidth=2, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((5, 65), 28, 6, boxstyle="round,pad=0.1,rounding_size=0.6",
                                        facecolor='#DC2626', edgecolor='#B91C1C', linewidth=1.5, zorder=3))
    ax.text(19, 68, "KENH 1: AUDIO & TTS TRONG XE", fontsize=8.8, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
    c1_text = (
        "• Doi tuong: Tai xe dang lai xe\n\n"
        "• Coi Beeper khan cap:\n"
        "  - Phat xung am tan 500Hz - 2500Hz\n"
        "  - Danh thuc tuc thi khi ngu gat\n\n"
        "• Voice TTS Tieng Viet:\n"
        "  - Cau lenh ngan gon <= 8 tu\n"
        "  - 'Nguy hiem! Giam toc do!'\n"
        "  - 'Tai xe tap trung lai xe!'\n\n"
        "• Phan xa tai xe: Chi 0.3s - 0.5s"
    )
    ax.text(7, 61, c1_text, fontsize=8.0, color='#1E293B', linespacing=1.2, va='top', zorder=4)

    # Channel 2: Mobile HUD
    ax.add_patch(patches.FancyBboxPatch((36, 12), 28, 59, boxstyle="round,pad=0.4,rounding_size=1.2",
                                        facecolor='#FFFBEB', edgecolor='#D97706', linewidth=2, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((36, 65), 28, 6, boxstyle="round,pad=0.1,rounding_size=0.6",
                                        facecolor='#D97706', edgecolor='#B45309', linewidth=1.5, zorder=3))
    ax.text(50, 68, "KENH 2: MOBILE HUD KINH LAI", fontsize=8.8, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
    c2_text = (
        "• Nen tang: React Native App Taplo\n\n"
        "• Che do Head-Up Display (HUD):\n"
        "  - Chieu nguoc kinh lai ban dem\n"
        "  - Nen den OLED tuong phan cao\n\n"
        "• Hien thi truc quan:\n"
        "  - Van toc GPS so lon (60pt)\n"
        "  - Cu ly xe truoc & Bien bao duong\n"
        "  - Vien man hinh doi mau Xanh/Do\n\n"
        "• Khong gay phan tam tam nhin"
    )
    ax.text(38, 61, c2_text, fontsize=8.0, color='#1E293B', linespacing=1.2, va='top', zorder=4)

    # Channel 3: Web Dashboard
    ax.add_patch(patches.FancyBboxPatch((67, 12), 28, 59, boxstyle="round,pad=0.4,rounding_size=1.2",
                                        facecolor='#F0F9FF', edgecolor='#0284C7', linewidth=2, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((67, 65), 28, 6, boxstyle="round,pad=0.1,rounding_size=0.6",
                                        facecolor='#0284C7', edgecolor='#0369A1', linewidth=1.5, zorder=3))
    ax.text(81, 68, "KENH 3: WEB FLEET DASHBOARD", fontsize=8.8, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
    c3_text = (
        "• Nen tang: Next.js 14 Web Portal\n\n"
        "• Do hoa Canvas 2D 60 FPS:\n"
        "  - Render muot ma telemetry truc tiep\n\n"
        "• Ban do so GIS GPS Realtime:\n"
        "  - Giam sat vi tri toan doi xe\n\n"
        "• Canh bao Dieu hanh vien:\n"
        "  - Popup chuong bao do khi co Cap 1\n"
        "  - Xem snapshot mo & ho tro tuc thi"
    )
    ax.text(69, 61, c3_text, fontsize=8.0, color='#1E293B', linespacing=1.2, va='top', zorder=4)

    # Arrows from Bus
    ax.annotate('', xy=(19, 71), xytext=(25, 80), arrowprops=dict(arrowstyle="-|>", color='#DC2626', lw=2, mutation_scale=15))
    ax.annotate('', xy=(50, 71), xytext=(50, 80), arrowprops=dict(arrowstyle="-|>", color='#D97706', lw=2, mutation_scale=15))
    ax.annotate('', xy=(81, 71), xytext=(75, 80), arrowprops=dict(arrowstyle="-|>", color='#0284C7', lw=2, mutation_scale=15))

    ax.text(50, 3, "Hinh 3.2c: So do dong bo dau ra da kenh thoi gian thuc (< 100ms)",
            fontsize=10, style='italic', fontweight='bold', ha='center', color='#1E293B')

    plt.tight_layout()
    p_32c = OUT_DIR / "fig_dual_stream_3_2c_output_sync.png"
    fig.savefig(p_32c, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[OK] Generated PNG: {p_32c}")

    # -------------------------------------------------------------
    # 4. FIG 3.3a PNG (ERD ORG & RBAC)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14.5, 8.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.add_patch(patches.Rectangle((0, 0), 100, 100, facecolor='#F8FAFC', zorder=0))

    ax.text(50, 96.5, "HINH 3.3a: ERD PHAN HE QUAN TRI TO CHUC DA CAP & PHAN QUYEN RBAC",
            fontsize=13, fontweight='bold', ha='center', color='#0F172A')
    ax.text(50, 93.5, "Kien truc da khach hang (Multi-tenancy): To chuc > Chi nhanh > Doi xe, Tai khoan & Ma tran quyen RBAC",
            fontsize=9.2, ha='center', color='#64748B')

    def draw_box(x, y, w, h, title, fields, color):
        ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.0",
                                            facecolor='#FFFFFF', edgecolor=color, linewidth=1.8, zorder=2))
        ax.add_patch(patches.FancyBboxPatch((x, y + h - 5.5), w, 5.5, boxstyle="round,pad=0.1,rounding_size=0.8",
                                            facecolor=color, edgecolor=color, linewidth=1.5, zorder=3))
        ax.text(x + w/2, y + h - 2.8, title, fontsize=9.2, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
        ax.text(x + 1.8, y + h - 7.5, "\n".join(fields), fontsize=7.7, color='#1E293B', va='top', linespacing=1.35, zorder=4)

    # Column 1
    draw_box(5, 68, 27, 21, "organizations",
             ["PK id : INT", "- name : VARCHAR(200)", "- code : VARCHAR(50) [UNIQUE]", "- tax_code : VARCHAR(50)", "- is_active : BOOLEAN", "- created_at : DATETIME"], "#1D4ED8")
    draw_box(5, 38, 27, 21, "branches",
             ["PK id : INT", "FK company_id : INT [-> org.id]", "- name : VARCHAR(200)", "- code : VARCHAR(50)", "- status : VARCHAR(20) (active)", "- created_at : DATETIME"], "#1D4ED8")
    draw_box(5, 8, 27, 21, "fleets",
             ["PK id : INT", "FK company_id : INT [-> org.id]", "FK branch_id : INT [-> bra.id]", "- name : VARCHAR(200)", "- code : VARCHAR(50)", "- status : VARCHAR(20)"], "#1D4ED8")

    # Column 2
    draw_box(37, 50, 27, 39, "drivers (Users / Accounts)",
             ["PK id : INT", "FK company_id : INT [-> org.id]", "FK branch_id : INT [-> bra.id]", "FK role_id : INT [-> roles.id]", "- email : VARCHAR [UNIQUE]", "- password_hash : VARCHAR (Bcrypt)", "- full_name : VARCHAR", "- role : VARCHAR (ADMIN/DRIVER)", "- safety_score : FLOAT (100.0)", "- is_active : BOOLEAN", "- created_at : DATETIME"], "#059669")
    draw_box(37, 10, 27, 30, "audit_logs",
             ["PK id : INT", "FK company_id : INT [-> org.id]", "FK user_id : INT [-> drivers.id]", "- action : VARCHAR (CREATE/UPDATE)", "- resource : VARCHAR", "- ip_address : VARCHAR", "- timestamp : DATETIME"], "#64748B")

    # Column 3
    draw_box(69, 68, 27, 21, "roles",
             ["PK id : INT", "- code : VARCHAR(50) [UNIQUE]", "- name : VARCHAR(100)", "- default_scope : VARCHAR(50)", "- description : VARCHAR(500)"], "#7C3AED")
    draw_box(69, 44, 27, 15, "role_permissions (N:N)",
             ["PK,FK role_id : INT [-> roles.id]", "PK,FK permission_id : INT [-> perms.id]"], "#7C3AED")
    draw_box(69, 10, 27, 25, "permissions",
             ["PK id : INT", "- code : VARCHAR(100) [UNIQUE]", "- name : VARCHAR(200)", "- module : VARCHAR(100)", "- description : VARCHAR(500)"], "#7C3AED")

    # Connectors
    ax.annotate('1:N', xy=(18.5, 59), xytext=(18.5, 68), arrowprops=dict(arrowstyle="-|>", color='#1D4ED8', lw=1.8), fontsize=7.5, color='#1D4ED8', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(18.5, 29), xytext=(18.5, 38), arrowprops=dict(arrowstyle="-|>", color='#1D4ED8', lw=1.8), fontsize=7.5, color='#1D4ED8', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(37, 78.5), xytext=(32, 78.5), arrowprops=dict(arrowstyle="-|>", color='#059669', lw=1.8), fontsize=7.5, color='#059669', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(50.5, 40), xytext=(50.5, 50), arrowprops=dict(arrowstyle="-|>", color='#64748B', lw=1.8), fontsize=7.5, color='#64748B', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(64, 75), xytext=(69, 78.5), arrowprops=dict(arrowstyle="-|>", color='#7C3AED', lw=1.8), fontsize=7.5, color='#7C3AED', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(82.5, 59), xytext=(82.5, 68), arrowprops=dict(arrowstyle="-|>", color='#7C3AED', lw=1.8), fontsize=7.5, color='#7C3AED', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('N:1', xy=(82.5, 35), xytext=(82.5, 44), arrowprops=dict(arrowstyle="-|>", color='#7C3AED', lw=1.8), fontsize=7.5, color='#7C3AED', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))

    ax.text(50, 2.5, "Hinh 3.3a: So do quan he thuc the phan he quan tri to chuc da cap & phan quyen RBAC",
            fontsize=10, style='italic', fontweight='bold', ha='center', color='#1E293B')

    plt.tight_layout()
    p_33a = OUT_DIR / "fig_erd_3_3a_org_rbac.png"
    fig.savefig(p_33a, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[OK] Generated PNG: {p_33a}")

    # -------------------------------------------------------------
    # 5. FIG 3.3b PNG (ERD VEHICLES & SESSIONS)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14.5, 8.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.add_patch(patches.Rectangle((0, 0), 100, 100, facecolor='#F8FAFC', zorder=0))

    ax.text(50, 96.5, "HINH 3.3b: ERD PHAN HE PHUONG TIEN, THIET BI CAM BIEN & HANH TRINH LAI XE",
            fontsize=13, fontweight='bold', ha='center', color='#0F172A')
    ax.text(50, 93.5, "Quan ly doi xe, Ban giao xe tai xe, Suc khoe 7 cam bien Edge AI & Su kien viễn trac GPS",
            fontsize=9.2, ha='center', color='#64748B')

    # Col 1
    draw_box(5, 52, 27, 34, "vehicles",
             ["PK id : INT", "FK company_id : INT [-> org.id]", "FK branch_id : INT [-> bra.id]", "FK fleet_id : INT [-> fleets.id]", "- license_plate : VARCHAR [UNIQUE]", "- vehicle_type : VARCHAR (car/truck)", "- status : VARCHAR (active)"], "#EA580C")
    draw_box(5, 10, 27, 34, "vehicle_assignments",
             ["PK id : INT", "FK company_id : INT [-> org.id]", "FK vehicle_id : INT [-> veh.id]", "FK driver_id : INT [-> drv.id]", "- assigned_from : DATETIME", "- assigned_to : DATETIME", "FK assigned_by : INT (Dispatcher)", "- status : VARCHAR (active/ended)"], "#EA580C")

    # Col 2
    draw_box(37, 44, 27, 42, "device_health",
             ["PK id : INT", "UK device_id : VARCHAR(100)", "FK vehicle_id : INT [-> veh.id]", "- status : VARCHAR (ONLINE)", "- road_camera_status : VARCHAR", "- cabin_camera_status : VARCHAR", "- gps_status : VARCHAR", "- dms_status : VARCHAR", "- firmware_version : VARCHAR (v2.4.1)", "- last_heartbeat_at : DATETIME"], "#78350F")
    draw_box(37, 10, 27, 24, "device_heartbeats",
             ["PK id : INT", "FK device_id : VARCHAR [-> dev.id]", "- heartbeat_at : DATETIME", "- metrics_json : TEXT (CPU, Temp, FPS)"], "#78350F")

    # Col 3
    draw_box(69, 52, 27, 34, "driving_sessions",
             ["PK id : INT", "FK company_id : INT [-> org.id]", "FK driver_id : INT [-> drv.id]", "- start_time : DATETIME", "- end_time : DATETIME", "- total_minutes : FLOAT", "[Invariant: 1 Active Session/Drv]"], "#2563EB")
    draw_box(69, 10, 27, 34, "trip_events",
             ["PK id : INT", "FK session_id : INT [-> ses.id]", "- event_type : VARCHAR (GPS/BRAKE)", "- timestamp : DATETIME", "- latitude : FLOAT", "- longitude : FLOAT", "- speed_kmh : FLOAT", "- metadata_json : TEXT"], "#2563EB")

    # Connectors
    ax.annotate('1:N', xy=(18.5, 44), xytext=(18.5, 52), arrowprops=dict(arrowstyle="-|>", color='#EA580C', lw=1.8), fontsize=7.5, color='#EA580C', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:1', xy=(37, 70), xytext=(32, 70), arrowprops=dict(arrowstyle="-|>", color='#78350F', lw=1.8), fontsize=7.5, color='#78350F', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(50.5, 34), xytext=(50.5, 44), arrowprops=dict(arrowstyle="-|>", color='#78350F', lw=1.8), fontsize=7.5, color='#78350F', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(82.5, 44), xytext=(82.5, 52), arrowprops=dict(arrowstyle="-|>", color='#2563EB', lw=1.8), fontsize=7.5, color='#2563EB', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))

    ax.text(50, 2.5, "Hinh 3.3b: So do quan he thuc the phan he phuong tien, thiet bi & hanh trinh lai xe",
            fontsize=10, style='italic', fontweight='bold', ha='center', color='#1E293B')

    plt.tight_layout()
    p_33b = OUT_DIR / "fig_erd_3_3b_vehicles_sessions.png"
    fig.savefig(p_33b, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[OK] Generated PNG: {p_33b}")

    # -------------------------------------------------------------
    # 6. FIG 3.3c PNG (ERD VIOLATIONS & COACHING)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14.5, 8.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.add_patch(patches.Rectangle((0, 0), 100, 100, facecolor='#F8FAFC', zorder=0))

    ax.text(50, 96.5, "HINH 3.3c: ERD PHAN HE GIAM SAT VI PHAM, BANG CHUNG AN NINH & HUAN LUYEN",
            fontsize=13, fontweight='bold', ha='center', color='#0F172A')
    ax.text(50, 93.5, "Chu trinh khep kin: AI phat hien > An danh anh SHA-256 > Tham dinh 2 buoc > Huan luyen phuc hoi diem",
            fontsize=9.2, ha='center', color='#64748B')

    # Col 1: Violations
    draw_box(5, 15, 28, 71, "violations",
             ["PK id : INT", "FK company_id : INT [-> org.id]", "FK fleet_id : INT [-> fleets.id]", "FK driver_id : INT [-> drv.id]", "FK vehicle_id : INT [-> veh.id]", "FK session_id : INT [-> ses.id]", "- violation_type : VARCHAR (drowsy/speed)", "- severity : VARCHAR (WARNING/CRITICAL)", "- review_status : VARCHAR (PENDING)", "- confidence : FLOAT (0.0 - 1.0)", "- speed_kph / limit_kph : FLOAT", "- image_path : VARCHAR (Mo mat ND13)", "- detected_at : DATETIME", "- version : INT (Optimistic OCC)"], "#DC2626")

    # Col 2: Reviews & Notifications
    draw_box(37, 50, 27, 36, "violation_reviews",
             ["PK id : INT", "FK violation_id : INT [-> vio.id]", "FK reviewer_id : INT [-> drv.id]", "- action : VARCHAR (CONFIRM/FALSE_POS)", "- old_review_status : VARCHAR", "- new_review_status : VARCHAR", "- note : TEXT (Giai trinh >= 5 ky tu)", "- created_at : DATETIME"], "#DC2626")
    draw_box(37, 15, 27, 28, "notifications",
             ["PK id : INT", "FK company_id : INT [-> org.id]", "FK user_id : INT [-> drv.id]", "FK violation_id : INT [-> vio.id]", "- channel : VARCHAR (WEBSOCKET/SMS)", "- status : VARCHAR (DELIVERED)", "- sent_at : DATETIME"], "#7C3AED")

    # Col 3: Coaching Assignments
    draw_box(69, 36, 27, 50, "coaching_assignments",
             ["PK id : INT", "FK company_id : INT [-> org.id]", "FK driver_id : INT [-> drv.id]", "FK assigned_by : INT (Dispatcher)", "FK violation_id : INT [-> vio.id]", "- title : VARCHAR(255)", "- module_type : VARCHAR (DMS/SPEED)", "- status : VARCHAR (ASSIGNED/COMPLETED)", "- score_restored : FLOAT (+5.0 diem)", "- completed_at : DATETIME"], "#059669")

    # Connectors
    ax.annotate('1:N', xy=(37, 68), xytext=(33, 68), arrowprops=dict(arrowstyle="-|>", color='#DC2626', lw=1.8), fontsize=7.5, color='#DC2626', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:N', xy=(37, 29), xytext=(33, 29), arrowprops=dict(arrowstyle="-|>", color='#7C3AED', lw=1.8), fontsize=7.5, color='#7C3AED', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate('1:1', xy=(69, 61), xytext=(64, 61), arrowprops=dict(arrowstyle="-|>", color='#059669', lw=1.8), fontsize=7.5, color='#059669', ha='center', va='center', bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))

    ax.text(50, 2.5, "Hinh 3.3c: So do quan he thuc the phan he giam sat vi pham, bang chung & huan luyen",
            fontsize=10, style='italic', fontweight='bold', ha='center', color='#1E293B')

    plt.tight_layout()
    p_33c = OUT_DIR / "fig_erd_3_3c_violations_coaching.png"
    fig.savefig(p_33c, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[OK] Generated PNG: {p_33c}")

def main():
    print("=== DANG KHOI TAO VA XUAT BO 6 SO DO CHUYEN NGHIEP ===")
    gen_drawio_3_2a()
    gen_drawio_3_2b()
    gen_drawio_3_2c()
    gen_drawio_3_3a()
    gen_drawio_3_3b()
    gen_drawio_3_3c()
    print("=== DANG XUAT 6 ANH PNG DO NET CAO 300 DPI ===")
    render_all_6_png_images()
    print("=== HOAN TAT 100%! TAT CA FILE DA SAN SANG TRONG report_assets/ ===")

if __name__ == "__main__":
    main()
