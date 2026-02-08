import sys
import os
import platform
import threading
import time
import ctypes
from ctypes import *

# Add MVS SDK to path
# Add MVS SDK to path
if platform.system() == 'Windows':
    # Try environment variable first
    mv_env = os.getenv('MVCAM_COMMON_RUNENV')
    if mv_env:
        sys.path.append(os.path.join(mv_env, "Samples", "Python", "MvImport"))
    
    # Also add the local MVSPython directory which is likely where the user has the SDK files
    # Based on file structure: c:\MyStuff\VS\MECup\MVSPython\MvImport
    # Assuming this file is in c:\MyStuff\VS\MECup\backend\camera\
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    mvs_python_path = os.path.join(project_root, "MVSPython", "MvImport")
    if os.path.exists(mvs_python_path):
        sys.path.append(mvs_python_path)

try:
    from MvCameraControl_class import *
    from CameraParams_header import *
    from MvErrorDefine_const import *
    SDK_AVAILABLE = True
    print("[Camera Manager] MVS SDK loaded successfully")
except ImportError as e:
    print(f"[Camera Manager] Error importing MVS SDK: {e}")
    SDK_AVAILABLE = False
    # Define dummy classes to prevent crash if SDK is missing during development
    class MvCamera: 
        def MV_CC_CreateHandle(self, *args): return 0
        def MV_CC_OpenDevice(self, *args): return 0
        def MV_CC_StartGrabbing(self): return 0
        def MV_CC_StopGrabbing(self): return 0
        def MV_CC_CloseDevice(self): return 0
        def MV_CC_DestroyHandle(self): return 0
        def MV_CC_EnumDevices(self, *args): return 0
        def MV_CC_GetOptimalPacketSize(self): return 0
        def MV_CC_SetIntValue(self, *args): return 0
        def MV_CC_GetIntValue(self, *args): return 0
        def MV_CC_GetFloatValue(self, *args): return 0
        def MV_CC_SetFloatValue(self, *args): return 0
        def MV_CC_SetEnumValue(self, *args): return 0
        def MV_CC_GetEnumValue(self, *args): return 0
        def MV_CC_GetImageBuffer(self, *args): return -1
        def MV_CC_FreeImageBuffer(self, *args): return 0
        def MV_CC_SaveImageEx2(self, *args): return -1

    class MV_CC_DEVICE_INFO_LIST: 
        nDeviceNum = 0
        pDeviceInfo = []
    class MV_FRAME_OUT_INFO_EX: pass
    class MV_FRAME_OUT: 
        stFrameInfo = MV_FRAME_OUT_INFO_EX()
        pBufAddr = None
    class MVCC_INTVALUE: nCurValue = 0
    class MVCC_FLOATVALUE: fCurValue = 0
    class MV_SAVE_IMAGE_PARAM_EX: pass
    
    # Define dummy constants
    MV_GIGE_DEVICE = 1
    MV_USB_DEVICE = 2
    MV_GENTL_CAMERALINK_DEVICE = 4
    MV_GENTL_CXP_DEVICE = 8
    MV_GENTL_XOF_DEVICE = 16
    MV_OK = 0
    MV_ACCESS_Exclusive = 1
    MV_Image_Jpeg = 2
    MV_EXPOSURE_AUTO_MODE_OFF = 0
    MV_EXPOSURE_AUTO_MODE_CONTINUOUS = 2
    MV_GAIN_MODE_OFF = 0


