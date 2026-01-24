import threading
import time
import socket
import datetime
import os
# Import the library directly
import rk_mcprotocol as mc
from .settings import save_plc_settings, load_plc_settings
# Import camera manager for triggering captures
# Use relative import based on package structure
try:
    from ..camera.camera_manager import camera_manager
except ImportError:
    # If running as script, might need adjustment, but inside package structure this should work
    pass

# Store last known connection status
plc_status = {
    "ip": None,
    "port": None,
    "connected": False,
    "last_checked": None,
    "error": None
}

def poll_plc(ip, port, interval=0.01): # Reduced interval for faster response
    """Background polling to verify PLC connection status by reading X0 and monitoring Y2 for trigger."""
    global plc_status
    sock = None
    last_y2 = 0
    
    while True:
        try:
            # Reconnect if socket is closed or lost
            if sock is None:
                try:
                    print(f"[PLC POLL] Attempting to connect to {ip}:{port}...")
                    sock = mc.open_socket(ip, port)
                    print(f"[PLC POLL] Socket opened successfully.")
                except Exception as e:
                    print(f"[PLC POLL] Connection failed: {e}")
                    # Connection failed
                    plc_status.update({
                        "ip": ip,
                        "port": port,
                        "connected": False,
                        "last_checked": time.time(),
                        "error": str(e)
                    })
                    time.sleep(2) # Wait longer between reconnections
                    continue

            # Check connection by reading X0 and Y2
            try:
                # Read X0 for status check
                resp = mc.read_bit(sock, "X0", 1)
                
                # Check for error responses
                if isinstance(resp, list):
                    # Only log transition to avoid spam
                    if not plc_status["connected"]:
                        print(f"[PLC POLL] Connection verified/restored.")
                        
                    plc_status.update({
                        "ip": ip,
                        "port": port,
                        "connected": True,
                        "last_checked": time.time(),
                        "error": None
                    })
                    
                    # POLL Y2 FOR TRIGGER
                    # We do this only if connected
                    resp_y2 = mc.read_bit(sock, "Y2", 1)
                    if isinstance(resp_y2, list) and len(resp_y2) > 0:
                        current_y2 = resp_y2[0]
                        
                        # Detect Rising Edge (0 -> 1)
                        if current_y2 == 1 and last_y2 == 0:
                            print(f"[PLC POLL] Y2 Rising Edge Detected! Triggering Capture.")
                            
                            # Generate filename
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            # Save in a 'captured_images' folder in the backend root
                            # Assuming this file is in backend/plc/
                            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                            save_dir = os.path.join(backend_dir, "captured_images")
                            filepath = os.path.join(save_dir, f"capture_{timestamp}.jpg")
                            
                            # Trigger Save
                            try:
                                if camera_manager.save_current_frame(filepath):
                                    print(f"[PLC POLL] Image saved successfully: {filepath}")
                                    mc.write_bit(sock, "M40", 1)
                                    time.sleep(0.1) 
                                    mc.write_bit(sock, "M40", 0)  
                                else:
                                    print(f"[PLC POLL] Failed to save image. (Is camera running?)")
                            except Exception as cam_err:
                                print(f"[PLC POLL] Camera trigger error: {cam_err}")
                                
                        last_y2 = current_y2
                        
                else:
                    print(f"[PLC POLL] Unexpected response format: {resp}")
                    # Verification failed
                    raise Exception(f"Unexpected response: {resp}")

            except Exception as e:
                print(f"[PLC POLL] Read failed: {e}")
                # Read failed, mark as disconnected and close socket to force reconnect
                raise e

        except Exception as e:
            plc_status.update({
                "ip": ip,
                "port": port,
                "connected": False,
                "last_checked": time.time(),
                "error": str(e)
            })
            if sock:
                try:
                    sock.close()
                except:
                    pass
            sock = None
            
        time.sleep(interval)

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class PLCConnectRequest(BaseModel):
    ip: str
    port: int

@router.post("/plc/connect")
async def plc_connect(req: PLCConnectRequest):
    """Check PLC connectivity by attempting TCP connection using rk_mcprotocol and save settings."""
    try:
        # First attempt a quick connection check
        s = mc.open_socket(req.ip, req.port)
        # Try a dummy read to ensure it's a valid PLC talking MC protocol
        mc.read_bit(s, "X0", 1)
        s.close()
        
        # Save settings
        save_plc_settings(req.ip, req.port)
        
        # Start polling thread if not already started or if IP/port changed
        global plc_status
        if plc_status["ip"] != req.ip or plc_status["port"] != req.port:
            plc_status["ip"] = req.ip
            plc_status["port"] = req.port
            # In a real app we might want to stop the old thread, but for now we just start a new one
            # The proper way would be to have a single thread that reads params from the global dict
            # For simplicity, we'll assume one active PLC connection at a time.
            polling_thread = threading.Thread(target=poll_plc, args=(req.ip, req.port), daemon=True)
            polling_thread.start()
            
        plc_status["connected"] = True
        plc_status["last_checked"] = time.time()
        plc_status["error"] = None
        return {"connected": True}
    except Exception as e:
        print(f"[PLC CONNECT ERROR] Endpoint exception: {e}")
        plc_status["connected"] = False
        plc_status["last_checked"] = time.time()
        plc_status["error"] = str(e)
        return {"connected": False, "error": str(e)}

# On startup, load last PLC settings and start polling if available
settings = load_plc_settings()
if settings and settings.get("ip") and settings.get("port"):
    plc_status["ip"] = settings["ip"]
    plc_status["port"] = settings["port"]
    polling_thread = threading.Thread(target=poll_plc, args=(settings["ip"], settings["port"]), daemon=True)
    polling_thread.start()

# Endpoint to get current PLC connection status
@router.get("/plc/status")
async def get_plc_status():
    """Return the last known PLC connection status."""
    return {
        "ip": plc_status["ip"],
        "port": plc_status["port"],
        "connected": plc_status["connected"],
        "last_checked": plc_status["last_checked"],
        "error": plc_status["error"]
    }
