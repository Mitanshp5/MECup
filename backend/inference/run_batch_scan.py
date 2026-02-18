
import sys
import glob
from pathlib import Path
import logging
import time

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.inference.inference_service import run_inference_task

# Configuration
SCAN_DIR = Path(r"c:\MyStuff\VS\MECup\backend\captured_images\scan_20260212_190653")
OUTPUT_DIR = SCAN_DIR / "results"
MODEL_TYPE = "black" 
MM2_PER_PIXEL = 0.0037

if __name__ == "__main__":
    # Ensure output directory exists (cleared by previous command ideally)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all grid images
    # Pattern: grid_*.jpg
    image_pattern = str(SCAN_DIR / "grid_*.jpg")
    image_files = glob.glob(image_pattern)
    
    logger.info(f"Found {len(image_files)} images in {SCAN_DIR}")
    logger.info(f"Running batch inference with model='{MODEL_TYPE}'...")
    
    start_total = time.perf_counter()
    success_count = 0
    fail_count = 0
    
    # only run first 5 for quick verification
    # actually runs all in background so user gets full results
    
    for img_path in image_files:
        try:
            logger.info(f"Processing {Path(img_path).name}...")
            result = run_inference_task(
                image_path=img_path,
                output_dir=str(OUTPUT_DIR),
                save_overlay=True,
                model_type=MODEL_TYPE,
                mm2_per_pixel=MM2_PER_PIXEL
            )
            
            if result[0] is None:
                success_count += 1
                # Log detection count
                defects = result[3]
                if defects:
                    logger.info(f"  -> Detected {len(defects)} defects")
                else:
                    logger.info(f"  -> No defects detected")
            else:
                logger.error(f"Failed {Path(img_path).name}: {result[0]}")
                fail_count += 1
                
        except Exception as e:
            logger.error(f"Error processing {img_path}: {e}")
            fail_count += 1
            
    end_total = time.perf_counter()
    duration = end_total - start_total
    
    logger.info("-" * 30)
    logger.info(f"Batch Processing Complete.")
    logger.info(f"Total Time: {duration:.2f}s")
    logger.info(f"Successfully processed: {success_count}")
    logger.info(f"Failed: {fail_count}")
    logger.info(f"Results saved to: {OUTPUT_DIR}")
