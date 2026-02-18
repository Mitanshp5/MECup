
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from inference.inference_service import get_predictor

print("Initializing Predictor...")
predictor = get_predictor()
print(f"Current Model Type: {predictor.current_model_type}")

if predictor.current_model_type == "black":
    print("SUCCESS: Default is BLACK")
else:
    print(f"FAILURE: Default is {predictor.current_model_type}")
