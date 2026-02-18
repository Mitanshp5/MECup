
import uvicorn
import os
import psutil
import time
import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from contextlib import asynccontextmanager

from contextlib import asynccontextmanager

# Reuse existing database and auth
try:
    from database import get_db, engine
    from auth import router as auth_router, models as auth_models, security
    from plc import models as plc_models
    from utils.image_stitcher import stitch_images
    from plc.settings import load_stitch_scale
except ImportError:
    # Fallback for relative imports if run differently
    from .database import get_db, engine
    from .auth import router as auth_router, models as auth_models, security
    from .plc import models as plc_models
    from .utils.image_stitcher import stitch_images
    from .plc.settings import load_stitch_scale

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure Tables Exist
    auth_models.Base.metadata.create_all(bind=engine)
    plc_models.Base.metadata.create_all(bind=engine)
    
    # Create Default Admin User
    try:
        db = next(get_db())
        admin_user = os.getenv("MECUP_ADMIN_USER", "mee")
        admin_pass = os.getenv("MECUP_ADMIN_PASSWORD", "1234")
        
        user = db.query(auth_models.User).filter(auth_models.User.username == admin_user).first()
        hashed_pwd = security.get_password_hash(admin_pass)
        
        if not user:
            print(f"[Mobile] Creating default user '{admin_user}'...", flush=True)
            new_user = auth_models.User(
                username=admin_user, 
                hashed_password=hashed_pwd, 
                role="admin"
            )
            db.add(new_user)
            db.commit()
            print(f"[Mobile] Default user created: {admin_user}", flush=True)
        else:
            # Sync password/role
            user.hashed_password = hashed_pwd
            user.role = "admin"
            db.commit()
            print(f"[Mobile] User '{admin_user}' synced.", flush=True)
    except Exception as e:
        print(f"[Mobile] Failed to ensure admin user: {e}", flush=True)
    
    yield

