"""Inference API endpoints."""

import os
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# Result images directory
RESULT_IMAGES_DIR = Path(__file__).parent.parent / "result_images"
RESULT_IMAGES_DIR.mkdir(exist_ok=True)

# Captured images directory (from camera)
CAPTURED_IMAGES_DIR = Path(__file__).parent.parent / "captured_images"


class DefectInfo(BaseModel):
    type: str
    class_id: int
    pixel_count: int
    area_ratio: float
    severity: str


class InferenceResult(BaseModel):
    success: bool
    inference_time_ms: float
    defects: List[DefectInfo]
    mask_url: Optional[str]
    overlay_url: Optional[str]
    message: Optional[str] = None


@router.post("/inference/run", response_model=InferenceResult)
async def run_inference():
    """Capture current frame and run defect detection inference."""
    try:
        # Import here to avoid circular imports and lazy loading
        from camera.camera_manager import camera_manager
        from .inference_service import get_predictor
        
        # Check if camera is running
        if not camera_manager.is_grabbing:
            return InferenceResult(
                success=False,
                inference_time_ms=0,
                defects=[],
                mask_url=None,
                overlay_url=None,
                message="Camera not connected or not grabbing"
            )
        
        # Capture current frame
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        capture_path = CAPTURED_IMAGES_DIR / f"capture_{timestamp}.jpg"
        CAPTURED_IMAGES_DIR.mkdir(exist_ok=True)
        
        if not camera_manager.save_current_frame(str(capture_path)):
            return InferenceResult(
                success=False,
                inference_time_ms=0,
                defects=[],
                mask_url=None,
                overlay_url=None,
                message="Failed to capture frame"
            )
        
        # Run inference
        predictor = get_predictor()
        mask_path, overlay_path, inference_time, defects = predictor.predict_and_save(
            str(capture_path),
            str(RESULT_IMAGES_DIR),
            save_overlay=True
        )
        
        # Generate URLs for frontend
        mask_filename = Path(mask_path).name
        overlay_filename = Path(overlay_path).name if overlay_path else None
        
        return InferenceResult(
            success=True,
            inference_time_ms=round(inference_time, 2),
            defects=[DefectInfo(**d) for d in defects],
            mask_url=f"/inference/result/{mask_filename}",
            overlay_url=f"/inference/result/{overlay_filename}" if overlay_filename else None,
            message=f"Inference completed in {inference_time:.2f}ms"
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return InferenceResult(
            success=False,
            inference_time_ms=0,
            defects=[],
            mask_url=None,
            overlay_url=None,
            message=f"Error: {str(e)}"
        )


@router.get("/inference/result/{filename}")
async def get_result_image(filename: str):
    """Serve result images (masks and overlays)."""
    file_path = RESULT_IMAGES_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(str(file_path), media_type="image/png")


@router.get("/inference/results")
async def list_results():
    """List all result images."""
    results = []
    
    if RESULT_IMAGES_DIR.exists():
        for f in sorted(RESULT_IMAGES_DIR.glob("*.png"), reverse=True)[:20]:
            results.append({
                "filename": f.name,
                "url": f"/inference/result/{f.name}",
                "created": f.stat().st_mtime
            })
    
    return {"results": results}


@router.delete("/inference/results")
async def clear_results():
    """Clear all result images."""
    count = 0
    if RESULT_IMAGES_DIR.exists():
        for f in RESULT_IMAGES_DIR.glob("*.png"):
            f.unlink()
            count += 1
    
    return {"success": True, "deleted": count}


# Store last mock inference result for frontend polling
last_mock_result = {
    "overlay_url": None,
    "defects": [],
    "inference_time_ms": 0,
    "timestamp": None,
    "source_image": None
}


@router.post("/inference/mock-run")
async def run_mock_inference():
    """Pick a random image from captured_images and run inference on it."""
    import random
    import datetime
    
    try:
        from .inference_service import get_predictor
        
        # Get list of images from captured_images
        if not CAPTURED_IMAGES_DIR.exists():
            return {"success": False, "message": "No captured_images folder found"}
        
        images = list(CAPTURED_IMAGES_DIR.glob("*.jpg")) + list(CAPTURED_IMAGES_DIR.glob("*.png"))
        
        if not images:
            return {"success": False, "message": "No images in captured_images folder"}
        
        # Pick a random image
        selected_image = random.choice(images)
        
        # Run inference
        predictor = get_predictor()
        mask_path, overlay_path, inference_time, defects = predictor.predict_and_save(
            str(selected_image),
            str(RESULT_IMAGES_DIR),
            save_overlay=True
        )
        
        # Generate URLs for frontend
        overlay_filename = Path(overlay_path).name if overlay_path else None
        overlay_url = f"/inference/result/{overlay_filename}" if overlay_filename else None
        
        # Update global mock result
        global last_mock_result
        last_mock_result = {
            "overlay_url": overlay_url,
            "defects": defects,
            "inference_time_ms": round(inference_time, 2),
            "timestamp": datetime.datetime.now().isoformat(),
            "source_image": selected_image.name
        }
        
        return {
            "success": True,
            "inference_time_ms": round(inference_time, 2),
            "defects": defects,
            "overlay_url": overlay_url,
            "source_image": selected_image.name
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e)}


@router.get("/inference/mock-latest")
async def get_mock_latest():
    """Get the latest mock inference result."""
    if last_mock_result["timestamp"] is None:
        return {"has_result": False}
    
    return {
        "has_result": True,
        "overlay_url": last_mock_result["overlay_url"],
        "defects": last_mock_result["defects"],
        "inference_time_ms": last_mock_result["inference_time_ms"],
        "timestamp": last_mock_result["timestamp"],
        "source_image": last_mock_result["source_image"]
    }

