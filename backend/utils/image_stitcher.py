import cv2
import numpy as np
import pandas as pd
import os
import json
import glob
from typing import Optional, Dict, Any, List


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


def _load_results_json(scan_folder_path: str) -> List[Dict[str, Any]]:
    """Load all result JSON files from the results folder."""
    results_dir = os.path.join(scan_folder_path, "results")
    if not os.path.exists(results_dir):
        return []
    
    reports = []
    for json_file in sorted(glob.glob(os.path.join(results_dir, "*_report.json"))):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                reports.append(data)
        except (json.JSONDecodeError, IOError):
            continue
    return reports


def generate_heatmap(scan_folder_path: str, scale: float = 18.0) -> Optional[str]:
    """
    Generate a defect heatmap overlay on the stitched image.
    Reads defect data from results JSON files and maps defect density
    onto the stitched canvas using grid coordinates.
    
    Returns:
        Path to the heatmap image if successful, None otherwise.
    """
    csv_path = os.path.join(scan_folder_path, "grid_locations.csv")
    stitched_path = os.path.join(scan_folder_path, "stitched_result.jpg")
    
    if not os.path.exists(csv_path):
        print(f"grid_locations.csv not found in {scan_folder_path}")
        return None
    
    # Load stitched image (generate if missing)
    if not os.path.exists(stitched_path):
        result = stitch_images(scan_folder_path, "stitched_result.jpg", scale)
        if result is None:
            return None
    
    stitched = cv2.imread(stitched_path)
    if stitched is None:
        return None
    
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return None
    
    df['X'] = -df['X']
    df['Y'] = -df['Y']
    
    min_x = df['X'].min()
    max_x = df['X'].max()
    min_y = df['Y'].min()
    max_y = df['Y'].max()
    
    # Get tile dimensions from first image
    first_img_path = os.path.join(scan_folder_path, df.iloc[0]['Filename'])
    sample_img = cv2.imread(first_img_path)
    if sample_img is None:
        return None
    h, w = sample_img.shape[:2]
    
    canvas_h, canvas_w = stitched.shape[:2]
    
    # Load all result JSONs and build a map: image filename -> defect data
    reports = _load_results_json(scan_folder_path)
    defect_map = {}
    for report in reports:
        img_name = report.get("image", "")
        summary = report.get("summary", {})
        defect_map[img_name] = summary
    
    # Create heatmap intensity canvas
    heat_canvas = np.zeros((canvas_h, canvas_w), dtype=np.float32)
    
    for _, row in df.iterrows():
        filename = row['Filename']
        summary = defect_map.get(filename, {})
        defect_count = summary.get("total_defects", 0)
        defect_area_pct = summary.get("defect_area_percentage", 0.0)
        
        # Intensity based on defect area percentage (stronger signal)
        intensity = min(defect_area_pct / 10.0, 1.0)  # Normalize: 10% area = max intensity
        # Also factor in count
        intensity = max(intensity, min(defect_count / 5.0, 1.0))
        
        if intensity < 0.01:
            continue
        
        physical_x = row['X']
        physical_y = row['Y']
        
        x_pos = int((physical_x - min_x) * scale)
        y_pos = int((max_y - physical_y) * scale)
        
        end_x = min(x_pos + w, canvas_w)
        end_y = min(y_pos + h, canvas_h)
        
        if end_x <= x_pos or end_y <= y_pos:
            continue
        
        heat_canvas[y_pos:end_y, x_pos:end_x] = np.maximum(
            heat_canvas[y_pos:end_y, x_pos:end_x], intensity
        )
    
    # Apply Gaussian blur for smooth heatmap
    blur_k = max(int(min(canvas_h, canvas_w) * 0.05) | 1, 31)
    heat_canvas = cv2.GaussianBlur(heat_canvas, (blur_k, blur_k), 0)
    
    # Normalize to 0-255
    if heat_canvas.max() > 0:
        heat_canvas = (heat_canvas / heat_canvas.max() * 255).astype(np.uint8)
    else:
        heat_canvas = heat_canvas.astype(np.uint8)
    
    # Apply colormap (JET: blue=low, red=high)
    heatmap_colored = cv2.applyColorMap(heat_canvas, cv2.COLORMAP_JET)
    
    # Create mask where there are defects (non-zero heat)
    alpha = 0.45
    mask = heat_canvas > 5
    
    # Blend heatmap onto stitched image
    result = stitched.copy()
    for c in range(3):
        result[:, :, c] = np.where(
            mask,
            np.clip(stitched[:, :, c] * (1 - alpha) + heatmap_colored[:, :, c] * alpha, 0, 255).astype(np.uint8),
            stitched[:, :, c]
        )
    
    output_path = os.path.join(scan_folder_path, "heatmap_result.jpg")
    cv2.imwrite(output_path, result)
    print(f"Heatmap image saved to {output_path}")
    
    return output_path


