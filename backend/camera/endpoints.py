from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import time
import asyncio
from .camera_manager import camera_manager
from .settings import load_camera_settings, save_camera_settings

router = APIRouter()

class CameraSettings(BaseModel):
    exposure: float
    gain: float
    auto_exposure: bool = False

@router.post("/camera/connect")
async def connect_camera():
    devices = camera_manager.enum_devices()
    if not devices:
        return {"success": False, "message": "No devices found"}
    
    # Try to open the first device
    if camera_manager.open_device(0):
        # Apply saved settings
        settings = load_camera_settings()
        camera_manager.set_exposure_mode(settings['auto_exposure'])
        if not settings['auto_exposure']:
            camera_manager.set_exposure(settings['exposure'])
        camera_manager.set_gain(settings['gain'])
        
        # Start grabbing
        if camera_manager.start_grabbing():
            return {"success": True, "message": "Camera connected and streaming"}
    
    return {"success": False, "message": "Failed to open device or start grabbing"}

@router.post("/camera/disconnect")
async def disconnect_camera():
    camera_manager.close_device()
    return {"success": True, "message": "Camera disconnected"}

@router.get("/camera/status")
async def get_status():
    return {
        "is_open": camera_manager.is_open,
        "is_grabbing": camera_manager.is_grabbing
    }

@router.get("/camera/settings")
async def get_settings():
    if camera_manager.is_open:
        # Get live values
        return {
            "exposure": camera_manager.get_exposure(),
            "gain": camera_manager.get_gain(),
            "auto_exposure": camera_manager.get_exposure_mode_status()
        }
    else:
        # Return saved values
        return load_camera_settings()

@router.post("/camera/settings")
async def update_settings(settings: CameraSettings):
    # Save to file
    save_camera_settings(settings.exposure, settings.gain, settings.auto_exposure)
    
    # Apply if camera is open
    if camera_manager.is_open:
        camera_manager.set_exposure_mode(settings.auto_exposure)
        if not settings.auto_exposure:
             camera_manager.set_exposure(settings.exposure)
        camera_manager.set_gain(settings.gain)
        return {"success": True, "message": "Settings applied and saved"}
    
    return {"success": True, "message": "Settings saved (camera not connected)"}

def get_image_stream():
    """Generator for MJPEG stream."""
    while True:
        frame_bytes = camera_manager.get_latest_frame_jpeg()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            # If no frame, yield a tiny delay to prevent busy loop
            pass
        time.sleep(0.033) # ~30 FPS limit check

@router.get("/camera/stream")
async def stream():
    if not camera_manager.is_grabbing:
        # Try to auto-connect if not grabbing
        # Check if connected but just not grabbing?
         pass # Endpoint logic should ideally handle this or rely on explicit connect
    
    return StreamingResponse(get_image_stream(), media_type="multipart/x-mixed-replace; boundary=frame")
