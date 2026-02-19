
import urllib.request
import json
import sqlite3
import os

try:
    print("Checking API endpoint...")
    with urllib.request.urlopen('http://localhost:5001/servo/history') as response:
        if response.status == 200:
            data = json.loads(response.read().decode())
            print("API Response Stats:", json.dumps(data.get('stats'), indent=2))
        else:
            print(f"API Failed: {response.status}")

    print("\nChecking Database...")
    # Try multiple paths
    possible_paths = [
        os.path.join(os.getcwd(), 'backend', 'mecup.db'),
        os.path.join(os.getcwd(), 'mecup.db'),
        r'c:\MyStuff\VS\MECup\backend\mecup.db'
    ]
    
    db_path = None
    for p in possible_paths:
        if os.path.exists(p):
            db_path = p
            break
            
    if db_path:
        print(f"Found DB at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM servo_daily_stats")
            rows = cursor.fetchall()
            print("DB Rows Count:", len(rows))
            if rows:
                print("First row sample:", rows[0])
        except Exception as dbe:
            print(f"DB Query Failed: {dbe}")
        conn.close()
    else:
        print(f"Database not found. Checked: {possible_paths}")

except Exception as e:
    print(f"Error: {e}")
