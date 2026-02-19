
import sqlite3
import os
import datetime

db_path = os.path.join(os.getcwd(), 'backend', 'mecup.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check table first
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='servo_daily_stats'")
    if not cursor.fetchone():
        print("Table 'servo_daily_stats' does not exist! Running create...")
        # Minimal create for test
        cursor.execute('''CREATE TABLE IF NOT EXISTS servo_daily_stats (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME,
            axis VARCHAR,
            metric VARCHAR,
            min_val FLOAT,
            min_time DATETIME,
            max_val FLOAT,
            max_time DATETIME
        )''')
    
    # Insert for all axes
    now = datetime.datetime.now()
    axes = ['x', 'y', 'z']
    metrics = ['current', 'torque', 'pk_torque', 'load'] # Check exact metric names in endpoints.py: current, torque, peak, load
    
    # In endpoints.py: metrics are ['current', 'torque', 'peak', 'load', 'health']
    
    for axis in axes:
        cursor.execute(f"DELETE FROM servo_daily_stats WHERE axis='{axis}'")
        for metric in ['current', 'torque', 'peak', 'load']:
            cursor.execute('''
                INSERT INTO servo_daily_stats (axis, metric, min_val, max_val, timestamp, min_time, max_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (axis, metric, 5.0, 80.0, now, now, now))
            
    conn.commit()
    print("Inserted dummy stats for X, Y, Z axes")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
