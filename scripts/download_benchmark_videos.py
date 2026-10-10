import os
import sys
import time
import requests

DOWNLOADS = [
    {
        "url": "https://huggingface.co/datasets/danny2507/learning-xu-ly-video/resolve/main/videos/hanoi_bach_mai_traffic.mp4",
        "save_name": "raw_hanoi_bach_mai.mp4",
        "source": "danny2507/learning-xu-ly-video (HuggingFace)",
        "condition": "dong_xe_may",
        "location": "hanoi"
    },
    {
        "url": "https://raw.githubusercontent.com/KasumiYae/Recognition-and-analysis-of-road-traffic-signs-in-Vietnam-Conditions-for-self-driving-cars/main/1.mp4",
        "save_name": "raw_kasumi_sign_dashcam.mp4",
        "source": "KasumiYae/Recognition-and-analysis-of-road-traffic-signs (GitHub)",
        "condition": "bien_bao",
        "location": "hanoi"
    },
    {
        "url": "https://raw.githubusercontent.com/franceto/YOLOv26-VietNam-Traffic-Sign/main/anh_video_test/7612660128940.mp4",
        "save_name": "raw_franceto_traffic_sign_01.mp4",
        "source": "franceto/YOLOv26-VietNam-Traffic-Sign (GitHub)",
        "condition": "bien_bao",
        "location": "hcm"
    },
    {
        "url": "https://raw.githubusercontent.com/franceto/YOLOv26-VietNam-Traffic-Sign/main/anh_video_test/7612678878718.mp4",
        "save_name": "raw_franceto_traffic_sign_02.mp4",
        "source": "franceto/YOLOv26-VietNam-Traffic-Sign (GitHub)",
        "condition": "bien_bao",
        "location": "hcm"
    },
    {
        "url": "https://raw.githubusercontent.com/tuanquoc-tran/Vehicle-detection/master/videos/video1.mp4",
        "save_name": "raw_tuanquoc_vehicle.mp4",
        "source": "tuanquoc-tran/Vehicle-detection (GitHub)",
        "condition": "ngay",
        "location": "hcm"
    },
    {
        "url": "https://raw.githubusercontent.com/phamthanhlam0201/CS338_Detecting_Tracking_and_Counting_Vietnam_Trafic_Vehicle/main/Sourcecode/Demo.mp4",
        "save_name": "raw_uit_cs338_demo.mp4",
        "source": "phamthanhlam0201/CS338 (GitHub - UIT VNU-HCM)",
        "condition": "dong_xe_may",
        "location": "hcm"
    },
    {
        "url": "https://raw.githubusercontent.com/phamthanhlam0201/CS338_Detecting_Tracking_and_Counting_Vietnam_Trafic_Vehicle/main/Sourcecode/assets/Videos/trafic_camera.mp4",
        "save_name": "raw_uit_cs338_cam.mp4",
        "source": "phamthanhlam0201/CS338 (GitHub - UIT VNU-HCM)",
        "condition": "dong_xe_may",
        "location": "hcm"
    },
    {
        "url": "https://raw.githubusercontent.com/phamthanhlam0201/CS338_Detecting_Tracking_and_Counting_Vietnam_Trafic_Vehicle/main/Sourcecode/assets/Videos/video1.mp4",
        "save_name": "raw_uit_cs338_v1.mp4",
        "source": "phamthanhlam0201/CS338 (GitHub - UIT VNU-HCM)",
        "condition": "ngay",
        "location": "hcm"
    },
    {
        "url": "https://raw.githubusercontent.com/phamthanhlam0201/CS338_Detecting_Tracking_and_Counting_Vietnam_Trafic_Vehicle/main/Sourcecode/assets/Videos/video2.mp4",
        "save_name": "raw_uit_cs338_v2.mp4",
        "source": "phamthanhlam0201/CS338 (GitHub - UIT VNU-HCM)",
        "condition": "ngay",
        "location": "hcm"
    }
]

def download_videos():
    out_dir = "tests/benchmark/downloads"
    os.makedirs(out_dir, exist_ok=True)
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for item in DOWNLOADS:
        target_path = os.path.join(out_dir, item["save_name"])
        if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
            print(f"[EXISTS] {item['save_name']} ({os.path.getsize(target_path):,} bytes)")
            continue
            
        print(f"[DOWNLOADING] {item['save_name']} from {item['url']} ...")
        try:
            r = requests.get(item["url"], headers=headers, stream=True, timeout=60)
            if r.status_code == 200:
                with open(target_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                print(f"[OK] Downloaded {item['save_name']}: {os.path.getsize(target_path):,} bytes")
            else:
                print(f"[FAIL] HTTP {r.status_code} for {item['save_name']}")
        except Exception as e:
            print(f"[ERROR] {item['save_name']}: {e}")

if __name__ == "__main__":
    download_videos()
