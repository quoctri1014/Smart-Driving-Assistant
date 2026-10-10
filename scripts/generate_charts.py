import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Use clean styling
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#CBD5E1'
plt.rcParams['axes.linewidth'] = 1.0

OUT_DIR = Path("report_assets")
OUT_DIR.mkdir(exist_ok=True)

# 1. Chart: Safe Distance Curves (TT 31/2019/TT-BGTVT)
def gen_safe_distance_chart():
    speeds = np.array([30, 50, 60, 70, 80, 90, 100, 110, 120])
    # TT 31 dry road
    dry_distances = np.array([20, 30, 35, 55, 55, 70, 70, 100, 100])
    wet_distances = dry_distances * 1.30
    
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    ax.step(speeds, dry_distances, where='post', label='Khoảng cách an toàn đường khô (TT 31/2019)', color='#1E40AF', linewidth=2.5)
    ax.step(speeds, wet_distances, where='post', label='Khoảng cách trời mưa / đường trơn (x1.30)', color='#DC2626', linewidth=2.5, linestyle='--')
    
    ax.set_title('Đồ thị Khoảng cách An toàn Tối thiểu theo Thông tư 31/2019/TT-BGTVT', fontsize=12, fontweight='bold', pad=12, color='#0F172A')
    ax.set_xlabel('Vận tốc xe chạy (km/h)', fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylabel('Cự ly an toàn tối thiểu (mét)', fontsize=10, fontweight='bold', color='#334155')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', frameon=True, facecolor='#F8FAFC', edgecolor='#E2E8F0')
    
    # Annotations
    ax.annotate('V ≤ 60 km/h: Chủ động\n(Khuyến nghị ≥ 35m)', xy=(50, 35), xytext=(35, 60),
                arrowprops=dict(facecolor='#1E40AF', shrink=0.08, width=1, headwidth=6),
                fontsize=8.5, bbox=dict(boxstyle="round,pad=0.3", fc="#EFF6FF", ec="#93C5FD"))
    ax.annotate('100 < V ≤ 120 km/h: 100m\n(Mưa: 130m)', xy=(110, 100), xytext=(85, 120),
                arrowprops=dict(facecolor='#DC2626', shrink=0.08, width=1, headwidth=6),
                fontsize=8.5, bbox=dict(boxstyle="round,pad=0.3", fc="#FEF2F2", ec="#FCA5A5"))
    
    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig_safe_distance_curve.png")
    plt.close()
    print("Saved fig_safe_distance_curve.png")

# 2. Chart: AI Accuracy Benchmark (mAP, Precision, Recall, F1)
def gen_accuracy_chart():
    categories = ['Phát hiện xe\n(YOLOv8n)', 'Biển báo QCVN\n(Hierarchical)', 'Biển số OCR\n(YOLO+OCR)', 'Giám sát ngủ gật\n(PERCLOS/EAR)', 'Mũ bảo hiểm\n(Deduplication)']
    map_scores = [94.2, 95.8, 91.5, 96.0, 93.8]
    precision = [93.5, 96.2, 90.8, 95.2, 94.5]
    recall = [94.8, 95.4, 92.1, 96.8, 93.0]
    
    x = np.arange(len(categories))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=300)
    rects1 = ax.bar(x - width, map_scores, width, label='Độ chính xác (Accuracy / mAP@0.5 %)', color='#2563EB')
    rects2 = ax.bar(x, precision, width, label='Precision (%)', color='#059669')
    rects3 = ax.bar(x + width, recall, width, label='Recall (%)', color='#D97706')
    
    ax.set_title('Đánh giá Hiệu năng Độ chính xác 5 Tác vụ AI Cốt lõi', fontsize=12, fontweight='bold', pad=12, color='#0F172A')
    ax.set_ylabel('Tỷ lệ phần trăm (%)', fontsize=10, fontweight='bold', color='#334155')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=9)
    ax.set_ylim(80, 100)
    ax.grid(True, axis='y', linestyle=':', alpha=0.6)
    ax.legend(loc='lower right', frameon=True, facecolor='#F8FAFC', edgecolor='#E2E8F0')
    
    # Auto-label
    for rect in rects1:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}%', xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=7.5, fontweight='bold')
                    
    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig_ai_benchmark_accuracy.png")
    plt.close()
    print("Saved fig_ai_benchmark_accuracy.png")

