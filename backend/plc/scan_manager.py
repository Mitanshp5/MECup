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
        
        # New State Fields
        self.status = "IDLE" # IDLE, RUNNING, PAUSED
        self.scan_id = None
        self.model_type = "white" # white, black
        
        # Thread safety locks
        self.state_lock = threading.Lock()
        self._initialized = True
        
        # Configure logging if not already done
        logging.basicConfig(
            filename=os.path.join(os.path.dirname(os.path.dirname(__file__)), "error_log.txt"),
            level=logging.ERROR,
            format='%(asctime)s [%(levelname)s] %(message)s'
        )

    def start_new_scan(self, username, base_dir, model_type="white"):
        """Initialize a new scan or resume existing one."""
        with self.state_lock:
            
            # If already running, do nothing
            if self.status == "RUNNING":
                return self.current_batch_folder, self.scan_id

            self.current_scan_user = username
            self.model_type = model_type
            
            # If IDLE or just starting fresh, create new folders
            if self.status == "IDLE":
                self.count = 1
                self.county = 1
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                self.scan_id = f"scan_{timestamp}"
                self.current_batch_folder = os.path.join(base_dir, "captured_images", self.scan_id)
                os.makedirs(self.current_batch_folder, exist_ok=True)
            
            # Switch to RUNNING (Resume or Start)
            self.status = "RUNNING"
            logging.info(f"Scan Started/Resumed: {self.scan_id} ({self.model_type})")
            
            return self.current_batch_folder, self.scan_id

    def pause_scan(self):
        """Pause the current scan."""
        with self.state_lock:
            if self.status == "RUNNING":
                self.status = "PAUSED"
                logging.info(f"Scan Paused: {self.scan_id}")

    def reset_cycle(self):
        """Reset counters and fully reset scan state (User must start fresh)."""
        with self.state_lock:
            self.count = 1
            self.county = 1
            self.current_batch_folder = None
            self.scan_id = None
            self.status = "IDLE"
            # model_type remains as last selected or default
            logging.info("Cycle Fully Reset (IDLE)")

    def increment_counters(self):
        """Thread-safe increment of counters."""
        with self.state_lock:
            if self.status == "RUNNING":
                self.count += 1

    def increment_county(self):
        """Thread-safe increment of Y counter."""
        with self.state_lock:
            if self.status == "RUNNING":
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
                "click": self.click,
                "status": self.status,
                "scan_id": self.scan_id,
                "model_type": self.model_type
            }

    def get_current_folder(self):
        with self.state_lock:
            return self.current_batch_folder

# Global instance
scan_session = ScanSession()
