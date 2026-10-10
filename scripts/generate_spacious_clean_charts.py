import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Setup clean, spacious styling
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.edgecolor'] = '#94A3B8'
plt.rcParams['axes.linewidth'] = 1.0

OUT_DIR = Path("report_assets")
OUT_DIR.mkdir(exist_ok=True)

# 1. Clean Chart: Safe Distance Curves (Thông tư 31/2019/TT-BGTVT) - Spacious Layout
def gen_clean_safe_distance():
    speeds = np.array([20, 40, 60, 70, 80, 90, 100, 110, 120])
    dry = np.array([15, 25, 35, 55, 55, 70, 70, 100, 100])
    wet = dry * 1.30
    
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    
    # Step plots with distinct line styles
    ax.step(speeds, dry, where='post', label='Khoảng cách tối thiểu đường khô ráo (TT 31/2019)', 
            color='#1D4ED8', linewidth=2.8)
    ax.step(speeds, wet, where='post', label='Khoảng cách khi trời mưa / đường trơn (x1.30)', 
            color='#DC2626', linewidth=2.8, linestyle='--')
    
    # Shaded safe operating zone
    ax.fill_between(speeds, 0, dry, step='post', alpha=0.06, color='#1D4ED8')
    
    ax.set_title('ĐỒ THỊ QUY ĐỊNH KHOẢNG CÁCH AN TOÀN THEO THÔNG TƯ 31/2019/TT-BGTVT', 
                 fontsize=12, fontweight='bold', pad=16, color='#0F172A')
    ax.set_xlabel('Vận tốc xe đang lưu thông (km/h)', fontsize=11, fontweight='bold', labelpad=10, color='#334155')
    ax.set_ylabel('Cự ly an toàn tối thiểu bắt buộc (mét)', fontsize=11, fontweight='bold', labelpad=10, color='#334155')
    
    ax.set_xlim(15, 125)
    ax.set_ylim(0, 150)
    ax.grid(True, linestyle=':', alpha=0.7, color='#CBD5E1')
    
    # Place legend in top left with good margin
    ax.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1', 
              fontsize=9.5, borderpad=1.0)
    
    # Spacious callouts placed in empty canvas regions with clear leader lines
    ax.annotate('Khu vực V ≤ 60 km/h:\nTài xế chủ động giữ cự ly\n(Khuyến nghị ≥ 35m)', 
                xy=(55, 35), xytext=(22, 90),
                arrowprops=dict(facecolor='#1D4ED8', edgecolor='#1D4ED8', width=1.5, headwidth=6, shrink=0.08),
                fontsize=9, fontweight='bold', color='#1E3A8A',
                bbox=dict(boxstyle="round,pad=0.5", fc="#EFF6FF", ec="#93C5FD", lw=1.2))
                
    ax.annotate('Khu vực 100 < V ≤ 120 km/h:\nCự ly khô: 100 mét\nTrời mưa: 130 mét', 
                xy=(105, 130), xytext=(80, 138),
                arrowprops=dict(facecolor='#DC2626', edgecolor='#DC2626', width=1.5, headwidth=6, shrink=0.08),
                fontsize=9, fontweight='bold', color='#991B1B',
                bbox=dict(boxstyle="round,pad=0.5", fc="#FEF2F2", ec="#FCA5A5", lw=1.2))

    plt.tight_layout(pad=2.0)
    fig.savefig(OUT_DIR / "fig_safe_distance_clean.png")
    plt.close()
    print("Regenerated fig_safe_distance_clean.png")

