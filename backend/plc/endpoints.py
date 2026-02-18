import threading
import time
import asyncio
import datetime
import os
import csv
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from .settings import save_plc_settings, load_plc_settings
from .connection import manager
from .scan_manager import scan_session
from . import models as plc_models
try:
    from database import SessionLocal
except ImportError:
    from ..database import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import func
import math

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
    logging.warning("Camera manager import failed")

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
    logging.warning("Inference service import failed")

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

# Monitoring Configuration
MONITORED_REGISTERS = ["D21", "D25"]
MONITOR_CSV_NAME = "register_monitor.csv"

# Critical Error Flag
critical_error_active = False

# Global Settings
current_mm2_per_pixel = 0.0037


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


# Global storage for axis monitoring
axis_monitoring_data = {
    "x": {"load": 0, "torque": 0, "peak": 0, "current": 0, "health": 0},
    "y": {"load": 0, "torque": 0, "peak": 0, "current": 0, "health": 0},
    "z": {"load": 0, "torque": 0, "peak": 0, "current": 0, "health": 0}
}
# In-memory history (last 60s @ 2s interval)
servo_history = []
last_history_update = 0

# Daily Stats Cache
servo_daily_stats = {}
last_stats_save_time = 0

# ------------- Helper Functions -------------

def init_daily_stats():
    """Load daily stats from DB or initialize empty structure."""
    global servo_daily_stats
    
    # Structure: axis -> metric -> {min, max, min_time, max_time}
    # Initialize empty first
    stats = {}
    for axis in ['x', 'y', 'z']:
        stats[axis] = {}
        for metric in ['current', 'torque', 'peak', 'load', 'health']:
            stats[axis][metric] = {
                "min_val": None, "min_time": None,
                "max_val": None, "max_time": None
            }
            
    # Load from DB
    db = SessionLocal()
    try:
        records = db.query(plc_models.ServoDailyStat).all()
        for r in records:
            if r.axis in stats and r.metric in stats[r.axis]:
                stats[r.axis][r.metric] = {
                    "min_val": r.min_val,
                    "min_time": r.min_time.isoformat() if r.min_time else None,
                    "max_val": r.max_val,
                    "max_time": r.max_time.isoformat() if r.max_time else None
                }
    except Exception as e:
        logging.error(f"Failed to load daily stats: {e}")
    finally:
        db.close()
        
    servo_daily_stats = stats

def save_daily_stats():
    """Save current daily stats to DB."""
    if not servo_daily_stats: return
    
    db = SessionLocal()
    try:
        for axis, metrics in servo_daily_stats.items():
            for metric, values in metrics.items():
                # Check if record exists
                record = db.query(plc_models.ServoDailyStat).filter_by(axis=axis, metric=metric).first()
                if not record:
                    record = plc_models.ServoDailyStat(axis=axis, metric=metric)
                    db.add(record)
                
                # Update values
                record.min_val = values["min_val"]
                record.min_time = datetime.datetime.fromisoformat(values["min_time"]) if values["min_time"] else None
                record.max_val = values["max_val"]
                record.max_time = datetime.datetime.fromisoformat(values["max_time"]) if values["max_time"] else None
                record.timestamp = datetime.datetime.utcnow()
                
        db.commit()
    except Exception as e:
        logging.error(f"Failed to save daily stats: {e}")
    finally:
        db.close()



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
        db = SessionLocal()
        try:
            # Check if scan record exists, create if not (lazy creation)
            scan = db.query(plc_models.Scan).filter(plc_models.Scan.id == scan_id).first()
            if not scan:
                # Create scan record on first image capture
                batch_folder = scan_session.get_current_folder()
                scanned_by = scan_session.current_scan_user
                scan = plc_models.Scan(
                    id=scan_id,
                    start_time=datetime.datetime.now(),
                    scanned_by=scanned_by,
                    batch_folder=batch_folder,
                    status="pass"
                )
                db.add(scan)
                db.flush()  # Ensure scan is created before adding images
            
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
            scan.image_count += 1
            scan.defect_count += len(defects)
            if scan.defect_count > (scan.image_count / 10): # Simple threshold
                scan.status = "fail"
            
            db.commit()
        except Exception as db_err:
            logging.error(f"DB Error saving result: {db_err}")
        finally:
            db.close()
            
    except Exception as e:
        logging.error(f"Inference Task Failed: {e}")

def run_inference_wrapper(filepath, result_dir, save_overlay, scan_id, model_type="black", mm2_per_pixel=0.0037):
    """Wrapper to return filepath and scan_id along with results."""
    from inference.inference_service import run_inference_task
    res = run_inference_task(filepath, result_dir, save_overlay, model_type=model_type, mm2_per_pixel=mm2_per_pixel)
    return (*res, filepath, scan_id)


# ------------- Global / Manager -------------
router = APIRouter()
# manager = PLCManager() # Use imported manager

