"""
Real-time preview utilities for slider adjustments
Uses PIL for fast preview generation
"""

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from typing import Optional
import io

def apply_preview_adjustments(
    image: Image.Image,
    gamma: float = 1.0,
    brightness: int = 0,
    contrast: int = 0,
    saturation: int = 100,
    highlights: int = 0,
    shadows: int = 0,
    sharpness_radius: float = 1.0,
    sharpness_sigma: float = 0.5
) -> Image.Image:
    """
    Apply adjustments to image for preview purposes
    Uses PIL for fast processing suitable for real-time updates
    """
    # Make a copy to avoid modifying original
    img = image.copy()
    
    # Convert to RGB if needed (for consistency)
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')
    
    # 1. Gamma adjustment
    if gamma != 1.0:
        # Apply gamma using numpy for speed
        img_array = np.array(img).astype(float) / 255.0
        img_array = np.power(img_array, 1.0 / gamma)
        img_array = (img_array * 255).astype(np.uint8)
        img = Image.fromarray(img_array, mode=img.mode)
    
    # 2. Brightness adjustment (-10 to +10 mapped to 0.9 to 1.1)
    if brightness != 0:
        enhancer = ImageEnhance.Brightness(img)
        factor = 1.0 + (brightness / 100.0)  # -10 becomes 0.9, +10 becomes 1.1
        img = enhancer.enhance(factor)
    
    # 3. Contrast adjustment (-10 to +10 mapped to 0.9 to 1.1)
    if contrast != 0:
        enhancer = ImageEnhance.Contrast(img)
        factor = 1.0 + (contrast / 100.0)
        img = enhancer.enhance(factor)
    
    # 4. Saturation adjustment (90-120 mapped to 0.9 to 1.2)
    if saturation != 100:
        enhancer = ImageEnhance.Color(img)
        factor = saturation / 100.0
        img = enhancer.enhance(factor)
    
    # 5. Highlights/Shadows (simplified for preview)
    if highlights != 0 or shadows != 0:
        # Convert to numpy for level adjustments
        img_array = np.array(img).astype(float)
        
        # Simple shadows lift (affects dark areas more)
        if shadows > 0:
            shadow_factor = shadows / 100.0
            img_array = img_array + (255 - img_array) * shadow_factor * (1 - img_array/255)
        
        # Simple highlights compression (affects bright areas more)
        if highlights < 0:
            highlight_factor = abs(highlights) / 100.0
            img_array = img_array * (1 - highlight_factor * (img_array/255))
        
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        img = Image.fromarray(img_array, mode=img.mode)
    
    # 6. Sharpness (using UnsharpMask)
    if sharpness_radius > 0:
        # PIL's UnsharpMask is good for preview
        img = img.filter(ImageFilter.UnsharpMask(
            radius=sharpness_radius,
            percent=int(sharpness_sigma * 100),
            threshold=3
        ))
    
    return img

def generate_preview_from_sliders(
    source_image_path: str,
    gamma: float = 1.0,
    brightness: int = 0,
    contrast: int = 0,
    saturation: int = 108,
    highlights: int = -5,
    shadows: int = 3,
    sharpness_radius: float = 1.0,
    sharpness_sigma: float = 0.5,
    max_size: tuple = (800, 800)
) -> bytes:
    """
    Generate a preview image from slider values
    Returns bytes suitable for displaying in Streamlit
    """
    # Load and resize for faster preview
    img = Image.open(source_image_path)
    
    # Resize for faster processing (maintaining aspect ratio)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Apply adjustments
    img = apply_preview_adjustments(
        img,
        gamma=gamma,
        brightness=brightness,
        contrast=contrast,
        saturation=saturation,
        highlights=highlights,
        shadows=shadows,
        sharpness_radius=sharpness_radius,
        sharpness_sigma=sharpness_sigma
    )
    
    # Convert to bytes for Streamlit
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()