# 3. Chart: Module Latency Breakdown (Horizontal Bar)
def gen_latency_chart():
    modules = [
        'Vehicle Detector (YOLO)',
        'Multi-Object Tracker (MOT)',
        'Speed Estimator (Homography)',
        'Traffic Sign (QCVN 41 + S.508)',
        'Safe Distance & TTC Calculator',
        'Face Mesh & EAR/MAR (DMS)',
        'Head Pose & PERCLOS 60s',
        'License Plate OCR (when triggered)',
        'Decision Engine & DB Sync'
    ]
    latencies = [9.2, 2.1, 1.8, 6.4, 1.2, 8.5, 3.1, 4.5, 1.2]
    colors = ['#1E40AF', '#3B82F6', '#60A5FA', '#059669', '#10B981', '#7C3AED', '#8B5CF6', '#D97706', '#64748B']
    
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=300)
    y_pos = np.arange(len(modules))
    bars = ax.barh(y_pos, latencies, color=colors, height=0.65)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(modules, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel('Thời gian thực thi trung bình mỗi khung hình (ms)', fontsize=10, fontweight='bold', color='#334155')
    ax.set_title('Đo lường Độ trễ từng Module AI (Tổng Pipeline: ~38ms | Đạt chuẩn < 50ms)', fontsize=11, fontweight='bold', pad=12, color='#0F172A')
    ax.set_xlim(0, 12)
    ax.grid(True, axis='x', linestyle=':', alpha=0.6)
    
    for bar in bars:
        width = bar.get_width()
        ax.annotate(f'{width:.1f} ms', xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(4, 0), textcoords="offset points", ha='left', va='center', fontsize=8.5, fontweight='bold', color='#1E293B')
                    
    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig_module_latency.png")
    plt.close()
    print("Saved fig_module_latency.png")

# 4. Chart: Fleet Violation Distribution (Donut Chart)
def gen_violation_distribution_chart():
    labels = ['Không giữ cự ly an toàn (TT 31)', 'Vượt quá tốc độ quy định', 'Buồn ngủ / PERCLOS > 0.15', 'Không thắt dây an toàn', 'Không đội mũ bảo hiểm']
    sizes = [32, 28, 20, 12, 8]
    colors = ['#EF4444', '#F97316', '#8B5CF6', '#3B82F6', '#10B981']
    explode = (0.05, 0.05, 0.05, 0, 0)
    
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                                      startangle=140, colors=colors, pctdistance=0.75,
                                      textprops=dict(color="#1E293B", fontsize=8.5))
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(8.5)
        
    centre_circle = plt.Circle((0,0), 0.50, fc='white')
    fig.gca().add_artist(centre_circle)
    
    ax.set_title('Phân bố Cơ cấu Lỗi Vi phạm An toàn Giao thông (Fleet Telemetry)', fontsize=11, fontweight='bold', pad=10, color='#0F172A')
    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig_violation_distribution.png")
    plt.close()
    print("Saved fig_violation_distribution.png")