# Global executor for inference
from concurrent.futures import ProcessPoolExecutor
inference_executor = ProcessPoolExecutor(max_workers=1)

# ------------- Models -------------
# ... (Keep models as is) ...
# ... (Keep models as is) ...
class PLCConnectRequest(BaseModel):
    ip: str
    port: int
    timeout: int = 5000 
    mm2_per_pixel: float = 0.0037

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

class ScanStartRequest(BaseModel):
    model_type: str = "black" # white, black

class ModelChangeRequest(BaseModel):
    model_type: str

class ScanStopRequest(BaseModel):
    pass

class ErrorResetRequest(BaseModel):
    pass

# ------------- Constants -------------
MOTION_COMMANDS = {
    # Control
    "servo_on": "M0",
    # M46 is Homing Completed Flag (Read Only generally)
    
    # --- POSITION MODE (M46=1) ---
    "x_left_pos": "M433",
    "x_right_pos": "M434",
    "y_fwd_pos": "M432",
    "y_back_pos": "M431",
    "z_up_pos": "M435",
    "z_down_pos": "M436",

    # --- JOG MODE (M46=0) ---
    "x_left_jog": "M10",
    # "x_right_jog": "M???", # User didn't specify right jog, assuming not needed or M200?
    "y_back_jog": "M20",
    "z_down_jog": "M30",
    
    # Legacy/Misc
    "home_cmd": "M1"
}

# ------------- Polling Logic -------------

