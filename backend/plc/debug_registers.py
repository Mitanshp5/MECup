from connection import manager
import time

def debug_registers():
    print("Connecting to PLC...")
    if not manager.connect():
        print(f"Failed to connect: {manager.last_error}")
        return

    print("Reading D40 - D80 (42 words)...")
    try:
        # Read using the method we suspect is causing issues
        values = manager.read_sign_word("D40", 42)
        
        print(f"Read {len(values)} values.")
        
        # Print valid indices mapping
        print("\n--- Register Dump ---")
        for i, val in enumerate(values):
            reg = 40 + i
            print(f"Index {i:2d} | D{reg}: {val}")
            
            # Highlight suspected X_Current registers
            if reg == 50:
                print(f"          ^^^^ D50 (X Current) ^^^^")
            if reg == 45:
                 print(f"          ^^^^ D45 (User Tried) ^^^^")

    except Exception as e:
        print(f"Error reading registers: {e}")

if __name__ == "__main__":
    # Ensure settings are loaded or defaults are used
    # manager.configure("192.168.1.5", 8000) # Use actual IP if known, otherwise relies on defaults/loaded settings
    
    # We need to load settings if they aren't hardcoded in the class
    import json
    import os
    try:
        with open("backend/plc/plc_settings.json", "r") as f:
            settings = json.load(f)
            print(f"Loaded settings: {settings}")
            manager.configure(settings["ip"], settings["port"])
    except Exception as e:
        print(f"Could not load settings: {e}. Using defaults if any.")

    debug_registers()
