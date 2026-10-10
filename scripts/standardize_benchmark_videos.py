import os
import sys
import json
import time
import requests
import cv2
import numpy as np

DOWNLOAD_DIR = "tests/benchmark/downloads"
OUTPUT_DIR = "tests/benchmark/videos"
METADATA_DIR = "tests/benchmark/metadata"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

# Additional night/rain/glare clips to download
ROADSCAPES_BASE = "https://huggingface.co/datasets/vijpandaturtle/roadscapes-video/resolve/main/test"
ADDITIONAL_CLIPS = [
    ("Sequence_Night_12/Sequence_Night_12_clip1.mp4", "night_clip1.mp4"),
    ("Sequence_Night_12/Sequence_Night_12_clip2.mp4", "night_clip2.mp4"),
    ("Sequence_Night_12/Sequence_Night_12_clip80.mp4", "night_clip80.mp4"),
    ("Sequence_Night_12/Sequence_Night_12_clip79.mp4", "night_clip79.mp4"),
    ("Sequence_Night_16/Sequence_Night_16_clip12.mp4", "rain_night_clip12.mp4"),
    ("Sequence_Night_16/Sequence_Night_16_clip13.mp4", "rain_night_clip13.mp4"),
    ("Sequence_Night_8/Sequence_Night_8_clip11.mp4", "rain_windshield_clip11.mp4"),
    ("Sequence_Night_8/Sequence_Night_8_clip12.mp4", "rain_windshield_clip12.mp4"),
    ("Sequence_Day_18/Sequence_Day_18_clip14.mp4", "rain_day_clip14.mp4"),
    ("Sequence_Day_18/Sequence_Day_18_clip15.mp4", "rain_day_clip15.mp4"),
    ("Sequence_Day_18/Sequence_Day_18_clip58.mp4", "glare_clip58.mp4"),
    ("Sequence_Day_18/Sequence_Day_18_clip57.mp4", "glare_clip57.mp4"),
]

def download_additional():
    headers = {"User-Agent": "Mozilla/5.0"}
    for rel_path, save_name in ADDITIONAL_CLIPS:
        dest = os.path.join(DOWNLOAD_DIR, save_name)
        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            continue
        url = f"{ROADSCAPES_BASE}/{rel_path}"
        try:
            r = requests.get(url, headers=headers, stream=True, timeout=30)
            if r.status_code == 200:
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=512 * 1024):
                        if chunk:
                            f.write(chunk)
                print(f"[OK] Downloaded {save_name}: {os.path.getsize(dest):,} bytes")
            else:
                print(f"[FAIL] HTTP {r.status_code} for {save_name}")
        except Exception as e:
            print(f"[ERR] {save_name}: {e}")

def cut_and_normalize(input_paths, output_path, start_sec=0.0, target_duration=30.0, target_w=1280, target_h=720, target_fps=30.0):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, target_fps, (target_w, target_h))
    
    total_target_frames = int(target_duration * target_fps)
    written_frames = 0
    
    if not isinstance(input_paths, list):
        input_paths = [input_paths]
        
    for inp in input_paths:
        cap = cv2.VideoCapture(inp)
        fps = cap.get(cv2.CAP_PROP_FPS) or target_fps
        skip_frames = int(start_sec * fps)
        
        for _ in range(skip_frames):
            ret = cap.grab()
            if not ret:
                break
                
        while written_frames < total_target_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if frame.shape[1] != target_w or frame.shape[0] != target_h:
                frame = cv2.resize(frame, (target_w, target_h))
            out.write(frame)
            written_frames += 1
            
        cap.release()
        if written_frames >= total_target_frames:
            break
            
    # If still short, loop slightly to reach at least 30s
    while written_frames < total_target_frames and written_frames > 0:
        cap = cv2.VideoCapture(input_paths[0])
        while written_frames < total_target_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if frame.shape[1] != target_w or frame.shape[0] != target_h:
                frame = cv2.resize(frame, (target_w, target_h))
            out.write(frame)
            written_frames += 1
        cap.release()
        
    out.release()
    return written_frames / target_fps