def poll_plc_thread():
    """Background polling using the shared manager."""
    # Use scan_session state
    last_Y14 = 0
    last_Y15 = 0
    last_m101 = 1
    
    last_health_log_time = time.time()
    
    global critical_error_active
    
    while True:
        try:
            # Status check (Heartbeat)
            # manager.read_bit handles errors internally but returns None on failure
            resp = manager.read_bit("X0", 1)
            m5_status = manager.read_bit("M5", 1)
            
            if m5_status and m5_status[0] == 1:
                # Check Y14 Trigger
                resp_y = manager.read_bit("Y14", 2)
                if resp_y and len(resp_y) > 0:
                    current_Y14 = resp_y[0]
                    current_Y15 = resp_y[1]
                    
                    state = scan_session.get_state()
                    click_state = state["click"]

                    # Rising Edge (0 -> 1)
                    if (current_Y14 == 1 and last_Y14 == 0) or (current_Y15 == 1 and last_Y15 == 0) or (click_state == 1):
                        scan_session.set_click(0)
                        time.sleep(0.1)

                        
                        current_m101 = manager.read_bit("M101", 1)
                        if current_m101 and last_m101 != current_m101[0]:
                            scan_session.increment_county()
                            last_m101 = current_m101[0]
                            
                        # Refresh state after updates
                        state = scan_session.get_state()
                        current_batch = state["batch_folder"]
                        
                        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        save_dir = current_batch

                        # Use batch folder if set, otherwise create one (Fallback)
                        if not save_dir:
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            save_dir = os.path.join(backend_dir, "captured_images", f"scan_{timestamp}")
                            os.makedirs(save_dir, exist_ok=True)



                        
                        # --- Grid Location Logging ---
                        try:
                            # Read Coordinates (D25=X, D21=Y, D27=Z) - 1 Angstrom = 1e-4 mm
                            loc_raw = manager.read_sign_dword("D21", 10) # Read block covering D21-D30 to get D21, D25, D27
                            # D21 is index 0 (Y)
                            # D25 is index 4 (X) - 32-bit registers, check addressing?
                            # Wait, read_sign_dword("D21", 10) returns list of 10 DWORDs usually.
                            
                            # Let's read individually to be safe and consistent with get_control_status
                            x_raw = manager.read_sign_dword("D25", 1)
                            y_raw = manager.read_sign_dword("D21", 1)
                            z_raw = manager.read_sign_dword("D27", 1)
                            
                            def to_mm(raw_list):
                                return round(raw_list[0] * 1e-4, 2) if raw_list else 0.0
                                
                            x_mm = to_mm(x_raw)
                            y_mm = to_mm(y_raw)
                            z_mm = to_mm(z_raw)
                            
                            grid_csv = os.path.join(save_dir, "grid_locations.csv")
                            file_exists = os.path.exists(grid_csv)
                            
                            with open(grid_csv, 'a', newline='') as f:
                                writer = csv.writer(f)
                                if not file_exists:
                                    writer.writerow(["Filename", "Grid_Y", "Grid_X", "X", "Y", "Z", "Timestamp"])
                                
                                filename = f"grid_{state['county']}_{state['count']}.jpg"
                                writer.writerow([
                                    filename, 
                                    state['county'], 
                                    state['count'], 
                                    x_mm, 
                                    y_mm, 
                                    z_mm,
                                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                ])
                        except Exception as loc_err:
                            logging.error(f"Failed to log grid location: {loc_err}")
                        # -----------------------------

                        filepath = os.path.join(save_dir, f"grid_{state['county']}_{state['count']}.jpg")
                        
                        if camera_manager:
                            try:
                                if camera_manager.save_current_frame(filepath):
                                    # Run inference on captured image
                                    if get_predictor is not None:
                                        try:
                                            result_dir = os.path.join(save_dir, "results")
                                            os.makedirs(result_dir, exist_ok=True)
                                            
                                            scan_id = os.path.basename(save_dir)
                                            
                                            future = inference_executor.submit(
                                                 run_inference_wrapper, 
                                                 filepath, 
                                                 result_dir, 
                                                 True, 
                                                 scan_id,
                                                 scan_session.model_type,
                                                 current_mm2_per_pixel
                                            )
                                            
                                            future.add_done_callback(save_inference_callback)
                                            
                                        except Exception as ie:
                                            logging.error(f"Inference submission failed: {ie}")
                                    
                                    try:
                                        time.sleep(0.1) 
                                        manager.write_bit("M77", [1])
                                        scan_session.increment_counters()
                                        
                                        try:
                                            x0_resp = manager.read_bit("X0", 1)
                                            if x0_resp and x0_resp[0] == 1:
                                                scan_session.set_click(1)
                                                time.sleep(1)
                                        except Exception as xe:
                                            logging.error(f"Error reading X0: {xe}")
                                            
                                    except Exception as we:
                                        logging.error(f"Failed to write M77: {we}")
                            except Exception as came:
                                logging.error(f"Camera save frame failed: {came}")
                    
                    last_Y14 = current_Y14
                    last_Y15 = current_Y15
                
                
            # --- Axis Data Monitoring (D40 - D80) ---
            try:
                # Read 21 DWords starting at D40 (D40 to D80 inclusive is 41 words? No, D40, 42..80 is 21 DWords)
                # D40, D42, ..., D80
                # Read 42 Signed Words (D40 - D81) for 16-bit registers
                axis_block = manager.read_sign_word("D40", 42)
                if axis_block and len(axis_block) >= 42:
                    
                    global axis_monitoring_data
                    
                    # Helper to get value securely
                    def get_val(idx):
                        return axis_block[idx] if idx < len(axis_block) else 0

                    def calc_health(current, regen, eff_torque, peak):
                         # Formula: 0.4*current + 0.2*regen + 0.2*eff_torque + 0.2*peak
                         # Uses abs() (modulus) to handle negative values correctly
                         return round(0.4 * abs(current) + 0.2 * abs(regen) + 0.2 * abs(eff_torque) + 0.2 * abs(peak), 1)

                    # X Axis (D40, D42, D44, D50) -> Indices doubled from D-word logic
                    # D40(0), D42(2), D44(4), D50(10)
                    x_load = abs(get_val(0))
                    x_torque = abs(get_val(2))
                    x_peak = abs(get_val(4))
                    x_current = abs(get_val(10)) / 10
                    x_health = calc_health(x_current, x_load, x_torque, x_peak)
                    
                    axis_monitoring_data["x"] = {
                        "load": x_load,
                        "torque": x_torque,
                        "peak": x_peak,
                        "current": x_current,
                        "health": x_health
                    }

                    # Y Axis (D58, D62, D78, D52)
                    # D58(18), D62(22), D78(38), D52(12)
                    y_load = abs(get_val(18))
                    y_torque = abs(get_val(22))
                    y_peak = abs(get_val(38))
                    y_current = abs(get_val(12)) / 10
                    y_health = calc_health(y_current, y_load, y_torque, y_peak)
                    
                    axis_monitoring_data["y"] = {
                        "load": y_load,
                        "torque": y_torque,
                        "peak": y_peak,
                        "current": y_current,
                        "health": y_health
                    }

                    # Z Axis (D64, D60, D80, D56)
                    # D64(24), D60(20), D80(40), D56(16)
                    z_load = abs(get_val(24))
                    z_torque = abs(get_val(20))
                    z_peak = abs(get_val(40))
                    z_current = abs(get_val(16)) / 10
                    z_health = calc_health(z_current, z_load, z_torque, z_peak)
                    
                    axis_monitoring_data["z"] = {
                        "load": z_load,
                        "torque": z_torque,
                        "peak": z_peak,
                        "current": z_current,
                        "health": z_health
                    }
                    
                    # --- Critical Error Check ---
                    if (x_health > 60 or y_health > 60 or z_health > 60):
                        if not critical_error_active:
                             critical_error_active = True
                             logging.error(f"CRITICAL ERROR: High Health Index! X:{x_health} Y:{y_health} Z:{z_health}")
                             # STOP SCAN (M5 OFF)
                             manager.write_bit("M5", [0])
                             # STOP MOTORS (M190 OFF)
                             # manager.write_bit("M190", [0]) # Disabled auto-off per request
                             add_event("CRITICAL: Servo Overload - System Halted", "error")
                    else:
                         if critical_error_active:
                              critical_error_active = False # Auto-reset flag if values drop? Or require manual reset?
                              # Usually critical errors need manual reset, but for now let's adhere to "if any one is above 60"
                              # So if it drops, the flag clears, but the motors stay off until user restarts.
                    

                    # --- History & Daily Stats Logic ---
                    current_time = datetime.datetime.now()
                    
                    # 1. Update In-Memory History (60s buffer)
                    # We want to store approximately last 60s. Polling is ~0.1s, but we only want to sample every ~2s?
                    # Or just store every Nth point?
                    # The request said: "store just values of past 60 seconds... status should be monitored in background every 2 seconds"
                    # Since this loop runs fast (~10Hz), we should throttle the history append.
                    
                    if time.time() - last_history_update >= 2.0:
                        last_history_update = time.time()
                        
                        snapshot = {
                            "time": current_time.isoformat(),
                            "x": axis_monitoring_data["x"],
                            "y": axis_monitoring_data["y"],
                            "z": axis_monitoring_data["z"]
                        }
                        servo_history.append(snapshot)
                        if len(servo_history) > 30: # 30 points * 2s = 60s
                             servo_history.pop(0)

                    # 2. Update Daily Stats (Peaks/Lows) - Check every cycle (fast) or every 2s?
                    # Real-time peak detection is better done every cycle.
                    
                    # Initialize stats from DB if empty
                    if not servo_daily_stats:
                         init_daily_stats()

                    # Check for day change to reset? 
                    # Request: "peak and lowest value of last 24 hours". 
                    # Strictly "last 24h" implies a sliding window, which is hard with just min/max scalars.
                    # Usually "Daily" implies "Today". 
                    # If "last 24h" means "rolling 24h", we need to store ALL data points for 24h?
                    # The user said: "remove the database... store just values of past 60 seconds AND peak/lowest value of last 24 hours".
                    # Interpretation: Keep a "Daily High/Low" record. If it's a fixed "Today" or "Yesterday+Today", simple min/max works.
                    # If strictly "Rolling 24h", we can't easily evict old peaks without full history.
                    # Assumption: "Daily Stats" (reset at midnight or just persistent all time peaks until manual reset?).
                    # Let's stick to "Session/Persistent Peaks", maybe reset manually or never?
                    # Or implementing a simple "reset if > 24h old"? 
                    # Let's just track absolute Min/Max since system start/DB creation for now, or per day.
                    # I will implement it as "Current Max/Min tracking", updated live.
                    
                    updates_needed = False
                    
                    def check_stat(axis, metric, value, timestamp):
                        nonlocal updates_needed
                        stats = servo_daily_stats[axis][metric]
                        
                        # Modulus (abs) for value comparison as requested "health index should be modulous"
                        # But metrics like current can be negative. User said "negative values too should be displayed as positive".
                        # So we track min/max of the MAGNITUDE? Or min/max of raw value?
                        # Request: "displayed as positive... peak and lowest value... mark them".
                        # If we display as positive, then "Lowest" is essentially 0? Or closest to 0?
                        # Or does "Lowest" mean most negative?
                        # "positive... displayed" suggests visuals.
                        # Storing: Let's store ABSOLUTE value for everything if that's what the graph shows.
                        # "keep track of highest lowest value of that field... mark them... remove database... store just values of past 60s"
                        # If graph is 0-Positive, then Min is likely close to 0.
                        # Let's use abs(value) for stats tracking too.
                        
                        abs_val = abs(value)
                        
                        if stats["min_val"] is None or abs_val < stats["min_val"]:
                            stats["min_val"] = abs_val
                            stats["min_time"] = timestamp
                            updates_needed = True
                            
                        if stats["max_val"] is None or abs_val > stats["max_val"]:
                            stats["max_val"] = abs_val
                            stats["max_time"] = timestamp
                            updates_needed = True

                    for axis_char in ['x', 'y', 'z']:
                        data = axis_monitoring_data[axis_char]
                        # Metrics to track: current, torque, peak, load, health
                        for metric in ['current', 'torque', 'peak', 'load', 'health']:
                            check_stat(axis_char, metric, data[metric], current_time)
                            
                    if updates_needed:
                        # Save to DB (Throttle this? maybe every 10s or 1min? To avoid disk hammering for noisy signals?)
                        # But user wants "displayed even if backend restarts".
                        # Immediate save is safest but costly. Let's do it. SQLite is fast enough for occasional peaks.
                        # But if signal is rising fast, every polling cycle will trigger a new max.
                        # Let's throttle DB saves to once every 5 seconds max if dirty.
                        pass
                    
                    if updates_needed and (time.time() - last_stats_save_time > 5.0):
                        save_daily_stats()
                        last_stats_save_time = time.time()

                            
            except Exception as e_mon:
                # Don't spam logs if it fails, maybe just debug or ignore
                pass

        except Exception as e:
            logging.error(f"Polling thread error: {e}")
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
             None, # output_dir=None to skip saving
             False, # save_overlay (ignored when output_dir is None, but good for clarity)
             "warmup_scan",
             "black" # model_type explicitly
        )
        # We don't wait for result here to not block startup, but it will run in background.
        print("[PLC INIT] Inference warmup task submitted.", flush=True)
        
    except Exception as e:
        print(f"[PLC INIT] Warmup failed: {e}")

    settings = load_plc_settings()
    if settings and settings.get("ip") and settings.get("port"):
        print(f"[PLC INIT] Loading settings: {settings['ip']}:{settings['port']}", flush=True)
        manager.configure(settings["ip"], settings["port"])
        # Set global mm2_per_pixel
        global current_mm2_per_pixel
        current_mm2_per_pixel = settings.get("mm2_per_pixel", 0.0037)
        print(f"[PLC INIT] mm2_per_pixel: {current_mm2_per_pixel}", flush=True)
        start_polling()
    else:
        print("[PLC INIT] No settings found. Waiting for manual connect.", flush=True)

    try:
         import glob
         pass
    except:
         pass





