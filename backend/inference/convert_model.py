
import sys
import os
from pathlib import Path
import logging

# Add the project root to sys.path to allow imports from backend
# Assuming this script is in backend/inference/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

import torch
import openvino as ov
import yaml

try:
    from backend.models.model import SegmentationModel, build_model
except ImportError as e:
    print(f"Error importing model definition: {e}")
    print("Make sure you are running this script from the project root or that 'backend' is in your Python path.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define model paths
BASE_DIR = Path(__file__).parent / "openvino_models"
WHITE_MODEL_PATH = BASE_DIR / "white_matt.pth"
BLACK_MODEL_PATH = BASE_DIR / "black.pth"

# Default configuration if not found in checkpoint
DEFAULT_CONFIG = {
    'model': {
        'encoder': 'dinov2_vitb14',
        'skip_layers': [3, 7, 11],
        'decoder_channels': [256, 128, 64],
        'num_classes': 4,
        'encoder_frozen': True
    }
}

def convert_to_openvino(pth_path, output_dir, model_name, img_size=518):
    """
    Convert a PyTorch .pth model to OpenVINO IR format.
    """
    if not pth_path.exists():
        logger.warning(f"Skipping {model_name}: Model file not found at {pth_path}")
        return

    logger.info(f"Converting {model_name} from {pth_path}...")
    
    device = torch.device("cpu")
    
    try:
        # Load checkpoint
        checkpoint = torch.load(pth_path, map_location=device)
        
        config = DEFAULT_CONFIG
        state_dict = None
        
        if isinstance(checkpoint, dict):
            if 'config' in checkpoint:
                config = checkpoint['config']
                logger.info(f"Loaded config from checkpoint for {model_name}")
            else:
                logger.info(f"No config found in checkpoint, using default for {model_name}")
                
            if 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
            else:
                # Assume the dict itself is the state dict if 'model_state_dict' is missing
                # but has keys that look like weights
                if any(k.startswith('encoder') or k.startswith('decoder') for k in checkpoint.keys()):
                     state_dict = checkpoint
                else:
                     logger.error(f"Could not find state_dict in checkpoint for {model_name}")
                     return
        else:
             logger.error(f"Checkpoint is not a dict, cannot process {model_name}")
             return

        # Build model
        try:
             # Ensure config has 'model' key for build_model
             if 'model' not in config:
                 config = {'model': config}
                 
             model = build_model(config)
             model.to(device)
             model.eval()
             
             # Load weights
             if state_dict:
                 msg = model.load_state_dict(state_dict, strict=False)
                 logger.info(f"Loaded weights with result: {msg}")
             
        except Exception as e:
            logger.error(f"Failed to build/load model {model_name}: {e}")
            return

        # Create dummy input
        dummy_input = torch.randn(1, 3, img_size, img_size).to(device)
        
        # Convert to OpenVINO
        logger.info(f"Starting OpenVINO conversion for {model_name}...")
        ov_model = ov.convert_model(model, example_input=dummy_input)
        
        # Save IR
        output_path_xml = output_dir / f"{model_name}.xml"
        ov.save_model(ov_model, output_path_xml)
        logger.info(f"Successfully converted {model_name} to {output_path_xml}")
        
    except Exception as e:
        logger.error(f"Failed to convert {model_name}: {e}", exc_info=True)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--img_size", type=int, default=518, help="Input image size")
    args = parser.parse_args()

    output_dir = BASE_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if OpenVINO models already exist? No, we want to overwrite/regenerate.

    # convert_to_openvino(WHITE_MODEL_PATH, output_dir, "white_model", args.img_size)
    convert_to_openvino(BLACK_MODEL_PATH, output_dir, "black_model", args.img_size)
