from ultralytics import YOLO
import torch

# Automatically use GPU if available
device = 0 if torch.cuda.is_available() else 'cpu'
print("Using device:", "CUDA" if device == 0 else "CPU")

# Load and export model
model = YOLO('models/yolo11n.pt')
model.export(format="engine", device=device)

print("✅ Export complete: YOLO model saved as TensorRT engine.")