import threading
import time
import datetime
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
from .settings import save_plc_settings, load_plc_settings
from .connection import PLCManager

# ------------- camera imports -------------
camera_manager = None
try:
    from camera.camera_manager import camera_manager
except ImportError:
    try:
        from ..camera.camera_manager import camera_manager
    except ImportError:
        pass
except Exception:
    pass

# ------------- inference imports -------------
get_predictor = None
try:
    from inference.inference_service import get_predictor
except ImportError:
    try:
        from ..inference.inference_service import get_predictor
    except ImportError:
        pass
except Exception:
    pass

# Store last inference result for frontend polling
last_inference_result = {
    "filepath": None,
    "overlay_path": None,
    "defects": [],
    "inference_time_ms": 0,
    "timestamp": None
}

# ------------- Global / Manager -------------
router = APIRouter()
manager = PLCManager()

# ------------- Models -------------

class PLCConnectRequest(BaseModel):
    ip: str
    port: int
    timeout: int = 5000 

class PLCWriteRequest(BaseModel):
    device: str
    value: int

class ServoSpeedRequest(BaseModel):
    x: int = Field(..., ge=0, le=50000, description="Speed for X axis (D2)")
    y: int = Field(..., ge=0, le=50000, description="Speed for Y axis (D0)")
    z: int = Field(..., ge=0, le=50000, description="Speed for Z axis (D4)")

class ServoEnableRequest(BaseModel):
    enable: bool

class ServoMoveRequest(BaseModel):
    command: str

# ------------- Constants -------------
MOTION_COMMANDS = {
    # Control
    "servo_on": "M0",
    # X Axis
    "x_left_17": "M100",
    "x_right_17": "M200",
    "x_home": "M300",
    # Y Axis
    "y_back_12.5": "M500",
    "y_fwd_12.5": "M600",
    # Z Axis
    "z_up_5": "M800",
    "z_down_5": "M900",
    "z_up_jog": "M8",
    "z_down_jog": "M7"
}

# ------------- Polling Logic -------------

def poll_plc_thread():
    """Background polling using the shared manager."""
    last_y2 = 0
    last_y7 = 0
    last_m101 = 1
    count = 1
    county=1
    start= 0
    while True:
        try:
            # Status check (Heartbeat)
            resp = manager.read_bit("X0", 1)
            m5_status=manager.read_bit("M5",1)  
            if m5_status[0]==1:
                # Check Y2 Trigger
                resp_y = manager.read_bit("Y2", 6)
                if resp_y and len(resp_y) > 0:
                    current_y2 = resp_y[0]
                    current_y7 = resp_y[5]
                    
                    # Rising Edge (0 -> 1)
                    if (current_y2 == 1 and last_y2 == 0) or (current_y7 == 1 and last_y7 == 0):
                        current_m101= manager.read_bit("M101",1)
                        if last_m101!=current_m101[0]:
                            county+=1
                            count=1
                            last_m101=current_m101[0]
                        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        save_dir = os.path.join(backend_dir, "captured_images")
                        os.makedirs(save_dir, exist_ok=True)
                        filepath = os.path.join(save_dir, f"grid_{county}_{count}.jpg")
                        
                        if camera_manager:
                            try:
                                if camera_manager.save_current_frame(filepath):
                                    # Run inference on captured image
                                    if get_predictor is not None:
                                        try:
                                            predictor = get_predictor()
                                            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                            result_dir = os.path.join(backend_dir, "result_images")
                                            mask_path, overlay_path, inference_time, defects = predictor.predict_and_save(
                                                filepath, result_dir, save_overlay=True
                                            )
                                            
                                            # Update global result for frontend polling
                                            global last_inference_result
                                            last_inference_result = {
                                                "filepath": filepath,
                                                "overlay_path": overlay_path,
                                                "defects": defects,
                                                "inference_time_ms": inference_time,
                                                "timestamp": datetime.datetime.now().isoformat()
                                            }
                                        except Exception:
                                            pass
                                    
                                    # Feedback M77
                                    try:
                                        time.sleep(2)
                                        manager.write_bit("M77", [1])
                                        count += 1
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                    
                    last_y2 = current_y2
                    last_y7 = current_y7
                
                
        except Exception:
            # Logging suppressed for cleanliness
            time.sleep(1)
            
        time.sleep(0.075)

# ------------- Startup Logic -------------

def start_polling():
    t = threading.Thread(target=poll_plc_thread, daemon=True)
    t.start()

# Load settings on import and start polling if configured
settings = load_plc_settings()
if settings and settings.get("ip") and settings.get("port"):
    manager.configure(settings["ip"], settings["port"])
    start_polling()


# ------------- General PLC Endpoints -------------

@router.get("/plc/status")
async def get_plc_status():
    st = manager.get_status()
    return st

