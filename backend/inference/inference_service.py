"""OpenVINO inference service for defect detection.

Adapted from dinoxdecoder inference_openvino_optimized.py for MECup integration.
"""

import logging
import time
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
import openvino as ov
from openvino.preprocess import PrePostProcessor, ColorFormat
from PIL import Image

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Defect class mapping
CLASS_NAMES = {
    0: "Background",
    1: "Dust",
    2: "RunDown", 
    3: "Scratch"
}

CLASS_COLORS = {
    0: (0, 0, 0),       # Background - Black
    1: (255, 0, 0),     # Dust - Red
    2: (0, 255, 0),     # RunDown - Green
    3: (255, 255, 0)    # Scratch - Yellow
}


def mask_to_rgb(mask: np.ndarray) -> np.ndarray:
    """Convert class mask to RGB image."""
    h, w = mask.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for class_id, color in CLASS_COLORS.items():
        rgb[mask == class_id] = color
    return rgb


class DefectPredictor:
    """OpenVINO predictor for defect detection."""
    
    _instance = None
    
    def __init__(
        self,
        model_path: str = None,
        device: str = "GPU",
        image_size: int = 518,
        enable_cache: bool = True
    ) -> None:
        """Initialize predictor.
        
        Args:
            model_path: Path to OpenVINO model XML file.
            device: Target device (GPU, CPU, AUTO).
            image_size: Input image size for model.
            enable_cache: Enable model caching for faster startup.
        """
        if model_path is None:
            # Default to model in same directory
            model_path = str(Path(__file__).parent / "openvino_model" / "model.xml")
        
        self.image_size = image_size
        self.core = ov.Core()
        
        # Enable model caching
        if enable_cache:
            cache_dir = Path(model_path).parent / "cache"
            cache_dir.mkdir(exist_ok=True)
            self.core.set_property({"CACHE_DIR": str(cache_dir)})
            # Cache enabled silently
        
        devices = self.core.available_devices
        # Device detection done silently
        
        if device == "GPU" and "GPU" not in devices:
            logger.warning("GPU not available, using CPU")
            device = "CPU"
        
        self.device = device
        
        # Load and optimize model
        # Load model silently
        model = self.core.read_model(model_path)
        
        # Add preprocessing to model
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
        model.reshape({model.input(0): [1, image_size, image_size, 3]})
        
        # Compile with optimizations
        config = {"PERFORMANCE_HINT": "LATENCY"}
        # Compile silently
        self.compiled_model = self.core.compile_model(model, device, config)
        
        self.sync_request = self.compiled_model.create_infer_request()
        self.input_layer = self.compiled_model.input(0)
        self.output_layer = self.compiled_model.output(0)
        
        print(f"[Inference] Model ready on {device}")
        
        # Warmup
        self._warmup()
    
    @classmethod
    def get_instance(cls) -> "DefectPredictor":
        """Get singleton instance of predictor."""
        if cls._instance is None:
            cls._instance = DefectPredictor()
        return cls._instance
    
    def _warmup(self, iterations: int = 3):
        """Warmup the model."""
        # Warmup silently
        dummy = np.zeros((1, self.image_size, self.image_size, 3), dtype=np.uint8)
        for _ in range(iterations):
            self.sync_request.infer({self.input_layer: dummy})
        # Warmup complete
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for inference."""
        img = Image.fromarray(image).resize(
            (self.image_size, self.image_size),
            Image.BILINEAR
        )
        return np.expand_dims(np.array(img, dtype=np.uint8), 0)
    
    def predict(self, image_path: str) -> Tuple[np.ndarray, float, List[Dict]]:
        """Run inference on an image.
        
        Args:
            image_path: Path to input image.
            
        Returns:
            Tuple of (prediction mask, inference time ms, list of defects)
        """
        original = Image.open(image_path).convert('RGB')
        original_size = original.size[::-1]  # (height, width)
        
        input_tensor = self.preprocess(np.array(original))
        
        start = time.perf_counter()
        self.sync_request.infer({self.input_layer: input_tensor})
        inference_time = (time.perf_counter() - start) * 1000
        
        output = self.sync_request.get_output_tensor().data
        pred_mask = np.argmax(output[0], axis=0).astype(np.uint8)
        
        # Resize to original size
        pred_mask = np.array(
            Image.fromarray(pred_mask).resize(
                (original_size[1], original_size[0]), Image.NEAREST
            )
        )
        
        # Extract defects from mask
        defects = self._extract_defects(pred_mask)
        
        return pred_mask, inference_time, defects
    
    def _extract_defects(self, mask: np.ndarray) -> List[Dict]:
        """Extract defect information from prediction mask."""
        defects = []
        
        for class_id in [1, 2, 3]:  # Skip background
            class_mask = (mask == class_id)
            pixel_count = np.sum(class_mask)
            
            if pixel_count > 0:
                # Calculate severity based on area
                total_pixels = mask.size
                area_ratio = pixel_count / total_pixels
                
                if area_ratio > 0.05:
                    severity = "high"
                elif area_ratio > 0.01:
                    severity = "medium"
                else:
                    severity = "low"
                
                defects.append({
                    "type": CLASS_NAMES[class_id],
                    "class_id": class_id,
                    "pixel_count": int(pixel_count),
                    "area_ratio": float(area_ratio),
                    "severity": severity
                })
        
        return defects
    
    def predict_and_save(
        self,
        image_path: str,
        output_dir: str,
        save_overlay: bool = True,
        alpha: float = 0.5
    ) -> Tuple[str, str, float, List[Dict]]:
        """Run inference and save result images.
        
        Args:
            image_path: Path to input image.
            output_dir: Directory to save results.
            save_overlay: Whether to save overlay image.
            alpha: Overlay transparency.
            
        Returns:
            Tuple of (mask path, overlay path, inference time, defects)
        """
        original = Image.open(image_path).convert('RGB')
        original_np = np.array(original)
        
        pred_mask, inference_time, defects = self.predict(image_path)
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base_name = Path(image_path).stem
        
        # Save mask
        mask_rgb = mask_to_rgb(pred_mask)
        mask_path = output_dir / f"{base_name}_{timestamp}_mask.png"
        Image.fromarray(mask_rgb).save(mask_path)
        
        overlay_path = None
        if save_overlay:
            overlay = (original_np * (1 - alpha) + mask_rgb * alpha).astype(np.uint8)
            overlay_path = output_dir / f"{base_name}_{timestamp}_overlay.png"
            Image.fromarray(overlay).save(overlay_path)
        
        return str(mask_path), str(overlay_path) if overlay_path else None, inference_time, defects


# Global predictor instance (lazy initialized)
_predictor: Optional[DefectPredictor] = None


def get_predictor() -> DefectPredictor:
    """Get or create the global predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = DefectPredictor()
    return _predictor
