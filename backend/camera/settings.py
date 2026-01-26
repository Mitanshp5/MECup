import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')

def save_camera_settings(exposure, gain, auto_exposure=False):
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                pass
    
    settings['camera_exposure'] = exposure
    settings['camera_gain'] = gain
    settings['camera_auto_exposure'] = auto_exposure

    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def load_camera_settings():
    defaults = {'exposure': 5000.0, 'gain': 0.0, 'auto_exposure': False}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                data = json.load(f)
                return {
                    'exposure': data.get('camera_exposure', defaults['exposure']), 
                    'gain': data.get('camera_gain', defaults['gain']),
                    'auto_exposure': data.get('camera_auto_exposure', defaults['auto_exposure'])
                }
            except json.JSONDecodeError:
                return defaults
    return defaults