# ------------- General PLC Endpoints -------------

@router.get("/plc/status")
def get_plc_status():
    st = manager.get_status()
    return st

@router.post("/plc/connect")
def plc_connect(req: PLCConnectRequest):
    """Save settings and restart/configure manager."""
    try:
        # Save settings to JSON file
        save_plc_settings(req.ip, req.port, req.mm2_per_pixel)
        
        # Update global mm2
        global current_mm2_per_pixel
        current_mm2_per_pixel = req.mm2_per_pixel
        
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
def plc_write(req: PLCWriteRequest):
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
def control_lights(req: LightControlRequest):
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

@router.post("/plc/set-model")
def set_model(req: ModelChangeRequest):
    """Explicitly set/load the model without starting a scan."""
    try:
        # Update session state
        scan_session.model_type = req.model_type
        
        # Trigger warm-up/load
        dummy_path = os.path.join(os.path.dirname(__file__), "warmup.jpg")
        # Ensure dummy exists (it should from init, but good to be safe)
        if not os.path.exists(dummy_path):
             import numpy as np
             from PIL import Image
             img = Image.fromarray(np.zeros((518, 518, 3), dtype=np.uint8))
             img.save(dummy_path)

        # Submit task to force load
        inference_executor.submit(
             run_inference_wrapper, 
             dummy_path, 
             None, 
             False, 
             "manual_switch",
             req.model_type
        )
        add_event(f"Model Switched to {req.model_type}", "info")
        return {"success": True, "message": f"Model switched to {req.model_type}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/scan-start")