class CameraManager:
    def __init__(self):
        self.cam = MvCamera()
        self.device_list = MV_CC_DEVICE_INFO_LIST()
        self.n_sel_cam_index = 0
        self.is_open = False
        self.is_grabbing = False
        self.data_buf = None
        self.n_payload_size = 0
        self.lock = threading.Lock()
        self.current_frame = None
        self.st_out_frame = MV_FRAME_OUT()
        self.st_frame_info = MV_FRAME_OUT_INFO_EX()
        self.buf_save_image = None
        self.buf_save_image_len = 0

    def enum_devices(self):
        """Enumerate connected devices."""
        t_layer_type = MV_GIGE_DEVICE | MV_USB_DEVICE | MV_GENTL_CAMERALINK_DEVICE | MV_GENTL_CXP_DEVICE | MV_GENTL_XOF_DEVICE
        ret = MvCamera.MV_CC_EnumDevices(t_layer_type, self.device_list)
        if ret != 0:
            print(f"Enum devices failed! ret: {hex(ret)}")
            return []
        
        if self.device_list.nDeviceNum == 0:
            print("Find no device!")
            return []

        print(f"Find {self.device_list.nDeviceNum} devices!")
        devices = []
        for i in range(0, self.device_list.nDeviceNum):
            mvcc_dev_info = cast(self.device_list.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            model_name = ""
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE or mvcc_dev_info.nTLayerType == MV_GENTL_GIGE_DEVICE:
                # Basic parsing for GigE
                # For simplicity, we just return index and basic info. 
                # Real implementation might parse strings better as shown in BasicDemo
                pass
            devices.append(f"Device {i}")
        return devices

    def open_device(self, index=0):
        """
        Open the selected camera using the handle created in enumerate_devices.
        Follows MVS Python Sample BasicDemo logic.
        """
        if self.is_open:
            print("Camera already open.")
            return True

        if index >= self.device_list.nDeviceNum:
            print(f"Invalid device index: {index}. Max: {self.device_list.nDeviceNum - 1}")
            return False

        # Select device and create handle
        st_device_list = cast(self.device_list.pDeviceInfo[int(index)], POINTER(MV_CC_DEVICE_INFO)).contents
        
        ret = self.cam.MV_CC_CreateHandle(st_device_list)
        if ret != 0:
            print(f"Create handle failed! ret: {hex(ret)}")
            return False

        # Open Device
        ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            print(f"Open device failed! ret: {hex(ret)}")
            self.cam.MV_CC_DestroyHandle() # Clean up handle if open fails
            return False

        print("Camera opened successfully.")

        # --- Packet Size Configuration (Crucial for GigE) ---
        # Get optimal packet size from the driver
        nPacketSize = self.cam.MV_CC_GetOptimalPacketSize()
        if int(nPacketSize) > 0:
            ret = self.cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
            if ret != 0:
                print(f"Warning: Failed to set GevSCPSPacketSize to {nPacketSize}! ret: {hex(ret)}")
            else:
                print(f"Set GevSCPSPacketSize to {nPacketSize}")
        else:
            print(f"Warning: GetOptimalPacketSize failed or returned 0. ret: {hex(nPacketSize)}")
            # Fallback to a safe default if detection fails (e.g. 1500 or jumbo 9000 if supported)
            # MVS sample just prints warning. We will try to set 1500 as a safe baseline.
            self.cam.MV_CC_SetIntValue("GevSCPSPacketSize", 1500)

        # --- Trigger Mode Off (Continuous) ---
        ret = self.cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        if ret != 0:
             print(f"Set TriggerMode Off failed! ret: {hex(ret)}")
             
        # --- Remove Failing Settings (Exposure, FPS) ---
        # As requested, removing Max/Min Exposure and FPS settings that were failing.
        # User reported these causes issues. We leave them at default or auto.
        
        # Turn off ExposureAuto first (if we want manual control later, but for now defaults are fine)
        # self.cam.MV_CC_SetEnumValue("ExposureAuto", MV_EXPOSURE_AUTO_OFF) 
        
        self.is_open = True
        return True

    def start_grabbing(self):
        """
        Start the image grabbing thread.
        Allocates buffer based on PayloadSize.
        """
        if self.is_grabbing:
            print("Already grabbing.")
            return True

        if not self.is_open:
            print("Camera not open. Call open_device() first.")
            return False

        # 1. Get Payload Size (Data buffer size)
        stParam = MVCC_INTVALUE()
        memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
        
        ret = self.cam.MV_CC_GetIntValue("PayloadSize", stParam)
        if ret != 0:
            print(f"Get PayloadSize failed! ret: {hex(ret)}")
            # Fallback: Use a large buffer (20MB) to prevent crashing
            print("Using fallback payload size (20MB)")
            self.n_payload_size = 20 * 1024 * 1024
        else:
            self.n_payload_size = stParam.nCurValue
            
        if self.n_payload_size <= 0:
             self.n_payload_size = 20 * 1024 * 1024 # Double check

        # 2. Allocate Buffer
        self.data_buf = (c_ubyte * self.n_payload_size)()

        # 3. Start Grabbing
        ret = self.cam.MV_CC_StartGrabbing()
        if ret != 0:
            print(f"StartGrabbing failed! ret: {hex(ret)}")
            return False

        self.is_grabbing = True
        self.quit_event.clear()
        
        # Start Thread
        try:
            self.thread = threading.Thread(target=self.work_thread, daemon=True)
            self.thread.start()
            print("Grabbing thread started.")
            return True
        except Exception as e:
            print(f"Failed to start thread: {e}")
            self.is_grabbing = False
            return False

    def stop_grabbing(self):
        if not self.is_grabbing:
            return

        self.is_grabbing = False # Signal thread to stop
        # Wait for thread? For now, we trust SDK StopGrabbing to handle it or thread to check flag
        
        ret = self.cam.MV_CC_StopGrabbing()
        if ret != 0:
            print(f"Stop grabbing fail! ret: {hex(ret)}")

    def close_device(self):
        if self.is_grabbing:
            self.stop_grabbing()
            
        if self.is_open:
            self.cam.MV_CC_CloseDevice()
            self.cam.MV_CC_DestroyHandle()
            self.is_open = False

    def get_latest_frame_jpeg(self):
        """Returns the latest frame as JPEG bytes."""
        with self.lock:
            if self.current_frame:
                return self.current_frame
        return None

    def work_thread(self):
        stOutFrame = MV_FRAME_OUT()
        memset(byref(stOutFrame), 0, sizeof(stOutFrame))
        
        while self.is_grabbing:
            ret = self.cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
            if ret == 0:
                # We have a frame
                # Convert to JPEG
                self._convert_and_store_jpeg(stOutFrame)
                self.cam.MV_CC_FreeImageBuffer(stOutFrame)
            else:
                # print(f"No data! ret: {hex(ret)}")
                continue

    def _convert_and_store_jpeg(self, stOutFrame):
        # Prepare for saving/converting
        # Using MV_CC_SaveImageEx2 with MV_SAVE_IMAGE_PARAM_EX

        # If we need a bigger buffer for the JPEG, allocate it
        # JPEG usually smaller than raw, but safety first
        n_buf_size = stOutFrame.stFrameInfo.nFrameLen + 2048 # padding
        if self.buf_save_image is None or self.buf_save_image_len < n_buf_size:
             self.buf_save_image = (c_ubyte * n_buf_size)()
             self.buf_save_image_len = n_buf_size

        stSaveParam = MV_SAVE_IMAGE_PARAM_EX()
        stSaveParam.enPixelType = stOutFrame.stFrameInfo.enPixelType
        stSaveParam.nWidth = stOutFrame.stFrameInfo.nWidth
        stSaveParam.nHeight = stOutFrame.stFrameInfo.nHeight
        stSaveParam.nDataLen = stOutFrame.stFrameInfo.nFrameLen
        stSaveParam.pData = cast(stOutFrame.pBufAddr, POINTER(c_ubyte))
        stSaveParam.enImageType = MV_Image_Jpeg 
        stSaveParam.nJpgQuality = 80
        stSaveParam.pImageBuffer = self.buf_save_image
        stSaveParam.nBufferSize = self.buf_save_image_len
        stSaveParam.iMethodValue = 0

        try:
             ret = self.cam.MV_CC_SaveImageEx2(stSaveParam)
             if ret == 0:
                 # Success
                 data_len = stSaveParam.nImageLen
                 # distinct copy to store
                 with self.lock:
                    self.current_frame = string_at(self.buf_save_image, data_len)
             else:
                 print(f"MV_CC_SaveImageEx2 failed: {hex(ret)}")
        except AttributeError:
            print("MV_CC_SaveImageEx2 not found")
        except Exception as e:
            print(f"Image conversion error: {e}")

    # Remove old/duplicate methods
    def get_exposure_mode_status(self):
        # Helper to actually called by API
        if not self.is_open: return False
        stParam = MVCC_INTVALUE()
        memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
        # Using GetEnumValue is correct for Enum nodes
        ret = self.cam.MV_CC_GetEnumValue("ExposureAuto", stParam)
        if ret == 0:
            return stParam.nCurValue == MV_EXPOSURE_AUTO_MODE_CONTINUOUS
        return False

    def get_exposure(self):
        if not self.is_open: return 0
        stFloatParam = MVCC_FLOATVALUE()
        memset(byref(stFloatParam), 0, sizeof(MVCC_FLOATVALUE))
        ret = self.cam.MV_CC_GetFloatValue("ExposureTime", stFloatParam)
        if ret == 0:
            return stFloatParam.fCurValue
        return 0

    def get_exposure_range(self):
        """Returns (min, max, current) exposure time values."""
        if not self.is_open: 
            return (0, 0, 0)
        stFloatParam = MVCC_FLOATVALUE()
        memset(byref(stFloatParam), 0, sizeof(MVCC_FLOATVALUE))
        ret = self.cam.MV_CC_GetFloatValue("ExposureTime", stFloatParam)
        if ret == 0:
            return (stFloatParam.fMin, stFloatParam.fMax, stFloatParam.fCurValue)
        return (0, 0, 0)


    def get_gain(self):
        if not self.is_open: return 0
        stFloatParam = MVCC_FLOATVALUE()
        memset(byref(stFloatParam), 0, sizeof(MVCC_FLOATVALUE))
        ret = self.cam.MV_CC_GetFloatValue("Gain", stFloatParam)
        if ret == 0:
            return stFloatParam.fCurValue
        return 0

    def get_fps(self):
        """Returns the current resulting frame rate from camera."""
        if not self.is_open: return 0
        stFloatParam = MVCC_FLOATVALUE()
        memset(byref(stFloatParam), 0, sizeof(MVCC_FLOATVALUE))
        # Try ResultingFrameRate first (read-only parameter showing actual FPS)
        ret = self.cam.MV_CC_GetFloatValue("ResultingFrameRate", stFloatParam)
        if ret == 0:
            return round(stFloatParam.fCurValue, 2)
        # Fallback to AcquisitionFrameRate
        ret = self.cam.MV_CC_GetFloatValue("AcquisitionFrameRate", stFloatParam)
        if ret == 0:
            return round(stFloatParam.fCurValue, 2)
        return 0

    def set_exposure_mode(self, auto_exposure: bool):
        """
        Set Exposure Auto Mode.
        True: Continuous (2) - Camera adjusts exposure automatically.
        False: Off (0) - Manual exposure time used.
        """
        if not self.is_open:
            return False
        
        mode = MV_EXPOSURE_AUTO_MODE_CONTINUOUS if auto_exposure else MV_EXPOSURE_AUTO_OFF
        ret = self.cam.MV_CC_SetEnumValue("ExposureAuto", mode)
        if ret != 0:
            print(f"Failed to set ExposureAuto to {mode}: {hex(ret)}")
            return False
        return True

    def set_exposure(self, exposure_time: float):
        """
        Set Manual Exposure Time (us).
        Requires ExposureAuto to be OFF.
        """
        if not self.is_open:
            return False
        
        ret = self.cam.MV_CC_SetFloatValue("ExposureTime", float(exposure_time))
        if ret != 0:
            print(f"Failed to set ExposureTime to {exposure_time}: {hex(ret)}")
            return False
        return True

    def set_gain(self, gain: float):
        """Set Gain."""
        if not self.is_open:
            return False
            
        ret = self.cam.MV_CC_SetFloatValue("Gain", float(gain))
        if ret != 0:
            print(f"Failed to set Gain to {gain}: {hex(ret)}")
            return False
        return True

    def save_current_frame(self, filepath):
        """Saves the latest frame to the specified filepath."""
        frame_data = None
        with self.lock:
            if self.current_frame:
                frame_data = self.current_frame
        
        if frame_data:
            try:
                # Make sure directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'wb') as f:
                    f.write(frame_data)
                return True
            except Exception as e:
                print(f"Failed to save image: {e}")
                return False
        return False

# Global instance
camera_manager = CameraManager()
