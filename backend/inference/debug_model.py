
import sys
import os
from pathlib import Path
import logging
import cv2
import numpy as np
import torch
import openvino as ov

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from backend.models.model import SegmentationModel, build_model

# Config
IMAGE_PATH = r"c:\MyStuff\VS\MECup\backend\captured_images\scan_20260212_190653\grid_1_1.jpg"
MODEL_PATH = r"c:\MyStuff\VS\MECup\backend\inference\openvino_models\black.pth"
OV_MODEL_PATH = r"c:\MyStuff\VS\MECup\backend\inference\openvino_models\black_model.xml"

def debug_inference():
    print(f"Debugging model: {MODEL_PATH}")
    
    # 1. Load PyTorch Model
    device = torch.device("cpu")
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    
    config = {
        'model': {
            'encoder': 'dinov2_vitb14',
            'skip_layers': [3, 7, 11],
            'decoder_channels': [256, 128, 64],
            'num_classes': 2,
            'encoder_frozen': True
        }
    }
    
    if isinstance(checkpoint, dict) and 'config' in checkpoint:
        config = checkpoint['config']
        print("Loaded config from checkpoint.")
    
    model = build_model(config)
    model.to(device)
    model.eval()
    
    state_dict = checkpoint
    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
        
    msg = model.load_state_dict(state_dict, strict=False)
    print(f"PyTorch Load Result: {msg}")
    
    # 2. Prep Image
    img = cv2.imread(IMAGE_PATH)
    if img is None:
        print("Failed to load image.")
        return
        
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (518, 518))
    
    # PyTorch Preprocessing (ImageNet)
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    
    input_norm = (img_resized / 255.0 - mean) / std
    input_norm = input_norm.transpose(2, 0, 1).astype(np.float32)
    input_tensor = torch.from_numpy(input_norm).unsqueeze(0).to(device)
    
    # 3. Validation: PyTorch Inference
    with torch.no_grad():
        pt_output = model(input_tensor)
        
    print("\n--- PyTorch Output Statistics ---")
    print(f"Shape: {pt_output.shape}")
    print(f"Min: {pt_output.min().item():.4f}")
    print(f"Max: {pt_output.max().item():.4f}")
    print(f"Mean: {pt_output.mean().item():.4f}")
    
    # Check for actual detections (argmax)
    pt_pred = torch.argmax(pt_output, dim=1).numpy()
    print(f"Unique classes predicted: {np.unique(pt_pred)}")
    
    # 4. OpenVINO Inference
    print("\n--- OpenVINO Inference ---")
    core = ov.Core()
    ov_model = core.read_model(OV_MODEL_PATH)
    compiled_model = core.compile_model(ov_model, "CPU")
    
    # OpenVINO Preprocessing check
    # Our inference_service uses PPP. Here we manually feed the processed tensor 
    # to see if the model itself is ok.
    # Note: convert_model.py exported the model expecting input [1, 3, 518, 518]
    
    ov_output = compiled_model(input_tensor)[0]
    
    print(f"Shape: {ov_output.shape}")
    print(f"Min: {ov_output.min():.4f}")
    print(f"Max: {ov_output.max():.4f}")
    print(f"Mean: {ov_output.mean():.4f}")
    
    ov_pred = np.argmax(ov_output, axis=1)
    print(f"Unique classes predicted: {np.unique(ov_pred)}")

if __name__ == "__main__":
    debug_inference()
