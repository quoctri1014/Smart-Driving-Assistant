"""
test_license_plate.py
--------------------
Quick smoke test for the trained license plate detector.

This script loads the trained model and runs detection on:
- a single image
- a sample video frame or frame sequence

It prints the bounding boxes and confidence scores to confirm the model is
working before integrating it into the main traffic pipeline.

Usage:
    python test_license_plate.py --image path/to/image.jpg
    python test_license_plate.py --video path/to/video.mp4
    python test_license_plate.py --video path/to/video.mp4 --frame-index 10
"""

import argparse
from pathlib import Path

import cv2

from ultralytics import YOLO


MODEL_PATH = "models/license_plate.pt"


def parse_args():
    parser = argparse.ArgumentParser(description="Test the license plate detector.")
    parser.add_argument("--image", type=str, default=None, help="Path to a test image.")
    parser.add_argument("--video", type=str, default=None, help="Optional sample video path.")
    parser.add_argument(
        "--frame-index",
        type=int,
        default=None,
        help="Only test this frame. Omit to process and display the full video.",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Process the full video without opening a preview window.",
    )
    return parser.parse_args()


def detect_on_image(model, image_path: str):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found or cannot be read: {image_path}")

    results = model(image, conf=0.25, verbose=False)[0]
    print(f"[Image] Results for: {image_path}")
    for box in results.boxes:
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        conf = float(box.conf[0])
        cls_id = int(box.cls[0])
        print(f"  class={cls_id} conf={conf:.3f} box=({x1}, {y1}, {x2}, {y2})")

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            image,
            f"{conf:.2f}",
            (x1, max(0, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    out_path = Path("output") / "license_plate_test_result.jpg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), image)
    print(f"[Image] Saved result: {out_path}")


def draw_detections(model, frame):
    results = model(frame, conf=0.25, verbose=False)[0]
    detections = []
    for box in results.boxes:
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        conf = float(box.conf[0])
        detections.append((conf, (x1, y1, x2, y2)))
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"license_plate {conf:.2f}",
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 0),
            2,
        )
    return detections


def detect_on_video(model, video_path: str, frame_index=None, display=True):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Video cannot be opened: {video_path}")

    if frame_index is not None and frame_index < 0:
        cap.release()
        raise ValueError("--frame-index must be zero or greater.")

    if frame_index is not None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise ValueError(f"Frame {frame_index} is outside the video.")

        detections = draw_detections(model, frame)
        print(f"[Video] Results for frame {frame_index}")
        for conf, (x1, y1, x2, y2) in detections:
            print(f"  conf={conf:.3f} box=({x1}, {y1}, {x2}, {y2})")

        out_path = Path("output") / "license_plate_video_test_frame.jpg"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), frame)
        print(f"[Video] Saved frame result: {out_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if fps and fps > 0 else 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out_path = Path("output") / "license_plate_video_result.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Cannot create output video: {out_path}")

    print("[Video] Processing full video. Press Q in the preview window to stop.")
    current_frame = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        draw_detections(model, frame)
        writer.write(frame)
        current_frame += 1

        if display:
            cv2.imshow("License Plate Detection - Press Q to stop", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        if current_frame % 100 == 0:
            print(f"[Video] Processed {current_frame}/{total_frames or '?'} frames")

    cap.release()
    writer.release()
    if display:
        cv2.destroyAllWindows()
    print(f"[Video] Saved result: {out_path}")


def main():
    args = parse_args()
    model_path = Path(MODEL_PATH)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Trained model not found: {model_path}. "
            "Train the model first with 'python train_license_plate.py'."
        )

    model = YOLO(str(model_path))

    if args.image:
        detect_on_image(model, args.image)
    elif args.video:
        detect_on_video(model, args.video, args.frame_index, not args.no_display)
    else:
        print("[Info] No image or video was provided. Run with --image or --video.")


if __name__ == "__main__":
    main()
