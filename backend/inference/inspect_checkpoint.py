
import torch
import sys
from pathlib import Path

MODEL_PATH = r"c:\MyStuff\VS\MECup\backend\inference\openvino_models\black.pth"

def inspect_checkpoint():
    print(f"Inspecting {MODEL_PATH}...")
    try:
        checkpoint = torch.load(MODEL_PATH, map_location="cpu")
        state_dict = None
        if isinstance(checkpoint, dict):
            if 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
            else:
                state_dict = checkpoint
        
        if state_dict:
            # Look for head weights
            head_weight = None
            head_bias = None
            for key in state_dict.keys():
                if 'head.weight' in key:
                    head_weight = state_dict[key]
                    print(f"Found head.weight: {head_weight.shape}")
                if 'head.bias' in key:
                    head_bias = state_dict[key]
                    print(f"Found head.bias: {head_bias.shape}")
            
            if head_weight is None:
                print("Could not find head.weight in state_dict")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_checkpoint()
