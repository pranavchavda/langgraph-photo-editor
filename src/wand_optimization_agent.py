"""
Wand-based ImageMagick Agent
High-quality image optimization using Wand (Python bindings for ImageMagick)
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import base64
from io import BytesIO

try:
    from wand.image import Image as WandImage
    from wand.display import display
    WAND_AVAILABLE = True
except ImportError:
    WAND_AVAILABLE = False
    print("⚠️ Wand not available - ImageMagick Python bindings not installed")

from PIL import Image as PILImage
import numpy as np


def get_stream_writer():
    """Get the stream writer for progress updates"""
    try:
        from langgraph.config import get_stream_writer
        return get_stream_writer()
    except:
        return lambda x: None


async def wand_optimization_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """
    🎨 Wand-based ImageMagick Optimization Agent
    Professional-grade image processing using ImageMagick through Python
    """
    writer = get_stream_writer()
    
    if not WAND_AVAILABLE:
        writer({
            "agent": "wand_optimizer",
            "status": "error",
            "message": "Wand not available - falling back to subprocess ImageMagick"
        })
        # Fall back to the original subprocess-based agent
        from .agents_enhanced import imagemagick_optimization_agent
        return await imagemagick_optimization_agent(image_path, analysis)
    
    writer({
        "agent": "wand_optimizer",
        "status": "processing",
        "message": "Applying professional ImageMagick optimizations via Wand"
    })
    
    try:
        with WandImage(filename=image_path) as img:
            # Store original dimensions
            original_width = img.width
            original_height = img.height
            
            # 1. Color and Exposure Adjustments
            lighting_issues = analysis.get("lighting_issues", [])
            color_problems = analysis.get("color_problems", [])
            
            if "uneven_lighting" in lighting_issues or "harsh_shadows" in lighting_issues:
                # Sigmoidal contrast for better shadow/highlight balance
                img.sigmoidal_contrast(sharpen=True, strength=3, midpoint=0.5)
                writer({"agent": "wand_optimizer", "status": "info", "message": "Applied lighting corrections"})
            
            if "needs_vibrancy_boost" in color_problems:
                # Modulate for vibrancy (brightness, saturation, hue)
                img.modulate(brightness=105, saturation=115, hue=100)
                writer({"agent": "wand_optimizer", "status": "info", "message": "Enhanced vibrancy"})
            
            if "slight_color_cast" in lighting_issues:
                # Auto white balance
                img.auto_level()
                img.auto_gamma()
                writer({"agent": "wand_optimizer", "status": "info", "message": "Corrected color cast"})
            
            # 2. Material-specific Enhancements
            materials = analysis.get("surface_materials", [])
            
            if "chrome" in materials or "stainless_steel" in materials:
                # Enhance metallic surfaces with local contrast
                img.adaptive_sharpen(radius=1.0, sigma=0.5)
                # Increase contrast for reflections
                img.brightness_contrast(brightness=2, contrast=5)
                writer({"agent": "wand_optimizer", "status": "info", "message": "Enhanced metallic surfaces"})
            
            if "wood_grain" in materials:
                # Enhance wood texture with edge enhancement
                with img.clone() as edge:
                    edge.edge(radius=1)
                    edge.negate()
                    img.composite(edge, left=0, top=0, operator='multiply')
                # Warm up wood tones slightly
                img.colorize(color='#FFF5E6', alpha=0.05)
                writer({"agent": "wand_optimizer", "status": "info", "message": "Enhanced wood grain"})
            
            if "matte_surfaces" in materials:
                # Gentle enhancement for matte surfaces
                img.unsharp_mask(radius=0.5, sigma=0.5, amount=0.5, threshold=0.02)
                writer({"agent": "wand_optimizer", "status": "info", "message": "Enhanced matte surfaces"})
            
            # 3. Sharpness and Detail Enhancement
            # Professional unsharp mask settings
            img.unsharp_mask(
                radius=1.0,    # Radius of the Gaussian blur
                sigma=0.5,     # Standard deviation of the Gaussian
                amount=0.8,    # Percentage of the difference to add
                threshold=0.05 # Threshold to prevent sharpening noise
            )
            writer({"agent": "wand_optimizer", "status": "info", "message": "Applied professional sharpening"})
            
            # 4. Dust and Spot Removal
            if analysis.get("needs_dust_removal"):
                dust_issues = analysis.get("dust_issues", [])
                if "spots" in dust_issues or "sensor_debris" in dust_issues:
                    # Use median filter for dust removal
                    img.statistic('median', width=3, height=3)
                    writer({"agent": "wand_optimizer", "status": "info", "message": "Removed dust spots"})
            
            # 5. Final Quality Enhancements
            # Reduce noise while preserving details
            img.enhance()
            
            # Ensure we maintain original resolution
            if img.width != original_width or img.height != original_height:
                img.resize(width=original_width, height=original_height, filter='lanczos')
            
            # 6. Optimize and Save
            output_path = str(Path(image_path).parent / f"{Path(image_path).stem}-optimized.webp")
            
            # Set WebP compression options for maximum quality
            img.options['webp:method'] = '6'  # Slowest/best compression
            img.options['webp:lossless'] = 'false'
            img.options['webp:auto-filter'] = 'true'
            img.options['webp:alpha-quality'] = '100'
            img.compression_quality = 95
            
            img.save(filename=output_path)
            
            writer({
                "agent": "wand_optimizer",
                "status": "complete",
                "output": output_path,
                "message": f"Wand optimization complete: {Path(output_path).name}"
            })
            
            return output_path
            
    except Exception as e:
        error_msg = f"Wand optimization failed: {str(e)}"
        writer({
            "agent": "wand_optimizer",
            "status": "error",
            "message": error_msg
        })
        
        # Fall back to subprocess-based ImageMagick
        from .agents_enhanced import imagemagick_optimization_agent
        writer({
            "agent": "wand_optimizer",
            "status": "info",
            "message": "Falling back to subprocess ImageMagick"
        })
        return await imagemagick_optimization_agent(image_path, analysis)


async def smart_crop_agent(image_path: str, analysis: Dict[str, Any]) -> Tuple[str, Dict]:
    """
    ✂️ Smart Cropping Agent
    Intelligently crops images based on composition analysis
    """
    writer = get_stream_writer()
    
    writer({
        "agent": "smart_crop",
        "status": "analyzing",
        "message": "Analyzing image composition for optimal cropping"
    })
    
    try:
        # Check if cropping is needed from analysis
        needs_cropping = analysis.get("needs_cropping", False)
        crop_suggestion = analysis.get("crop_suggestion", None)
        
        if not needs_cropping and not crop_suggestion:
            writer({
                "agent": "smart_crop",
                "status": "skipped",
                "message": "No cropping needed - composition is good"
            })
            return image_path, {"cropped": False}
        
        with WandImage(filename=image_path) as img:
            original_width = img.width
            original_height = img.height
            
            # Default: try to detect edges and crop to content
            if crop_suggestion and "auto" in str(crop_suggestion).lower():
                # Auto-trim whitespace/uniform borders
                img.trim(fuzz=0.1)
                
                # Add small padding back
                padding = 20
                img.border(color='white', width=padding, height=padding)
                
            elif crop_suggestion and isinstance(crop_suggestion, dict):
                # Specific crop coordinates from analysis
                left = crop_suggestion.get('left', 0)
                top = crop_suggestion.get('top', 0)
                width = crop_suggestion.get('width', original_width)
                height = crop_suggestion.get('height', original_height)
                
                img.crop(left=left, top=top, width=width, height=height)
                
            else:
                # Smart center crop - remove 5% from edges if image is too loose
                if original_width > 2000 and original_height > 2000:
                    crop_margin = 0.05  # 5% from each edge
                    new_width = int(original_width * (1 - 2 * crop_margin))
                    new_height = int(original_height * (1 - 2 * crop_margin))
                    left = int(original_width * crop_margin)
                    top = int(original_height * crop_margin)
                    
                    img.crop(left=left, top=top, width=new_width, height=new_height)
            
            # Save cropped version
            output_path = str(Path(image_path).parent / f"{Path(image_path).stem}-cropped{Path(image_path).suffix}")
            img.save(filename=output_path)
            
            new_width = img.width
            new_height = img.height
            
            writer({
                "agent": "smart_crop",
                "status": "complete",
                "message": f"Cropped from {original_width}x{original_height} to {new_width}x{new_height}"
            })
            
            return output_path, {
                "cropped": True,
                "original_size": (original_width, original_height),
                "new_size": (new_width, new_height),
                "reduction": f"{(1 - (new_width * new_height) / (original_width * original_height)) * 100:.1f}%"
            }
            
    except Exception as e:
        writer({
            "agent": "smart_crop",
            "status": "error",
            "message": f"Cropping failed: {str(e)}"
        })
        return image_path, {"cropped": False, "error": str(e)}