import requests
import time

BASE_URL = "http://localhost:5001"

def check_backend():
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=2)
        print(f"Backend Health: {resp.status_code} - {resp.json()}")
        return True
    except Exception as e:
        print(f"Backend Health: FAILED - {e}")
        return False

def check_camera_status():
    try:
        resp = requests.get(f"{BASE_URL}/camera/status", timeout=2)
        print(f"Camera Status: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"Camera Status: FAILED - {e}")

def api_connect_camera():
    try:
        print("Attempting to connect camera via API...")
        resp = requests.post(f"{BASE_URL}/camera/connect", timeout=5)
        print(f"Connect Response: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"Connect Request: FAILED - {e}")

if __name__ == "__main__":
    print("Checking system status...")
    if check_backend():
        check_camera_status()
        api_connect_camera()
        time.sleep(1)
        check_camera_status()
    else:
        print("Backend appears down.")
