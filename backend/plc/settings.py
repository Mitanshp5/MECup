import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'plc_settings.json')

def save_plc_settings(ip, port):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump({'ip': ip, 'port': port}, f)

def load_plc_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return None
