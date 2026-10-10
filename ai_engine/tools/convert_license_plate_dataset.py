"""
convert_license_plate_dataset.py
--------------------------------
Convert the Vietnamese license plate dataset from the GitHub source into
an Ultralytics YOLOv8-compatible directory structure.

Important:
- The upstream repository is NOT a native YOLO detection dataset.
- It contains image samples and KNN training data, but no YOLO bounding-box labels.
- This script therefore prepares the folder layout and copies images into the
  expected train/val structure.
- If no .txt label files are found, it creates empty placeholder labels so the
  folder structure is ready for later manual annotation or future labeling.

Usage:
    python tools/convert_license_plate_dataset.py \
        --source "tmp_vi_license_repo/data/image" \
        --output "datasets/license_plate_vietnam"
"""

import argparse
import shutil
from pathlib import Path


VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert Vietnamese license plate dataset to YOLO folder layout."
    )
    parser.add_argument(
        "--source",
        type=str,
        default="tmp_vi_license_repo/data/image",
        help="Path to the source image folder from the GitHub dataset repo.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="datasets/license_plate_vietnam",
        help="Destination dataset folder for the YOLO-ready structure.",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.9,
        help="Train/validation split ratio for images. Default: 0.9",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used when splitting images into train/val.",
    )
    return parser.parse_args()


def collect_images(source_dir: Path):
    """Return list of image files in the source folder."""
    images = []
    for path in sorted(source_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in VALID_IMAGE_EXTENSIONS:
            images.append(path)
    return images


def ensure_directories(output_dir: Path):
    """Create the required YOLO dataset folder layout."""
    (output_dir / "images" / "train").mkdir(parents=True, exist_ok=True)
    (output_dir / "images" / "val").mkdir(parents=True, exist_ok=True)
    (output_dir / "labels" / "train").mkdir(parents=True, exist_ok=True)
    (output_dir / "labels" / "val").mkdir(parents=True, exist_ok=True)


def write_data_yaml(output_dir: Path):
    """Write YOLO data.yaml with a single class: license_plate."""
    yaml_path = output_dir / "data.yaml"
    yaml_content = """train: images/train
val: images/val

nc: 1
names: ['license_plate']
"""
    yaml_path.write_text(yaml_content, encoding="utf-8")


def create_empty_label(label_path: Path):
    """Create a placeholder .txt file for annotation later."""
    label_path.write_text("", encoding="utf-8")


def main():
    args = parse_args()
    source_dir = Path(args.source).resolve()
    output_dir = Path(args.output).resolve()

    if not source_dir.exists():
        raise FileNotFoundError(f"Source dataset folder does not exist: {source_dir}")

    images = collect_images(source_dir)
    if not images:
        raise FileNotFoundError(
            f"No image files were found under '{source_dir}'. "
            "Expected .jpg/.png files for the dataset."
        )

    if not 0.0 < args.train_ratio < 1.0:
        raise ValueError("--train-ratio must be between 0 and 1 (exclusive).")

    ensure_directories(output_dir)

    import random

    random.seed(args.seed)
    random.shuffle(images)

    split_index = max(1, int(len(images) * args.train_ratio))
    train_images = images[:split_index]
    val_images = images[split_index:]

    # Copy images into train/val folders
    for image_path in train_images:
        target = output_dir / "images" / "train" / image_path.name
        shutil.copy2(image_path, target)

    for image_path in val_images:
        target = output_dir / "images" / "val" / image_path.name
        shutil.copy2(image_path, target)

    # Copy matching YOLO labels if the source already has them.
    # Otherwise create empty placeholder labels so the dataset structure is valid.
    found_label_files = 0
    for image_path in images:
        label_path = image_path.with_suffix(".txt")
        if label_path.exists():
            found_label_files += 1
            target_label = output_dir / "labels" / "train" / image_path.name.replace(image_path.suffix, ".txt")
            if image_path in train_images:
                shutil.copy2(label_path, target_label)
            else:
                target_label = output_dir / "labels" / "val" / image_path.name.replace(image_path.suffix, ".txt")
                shutil.copy2(label_path, target_label)

    if found_label_files == 0:
        print("[Warning] No YOLO-style .txt label files were found in the source dataset.")
        print("[Warning] The source repository is an OpenCV/KNN dataset, not a native YOLO object-detection dataset.")
        print("[Warning] Creating empty placeholder labels in the YOLO structure for later annotation.")

    for image_path in train_images:
        txt_name = image_path.name.replace(image_path.suffix, ".txt")
        target_label = output_dir / "labels" / "train" / txt_name
        if not target_label.exists():
            create_empty_label(target_label)

    for image_path in val_images:
        txt_name = image_path.name.replace(image_path.suffix, ".txt")
        target_label = output_dir / "labels" / "val" / txt_name
        if not target_label.exists():
            create_empty_label(target_label)

    write_data_yaml(output_dir)

    print(f"Source images found: {len(images)}")
    print(f"Train images: {len(train_images)}")
    print(f"Val images: {len(val_images)}")
    print(f"Dataset exported to: {output_dir}")
    print("Next step: annotate the license plate bounding boxes in the generated label files.")


if __name__ == "__main__":
    main()
