
import uvicorn
import os
import psutil
import datetime
import time

def get_system_resources():
    print("Testing system resources...")
    try:
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        uptime = int(time.time() - psutil.boot_time())
        print(f"Success: CPU={cpu}, Mem={memory}, Disk={disk}, Uptime={uptime}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_system_resources()
