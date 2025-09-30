"""
Quality Configuration Module
Centralized settings for preserving image quality throughout the pipeline
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# Quality presets
QUALITY_PRESETS = {
    "maximum": {
        "webp_quality": 100,
        "webp_lossless": True,
        "webp_method": 6,  # Slowest but best compression
        "jpeg_quality": 100,
        "png_compression": 0,  # No compression
        "imagemagick_quality": 100,
        "preserve_original_format": True,
        "use_lossless_intermediate": True
    },
    "ultra": {
        "webp_quality": 98,
        "webp_lossless": False,
        "webp_method": 6,
        "jpeg_quality": 98,
        "png_compression": 1,
        "imagemagick_quality": 98,
        "preserve_original_format": False,
        "use_lossless_intermediate": True
    },
    "high": {
        "webp_quality": 95,
        "webp_lossless": False,
        "webp_method": 6,
        "jpeg_quality": 95,
        "png_compression": 3,
        "imagemagick_quality": 95,
        "preserve_original_format": False,
        "use_lossless_intermediate": False
    },
    "balanced": {
        "webp_quality": 92,
        "webp_lossless": False,
        "webp_method": 4,
        "jpeg_quality": 92,
        "png_compression": 6,
        "imagemagick_quality": 92,
        "preserve_original_format": False,
        "use_lossless_intermediate": False
    },
    "web": {
        "webp_quality": 85,
        "webp_lossless": False,
        "webp_method": 4,
        "jpeg_quality": 85,
        "png_compression": 9,
        "imagemagick_quality": 85,
        "preserve_original_format": False,
        "use_lossless_intermediate": False
    }
}

def get_quality_settings(preset: Optional[str] = None) -> Dict[str, Any]:
    """
    Get quality settings based on preset or environment variables

    Args:
        preset: Name of preset ('maximum', 'ultra', 'high', 'balanced', 'web')

    Returns:
        Dictionary of quality settings
    """
    # Check environment for preset
    if preset is None:
        preset = os.getenv("QUALITY_PRESET", "maximum")  # Default to maximum quality

    # Get base settings from preset
    if preset in QUALITY_PRESETS:
        settings = QUALITY_PRESETS[preset].copy()
    else:
        # Default to ultra quality
        settings = QUALITY_PRESETS["ultra"].copy()

    # Allow environment variable overrides
    if os.getenv("WEBP_QUALITY"):
        settings["webp_quality"] = int(os.getenv("WEBP_QUALITY"))
    if os.getenv("WEBP_LOSSLESS"):
        settings["webp_lossless"] = os.getenv("WEBP_LOSSLESS", "false").lower() == "true"
    if os.getenv("JPEG_QUALITY"):
        settings["jpeg_quality"] = int(os.getenv("JPEG_QUALITY"))
    if os.getenv("IMAGEMAGICK_QUALITY"):
        settings["imagemagick_quality"] = int(os.getenv("IMAGEMAGICK_QUALITY"))
    if os.getenv("PRESERVE_FORMAT"):
        settings["preserve_original_format"] = os.getenv("PRESERVE_FORMAT", "false").lower() == "true"
    if os.getenv("USE_LOSSLESS_INTERMEDIATE"):
        settings["use_lossless_intermediate"] = os.getenv("USE_LOSSLESS_INTERMEDIATE", "false").lower() == "true"

    return settings

def get_save_kwargs(format: str, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get the appropriate save kwargs for a given format

    Args:
        format: Image format (e.g., 'WEBP', 'JPEG', 'PNG')
        settings: Quality settings dictionary

    Returns:
        Dictionary of save parameters
    """
    if settings is None:
        settings = get_quality_settings()

    format = format.upper()

    if format == 'WEBP':
        if settings["webp_lossless"]:
            return {
                'format': 'WEBP',
                'lossless': True,
                'quality': 100,
                'method': settings["webp_method"]
            }
        else:
            return {
                'format': 'WEBP',
                'quality': settings["webp_quality"],
                'method': settings["webp_method"],
                'lossless': False
            }

    elif format in ('JPEG', 'JPG'):
        return {
            'format': 'JPEG',
            'quality': settings["jpeg_quality"],
            'optimize': True,
            'progressive': True
        }

    elif format == 'PNG':
        return {
            'format': 'PNG',
            'compress_level': settings["png_compression"],
            'optimize': True
        }

    elif format == 'AVIF':
        # AVIF support via pillow-avif-plugin if available
        return {
            'format': 'AVIF',
            'quality': settings.get("webp_quality", 95),  # Use webp_quality as fallback
            'speed': 1  # Slowest but best quality
        }

    else:
        # Default fallback
        return {'format': format}

