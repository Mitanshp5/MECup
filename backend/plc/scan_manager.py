import threading
import os
import datetime
import logging

class ScanSession:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ScanSession, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.count = 1
        self.county = 1
        self.current_batch_folder = None
        self.current_scan_user = "operator"
        self.click = 0 # Used for rising edge detection logic
        
        # Thread safety locks
        self.state_lock = threading.Lock()
        self._initialized = True
        
        # Configure logging if not already done
        logging.basicConfig(
            filename=os.path.join(os.path.dirname(os.path.dirname(__file__)), "error_log.txt"),
            level=logging.ERROR,
            format='%(asctime)s [%(levelname)s] %(message)s'
        )

    def start_new_scan(self, username, base_dir):
        """Initialize a new scan session properly."""
        with self.state_lock:
            self.current_scan_user = username
            self.count = 1
            self.county = 1
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_batch_folder = os.path.join(base_dir, "captured_images", f"scan_{timestamp}")
            os.makedirs(self.current_batch_folder, exist_ok=True)
            
            return self.current_batch_folder, timestamp

    def reset_cycle(self):
        """Reset counters and clear batch folder reference."""
        with self.state_lock:
            self.count = 1
            self.county = 1
            self.current_batch_folder = None
            logging.info("Cycle reset initiated")

    def increment_counters(self):
        """Thread-safe increment of counters."""
        with self.state_lock:
            self.count += 1

    def increment_county(self):
        """Thread-safe increment of Y counter."""
        with self.state_lock:
            self.county += 1
            self.count = 1

    def set_click(self, value):
        with self.state_lock:
            self.click = value

    def get_state(self):
        """Return a snapshot of the current state."""
        with self.state_lock:
            return {
                "count": self.count,
                "county": self.county,
                "batch_folder": self.current_batch_folder,
                "click": self.click
            }

    def get_current_folder(self):
        with self.state_lock:
            return self.current_batch_folder

# Global instance
scan_session = ScanSession()