def scan_start(username: str = "operator", req: ScanStartRequest = ScanStartRequest()):
    """Start (or Resume) Scan with Model Selection."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    
    try:
        # Check if we can change model (only if IDLE)
        state = scan_session.get_state()
        if state["status"] == "RUNNING" and state["model_type"] != req.model_type:
             return {"success": False, "error": f"Cannot change model during run. Current: {state['model_type']}. Reset cycle first."}
        
        # Start/Resume Session
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        scan_session.start_new_scan(username, backend_dir, req.model_type)
        
        # Trigger explicit warmup/load of the selected model so user sees log immediately
        try:
             # Create dummy/blank image path if needed (reusing the one from init)
             dummy_path = os.path.join(os.path.dirname(__file__), "warmup.jpg")
             if not os.path.exists(dummy_path):
                 import numpy as np
                 from PIL import Image
                 img = Image.fromarray(np.zeros((518, 518, 3), dtype=np.uint8))
                 img.save(dummy_path)
                 
             inference_executor.submit(
                 run_inference_wrapper, 
                 dummy_path, 
                 None, 
                 False, 
                 "warmup_switch",
                 req.model_type # Force load of selected model
             )
        except Exception as we:
             print(f"[Scan Start] Warmup trigger failed: {we}")

        # Set M5 ON
        manager.write_bit("M5", [1])
        add_event(f"Scan Started ({req.model_type})", "success")
        
        return {"success": True, "scan_id": scan_session.scan_id, "status": "RUNNING"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/scan-stop")
def scan_stop(req: ScanStopRequest):
    """Pause scan by setting M5 to OFF."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    try:
        manager.write_bit("M5", [0])
        scan_session.pause_scan()
        add_event("Scan Paused", "info")
        return {"success": True, "message": "Scan Paused (M5 OFF)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/cycle-reset")
def cycle_reset():
    """Reset Cycle (M120 Pulse) and Backend State."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    try:
        # Pulse M120
        manager.write_bit("M120", [1])
        time.sleep(0.1)
        manager.write_bit("M120", [0])
        
        # Reset Backend State
        scan_session.reset_cycle()
        
        add_event("Cycle Reset", "info")
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/error-reset")
def error_reset(req: ErrorResetRequest):
    """Pulse M15 to reset errors."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    try:
        # Pulse M15: ON then OFF
        manager.write_bit("M15", [1])
        time.sleep(0.2)
        manager.write_bit("M15", [0])
        add_event("Error reset triggered", "info")
        return {"success": True, "message": "Error Reset (M15 Pulsed)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/toggle-pulse")
