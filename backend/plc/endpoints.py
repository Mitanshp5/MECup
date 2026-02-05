import threading
import time
import asyncio
import datetime
import os
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from .settings import save_plc_settings, load_plc_settings
from .connection import manager
from . import models as plc_models
try:
    from database import SessionLocal
except ImportError:
    from ..database import SessionLocal
from sqlalchemy.orm import Session

# Try sourcing from parent auth module
try:
    from auth.dependencies import get_current_active_user
    from auth.models import User
except ImportError:
    # Fallback for when running tests or different path context
    from ..auth.dependencies import get_current_active_user
    from ..auth.models import User

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
run_inference_task = None
try:
    from inference.inference_service import get_predictor, run_inference_task
except ImportError:
    try:
        from ..inference.inference_service import get_predictor, run_inference_task
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
    "timestamp": None,
    "scan_id": None
}

# Event log for recent events
recent_events = []
MAX_EVENTS = 50

def add_event(event: str, event_type: str = "info"):
    """Add an event to the recent events list."""
    global recent_events
    recent_events.insert(0, {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "event": event,
        "type": event_type  # success, warning, error, info
    })
    # Keep only last MAX_EVENTS
    if len(recent_events) > MAX_EVENTS:
        recent_events = recent_events[:MAX_EVENTS]

# ------------- Helper Functions -------------

def save_inference_callback(future):
    """Callback to save inference result to DB and update global state."""
    try:
        mask_path, overlay_path, inference_time, defects, filepath, scan_id = future.result()
        
        # Update global result for frontend polling
        global last_inference_result
        last_inference_result = {
            "filepath": filepath,
            "overlay_path": overlay_path,
            "defects": defects,
            "inference_time_ms": inference_time,
            "timestamp": datetime.datetime.now().isoformat(),
            "scan_id": scan_id
        }
        
        # Save result to database
        try:
            db = SessionLocal()
            
            # Create image record
            scan_image = plc_models.ScanImage(
                scan_id=scan_id,
                filename=os.path.basename(filepath),
                filepath=filepath,
                defect_count=len(defects),
                has_defects=(len(defects) > 0),
                overlay_path=overlay_path,
                inference_time_ms=inference_time
            )
            db.add(scan_image)
            
            # Update scan stats
            scan = db.query(plc_models.Scan).filter(plc_models.Scan.id == scan_id).first()
            if scan:
                scan.image_count += 1
                scan.defect_count += len(defects)
                if scan.defect_count > (scan.image_count / 10): # Simple threshold
                    scan.status = "fail"
            
            db.commit()
            db.close()
        except Exception as db_err:
            print(f"DB Error saving result: {db_err}")
            
    except Exception as e:
        print(f"Inference Task Failed: {e}")

def run_inference_wrapper(filepath, result_dir, save_overlay, scan_id):
    """Wrapper to return filepath and scan_id along with results."""
    # This must be importable by the worker process! 
    # Since we are in endpoints.py, we might need to rely on run_inference_task static import
    # But we want to return extra args.
    # It's better to modify run_inference_task or just pass args through.
    # NOTE: ProcessPoolExecutor requires functions to be picklable. 
    # Lambdas and local functions don't work reliably.
    # We will use the imported run_inference_task and handle logic elsewhere?
    # No, we need context in callback.
    
    # Let's assume run_inference_task is importable.
    from inference.inference_service import run_inference_task
    res = run_inference_task(filepath, result_dir, save_overlay)
    return (*res, filepath, scan_id)


# ------------- Global / Manager -------------
router = APIRouter()
router = APIRouter()
# manager = PLCManager() # Use imported manager

# Global executor for inference
from concurrent.futures import ProcessPoolExecutor
inference_executor = ProcessPoolExecutor(max_workers=1)

# Batch folder for current scan session
current_batch_folder = None

# ------------- Models -------------

class PLCConnectRequest(BaseModel):
    ip: str
    port: int
    timeout: int = 5000 

class PLCWriteRequest(BaseModel):
    device: str
    value: int

