import os
import json
import hashlib
import pytest

SPLITS_PATH = "tests/benchmark/splits/dataset_splits.json"
VIDEOS_DIR = "tests/benchmark/videos"

def test_dataset_splits_zero_leakage():
    assert os.path.exists(SPLITS_PATH), "File dataset_splits.json không tồn tại!"
    
    with open(SPLITS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    test_videos = [v["filename"] for v in data["test_set"]["videos"]]
    train_videos = [v["filename"] for v in data["train_set"]["videos"]]
    
    # 1. Đảm bảo 100% không có video nào xuất hiện đồng thời trong cả 2 tập
    intersection = set(test_videos).intersection(set(train_videos))
    assert len(intersection) == 0, f"RÒ RỈ DỮ LIỆU: Video bị trùng giữa Train và Test: {intersection}"
    
    # 2. Đảm bảo tổng số video khớp
    total = len(test_videos) + len(train_videos)
    assert total == 17, f"Tổng số video phải là 17, thực tế: {total}"
    assert len(test_videos) == 7
    assert len(train_videos) == 10
    
    # 3. Đảm bảo cờ khóa tập test được kích hoạt
    assert data["lock_status"] == "LOCKED"
    assert data["forbidden_for_training"] is True

def test_dataset_test_set_tamper_proofing():
    """Kiểm tra mã băm SHA-256 của tập Test trên đĩa để chống tráo đổi video."""
    with open(SPLITS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for item in data["test_set"]["videos"]:
        vpath = os.path.join(VIDEOS_DIR, item["filename"])
        assert os.path.exists(vpath), f"Video test không tồn tại: {vpath}"
        
        sha = hashlib.sha256()
        with open(vpath, "rb") as vf:
            while chunk := vf.read(65536):
                sha.update(chunk)
                
        actual_hash = sha.hexdigest()
        assert actual_hash == item["sha256"], f"Video {item['filename']} bị sai lệch hash SHA-256! Có thể đã bị sửa đổi."
