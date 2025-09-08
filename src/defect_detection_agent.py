"""
Defect Detection Agent
Automatically detects dust, scratches, and hot pixels in images
Uses OpenCV morphological operations to create repair masks
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import os


async def detect_defects_agent(
    image_path: str,
    sensitivity: int = 50,
    min_dust_size: int = 3,
    max_dust_size: int = 15,
    scratch_threshold: int = 15
) -> Dict[str, Any]:
    """
    🔍 Detect dust, scratches, and other defects in an image
    
    Args:
        image_path: Path to the image to analyze
        sensitivity: Detection sensitivity (0-100, higher = more sensitive)
        min_dust_size: Minimum size of dust spots to detect (pixels)
        max_dust_size: Maximum size of dust spots to detect (pixels)
        scratch_threshold: Darkness threshold for scratch detection (0-255)
    
    Returns:
        Dictionary with:
        - has_defects: Boolean indicating if defects were found
        - mask_path: Path to the defect mask (if defects found)
        - defect_count: Number of defects detected
        - defect_types: List of defect types found
        - preview_path: Path to preview image showing detected defects
    """
    
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ Could not load image: {image_path}")
            return {"has_defects": False, "error": "Could not load image"}
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        
        # Initialize mask
        mask = np.zeros_like(gray)
        defect_types = []
        
        # 1. DETECT DUST (bright spots on dark surfaces)
        # Use local contrast to find bright spots relative to their surroundings
        # This is better for dust which appears as local bright anomalies
        
        # Apply Gaussian blur to get local average
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Find pixels significantly brighter than their local area
        diff = cv2.subtract(gray, blurred)
        
        # Threshold to find bright anomalies (dust appears brighter than surroundings)
        dust_sensitivity = 30 - (sensitivity * 0.2)  # 30 to 20 range
        _, bright_spots = cv2.threshold(diff, dust_sensitivity, 255, cv2.THRESH_BINARY)
        
        # Use morphological operations to filter noise
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (min_dust_size, min_dust_size))
        
        # Clean up noise
        bright_spots = cv2.morphologyEx(bright_spots, cv2.MORPH_OPEN, kernel_small)
        bright_spots = cv2.morphologyEx(bright_spots, cv2.MORPH_CLOSE, kernel_small)
        
        # Find connected components to filter by size
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bright_spots, connectivity=8)
        
        dust_mask = np.zeros_like(gray)
        dust_count = 0
        
        for i in range(1, num_labels):  # Skip background (label 0)
            area = stats[i, cv2.CC_STAT_AREA]
            if min_dust_size <= area <= max_dust_size * max_dust_size:
                dust_mask[labels == i] = 255
                dust_count += 1
        
        if dust_count > 0:
            mask = cv2.bitwise_or(mask, dust_mask)
            defect_types.append(f"dust ({dust_count} spots)")
        
        # 2. DETECT SCRATCHES (thin dark lines)
        # Use adaptive threshold for better scratch detection
        # Increase block size and C value to be less sensitive
        adaptive_thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 21, 5  # Was 11, 2 - now less sensitive
        )
        
        # Detect lines using morphological operations
        # Horizontal scratches
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        horizontal_scratches = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_OPEN, horizontal_kernel)
        horizontal_scratches = cv2.morphologyEx(horizontal_scratches, cv2.MORPH_CLOSE, horizontal_kernel)
        
        # Vertical scratches
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        vertical_scratches = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_OPEN, vertical_kernel)
        vertical_scratches = cv2.morphologyEx(vertical_scratches, cv2.MORPH_CLOSE, vertical_kernel)
        
        # Combine scratches
        scratches = cv2.bitwise_or(horizontal_scratches, vertical_scratches)
        
        # Filter out large areas (not scratches)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(scratches, connectivity=8)
        scratch_mask = np.zeros_like(gray)
        scratch_count = 0
        
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            width = stats[i, cv2.CC_STAT_WIDTH]
            height = stats[i, cv2.CC_STAT_HEIGHT]
            aspect_ratio = max(width, height) / max(min(width, height), 1)
            
            # Scratches are thin and elongated - make requirements stricter
            if aspect_ratio > 10 and area < 500:  # Was > 5 and < 1000
                scratch_mask[labels == i] = 255
                scratch_count += 1
        
        if scratch_count > 0:
            mask = cv2.bitwise_or(mask, scratch_mask)
            defect_types.append(f"scratches ({scratch_count} lines)")
        
        # 3. DETECT HOT PIXELS (single very bright pixels)
        # Look for isolated maximum brightness pixels - only pure white
        hot_pixel_threshold = 254  # Only detect near-white pixels
        _, hot_pixels = cv2.threshold(gray, hot_pixel_threshold, 255, cv2.THRESH_BINARY)
        
        # Erode to keep only isolated pixels
        kernel_tiny = np.ones((2, 2), np.uint8)
        hot_pixels = cv2.erode(hot_pixels, kernel_tiny, iterations=1)
        
        hot_pixel_count = cv2.countNonZero(hot_pixels)
        if hot_pixel_count > 0:
            mask = cv2.bitwise_or(mask, hot_pixels)
            defect_types.append(f"hot pixels ({hot_pixel_count})")
        
        # 4. DETECT DARK SPOTS (sensor dust on lens)
        # Look for dark circular spots - make much less sensitive
        dark_threshold = 30 + (100 - sensitivity) * 0.3  # 30 to 60 range (was 50 to 100)
        _, dark_spots = cv2.threshold(gray, dark_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Filter for circular spots
        kernel_circular = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        dark_spots = cv2.morphologyEx(dark_spots, cv2.MORPH_OPEN, kernel_circular)
        dark_spots = cv2.morphologyEx(dark_spots, cv2.MORPH_CLOSE, kernel_circular)
        
        # Filter by size and circularity
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(dark_spots, connectivity=8)
        dark_spot_mask = np.zeros_like(gray)
        dark_spot_count = 0
        
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if 10 <= area <= 500:  # Reasonable size for sensor dust
                dark_spot_mask[labels == i] = 255
                dark_spot_count += 1
        
        if dark_spot_count > 0:
            mask = cv2.bitwise_or(mask, dark_spot_mask)
            defect_types.append(f"sensor dust ({dark_spot_count} spots)")
        
        # Dilate mask slightly for better coverage
        dilation_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.dilate(mask, dilation_kernel, iterations=1)
        
        # Count total defects
        total_defects = cv2.countNonZero(mask)
        
        print(f"🔍 Defect detection results:")
        print(f"   - Dust spots: {dust_count}")
        print(f"   - Scratches: {scratch_count}")  
        print(f"   - Hot pixels: {hot_pixel_count}")
        print(f"   - Dark spots: {dark_spot_count}")
        print(f"   - Total defect pixels: {total_defects}")
        
        # Check if we found any defects - raised threshold to reduce false positives
        if total_defects > 200:  # Minimum threshold to consider defects present (was 50)
            # Save mask
            mask_filename = f"defect_mask_{Path(image_path).stem}.png"
            mask_path = str(Path("/tmp") / mask_filename)
            cv2.imwrite(mask_path, mask)
            
            # Create preview image showing defects
            preview = img.copy()
            
            # Overlay mask in red
            overlay = preview.copy()
            overlay[mask > 0] = [0, 0, 255]  # Red for defects
            preview = cv2.addWeighted(preview, 0.7, overlay, 0.3, 0)
            
            # Add contours around defects
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(preview, contours, -1, (0, 255, 0), 1)  # Green contours
            
            # Save preview
            preview_filename = f"defect_preview_{Path(image_path).stem}.jpg"
            preview_path = str(Path("/tmp") / preview_filename)
            cv2.imwrite(preview_path, preview)
            
            print(f"🔍 Defects detected: {', '.join(defect_types)}")
            print(f"   Total defect pixels: {total_defects}")
            print(f"   Mask saved to: {mask_path}")
            
            return {
                "has_defects": True,
                "mask_path": mask_path,
                "defect_count": total_defects,
                "defect_types": defect_types,
                "preview_path": preview_path,
                "dust_count": dust_count,
                "scratch_count": scratch_count,
                "hot_pixel_count": hot_pixel_count,
                "dark_spot_count": dark_spot_count
            }
        else:
            print(f"✅ No significant defects detected (only {total_defects} pixels, threshold is 200)")
            return {
                "has_defects": False,
                "defect_count": total_defects,
                "dust_count": dust_count,
                "scratch_count": scratch_count,
                "hot_pixel_count": hot_pixel_count,
                "dark_spot_count": dark_spot_count,
                "message": f"Minor defects below threshold ({total_defects} pixels)"
            }
            
    except Exception as e:
        print(f"❌ Defect detection error: {e}")
        return {
            "has_defects": False,
            "error": str(e)
        }


def visualize_defects(image_path: str, mask_path: str, output_path: str) -> str:
    """
    Create a side-by-side visualization of original and defects
    
    Args:
        image_path: Original image
        mask_path: Defect mask
        output_path: Where to save visualization
    
    Returns:
        Path to visualization image
    """
    img = cv2.imread(image_path)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    
    # Create colored overlay
    overlay = img.copy()
    overlay[mask > 0] = [0, 0, 255]  # Red for defects
    
    # Blend
    result = cv2.addWeighted(img, 0.7, overlay, 0.3, 0)
    
    # Create side-by-side
    vis = np.hstack([img, result])
    
    cv2.imwrite(output_path, vis)
    return output_path