@router.post("/plc/connect")
async def plc_connect(req: PLCConnectRequest):
    """Save settings and restart/configure manager."""
    try:
        # Save settings to JSON file
        save_plc_settings(req.ip, req.port)
        
        # Configure manager (forces reconnect)
        manager.configure(req.ip, req.port)
        
        # Determine status
        if manager.connect():
            return {"connected": True}
        else:
            return {"connected": False, "error": manager.last_error}
    except Exception as e:
        return {"connected": False, "error": str(e)}

@router.post("/plc/write")
async def plc_write(req: PLCWriteRequest):
    """Generic write endpoint."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    try:
        val_list = [1] if req.value == 1 else [0]
        manager.write_bit(req.device, val_list)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ------------- Control Endpoints -------------

@router.post("/plc/scan-start")
async def scan_start():
    """Start scan by setting M5 to ON."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    try:
        manager.write_bit("M5", [1])
        time.sleep(1)
        manager.write_bit("M77", [1])
        time.sleep(0.1)
        manager.write_bit("M77", [0])
        count=1
        county=1
        return {"success": True, "message": "Scan Started (M5 ON)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/grid-one")
async def grid_one():
    """Trigger Grid One by setting M4 to ON."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    try:
        manager.write_bit("M4", [1])
        return {"success": True, "message": "Grid One Triggered (M4 ON)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/cycle-reset")
async def cycle_reset():
    """Reset cycle by setting M120 to ON."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    try:
        manager.write_bit("M120", [1])
        return {"success": True, "message": "Cycle Reset (M120 ON)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/homing-start")
async def homing_start():
    """Start homing sequence by setting X6 to ON."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    try:
        manager.write_bit("X6", [1])
        return {"success": True, "message": "Homing Started (X6 ON)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/plc/control-status")
async def get_control_status():
    """Read current status of control bits M5, M4, M120, X6."""
    if not manager.connected:
        return {"error": "PLC Not Connected", "m5": None, "m4": None, "m120": None, "x6": None}
    try:
        m5 = manager.read_bit("M5", 1)
        m4 = manager.read_bit("M4", 1)
        m120 = manager.read_bit("M120", 1)
        x6 = manager.read_bit("X6", 1)
        return {
            "m5": m5[0] if m5 else None,
            "m4": m4[0] if m4 else None,
            "m120": m120[0] if m120 else None,
            "x6": x6[0] if x6 else None
        }
    except Exception as e:
        return {"error": str(e), "m5": None, "m4": None, "m120": None, "x6": None}

@router.get("/plc/latest-inference")
async def get_latest_inference():
    """Get the latest automatic inference result from PLC-triggered capture."""
    if last_inference_result["timestamp"] is None:
        return {"has_result": False}
    
    # Generate URL for overlay
    overlay_url = None
    if last_inference_result["overlay_path"]:
        from pathlib import Path
        overlay_filename = Path(last_inference_result["overlay_path"]).name
        overlay_url = f"/inference/result/{overlay_filename}"
    
    return {
        "has_result": True,
        "filepath": last_inference_result["filepath"],
        "overlay_url": overlay_url,
        "defects": last_inference_result["defects"],
        "inference_time_ms": last_inference_result["inference_time_ms"],
        "timestamp": last_inference_result["timestamp"]
    }

# ------------- Servo Endpoints (Merged) -------------

@router.post("/servo/speeds")
async def set_servo_speeds(speeds: ServoSpeedRequest) -> Dict[str, str]:
    if not manager.connected:
        raise HTTPException(status_code=503, detail="PLC Not Connected")
    try:
        manager.write_sign_dword("D2", [speeds.x])
        manager.write_sign_dword("D0", [speeds.y])
        manager.write_sign_dword("D4", [speeds.z])
        print(f"[SERVO] Speeds set: {speeds}")
        return {"status": "success", "message": "Speeds updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servo/enable")
async def enable_servo(req: ServoEnableRequest) -> Dict[str, str]:
    if not manager.connected:
        raise HTTPException(status_code=503, detail="PLC Not Connected")
    try:
        val = [1] if req.enable else [0]
        manager.write_bit("M0", val)
        return {"status": "success", "message": f"Servo {'Enabled' if req.enable else 'Disabled'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servo/move")
async def trigger_motion(req: ServoMoveRequest) -> Dict[str, str]:
    if req.command not in MOTION_COMMANDS:
        raise HTTPException(status_code=400, detail="Invalid Command")
    if not manager.connected:
        raise HTTPException(status_code=503, detail="PLC Not Connected")
    
    bit_addr = MOTION_COMMANDS[req.command]
    try:
        manager.write_bit(bit_addr, [1])
        print(f"[SERVO] Triggered {req.command}")
        time.sleep(4)
        manager.write_bit(bit_addr, [0])
        return {"status": "success", "message": f"Triggered {req.command}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
