import threading
import time
import socket
import datetime
import os
# Import the library directly
import rk_mcprotocol as mc
from .settings import save_plc_settings, load_plc_settings
# Import camera manager for triggering captures
# Import camera manager for triggering captures
try:
    # Try absolute import (if running from backend root)
    from camera.camera_manager import camera_manager
    print("[PLC] Successfully imported camera_manager from camera package")
except ImportError:
    try:
        # Try relative import (fallback)
        from ..camera.camera_manager import camera_manager
        print("[PLC] Successfully imported camera_manager from relative path")
    except ImportError as e:
        print(f"[PLC] Warning: Could not import camera_manager: {e}")
        camera_manager = None

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
                        if camera_manager:
                            try:
                                if camera_manager.save_current_frame(filepath):
                                    print(f"[PLC POLL] Image saved successfully: {filepath}")
                                    time.sleep(1)
                                    # Send feedback to PLC
                                    try:
                                        # User confirmed list format is correct: [1]*1
                                        mc.write_bit(sock, "M77", [1]*1) 
                                        print(f"[PLC POLL] Sent M77 feedback (ON)")
                                    except Exception as write_err:
                                        print(f"[PLC POLL] Failed to write M77 feedback: {write_err}")

                                else:
                                    print(f"[PLC POLL] Failed to save image. Camera returned False.")
                            except Exception as cam_err:
                                print(f"[PLC POLL] Camera trigger error: {cam_err}")
                        else:
                            print(f"[PLC POLL] Camera manager not available. Cannot save image.")
                                
                                
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
    timeout: int = 5000  # Default 5000ms

class PLCWriteRequest(BaseModel):
    device: str
    value: int
    
@router.post("/plc/write")
async def plc_write(req: PLCWriteRequest):
    """Write a value to a PLC device."""
    global plc_status
    ip = plc_status["ip"]
    port = plc_status["port"]
    
    if not ip or not port:
        return {"success": False, "error": "PLC settings not configured"}
        
    try:
        sock = mc.open_socket(ip, port)
        if req.value == 1:
            # We assume bit device for now based on request M5
            mc.write_bit(sock, req.device, 1)
        else:
            mc.write_bit(sock, req.device, 0)
        
        # If we want to simulate a momentary button (press and release), we might handle that in frontend or here with separate calls.
        # User asked to "turn on m5", implying setting it to 1. 
        # Usually scan start is a trigger. 
        
        sock.close()
        return {"success": True}
    except Exception as e:
         print(f"[PLC WRITE ERROR] {e}")
         return {"success": False, "error": str(e)}

@router.post("/plc/connect")
async def plc_connect(req: PLCConnectRequest):
    """Check PLC connectivity by attempting TCP connection using rk_mcprotocol and save settings."""
    try:
        # First attempt a quick connection check
        # rk_mcprotocol doesn't expose timeout in open_socket easily if it's just wrapping socket.create_connection
        # But we can try to set default socket timeout temporarily or inspect library.
        # Assuming we can't easily change library internals, we can try a raw socket check first with timeout.
        
        # Raw socket check for speed
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(req.timeout / 1000.0)
        sock.connect((req.ip, req.port))
        sock.close()

        # If raw check passes, try protocol check (fast)
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
