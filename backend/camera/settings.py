import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')

def save_camera_settings(exposure, gain):
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                pass
    
    settings['camera_exposure'] = exposure
    settings['camera_gain'] = gain

    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def load_camera_settings():
    defaults = {'exposure': 5000.0, 'gain': 0.0}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                data = json.load(f)
                return {
                    'exposure': data.get('camera_exposure', defaults['exposure']), 
                    'gain': data.get('camera_gain', defaults['gain'])
                }
            except json.JSONDecodeError:
                return defaults
    return defaults