class ServoSpeedRequest(BaseModel):
    x: int = Field(..., ge=0, le=500000, description="Speed for X axis (D2)")
    y: int = Field(..., ge=0, le=500000, description="Speed for Y axis (D0)")
    z: int = Field(..., ge=0, le=500000, description="Speed for Z axis (D4)")

class ServoEnableRequest(BaseModel):
    enable: bool

class ServoMoveRequest(BaseModel):
    command: str

class TogglePulseRequest(BaseModel):
    mode: str

class LightControlRequest(BaseModel):
    pass

class ScanStopRequest(BaseModel):
    pass

class ErrorResetRequest(BaseModel):
    pass

# ------------- Constants -------------
MOTION_COMMANDS = {
    # Control
    "servo_on": "M0",
    # X Axis
    "x_left_17": "M10",
    "x_right_17": "M200",
    "x_home": "M1",
    # Y Axis
    "y_back_12.5": "M20",
    "y_fwd_12.5": "M600",
    # Z Axis
    "z_up_5": "M800",
    "z_down_5": "M30",
    "z_up_jog": "M8",
    "z_down_jog": "M30"
}

# ------------- Polling Logic -------------

def poll_plc_thread():
    """Background polling using the shared manager."""
    last_Y14 = 0
    last_Y15 = 0
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
                # Check y14 Trigger
                resp_y = manager.read_bit("Y14", 2)
                if resp_y and len(resp_y) > 0:
                    current_Y14 = resp_y[0]
                    current_Y15 = resp_y[1]
                    
                    # Rising Edge (0 -> 1)
                    if (current_Y14 == 1 and last_Y14 == 0) or (current_Y15 == 1 and last_Y15 == 0) or (passleft==1):
                        passleft=0
                        current_m101= manager.read_bit("M101",1)
                        if last_m101!=current_m101[0]:
                            county+=1
                            count=1
                            last_m101=current_m101[0]
                        global current_batch_folder
                        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        
                        # Use batch folder if set, otherwise create one
                        if current_batch_folder:
                            save_dir = current_batch_folder
                        else:
                            # Fallback: create new batch folder
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            save_dir = os.path.join(backend_dir, "captured_images", f"scan_{timestamp}")
                            current_batch_folder = save_dir
                        
                        os.makedirs(save_dir, exist_ok=True)
                        filepath = os.path.join(save_dir, f"grid_{county}_{count}.jpg")
                        
                        if camera_manager:
                            try:
                                if camera_manager.save_current_frame(filepath):
                                    # Run inference on captured image
                                    if get_predictor is not None:
                                        try:
                                            predictor = get_predictor()
                                            # Store results in 'results' subfolder of current batch
                                            # result_dir = os.path.join(save_dir, "results")
                                            # os.makedirs(result_dir, exist_ok=True)
                                            # mask_path, overlay_path, inference_time, defects = predictor.predict_and_save(
                                            #     filepath, result_dir, save_overlay=True
                                            # )
                                            
                                            # Use executor to run in separate process (Non-blocking)
                                            result_dir = os.path.join(save_dir, "results")
                                            os.makedirs(result_dir, exist_ok=True)
                                            
                                            scan_id = os.path.basename(current_batch_folder)
                                            
                                            future = inference_executor.submit(
                                                 run_inference_wrapper, # Use wrapper to pass context
                                                 filepath, 
                                                 result_dir, 
                                                 True, # save_overlay
                                                 scan_id
                                            )
                                            
                                            future.add_done_callback(save_inference_callback)
                                            
                                        except Exception as ie:
                                            print(f"Inference Submission Error: {ie}")
                                            pass
                                    
                                    # Feedback M77 - Now Immediate!
                                    try:
                                        time.sleep(0.05) # Small buffer
                                        manager.write_bit("M77", [1])
                                        count += 1
                                        if manager.read_bit("X0",1)[0]==1:
                                            passleft=1
                                        # if (manager.read_bit("X0",1)[0]==1 and manager.read_bit("Y14",1)[0]==0):
                                        #     time.sleep(1)
                                        #     manager.write_bit("M77",[1])
                                    except Exception:
                                        print("Failed to write M77 feedback")
                                        manager.write_bit("M77", [1])
                            except Exception:
                                pass
                    
                    last_Y14 = current_Y14
                    last_Y15 = current_Y15
                
                
        except Exception:
            # Logging suppressed for cleanliness
            time.sleep(1)
            
        time.sleep(0.075)