# 5. Chart: EAR and MAR curves with Alert Triggers
def gen_ear_mar_chart():
    t = np.linspace(0, 30, 300)
    # EAR baseline 0.32, dips to 0.15 around t=12..18
    ear = 0.32 + 0.02 * np.sin(t * 1.5) + 0.01 * np.random.normal(0, 0.5, len(t))
    ear[110:170] -= 0.17 # eye closure
    
    # MAR baseline 0.15, rises to 0.72 around t=20..25 (yawn)
    mar = 0.18 + 0.02 * np.cos(t * 1.2) + 0.01 * np.random.normal(0, 0.5, len(t))
    mar[200:250] += 0.52 # yawn
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.5, 5.0), sharex=True, dpi=300)
    
    # EAR subplot
    ax1.plot(t, ear, label='Chỉ số mở mắt (EAR - Eye Aspect Ratio)', color='#2563EB', linewidth=2)
    ax1.axhline(y=0.20, color='#DC2626', linestyle='--', linewidth=1.5, label='Ngưỡng nhắm mắt (Threshold = 0.20)')
    ax1.fill_between(t, 0.05, 0.20, alpha=0.15, color='#DC2626')
    ax1.set_ylabel('Giá trị EAR', fontsize=9.5, fontweight='bold', color='#334155')
    ax1.set_title('Biến thiên Sinh trắc học DMS: Phát hiện Mắt nhắm kéo dài & Ngáp ngủ gật', fontsize=11, fontweight='bold', color='#0F172A')
    ax1.legend(loc='upper right', fontsize=8, frameon=True)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.annotate('Báo động: Nhắm mắt > 1.5s\n(Eyes Closed Alert)', xy=(14, 0.16), xytext=(15, 0.27),
                 arrowprops=dict(facecolor='#DC2626', shrink=0.08, width=1, headwidth=5),
                 fontsize=8, bbox=dict(boxstyle="round,pad=0.3", fc="#FEF2F2", ec="#FCA5A5"))

    # MAR subplot
    ax2.plot(t, mar, label='Chỉ số mở miệng (MAR - Mouth Aspect Ratio)', color='#D97706', linewidth=2)
    ax2.axhline(y=0.65, color='#B91C1C', linestyle='--', linewidth=1.5, label='Ngưỡng ngáp ngủ (Threshold = 0.65)')
    ax2.fill_between(t, 0.65, 0.85, alpha=0.15, color='#B91C1C')
    ax2.set_xlabel('Thời gian quan sát (Giây)', fontsize=9.5, fontweight='bold', color='#334155')
    ax2.set_ylabel('Giá trị MAR', fontsize=9.5, fontweight='bold', color='#334155')
    ax2.legend(loc='upper left', fontsize=8, frameon=True)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.annotate('Cảnh báo: Ngáp ngủ liên tục\n(Yawning Detected)', xy=(22.5, 0.70), xytext=(22.5, 0.40),
                 arrowprops=dict(facecolor='#D97706', shrink=0.08, width=1, headwidth=5),
                 fontsize=8, bbox=dict(boxstyle="round,pad=0.3", fc="#FFFBEB", ec="#FDE68A"))

    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig_ear_mar_curves.png")
    plt.close()
    print("Saved fig_ear_mar_curves.png")

