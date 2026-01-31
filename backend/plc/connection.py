import threading
import socket
import time
import rk_mcprotocol as mc

class PLCManager:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PLCManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._sock = None
        self._socket_lock = threading.RLock()
        self.ip = None
        self.port = None
        self.connected = False
        self.last_error = None
        self.last_checked = None

    def configure(self, ip, port):
        """Update connection settings. Forces reconnect if changed."""
        with self._socket_lock:
            if self.ip != ip or self.port != port:
                self.ip = ip
                self.port = port
                self.disconnect()  # will reconnect on next usage or poll

    def disconnect(self):
        with self._socket_lock:
            if self._sock:
                try:
                    self._sock.close()
                except:
                    pass
                self._sock = None
            self.connected = False

    def connect(self):
        """Establish connection if not already connected."""
        with self._socket_lock:
            if self._sock:
                return True
            
            if not self.ip or not self.port:
                self.connected = False
                self.last_error = "PLC IP/Port not configured"
                return False

            try:
                print(f"[PLC MANAGER] Connecting to {self.ip}:{self.port}...")
                self._sock = mc.open_socket(self.ip, self.port)
                self.connected = True
                self.last_error = None
                self.last_checked = time.time()
                print(f"[PLC MANAGER] Connected.")
                return True
            except Exception as e:
                self.connected = False
                self.last_error = str(e)
                self.last_checked = time.time()
                print(f"[PLC MANAGER] Connection failed: {e}")
                return False

    def read_bit(self, device, count=1):
        with self._socket_lock:
            if not self.connect():
                raise Exception(f"PLC disconnected: {self.last_error}")
            try:
                return mc.read_bit(self._sock, device, count)
            except Exception as e:
                self.disconnect()
                raise e

    def write_bit(self, device, value_list):
        """
        Write a list of bits (0 or 1) to the devise.
        value_list must be a list, e.g. [1] or [1, 0]
        """
        with self._socket_lock:
            if not self.connect():
                raise Exception(f"PLC disconnected: {self.last_error}")
            try:
                mc.write_bit(self._sock, device, value_list)
            except Exception as e:
                self.disconnect()
                raise e

    def write_sign_dword(self, device, value_list):
        with self._socket_lock:
            if not self.connect():
                raise Exception(f"PLC disconnected: {self.last_error}")
            try:
                mc.write_sign_dword(self._sock, device, value_list)
            except Exception as e:
                self.disconnect()
                raise e

    def read_sign_dword(self, device, count=1):
        with self._socket_lock:
            if not self.connect():
                raise Exception(f"PLC disconnected: {self.last_error}")
            try:
                return mc.read_sign_dword(self._sock, device, count)
            except Exception as e:
                self.disconnect()
                raise e

    def get_status(self):
        return {
            "ip": self.ip,
            "port": self.port,
            "connected": self.connected,
            "error": self.last_error,
            "last_checked": self.last_checked
        }
