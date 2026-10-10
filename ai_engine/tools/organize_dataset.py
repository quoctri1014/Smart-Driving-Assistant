#!/usr/bin/env python3
"""
Organize yolo_plate_dataset into YOLO train/val structure
"""

import shutil
from pathlib import Path
import random

# Set seed for reproducibility
random.seed(42)

# Paths
SOURCE_DIR = Path("../../yolo_plate_dataset")
OUTPUT_DIR = Path("../datasets/license_plate_detection")
TRAIN_RATIO = 0.9

def organize_dataset():
    """Copy and organize dataset into train/val split"""
    
    # Create directories
    images_train = OUTPUT_DIR / "images" / "train"
    images_val = OUTPUT_DIR / "images" / "val"
    labels_train = OUTPUT_DIR / "labels" / "train"
    labels_val = OUTPUT_DIR / "labels" / "val"
    
    for d in [images_train, images_val, labels_train, labels_val]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Get all image files
    image_files = sorted([f for f in SOURCE_DIR.glob("*.jpg")])
    print(f"📊 Total images found: {len(image_files)}")
    
    # Split into train/val
    split_idx = int(len(image_files) * TRAIN_RATIO)
    train_files = image_files[:split_idx]
    val_files = image_files[split_idx:]
    
    print(f"📌 Train: {len(train_files)} | Val: {len(val_files)}")
    
    # Copy train files
    for img_file in train_files:
        txt_file = img_file.with_suffix('.txt')
        
        # Copy image
        dest_img = images_train / img_file.name
        if not dest_img.exists():
            shutil.copy2(img_file, dest_img)
        
        # Copy label
        if txt_file.exists():
            dest_txt = labels_train / txt_file.name
            if not dest_txt.exists():
                shutil.copy2(txt_file, dest_txt)
    
    # Copy val files
    for img_file in val_files:
        txt_file = img_file.with_suffix('.txt')
        
        # Copy image
        dest_img = images_val / img_file.name
        if not dest_img.exists():
            shutil.copy2(img_file, dest_img)
        
        # Copy label
        if txt_file.exists():
            dest_txt = labels_val / txt_file.name
            if not dest_txt.exists():
                shutil.copy2(txt_file, dest_txt)
    
    # Verify
    train_imgs = len(list(images_train.glob("*.jpg")))
    val_imgs = len(list(images_val.glob("*.jpg")))
    train_labels = len(list(labels_train.glob("*.txt")))
    val_labels = len(list(labels_val.glob("*.txt")))
    
    print(f"\n✅ Organization complete!")
    print(f"   Train images: {train_imgs}")
    print(f"   Train labels: {train_labels}")
    print(f"   Val images: {val_imgs}")
    print(f"   Val labels: {val_labels}")

if __name__ == "__main__":
    try:
        organize_dataset()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
