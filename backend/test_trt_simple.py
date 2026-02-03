import os
import sys
import ctypes

print(f"Python: {sys.version}")
print(f"Platform: {sys.platform}")

# 1. Print PATH to see if TensorRT lib is there
print("\n--- PATH Environment Variable ---")
for p in os.environ.get("PATH", "").split(os.pathsep):
    if "TensorRT" in p or "tensorrt" in p or "lib" in p.lower():
        print(f"Found potential TRT path: {p}")
        if os.path.exists(p):
            print(f"  -> Exists! Contents: {[f for f in os.listdir(p) if f.endswith('.dll')][:5]}...")
            try:
                if sys.platform == "win32":
                    os.add_dll_directory(p)
                    print("  -> Added to DLL search path")
            except Exception as e:
                print(f"  -> Failed to add to DLL path: {e}")

# 2. Try loading nvinfer.dll directly
print("\n--- DLL Load Test ---")
try:
    nvinfer = ctypes.CDLL("nvinfer.dll")
    print("SUCCESS: nvinfer.dll loaded directly")
except Exception as e:
    print(f"FAILURE: Could not load nvinfer.dll: {e}")
    print("This means the 'lib' folder is not in PATH or missing dependencies.")

# 3. Import TensorRT
print("\n--- Import TensorRT ---")
try:
    import tensorrt as trt
    print(f"SUCCESS: Imported tensorrt")
    print(f"Version: {trt.__version__}")
    print(f"File: {trt.__file__}")
    
    print("\n--- Runtime Test ---")
    try:
        logger = trt.Logger(trt.Logger.WARNING)
        print("Logger created")
        runtime = trt.Runtime(logger)
        print("Runtime created successfully!")
    except Exception as e:
        print(f"FAILURE: Could not create Runtime: {e}")

except ImportError as e:
    print(f"FAILURE: Could not import tensorrt: {e}")
except Exception as e:
    print(f"FAILURE: Unexpected error: {e}")