# Initialize App
app = FastAPI(
    title="MECup Mobile Companion API",
    description="Lightweight API for Mobile Devices (Auth, Heartbeat, Past Scans)",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Mobile Access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local network validation
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Auth Router (Login users)
# Include Auth Router (Login users)
app.include_router(auth_router.router)

# --- Mobile Specific Endpoints ---


# --- Mobile Specific Endpoints (Frontend Aligned) ---

@app.get("/")
async def root():
    return {"message": "MECup Mobile Server Running"}

# --- System & Heartbeat ---

@app.get("/system/resources")
def get_system_resources():
    """Matches /system/resources expectation."""
    cpu = 0
    memory = 0
    disk = 0
    uptime = 0
    gpu = 0

    try:
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        uptime = int(time.time() - psutil.boot_time())
        
        # GPU - Generic Windows via typeperf
        try:
            import subprocess
            # Query 3D engines.
            cmd = ['typeperf', r'\GPU Engine(*engtype_3D*)\Utilization Percentage', '-sc', '1']
            # timeout is critical
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                output = result.stdout.strip().split('\n')
                # Find data lines
                data_lines = [line for line in output if line and '"' in line]
                if len(data_lines) >= 2:
                    # Last line is data: "02/12/2026 09:46:12.123","0.000000","5.234123",...
                    values = data_lines[-1].split(',')[1:] # Skip timestamp
                    valid_values = []
                    for v in values:
                        try:
                            val = float(v.replace('"', ''))
                            valid_values.append(val)
                        except:
                            pass
                    if valid_values:
                        gpu = max(valid_values) # Take peak usage of any 3D engine
        except Exception as e:
            print(f"[Mobile] GPU Fetch Error: {e}", flush=True)

    except Exception as e:
        print(f"[Mobile] Error fetching system resources: {e}", flush=True)

    return {
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "gpu": round(gpu, 1),
        "network": 0,
        "uptime": uptime
    }

@app.get("/mobile/heartbeat")
def get_mobile_heartbeat(db: Session = Depends(get_db)):
    """Keep this for legacy or specialized mobile view if needed."""
    # Reuse system resources logic
    res = get_system_resources()
    res["status"] = "online"
    res["timestamp"] = datetime.datetime.now().isoformat()
    
    # Add PLC Health
    latest = db.query(plc_models.ServoHealth).order_by(plc_models.ServoHealth.timestamp.desc()).first()
    res["plc"] = {"connected": False}
    if latest:
        is_fresh = (datetime.datetime.utcnow() - latest.timestamp).total_seconds() < 30
        res["plc"] = {
            "connected": is_fresh,
            "x": {"health": latest.x_health},
            "y": {"health": latest.y_health},
            "z": {"health": latest.z_health}
        }
    return res

@app.get("/plc/status")
def get_plc_status(db: Session = Depends(get_db)):
    """Used by MobileHealthPage."""
    latest = db.query(plc_models.ServoHealth).order_by(plc_models.ServoHealth.timestamp.desc()).first()
    connected = False
    if latest:
        connected = (datetime.datetime.utcnow() - latest.timestamp).total_seconds() < 30
    return {"connected": connected}

@app.get("/plc/heartbeat")
def get_plc_heartbeat_aligned(db: Session = Depends(get_db)):
    """Aligned with details expected by MobileHealthPage."""
    latest = db.query(plc_models.ServoHealth).order_by(plc_models.ServoHealth.timestamp.desc()).first()
    
    connected = False
    axis_data = {}
    
    if latest:
        connected = (datetime.datetime.utcnow() - latest.timestamp).total_seconds() < 30
        axis_data = {
            "x": {
                "speed": int(latest.x_current * 10), # Approximation or raw? Code used speed in one place, current in another.
                "load": latest.x_load,
                "torque": latest.x_torque,
                "peak": latest.x_peak,
                "current": latest.x_current
            },
            "y": {
                "speed": int(latest.y_current * 10),
                "load": latest.y_load,
                "torque": latest.y_torque,
                "peak": latest.y_peak,
                "current": latest.y_current
            },
            "z": {
                "speed": int(latest.z_current * 10),
                "load": latest.z_load,
                "torque": latest.z_torque,
                "peak": latest.z_peak,
                "current": latest.z_current
            }
        }

    return {
        "connected": connected,
        "y1": 0, # Mock output status
        "axis_data": axis_data
    }

@app.get("/servo/history")
def get_mobile_servo_history(db: Session = Depends(get_db)):
    """
    Get servo daily stats from DB for Mobile Chart Min/Max lines.
    Mobile builds its own live history, but needs persistence stats.
    """
    stats = {}
    try:
        # Structure: axis -> metric -> {min, max, min_time, max_time}
        # Initialize empty first
        for axis in ['x', 'y', 'z']:
            stats[axis] = {}
            for metric in ['current', 'torque', 'peak', 'load', 'health']:
                stats[axis][metric] = {
                    "min_val": None, "min_time": None,
                    "max_val": None, "max_time": None
                }
        
        # Query DB
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
        print(f"[Mobile] Failed to fetch daily stats: {e}", flush=True)

    return {
        # Mobile maintains its own live history buffer in frontend state
        "history": [], 
        "stats": stats
    }

@app.get("/camera/fps")
def get_camera_fps():
    """Mock for MobileHealthPage."""
    return {"fps": 0, "is_open": False}

@app.get("/events")
def get_events():
    """Mock or DB events."""
    return {"events": []}

# --- Scans ---

@app.get("/scans/list")
def get_scans_list(limit: int = 50, db: Session = Depends(get_db)):
    """Matches MobileReportPage."""
    scans = db.query(plc_models.Scan).order_by(plc_models.Scan.start_time.desc()).limit(limit).all()
    # Transform to match expected format: { scans: [...] }
    # ScanRecord interface: id, date, time, image_count, defect_count, status, scanned_by
    result = []
    for s in scans:
        result.append({
            "id": s.id,
            "date": s.start_time.strftime("%Y-%m-%d"),
            "time": s.start_time.strftime("%H:%M:%S"),
            "image_count": s.image_count,
            "defect_count": s.defect_count,
            "status": s.status,
            "scanned_by": s.scanned_by
        })
    return {"scans": result}

@app.get("/scans/{scan_id}")
def get_scan_detail_aligned(scan_id: str, db: Session = Depends(get_db)):
    """Matches MobileReportPage detail view."""
    import json as json_lib
    scan = db.query(plc_models.Scan).filter(plc_models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get images
    images_db = db.query(plc_models.ScanImage).filter(plc_models.ScanImage.scan_id == scan_id).all()
    
    images = []
    defects_list = []
    defect_types = {}
    
    # Try to load defect details from metadata JSON files in results folder
    backend_dir = os.path.dirname(os.path.abspath(__file__))
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
            defects_list.append({
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
        "date": scan.start_time.strftime("%Y-%m-%d"),
        "time": scan.start_time.strftime("%H:%M:%S"),
        "image_count": scan.image_count,
        "images": images,
        "total_defects": scan.defect_count,
        "defect_types": defect_types,
        "defects": defects_list,
        "status": scan.status,
        "scanned_by": scan.scanned_by
    }

# --- Image Serving Endpoints ---
from fastapi.responses import FileResponse

@app.get("/scans/{scan_id}/image/{filename}")
def get_scan_image(scan_id: str, filename: str):
    """Get a specific original image from a scan."""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(backend_dir, "captured_images", scan_id, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(file_path, media_type="image/jpeg")

@app.get("/scans/{scan_id}/results/{filename}")
def get_scan_result(scan_id: str, filename: str):
    """Get a result/overlay image from a scan."""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(backend_dir, "captured_images", scan_id, "results", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Result image not found")
    
    media_type = "image/png" if filename.endswith(".png") else "image/jpeg"
    return FileResponse(file_path, media_type=media_type)

@app.get("/scans/{scan_id}/stitched")
def get_stitched_image(scan_id: str):
    """Get or generate stitched image for a scan."""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    scan_folder = os.path.join(backend_dir, "captured_images", scan_id)
    
    if not os.path.exists(scan_folder):
        raise HTTPException(status_code=404, detail="Scan folder not found")
    
    stitched_path = os.path.join(scan_folder, "stitched_result.jpg")
    
    # Check if stitched image already exists
    if not os.path.exists(stitched_path):
        # Generate stitched image with scale from settings
        try:
            scale = load_stitch_scale()
            result_path = stitch_images(scan_folder, "stitched_result.jpg", scale)
            if result_path is None:
                raise HTTPException(status_code=500, detail="Failed to stitch images")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Stitching error: {str(e)}")
    
    return FileResponse(stitched_path, media_type="image/jpeg")

@app.get("/mobile/scans")
def get_recent_scans_legacy(limit: int = 20, db: Session = Depends(get_db)):
    """Legacy/Direct listing."""
    scans = db.query(plc_models.Scan).order_by(plc_models.Scan.start_time.desc()).limit(limit).all()
    return scans


if __name__ == "__main__":
    print("[Mobile] Starting Server on 0.0.0.0:5002...", flush=True)
    # Host 0.0.0.0 is CRITICAL for network access
    uvicorn.run("mobile_main:app", host="0.0.0.0", port=5002, reload=True)
