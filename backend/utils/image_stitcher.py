import cv2
import numpy as np
import pandas as pd
import os
from typing import Optional


def flat_field_correct(img, blur_size=201):
    """Apply flat-field correction to normalize illumination."""
    img_f = img.astype(np.float32)
    bg = cv2.GaussianBlur(img_f, (blur_size, blur_size), 0)
    bg[bg < 1] = 1
    corrected = img_f / bg * np.mean(bg)
    return np.clip(corrected, 0, 255).astype(np.uint8)


def normalize_tile(img, target_mean=128):
    """Normalize brightness of image tile to target mean."""
    mean = np.mean(img)
    scale = target_mean / (mean + 1e-5)
    img = img.astype(np.float32) * scale
    return np.clip(img, 0, 255).astype(np.uint8)


def create_weight_mask(h, w):
    """Create Gaussian blending mask for smooth transitions."""
    y, x = np.ogrid[:h, :w]
    center_y = h / 2
    center_x = w / 2
    dist = ((x - center_x) ** 2 + (y - center_y) ** 2)
    sigma = min(h, w) * 0.4
    weights = np.exp(-dist / (2 * sigma * sigma))
    weights = weights.astype(np.float32)
    return np.dstack([weights, weights, weights])


def stitch_images(scan_folder_path: str, output_filename: str = "stitched_result.jpg", scale: float = 18.0) -> Optional[str]:
    """
    Stitch images from a scan folder using grid_locations.csv.
    
    Args:
        scan_folder_path: Path to the scan folder containing images and grid_locations.csv
        output_filename: Name of the output stitched image file
        scale: Scale factor in pixels per millimeter (default: 18.0)
        
    Returns:
        Path to the stitched image if successful, None otherwise
    """
    csv_path = os.path.join(scan_folder_path, "grid_locations.csv")
    
    if not os.path.exists(csv_path):
        print(f"grid_locations.csv not found in {scan_folder_path}")
        return None
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None
    
    # Invert coordinates
    df['X'] = -df['X']
    df['Y'] = -df['Y']
    
    print(f"Using Scale: {scale:.4f} px/mm")
    
    min_x = df['X'].min()
    max_x = df['X'].max()
    min_y = df['Y'].min()
    max_y = df['Y'].max()
    
    # Read first image to get dimensions
    first_img_path = os.path.join(scan_folder_path, df.iloc[0]['Filename'])
    sample_img = cv2.imread(first_img_path)
    if sample_img is None:
        print(f"Error reading first image: {first_img_path}")
        return None
    
    h, w = sample_img.shape[:2]
    weight_mask = create_weight_mask(h, w)
    
    # Calculate canvas size
    canvas_w = int((max_x - min_x) * scale) + w
    canvas_h = int((max_y - min_y) * scale) + h
    
    canvas_acc = np.zeros((canvas_h, canvas_w, 3), dtype=np.float32)
    weights_acc = np.zeros((canvas_h, canvas_w, 3), dtype=np.float32)
    
    print(f"Stitching {len(df)} images...")
    
    # Process each image
    for idx, row in df.iterrows():
        img_path = os.path.join(scan_folder_path, row['Filename'])
        img = cv2.imread(img_path)
        if img is None:
            print(f"Warning: Could not read {img_path}")
            continue
        
        # Apply flat-field correction and brightness normalization
        img = flat_field_correct(img)
        img = normalize_tile(img)
        img = img.astype(np.float32)
        
        physical_x = row['X']
        physical_y = row['Y']
        
        x_pos = int((physical_x - min_x) * scale)
        y_pos = int((max_y - physical_y) * scale)
        
        end_x = x_pos + w
        end_y = y_pos + h
        
        if end_x > canvas_w:
            end_x = canvas_w
        if end_y > canvas_h:
            end_y = canvas_h
        
        src_end_x = w - (x_pos + w - end_x)
        src_end_y = h - (y_pos + h - end_y)
        
        if src_end_x <= 0 or src_end_y <= 0:
            continue
        
        img_crop = img[0:src_end_y, 0:src_end_x]
        weight_crop = weight_mask[0:src_end_y, 0:src_end_x]
        
        canvas_acc[y_pos:end_y, x_pos:end_x] += img_crop * weight_crop
        weights_acc[y_pos:end_y, x_pos:end_x] += weight_crop
    
    # Normalize
    final_canvas = np.zeros_like(canvas_acc)
    mask = weights_acc > 1e-5
    final_canvas[mask] = canvas_acc[mask] / weights_acc[mask]
    final_canvas = np.clip(final_canvas, 0, 255).astype(np.uint8)
    
    # Fill missing areas with mean color of surrounding pixels (inpainting)
    missing_mask = (weights_acc[:, :, 0] < 1e-5).astype(np.uint8)
    if np.any(missing_mask):
        print("Filling missing areas with inpainting...")
        # Calculate mean color from valid pixels
        valid_pixels = final_canvas[mask[:, :, 0]]
        if len(valid_pixels) > 0:
            mean_color = np.mean(valid_pixels, axis=0).astype(np.uint8)
            # Fill missing areas with mean color
            for c in range(3):
                final_canvas[:, :, c][missing_mask == 1] = mean_color[c]
    
    # Save stitched image
    output_path = os.path.join(scan_folder_path, output_filename)
    cv2.imwrite(output_path, final_canvas)
    print(f"Stitched image saved to {output_path}")
    
    return output_path