def toggle_pulse(req: TogglePulseRequest):
    """Cycle M103/M104 based on mode."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    
    try:
        # White=M103, Green=M104 (following ManualMode logic)
        bit_on = None
        bit_off = None

        if req.mode.lower() == "white":
            bit_on = "M103"
            bit_off = "M104"
        elif req.mode.lower() == "green":
            bit_on = "M104"
            bit_off = "M103"
        elif req.mode.lower() == "off":
            # Both off
            manager.write_bit("M103", [0])
            manager.write_bit("M104", [0])
            return {"success": True, "message": "Lights OFF"}
        else:
             return {"success": False, "error": "Invalid Mode"}

        # Switch
        manager.write_bit(bit_on, [1])
        manager.write_bit(bit_off, [0])
        
        add_event(f"Pulse sent: {req.mode} ({bit_on})", "info")
        return {"success": True, "message": f"Set {bit_on}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ------------- Control Endpoints -------------

@router.post("/plc/scan-start")
def scan_start(username: str = "operator"):
    """Start scan by setting M5 to ON and creating a new batch folder."""
    # Global vars removed, using scan_session
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Use ScanSession to initialize
        current_batch_folder, timestamp = scan_session.start_new_scan(username, backend_dir)

        # NOTE: DB Record for Scan will be created lazily when first image is captured
        # This prevents empty scans from appearing in the database
        
        # Save Scan Metadata having scanned_by (Legacy JSON support)
        try:
            import json
            meta_file = os.path.join(current_batch_folder, "scan_info.json")
            with open(meta_file, 'w') as f:
                json.dump({
                    "scanned_by": username,
                    "start_time": timestamp,
                    "role": "operator"
                }, f, indent=2)
        except Exception as ex:
            logging.error(f"Failed to save scan info: {ex}")

        time.sleep(0.1)
        manager.write_bit("M5", [1])
        time.sleep(0.1)
        scan_session.set_click(1)
        add_event("Scan started", "success")
        return {"success": True, "message": "Scan Started (M5 ON)", "batch_folder": current_batch_folder}
    except Exception as e:
        import traceback
        logging.error(f"SCAN START ERROR: {e}")
        try:
            # Also keep the file logging for now as a backup/legacy expectation
            with open("C:/MyStuff/VS/MECup/backend/error_log.txt", "a") as log:
                traceback.print_exc(file=log)
        except:
             logging.error("Failed to write to legacy error log file")
        return {"success": False, "error": str(e)}

@router.post("/plc/grid-one")
def grid_one():
    """Trigger Grid One by setting M4 to ON."""
    try:
        time.sleep(0.1)
        manager.write_bit("M4", [1])
        return {"success": True, "message": "Grid One Triggered (M4 ON)"}
    except Exception as e:
        logging.error(f"Grid One Error: {e}")
        return {"success": False, "error": str(e)}

@router.post("/plc/cycle-reset")
def cycle_reset():
    """Reset cycle by setting M120 to ON and clearing batch folder."""
    try:
        manager.write_bit("M120", [1])
        # Use ScanSession to reset
        scan_session.reset_cycle()
        
        add_event("Cycle reset completed", "info")
        return {"success": True, "message": "Cycle Reset (M120 ON) - Batch cleared"}
    except Exception as e:
        logging.error(f"Cycle Reset Error: {e}")
        return {"success": False, "error": str(e)}

@router.post("/plc/homing-start")
def homing_start():
    """Start homing sequence by setting M1 to ON."""
    try:
        manager.write_bit("M1", [1])
        add_event("Homing sequence started", "info")
        return {"success": True, "message": "Homing Started (M4 ON)"}
    except Exception as e:
        logging.error(f"Homing Error: {e}")
        return {"success": False, "error": str(e)}

@router.get("/plc/control-status")
def get_control_status():
    """Read current status of control bits."""
    if not manager.connected:
        return {
            "error": "PLC Not Connected", 
            "m5": None, "m4": None, "m120": None, "m1": None, "m0": None, 
            "m190": None, "y0": None,
            "m103": None, "m104": None, 
            "m68": None, "m69": None, "m70": None, "m71": None, 
            "m46": None, "x_pos": 0, "y_pos": 0, "z_pos": 0
        }
    try:
        m_block = manager.read_bit("M0", 125) 
        
        # Read Y0 separately (Output)
        y0 = manager.read_bit("Y0", 1)
        
        # Read M190 separately for reliable servo status
        m190 = manager.read_bit("M190", 1)
        
        # Read Coordinates D21-D28 in one block of 4 DWORDs (D21, D23, D25, D27)
        # D21=Y, D25=X, D27=Z
        d_block = manager.read_sign_dword("D21", 4)

        def to_mm(raw_val):
            if not raw_val: return 0.0
            # Convert Angstrom to mm (1e-4) -> value * 0.0001
            return round(raw_val * 1e-4, 2)

        # Parse D-block
        # d_block indices: 0=(D21,D22)[Y], 1=(D23,D24), 2=(D25,D26)[X], 3=(D27,D28)[Z]
        y_mm = 0.0
        x_mm = 0.0
        z_mm = 0.0
        
        if d_block and len(d_block) >= 4:
            y_mm = to_mm(d_block[0])
            x_mm = to_mm(d_block[2])
            z_mm = to_mm(d_block[3])
        
        def get_bit(idx):
            return m_block[idx] if m_block and len(m_block) > idx else None
            
        return {
            "m5": get_bit(5),
            "m4": get_bit(4),
            "m120": get_bit(120),
            "m1": get_bit(1),
            "m0": get_bit(0),
            "m190": m190[0] if m190 else None, # Servo Enable
            "y0": y0[0] if y0 else None,
            "m68": get_bit(68), # Up
            "m69": get_bit(69), # Down
            "m70": get_bit(70), # Right
            "m71": get_bit(71), # Left
            "m103": get_bit(103), "m104": get_bit(104),
            "m46": get_bit(46), # Homing Done Flag
            "x_pos": x_mm,
            "y_pos": y_mm,
            "z_pos": z_mm
        }

    except Exception as e:
         return {"error": str(e), "connected": False}

class LightModeRequest(BaseModel):
    mode: str # "off", "white", "green"

class LightDirectRequest(BaseModel):
    direction: str # "up", "down", "left", "right"
    state: bool

@router.post("/plc/light-mode")
def set_light_mode(req: LightModeRequest):
    """Set light mode: Off (M103/104=0), White (M103=1), Green (M104=1)."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    try:
        m103_val = 1 if req.mode == "white" else 0
        m104_val = 1 if req.mode == "green" else 0
        
        # Write both
        manager.write_bit("M103", [m103_val])
        manager.write_bit("M104", [m104_val])
        
        add_event(f"Light Mode: {req.mode}", "info")
        return {"success": True, "mode": req.mode}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/plc/light-direction")