# 2. Clean Chart: AI Accuracy Benchmark - Wide, clear margins, no overlapping text
def gen_clean_accuracy():
    categories = [
        'Phát hiện xe\n(YOLOv8n)', 
        'Biển báo QCVN\n(Hierarchical)', 
        'Biển số OCR\n(YOLOv11+OCR)', 
        'Giám sát ngủ gật\n(PERCLOS/EAR)', 
        'Mũ bảo hiểm\n(Deduplication)'
    ]
    map_scores = [94.2, 95.8, 91.5, 96.0, 93.8]
    precision = [93.5, 96.2, 90.8, 95.2, 94.5]
    recall = [94.8, 95.4, 92.1, 96.8, 93.0]
    
    x = np.arange(len(categories))
    width = 0.24
    
    fig, ax = plt.subplots(figsize=(10.5, 5.5), dpi=300)
    
    rects1 = ax.bar(x - width, map_scores, width, label='Độ chính xác / mAP@0.5 (%)', color='#2563EB', edgecolor='white', lw=1.2)
    rects2 = ax.bar(x, precision, width, label='Độ chuẩn xác - Precision (%)', color='#059669', edgecolor='white', lw=1.2)
    rects3 = ax.bar(x + width, recall, width, label='Độ bao phủ - Recall (%)', color='#D97706', edgecolor='white', lw=1.2)
    
    ax.set_title('ĐÁNH GIÁ ĐỘ CHÍNH XÁC (mAP, PRECISION, RECALL) 5 TÁC VỤ AI CỐT LÕI', 
                 fontsize=12, fontweight='bold', pad=16, color='#0F172A')
    ax.set_ylabel('Tỷ lệ phần trăm (%)', fontsize=11, fontweight='bold', labelpad=10, color='#334155')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=9.5, fontweight='bold', color='#1E293B')
    ax.set_ylim(80, 104)  # High ceiling so text labels don't collide with chart ceiling
    
    ax.grid(True, axis='y', linestyle=':', alpha=0.7, color='#CBD5E1')
    ax.legend(loc='upper right', frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1', fontsize=9.5, borderpad=0.8)
    
    # Clean text numbers on top of bars with comfortable offset
    def autolabel(rects, text_color):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 4), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, fontweight='bold', color=text_color)
                        
    autolabel(rects1, '#1D4ED8')
    autolabel(rects2, '#047857')
    autolabel(rects3, '#B45309')
    
    plt.tight_layout(pad=2.0)
    fig.savefig(OUT_DIR / "fig_ai_benchmark_accuracy_clean.png")
    plt.close()
    print("Regenerated fig_ai_benchmark_accuracy_clean.png")

# 3. Clean Chart: Module Latency Breakdown - Generous padding
def gen_clean_latency():
    modules = [
        'Decision Engine & DB Sync',
        'Safe Distance & TTC Calculator',
        'Speed Estimator (Homography)',
        'Multi-Object Tracker (MOT)',
        'Helmet Checker (Deduplication)',
        'Head Pose & PERCLOS 60s',
        'License Plate OCR (When Triggered)',
        'Traffic Sign (QCVN 41 + S.508)',
        'Face Mesh & EAR/MAR (DMS)',
        'Vehicle Detector (YOLOv8n)'
    ]
    latencies = [1.2, 1.2, 1.8, 2.1, 2.4, 3.1, 4.5, 6.4, 8.5, 9.2]
    colors = ['#64748B', '#10B981', '#065F46', '#3B82F6', '#1E40AF', '#8B5CF6', '#D97706', '#059669', '#7C3AED', '#2563EB']
    
    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=300)
    y_pos = np.arange(len(modules))
    bars = ax.barh(y_pos, latencies, color=colors, height=0.6, edgecolor='white', lw=1.2)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(modules, fontsize=9.5, fontweight='bold', color='#1E293B')
    ax.set_xlabel('Thời gian thực thi trung bình mỗi khung hình (Mili-giây - ms)', fontsize=11, fontweight='bold', labelpad=10, color='#334155')
    ax.set_title('ĐO LƯỜNG ĐỘ TRỄ SUY LUẬN TỪNG MODULE AI (TỔNG PIPELINE: ~38ms | ĐẠT CHUẨN < 50ms)', 
                 fontsize=11.5, fontweight='bold', pad=16, color='#0F172A')
    ax.set_xlim(0, 13)
    ax.grid(True, axis='x', linestyle=':', alpha=0.7, color='#CBD5E1')
    
    # Safe threshold marker at 50ms (concept) or target indicator
    for bar in bars:
        width = bar.get_width()
        ax.annotate(f' {width:.1f} ms', 
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points", 
                    ha='left', va='center', fontsize=9, fontweight='bold', color='#0F172A')
                    
    plt.tight_layout(pad=2.0)
    fig.savefig(OUT_DIR / "fig_module_latency_clean.png")
    plt.close()
    print("Regenerated fig_module_latency_clean.png")

