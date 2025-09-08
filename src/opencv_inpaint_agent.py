"""
OpenCV Inpainting Agent
Mask-guided defect removal using OpenCV's inpainting algorithms
Provides Telea and Navier-Stokes methods for different defect types
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


async def opencv_inpaint_agent(
    image_path: str,
    mask_path: str,
    method: str = "auto",
    inpaint_radius: int = 3,
    dilate_mask: bool = True
) -> Dict[str, Any]:
    """
    🎨 Inpaint defects using OpenCV algorithms
    
    Args:
        image_path: Path to image to repair
        mask_path: Path to defect mask (white = defects)
        method: "telea", "ns" (Navier-Stokes), or "auto"
        inpaint_radius: Radius of circular neighborhood for inpainting
        dilate_mask: Whether to dilate mask for better coverage
    
    Returns:
        Dictionary with:
        - success: Boolean indicating if inpainting succeeded
        - output_path: Path to inpainted image
        - method_used: Inpainting method applied
        - pixels_inpainted: Number of pixels repaired
    """
    
    try:
        # Load image and mask
        img = cv2.imread(image_path)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        
        if img is None or mask is None:
            print(f"❌ Could not load image or mask")
            return {
                "success": False,
                "output_path": image_path,
                "message": "Could not load input files"
            }
        
        # Ensure mask is binary
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
        
        # Optionally dilate mask for better defect coverage
        if dilate_mask:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask = cv2.dilate(mask, kernel, iterations=1)
        
        # Count pixels to be inpainted
        pixels_to_inpaint = cv2.countNonZero(mask)
        
        if pixels_to_inpaint == 0:
            print("ℹ️ No defects in mask, returning original")
            return {
                "success": True,
                "output_path": image_path,
                "method_used": "none",
                "pixels_inpainted": 0,
                "message": "No defects to inpaint"
            }
        
        print(f"🎨 Inpainting {pixels_to_inpaint} pixels using {method} method")
        
        # Choose inpainting method
        if method == "auto":
            # Auto-select based on defect characteristics
            # Use Telea for small defects, NS for larger areas
            if pixels_to_inpaint < 1000:
                method = "telea"
            else:
                method = "ns"
        
        # Apply inpainting
        if method == "telea":
            # Telea method - faster, good for small defects
            result = cv2.inpaint(img, mask, inpaint_radius, cv2.INPAINT_TELEA)
            method_name = "Telea"
        elif method == "ns":
            # Navier-Stokes method - slower, better for larger areas
            result = cv2.inpaint(img, mask, inpaint_radius, cv2.INPAINT_NS)
            method_name = "Navier-Stokes"
        else:
            # Fallback to Telea
            result = cv2.inpaint(img, mask, inpaint_radius, cv2.INPAINT_TELEA)
            method_name = "Telea (fallback)"
        
        # Save result
        output_path = str(Path("/tmp") / f"opencv_inpainted_{Path(image_path).stem}.png")
        cv2.imwrite(output_path, result)
        
        print(f"✅ Inpainting complete using {method_name}")
        
        return {
            "success": True,
            "output_path": output_path,
            "method_used": method_name,
            "pixels_inpainted": pixels_to_inpaint,
            "inpaint_radius": inpaint_radius,
            "message": f"Inpainted {pixels_to_inpaint} pixels"
        }
        
    except Exception as e:
        print(f"❌ OpenCV inpainting error: {e}")
        return {
            "success": False,
            "output_path": image_path,
            "message": str(e),
            "pixels_inpainted": 0
        }


async def smart_inpaint(
    image_path: str,
    defect_analysis: Dict[str, Any],
    aggressive: bool = False
) -> Dict[str, Any]:
    """
    Smart inpainting based on defect analysis
    Chooses optimal parameters based on defect types
    
    Args:
        image_path: Image to repair
        defect_analysis: Result from detect_defects_agent
        aggressive: Use more aggressive inpainting parameters
    
    Returns:
        Inpainting result
    """
    
    if not defect_analysis.get("has_defects"):
        return {
            "success": True,
            "output_path": image_path,
            "message": "No defects to repair"
        }
    
    mask_path = defect_analysis.get("mask_path")
    if not mask_path:
        return {
            "success": False,
            "output_path": image_path,
            "message": "No defect mask available"
        }
    
    # Determine optimal parameters based on defect types
    dust_count = defect_analysis.get("dust_count", 0)
    scratch_count = defect_analysis.get("scratch_count", 0)
    hot_pixel_count = defect_analysis.get("hot_pixel_count", 0)
    total_defects = defect_analysis.get("defect_count", 0)
    
    # Choose method and radius
    if scratch_count > dust_count:
        # Scratches need larger radius and NS method
        method = "ns"
        radius = 9 if aggressive else 7
    elif dust_count > 100:
        # Lots of dust - use NS with medium radius
        method = "ns"
        radius = 7 if aggressive else 5
    elif hot_pixel_count > 10:
        # Hot pixels need small radius, Telea is fine
        method = "telea"
        radius = 3
    else:
        # General defects - be more aggressive for larger defect counts
        method = "ns" if total_defects > 1000 else "telea"
        radius = 7 if aggressive else 5
    
    return await opencv_inpaint_agent(
        image_path,
        mask_path,
        method=method,
        inpaint_radius=radius,
        dilate_mask=aggressive
    )


async def iterative_inpaint(
    image_path: str,
    mask_path: str,
    iterations: int = 2,
    reduce_radius: bool = True
) -> Dict[str, Any]:
    """
    Apply inpainting iteratively for better results
    
    Args:
        image_path: Image to repair
        mask_path: Defect mask
        iterations: Number of inpainting passes
        reduce_radius: Reduce radius each iteration
    
    Returns:
        Final inpainting result
    """
    
    current_image = image_path
    current_radius = 5
    
    for i in range(iterations):
        print(f"🔄 Inpainting iteration {i+1}/{iterations}")
        
        result = await opencv_inpaint_agent(
            current_image,
            mask_path,
            method="telea" if i == 0 else "ns",  # Telea first, then NS
            inpaint_radius=current_radius,
            dilate_mask=(i == 0)  # Only dilate first iteration
        )
        
        if not result["success"]:
            break
            
        current_image = result["output_path"]
        
        if reduce_radius:
            current_radius = max(2, current_radius - 1)
    
    return result


def create_smart_mask(
    image_path: str,
    enhance_edges: bool = True,
    edge_threshold: int = 50
) -> str:
    """
    Create an intelligent mask that avoids important edges
    
    Args:
        image_path: Input image
        enhance_edges: Protect edges from inpainting
        edge_threshold: Threshold for edge detection
    
    Returns:
        Path to smart mask
    """
    
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    # Basic defect detection (simplified)
    _, bright = cv2.threshold(img, 250, 255, cv2.THRESH_BINARY)
    _, dark = cv2.threshold(img, 10, 255, cv2.THRESH_BINARY_INV)
    
    mask = cv2.bitwise_or(bright, dark)
    
    if enhance_edges:
        # Detect edges to protect
        edges = cv2.Canny(img, edge_threshold, edge_threshold * 2)
        
        # Dilate edges
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Remove mask pixels near edges
        mask = cv2.bitwise_and(mask, cv2.bitwise_not(edges))
    
    # Clean up small noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    mask_path = str(Path("/tmp") / f"smart_mask_{Path(image_path).stem}.png")
    cv2.imwrite(mask_path, mask)
    
    return mask_path


async def hybrid_repair(
    image_path: str,
    defect_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Combine G'MIC and OpenCV for optimal repair
    Use G'MIC for general repair, OpenCV for specific defects
    
    Args:
        image_path: Image to repair
        defect_analysis: Defect analysis results
    
    Returns:
        Repair result
    """
    
    from .gmic_repair_agent import gmic_repair_agent, check_gmic_available
    
    current_image = image_path
    repairs_applied = []
    
    # First pass: G'MIC if available
    if check_gmic_available() and defect_analysis.get("dust_count", 0) > 0:
        print("🔧 Pass 1: G'MIC dust removal")
        gmic_result = await gmic_repair_agent(
            current_image,
            repair_mode="dust",
            despeckle_size=5
        )
        if gmic_result["success"]:
            current_image = gmic_result["output_path"]
            repairs_applied.append("G'MIC dust removal")
    
    # Second pass: OpenCV for remaining defects
    if defect_analysis.get("scratch_count", 0) > 0:
        print("🎨 Pass 2: OpenCV scratch inpainting")
        mask_path = defect_analysis.get("mask_path")
        if mask_path:
            opencv_result = await opencv_inpaint_agent(
                current_image,
                mask_path,
                method="ns",
                inpaint_radius=5
            )
            if opencv_result["success"]:
                current_image = opencv_result["output_path"]
                repairs_applied.append("OpenCV scratch repair")
    
    return {
        "success": len(repairs_applied) > 0,
        "output_path": current_image,
        "repairs_applied": repairs_applied,
        "message": f"Applied {len(repairs_applied)} repair methods"
    }