def save_with_quality(image, output_path: str, source_format: Optional[str] = None,
                      settings: Optional[Dict[str, Any]] = None):
    """
    Save an image with appropriate quality settings

    Args:
        image: PIL Image object
        output_path: Output file path
        source_format: Original format of the image (for preservation)
        settings: Quality settings dictionary
    """
    from PIL import Image

    if settings is None:
        settings = get_quality_settings()

    # Force lossless for images with transparency (e.g., from background removal)
    if hasattr(image, 'mode') and image.mode in ('RGBA', 'LA'):
        output_ext = Path(output_path).suffix.lower()
        if output_ext == '.webp' and not settings.get('webp_lossless'):
            print(f"🔒 Forcing lossless WebP for image with transparency")
            settings = settings.copy()
            settings['webp_lossless'] = True

    output_path = Path(output_path)

    # Determine output format
    if settings.get("preserve_original_format") and source_format:
        output_format = source_format.upper()
        # Update extension if needed
        if output_format == 'JPEG':
            output_path = output_path.with_suffix('.jpg')
        elif output_format == 'PNG':
            output_path = output_path.with_suffix('.png')
        elif output_format == 'WEBP':
            output_path = output_path.with_suffix('.webp')
    else:
        # Determine format from file extension
        ext_map = {
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.png': 'PNG',
            '.webp': 'WEBP',
            '.avif': 'AVIF'
        }
        output_format = ext_map.get(output_path.suffix.lower(), 'WEBP')

    # Get appropriate save parameters
    save_kwargs = get_save_kwargs(output_format, settings)

    # Save the image
    image.save(str(output_path), **save_kwargs)

    return str(output_path)

def get_intermediate_format(settings: Optional[Dict[str, Any]] = None) -> str:
    """
    Get the format to use for intermediate files

    Args:
        settings: Quality settings dictionary

    Returns:
        Format string ('PNG' for lossless, 'WEBP' for lossy)
    """
    if settings is None:
        settings = get_quality_settings()

    if settings.get("use_lossless_intermediate", True):
        return "PNG"
    else:
        return "WEBP"

def convert_for_api(image_path: str, api_name: str = "claude") -> tuple[str, bool]:
    """
    Convert image to a format compatible with the specified API

    Args:
        image_path: Path to input image
        api_name: Name of the API ('claude', 'gemini')

    Returns:
        Tuple of (converted_path, was_converted)
    """
    from PIL import Image
    import tempfile

    path_obj = Path(image_path)
    settings = get_quality_settings()

    # Check if conversion is needed
    if api_name == "claude" and path_obj.suffix.lower() == '.avif':
        # Claude doesn't support AVIF, convert to high-quality PNG or WebP
        with Image.open(image_path) as img:
            # Use lossless PNG for maximum quality preservation
            if settings.get("use_lossless_intermediate", True):
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                save_kwargs = get_save_kwargs('PNG', settings)
            else:
                temp_file = tempfile.NamedTemporaryFile(suffix='.webp', delete=False)
                save_kwargs = get_save_kwargs('WEBP', settings)

            img.save(temp_file.name, **save_kwargs)
            return temp_file.name, True

    return image_path, False

def get_imagemagick_quality_param(settings: Optional[Dict[str, Any]] = None) -> str:
    """
    Get the ImageMagick quality parameter

    Args:
        settings: Quality settings dictionary

    Returns:
        Quality parameter string for ImageMagick
    """
    if settings is None:
        settings = get_quality_settings()

    return f"-quality {settings['imagemagick_quality']}"