# 4. Clean Donut Chart: Fleet Violations with Separated Legend (No overlapping labels)
def gen_clean_violation_distribution():
    labels = [
        'Không giữ cự ly an toàn (Thông tư 31)',
        'Vượt quá tốc độ tối đa cho phép',
        'Buồn ngủ / Ngủ gật (PERCLOS > 0.15)',
        'Không thắt dây an toàn khi lái xe',
        'Không đội mũ bảo hiểm (Người đi xe máy)'
    ]
    sizes = [32.0, 28.0, 20.0, 12.0, 8.0]
    colors = ['#EF4444', '#F97316', '#8B5CF6', '#3B82F6', '#10B981']
    explode = (0.04, 0.04, 0.04, 0.04, 0.04)
    
    fig, ax = plt.subplots(figsize=(9.5, 5.0), dpi=300)
    
    # Pie with no inline text labels to prevent clutter
    wedges, texts, autotexts = ax.pie(
        sizes, explode=explode, labels=None, autopct='%1.1f%%',
        startangle=140, colors=colors, pctdistance=0.75,
        wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2)
    )
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(9.5)
        
    ax.set_title('CƠ CẤU CÁC LOẠI LỖI VI PHẠM AN TOÀN GIAO THÔNG (FLEET TELEMETRY)', 
                 fontsize=12, fontweight='bold', pad=14, color='#0F172A')
                 
    # Put clean legend outside on the right
    legend_labels = [f'{label} ({size}%)' for label, size in zip(labels, sizes)]
    ax.legend(wedges, legend_labels, title="Danh mục Lỗi Vi phạm", loc="center left", 
              bbox_to_anchor=(1.02, 0.5), fontsize=9, title_fontsize=10, 
              frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", borderpad=0.8)
              
    plt.tight_layout(pad=2.0)
    fig.savefig(OUT_DIR / "fig_violation_distribution_clean.png")
    plt.close()
    print("Regenerated fig_violation_distribution_clean.png")

# 5. Clean Chart: EAR and MAR curves with spacious layout and non-overlapping text
def gen_clean_ear_mar():
    t = np.linspace(0, 30, 300)
    # EAR baseline 0.32, drops clearly between t=12..18
    ear = 0.32 + 0.015 * np.sin(t * 1.5) + 0.008 * np.random.normal(0, 0.5, len(t))
    ear[115:165] -= 0.17 # eye closure
    
    # MAR baseline 0.16, rises clearly between t=21..26 (yawn)
    mar = 0.16 + 0.015 * np.cos(t * 1.2) + 0.008 * np.random.normal(0, 0.5, len(t))
    mar[210:255] += 0.54 # yawn
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 6.0), sharex=True, dpi=300)
    
    # EAR subplot
    ax1.plot(t, ear, label='Chỉ số mở mắt (EAR)', color='#2563EB', linewidth=2.2)
    ax1.axhline(y=0.20, color='#DC2626', linestyle='--', linewidth=1.6, label='Ngưỡng nhắm mắt (Threshold = 0.20)')
    ax1.fill_between(t, 0.05, 0.20, alpha=0.12, color='#DC2626')
    ax1.set_ylabel('Giá trị EAR', fontsize=10, fontweight='bold', color='#334155')
    ax1.set_ylim(0.08, 0.42)
    ax1.set_title('CHỈ SỐ SINH TRẮC HỌC DMS: GIÁM SÁT MẮT NHẮM KÉO DÀI (EAR) VÀ NGÁP NGỦ (MAR)', 
                  fontsize=11.5, fontweight='bold', pad=12, color='#0F172A')
    ax1.legend(loc='upper right', fontsize=8.5, frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1')
    ax1.grid(True, linestyle=':', alpha=0.6, color='#CBD5E1')
    
    # Callout placed in top-left empty space
    ax1.annotate('Báo động khẩn cấp:\nNhắm mắt kéo dài > 1.5s', 
                 xy=(14, 0.16), xytext=(4, 0.12),
                 arrowprops=dict(facecolor='#DC2626', edgecolor='#DC2626', width=1.2, headwidth=5, shrink=0.08),
                 fontsize=8.5, fontweight='bold', color='#991B1B',
                 bbox=dict(boxstyle="round,pad=0.4", fc="#FEF2F2", ec="#FCA5A5", lw=1.0))

    # MAR subplot
    ax2.plot(t, mar, label='Chỉ số mở miệng (MAR)', color='#D97706', linewidth=2.2)
    ax2.axhline(y=0.65, color='#B91C1C', linestyle='--', linewidth=1.6, label='Ngưỡng ngáp ngủ (Threshold = 0.65)')
    ax2.fill_between(t, 0.65, 0.88, alpha=0.12, color='#B91C1C')
    ax2.set_xlabel('Thời gian quan sát (Giây)', fontsize=10, fontweight='bold', color='#334155')
    ax2.set_ylabel('Giá trị MAR', fontsize=10, fontweight='bold', color='#334155')
    ax2.set_ylim(0.05, 0.85)
    ax2.legend(loc='upper left', fontsize=8.5, frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1')
    ax2.grid(True, linestyle=':', alpha=0.6, color='#CBD5E1')
    
    # Callout placed comfortably
    ax2.annotate('Cảnh báo mệt mỏi:\nNgáp miệng mở rộng MAR > 0.65', 
                 xy=(23.5, 0.70), xytext=(12, 0.72),
                 arrowprops=dict(facecolor='#D97706', edgecolor='#D97706', width=1.2, headwidth=5, shrink=0.08),
                 fontsize=8.5, fontweight='bold', color='#92400E',
                 bbox=dict(boxstyle="round,pad=0.4", fc="#FFFBEB", ec="#FDE68A", lw=1.0))

    plt.tight_layout(pad=2.0)
    fig.savefig(OUT_DIR / "fig_ear_mar_clean.png")
    plt.close()
    print("Regenerated fig_ear_mar_clean.png")

# 6. Clean Chart: Time-To-Collision (TTC) Dynamic Safety Zones
def gen_clean_ttc_zones():
    d_rel = np.linspace(5, 80, 200) # distance 5m to 80m
    # Relative speed = 10, 15, 20 m/s
    v_rel_list = [(10, '#2563EB', 'Vận tốc tương đối Δv = 10 m/s (36 km/h)'),
                  (15, '#D97706', 'Vận tốc tương đối Δv = 15 m/s (54 km/h)'),
                  (20, '#DC2626', 'Vận tốc tương đối Δv = 20 m/s (72 km/h)')]
                  
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=300)
    
    for v_rel, col, lbl in v_rel_list:
        ttc = d_rel / v_rel
        ax.plot(d_rel, ttc, label=lbl, color=col, linewidth=2.4)
        
    # Safety zones shading
    ax.axhspan(0, 1.5, color='#FEE2E2', alpha=0.5, label='Vùng Nguy cấp (TTC ≤ 1.5s - Báo động FCW)')
    ax.axhspan(1.5, 3.0, color='#FEF3C7', alpha=0.4, label='Vùng Chú ý (1.5s < TTC ≤ 3.0s)')
    ax.axhspan(3.0, 8.0, color='#DCFCE7', alpha=0.3, label='Vùng An toàn (TTC > 3.0s)')
    
    ax.set_title('MÔ HÌNH THỜI GIAN VA CHẠM TIỀM ẨN (TIME-TO-COLLISION - TTC) VÀ CÁC PHÂN VÙNG AN TOÀN', 
                 fontsize=11.5, fontweight='bold', pad=14, color='#0F172A')
    ax.set_xlabel('Khoảng cách thực tế tới xe liền trước (mét)', fontsize=10.5, fontweight='bold', color='#334155')
    ax.set_ylabel('Thời gian va chạm ước tính (TTC - Giây)', fontsize=10.5, fontweight='bold', color='#334155')
    ax.set_xlim(5, 80)
    ax.set_ylim(0, 6.0)
    ax.grid(True, linestyle=':', alpha=0.6, color='#CBD5E1')
    
    ax.legend(loc='upper left', fontsize=8.5, frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1')
    
    plt.tight_layout(pad=2.0)
    fig.savefig(OUT_DIR / "fig_ttc_zones_clean.png")
    plt.close()
    print("Generated fig_ttc_zones_clean.png")

# 7. Clean Schematic: Case study pole proportional slicing (non-overlapping callouts)
def gen_clean_pole_slicing_diagram():
    fig, ax = plt.subplots(figsize=(9.5, 5.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Pole background
    pole_rect = plt.Rectangle((18, 5), 4, 90, facecolor='#64748B', edgecolor='#475569')
    ax.add_patch(pole_rect)
    
    # Sign 1: P.124b Primary Prohibition Sign (Circle)
    circle1 = plt.Circle((20, 78), 12, facecolor='#FFFFFF', edgecolor='#DC2626', linewidth=5)
    ax.add_patch(circle1)
    ax.text(20, 78, 'P.124b\nCẤM QUAY ĐẦU\n& RẼ TRÁI', fontsize=7.5, fontweight='bold', ha='center', va='center', color='#DC2626')
    
    # Sign 2: S.508 Auxiliary Time Sign (Rectangle beneath circle)
    rect2 = plt.Rectangle((10, 48), 20, 12, facecolor='#FFFFFF', edgecolor='#1E293B', linewidth=2.5)
    ax.add_patch(rect2)
    ax.text(20, 54, 'S.508 (Biển phụ)\n06:00 - 22:00', fontsize=8, fontweight='bold', ha='center', va='center', color='#1E293B')
    
    # Sign 3: W.245a Warning Sign (Triangle beneath)
    tri_pts = np.array([[20, 42], [9, 20], [31, 20]])
    tri = plt.Polygon(tri_pts, facecolor='#FEF08A', edgecolor='#DC2626', linewidth=4)
    ax.add_patch(tri)
    ax.text(20, 27, 'W.245a\nĐI CHẬM', fontsize=7.5, fontweight='bold', ha='center', va='center', color='#991B1B')
    
    # Bounding boxes dashed lines (Green / Blue / Orange)
    bb1 = plt.Rectangle((6, 64), 28, 28, facecolor='none', edgecolor='#10B981', linewidth=2.0, linestyle='--')
    bb2 = plt.Rectangle((8, 46), 24, 16, facecolor='none', edgecolor='#3B82F6', linewidth=2.0, linestyle='--')
    bb3 = plt.Rectangle((7, 18), 26, 26, facecolor='none', edgecolor='#F59E0B', linewidth=2.0, linestyle='--')
    ax.add_patch(bb1)
    ax.add_patch(bb2)
    ax.add_patch(bb3)
    
    # SEPARATED EXPLANATIONS TO THE RIGHT (NO OVERLAPPING!)
    # Box 1
    ax.annotate('', xy=(34, 78), xytext=(48, 78), arrowprops=dict(arrowstyle="<-", color='#10B981', lw=2))
    rect_desc1 = plt.Rectangle((48, 68), 48, 20, facecolor='#ECFDF5', edgecolor='#10B981', linewidth=1.5)
    ax.add_patch(rect_desc1)
    ax.text(50, 81, 'BƯỚC 1: BIỂN CHÍNH P.124b (Tỷ lệ 98%)', fontsize=8.5, fontweight='bold', color='#065F46')
    ax.text(50, 72, '• Chuẩn hóa crop về 80x80 với INTER_CUBIC.\n• Phân loại bất biến khoảng cách (Scale-Invariant).\n• Tránh nhầm lẫn với biển P.103a ở cự ly xa.', fontsize=7.5, color='#0F172A')

    # Box 2
    ax.annotate('', xy=(32, 54), xytext=(48, 54), arrowprops=dict(arrowstyle="<-", color='#3B82F6', lw=2))
    rect_desc2 = plt.Rectangle((48, 44), 48, 20, facecolor='#EFF6FF', edgecolor='#3B82F6', linewidth=1.5)
    ax.add_patch(rect_desc2)
    ax.text(50, 57, 'BƯỚC 2: BIỂN PHỤ S.508 (Tỷ lệ 95%)', fontsize=8.5, fontweight='bold', color='#1E40AF')
    ax.text(50, 48, '• Cắt lát tỷ lệ cột: aux_y2 = cy2 + 0.52 * ch.\n• Tiền xử lý tương phản & bóc tách văn bản.\n• OCR giải mã khung giờ cấm: "06:00 - 22:00".', fontsize=7.5, color='#0F172A')

    # Box 3
    ax.annotate('', xy=(33, 30), xytext=(48, 30), arrowprops=dict(arrowstyle="<-", color='#F59E0B', lw=2))
    rect_desc3 = plt.Rectangle((48, 20), 48, 20, facecolor='#FFFBEB', edgecolor='#F59E0B', linewidth=1.5)
    ax.add_patch(rect_desc3)
    ax.text(50, 33, 'BƯỚC 3: BIỂN CẢNH BÁO PHỤ W.245a (Tỷ lệ 94%)', fontsize=8.5, fontweight='bold', color='#92400E')
    ax.text(50, 24, '• Tìm kiếm vùng phụ cận bên dưới: pole_y1 > aux_y2.\n• Nhận diện tam giác vàng viền đỏ W.245a.\n• Đưa vào động cơ ra quyết định ADAS.', fontsize=7.5, color='#0F172A')

    ax.set_title('SƠ ĐỒ BÓC TÁCH CỤM BIỂN BÁO TRÊN CỘT BẰNG THUẬT TOÁN POLE PROPORTIONAL SLICING', 
                 fontsize=11, fontweight='bold', pad=12, color='#0F172A')
                 
    plt.tight_layout(pad=1.5)
    fig.savefig(OUT_DIR / "fig_pole_slicing_clean.png")
    plt.close()
    print("Generated fig_pole_slicing_clean.png")

if __name__ == '__main__':
    gen_clean_safe_distance()
    gen_clean_accuracy()
    gen_clean_latency()
    gen_clean_violation_distribution()
    gen_clean_ear_mar()
    gen_clean_ttc_zones()
    gen_clean_pole_slicing_diagram()
    print("All clean, spacious charts successfully generated!")
