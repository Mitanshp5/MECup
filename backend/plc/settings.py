import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')

def save_plc_settings(ip, port):
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                pass
    
    settings['plc_ip'] = ip
    settings['plc_port'] = port

    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def load_plc_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                data = json.load(f)
                return {'ip': data.get('plc_ip'), 'port': data.get('plc_port')}
            except json.JSONDecodeError:
                return None
    return None

def save_stitch_scale(scale):
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                pass
    
    settings['stitch_scale'] = scale

    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def load_stitch_scale():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                data = json.load(f)
                return data.get('stitch_scale', 18.0)
            except json.JSONDecodeError:
                return 18.0
    return 18.0
