import sys
try:
    import rk_mcprotocol as mc
except ImportError:
    print("Error: rk_mcprotocol is not installed.")
    print("Please run: pip install rk_mcprotocol")
    sys.exit(1)

def test_connection(ip, port):
    print(f"Attempting to connect to PLC at {ip}:{port}...")
    
    try:
        # Open connection using the library's function
        sock = mc.open_socket(ip, port)
        print("Successfully connected to PLC!")
        
        # Try to read a bit (e.g., X0) to verify data transfer
        # Reading 1 bit from X0
        print("Reading X0...")
        data = mc.read_bit(sock, "X0", 1)
        print(f"Read X0 value: {data}")
        
        sock.close()
        print("Connection closed.")
        return True
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    # You can change these values or pass them as arguments
    target_ip = "169.254.180.21" 
    target_port = 5000 
    
    if len(sys.argv) > 1:
        target_ip = sys.argv[1]
    if len(sys.argv) > 2:
        target_port = int(sys.argv[2])
        
    test_connection(target_ip, target_port)
