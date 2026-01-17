import sys
import os
import platform
import threading
import time
import ctypes
from ctypes import *

# Add MVS SDK to path
if platform.system() == 'Windows':
    mv_env = os.getenv('MVCAM_COMMON_RUNENV')
    if mv_env:
        sys.path.append(os.path.join(mv_env, "Samples", "Python", "MvImport"))
    else:
        print("Error: MVCAM_COMMON_RUNENV environment variable not set. Camera SDK might not be installed.")

try:
    from MvCameraControl_class import *
    from CameraParams_header import *
    from MvErrorDefine_const import *
except ImportError as e:
    print(f"Error importing MVS SDK: {e}")
    # Define dummy classes to prevent crash if SDK is missing during development
    class MvCamera: pass
    class MV_CC_DEVICE_INFO_LIST: pass
    class MV_FRAME_OUT_INFO_EX: pass

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
        if self.is_open:
            return True

        if index >= self.device_list.nDeviceNum:
            return False

        # Select device
        st_device_list = cast(self.device_list.pDeviceInfo[int(index)], POINTER(MV_CC_DEVICE_INFO)).contents
        
        ret = self.cam.MV_CC_CreateHandle(st_device_list)
        if ret != 0:
            print(f"Create handle failed! ret: {hex(ret)}")
            return False

        ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            print(f"Open device failed! ret: {hex(ret)}")
            return False
        
        # Detect packet size for GigE
        if st_device_list.nTLayerType == MV_GIGE_DEVICE or st_device_list.nTLayerType == MV_GENTL_GIGE_DEVICE:
            nPacketSize = self.cam.MV_CC_GetOptimalPacketSize()
            if int(nPacketSize) > 0:
                ret = self.cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                if ret != 0:
                    print(f"Warning: Set Packet Size fail! ret: {hex(ret)}")
            else:
                print(f"Warning: Get Packet Size fail! ret: {hex(nPacketSize)}")

        self.is_open = True
        return True

    def start_grabbing(self):
        if not self.is_open or self.is_grabbing:
            return False

        # Get payload size
        stParam = MVCC_INTVALUE()
        memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
        ret = self.cam.MV_CC_GetIntValue("PayloadSize", stParam)
        if ret != 0:
            print(f"Get PayloadSize fail! ret: {hex(ret)}")
            return False
        
        self.n_payload_size = stParam.nCurValue
        self.data_buf = (c_ubyte * self.n_payload_size)()

        ret = self.cam.MV_CC_StartGrabbing()
        if ret != 0:
            print(f"Start grabbing fail! ret: {hex(ret)}")
            return False

        self.is_grabbing = True
        
        # Start thread
        self.thread = threading.Thread(target=self.work_thread)
        self.thread.daemon = True
        self.thread.start()
        return True

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

    def set_exposure(self, value):
        if not self.is_open: return False
        # Turn off auto exposure first
        self.cam.MV_CC_SetEnumValue("ExposureAuto", MV_EXPOSURE_AUTO_MODE_OFF)
        return self.cam.MV_CC_SetFloatValue("ExposureTime", float(value)) == 0

    def set_gain(self, value):
        if not self.is_open: return False
        self.cam.MV_CC_SetEnumValue("GainAuto", MV_GAIN_MODE_OFF)
        return self.cam.MV_CC_SetFloatValue("Gain", float(value)) == 0

    def get_exposure(self):
        if not self.is_open: return 0
        stFloatParam = MVCC_FLOATVALUE()
        memset(byref(stFloatParam), 0, sizeof(MVCC_FLOATVALUE))
        ret = self.cam.MV_CC_GetFloatValue("ExposureTime", stFloatParam)
        if ret == 0:
            return stFloatParam.fCurValue
        return 0

    def get_gain(self):
        if not self.is_open: return 0
        stFloatParam = MVCC_FLOATVALUE()
        memset(byref(stFloatParam), 0, sizeof(MVCC_FLOATVALUE))
        ret = self.cam.MV_CC_GetFloatValue("Gain", stFloatParam)
        if ret == 0:
            return stFloatParam.fCurValue
        return 0

# Global instance
camera_manager = CameraManager()
