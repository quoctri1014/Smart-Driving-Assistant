import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9.5
plt.rcParams['axes.edgecolor'] = '#94A3B8'

OUT_DIR = Path("report_assets")
OUT_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------------------------
# 1. HÌNH 3.2: DUAL STREAM PIPELINE (ROAD + CABIN -> FASTAPI CORE -> OUTPUT)
# -------------------------------------------------------------------------
def gen_dual_stream_pipeline():
    fig, ax = plt.subplots(figsize=(12, 6.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Main Title
    ax.text(50, 95, "Sơ đồ Luồng Xử lý Song song 2 Kênh Camera (Dual Stream Pipeline)",
            fontsize=13, fontweight='bold', ha='center', color='#0F172A')

    # Sub-headers
    ax.text(18, 87, "LUỒNG ROAD-FACING (MẶT ĐƯỜNG)", fontsize=10.5, fontweight='bold', ha='center', color='#1D4ED8')
    ax.text(82, 87, "LUỒNG DRIVER-FACING (CABIN DMS)", fontsize=10.5, fontweight='bold', ha='center', color='#6D28D9')

    # Box 1: Road (Left)
    r_road = plt.Rectangle((4, 25), 28, 58, facecolor='#F8FAFC', edgecolor='#2563EB', linewidth=2.0, zorder=2)
    ax.add_patch(r_road)
    road_text = (
        "1. Thu nhận Frame 1080p\n"
        "2. ROI Crop (Bỏ 30% trời)\n"
        "3. YOLOv8 Phát hiện xe\n"
        "4. MOT Bám vết (IoU/Kalman)\n"
        "5. Homography tính Vận tốc\n"
        "6. Biển báo QCVN 41 & S.508\n"
        "7. Cự ly an toàn (TT31) & TTC"
    )
    ax.text(6, 78, road_text, fontsize=8.8, color='#0F172A', linespacing=1.65, va='top')

    # Box 2: Center (FastAPI Backend Core)
    r_core = plt.Rectangle((36, 28), 28, 52, facecolor='#F0FDF4', edgecolor='#15803D', linewidth=2.2, zorder=2)
    ax.add_patch(r_core)
    ax.text(50, 75, "FASTAPI BACKEND CORE", fontsize=10, fontweight='bold', ha='center', color='#166534')
    core_text = (
        "• WebSocket Server (ws/stream)\n"
        "• In-Memory Frame Processing\n"
        "  - Priority Decision Engine\n"
        "    + Mức 1: CRITICAL (TTC/Sleep)\n"
        "    + Mức 2: WARNING (Speed/Dist)\n"
        "    + Mức 3: INFO (Seatbelt/Rest)\n"
        "  - Debounce Filter (Chống dội)\n"
        "  - Privacy Blur & Hash SHA-256"
    )
    ax.text(38, 70, core_text, fontsize=8.0, color='#0F172A', linespacing=1.45, va='top')

    # Box 3: Cabin (Right)
    r_cabin = plt.Rectangle((68, 25), 28, 58, facecolor='#FAF5FF', edgecolor='#7C3AED', linewidth=2.0, zorder=2)
    ax.add_patch(r_cabin)
    cabin_text = (
        "1. Thu nhận Frame Cabin\n"
        "2. MediaPipe 468 Face Mesh\n"
        "3. Dynamic Calibration EAR\n"
        "4. Tính EAR (Mắt) & MAR (Miệng)\n"
        "5. Cửa sổ PERCLOS 60s\n"
        "6. 3D Head Pose (solvePnP)\n"
        "7. Dây an toàn & Đếm giờ 4h"
    )
    ax.text(70, 78, cabin_text, fontsize=8.8, color='#0F172A', linespacing=1.65, va='top')

    # Arrows Left -> Center and Right -> Center
    ax.annotate('', xy=(36, 54), xytext=(32, 54),
                arrowprops=dict(arrowstyle="-|>", color='#1D4ED8', lw=2.2, mutation_scale=18))
    ax.annotate('', xy=(64, 54), xytext=(68, 54),
                arrowprops=dict(arrowstyle="-|>", color='#7C3AED', lw=2.2, mutation_scale=18))

    # Bottom Box (Output)
    r_out = plt.Rectangle((12, 12), 76, 7.5, facecolor='#FFFBEB', edgecolor='#D97706', linewidth=1.8, zorder=2)
    ax.add_patch(r_out)
    ax.text(50, 15.8, "Đồng bộ đầu ra: Web Dashboard (Canvas 60fps) + Mobile App HUD + Còi Web Audio & Giọng nói tiếng Việt",
            fontsize=9.0, fontweight='bold', ha='center', va='center', color='#B45309')

    # Arrow Center -> Bottom
    ax.annotate('', xy=(50, 19.5), xytext=(50, 28),
                arrowprops=dict(arrowstyle="-|>", color='#D97706', lw=2.0, mutation_scale=16))

    # Caption underneath
    ax.text(50, 4, "Hình 3.2: Sơ đồ luồng xử lý song song 2 kênh camera (Dual Stream Pipeline)",
            fontsize=10.5, style='italic', fontweight='bold', ha='center', color='#1E293B')

    plt.tight_layout()
    out_p = OUT_DIR / "fig_dual_stream_pipeline_clean.png"
    fig.savefig(out_p, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Generated: {out_p}")

# -------------------------------------------------------------------------
# 2. HÌNH 3.3: DATABASE ERD SCHEMA (15 BẢNG)
# -------------------------------------------------------------------------
def gen_database_erd_schema():
    fig, ax = plt.subplots(figsize=(12.5, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(50, 96, "Sơ đồ Quan hệ Thực thể Cơ sở Dữ liệu (Database ERD Schema - 15 Bảng)",
            fontsize=13, fontweight='bold', ha='center', color='#0F172A')

    def draw_entity(x, y, w, h, title, fields, bg_header, edge_color):
        # Outer box
        rect = plt.Rectangle((x, y), w, h, facecolor='#FFFFFF', edgecolor=edge_color, linewidth=1.8, zorder=2)
        ax.add_patch(rect)
        # Header box
        h_rect = plt.Rectangle((x, y + h - 5.5), w, 5.5, facecolor=bg_header, edgecolor=edge_color, linewidth=1.8, zorder=3)
        ax.add_patch(h_rect)
        ax.text(x + w / 2, y + h - 2.8, title, fontsize=9.2, fontweight='bold', ha='center', va='center', color='#FFFFFF', zorder=4)
        # Fields text
        f_str = "\n".join(fields)
        ax.text(x + 1.8, y + h - 7.5, f_str, fontsize=7.6, color='#1E293B', va='top', linespacing=1.35, zorder=4)

    # Column 1
    draw_entity(6, 68, 24, 22, "organizations", 
                ["id (PK)", "name", "code", "plan_tier", "created_at"], "#1D4ED8", "#1D4ED8")
    draw_entity(6, 38, 24, 22, "users", 
                ["id (PK)", "org_id (FK)", "email", "hashed_pwd", "role"], "#1D4ED8", "#1D4ED8")
    draw_entity(6, 8, 24, 22, "drivers", 
                ["id (PK)", "user_id (FK)", "license_no", "safety_score"], "#15803D", "#15803D")

    # Column 2
    draw_entity(38, 68, 24, 22, "vehicles", 
                ["id (PK)", "org_id (FK)", "plate_number", "model", "camera_id"], "#EA580C", "#EA580C")
    draw_entity(38, 38, 24, 22, "driving_sessions", 
                ["id (PK)", "vehicle_id (FK)", "driver_id (FK)", "start_time", "km"], "#EA580C", "#EA580C")
    draw_entity(38, 8, 24, 22, "trip_events", 
                ["id (PK)", "session_id (FK)", "event_type", "speed", "timestamp"], "#7C3AED", "#7C3AED")

    # Column 3
    draw_entity(70, 68, 24, 22, "violations", 
                ["id (PK)", "session_id (FK)", "type", "evidence_url", "sha256_hash"], "#DC2626", "#DC2626")
    draw_entity(70, 38, 24, 22, "violation_reviews", 
                ["id (PK)", "violation_id (FK)", "reviewer_id (FK)", "status"], "#DC2626", "#DC2626")
    draw_entity(70, 8, 24, 22, "device_health", 
                ["id (PK)", "vehicle_id (FK)", "fps", "gpu_temp", "ping_ms"], "#78350F", "#78350F")

    # Arrows connecting tables
    # 1. organizations -> users
    ax.annotate('', xy=(18, 60), xytext=(18, 68), arrowprops=dict(arrowstyle="-|>", color='#475569', lw=1.5, mutation_scale=14))
    # 2. users -> drivers
    ax.annotate('', xy=(18, 30), xytext=(18, 38), arrowprops=dict(arrowstyle="-|>", color='#475569', lw=1.5, mutation_scale=14))
    # 3. users -> driving_sessions
    ax.annotate('', xy=(38, 49), xytext=(30, 49), arrowprops=dict(arrowstyle="-|>", color='#475569', lw=1.5, mutation_scale=14))
    # 4. vehicles -> driving_sessions
    ax.annotate('', xy=(50, 60), xytext=(50, 68), arrowprops=dict(arrowstyle="-|>", color='#475569', lw=1.5, mutation_scale=14))
    # 5. driving_sessions -> trip_events
    ax.annotate('', xy=(50, 30), xytext=(50, 38), arrowprops=dict(arrowstyle="-|>", color='#475569', lw=1.5, mutation_scale=14))
    # 6. driving_sessions -> violations (diagonal up right)
    ax.annotate('', xy=(72, 70), xytext=(62, 58), arrowprops=dict(arrowstyle="-|>", color='#475569', lw=1.5, mutation_scale=14))
    # 7. violations -> violation_reviews
    ax.annotate('', xy=(82, 60), xytext=(82, 68), arrowprops=dict(arrowstyle="-|>", color='#475569', lw=1.5, mutation_scale=14))
    # 8. vehicles -> device_health (long diagonal down right)
    ax.annotate('', xy=(71, 23), xytext=(59, 70), arrowprops=dict(arrowstyle="-|>", color='#475569', lw=1.5, mutation_scale=14))

    # Caption
    ax.text(50, 2.5, "Hình 3.3: Sơ đồ quan hệ thực thể cơ sở dữ liệu (Database ERD Schema - 15 Bảng)",
            fontsize=10.5, style='italic', fontweight='bold', ha='center', color='#1E293B')

    plt.tight_layout()
    out_p = OUT_DIR / "fig_database_erd_schema_clean.png"
    fig.savefig(out_p, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Generated: {out_p}")

# -------------------------------------------------------------------------
# 3. HÌNH 4.1: QUY TRÌNH NHẬN DIỆN BIỂN SỐ XE (5 BƯỚC)
# -------------------------------------------------------------------------
def gen_plate_recognition_pipeline():
    fig, ax = plt.subplots(figsize=(12, 4.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Main Title
    ax.text(50, 90, "Quy trình Nhận diện Biển số xe Việt Nam (YOLOv11 + CLAHE + EasyOCR + Regex)",
            fontsize=12, fontweight='bold', ha='center', color='#0F172A')

    steps = [
        ("1. Input Frame\n(1080p Image)", "#EFF6FF", "#2563EB", "#1D4ED8"),
        ("2. YOLOv11 Plate\n(ROI Detection)", "#F0FDF4", "#16A34A", "#15803D"),
        ("3. Perspective\nDeskew & CLAHE", "#FFF7ED", "#EA580C", "#C2410C"),
        ("4. EasyOCR Engine\n(Character Recog)", "#FAF5FF", "#9333EA", "#7E22CE"),
        ("5. Regex Matcher\n51H-982.45", "#FFFBEB", "#D97706", "#B45309"),
    ]

    box_w = 16.5
    box_h = 42
    start_x = 4.5
    gap = 2.8
    y = 30

    for i, (text, bg, edge, txt_col) in enumerate(steps):
        x = start_x + i * (box_w + gap)
        rect = plt.Rectangle((x, y), box_w, box_h, facecolor=bg, edgecolor=edge, linewidth=2.0, zorder=2)
        ax.add_patch(rect)
        ax.text(x + box_w / 2, y + box_h / 2, text, fontsize=8.8, fontweight='bold',
                ha='center', va='center', color=txt_col, linespacing=1.35, zorder=3)
        
        # Arrow to next step
        if i < len(steps) - 1:
            arr_x = x + box_w
            ax.annotate('', xy=(arr_x + gap, y + box_h / 2), xytext=(arr_x, y + box_h / 2),
                        arrowprops=dict(arrowstyle="-|>", color='#475569', lw=2.0, mutation_scale=16))

    # Caption underneath
    ax.text(50, 10, "Hình 4.1: Quy trình 4 bước nhận dạng biển số xe Việt Nam (YOLOv11 + CLAHE + EasyOCR + Regex)",
            fontsize=10.5, style='italic', fontweight='bold', ha='center', color='#1E293B')

    plt.tight_layout()
    out_p = OUT_DIR / "fig_plate_recognition_pipeline_clean.png"
    fig.savefig(out_p, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Generated: {out_p}")

if __name__ == '__main__':
    gen_dual_stream_pipeline()
    gen_database_erd_schema()
    gen_plate_recognition_pipeline()
