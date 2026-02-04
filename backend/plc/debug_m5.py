import socket
import time
import sys
import os

# Add parent directory to path to find rk_mcprotocol if needed, 
# or use the fixed one if in same dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import mc_protocol_fixed as mc
except ImportError:
    try:
        import rk_mcprotocol as mc
    except ImportError:
        print("Could not import mc_protocol. Ensure it is installed or in path.")
        sys.exit(1)

IP = '192.168.1.30'
PORT = 5000

print(f"Connecting to {IP}:{PORT}...")
try:
    s = mc.open_socket(IP, PORT)
    print("Connected.")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

try:
    print("Attempting to write M5 = 1...")
    mc.write_bit(s, 'M5', [1])
    print("Write M5=1 sent.")
    
    time.sleep(0.5)
    
    print("Reading M5 status...")
    status = mc.read_bit(s, 'M5', 1)
    print(f"M5 Status: {status}")

    time.sleep(1)

    print("Attempting to write M5 = 0...")
    mc.write_bit(s, 'M5', [0])
    print("Write M5=0 sent.")
    
    time.sleep(0.5)
    
    print("Reading M5 status again...")
    status = mc.read_bit(s, 'M5', 1)
    print(f"M5 Status: {status}")

    s.close()
    print("Done.")

except Exception as e:
    print(f"Operation failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        s.close()
    except:
        pass
