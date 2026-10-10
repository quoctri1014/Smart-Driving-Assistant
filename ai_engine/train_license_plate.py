"""
train_license_plate.py
---------------------
Train a YOLOv8 model for Vietnamese license plate detection.

Requirements:
- Ultralytics YOLO
- Base model: yolov8n.pt
- Single class: license_plate
- Epochs: 100
- Image size: 640

Output:
- models/license_plate.pt

Usage:
    python train_license_plate.py
"""

from pathlib import Path

from ultralytics import YOLO


DATASET_YAML = "datasets/license_plate_detection/data.yaml"
MODEL_PATH = "yolov8n.pt"
OUTPUT_MODEL = "models/license_plate.pt"


def auto_batch_size(model_name: str = MODEL_PATH):
    """Return a simple batch size suggestion based on available CUDA memory.

    This function keeps the training pipeline simple and avoids hardcoding a
    batch size that may cause out-of-memory issues on smaller GPUs.
    """
    try:
        import torch

        if torch.cuda.is_available():
            gpu_mem_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            if gpu_mem_gb >= 8:
                return 16
            # A marketed 4 GB GPU reports slightly less than 4 GiB, so allow
            # for that difference when selecting the intended batch size.
            if gpu_mem_gb >= 3.5:
                return 8
            return 4
        return 4
    except Exception:
        return 4


def main():
    dataset_path = Path(DATASET_YAML)
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset YAML not found: {dataset_path}. "
            "Run the conversion script first to create the YOLO dataset structure."
        )

    model = YOLO(MODEL_PATH)
    batch_size = auto_batch_size()

    print(f"[Train] Using base model: {MODEL_PATH}")
    print(f"[Train] Batch size: {batch_size}")
    print(f"[Train] Dataset: {dataset_path}")

    model.train(
        data=str(dataset_path),
        epochs=100,
        imgsz=640,
        batch=batch_size,
        # Windows spawns a fresh Python process per DataLoader worker. Loading
        # the CUDA runtime in each process can exhaust a small system pagefile
        # (WinError 1455), so keep data loading in the training process.
        workers=0,
        name="license_plate",
        project="runs/train",
        exist_ok=True,
        hsv_h=0.0,
        hsv_s=0.0,
        hsv_v=0.0,
        degrees=0.0,
        translate=0.0,
        scale=0.0,
        fliplr=0.0,
        mosaic=0.0,
    )

    # Ultralytics may normalize/nest the requested project path depending on
    # its global runs directory. Use the trainer's resolved save directory
    # instead of assuming a relative output location.
    trained_model = Path(model.trainer.save_dir) / "weights" / "best.pt"
    output_path = Path(OUTPUT_MODEL)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if trained_model.exists():
        output_path.write_bytes(trained_model.read_bytes())
        print(f"[Train] Best model saved to: {output_path}")
    else:
        raise FileNotFoundError(
            f"Expected trained model not found after training: {trained_model}"
        )


if __name__ == "__main__":
    main()