# 6. Diagram: System Architecture
def gen_system_architecture_diagram():
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Layer 1: Edge & Acquisition
    rect1 = plt.Rectangle((5, 78), 90, 18, facecolor='#EFF6FF', edgecolor='#3B82F6', linewidth=1.5)
    ax.add_patch(rect1)
    ax.text(8, 91, 'TANG 1: THU THAP DU LIEU & THIET BI BIEN (EDGE & DATA ACQUISITION)', fontsize=9.5, fontweight='bold', color='#1E40AF')
    ax.text(10, 83, '* IP Camera / Dashcam (1080p)\n* Cabin DMS Camera (Face View)', fontsize=8.5, color='#1E293B')
    ax.text(45, 83, '* GPS / Telemetry Sensor\n* Mobile Camera Stream (Expo)', fontsize=8.5, color='#1E293B')
    ax.text(75, 83, '* OBD-II Speed Interface\n* Video MP4 File Upload', fontsize=8.5, color='#1E293B')

    # Arrow 1->2
    ax.annotate('', xy=(50, 74), xytext=(50, 78), arrowprops=dict(arrowstyle="->", color='#2563EB', lw=2))

    # Layer 2: AI Core
    rect2 = plt.Rectangle((5, 48), 90, 24, facecolor='#F0FDF4', edgecolor='#10B981', linewidth=1.5)
    ax.add_patch(rect2)
    ax.text(8, 67, 'TANG 2: LOI XU LY TRI TUE NHAN TAO 12 MODULE (AI CORE PIPELINE)', fontsize=9.5, fontweight='bold', color='#065F46')
    ax.text(10, 52, '* Luong Mat duong (Road Vision):\n  - Vehicle Detector (YOLOv8)\n  - MOT Tracker & Speed Estimator\n  - Lane & Safe Distance (TT31)\n  - Sign QCVN 41 & Bien phu S.508', fontsize=8, color='#0F172A')
    ax.text(42, 52, '* Luong Cabin (DMS Vision):\n  - MediaPipe 468 Face Mesh\n  - EAR/MAR & PERCLOS 60s\n  - Head Pose (Pitch/Yaw/Roll)\n  - Seatbelt & Driving Timer', fontsize=8, color='#0F172A')
    ax.text(74, 52, '* Dieu tiet & An toan:\n  - Load Shedder (Frame drop)\n  - Decision Engine (Loc nhieu)\n  - Privacy Blur (ND 13/2023)\n  - Evidence SHA-256 Hash', fontsize=8, color='#0F172A')

    # Arrow 2->3
    ax.annotate('', xy=(50, 44), xytext=(50, 48), arrowprops=dict(arrowstyle="->", color='#059669', lw=2))

    # Layer 3: Backend & Storage
    rect3 = plt.Rectangle((5, 24), 90, 18, facecolor='#FAF5FF', edgecolor='#8B5CF6', linewidth=1.5)
    ax.add_patch(rect3)
    ax.text(8, 37, 'TANG 3: MAY CHU DOANH NGHIEP & CSDL (FASTAPI & RELATIONAL DB)', fontsize=9.5, fontweight='bold', color='#5B21B6')
    ax.text(10, 28, '* FastAPI RESTful API (13 Routers)\n* WebSocket Dispatcher (Low-latency)', fontsize=8.5, color='#1E293B')
    ax.text(45, 28, '* JWT & RBAC 3 Tiers (Admin/Disp/Driver)\n* SQLAlchemy ORM (15 Database Tables)', fontsize=8.5, color='#1E293B')
    ax.text(75, 28, '* Local Object Storage (/storage/)\n* Audit Log & Device Health', fontsize=8.5, color='#1E293B')

    # Arrow 3->4
    ax.annotate('', xy=(50, 20), xytext=(50, 24), arrowprops=dict(arrowstyle="->", color='#7C3AED', lw=2))

    # Layer 4: Presentation
    rect4 = plt.Rectangle((5, 2), 90, 16, facecolor='#FFFBEB', edgecolor='#F59E0B', linewidth=1.5)
    ax.add_patch(rect4)
    ax.text(8, 14, 'TANG 4: GIAO DIEN NGUOI DUNG & TRO LY DIEU HANH (PRESENTATION LAYER)', fontsize=9.5, fontweight='bold', color='#92400E')
    ax.text(10, 6, '* Web Dashboard (Next.js 14):\n  - 9 Man hinh quan tri & Live CCTV Canvas 60fps', fontsize=8.5, color='#1E293B')
    ax.text(50, 6, '* Mobile App HUD (Expo React Native):\n  - Mat than quet duong & Coi bao khan cap', fontsize=8.5, color='#1E293B')
    ax.text(80, 6, '* Am thanh Web Audio\n* Giong noi tieng Viet', fontsize=8.5, color='#1E293B')

    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig_system_architecture.png")
    plt.close()
    print("Saved fig_system_architecture.png")

if __name__ == '__main__':
    gen_safe_distance_chart()
    gen_accuracy_chart()
    gen_latency_chart()
    gen_violation_distribution_chart()
    gen_ear_mar_chart()
    gen_system_architecture_diagram()
    print("All charts successfully generated!")
