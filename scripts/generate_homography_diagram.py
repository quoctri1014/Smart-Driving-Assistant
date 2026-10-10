import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Setup clean styling
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.edgecolor'] = '#94A3B8'
plt.rcParams['axes.linewidth'] = 1.0

OUT_DIR = Path("report_assets")
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / "fig_homography_transformation_clean.png"

def generate_homography_figure():
    fig, ax = plt.subplots(figsize=(12, 6.0), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # 0. Main Title (Clean, bold, comfortable margin)
    ax.text(50, 95, "Toán học Biến đổi Phối cảnh (Homography) để Đo Khoảng cách & Vận tốc", 
            fontsize=13.5, fontweight='bold', ha='center', color='#0F172A')

    # =========================================================================
    # 1. LEFT PANE: 2D CAMERA PERSPECTIVE VIEW (HÌNH THANG)
    # =========================================================================
    ax.text(25, 87, "1. Góc nhìn phối cảnh Camera (2D View)", 
            fontsize=11.5, fontweight='bold', ha='center', color='#1E40AF')
    
    # Trapezoid coordinates (u, v)
    # Top points: (16, 68) to (34, 68) [Width = 18]
    # Bottom points: (7, 24) to (43, 24) [Width = 36]
    trap_pts = np.array([[16, 68], [34, 68], [43, 24], [7, 24]])
    trapezoid = plt.Polygon(trap_pts, closed=True, 
                            facecolor='#EFF6FF', edgecolor='#1D4ED8', linewidth=2.5, zorder=2)
    ax.add_patch(trapezoid)
    
    # 4 Red vertex points
    for pt in trap_pts:
        ax.plot(pt[0], pt[1], 'o', color='#DC2626', markersize=8, markeredgecolor='#FFFFFF', markeredgewidth=1.5, zorder=3)
        
    # Top label: "Cạnh đỉnh xa xe: Hẹp lại (Điểm tụ)"
    ax.text(25, 73, "Cạnh đỉnh xa xe: Hẹp lại (Điểm tụ)", 
            fontsize=9.5, fontweight='bold', ha='center', color='#0F172A')
    
    # Bottom label: "Cạnh đáy gần xe: Rộng hơn (Pixel rộng)"
    ax.text(25, 18, "Cạnh đáy gần xe: Rộng hơn (Pixel rộng)", 
            fontsize=9.5, fontweight='bold', ha='center', color='#0F172A')
            
    # Center text inside trapezoid (Well within the boundaries)
    ax.text(25, 46, "Không gian ảnh Camera 2D\n(Góc nhìn phối cảnh nghiêng)\nTọa độ điểm ảnh: (u, v)", 
            fontsize=8.5, fontweight='bold', ha='center', va='center', color='#1E40AF', linespacing=1.3)

    # =========================================================================
    # CENTER BRIDGE: HOMOGRAPHY TRANSFORMATION ARROW & MATRIX
    # =========================================================================
    # Arrow from x=45 to x=58
    ax.annotate('', xy=(59, 46), xytext=(45, 46),
                arrowprops=dict(arrowstyle="-|>", color='#D97706', lw=3.2, mutation_scale=22), zorder=4)
                
    # Matrix info box
    ax.text(52, 57, "Ma trận Homography H (3x3)", 
            fontsize=9.5, fontweight='bold', ha='center', color='#B45309')
    ax.text(52, 35, "[X, Y, 1]ᵀ = H · [u, v, 1]ᵀ\n(Biến đổi phối cảnh)", 
            fontsize=8.5, fontweight='bold', ha='center', color='#78350F',
            bbox=dict(boxstyle="round,pad=0.5", fc="#FFFBEB", ec="#FDE68A", lw=1.2))

    # =========================================================================
    # 2. RIGHT PANE: BIRD'S EYE VIEW (BEV - HÌNH CHỮ NHẬT RỘNG RÃI)
    # =========================================================================
    ax.text(78, 87, "2. Mặt phẳng đường từ trên cao (Bird's Eye View)", 
            fontsize=11.5, fontweight='bold', ha='center', color='#065F46')
            
    # Rectangle coordinates in real-world metric space
    # (62, 24) to (94, 68) -> Width=32, Height=44 -> Plenty of room for text!
    rect_pts = np.array([[63, 68], [93, 68], [93, 24], [63, 24]])
    rectangle = plt.Polygon(rect_pts, closed=True, 
                            facecolor='#ECFDF5', edgecolor='#059669', linewidth=2.5, zorder=2)
    ax.add_patch(rectangle)
    
    # 4 Green vertex points
    for pt in rect_pts:
        ax.plot(pt[0], pt[1], 'o', color='#059669', markersize=8, markeredgecolor='#FFFFFF', markeredgewidth=1.5, zorder=3)
        
    # Top label: "Chiều dài thực tế: L = 20.0 mét"
    ax.text(78, 73, "Chiều dài thực tế: L = 20.0 mét", 
            fontsize=9.5, fontweight='bold', ha='center', color='#0F172A')
            
    # Bottom label: "Chiều rộng thực tế: W = 3.5 mét"
    ax.text(78, 18, "Chiều rộng thực tế: W = 3.5 mét", 
            fontsize=9.5, fontweight='bold', ha='center', color='#0F172A')
            
    # Center text inside rectangle (PLENTY of margin on left and right, zero overlap!)
    ax.text(78, 46, "Không gian thế giới thực (BEV)\n(Mặt phẳng thực tế trên đường)\nTọa độ thực tế: (X, Y) tính bằng mét", 
            fontsize=8.5, fontweight='bold', ha='center', va='center', color='#065F46', linespacing=1.3)

    # Save cleanly with tight bounding box
    plt.tight_layout()
    fig.savefig(OUT_PATH, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Re-generated clean homography figure at: {OUT_PATH}")

if __name__ == '__main__':
    generate_homography_figure()
