import os
import sys
import json
import csv
import cv2
import numpy as np
from ultralytics import YOLO

ANNOTATIONS_DIR = "tests/benchmark/annotations"
VIDEOS_DIR = "tests/benchmark/videos"
os.makedirs(ANNOTATIONS_DIR, exist_ok=True)

# 1. Label Studio Configuration XML
LABEL_STUDIO_XML = """<View>
  <Header value="ADAS Traffic Vietnam Benchmark Annotation Project" />
  
  <View style="display: flex;">
    <View style="flex: 70%">
      <Image name="image" value="$image" zoom="true" rotateControl="true"/>
    </View>
    
    <View style="flex: 30%; margin-left: 20px;">
      <Header value="1. Đối tượng giao thông (Traffic Objects)" />
      <RectangleLabels name="objects" toName="image">
        <Label value="car" background="#3388FF" />
        <Label value="motorbike" background="#FF3333" />
        <Label value="bus" background="#33FF57" />
        <Label value="truck" background="#FF9933" />
        <Label value="bicycle" background="#CC33FF" />
        <Label value="pedestrian" background="#FFFF33" />
        <Label value="license_plate" background="#00FFFF" />
        <Label value="traffic_sign" background="#FF00AA" />
      </RectangleLabels>

      <Header value="2. Trạng thái kiểm duyệt (Audit Status)" />
      <Choices name="review_status" toName="image" required="true">
        <Choice value="CHƯA DUYỆT" selected="true" />
        <Choice value="ĐÃ DUYỆT - HỢP LỆ" />
        <Choice value="ĐÃ DUYỆT - ĐIỀU CHỈNH BOX" />
        <Choice value="BÁC BỎ - FALSE POSITIVE" />
      </Choices>

      <Header value="3. Điều kiện khó (Edge Case Tags)" />
      <Choices name="edge_cases" toName="image" choice="multiple">
        <Choice value="Đêm tối / Chói đèn pha" />
        <Choice value="Trời mưa / Kính lái đọng nước" />
        <Choice value="Ngược sáng / Nắng gắt" />
        <Choice value="Xe máy chen chúc / Che khuất > 50%" />
        <Choice value="Biển số nhỏ / Mờ xa" />
        <Choice value="Biển báo che khuất / Xoay lệch" />
      </Choices>
    </View>
  </View>
</View>
"""

# 2. CVAT Project Specification JSON
CVAT_SPEC = {
    "name": "ADAS_Vietnam_Benchmark_Project",
    "version": "1.1",
    "categories": [
        {"id": 0, "name": "car", "color": "#3388FF", "type": "rectangle"},
        {"id": 1, "name": "motorbike", "color": "#FF3333", "type": "rectangle"},
        {"id": 2, "name": "bus", "color": "#33FF57", "type": "rectangle"},
        {"id": 3, "name": "truck", "color": "#FF9933", "type": "rectangle"},
        {"id": 4, "name": "bicycle", "color": "#CC33FF", "type": "rectangle"},
        {"id": 5, "name": "pedestrian", "color": "#FFFF33", "type": "rectangle"},
        {"id": 6, "name": "license_plate", "color": "#00FFFF", "type": "rectangle"},
        {"id": 7, "name": "traffic_sign", "color": "#FF00AA", "type": "rectangle"}
    ],
    "default_status": "CHƯA DUYỆT",
    "pre_annotation_model": "YOLOv8m (Ultralytics, 26M params)",
    "target_model_under_test": "YOLOv8n (Custom pipeline, 3M params)"
}

