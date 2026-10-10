import os
import sys
import json
import hashlib

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

VIDEOS_DIR = "tests/benchmark/videos"
SPLITS_DIR = "tests/benchmark/splits"
os.makedirs(SPLITS_DIR, exist_ok=True)

def compute_sha256(filepath):
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

# 1. Định nghĩa phân chia theo VIDEO độc lập (Zero-Leakage Policy)
# Tập Test đại diện đầy đủ mọi điều kiện: đông xe máy, ngày, biển báo, đêm, mưa, ngược sáng
TEST_VIDEOS = [
    {
        "filename": "dong_xe_may_hcm_01.mp4",
        "condition": "dong_xe_may",
        "location": "hcm_vong_xoay",
        "rationale": "Kiểm thử mật độ xe máy cực cao tại vòng xoay TP.HCM"
    },
    {
        "filename": "dong_xe_may_hanoi_03.mp4",
        "condition": "dong_xe_may",
        "location": "hanoi_nga_tu",
        "rationale": "Kiểm thử xe máy rẽ nhánh cắt ngang dòng tại ngã tư Hà Nội"
    },
    {
        "filename": "ngay_hcm_02.mp4",
        "condition": "ngay",
        "location": "hcm_quoc_lo",
        "rationale": "Kiểm thử làn đường và xe tải chạy tốc độ cao trên quốc lộ"
    },
    {
        "filename": "bien_bao_hcm_01.mp4",
        "condition": "bien_bao",
        "location": "hcm_dashcam_route1",
        "rationale": "Kiểm thử nhận diện biển báo đô thị qua kính lái"
    },
    {
        "filename": "dem_dashcam_01.mp4",
        "condition": "dem",
        "location": "dashcam_urban_night",
        "rationale": "Kiểm thử chóa đèn pha xe ngược chiều ban đêm"
    },
    {
        "filename": "mua_dashcam_02.mp4",
        "condition": "mua",
        "location": "dashcam_windshield_rain",
        "rationale": "Kiểm thử kính lái đọng giọt nước và gạt nước che khuất"
    },
    {
        "filename": "nguoc_sang_dashcam_01.mp4",
        "condition": "nguoc_sang",
        "location": "dashcam_direct_sun_glare",
        "rationale": "Kiểm thử lóa sáng quang học ngược hướng mặt trời"
    }
]

TRAIN_VIDEOS = [
    {
        "filename": "dong_xe_may_hanoi_01.mp4",
        "condition": "dong_xe_may",
        "location": "hanoi_bach_mai_sec1",
        "rationale": "Dữ liệu huấn luyện nhận dạng xe máy nội thành"
    },
    {
        "filename": "dong_xe_may_hanoi_02.mp4",
        "condition": "dong_xe_may",
        "location": "hanoi_bach_mai_sec2",
        "rationale": "Dữ liệu huấn luyện xe máy trời nhiều mây"
    },
    {
        "filename": "ngay_hanoi_01.mp4",
        "condition": "ngay",
        "location": "hanoi_bach_mai_sec3",
        "rationale": "Dữ liệu huấn luyện nhận dạng ô tô/buýt bóng râm"
    },
    {
        "filename": "dong_xe_may_hcm_02.mp4",
        "condition": "dong_xe_may",
        "location": "hcm_nga_tu_cam",
        "rationale": "Dữ liệu huấn luyện xe máy dừng đèn đỏ"
    },
    {
        "filename": "ngay_hcm_01.mp4",
        "condition": "ngay",
        "location": "hcm_dai_lo",
        "rationale": "Dữ liệu huấn luyện đại lộ thông thoáng"
    },
    {
        "filename": "bien_bao_hanoi_01.mp4",
        "condition": "bien_bao",
        "location": "hanoi_dashcam",
        "rationale": "Dữ liệu huấn luyện biển báo giao thông Hà Nội"
    },
    {
        "filename": "bien_bao_hcm_02.mp4",
        "condition": "bien_bao",
        "location": "hcm_dashcam_route2",
        "rationale": "Dữ liệu huấn luyện biển báo tốc độ TP.HCM"
    },
    {
        "filename": "dem_dashcam_02.mp4",
        "condition": "dem",
        "location": "dashcam_highway_night",
        "rationale": "Dữ liệu huấn luyện theo dõi xe thiếu sáng ban đêm"
    },
    {
        "filename": "mua_dashcam_01.mp4",
        "condition": "mua",
        "location": "dashcam_night_rain",
        "rationale": "Dữ liệu huấn luyện phân biệt vạch làn ướt"
    },
    {
        "filename": "mua_dashcam_03.mp4",
        "condition": "mua",
        "location": "dashcam_day_rain",
        "rationale": "Dữ liệu huấn luyện đường trơn ban ngày"
    }
]

