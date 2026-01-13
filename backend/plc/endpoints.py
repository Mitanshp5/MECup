# ...existing code...
import threading
import time
import struct
from .settings import save_plc_settings, load_plc_settings
# Store last known connection status
plc_status = {
    "ip": None,
    "port": None,
    "connected": False,
    "last_checked": None,
    "error": None
}

def poll_plc(ip, port, interval=2):
    """Background polling to verify PLC connection status by reading D0."""
    global plc_status
    sock = None
    while True:
        try:
            # Only reconnect if not already connected
            if sock is None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((ip, port))
            # Read D0 using MC Protocol (simple binary request)
            # This is a minimal MC Protocol request for FX5U, adjust as needed for your PLC
            mc_read_d0 = b'\x50\x00\x00\xff\x03\xff\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            sock.send(mc_read_d0)
            resp = sock.recv(1024)
            if resp:
                plc_status.update({
                    "ip": ip,
                    "port": port,
                    "connected": True,
                    "last_checked": time.time(),
                    "error": None
                })
            else:
                plc_status.update({
                    "ip": ip,
                    "port": port,
                    "connected": False,
                    "last_checked": time.time(),
                    "error": "No response from PLC"
                })
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
import socket

router = APIRouter()

class PLCConnectRequest(BaseModel):
    ip: str
    port: int

@router.post("/plc/connect")
async def plc_connect(req: PLCConnectRequest):
    """Check PLC connectivity by attempting TCP connection and save settings."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((req.ip, req.port))
        s.close()
        # Save settings
        save_plc_settings(req.ip, req.port)
        # Start polling thread if not already started or if IP/port changed
        global plc_status
        if plc_status["ip"] != req.ip or plc_status["port"] != req.port:
            plc_status["ip"] = req.ip
            plc_status["port"] = req.port
            polling_thread = threading.Thread(target=poll_plc, args=(req.ip, req.port), daemon=True)
            polling_thread.start()
        plc_status["connected"] = True
        plc_status["last_checked"] = time.time()
        plc_status["error"] = None
        return {"connected": True}
    except Exception as e:
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
