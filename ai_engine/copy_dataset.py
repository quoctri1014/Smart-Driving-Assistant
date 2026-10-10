import shutil
from pathlib import Path

source = Path("..") / "yolo_plate_dataset"
base_out = Path("../datasets/license_plate_detection")

imgs = sorted([f for f in source.glob("*.jpg")])
print(f"Total images: {len(imgs)}")

split = int(len(imgs) * 0.9)

for i, img_path in enumerate(imgs):
    lbl_path = img_path.with_suffix(".txt")
    
    if i < split:
        dest_img = base_out / "images" / "train" / img_path.name
        dest_lbl = base_out / "labels" / "train" / lbl_path.name
    else:
        dest_img = base_out / "images" / "val" / img_path.name
        dest_lbl = base_out / "labels" / "val" / lbl_path.name
    
    shutil.copy2(img_path, dest_img)
    if lbl_path.exists():
        shutil.copy2(lbl_path, dest_lbl)
    
    if (i + 1) % 500 == 0:
        print(f"Copied {i+1}/{len(imgs)}")

print("Done!")
train_imgs = len(list((base_out / "images" / "train").glob("*.jpg")))
val_imgs = len(list((base_out / "images" / "val").glob("*.jpg")))
print(f"Train: {train_imgs}, Val: {val_imgs}")