def generate_splits():
    test_filenames = {item["filename"] for item in TEST_VIDEOS}
    train_filenames = {item["filename"] for item in TRAIN_VIDEOS}

    # Đảm bảo 100% không trùng lặp video giữa Train và Test
    overlap = test_filenames.intersection(train_filenames)
    assert len(overlap) == 0, f"LỖI RÒ RỈ DỮ LIỆU: Trùng video giữa Train và Test: {overlap}"

    all_videos = sorted(os.listdir(VIDEOS_DIR))
    covered = test_filenames.union(train_filenames)
    assert len(covered) == len(all_videos), f"LỖI: Chưa phân bổ hết video. Thiếu: {set(all_videos) - covered}"

    print(f"Tổng số video: {len(all_videos)}")
    print(f" - Tập Huấn luyện / Tinh chỉnh (Train/Fine-tune): {len(train_filenames)} video ({len(train_filenames)/len(all_videos)*100:.1f}%)")
    print(f" - Tập Kiểm thử / Đánh giá (Test/Benchmark):      {len(test_filenames)} video ({len(test_filenames)/len(all_videos)*100:.1f}%)")

    # Hash SHA-256 để khóa cứng tập Test (chống sửa đổi/pha trộn)
    test_manifest = []
    for item in TEST_VIDEOS:
        path = os.path.join(VIDEOS_DIR, item["filename"])
        item["sha256"] = compute_sha256(path)
        item["size_bytes"] = os.path.getsize(path)
        test_manifest.append(item)

    train_manifest = []
    for item in TRAIN_VIDEOS:
        path = os.path.join(VIDEOS_DIR, item["filename"])
        item["sha256"] = compute_sha256(path)
        item["size_bytes"] = os.path.getsize(path)
        train_manifest.append(item)

    dataset_splits = {
        "policy": "SPLIT_BY_VIDEO_ZERO_LEAKAGE",
        "description": "Phân chia tập tinh chỉnh và tập kiểm thử hoàn toàn theo VIDEO độc lập. Tập kiểm thử bị khóa cứng, nghiêm cấm sử dụng cho huấn luyện hoặc tinh chỉnh trọng số.",
        "lock_status": "LOCKED",
        "forbidden_for_training": True,
        "test_set": {
            "count": len(test_manifest),
            "videos": test_manifest
        },
        "train_set": {
            "count": len(train_manifest),
            "videos": train_manifest
        }
    }

    # Xuất file JSON đặc tả phân chia
    json_path = os.path.join(SPLITS_DIR, "dataset_splits.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dataset_splits, f, ensure_ascii=False, indent=2)

    # Xuất danh sách txt riêng biệt
    test_txt = os.path.join(SPLITS_DIR, "test_videos_LOCKED.txt")
    with open(test_txt, "w", encoding="utf-8") as f:
        f.write("# TẬP KIỂM THỬ ĐÃ KHÓA (LOCKED BENCHMARK TEST SET)\n")
        f.write("# NGHIÊM CẤM DÙNG CÁC VIDEO NÀY ĐỂ HUẤN LUYỆN HOẶC TINH CHỈNH MÔ HÌNH\n\n")
        for item in test_manifest:
            f.write(f"{item['filename']} | SHA256: {item['sha256']} | {item['condition']} | {item['rationale']}\n")

    train_txt = os.path.join(SPLITS_DIR, "train_videos.txt")
    with open(train_txt, "w", encoding="utf-8") as f:
        f.write("# TẬP TINH CHỈNH / HUẤN LUYỆN (FINE-TUNING TRAIN SET)\n\n")
        for item in train_manifest:
            f.write(f"{item['filename']} | SHA256: {item['sha256']} | {item['condition']}\n")

    print(f"\n[OK] Xuất thành công:")
    print(f"     - {json_path}")
    print(f"     - {test_txt}")
    print(f"     - {train_txt}")

if __name__ == "__main__":
    generate_splits()
