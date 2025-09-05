"""
Native Python Image Processing Agent
Alternative to ImageMagick using Python libraries for high-quality image processing
"""

import asyncio
from pathlib import Path
from typing import Dict, Any
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2
from .agents_enhanced import AgentError

def get_stream_writer():
    """Get the stream writer for progress updates"""
    try:
        from langgraph.config import get_stream_writer
        return get_stream_writer()
    except:
        return lambda x: None


async def python_optimization_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """
    🐍 Python Native Image Processing Agent
    High-quality image optimization using Python libraries
    """
    writer = get_stream_writer()
    
    writer({
        "agent": "python_optimizer",
        "status": "processing",
        "message": "Applying high-quality Python-based optimizations"
    })
    
    try:
        # Load image
        img = Image.open(image_path)
        original_width, original_height = img.size
        
        # Convert to RGB if needed (for consistency)
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        
        # 1. Auto-adjust brightness and contrast
        if "uneven_lighting" in analysis.get("lighting_issues", []):
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.1)  # 10% brighter
            
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.15)  # 15% more contrast
        
        # 2. Enhance vibrancy and saturation
        if "needs_vibrancy_boost" in analysis.get("color_problems", []):
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.2)  # 20% more vibrant
        
        # 3. Sharpen details
        if any("sharp" in issue for issue in analysis.get("optimization_priority", [])):
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=50, threshold=3))
        
        # 4. Advanced color correction using OpenCV
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Auto white balance
        if "color_cast" in analysis.get("lighting_issues", []):
            result = cv2.xphoto.createGrayworldWB()
            result.balanceWhite(img_cv, img_cv)
        
        # Enhance local contrast with CLAHE
        lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l_channel = clahe.apply(l_channel)
        
        lab = cv2.merge([l_channel, a_channel, b_channel])
        img_cv = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Convert back to PIL
        img = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        
        # 5. Noise reduction for surface materials
        if "dust_issues" in analysis or "surface_dirt" in analysis.get("dust_issues", []):
            # Gentle denoising
            img_array = np.array(img)
            denoised = cv2.fastNlMeansDenoisingColored(img_array, None, 3, 3, 7, 21)
            img = Image.fromarray(denoised)
        
        # 6. Material-specific enhancement
        materials = analysis.get("surface_materials", [])
        if "chrome" in materials or "stainless_steel" in materials:
            # Enhance metallic surfaces
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.05)
            
            # Slight sharpening for reflections
            img = img.filter(ImageFilter.SHARPEN)
        
        if "wood_grain" in materials:
            # Enhance wood texture
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)  # Warm up wood tones
        
        # 7. Final quality pass
        # Ensure we maintain original resolution
        if img.size != (original_width, original_height):
            img = img.resize((original_width, original_height), Image.Resampling.LANCZOS)
        
        # Save with high quality
        output_path = str(Path(image_path).parent / f"{Path(image_path).stem}-python-optimized.webp")
        img.save(output_path, 'WEBP', quality=95, method=6)
        
        writer({
            "agent": "python_optimizer",
            "status": "complete",
            "output": output_path,
            "message": f"Python optimization complete: {Path(output_path).name}"
        })
        
        return output_path
        
    except Exception as e:
        error_msg = f"Python optimization failed: {str(e)}"
        writer({
            "agent": "python_optimizer", 
            "status": "error",
            "message": error_msg
        })
        raise AgentError(error_msg)