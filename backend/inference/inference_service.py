"""Multi-backend inference service for defect detection.

Tries backends in order: CUDA (ONNX Runtime) -> OpenVINO (Intel GPU) -> CPU
"""

import logging
import time
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Model paths - local project folder
MODEL_DIR = Path(__file__).parent / "openvino_model"
ONNX_MODEL_PATH = MODEL_DIR / "model.onnx"
OPENVINO_MODEL_PATH = MODEL_DIR / "model.xml"
TRT_MODEL_PATH = MODEL_DIR / "model.trt"

# Defect class mapping
CLASS_NAMES = {
    0: "Background",
    1: "Dust",
    2: "RunDown", 
    3: "Scratch"
}

CLASS_COLORS = {
    0: (0, 0, 0),       # Background - Black
    1: (255, 0, 0),     # Dust - Red
    2: (0, 255, 0),     # RunDown - Green
    3: (255, 255, 0)    # Scratch - Yellow
}


def mask_to_rgb(mask: np.ndarray) -> np.ndarray:
    """Convert class mask to RGB image."""
    h, w = mask.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for class_id, color in CLASS_COLORS.items():
        rgb[mask == class_id] = color
    return rgb


class DefectPredictor:
    """Multi-backend predictor for defect detection.
    
    Tries backends in order: TensorRT -> OpenVINO GPU -> OpenVINO CPU
    """
    
    _instance = None
    
    def __init__(self, image_size: int = 518) -> None:
        """Initialize predictor with best available backend."""
        self.image_size = image_size
        self.backend = None
        self.session = None  # For ONNX Runtime
        self.compiled_model = None  # For OpenVINO
        
        # TensorRT specific
        self.trt_logger = None
        self.engine = None
        self.context = None
        self.inputs = []
        self.outputs = []
        self.bindings = []
        self.stream = None

        # ImageNet normalization
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        
        # Try backends in order
        if self._try_tensorrt():
            logger.info("[Inference] Using TensorRT backend")
        elif self._try_openvino():
             logger.info(f"[Inference] Using OpenVINO backend on {self.device}")
        else:
            self._fallback_cpu()
            logger.info("[Inference] Using CPU backend (ONNX Runtime)")
        
        # Warmup
        self._warmup()
    
    def _try_tensorrt(self) -> bool:
        """Try to initialize TensorRT backend."""
        try:
            import tensorrt as trt
            import numpy as np
            
            cudart = None
            try:
                # Try explicit submodule import which works better with namespace packages
                # On some versions/installs, it's cuda.bindings.runtime or cuda.cudart
                try:
                    from cuda import cudart as _cudart
                    cudart = _cudart
                except ImportError:
                    # Fallback to bindings.runtime which was verified to exist
                    from cuda.bindings import runtime as _cudart
                    cudart = _cudart

            except ImportError as e:
                logger.warning(f"[Inference] Could not import cuda-python: {e}")
                return False
            
            if not TRT_MODEL_PATH.exists():
                logger.warning(f"[Inference] TensorRT engine not found at {TRT_MODEL_PATH}")
                return False

            logger.info(f"[Inference] Loading TensorRT engine from {TRT_MODEL_PATH}")
            self.trt_logger = trt.Logger(trt.Logger.WARNING)
            
            with open(TRT_MODEL_PATH, "rb") as f, trt.Runtime(self.trt_logger) as runtime:
                self.engine = runtime.deserialize_cuda_engine(f.read())
            
            if not self.engine:
                logger.error("[Inference] Failed to load TensorRT engine")
                return False
                
            self.context = self.engine.create_execution_context()
            
            # Create stream
            _, self.stream = cudart.cudaStreamCreate()
            
            # Allocate buffers
            self.inputs = []
            self.outputs = []
            self.bindings = []
            
            for binding in self.engine:
                # get_binding_shape returns a Dims object or tuple, volume calculates total elements
                # Note: valid for TRT 8.x. 10.x uses different API, assuming 8.x/9.x based on common use
                shape = self.engine.get_binding_shape(binding)
                size = trt.volume(shape) * self.engine.max_batch_size
                dtype = trt.nptype(self.engine.get_binding_dtype(binding))
                
                # Allocate host memory (standard numpy array)
                host_mem = np.zeros(size, dtype=dtype)
                
                # Allocate device memory
                nbytes = host_mem.nbytes
                _, device_mem = cudart.cudaMalloc(nbytes)
                
                self.bindings.append(int(device_mem))
                
                if self.engine.binding_is_input(binding):
                    self.inputs.append({"host": host_mem, "device": device_mem, "nbytes": nbytes})
                else:
                    self.outputs.append({"host": host_mem, "device": device_mem, "nbytes": nbytes})
            
            self.backend = "tensorrt"
            return True
            
        except ImportError as e:
            logger.warning(f"[Inference] TensorRT or cuda-python not installed: {e}")
            return False
        except Exception as e:
            logger.error(f"[Inference] TensorRT init failed: {e}")
            return False

    
    def _try_cuda(self) -> bool:
        """Try to initialize CUDA backend via ONNX Runtime."""
        try:
            import onnxruntime as ort
            
            # Check if CUDA is available
            providers = ort.get_available_providers()
            print(f"[Inference] ONNX Runtime providers: {providers}")
            
            if 'CUDAExecutionProvider' not in providers:
                print("[Inference] CUDA not available in ONNX Runtime")
                return False
            
            # Find ONNX model
            onnx_path = ONNX_MODEL_PATH if ONNX_MODEL_PATH.exists() else LOCAL_MODEL_DIR / "model.onnx"
            if not onnx_path.exists():
                print(f"[Inference] ONNX model not found at {onnx_path}")
                return False
            
            print(f"[Inference] Loading ONNX model from {onnx_path}")
            
            # Create session with CUDA
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            self.session = ort.InferenceSession(
                str(onnx_path),
                sess_options,
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            
            # Verify CUDA is actually being used
            active_provider = self.session.get_providers()[0]
            if active_provider != 'CUDAExecutionProvider':
                print(f"[Inference] CUDA provider not active, got {active_provider}")
                self.session = None
                return False
            
            self.backend = "cuda"
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            return True
            
        except ImportError:
            print("[Inference] ONNX Runtime not installed")
            return False
        except Exception as e:
            print(f"[Inference] CUDA init failed: {e}")
            return False
    
    def _try_openvino(self) -> bool:
        """Try to initialize OpenVINO backend with GPU.0 -> GPU.1 -> fallback."""
        try:
            import openvino as ov
            from openvino.preprocess import PrePostProcessor, ColorFormat
            
            core = ov.Core()
            devices = core.available_devices
            print(f"[Inference] OpenVINO devices: {devices}")
            
            # Try GPU.0 first, then GPU.1, then fail (fall back to CPU via ONNX)
            if "GPU.0" in devices:
                self.device = "GPU.0"
                logger.info("[Inference] Using GPU.0")
            elif "GPU.1" in devices:
                self.device = "GPU.1"
                logger.info("[Inference] Using GPU.1")
            elif "GPU" in devices:
                self.device = "GPU"
                logger.info("[Inference] Using GPU")
            else:
                logger.info("[Inference] OpenVINO GPU not available")
                return False
            
            # Find OpenVINO model
            if not OPENVINO_MODEL_PATH.exists():
                logger.warning(f"[Inference] OpenVINO model not found at {OPENVINO_MODEL_PATH}")
                return False
            
            logger.info(f"[Inference] Loading OpenVINO model from {OPENVINO_MODEL_PATH}")
            
            # Enable caching
            cache_dir = OPENVINO_MODEL_PATH.parent / "cache"
            cache_dir.mkdir(exist_ok=True)
            core.set_property({"CACHE_DIR": str(cache_dir)})
            
            # Load model
            model = core.read_model(str(OPENVINO_MODEL_PATH))
            
            # Add preprocessing
            ppp = PrePostProcessor(model)
            ppp.input().tensor() \
                .set_element_type(ov.Type.u8) \
                .set_layout(ov.Layout("NHWC")) \
                .set_color_format(ColorFormat.RGB)
            ppp.input().preprocess() \
                .convert_element_type(ov.Type.f32) \
                .convert_layout(ov.Layout("NCHW")) \
                .mean([0.485 * 255, 0.456 * 255, 0.406 * 255]) \
                .scale([0.229 * 255, 0.224 * 255, 0.225 * 255])
            ppp.input().model().set_layout(ov.Layout("NCHW"))
            
            model = ppp.build()
            model.reshape({model.input(0): [1, self.image_size, self.image_size, 3]})
            
            # Compile
            config = {"PERFORMANCE_HINT": "LATENCY"}
            self.compiled_model = core.compile_model(model, self.device, config)
            self.sync_request = self.compiled_model.create_infer_request()
            self.input_layer = self.compiled_model.input(0)
            self.output_layer = self.compiled_model.output(0)
            
            self.backend = "openvino"
            return True
            
        except ImportError:
            print("[Inference] OpenVINO not installed")
            return False
        except Exception as e:
            print(f"[Inference] OpenVINO init failed: {e}")
            return False
    
    def _fallback_cpu(self):
        """Fallback to CPU via ONNX Runtime."""
        try:
            import onnxruntime as ort
            
            onnx_path = ONNX_MODEL_PATH if ONNX_MODEL_PATH.exists() else LOCAL_MODEL_DIR / "model.onnx"
            
            if onnx_path.exists():
                self.session = ort.InferenceSession(
                    str(onnx_path),
                    providers=['CPUExecutionProvider']
                )
                self.backend = "cpu_onnx"
                self.input_name = self.session.get_inputs()[0].name
                self.output_name = self.session.get_outputs()[0].name
            else:
                raise FileNotFoundError(f"No model found at {onnx_path}")
                
        except Exception as e:
            print(f"[Inference] CPU fallback failed: {e}")
            raise RuntimeError("No inference backend available")
    
    @classmethod
    def get_instance(cls) -> "DefectPredictor":
        """Get singleton instance of predictor."""
        if cls._instance is None:
            cls._instance = DefectPredictor()
        return cls._instance
    
    def _warmup(self, iterations: int = 3):
        """Warmup the model."""
        dummy = np.zeros((1, self.image_size, self.image_size, 3), dtype=np.uint8)
        
        for _ in range(iterations):
            if self.backend == "tensorrt":
                # TensorRT preprocessing (NCHW format, normalized)
                dummy_f = dummy.astype(np.float32) / 255.0
                dummy_f = (dummy_f - self.mean) / self.std
                dummy_f = dummy_f.transpose(0, 3, 1, 2)
                
                # Copy input D2H
                np.copyto(self.inputs[0]['host'], dummy_f.ravel())
                
                # Inference steps included in predict, but for warmup we just check generic run
                from cuda import cudart
                
                cudart.cudaMemcpyAsync(
                    self.inputs[0]['device'], 
                    self.inputs[0]['host'].ctypes.data, 
                    self.inputs[0]['nbytes'], 
                    cudart.cudaMemcpyKind.cudaMemcpyHostToDevice, 
                    self.stream
                )
                
                self.context.execute_async_v2(bindings=self.bindings, stream_handle=int(self.stream))
                
                cudart.cudaMemcpyAsync(
                    self.outputs[0]['host'].ctypes.data, 
                    self.outputs[0]['device'], 
                    self.outputs[0]['nbytes'], 
                    cudart.cudaMemcpyKind.cudaMemcpyDeviceToHost, 
                    self.stream
                )
                
                cudart.cudaStreamSynchronize(self.stream)
                
            elif self.backend == "openvino":
                self.sync_request.infer({self.input_layer: dummy})
            else:
                # ONNX preprocessing (NCHW format, normalized)
                dummy_f = dummy.astype(np.float32) / 255.0
                dummy_f = (dummy_f - self.mean) / self.std
                dummy_f = dummy_f.transpose(0, 3, 1, 2)
                self.session.run([self.output_name], {self.input_name: dummy_f})
        
        logger.info(f"[Inference] Model ready ({self.backend})")
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for inference."""
        img = Image.fromarray(image).resize(
            (self.image_size, self.image_size),
            Image.BILINEAR
        )
        return np.array(img, dtype=np.uint8)
    
    def predict(self, image_path: str) -> Tuple[np.ndarray, float, List[Dict]]:
        """Run inference on an image."""
        original = Image.open(image_path).convert('RGB')
        original_size = original.size[::-1]  # (height, width)
        
        img = self.preprocess(np.array(original))
        
        start = time.perf_counter()
        
        if self.backend == "tensorrt":
            from cuda import cudart
            
            # Preprocess for TensorRT (NCHW, Float32, Normalized)
            img_f = img.astype(np.float32) / 255.0
            img_f = (img_f - self.mean) / self.std
            img_f = np.expand_dims(img_f.transpose(2, 0, 1), 0)  # NCHW
            
            # Copy input to host memory
            np.copyto(self.inputs[0]['host'], img_f.ravel())
            
            # Transfer input data to the GPU.
            cudart.cudaMemcpyAsync(
                self.inputs[0]['device'], 
                self.inputs[0]['host'].ctypes.data, 
                self.inputs[0]['nbytes'], 
                cudart.cudaMemcpyKind.cudaMemcpyHostToDevice, 
                self.stream
            )
            
            # Run inference.
            self.context.execute_async_v2(bindings=self.bindings, stream_handle=int(self.stream))
            
            # Transfer predictions back from the GPU.
            cudart.cudaMemcpyAsync(
                self.outputs[0]['host'].ctypes.data, 
                self.outputs[0]['device'], 
                self.outputs[0]['nbytes'], 
                cudart.cudaMemcpyKind.cudaMemcpyDeviceToHost, 
                self.stream
            )
            
            # Synchronize the stream
            cudart.cudaStreamSynchronize(self.stream)
            
            # Get output (assumes single output)
            output = self.outputs[0]['host'].reshape((1, 4, self.image_size, self.image_size))
            
        elif self.backend == "openvino":
            input_tensor = np.expand_dims(img, 0)
            self.sync_request.infer({self.input_layer: input_tensor})
            output = self.sync_request.get_output_tensor().data
        else:
            # ONNX Runtime (CUDA or CPU)
            img_f = img.astype(np.float32) / 255.0
            img_f = (img_f - self.mean) / self.std
            img_f = np.expand_dims(img_f.transpose(2, 0, 1), 0)  # NCHW
            output = self.session.run([self.output_name], {self.input_name: img_f})[0]
        
        inference_time = (time.perf_counter() - start) * 1000
        
        pred_mask = np.argmax(output[0], axis=0).astype(np.uint8)
        
        # Resize to original size
        pred_mask = np.array(
            Image.fromarray(pred_mask).resize(
                (original_size[1], original_size[0]), Image.NEAREST
            )
        )
        
        defects = self._extract_defects(pred_mask)
        return pred_mask, inference_time, defects
    
    def _extract_defects(self, mask: np.ndarray) -> List[Dict]:
        """Extract defect information from prediction mask."""
        defects = []
        
        for class_id in [1, 2, 3]:  # Skip background
            class_mask = (mask == class_id)
            pixel_count = np.sum(class_mask)
            
            if pixel_count > 0:
                total_pixels = mask.size
                area_ratio = pixel_count / total_pixels
                
                defects.append({
                    "type": CLASS_NAMES[class_id],
                    "class_id": class_id,
                    "pixel_count": int(pixel_count),
                    "area_ratio": float(area_ratio)
                })
        
        return defects
    
    def predict_and_save(
        self,
        image_path: str,
        output_dir: str,
        save_overlay: bool = True,
        alpha: float = 0.5
    ) -> Tuple[str, str, float, List[Dict]]:
        """Run inference and save result images."""
        import json
        
        original = Image.open(image_path).convert('RGB')
        original_np = np.array(original)
        
        pred_mask, inference_time, defects = self.predict(image_path)
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base_name = Path(image_path).stem
        
        # Generate mask RGB for overlay
        mask_rgb = mask_to_rgb(pred_mask)
        
        # Save overlay only (no mask file)
        overlay_path = None
        if save_overlay:
            overlay = (original_np * (1 - alpha) + mask_rgb * alpha).astype(np.uint8)
            overlay_path = output_dir / f"{base_name}_{timestamp}_overlay.png"
            Image.fromarray(overlay).save(overlay_path)
        
        # Save defect metadata JSON
        metadata_path = output_dir / f"{base_name}_{timestamp}_meta.json"
        metadata = {
            "image": Path(image_path).name,
            "timestamp": timestamp,
            "inference_time_ms": inference_time,
            "defect_count": len(defects),
            "defects": defects
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return None, str(overlay_path) if overlay_path else None, inference_time, defects


# Global predictor instance (lazy initialized)
_predictor: Optional[DefectPredictor] = None


def get_predictor() -> DefectPredictor:
    """Get or create the global predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = DefectPredictor()
    return _predictor
