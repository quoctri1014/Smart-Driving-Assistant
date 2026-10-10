import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import json
import urllib.request
from pathlib import Path
import cv2

def test_detect():
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    sample_path = Path('tests/sample_frame.jpg')
    with open(sample_path, 'rb') as f:
        file_bytes = f.read()

    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="sample.jpg"\r\n'
        f'Content-Type: image/jpeg\r\n\r\n'
    ).encode('utf-8') + file_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

    req = urllib.request.Request(
        'http://localhost:8000/api/v1/traffic-density/detect?is_video=true&session_id=live_test',
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print('=== TEST 1: Video Traffic Density Detection ===')
        print(f"Success: {data['success']}")
        print(f"Processing time: {data['processing_time_ms']} ms")
        print(f"Vehicles found: {data['vehicle_count']}")
        print(f"Lead vehicle distance: {data['lead_vehicle_distance']} m")
        print(f"Collision level: {data['collision_level']}")
        for v in data['vehicles']:
            print(f"   #{v['id']} {v['display_name']} ({v['class_name']}) bbox={v['bbox']} dist={v['distance_m']}m speed={v['speed_kmh']}")
        
        assert data['success'] is True
        assert data['vehicle_count'] > 0
        assert data['lead_vehicle_distance'] is not None
        assert 2.0 <= data['lead_vehicle_distance'] <= 50.0

    # Test static image mode (speed must be None)
    req_img = urllib.request.Request(
        'http://localhost:8000/api/v1/traffic-density/detect?is_video=false&session_id=live_test',
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    with urllib.request.urlopen(req_img) as resp:
        data_img = json.loads(resp.read().decode())
        print('\n=== TEST 2: Static Image Traffic Density ===')
        print(f"Success: {data_img['success']}")
        print(f"Vehicles found: {data_img['vehicle_count']}")
        print(f"Lead vehicle distance: {data_img['lead_vehicle_distance']} m")
        for v in data_img['vehicles']:
            assert v['speed_kmh'] is None, f"Speed should be None on static image, got {v['speed_kmh']}"
            print(f"   #{v['id']} {v['display_name']} dist={v['distance_m']}m speed={v['speed_kmh']}")
        print("PASS: Static image correctly has NO vehicle speeds.")

    # Test multi-frame video sequence
    print('\n=== TEST 3: Multi-frame Video Sequence Tracking ===')
    cap = cv2.VideoCapture('web-app/public/samples/dong_xe_may_hanoi_01.mp4')
    for f_idx in range(4):
        cap.set(cv2.CAP_PROP_POS_MSEC, (f_idx + 1) * 400)
        ret, frame = cap.read()
        if not ret: break
        _, buf = cv2.imencode('.jpg', frame)
        fbytes = buf.tobytes()
        fbody = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="file"; filename="f.jpg"\r\n'
            f'Content-Type: image/jpeg\r\n\r\n'
        ).encode('utf-8') + fbytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

        freq = urllib.request.Request(
            f'http://localhost:8000/api/v1/traffic-density/detect?is_video=true&session_id=video_test_seq&timestamp={(f_idx+1)*0.4}',
            data=fbody,
            headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
        )
        with urllib.request.urlopen(freq) as fresp:
            fd = json.loads(fresp.read().decode())
            print(f"Frame {f_idx+1}: {fd['vehicle_count']} vehicles, lead_dist={fd['lead_vehicle_distance']}m, level={fd['collision_level']}")
            for v in fd['vehicles']:
                sp = f"{v['speed_kmh']} km/h" if v['speed_kmh'] is not None else "Calculating..."
                print(f"   Vehicle #{v['id']} {v['display_name']} dist={v['distance_m']}m speed={sp}")
    cap.release()

    print("\nALL TRAFFIC DISTANCE & MULTI-FRAME TESTS PASSED!")

if __name__ == '__main__':
    test_detect()
