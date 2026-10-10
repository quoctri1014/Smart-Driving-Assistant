import os
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt

SIGNS_DIR = Path("web-app/public/signs")
OUT_FILE = Path("report_assets/fig_qcvn_signs_sample.png")

# Pick notable signs
sample_signs = [
    ("P_101.png", "P.101: Đường cấm"),
    ("P_102.png", "P.102: Cấm đi ngược chiều"),
    ("P_103a.png", "P.103a: Cấm ô tô"),
    ("P_104.png", "P.104: Cấm mô tô"),
    ("P_105.png", "P.105: Cấm ô tô & mô tô"),
    ("DP_135.png", "DP.135: Hết mọi lệnh cấm"),
    ("I_401.png", "I.401: Đường ưu tiên"),
    ("I_402.png", "I.402: Hết đường ưu tiên"),
]

existing_signs = []
for fname, label in sample_signs:
    p = SIGNS_DIR / fname
    if p.exists():
        existing_signs.append((p, label))

if len(existing_signs) >= 4:
    fig, axes = plt.subplots(2, 4, figsize=(10, 5), dpi=300)
    axes = axes.flatten()
    for idx, ax in enumerate(axes):
        if idx < len(existing_signs):
            img_path, label = existing_signs[idx]
            img = Image.open(img_path)
            ax.imshow(img)
            ax.set_title(label, fontsize=9, fontweight='bold', pad=4)
        ax.axis('off')
    
    plt.suptitle("Một số Mẫu Biển báo Giao thông QCVN 41:2019/BGTVT trong Cơ sở Dữ liệu Huấn luyện", fontsize=11, fontweight='bold', y=0.98)
    plt.tight_layout()
    fig.savefig(OUT_FILE)
    plt.close()
    print("Saved fig_qcvn_signs_sample.png")
else:
    print("Not enough signs found, skipping.")
