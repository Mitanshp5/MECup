from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
import rk_mcprotocol as mc
from plc.endpoints import plc_status

router = APIRouter()

class ServoSpeedRequest(BaseModel):
    x: int = Field(..., ge=0, le=50000, description="Speed for X axis (D2)")
    y: int = Field(..., ge=0, le=50000, description="Speed for Y axis (D0)")
    z: int = Field(..., ge=0, le=50000, description="Speed for Z axis (D4)")

class ServoEnableRequest(BaseModel):
    enable: bool

class ServoMoveRequest(BaseModel):
    command: str

# Motion Command Map
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

def get_plc_socket():
    if not plc_status.get("connected"):
        raise HTTPException(status_code=503, detail="PLC is not connected.")
    try:
        return mc.open_socket(plc_status["ip"], plc_status["port"])
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to PLC: {e}")

@router.post("/servo/speeds")
async def set_servo_speeds(speeds: ServoSpeedRequest) -> Dict[str, str]:
    """
    Set servo speeds:
    - X Axis -> D2
    - Y Axis -> D0
    - Z Axis -> D4
    """
    sock = get_plc_socket()
    try:
        # X Speed -> D2
        mc.write_sign_dword(sock, "D2", [speeds.x]*1)
        # Y Speed -> D0
        mc.write_sign_dword(sock, "D0", [speeds.y]*1)
        # Z Speed -> D4
        mc.write_sign_dword(sock, "D4", [speeds.z]*1)
        
        print(f"[SERVO] Speeds set: X({speeds.x})->D2, Y({speeds.y})->D0, Z({speeds.z})->D4")
        return {"status": "success", "message": "Speeds updated"}
    except Exception as e:
        print(f"[SERVO ERROR] Failed to write speeds: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        sock.close()

@router.post("/servo/enable")
async def enable_servo(req: ServoEnableRequest) -> Dict[str, str]:
    """
    Enable/Disable Servo (M0).
    """
    sock = get_plc_socket()
    try:
        val = 1 if req.enable else 0
        mc.write_bit(sock, "M0", val)
        status = "Enabled" if req.enable else "Disabled"
        print(f"[SERVO] {status} (M0={val})")
        return {"status": "success", "message": f"Servo {status}"}
    except Exception as e:
        print(f"[SERVO ERROR] Failed to toggle servo: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        sock.close()

@router.post("/servo/move")
async def trigger_motion(req: ServoMoveRequest) -> Dict[str, str]:
    """
    Trigger specific motion action.
    Command must be one of:
    - x_left_17, x_right_17, x_home
    - y_back_12.5, y_fwd_12.5
    - z_up_5, z_down_5, z_up_jog, z_down_jog
    
    This acts as a momentary trigger (ON). Assuming PLC handles the latch or it's a 'kick'.
    If it needs to be OFF, the frontend should send another request or we pulse it here.
    For now, we just turn it ON (1).
    """
    if req.command not in MOTION_COMMANDS:
        raise HTTPException(status_code=400, detail=f"Invalid command. Valid: {list(MOTION_COMMANDS.keys())}")
    
    bit_addr = MOTION_COMMANDS[req.command]
    sock = get_plc_socket()
    try:
        # Trigger ON
        mc.write_bit(sock, bit_addr, 1)
        print(f"[SERVO] Triggered {req.command} ({bit_addr}=1)")
        time.sleep(4)
        mc.write_bit(sock, bit_addr, 0)
        
        return {"status": "success", "message": f"Triggered {req.command}"}
    except Exception as e:
        print(f"[SERVO ERROR] Failed to trigger {req.command}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        sock.close()
