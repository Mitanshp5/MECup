
import sys
from pathlib import Path
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from backend.inference.inference_service import run_inference_task

# Configuration
IMAGE_PATH = r"c:\MyStuff\VS\MECup\backend\captured_images\scan_20260212_190653\grid_1_1.jpg"
OUTPUT_DIR = r"c:\MyStuff\VS\MECup\backend\captured_images\scan_20260212_190653\results_test_white"
MODEL_TYPE = "white" 
MM2_PER_PIXEL = 0.0037

if __name__ == "__main__":
    print(f"Testing WHITE model on {IMAGE_PATH}...")
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    result = run_inference_task(
        image_path=IMAGE_PATH,
        output_dir=OUTPUT_DIR,
        save_overlay=True,
        model_type=MODEL_TYPE,
        mm2_per_pixel=MM2_PER_PIXEL
    )
    
    if result[0] is None:
         defects = result[3]
         print(f"Success. Defects found: {len(defects)}")
    else:
         print(f"Failed: {result[0]}")
