import logging
import sys
import time
import os
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
from PIL import Image
import cv2
from scipy import ndimage
import torch
import torch.nn.functional as F

# Try importing openvino
try:
    import openvino as ov
    from openvino.preprocess import PrePostProcessor, ColorFormat
    OPENVINO_AVAILABLE = True
except ImportError:
    OPENVINO_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Model paths - local project folder
MODEL_DIR = Path(__file__).parent / "openvino_models"

# Default Model paths (Fallback)
DEFAULT_WHITE_MODEL = MODEL_DIR / "white_model.xml"
DEFAULT_BLACK_MODEL = MODEL_DIR / "black_model.xml"

MM2_PER_PIXEL_DEFAULT = 0.0037

# Class index → JSON key name mapping (model class IDs 1–3)
# 0 is Background
CLASS_INDEX_TO_NAME_WHITE = {
    1: "Dust",
    2: "Rundown",
    3: "Scratch", 
}

CLASS_INDEX_TO_NAME_BLACK = {
    1: "Dust",
    2: "Rundown", 
    3: "Scratch",
}

ALL_DEFECT_KEYS = ["Dust", "Rundown", "Scratch"]

class DefectPredictor:
    """Multi-backend predictor for defect detection with model switching."""
    
    _instance = None
    
    def __init__(self, image_size: int = 518) -> None:
        """Initialize predictor."""
        self.image_size = image_size
        self.backend = None
        self.compiled_model = None
        self.sync_request = None
        self.input_layer = None
        self.output_layer = None
        self.current_model_type = "white" # Default
        self.device = "CPU" # Default fallback
        
        # Check OpenVINO
        if OPENVINO_AVAILABLE:
            core = ov.Core()
            devices = core.available_devices
            logger.info(f"[Inference] OpenVINO devices: {devices}")
            
            if "GPU.0" in devices: self.device = "GPU.0"
            elif "GPU.1" in devices: self.device = "GPU.1"
            elif "GPU" in devices: self.device = "GPU"
            else: self.device = "CPU"
            
            self.core = core
        else:
            logger.warning("[Inference] OpenVINO not available. Inference will fail.")
        
        # Initial Load
        self.load_model("white")
        
    def load_model(self, model_type: str):
        """Load the specified model type (white/black)."""
        if not OPENVINO_AVAILABLE: 
            return False

        if model_type == self.current_model_type and self.compiled_model is not None:
             return True

        model_path = DEFAULT_WHITE_MODEL if model_type == "white" else DEFAULT_BLACK_MODEL
        
        if not model_path.exists():
            logger.error(f"[Inference] Model file not found: {model_path}")
            # Try to compile on the fly if .pth exists? No, keep it simple for now.
            return False

        logger.info(f"[Inference] Loading {model_type} model from {model_path} on {self.device}")

        try:
            # Enable caching
            cache_dir = MODEL_DIR / "cache"
            cache_dir.mkdir(exist_ok=True)
            self.core.set_property({"CACHE_DIR": str(cache_dir)})

            # Read Model
            model = self.core.read_model(str(model_path))
            
            # Preprocessing (Standard ImageNet)
            ppp = PrePostProcessor(model)
            ppp.input().tensor() \
                .set_element_type(ov.Type.u8) \
                .set_layout(ov.Layout("NHWC")) \
                .set_color_format(ColorFormat.RGB)
            ppp.input().preprocess() \
                .convert_element_type(ov.Type.f32) \
                .convert_layout(ov.Layout("NCHW")) \
                .mean([0.485 * 255, 0.456 * 255, 0.406 * 255]) \
                .scale([0.229 * 255, 0.224 * 255, 0.225 * 255])
            ppp.input().model().set_layout(ov.Layout("NCHW"))
            
            model = ppp.build()
            
            # Reshape if needed (Usually implicit in OV IR but good to be explicit)
            # model.reshape({model.input(0): [1, self.image_size, self.image_size, 3]})

            # Compile
            config = {"PERFORMANCE_HINT": "LATENCY"}
            self.compiled_model = self.core.compile_model(model, self.device, config)
            self.sync_request = self.compiled_model.create_infer_request()
            self.input_layer = self.compiled_model.input(0)
            self.output_layer = self.compiled_model.output(0)
            
            self.backend = "openvino"
            self.current_model_type = model_type
            logger.info(f"[Inference] {model_type} model loaded successfully.")
            return True

        except Exception as e:
            logger.error(f"[Inference] Failed to load model: {e}")
            return False

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for inference."""
        # OpenVINO PPP handles resizing/normalizing if configured, but let's resize here to be safe
        img = cv2.resize(image, (self.image_size, self.image_size), interpolation=cv2.INTER_LINEAR)
        return img
    
    def generate_report(self, image_path, pred_mask, softmax_probs, mm2_per_pixel):
        """Generate JSON report based on prediction."""
        H, W = pred_mask.shape
        total_image_pixels = H * W
        
        class_map = CLASS_INDEX_TO_NAME_WHITE if self.current_model_type == "white" else CLASS_INDEX_TO_NAME_BLACK
        
        defects_dict = {}
        grand_total_defect_pixels = 0
        
        for class_idx, class_name in class_map.items():
            binary_mask = (pred_mask == class_idx).astype(np.uint8)
            
            # Label connected components
            labelled, num_instances = ndimage.label(binary_mask)
            
            instances = []
            class_total_pixels = 0
            
            for inst_id in range(1, num_instances + 1):
                inst_mask = (labelled == inst_id)
                area_pixels = int(inst_mask.sum())
                if area_pixels == 0: continue
                
                class_total_pixels += area_pixels
                
                # Bbox
                ys, xs = np.where(inst_mask)
                x_min, x_max = int(xs.min()), int(xs.max())
                y_min, y_max = int(ys.min()), int(ys.max())
                
                # Centroid
                cy = round(float(ys.mean()), 2)
                cx = round(float(xs.mean()), 2)
                
                # Uncertainty
                uncertainty = 0.0
                if softmax_probs is not None:
                     max_probs = softmax_probs.max(axis=0)
                     uncertainty = round(float((1.0 - max_probs[inst_mask]).mean()), 4)
                
                instances.append({
                    "instance_id": len(instances) + 1,
                    "bbox": [x_min, y_min, x_max, y_max],
                    "area_pixels": area_pixels,
                    "area_mm2": round(area_pixels * mm2_per_pixel, 4),
                    "centroid": [cx, cy],
                    "uncertainty": uncertainty
                })

            grand_total_defect_pixels += class_total_pixels
            
            defects_dict[class_name] = {
                "count": len(instances),
                "total_area_pixels": class_total_pixels,
                "total_area_mm2": round(class_total_pixels * mm2_per_pixel, 4),
                "area_percentage_of_image": round(100.0 * class_total_pixels / total_image_pixels, 4),
                "area_percentage_of_all_defects": 0.0, # Filled later
                "instances": instances
            }

        # Fill relative percentages
        if grand_total_defect_pixels > 0:
            for class_name in defects_dict:
                pct = 100.0 * defects_dict[class_name]["total_area_pixels"] / grand_total_defect_pixels
                defects_dict[class_name]["area_percentage_of_all_defects"] = round(pct, 4)

        # Ensure all keys exist
        for key in ALL_DEFECT_KEYS:
            if key not in defects_dict:
                defects_dict[key] = {
                    "count": 0, "total_area_pixels": 0, "total_area_mm2": 0.0,
                    "area_percentage_of_image": 0.0, "area_percentage_of_all_defects": 0.0,
                    "instances": []
                }
        
        total_defect_count = sum(d["count"] for d in defects_dict.values())
        
        report = {
            "image": str(Path(image_path).name),
            "summary": {
                "total_defects": total_defect_count,
                "total_defect_area_pixels": grand_total_defect_pixels,
                "total_defect_area_mm2": round(grand_total_defect_pixels * mm2_per_pixel, 4),
                "defect_area_percentage": round(100.0 * grand_total_defect_pixels / total_image_pixels, 4)
            },
            "defects": defects_dict
        }
        return report

    def predict_and_save(
        self,
        image_path: str,
        output_dir: Optional[str] = None,
        save_overlay: bool = True,
        batch_folder_name: str = None, 
        model_type: str = "white",
        mm2_per_pixel: float = MM2_PER_PIXEL_DEFAULT
    ) -> Tuple[str, str, float, List[Dict]]:
        """Run inference, save report and overlay."""
        
        # Ensure correct model is loaded
        self.load_model(model_type)
        
        # Load Image
        try:
            # Use OpenCV for consistency
            img_bgr = cv2.imread(image_path)
            if img_bgr is None:
                raise ValueError(f"Failed to read image: {image_path}")
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            original_h, original_w = img_rgb.shape[:2]
        except Exception as e:
            logger.error(f"[Inference] Image load failed: {e}")
            return None, None, 0, []

        start_time = time.perf_counter()

        # Preprocess
        input_img = self.preprocess(img_rgb)
        input_tensor = np.expand_dims(input_img, 0) # NHWC handled by PPP? PPP expects NHWC U8, we gave it. 
        # Wait, in load_model:
        # ppp.input().tensor().set_layout(ov.Layout("NHWC"))
        # So we pass [1, H, W, 3] uint8.
        
        if self.backend == "openvino":
            self.sync_request.infer({self.input_layer: input_tensor})
            output = self.sync_request.get_output_tensor().data
            # Output is likely [1, C, H, W] logits
        else:
            # CPU Fallback or failure
            logger.error("No valid backend available.")
            return None, None, 0, []
        
        inference_time = (time.perf_counter() - start_time) * 1000
        
        # Process Output
        # Softmax & Argmax
        # output shape (1, C, H, W)
        try:
             # Convert to torch for easy softmax if numpy doesn't have it handy or just use scipy/numpy
             # using numpy for fewer deps in this function if possible
             pass
        except:
             pass

        # Manual Softmax on numpy
        # axis 1 is channels
        exp_logits = np.exp(output - np.max(output, axis=1, keepdims=True))
        softmax_probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        softmax_probs = softmax_probs[0] # (C, H, W)
        
        pred_mask = np.argmax(output, axis=1)[0] # (H, W)
        
        # Resize back to original
        pred_mask_resized = cv2.resize(
            pred_mask.astype(np.uint8), (original_w, original_h), interpolation=cv2.INTER_NEAREST
        )
        
        # Resize probs for uncertainty
        C = softmax_probs.shape[0]
        probs_resized = np.zeros((C, original_h, original_w), dtype=np.float32)
        for c in range(C):
            probs_resized[c] = cv2.resize(
                softmax_probs[c], (original_w, original_h), interpolation=cv2.INTER_LINEAR
            )

        # Generate Report
        report = self.generate_report(image_path, pred_mask_resized, probs_resized, mm2_per_pixel)
        
        # Save results
        overlay_path = None
        if output_dir:
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            base_name = Path(image_path).stem
            
            # Save Report
            json_path = out_path / f"{base_name}_{timestamp}_report.json"
            with open(json_path, "w") as f:
                json.dump(report, f, indent=2)
                
            # Create Overlay
            if save_overlay:
                # Simple Overlay
                # map mask to colors
                mask_rgb = np.zeros((original_h, original_w, 3), dtype=np.uint8)
                
                # Colors: 0=Black, 1=Red, 2=Green, 3=Yellow
                COLORS = {
                    0: [0, 0, 0],
                    1: [255, 0, 0],   # Dust
                    2: [0, 255, 0],   # Rundown
                    3: [255, 255, 0]  # Scratch
                }
                
                for c_idx, color in COLORS.items():
                     mask_rgb[pred_mask_resized == c_idx] = color
                
                alpha = 0.5
                overlay = cv2.addWeighted(img_bgr, 1-alpha, cv2.cvtColor(mask_rgb, cv2.COLOR_RGB2BGR), alpha, 0)
                
                overlay_path = out_path / f"{base_name}_{timestamp}_overlay.jpg"
                cv2.imwrite(str(overlay_path), overlay)

        # Return format expected by endpoints.py
        # Need to flatten the complex defects dict to a simple list for the frontend's current UI
        # Or update frontend. For now, let's strictly follow the existing interface for simple list,
        # but the JSON report on disk has everything.
        
        flat_defects = []
        for key, val in report["defects"].items():
             for inst in val["instances"]:
                  flat_defects.append({
                      "type": key,
                      "class_id": -1, # Not crucial directly
                      "pixel_count": inst["area_pixels"],
                      "area_ratio": inst["area_pixels"] / (original_h * original_w) # approx
                  })
                  
        return None, str(overlay_path) if overlay_path else None, inference_time, flat_defects


# Global predictor instance
_predictor: Optional[DefectPredictor] = None

def get_predictor() -> DefectPredictor:
    """Get or create the global predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = DefectPredictor()
    return _predictor

def run_inference_task(image_path, output_dir, save_overlay=True, model_type="white", mm2_per_pixel=0.0037):
    """
    Standalone function to run inference in a separate process.
    """
    try:
        predictor = get_predictor()
        return predictor.predict_and_save(image_path, output_dir, save_overlay, model_type=model_type, mm2_per_pixel=mm2_per_pixel)
    except Exception as e:
        logger.error(f"Error in inference process: {e}")
        return None, None, 0, []

if __name__ == "__main__":
    # Test run
    # Create dummy file if not exists
    test_img = Path("c:/MyStuff/VS/MECup/backend/inference/stitched_result.jpg")
    if test_img.exists():
         run_inference_task(str(test_img), "output_test", True)
