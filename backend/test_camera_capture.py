import sys
import os
import time

# Ensure we can import modules from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from camera.camera_manager import camera_manager
    print("[TEST] Successfully imported camera_manager")
except ImportError as e:
    print(f"[TEST] Failed to import camera_manager: {e}")
    # Try adjusting path if running from backend root
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "camera"))
    try:
        from camera_manager import camera_manager
        print("[TEST] Successfully imported camera_manager (adjusted path)")
    except ImportError as e2:
        print(f"[TEST] CRITICAL: Could not import camera_manager: {e2}")
        sys.exit(1)

def test_capture():
    print("[TEST] Enumerating devices...")
    devices = camera_manager.enum_devices()
    if not devices:
        print("[TEST] No devices found. connect a camera.")
        return

    print(f"[TEST] Found devices: {devices}")
    
    print("[TEST] Opening first device...")
    if not camera_manager.open_device(0):
        print("[TEST] Failed to open device.")
        return
    
    print("[TEST] Starting grab...")
    if not camera_manager.start_grabbing():
        print("[TEST] Failed to start grabbing.")
        camera_manager.close_device()
        return
    
    # Wait for frames to arrive
    print("[TEST] Waiting 3 seconds for frames...")
    time.sleep(3)
    
    if camera_manager.current_frame:
        print(f"[TEST] Frame available. Size: {len(camera_manager.current_frame)} bytes")
        
        filename = "test_capture_standalone.jpg"
        filepath = os.path.abspath(filename)
        
        print(f"[TEST] Attempting to save to {filepath}...")
        if camera_manager.save_current_frame(filepath):
            print("[TEST] SUCCESS: Image saved successfully.")
            if os.path.exists(filepath):
                 print(f"[TEST] Verified: File exists at {filepath}")
            else:
                 print(f"[TEST] WARNING: save_current_frame returned True but file not found?")
        else:
            print("[TEST] FAILURE: save_current_frame returned False.")
    else:
        print("[TEST] FAILURE: No frame captured after 3 seconds.")
        
    print("[TEST] Cleaning up...")
    camera_manager.close_device()
    print("[TEST] Done.")

if __name__ == "__main__":
    test_capture()