def set_light_direction(req: LightDirectRequest):
    """Set light direction bits (M68-M71)."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    
    # Map direction to bit
    dir_map = {
        "up": "M68",
        "down": "M69",
        "right": "M70",
        "left": "M71"
    }
    
    if req.direction not in dir_map:
        return {"success": False, "error": "Invalid Direction"}
        
    try:
        bit = dir_map[req.direction]
        # Inverted logic: 0 = ON, 1 = OFF
        val = 0 if req.state else 1
        manager.write_bit(bit, [val])
        return {"success": True, "bit": bit, "state": val}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/plc/heartbeat")
def get_heartbeat():
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
            "axis_data": axis_monitoring_data,
            "critical_error": critical_error_active,
            "error": None
        }
    except Exception as e:
        return {
            "connected": False,
            "y1": None,
            "axis_data": axis_monitoring_data,
            "critical_error": False,
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
def set_servo_speeds(speeds: ServoSpeedRequest) -> Dict[str, str]:
    if not manager.connected:
        raise HTTPException(status_code=503, detail="PLC Not Connected")
    try:
        manager.write_sign_dword("D2", [speeds.x])
        manager.write_sign_dword("D0", [speeds.y])
        manager.write_sign_dword("D4", [speeds.z])
        logging.info(f"[SERVO] Speeds set: {speeds}")
        return {"status": "success", "message": "Speeds updated"}
    except Exception as e:
        logging.error(f"Servo Speed Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/servo/speeds")
def get_servo_speeds():
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

class JogMoveRequest(BaseModel):
    command: str
    state: bool # True = Press (ON), False = Release (OFF)

@router.post("/servo/jog")
def jog_move(req: JogMoveRequest):
    """Handle Jog Move (Press/Release)."""
    if not manager.connected:
        return {"success": False, "error": "PLC Not Connected"}
    
    cmd_bit = MOTION_COMMANDS.get(req.command)
    if not cmd_bit:
        return {"success": False, "error": f"Invalid Command: {req.command}"}
    
    try:
        val = 1 if req.state else 0
        manager.write_bit(cmd_bit, [val])
        return {"success": True, "bit": cmd_bit, "state": val}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/servo/enable")
def enable_servo(req: ServoEnableRequest) -> Dict[str, Any]:
    if not manager.connected:
        raise HTTPException(status_code=503, detail="PLC Not Connected")
    try:
        # Use explicit state from request
        new_val = 1 if req.enable else 0
        
        manager.write_bit("M190", [new_val])
        return {"status": "success", "message": f"Servo {'Enabled' if new_val else 'Disabled'}", "enabled": bool(new_val)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servo/move")
def trigger_motion(req: ServoMoveRequest) -> Dict[str, str]:
    if req.command not in MOTION_COMMANDS:
        raise HTTPException(status_code=400, detail="Invalid Command")
    if not manager.connected:
        raise HTTPException(status_code=503, detail="PLC Not Connected")
    
    bit_addr = MOTION_COMMANDS[req.command]
    try:
        manager.write_bit(bit_addr, [1])
        logging.info(f"[SERVO] Triggered {req.command}")
        time.sleep(1)
        manager.write_bit(bit_addr, [0])
        return {"status": "success", "message": f"Triggered {req.command}"}
    except Exception as e:
        logging.error(f"Servo Motion Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------- Scan History Endpoints -------------

@router.get("/scans/list")
def list_scans():
    """List all past scans from Database."""
    db = SessionLocal()
    try:
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
        return {"scans": scans}
    except Exception as e:
        return {"scans": [], "error": str(e)}
    finally:
        db.close()

@router.get("/scans/{scan_id}")
def get_scan_details(scan_id: str):
    """Get detailed information about a specific scan from DB."""
    import json as json_lib
    db = SessionLocal()
    try:
        scan = db.query(plc_models.Scan).filter(plc_models.Scan.id == scan_id).first()
        if not scan:
             raise HTTPException(status_code=404, detail="Scan not found")
        
        # Get images
        images_db = db.query(plc_models.ScanImage).filter(plc_models.ScanImage.scan_id == scan_id).all()
        
        images = []
        defects = []
        defect_types = {}
        total_defect_count = scan.defect_count
        
        # Try to load defect details from metadata JSON files in results folder
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        results_dir = os.path.join(backend_dir, "captured_images", scan_id, "results")
        
        # Build a lookup of metadata by original image filename
        meta_lookup = {}
        if os.path.isdir(results_dir):
            for meta_file in os.listdir(results_dir):
                if meta_file.endswith("_meta.json"):
                    try:
                        with open(os.path.join(results_dir, meta_file), 'r') as mf:
                            meta = json_lib.load(mf)
                            orig_image = meta.get("image", "")
                            meta_lookup[orig_image] = meta
                    except Exception:
                        pass
        
        for img in images_db:
            images.append(img.filename)
            
            # Try to get per-image defect details from metadata
            img_meta = meta_lookup.get(img.filename, {})
            img_defect_details = img_meta.get("defects", [])
            
            # Accumulate defect_types from metadata
            for d in img_defect_details:
                dtype = d.get("type", "Unknown")
                if dtype != "Background":
                    defect_types[dtype] = defect_types.get(dtype, 0) + 1
            
            if img.has_defects:
                overlay_name = os.path.basename(img.overlay_path) if img.overlay_path else None
                defects.append({
                    "image": img.filename,
                    "overlay": overlay_name,
                    "overlay_url": f"/scans/{scan_id}/results/{overlay_name}" if overlay_name else None,
                    "image_url": f"/scans/{scan_id}/image/{img.filename}",
                    "defect_count": img.defect_count,
                    "defect_details": img_defect_details
                })
        
        images.sort()
        
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
            "status": scan.status,
            "scanned_by": scan.scanned_by
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.delete("/scans/{scan_id}")
def delete_scan(scan_id: str):
    """Delete a scan record and its associated files."""
    db = SessionLocal()
    try:
        scan = db.query(plc_models.Scan).filter(plc_models.Scan.id == scan_id).first()
        
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # 1. Delete Folder force
        if scan.batch_folder and os.path.exists(scan.batch_folder):
            try:
                import shutil
                shutil.rmtree(scan.batch_folder)
            except Exception as fe:
                logging.error(f"Failed to delete folder {scan.batch_folder}: {fe}")
        
        # 2. Delete from DB (Cascade should handle images)
        db.delete(scan)
        db.commit()
        
        return {"success": True, "message": f"Scan {scan_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Delete Scan Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

from fastapi.responses import FileResponse

@router.get("/scans/{scan_id}/image/{filename}")
def get_scan_image(scan_id: str, filename: str):
    """Get a specific image from a scan."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(backend_dir, "captured_images", scan_id, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(file_path, media_type="image/jpeg")

@router.get("/scans/{scan_id}/results/{filename}")
def get_scan_result(scan_id: str, filename: str):
    """Get a result image from a scan."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(backend_dir, "captured_images", scan_id, "results", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Result image not found")
    
    media_type = "image/png" if filename.endswith(".png") else "image/jpeg"
    media_type = "image/png" if filename.endswith(".png") else "image/jpeg"
    return FileResponse(file_path, media_type=media_type)


@router.get("/servo/history")
def get_servo_history():
    """Get servo health history and daily stats."""
    # Return in-memory buffer + stats
    
    # Init stats if not yet loaded (e.g. if polling hasn't run yet)
    if not servo_daily_stats:
        init_daily_stats()
        
    return {
        "history": servo_history,
        "stats": servo_daily_stats
    }

