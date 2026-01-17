import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    print("Importing settings...")
    from backend.camera import settings
    print("Importing camera_manager...")
    from backend.camera import camera_manager
    print("Importing endpoints...")
    from backend.camera import endpoints
    print("ALL IMPORTS SUCCESSFUL")
except ImportError as e:
    print(f"IMPORT FAILED: {e}")
except Exception as e:
    print(f"ERROR: {e}")
