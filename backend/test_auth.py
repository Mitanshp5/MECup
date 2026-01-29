import asyncio
import httpx
import sys

BASE_URL = "http://localhost:5001"

async def test_auth_flow():
    print("--- Testing User Management & RBAC ---")
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Health Check
        try:
            resp = await client.get("/api/health")
            print(f"Health: {resp.status_code}")
        except Exception as e:
            print(f"Backend not running? {e}")
            return

        # 2. Login as Default Admin
        print("\n[TEST] Login Admin...")
        resp = await client.post("/token", data={"username": "admin", "password": "admin"})
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
        token_data = resp.json()
        print(f"Admin Token: {token_data['access_token'][:20]}...")
        admin_headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        # 3. Create a viewer user (Admin Action)
        print("\n[TEST] Creating Viewer User...")
        viewer_payload = {"username": "view1", "password": "123", "role": "VIEWER"}
        resp = await client.post("/users", json=viewer_payload, headers=admin_headers)
        if resp.status_code == 200:
            print("Viewer created.")
        elif resp.status_code == 400 and "already registered" in resp.text:
            print("Viewer already exists.")
        else:
            print(f"Failed to create viewer: {resp.text}")

        # 4. Login as Viewer
        print("\n[TEST] Login Viewer...")
        resp = await client.post("/token", data={"username": "view1", "password": "123"})
        if resp.status_code != 200:
             print(f"Viewer Login failed: {resp.text}")
             return
        viewer_token = resp.json()['access_token']
        viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

        # 5. Access Control Test: Servo Speed (Admin Only)
        print("\n[TEST] Viewer tries to set Servo Speed (Admin Only)...")
        resp = await client.post("/servo/speeds", json={"x": 100, "y": 100, "z": 100}, headers=viewer_headers)
        print(f"Response: {resp.status_code} (Expected 403)")
        
        # 6. Access Control Test: PLC Status (Open/Viewer)
        print("\n[TEST] Viewer tries to get PLC Status...")
        resp = await client.get("/plc/status", headers=viewer_headers)
        print(f"Response: {resp.status_code} (Expected 200)")

        # 7. Settings Migration Verification
        print("\n[TEST] Checking PLC Status (implies settings loaded)...")
        print(f"PLC Info: {resp.json()}")

if __name__ == "__main__":
    # check for httpx
    try:
        import httpx
    except ImportError:
        import os
        os.system("pip install httpx")
        import httpx
        
    asyncio.run(test_auth_flow())
