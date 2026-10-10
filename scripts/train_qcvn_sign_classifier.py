import json
import os
import sys
import time
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T
from PIL import Image

BASE_DIR = Path(__file__).resolve().parents[1]
CATALOG_PATH = BASE_DIR / "backend" / "app" / "assets" / "qcvn_signs" / "qcvn_signs_catalog.json"
IMG_DIR = BASE_DIR / "backend" / "app" / "assets" / "qcvn_signs"
OUTPUT_ONNX = BASE_DIR / "backend" / "app" / "assets" / "qcvn_sign_classifier.onnx"
OUTPUT_CLASSES = BASE_DIR / "backend" / "app" / "assets" / "qcvn_classes.json"
WEBAPP_ONNX = BASE_DIR / "web-app" / "public" / "models" / "qcvn_sign_classifier.onnx"
WEBAPP_CLASSES = BASE_DIR / "web-app" / "public" / "models" / "qcvn_classes.json"


class QCVNSignCNN(nn.Module):
    def __init__(self, num_classes=144):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.classifier = nn.Sequential(
            nn.Linear(256 * 4 * 4, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        feat = self.features(x)
        feat = feat.flatten(1)
        return self.classifier(feat)


class SyntheticQCVNDataset(Dataset):
    def __init__(self, templates, class_to_idx, samples_per_class=40, is_train=True):
        self.templates = templates
        self.class_to_idx = class_to_idx
        self.samples_per_class = samples_per_class
        self.is_train = is_train

        if is_train:
            self.transform = T.Compose([
                T.Resize((64, 64)),
                T.RandomApply([T.RandomRotation(14, fill=255)], p=0.8),
                T.RandomApply([T.RandomAffine(degrees=0, translate=(0.08, 0.08), scale=(0.85, 1.15), fill=255)], p=0.8),
                T.RandomApply([T.RandomPerspective(distortion_scale=0.22, p=1.0, fill=255)], p=0.6),
                T.ColorJitter(brightness=0.35, contrast=0.35, saturation=0.35, hue=0.04),
                T.RandomApply([T.GaussianBlur(kernel_size=(3, 3), sigma=(0.1, 1.8))], p=0.4),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
        else:
            self.transform = T.Compose([
                T.Resize((64, 64)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])

        self.samples = []
        for code, img in self.templates.items():
            idx = self.class_to_idx[code]
            count = samples_per_class if is_train else 5
            for _ in range(count):
                self.samples.append((img, idx))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        pil_img, label = self.samples[idx]
        tensor = self.transform(pil_img)
        return tensor, label


def main():
    print("=" * 60)
    print("  TRAINING QCVN 41:2019 / 2020 OFFICIAL TRAFFIC SIGN CLASSIFIER")
    print("=" * 60)

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    classes = [item["code"] for item in catalog]
    class_to_idx = {c: i for i, c in enumerate(classes)}
    num_classes = len(classes)
    print(f"Loaded {num_classes} official traffic sign classes from {CATALOG_PATH.name}")

    templates = {}
    for item in catalog:
        code = item["code"]
        fname = item["img_filename"]
        fpath = IMG_DIR / fname
        if fpath.exists():
            img = Image.open(fpath).convert("RGB")
            templates[code] = img
        else:
            print(f"Warning: missing image for {code}: {fname}")

    print(f"Loaded {len(templates)} template images from disk.")

    train_ds = SyntheticQCVNDataset(templates, class_to_idx, samples_per_class=25, is_train=True)
    val_ds = SyntheticQCVNDataset(templates, class_to_idx, samples_per_class=5, is_train=False)

    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False)

    print(f"Dataset generated: {len(train_ds)} training samples, {len(val_ds)} validation samples.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")

    model = QCVNSignCNN(num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    epochs = 7
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    start_time = time.time()
    for ep in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * x.size(0)
            preds = out.argmax(dim=1)
            correct += (preds == y).sum().item()
            total += x.size(0)

        scheduler.step()
        train_acc = correct / total * 100.0
        avg_loss = total_loss / total

        # Validation
        model.eval()
        v_correct = 0
        v_total = 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                out = model(x)
                preds = out.argmax(dim=1)
                v_correct += (preds == y).sum().item()
                v_total += x.size(0)
        val_acc = v_correct / v_total * 100.0

        print(f"Epoch [{ep:2d}/{epochs:2d}] - Loss: {avg_loss:.4f} - Train Acc: {train_acc:.2f}% - Val Acc: {val_acc:.2f}%")

    duration = time.time() - start_time
    print(f"\nTraining completed in {duration:.1f}s ({duration/60:.2f} min). Final Val Acc: {val_acc:.2f}%")

    # Save PyTorch weights
    pt_path = OUTPUT_ONNX.with_suffix(".pt")
    torch.save(model.state_dict(), str(pt_path))
    print(f"Saved PyTorch model weights to: {pt_path}")

    # Export to ONNX with dynamo=False (stable legacy TorchScript exporter)
    model.eval()
    dummy_input = torch.randn(1, 3, 64, 64, device=device)
    OUTPUT_ONNX.parent.mkdir(parents=True, exist_ok=True)
    WEBAPP_ONNX.parent.mkdir(parents=True, exist_ok=True)

    torch.onnx.export(
        model,
        dummy_input,
        str(OUTPUT_ONNX),
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
        opset_version=14,
        dynamo=False,
    )
    print(f"Exported ONNX model to: {OUTPUT_ONNX}")

    # Copy to webapp public models
    import shutil
    shutil.copy2(OUTPUT_ONNX, WEBAPP_ONNX)
    print(f"Copied ONNX model to: {WEBAPP_ONNX}")

    # Save class mappings
    class_meta = []
    for item in catalog:
        class_meta.append({
            "idx": class_to_idx[item["code"]],
            "code": item["code"],
            "name": item["name"],
            "category": item["category"],
            "action": item["action"],
            "speed_limit": item.get("speed_limit")
        })

    with open(OUTPUT_CLASSES, "w", encoding="utf-8") as f:
        json.dump(class_meta, f, ensure_ascii=False, indent=2)
    with open(WEBAPP_CLASSES, "w", encoding="utf-8") as f:
        json.dump(class_meta, f, ensure_ascii=False, indent=2)

    print(f"Saved class metadata mapping ({len(class_meta)} classes).")
    print("ALL DONE SUCCESSFULLY!")


if __name__ == "__main__":
    main()
