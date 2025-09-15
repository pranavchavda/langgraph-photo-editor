#!/usr/bin/env python3
"""
Test different upscaling methods to compare quality
"""

from PIL import Image, ImageFilter
import numpy as np

def enhanced_lanczos_upscale(img, target_width, target_height):
    """Enhanced Lanczos with better sharpening"""
    
    # Step 1: Upscale with Lanczos
    upscaled = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # Step 2: Apply unsharp mask for detail enhancement
    upscaled = upscaled.filter(ImageFilter.UnsharpMask(
        radius=1.5,  # Slightly larger radius
        percent=80,  # Stronger enhancement
        threshold=2  # Lower threshold for more sharpening
    ))
    
    # Step 3: Edge enhancement
    edges = upscaled.filter(ImageFilter.FIND_EDGES)
    edges = edges.filter(ImageFilter.GaussianBlur(0.5))
    
    # Blend edges back
    upscaled = Image.blend(upscaled, edges, 0.05)  # Subtle edge enhancement
    
    return upscaled

def bicubic_sharp_upscale(img, target_width, target_height):
    """Bicubic with aggressive sharpening"""
    
    # Use bicubic for smoother upscale
    upscaled = img.resize((target_width, target_height), Image.Resampling.BICUBIC)
    
    # Aggressive sharpening
    upscaled = upscaled.filter(ImageFilter.SHARPEN)
    upscaled = upscaled.filter(ImageFilter.UnsharpMask(
        radius=2,
        percent=100,
        threshold=1
    ))
    
    return upscaled

# Test with a sample image
if __name__ == "__main__":
    print("Enhanced upscaling methods for better quality than AI upscaling")
    print("\nOptions:")
    print("1. Enhanced Lanczos - Better sharpening and edge enhancement")
    print("2. Bicubic Sharp - Smoother upscale with aggressive sharpening")
    print("3. Consider using Real-ESRGAN locally for best quality")