def generate_annotations_and_priority_list():
    # Save Studio & CVAT specs
    xml_path = os.path.join(ANNOTATIONS_DIR, "label_studio_config.xml")
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(LABEL_STUDIO_XML)
    print(f"[OK] Saved Label Studio config: {xml_path}")

    cvat_path = os.path.join(ANNOTATIONS_DIR, "cvat_project_spec.json")
    with open(cvat_path, "w", encoding="utf-8") as f:
        json.dump(CVAT_SPEC, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved CVAT specification: {cvat_path}")

    # Load independent larger model YOLOv8m
    yolo_m_path = "models/yolov8m.pt" if os.path.exists("models/yolov8m.pt") else "yolov8m.pt"
    model_m = YOLO(yolo_m_path)

    video_files = sorted([f for f in os.listdir(VIDEOS_DIR) if f.endswith(".mp4")])
    
    all_draft_frames = []
    
    # Sample 1 frame per 1.5 seconds (~20-23 frames per 30-35s video)
    for vname in video_files:
        vpath = os.path.join(VIDEOS_DIR, vname)
        cap = cv2.VideoCapture(vpath)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_f = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step_frames = int(fps * 1.5)  # 1 frame per 1.5s
        
        frame_idx = 0
        while frame_idx < total_f:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break
                
            time_sec = round(frame_idx / fps, 2)
            
            # Predict using YOLOv8m
            preds = model_m.predict(frame, conf=0.35, verbose=False)[0]
            
            boxes = []
            for b in preds.boxes:
                cid = int(b.cls[0])
                cname = model_m.names[cid]
                if cname in ("motorcycle", "motorbike"):
                    cname = "motorbike"
                elif cname in ("person",):
                    cname = "pedestrian"
                    
                if cname in ("car", "motorbike", "bus", "truck", "bicycle", "pedestrian"):
                    x1, y1, x2, y2 = b.xyxy[0].tolist()
                    boxes.append({
                        "cls_name": cname,
                        "box_xyxy": [round(x, 1) for x in [x1, y1, x2, y2]],
                        "pre_conf": round(float(b.conf[0]), 3),
                        "status": "CHƯA DUYỆT"  # BẮT BUỘC: Mọi nhãn chưa duyệt
                    })
                    
            # Determine edge case category & priority weight
            is_night = "dem_" in vname
            is_rain = "mua_" in vname
            is_glare = "nguoc_sang_" in vname
            is_sign = "bien_bao_" in vname
            is_dense = "dong_xe_may_" in vname
            
            difficulty_score = 0
            edge_tags = []
            if is_night:
                difficulty_score += 4
                edge_tags.append("Đêm tối / Chói đèn pha")
            if is_rain:
                difficulty_score += 4
                edge_tags.append("Trời mưa / Kính lái đọng nước")
            if is_glare:
                difficulty_score += 4
                edge_tags.append("Ngược sáng / Nắng gắt")
            if is_sign:
                difficulty_score += 3
                edge_tags.append("Biển báo nhỏ / Mờ xa")
            if is_dense:
                difficulty_score += 3
                edge_tags.append("Xe máy chen chúc dày đặc")
                
            # Extra difficulty if frame contains many tiny objects (< 600px area)
            small_boxes = [b for b in boxes if (b["box_xyxy"][2] - b["box_xyxy"][0]) * (b["box_xyxy"][3] - b["box_xyxy"][1]) < 600]
            if len(small_boxes) >= 2:
                difficulty_score += 2
                edge_tags.append("Nhiều vật thể nhỏ ở xa")
                
            all_draft_frames.append({
                "video_file": vname,
                "frame_index": frame_idx,
                "timestamp_sec": time_sec,
                "difficulty_score": difficulty_score,
                "edge_tags": edge_tags,
                "object_count": len(boxes),
                "objects": boxes,
                "audit_status": "CHƯA DUYỆT",
                "is_official_gt": False
            })
            
            frame_idx += step_frames
            
        cap.release()
        print(f"[PROCESSED] {vname}: {len([f for f in all_draft_frames if f['video_file'] == vname])} draft frames")

    # Save full draft pre-annotations
    draft_file = os.path.join(ANNOTATIONS_DIR, "draft_pre_annotations.json")
    with open(draft_file, "w", encoding="utf-8") as f:
        json.dump(all_draft_frames, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Saved {len(all_draft_frames)} draft frames to {draft_file}")

    # Select TOP 30% priority frames (highest difficulty: night, rain, glare, small sign, dense)
    all_draft_frames.sort(key=lambda x: (x["difficulty_score"], x["object_count"]), reverse=True)
    n_priority = int(len(all_draft_frames) * 0.30)
    priority_frames = all_draft_frames[:n_priority]

    # Save 30% priority review list (JSON and CSV)
    priority_json = os.path.join(ANNOTATIONS_DIR, "priority_30_percent_review.json")
    with open(priority_json, "w", encoding="utf-8") as f:
        json.dump(priority_frames, f, ensure_ascii=False, indent=2)

    priority_csv = os.path.join(ANNOTATIONS_DIR, "priority_30_percent_review.csv")
    with open(priority_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["priority_rank", "video_file", "frame_index", "timestamp_sec", "difficulty_score", "edge_tags", "object_count", "audit_status", "action_required"])
        for idx, item in enumerate(priority_frames, 1):
            writer.writerow([
                idx,
                item["video_file"],
                item["frame_index"],
                item["timestamp_sec"],
                item["difficulty_score"],
                "; ".join(item["edge_tags"]),
                item["object_count"],
                item["audit_status"],
                "Kiểm tra box xe máy/biển báo/lóa đèn; duyệt hoặc sửa box"
            ])

    print(f"[OK] Exported {len(priority_frames)} priority review frames (exactly {len(priority_frames)/len(all_draft_frames)*100:.1f}% of total) to:")
    print(f"     - {priority_json}")
    print(f"     - {priority_csv}")

if __name__ == "__main__":
    generate_annotations_and_priority_list()