def standardize_dataset():
    print("--- 1. Downloading additional night/rain/glare clips ---")
    download_additional()
    
    print("--- 2. Processing & Normalizing Videos (Target: 17 clips, 720p @ 30fps) ---")
    
    bach_mai = os.path.join(DOWNLOAD_DIR, "raw_hanoi_bach_mai.mp4")
    uit_demo = os.path.join(DOWNLOAD_DIR, "raw_uit_cs338_demo.mp4")
    uit_cam = os.path.join(DOWNLOAD_DIR, "raw_uit_cs338_cam.mp4")
    uit_v1 = os.path.join(DOWNLOAD_DIR, "raw_uit_cs338_v1.mp4")
    uit_v2 = os.path.join(DOWNLOAD_DIR, "raw_uit_cs338_v2.mp4")
    tuanquoc = os.path.join(DOWNLOAD_DIR, "raw_tuanquoc_vehicle.mp4")
    kasumi_sign = os.path.join(DOWNLOAD_DIR, "raw_kasumi_sign_dashcam.mp4")
    franceto_1 = os.path.join(DOWNLOAD_DIR, "raw_franceto_traffic_sign_01.mp4")
    franceto_2 = os.path.join(DOWNLOAD_DIR, "raw_franceto_traffic_sign_02.mp4")
    
    TASKS = [
        # (out_name, inputs, start_sec, dur, cond, loc, road_type, weather, sharpness)
        ("dong_xe_may_hanoi_01.mp4", [bach_mai], 0.0, 35.0, "dong_xe_may", "hanoi", "Do thi noi thanh", "Ngay, nang nhe", "Cao (720p)"),
        ("dong_xe_may_hanoi_02.mp4", [bach_mai], 90.0, 35.0, "dong_xe_may", "hanoi", "Do thi noi thanh", "Ngay, nhieu may", "Cao (720p)"),
        ("dong_xe_may_hanoi_03.mp4", [bach_mai], 200.0, 35.0, "dong_xe_may", "hanoi", "Do thi nga tu", "Ngay, mat me", "Cao (720p)"),
        ("dong_xe_may_hcm_01.mp4", [uit_demo], 0.0, 35.0, "dong_xe_may", "hcm", "Vong xoay do thi", "Ngay, nang gat", "Rat cao (1080p source)"),
        ("dong_xe_may_hcm_02.mp4", [uit_cam], 0.0, 30.0, "dong_xe_may", "hcm", "Nga tu do thi", "Ngay, nang", "Cao (720p)"),
        ("ngay_hcm_01.mp4", [uit_v1], 0.0, 30.0, "ngay", "hcm", "Dai lo do thi", "Ngay, trong xanh", "Rat cao (1080p source)"),
        ("ngay_hcm_02.mp4", [tuanquoc], 0.0, 30.0, "ngay", "hcm", "Quoc lo ven do", "Ngay, nang", "Trung binh (360p upscaled)"),
        ("ngay_hanoi_01.mp4", [bach_mai], 320.0, 35.0, "ngay", "hanoi", "Truc duong chinh", "Ngay, ram mat", "Cao (720p)"),
        ("bien_bao_hanoi_01.mp4", [kasumi_sign], 0.0, 30.0, "bien_bao", "hanoi", "Do thi co bien bao", "Ngay, quang may", "Cao (Dashcam)"),
        ("bien_bao_hcm_01.mp4", [franceto_1], 0.0, 35.0, "bien_bao", "hcm", "Tuyen duong co bien bao", "Ngay, nang", "Cao (Dashcam)"),
        ("bien_bao_hcm_02.mp4", [franceto_2], 0.0, 30.0, "bien_bao", "hcm", "Tuyen duong co bien bao", "Ngay, nang", "Cao (Dashcam)"),
        ("dem_dashcam_01.mp4", [os.path.join(DOWNLOAD_DIR, "night_clip1.mp4"), os.path.join(DOWNLOAD_DIR, "night_clip2.mp4")], 0.0, 30.0, "dem", "quoc_te_pov", "Duong pho dem co den duong", "Dem, den pha chieu", "Cao (HD)"),
        ("dem_dashcam_02.mp4", [os.path.join(DOWNLOAD_DIR, "night_clip80.mp4"), os.path.join(DOWNLOAD_DIR, "night_clip79.mp4")], 0.0, 30.0, "dem", "quoc_te_pov", "Duong cao toc dem", "Dem, toi kem den duong", "Cao (HD)"),
        ("mua_dashcam_01.mp4", [os.path.join(DOWNLOAD_DIR, "rain_night_clip12.mp4"), os.path.join(DOWNLOAD_DIR, "rain_night_clip13.mp4")], 0.0, 30.0, "mua", "quoc_te_pov", "Duong pho mua dem", "Mua nhe, mat duonguot", "Cao (HD)"),
        ("mua_dashcam_02.mp4", [os.path.join(DOWNLOAD_DIR, "rain_windshield_clip11.mp4"), os.path.join(DOWNLOAD_DIR, "rain_windshield_clip12.mp4")], 0.0, 30.0, "mua", "quoc_te_pov", "Kinh lai dinh hat mua", "Mua, gat nuoc", "Cao (HD)"),
        ("mua_dashcam_03.mp4", [os.path.join(DOWNLOAD_DIR, "rain_day_clip14.mp4"), os.path.join(DOWNLOAD_DIR, "rain_day_clip15.mp4")], 0.0, 30.0, "mua", "quoc_te_pov", "Duong ngoai o mua ngay", "Am u, duong tron", "Cao (HD)"),
        ("nguoc_sang_dashcam_01.mp4", [os.path.join(DOWNLOAD_DIR, "glare_clip58.mp4"), os.path.join(DOWNLOAD_DIR, "glare_clip57.mp4")], 0.0, 30.0, "nguoc_sang", "quoc_te_pov", "Tuyen duong chieu thang mat troi", "Nang gat, loa sang", "Cao (HD)"),
    ]
    
    metadata_list = []
    
    for item in TASKS:
        out_name, inputs, start_sec, dur, cond, loc, road_type, weather, sharpness = item
        out_path = os.path.join(OUTPUT_DIR, out_name)
        
        real_dur = cut_and_normalize(inputs, out_path, start_sec=start_sec, target_duration=dur)
        file_size = os.path.getsize(out_path)
        
        meta = {
            "filename": out_name,
            "filepath": out_path.replace("\\", "/"),
            "condition": cond,
            "location": loc,
            "duration_sec": round(real_dur, 1),
            "resolution": "1280x720",
            "fps": 30.0,
            "road_type": road_type,
            "weather": weather,
            "sharpness": sharpness,
            "file_size_bytes": file_size,
            "sources": [os.path.basename(p) for p in inputs]
        }
        metadata_list.append(meta)
        print(f"[STANDARDIZED] {out_name:28} : {real_dur:.1f}s | {file_size:,} bytes | {cond} | {weather}")

    meta_file = os.path.join(METADATA_DIR, "videos_metadata.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, ensure_ascii=False, indent=2)
        
    print(f"\nSuccessfully standardized {len(metadata_list)} benchmark videos. Metadata saved to {meta_file}.")

if __name__ == "__main__":
    standardize_dataset()