def generate_intensive_summary(scan_folder_path: str) -> Dict[str, Any]:
    """
    Generate an intensive summary from all result JSON files in a scan folder.
    Aggregates metrics across all tiles for a comprehensive analysis.
    
    Returns:
        Dictionary with aggregated metrics and per-type breakdowns.
    """
    reports = _load_results_json(scan_folder_path)
    
    total_tiles = len(reports)
    tiles_with_defects = 0
    total_defects = 0
    total_defect_area_mm2 = 0.0
    total_defect_area_pixels = 0
    max_defect_area_pct = 0.0
    worst_tile = ""
    
    type_stats: Dict[str, Dict[str, Any]] = {}
    tile_defect_counts: List[int] = []
    
    for report in reports:
        summary = report.get("summary", {})
        defects = report.get("defects", {})
        img_name = report.get("image", "")
        
        tile_total = summary.get("total_defects", 0)
        tile_defect_counts.append(tile_total)
        total_defects += tile_total
        total_defect_area_mm2 += summary.get("total_defect_area_mm2", 0.0)
        total_defect_area_pixels += summary.get("total_defect_area_pixels", 0)
        
        area_pct = summary.get("defect_area_percentage", 0.0)
        if area_pct > max_defect_area_pct:
            max_defect_area_pct = area_pct
            worst_tile = img_name
        
        if tile_total > 0:
            tiles_with_defects += 1
        
        for defect_type, type_data in defects.items():
            if defect_type not in type_stats:
                type_stats[defect_type] = {
                    "total_count": 0,
                    "total_area_mm2": 0.0,
                    "total_area_pixels": 0,
                    "tiles_affected": 0,
                    "max_single_area_mm2": 0.0,
                    "avg_uncertainty": 0.0,
                    "uncertainty_sum": 0.0,
                    "uncertainty_n": 0,
                }
            
            ts = type_stats[defect_type]
            count = type_data.get("count", 0)
            ts["total_count"] += count
            ts["total_area_mm2"] += type_data.get("total_area_mm2", 0.0)
            ts["total_area_pixels"] += type_data.get("total_area_pixels", 0)
            
            if count > 0:
                ts["tiles_affected"] += 1
            
            for inst in type_data.get("instances", []):
                area = inst.get("area_mm2", 0.0)
                if area > ts["max_single_area_mm2"]:
                    ts["max_single_area_mm2"] = area
                unc = inst.get("uncertainty", 0.0)
                ts["uncertainty_sum"] += unc
                ts["uncertainty_n"] += 1
    
    # Compute averages
    for defect_type, ts in type_stats.items():
        if ts["uncertainty_n"] > 0:
            ts["avg_uncertainty"] = round(ts["uncertainty_sum"] / ts["uncertainty_n"], 4)
        ts["total_area_mm2"] = round(ts["total_area_mm2"], 2)
        ts["max_single_area_mm2"] = round(ts["max_single_area_mm2"], 2)
        del ts["uncertainty_sum"]
        del ts["uncertainty_n"]
    
    avg_defects_per_tile = round(total_defects / total_tiles, 2) if total_tiles > 0 else 0
    defect_free_pct = round((total_tiles - tiles_with_defects) / total_tiles * 100, 1) if total_tiles > 0 else 0
    
    return {
        "total_tiles_scanned": total_tiles,
        "tiles_with_defects": tiles_with_defects,
        "tiles_clean": total_tiles - tiles_with_defects,
        "defect_free_percentage": defect_free_pct,
        "total_defects": total_defects,
        "avg_defects_per_tile": avg_defects_per_tile,
        "total_defect_area_mm2": round(total_defect_area_mm2, 2),
        "total_defect_area_pixels": total_defect_area_pixels,
        "worst_tile": worst_tile,
        "worst_tile_area_pct": round(max_defect_area_pct, 2),
        "defect_type_breakdown": type_stats,
    }
