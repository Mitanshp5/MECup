import requests
import time
import statistics

BASE_URL = "http://localhost:5001"

def test_endpoint(method, endpoint, payload=None, label=""):
    url = f"{BASE_URL}{endpoint}"
    print(f"\nTesting {label} ({method} {url})...")
    
    latencies = []
    
    for i in range(10):
        start_time = time.time()
        try:
            if method == "POST":
                response = requests.post(url, json=payload)
            else:
                response = requests.get(url)
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # We don't care if it returns 200 or 503 (PLC disconnected), we just want to know the server response time.
            # But we should note if it failed to connect entirely.
            
            latencies.append(duration_ms)
            print(f"  Request {i+1}: {duration_ms:.2f} ms (Status: {response.status_code})")
            
        except requests.exceptions.ConnectionError:
            print("  Connection Error: Make sure the backend server is running on port 5001.")
            return

    if latencies:
        print(f"Stats for {label}:")
        print(f"  Min: {min(latencies):.2f} ms")
        print(f"  Max: {max(latencies):.2f} ms")
        print(f"  Avg: {statistics.mean(latencies):.2f} ms")

if __name__ == "__main__":
    print(f"Checking backend at {BASE_URL}...")
    try:
        # Check health
        requests.get(f"{BASE_URL}/api/health", timeout=2)
        print("Backend is up.")
        
        # Test POST Servo Speeds
        test_endpoint(
            "POST", 
            "/servo/speeds", 
            payload={"x": 500, "y": 500, "z": 500}, 
            label="Servo Speed Update"
        )
        
        # Test GET PLC Status (as a reference)
        test_endpoint(
            "GET", 
            "/plc/status", 
            label="PLC Status Check"
        )
        
    except requests.exceptions.ConnectionError:
        print("Could not connect to backend. Please start the server using 'python backend/main.py'.")
