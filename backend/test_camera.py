import sys
import os
import time

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from camera.camera_manager import camera_manager
except ImportError:
    # If running from root project dir
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    from camera.camera_manager import camera_manager

print(f"MVCAM_COMMON_RUNENV: {os.environ.get('MVCAM_COMMON_RUNENV')}")

def main():
    print("Enumerating devices...")
    try:
        device_list = camera_manager.enum_devices()
    except Exception as e:
        print(f"Error enumerating devices: {e}")
        return

    print(f"Found {len(device_list)} devices")
    
    if not device_list:
        print("No devices found. Exiting.")
        return

    print("Opening first device...")
    if not camera_manager.open_device(0):
        print("Failed to open device")
        return

    print("Starting grabbing...")
    if not camera_manager.start_grabbing():
        print("Failed to start grabbing")
        camera_manager.close_device()
        return

    print("Checking for frames...")
    # Give it some time to fill buffer
    for i in range(10):
        frame = camera_manager.get_latest_frame_jpeg()
        if frame:
            print(f"Frame received! Size: {len(frame)} bytes")
            with open("test_capture.jpg", "wb") as f:
                f.write(frame)
            print("Saved test_capture.jpg")
            break
        else:
            print(f"Attempt {i+1}: No frame yet...")
            time.sleep(0.5)
    else: # no break
        print("No frames received after 5 seconds.")

    print("Closing device...")
    camera_manager.close_device()

if __name__ == "__main__":
    main()
