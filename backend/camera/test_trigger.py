
import sys
import os
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from camera.camera_manager import camera_manager

def test_save_trigger():
    print("Testing Save Trigger Logic...")
    
    # Mock current_frame since we don't have a camera
    camera_manager.current_frame = b"fake_jpeg_data"
    
    timestamp = "test_timestamp"
    # Save in a 'captured_images' folder in the backend root
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    save_dir = os.path.join(backend_dir, "captured_images")
    filepath = os.path.join(save_dir, f"capture_{timestamp}.txt") # Use .txt for fake data test
    
    print(f"Attempting to save to: {filepath}")
    
    if camera_manager.save_current_frame(filepath):
        print("Success! Image (fake) saved.")
        if os.path.exists(filepath):
            print("File verified on disk.")
            with open(filepath, 'rb') as f:
                content = f.read()
                print(f"Content: {content}")
            os.remove(filepath) # Cleanup
            print("Cleanup complete.")
        else:
            print("Error: File returned success but not found on disk.")
    else:
        print("Failed to save image.")

if __name__ == "__main__":
    test_save_trigger()
