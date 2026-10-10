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

def generate_both_versions():
    time_minutes = np.array([0, 15, 30, 45, 60, 75, 90, 105, 120])
    latency_ms = np.array([105, 110, 115, 114, 116, 115, 118, 115, 115])
    ram_gb = np.array([1.80, 2.00, 2.10, 2.10, 2.10, 2.10, 2.10, 2.10, 2.10])

    # 1. Version 1: Pure Chart
    fig, ax1 = plt.subplots(figsize=(10, 5.5), dpi=300)
    color_lat = '#1D4ED8'
    ax1.set_xlabel('Thời gian chạy tải liên tục (Phút)', fontsize=11, fontweight='bold', labelpad=10, color='#0F172A')
    ax1.set_ylabel('Độ trễ phản hồi WebSocket (ms)', fontsize=11, fontweight='bold', labelpad=10, color=color_lat)
    line1, = ax1.plot(time_minutes, latency_ms, color=color_lat, marker='o', markersize=6.5, linewidth=2.2, label='Độ trễ phản hồi (ms)')
    ax1.set_xlim(-3, 125)
    ax1.set_ylim(80, 160)
    ax1.set_xticks(np.arange(0, 130, 20))
    ax1.set_yticks(np.arange(80, 170, 10))
    ax1.tick_params(axis='y', labelcolor=color_lat, labelsize=9.5)
    ax1.tick_params(axis='x', labelsize=9.5)
    ax1.grid(True, linestyle=':', alpha=0.6, color='#CBD5E1')

    ax2 = ax1.twinx()
    color_ram = '#DC2626'
    ax2.set_ylabel('Mức tiêu thụ RAM Backend (GB)', fontsize=11, fontweight='bold', labelpad=10, color=color_ram)
    line2, = ax2.plot(time_minutes, ram_gb, color=color_ram, marker='s', markersize=6.0, linewidth=2.2, linestyle='--', label='Tiêu thụ RAM (GB)')
    ax2.set_ylim(1.00, 3.00)
    ax2.set_yticks(np.arange(1.00, 3.25, 0.25))
    ax2.tick_params(axis='y', labelcolor=color_ram, labelsize=9.5)

    plt.title('Kết quả Kiểm thử Tải (Locust Stress Test) 50 Clients Stream Đồng thời', 
              fontsize=12.5, fontweight='bold', pad=16, color='#0F172A')
    ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc='upper right', frameon=True, 
               facecolor='#FFFFFF', edgecolor='#CBD5E1', fontsize=9.5, borderpad=0.8, bbox_to_anchor=(0.98, 0.95))

    plt.tight_layout(pad=2.0)
    path_pure = OUT_DIR / "fig_locust_stress_test_clean.png"
    fig.savefig(path_pure, bbox_inches='tight', facecolor='white')
    plt.close()

    # 2. Version 2: With academic caption underneath
    fig, ax1 = plt.subplots(figsize=(10, 6.0), dpi=300)
    ax1.set_xlabel('Thời gian chạy tải liên tục (Phút)', fontsize=11, fontweight='bold', labelpad=10, color='#0F172A')
    ax1.set_ylabel('Độ trễ phản hồi WebSocket (ms)', fontsize=11, fontweight='bold', labelpad=10, color=color_lat)
    line1, = ax1.plot(time_minutes, latency_ms, color=color_lat, marker='o', markersize=6.5, linewidth=2.2, label='Độ trễ phản hồi (ms)')
    ax1.set_xlim(-3, 125)
    ax1.set_ylim(80, 160)
    ax1.set_xticks(np.arange(0, 130, 20))
    ax1.set_yticks(np.arange(80, 170, 10))
    ax1.tick_params(axis='y', labelcolor=color_lat, labelsize=9.5)
    ax1.tick_params(axis='x', labelsize=9.5)
    ax1.grid(True, linestyle=':', alpha=0.6, color='#CBD5E1')

    ax2 = ax1.twinx()
    ax2.set_ylabel('Mức tiêu thụ RAM Backend (GB)', fontsize=11, fontweight='bold', labelpad=10, color=color_ram)
    line2, = ax2.plot(time_minutes, ram_gb, color=color_ram, marker='s', markersize=6.0, linewidth=2.2, linestyle='--', label='Tiêu thụ RAM (GB)')
    ax2.set_ylim(1.00, 3.00)
    ax2.set_yticks(np.arange(1.00, 3.25, 0.25))
    ax2.tick_params(axis='y', labelcolor=color_ram, labelsize=9.5)

    plt.title('Kết quả Kiểm thử Tải (Locust Stress Test) 50 Clients Stream Đồng thời', 
              fontsize=12.5, fontweight='bold', pad=16, color='#0F172A')
    ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc='upper right', frameon=True, 
               facecolor='#FFFFFF', edgecolor='#CBD5E1', fontsize=9.5, borderpad=0.8, bbox_to_anchor=(0.98, 0.95))

    # Add Figure Caption cleanly underneath
    fig.text(0.5, 0.01, 'Hình 7.3: Biểu đồ kết quả kiểm thử tải hệ thống 50 Clients truyền stream đồng thời qua Locust',
             ha='center', fontsize=11, style='italic', fontweight='bold', color='#1E293B')

    plt.tight_layout(rect=[0, 0.05, 1, 1], pad=2.0)
    path_cap = OUT_DIR / "fig_locust_stress_test_captioned.png"
    fig.savefig(path_cap, bbox_inches='tight', facecolor='white')
    plt.close()

    print("Generated both pure and captioned versions successfully!")

if __name__ == '__main__':
    generate_both_versions()