# ------------- Startup Logic -------------

def start_polling():
    t = threading.Thread(target=poll_plc_thread, daemon=True)
    t.start()

def init_plc_system():
    """Initialize PLC connection, start polling thread, and warmup inference."""
    # Warmup Inference
    try:
        print("[PLC INIT] Warming up inference worker...", flush=True)
        # Submit a dummy task to force worker spawn and model load
        # We use a non-existent file, the worker should handle it gracefully or we just want the import side-effect
        # Ideally we pass a special flag or a tiny dummy image.
        # But run_inference_wrapper expects file.
        # Let's just rely on the fact that submitting ANY task starts the process.
        # We can't really "warmup" the TensorRT engine without running prediction.
        # So let's try to run a dummy prediction if possible, or just let the first scan be the warmup?
        # The user specifically complained about first grid.
        # So we SHOULD run a dummy prediction.
        
        # We need a dummy image path.
        # Let's create a dummy black image.
        dummy_path = os.path.join(os.path.dirname(__file__), "warmup.jpg")
        if not os.path.exists(dummy_path):
             import numpy as np
             from PIL import Image
             img = Image.fromarray(np.zeros((518, 518, 3), dtype=np.uint8))
             img.save(dummy_path)
             
        # Submit warmup task
        future = inference_executor.submit(
             run_inference_wrapper, 
             dummy_path, 
             os.path.join(os.path.dirname(__file__), "warmup_results"), 
             False, # save_overlay
             "warmup_scan"
        )
        # We don't wait for result here to not block startup, but it will run in background.
        print("[PLC INIT] Inference warmup task submitted.", flush=True)
        
    except Exception as e:
        print(f"[PLC INIT] Warmup failed: {e}")

    settings = load_plc_settings()
    if settings and settings.get("ip") and settings.get("port"):
        print(f"[PLC INIT] Loading settings: {settings['ip']}:{settings['port']}", flush=True)
        manager.configure(settings["ip"], settings["port"])
        start_polling()
    else:
        print("[PLC INIT] No settings found. Waiting for manual connect.", flush=True)




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
            add_event(f"PLC connected ({req.ip}:{req.port})", "success")
            return {"connected": True}
        else:
            add_event(f"PLC connection failed: {manager.last_error}", "error")
            return {"connected": False, "error": manager.last_error}
    except Exception as e:
        add_event(f"PLC connection error: {str(e)}", "error")
        return {"connected": False, "error": str(e)}

@router.get("/events")
async def get_events():
    """Get recent system events."""
    return {"events": recent_events[:20]}

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

@router.post("/plc/lights")
async def control_lights(req: LightControlRequest):
    """Control M104 lights (Toggle)."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    try:
        # Read current M104
        current = manager.read_bit("M104", 1)
        current_val = current[0] if current else 0
        
        # Toggle
        new_val = 1 if current_val == 0 else 0
        
        manager.write_bit("M104", [new_val])
        return {"success": True, "state": bool(new_val)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/scan-stop")
async def scan_stop(req: ScanStopRequest):
    """Stop scan by setting M5 to OFF."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    try:
        manager.write_bit("M5", [0])
        add_event("Scan stopped", "info")
        return {"success": True, "message": "Scan Stopped (M5 OFF)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/error-reset")
