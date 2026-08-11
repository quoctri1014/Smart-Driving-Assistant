import os
from ultralytics import YOLO

def train_sign_recognition():
    print("Training Traffic Sign Recognition Model...")
    # Load a pretrained model
    model = YOLO("yolov8n.pt") 
    
    # Train the model
    # Note: Requires a data.yaml file pointing to your custom dataset
    if os.path.exists("data/signs/data.yaml"):
        results = model.train(data="data/signs/data.yaml", epochs=50, imgsz=640)
        print("Training complete! Model saved to runs/detect/train/weights/best.pt")
    else:
        print("Error: Dataset configuration 'data/signs/data.yaml' not found.")
        print("Please download a traffic sign dataset (e.g. from Roboflow) and place it in the data folder.")

if __name__ == "__main__":
    train_sign_recognition()
