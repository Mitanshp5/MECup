
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
except ImportError:
    # Fallback for relative imports if run differently
    from .database import get_db, engine
    from .auth import router as auth_router, models as auth_models, security
    from .plc import models as plc_models

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
    scan = db.query(plc_models.Scan).filter(plc_models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get images
    images = db.query(plc_models.ScanImage).filter(plc_models.ScanImage.scan_id == scan_id).all()
    
    defects_list = []
    total_defects = 0
    defect_types = {}

    for img in images:
        if img.has_defects:
            total_defects += img.defect_count
            defects_list.append({
                "image": img.filename,
                "overlay": img.overlay_path,
                "overlay_url": f"/static/captures/{scan_id}/{img.filename}", # Simplified URL logic
                "defect_count": img.defect_count,
                "defect_details": [] # Populate if metadata exists
            })
    
    return {
        "id": scan.id,
        "date": scan.start_time.strftime("%Y-%m-%d"),
        "time": scan.start_time.strftime("%H:%M:%S"),
        "image_count": scan.image_count,
        "images": [img.filename for img in images],
        "total_defects": total_defects,
        "defect_types": defect_types, # Logic to parse types if available
        "defects": defects_list,
        "status": scan.status,
        "scanned_by": scan.scanned_by
    }

@app.get("/mobile/scans")
def get_recent_scans_legacy(limit: int = 20, db: Session = Depends(get_db)):
    """Legacy/Direct listing."""
    scans = db.query(plc_models.Scan).order_by(plc_models.Scan.start_time.desc()).limit(limit).all()
    return scans


if __name__ == "__main__":
    print("[Mobile] Starting Server on 0.0.0.0:5002...", flush=True)
    # Host 0.0.0.0 is CRITICAL for network access
    uvicorn.run("mobile_main:app", host="0.0.0.0", port=5002, reload=True)