async def error_reset(req: ErrorResetRequest):
    """Pulse M15 to reset errors."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    try:
        # Pulse M15: ON then OFF
        manager.write_bit("M15", [1])
        await asyncio.sleep(0.2)
        manager.write_bit("M15", [0])
        add_event("Error reset triggered", "info")
        return {"success": True, "message": "Error Reset (M15 Pulsed)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/toggle-pulse")
async def toggle_pulse(req: TogglePulseRequest):
    """Pulse M104 (White) or M103 (Black) for 0.2s."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    
    try:
        bit = "M103" if req.mode.lower() == "white" else "M104" if req.mode.lower() == "black" else None
        bit2= "M104" if req.mode.lower() == "white" else "M103" if req.mode.lower() == "black" else None
        if not bit:
            return {"success": False, "error": "Invalid Mode (use 'white' or 'black')"}

        # Pulse ON
        manager.write_bit(bit, [1])
        # await asyncio.sleep(0.2)
        # # Pulse OFF
        # manager.write_bit(bit, [0])
        manager.write_bit(bit2, [0])
        
        add_event(f"Pulse sent: {req.mode} ({bit})", "info")
        return {"success": True, "message": f"Pulsed {bit}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ------------- Control Endpoints -------------

@router.post("/plc/scan-start")
async def scan_start(username: str = "operator"):
    """Start scan by setting M5 to ON and creating a new batch folder."""
    global current_batch_folder, current_scan_user
    # if not manager.connected:
    #     return {"success": False, "error": "PLC Not Connected"}
    try:
        current_scan_user = username

        
        # Create new batch folder with timestamp if not already set
        if not current_batch_folder:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            current_batch_folder = os.path.join(backend_dir, "captured_images", f"scan_{timestamp}")
            os.makedirs(current_batch_folder, exist_ok=True)
            
            # Create DB Record for Scan
            try:
                db = SessionLocal()
                new_scan = plc_models.Scan(
                    id=f"scan_{timestamp}",
                    start_time=datetime.datetime.now(),
                    scanned_by=current_scan_user,
                    batch_folder=current_batch_folder,
                    status="pass"
                )
                db.add(new_scan)
                db.commit()
                db.close()
            except Exception as db_err:
                print(f"Failed to create DB record for scan: {db_err}")

            # Save Scan Metadata having scanned_by (Legacy JSON support)
            try:
                import json
                meta_file = os.path.join(current_batch_folder, "scan_info.json")
                with open(meta_file, 'w') as f:
                    json.dump({
                        "scanned_by": current_scan_user,
                        "start_time": timestamp,
                        "role": "operator"
                    }, f, indent=2)
            except Exception as ex:
                print(f"Failed to save scan info: {ex}")
        await asyncio.sleep(0.1)
        manager.write_bit("M5", [1])
        await asyncio.sleep(0.1)
        # manager.write_bit("Y14", [1])
        manager.write_bit("M77", [1])
        await asyncio.sleep(0.1)
        manager.write_bit("M77", [0])
        add_event("Scan started", "success")
        return {"success": True, "message": "Scan Started (M5 ON)", "batch_folder": current_batch_folder}
    except Exception as e:
        import traceback
        print(f"SCAN START ERROR: {e}", flush=True)
        try:
            with open("C:/MyStuff/VS/MECup/backend/error_log.txt", "w") as log:
                traceback.print_exc(file=log)
        except:
            print("Failed to write to error log file", flush=True)
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@router.post("/plc/grid-one")
async def grid_one():
    """Trigger Grid One by setting M4 to ON."""
    # if not manager.connected:
    #     return {"success": False, "error": "PLC Not Connected"}
    try:
        time.sleep(0.1)
        manager.write_bit("M4", [1])
        return {"success": True, "message": "Grid One Triggered (M4 ON)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/cycle-reset")
async def cycle_reset():
    """Reset cycle by setting M120 to ON and clearing batch folder."""
    global current_batch_folder
    # if not manager.connected:
    #     return {"success": False, "error": "PLC Not Connected"}
    try:
        manager.write_bit("M120", [1])
        # Clear batch folder so new scan creates a new folder
        current_batch_folder = None
        add_event("Cycle reset completed", "info")
        return {"success": True, "message": "Cycle Reset (M120 ON) - Batch cleared"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/homing-start")
async def homing_start():
    """Start homing sequence by setting X6 to ON."""
    # if not manager.connected:
    #     return {"success": False, "error": "PLC Not Connected"}
    try:
        manager.write_bit("M1", [1])
        add_event("Homing sequence started", "info")
        return {"success": True, "message": "Homing Started (M4 ON)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/plc/control-status")
async def get_control_status():
    """Read current status of control bits M5, M4, M120, M1, M0, M190, Y0."""
    if not manager.connected:
        return {"error": "PLC Not Connected", "m5": None, "m4": None, "m120": None, "m1": None, "m0": None, "M190": None, "y0": None}
    try:
        # Optimize: Read M0-M120 in one block (121 bits)
        # This reduces 5 separate calls to 1 call.
        # Indices: M0=0, M1=1, M4=4, M5=5, M190=99, M120=120
        m_block = manager.read_bit("M0", 121)
        
        # Read Y0 separately
        y0 = manager.read_bit("Y0", 1)
        
        # Read M190 separately (Servo Status)
        m190 = manager.read_bit("M190", 1)
        
        m0_val = m_block[0] if m_block and len(m_block) > 0 else None
        m1_val = m_block[1] if m_block and len(m_block) > 1 else None
        m4_val = m_block[4] if m_block and len(m_block) > 4 else None
        m5_val = m_block[5] if m_block and len(m_block) > 5 else None
        # M190_val = m_block[99] # This was M99, not M190!
        m120_val = m_block[120] if m_block and len(m_block) > 120 else None
        
        return {
            "m5": m5_val,
            "m4": m4_val,
            "m120": m120_val,
            "m1": m1_val,
            "m0": m0_val,
            "m190": m190[0] if m190 else None, # Changed key to lowercase m190
            "y0": y0[0] if y0 else None
        }
    except Exception as e:
        return {"error": str(e), "m5": None, "m4": None, "m120": None, "m1": None, "m0": None, "M190": None, "y0": None}

@router.get("/plc/heartbeat")
async def get_heartbeat():
    """Get PLC heartbeat status for system health monitoring."""
    if not manager.connected:
        return {
            "connected": False,
            "y1": None,
            "error": "PLC Not Connected"
        }
    try:
        # Read M104 for LED lights status
        y1_status = manager.read_bit("M104", 1)
        return {
            "connected": True,
            "y1": y1_status[0] if y1_status else None,
            "error": None
        }
    except Exception as e:
        return {
            "connected": False,
            "y1": None,
            "error": str(e)
        }

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
        if last_inference_result.get("scan_id"):
             overlay_url = f"/scans/{last_inference_result['scan_id']}/results/{overlay_filename}"
        else:
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

@router.get("/servo/speeds")
async def get_servo_speeds():
    """Read current servo speeds from PLC registers D0 (Y), D2 (X), D4 (Z)."""
    if not manager.connected:
        return {"connected": False, "x": 0, "y": 0, "z": 0}
    try:
        y_speed = manager.read_sign_dword("D0", 1)
        x_speed = manager.read_sign_dword("D2", 1)
        z_speed = manager.read_sign_dword("D4", 1)
        return {
            "connected": True,
            "x": x_speed[0] if x_speed else 0,
            "y": y_speed[0] if y_speed else 0,
            "z": z_speed[0] if z_speed else 0
        }
    except Exception as e:
        return {"connected": False, "x": 0, "y": 0, "z": 0, "error": str(e)}

@router.post("/servo/enable")
async def enable_servo(req: ServoEnableRequest) -> Dict[str, Any]:
    if not manager.connected:
        raise HTTPException(status_code=503, detail="PLC Not Connected")
    try:
        # Read current status of M190
        current = manager.read_bit("M190", 1)
        current_val = current[0] if current else 0
        
        # Toggle
        new_val = 1 if current_val == 0 else 0
        
        manager.write_bit("M190", [new_val])
        return {"status": "success", "message": f"Servo {'Enabled' if new_val else 'Disabled'}", "enabled": bool(new_val)}
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
        await asyncio.sleep(1)
        manager.write_bit(bit_addr, [0])
        return {"status": "success", "message": f"Triggered {req.command}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------- Scan History Endpoints -------------

@router.get("/scans/list")
async def list_scans():
    """List all past scans from Database."""
    try:
        db = SessionLocal()
        # Get latest 50 scans
        scans_db = db.query(plc_models.Scan).order_by(plc_models.Scan.start_time.desc()).limit(50).all()
        
        scans = []
        for s in scans_db:
             scans.append({
                "id": s.id,
                "folder_path": s.batch_folder,
                "date": s.start_time.strftime("%Y-%m-%d") if s.start_time else "Unknown",
                "time": s.start_time.strftime("%H:%M:%S") if s.start_time else "Unknown",
                "image_count": s.image_count,
                "defect_count": s.defect_count,
                "status": s.status,
                "scanned_by": s.scanned_by
            })
        db.close()
        return {"scans": scans}
    except Exception as e:
        return {"scans": [], "error": str(e)}

@router.get("/scans/{scan_id}")
async def get_scan_details(scan_id: str):
    """Get detailed information about a specific scan from DB."""
    try:
        db = SessionLocal()
        scan = db.query(plc_models.Scan).filter(plc_models.Scan.id == scan_id).first()
        if not scan:
             db.close()
             raise HTTPException(status_code=404, detail="Scan not found")
        
        # Get images
        images_db = db.query(plc_models.ScanImage).filter(plc_models.ScanImage.scan_id == scan_id).all()
        
        images = []
        defects = []
        defect_types = {}
        total_defect_count = scan.defect_count
        
        for img in images_db:
            images.append(img.filename)
            
            if img.has_defects:
                defects.append({
                    "image": img.filename,
                    "overlay": os.path.basename(img.overlay_path) if img.overlay_path else None,
                    "overlay_url": f"/scans/{scan_id}/results/{os.path.basename(img.overlay_path)}" if img.overlay_path else None,
                    "defect_count": img.defect_count,
                    "defect_details": [] # We didn't store details in DB yet, but that's fine for now
                })
        
        images.sort()
        db.close()
        
        return {
            "id": scan.id,
            "date": scan.start_time.strftime("%Y-%m-%d") if scan.start_time else "Unknown",
            "time": scan.start_time.strftime("%H:%M:%S") if scan.start_time else "Unknown",
            "folder_path": scan.batch_folder,
            "image_count": scan.image_count,
            "images": images,
            "total_defects": total_defect_count,
            "defect_types": defect_types, 
            "defects": defects,
            "status": scan.status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/scans/{scan_id}")
async def delete_scan(scan_id: str):
    """Delete a scan record and its associated files."""
    try:
        db = SessionLocal()
        scan = db.query(plc_models.Scan).filter(plc_models.Scan.id == scan_id).first()
        
        if not scan:
            db.close()
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # 1. Delete Folder force
        if scan.batch_folder and os.path.exists(scan.batch_folder):
            try:
                import shutil
                shutil.rmtree(scan.batch_folder)
            except Exception as fe:
                print(f"Failed to delete folder {scan.batch_folder}: {fe}")
        
        # 2. Delete from DB (Cascade should handle images)
        db.delete(scan)
        db.commit()
        db.close()
        
        return {"success": True, "message": f"Scan {scan_id} deleted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import FileResponse

@router.get("/scans/{scan_id}/image/{filename}")
async def get_scan_image(scan_id: str, filename: str):
    """Get a specific image from a scan."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(backend_dir, "captured_images", scan_id, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(file_path, media_type="image/jpeg")

@router.get("/scans/{scan_id}/results/{filename}")
async def get_scan_result(scan_id: str, filename: str):
    """Get a result image from a scan."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(backend_dir, "captured_images", scan_id, "results", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Result image not found")
    
    media_type = "image/png" if filename.endswith(".png") else "image/jpeg"
    return FileResponse(file_path, media_type=media_type)