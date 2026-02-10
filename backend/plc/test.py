
import sys
import os
import time
import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)

if backend_dir not in sys.path:
    sys.path.append(backend_dir)

try:
    import mc_protocol_fixed as mc
except ImportError:
    try:
        from . import mc_protocol_fixed as mc
    except ImportError:
        print("Error: Could not import mc_protocol_fixed. Make sure it's in the same directory.")
        sys.exit(1)

CAMERA_AVAILABLE = False
try:
    from camera.camera_manager import camera_manager
    CAMERA_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import CameraManager ({e}). Running in PLC-only mode.")

PLC_IP = '192.168.1.30'
PLC_PORT = 5000
REGISTER_X = "D12"
UNIT_TO_MM = 0.0001
TRIGGER_INTERVAL_MM = 15.0
TOLERANCE_MM = 1.0 

def main():
    print("--- PLC X-Axis Monitor & Camera Capture ---")
    print(f"Target: Every {TRIGGER_INTERVAL_MM} mm | Register: {REGISTER_X}")
    plc = None
    while not plc:
        try:
            print(f"Connecting to PLC ({PLC_IP}:{PLC_PORT})...")
            plc = mc.open_socket(PLC_IP, PLC_PORT)
            print("PLC Connected!")
        except Exception as e:
            print(f"Connection failed: {e}. Retrying in 2s...")
            time.sleep(2)

    if CAMERA_AVAILABLE:
        print("Initializing Camera...")
        if not camera_manager.open_device():
            print("Failed to open camera. Continuing in dry-run mode.")
        else:
            if not camera_manager.start_grabbing():
                print("Failed to start grabbing. Continuing in dry-run mode.")
            else:
                print("Camera grabbing started.")

    timestamp_session = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join(backend_dir, "captured_images", f"monitor_{timestamp_session}")
    os.makedirs(save_dir, exist_ok=True)
    print(f"Saving images to: {save_dir}")

    last_triggered_multiple = None
    
    try:
        while True:
            try:
                resp = mc.read_sign_Dword(plc, REGISTER_X, 1, True)
                
                if isinstance(resp, str):
                    print(f"\rPLC Read Error: {resp}    ", end="")
                    time.sleep(0.5)
                    continue

                if not resp:
                    continue

                raw_val = resp[0]
                current_mm = raw_val * UNIT_TO_MM
                
                multiple_index = round(current_mm / TRIGGER_INTERVAL_MM)
                target_mm = multiple_index * TRIGGER_INTERVAL_MM
                
                diff = abs(current_mm - target_mm)
                
                is_in_zone = diff <= TOLERANCE_MM
                
                status = f"Pos: {current_mm:7.2f} mm | Target: {target_mm:7.2f} | Diff: {diff:.2f}"
                print(status, end='\r')

                if is_in_zone:
                    if multiple_index != last_triggered_multiple:
                        print(f"\n[TRIGGER] Reached {target_mm} mm (Actual: {current_mm:.3f})")
                        
                        filename = f"img_{datetime.datetime.now().strftime('%H%M%S_%f')}_x{target_mm:.0f}.jpg"
                        filepath = os.path.join(save_dir, filename)
                        
                        saved = False
                        if CAMERA_AVAILABLE and camera_manager.is_grabbing:
                            saved = camera_manager.save_current_frame(filepath)
                            if saved:
                                print(f"   -> Saved: {filename}")
                            else:
                                print(f"   -> Failed to save frame")
                        else:
                            print(f"   -> [Dry Run] Would save to {filename}")
                        
                        last_triggered_multiple = multiple_index
                        print(f"Waiting for next multiple...")
                
                time.sleep(0.05)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"\nLoop Error: {e}")
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if CAMERA_AVAILABLE:
            camera_manager.stop_grabbing()
            camera_manager.close_device()
        try:
            plc.close()
        except:
            pass
        print("Done.")

if __name__ == "__main__":
    main()
