"""
Enhanced Agentic Photo Editor - 5-Agent System with Gemini 2.5 Flash Image
Combines Claude Sonnet 4 analysis with Gemini 2.5 Flash Image editing and ImageMagick optimization
"""

import asyncio
import os
import base64
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List

import google.generativeai as genai
from anthropic import AsyncAnthropic
import requests
from langgraph.config import get_stream_writer
from langgraph.func import task
from .quality_config import get_quality_settings, save_with_quality, convert_for_api, get_imagemagick_quality_param

# Global clients - initialized lazily
anthropic_client = None

def get_anthropic_client():
    """Get or create Anthropic client with current API key"""
    global anthropic_client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise AgentError("ANTHROPIC_API_KEY not set")
    if anthropic_client is None or anthropic_client.api_key != api_key:
        anthropic_client = AsyncAnthropic(api_key=api_key)
    return anthropic_client

def configure_gemini():
    """Configure Gemini with current API key"""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    else:
        raise AgentError("GEMINI_API_KEY not set")


class AgentError(Exception):
    """Custom exception for agent failures"""
    pass


# Base ImageMagick configuration inspired by Darktable XMP settings
# These values are derived from analyzing professional photo editing presets
IMAGEMAGICK_BASE_CONFIG = {
    "gamma": 1.0,           # Base gamma (0.8-1.2) - Darktable uses neutral
    "brightness": 0,        # Brightness adjustment (-10 to +10)
    "contrast": 2,          # Slight contrast boost inspired by RGB levels
    "saturation": 108,      # Slightly increased saturation (was 105)
    "sharpness": "1.0x0.5", # Moderate sharpening (Darktable sharpen enabled)
    "highlights": -5,       # Slight highlight recovery (Darktable highlights enabled)
    "shadows": 3,           # Slight shadow lift from RGB levels midpoint ~0.613
    "quality": 100,         # Output quality (maximum by default)
    "vibrance": 0,          # Vibrance adjustment (-100 to +100) - affects less saturated colors
    "hue_shift": 0,         # Hue rotation in degrees (-180 to +180)
    "color_balance": {      # Color balance adjustments
        "red": 0,           # Red channel adjustment (-100 to +100)
        "green": 0,         # Green channel adjustment (-100 to +100)  
        "blue": 0           # Blue channel adjustment (-100 to +100)
    },
    "auto_level": False,    # Apply auto-level (careful - can overexpose)
    "auto_gamma": False,    # Apply auto-gamma correction
    "normalize": False,     # Normalize histogram (careful - can overexpose)
    "equalize": False,      # Equalize histogram (very aggressive)
    "clahe": False,         # Contrast Limited Adaptive Histogram Equalization
    "denoise": 0,           # Noise reduction level (0-100)
    "blur": 0,              # Gaussian blur radius (0-10)
    "edge_enhance": False,  # Edge enhancement filter
    "despeckle": False,     # Remove speckle noise
    "trim": False,          # Auto-trim whitespace
    "trim_fuzz": 5,         # Fuzz factor for trimming (%)
    "resize": None,         # Resize dimensions (e.g., "1920x1080")
    "resize_filter": "Lanczos", # Resize filter (Lanczos, Mitchell, Catrom, etc.)
    "unsharp_mask": None,   # Alternative unsharp mask (e.g., "0x1+1+0.05")
    "modulate_separate": False, # Apply brightness/saturation/hue separately
    "colorspace": None,     # Convert to colorspace (e.g., "sRGB", "Lab", "HSL")
    "channel_ops": {},      # Per-channel operations {"red": "-gamma 1.1", ...}
}

def get_base_imagemagick_command():
    """Get the base ImageMagick command with Darktable-inspired optimizations"""
    # Allow environment variable override for simple command
    custom_base = os.getenv('IMAGEMAGICK_BASE_CONFIG')
    if custom_base:
        print(f"🎛️ Using custom base config: {custom_base}")
        return custom_base
    
    # Get quality settings from quality_config module
    quality_settings = get_quality_settings()

    # Load config from environment or use defaults
    config = IMAGEMAGICK_BASE_CONFIG.copy()

    # Override quality with the quality_config setting
    config['quality'] = quality_settings.get('imagemagick_quality', 95)

    # Allow environment overrides for individual settings
    env_overrides = {
        'IMAGEMAGICK_GAMMA': ('gamma', float),
        'IMAGEMAGICK_BRIGHTNESS': ('brightness', int),
        'IMAGEMAGICK_CONTRAST': ('contrast', int),
        'IMAGEMAGICK_SATURATION': ('saturation', int),
        'IMAGEMAGICK_SHARPNESS': ('sharpness', str),
        'IMAGEMAGICK_HIGHLIGHTS': ('highlights', int),
        'IMAGEMAGICK_SHADOWS': ('shadows', int),
        'IMAGEMAGICK_QUALITY': ('quality', int),  # Can override with env var
        'IMAGEMAGICK_VIBRANCE': ('vibrance', int),
        'IMAGEMAGICK_HUE_SHIFT': ('hue_shift', int),
        'IMAGEMAGICK_DENOISE': ('denoise', int),
        'IMAGEMAGICK_BLUR': ('blur', float),
        'IMAGEMAGICK_AUTO_LEVEL': ('auto_level', lambda x: x.lower() == 'true'),
        'IMAGEMAGICK_AUTO_GAMMA': ('auto_gamma', lambda x: x.lower() == 'true'),
        'IMAGEMAGICK_NORMALIZE': ('normalize', lambda x: x.lower() == 'true'),
        'IMAGEMAGICK_TRIM': ('trim', lambda x: x.lower() == 'true'),
        'IMAGEMAGICK_TRIM_FUZZ': ('trim_fuzz', int),
        'IMAGEMAGICK_RESIZE': ('resize', str),
        'IMAGEMAGICK_COLORSPACE': ('colorspace', str),
    }
    
    for env_var, (config_key, converter) in env_overrides.items():
        env_value = os.getenv(env_var)
        if env_value:
            try:
                config[config_key] = converter(env_value)
                print(f"🎛️ Override {config_key}: {config[config_key]}")
            except (ValueError, TypeError):
                print(f"⚠️ Invalid value for {env_var}: {env_value}")
    
    print(f"🎛️ Base config: gamma={config['gamma']}, brightness={config['brightness']}, contrast={config['contrast']}, saturation={config['saturation']}")
    
    # Build base command
    cmd_parts = []
    
    # IMPORTANT: Order matters in ImageMagick!
    
    # 0. Colorspace conversion (if specified)
    if config.get("colorspace"):
        cmd_parts.append(f"-colorspace {config['colorspace']}")
    
    # 1. Auto adjustments (if enabled)
    if config.get("auto_level"):
        cmd_parts.append("-auto-level")
    if config.get("auto_gamma"):
        cmd_parts.append("-auto-gamma")
    if config.get("normalize"):
        cmd_parts.append("-normalize")
    if config.get("equalize"):
        cmd_parts.append("-equalize")
    
    # 2. Trim (if enabled)
    if config.get("trim"):
        fuzz = config.get("trim_fuzz", 5)
        cmd_parts.append(f"-fuzz {fuzz}% -trim +repage")
    
    # 3. Gamma adjustment (affects overall brightness)
    if config["gamma"] != 1.0:
        cmd_parts.append(f"-gamma {config['gamma']}")
    
    # 4. Brightness/Contrast adjustments
    if config["brightness"] != 0 or config["contrast"] != 0:
        cmd_parts.append(f"-brightness-contrast {config['brightness']}x{config['contrast']}")
    
    # 5. Highlight/Shadow adjustment using -level
    highlights = config.get("highlights", 0)
    shadows = config.get("shadows", 0)
    if highlights != 0 or shadows != 0:
        black_point = max(0, shadows)  # Lift shadows
        white_point = min(100, 100 + highlights)  # Compress highlights
        if black_point != 0 or white_point != 100:
            cmd_parts.append(f"-level {black_point}%,{white_point}%")
    
    # 6. Color adjustments
    saturation = config["saturation"]
    vibrance = config.get("vibrance", 0)
    hue_shift = config.get("hue_shift", 0)
    
    if config.get("modulate_separate"):
        # Apply modulate components separately for more control
        if saturation != 100:
            cmd_parts.append(f"-modulate 100,{saturation},100")
        if hue_shift != 0:
            # Convert degrees to ImageMagick hue units (200 = full rotation)
            hue_value = 100 + (hue_shift / 180 * 100)
            cmd_parts.append(f"-modulate 100,100,{hue_value}")
    else:
        # Combined modulate
        if saturation != 100 or hue_shift != 0:
            hue_value = 100 + (hue_shift / 180 * 100) if hue_shift != 0 else 100
            cmd_parts.append(f"-modulate 100,{saturation},{hue_value}")
    
    # 7. Vibrance (affects less saturated colors more)
    if vibrance != 0:
        # Vibrance is more complex - use a simplified approach
        if vibrance > 0:
            cmd_parts.append(f"-colorspace HSL -channel G -sigmoidal-contrast {vibrance/10},50% +channel -colorspace sRGB")
        else:
            cmd_parts.append(f"-colorspace HSL -channel G +sigmoidal-contrast {abs(vibrance)/10},50% +channel -colorspace sRGB")
    
    # 8. Color balance
    color_balance = config.get("color_balance", {})
    if any(color_balance.get(c, 0) != 0 for c in ['red', 'green', 'blue']):
        r_adj = color_balance.get('red', 0)
        g_adj = color_balance.get('green', 0)
        b_adj = color_balance.get('blue', 0)
        if r_adj != 0:
            cmd_parts.append(f"-channel R -evaluate add {r_adj}% +channel")
        if g_adj != 0:
            cmd_parts.append(f"-channel G -evaluate add {g_adj}% +channel")
        if b_adj != 0:
            cmd_parts.append(f"-channel B -evaluate add {b_adj}% +channel")
    
    # 9. Noise reduction
    if config.get("denoise", 0) > 0:
        cmd_parts.append(f"-enhance -despeckle -enhance") if config["denoise"] > 50 else cmd_parts.append("-enhance")
    elif config.get("despeckle"):
        cmd_parts.append("-despeckle")
    
    # 10. Blur
    if config.get("blur", 0) > 0:
        cmd_parts.append(f"-blur 0x{config['blur']}")
    
    # 11. Edge enhancement
    if config.get("edge_enhance"):
        cmd_parts.append("-edge 1")
    
    # 12. Sharpening (should be near the end)
    if config.get("unsharp_mask"):
        cmd_parts.append(f"-unsharp {config['unsharp_mask']}")
    elif config["sharpness"]:
        cmd_parts.append(f"-unsharp {config['sharpness']}")
    
    # 13. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    if config.get("clahe"):
        cmd_parts.append("-clahe 25x25+128+3")
    
    # 14. Resize (if specified)
    if config.get("resize"):
        filter_type = config.get("resize_filter", "Lanczos")
        cmd_parts.append(f"-filter {filter_type} -resize {config['resize']}")
    
    # 15. Output quality
    cmd_parts.append(f"-quality {config['quality']}")
    
    final_command = " ".join(cmd_parts)
    print(f"🎛️ Final ImageMagick command: {final_command}")
    return final_command

def get_imagemagick_command():
    """Get the correct ImageMagick command for the platform"""
    import shutil
    
    # Try different ImageMagick command variations
    for cmd in ['magick', 'convert', 'imagemagick']:
        if shutil.which(cmd):
            return cmd
    
    # If no command found, return None
    return None


def encode_image_to_base64(image_path: str) -> tuple[str, str]:
    """Encode image to base64 string with quality preservation
    Returns: (base64_string, actual_image_path)
    """
    from PIL import Image
    import tempfile

    # Use quality_config for any necessary conversions
    converted_path, was_converted = convert_for_api(image_path, api_name="claude")

    try:
        # Check file size
        file_size = os.path.getsize(converted_path)

        # Claude's limit is 5MB for base64 encoded images
        # Base64 increases size by ~33%, so we need to stay under ~3.7MB
        max_file_size = 3.7 * 1024 * 1024  # 3.7 MB before base64 encoding

        analysis_image_path = converted_path  # Path for Claude analysis only

        if file_size > max_file_size:
            print(f"⚠️ Image too large for Claude ({file_size / 1024 / 1024:.1f} MB), compressing for analysis only...")

            # Open and compress the image (same resolution, lower quality)
            with Image.open(converted_path) as img:
                # Save to temp file with compressed quality FOR CLAUDE ONLY
                temp_file = tempfile.NamedTemporaryFile(suffix='.webp', delete=False)

                # Use lower quality to get under size limit
                # Start with quality 80 and reduce if needed
                quality = 80
                while quality >= 40:
                    img.save(temp_file.name, 'WEBP', quality=quality, method=4)
                    compressed_size = os.path.getsize(temp_file.name)

                    if compressed_size <= max_file_size:
                        print(f"✅ Compressed for Claude analysis: quality {quality}")
                        print(f"📦 Size for Claude: {file_size / 1024 / 1024:.1f} MB → {compressed_size / 1024 / 1024:.1f} MB")
                        print(f"📐 Resolution maintained: {img.width}x{img.height}")
                        print(f"⚠️ NOTE: Full quality image will be used for processing")
                        analysis_image_path = temp_file.name
                        break

                    quality -= 10
                else:
                    # If still too large, we have to resize as last resort
                    print(f"⚠️ Cannot compress enough, resizing as last resort...")
                    scale_factor = (max_file_size / compressed_size) ** 0.5
                    new_width = int(img.width * scale_factor)
                    new_height = int(img.height * scale_factor)
                    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    resized.save(temp_file.name, 'WEBP', quality=70, method=4)
                    print(f"📐 Resized for Claude: {img.width}x{img.height} → {new_width}x{new_height}")
                    analysis_image_path = temp_file.name

        # Read and encode the image FOR CLAUDE ANALYSIS
        with open(analysis_image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')

        # Clean up temporary analysis file if created
        if analysis_image_path != converted_path and analysis_image_path != image_path:
            try:
                if os.path.exists(analysis_image_path):
                    os.unlink(analysis_image_path)
            except:
                pass

        # Return the encoded image for Claude and the ORIGINAL high-quality path for processing
        return encoded, converted_path
    except Exception as e:
        print(f"⚠️ Failed to encode image: {e}")
        # Fall back to original file if conversion failed
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8'), image_path


def get_image_media_type(image_path: str) -> str:
    """Get media type for image based on actual file content, not just extension"""
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            format_map = {
                'JPEG': 'image/jpeg',
                'PNG': 'image/png',
                'WEBP': 'image/webp',
                'AVIF': 'image/avif'
            }
            return format_map.get(img.format, 'image/jpeg')
    except Exception:
        # Fallback to extension-based detection
        ext = Path(image_path).suffix.lower()
        media_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', 
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.avif': 'image/avif'
        }
        return media_types.get(ext, 'image/jpeg')


def build_adjusted_imagemagick_command(base_command: str, adjustments: dict) -> str:
    """Apply adjustments to base ImageMagick command"""
    if not adjustments:
        return base_command
    
    import re
    command = base_command
    
    # Apply gamma delta - EXPANDED RANGE
    if 'gamma_delta' in adjustments:
        gamma_match = re.search(r'-gamma\s+([\d.]+)', command)
        if gamma_match:
            current_gamma = float(gamma_match.group(1))
            new_gamma = max(0.5, min(2.0, current_gamma + adjustments['gamma_delta']))  # Expanded from 0.8-1.2 to 0.5-2.0
            command = re.sub(r'-gamma\s+[\d.]+', f'-gamma {new_gamma}', command)
        else:
            new_gamma = max(0.5, min(2.0, 1.0 + adjustments['gamma_delta']))
            if new_gamma != 1.0:
                command = f"-gamma {new_gamma} {command}"
    
    # Apply brightness/contrast deltas - EXPANDED RANGE
    if 'brightness_delta' in adjustments or 'contrast_delta' in adjustments:
        bc_match = re.search(r'-brightness-contrast\s+(-?\d+)x(-?\d+)', command)
        if bc_match:
            current_brightness = int(bc_match.group(1))
            current_contrast = int(bc_match.group(2))
        else:
            current_brightness = 0
            current_contrast = 0
        
        new_brightness = max(-20, min(20, current_brightness + adjustments.get('brightness_delta', 0)))  # Expanded from -5/+5 to -20/+20
        new_contrast = max(-20, min(20, current_contrast + adjustments.get('contrast_delta', 0)))  # Expanded from -5/+5 to -20/+20
        
        if bc_match:
            command = re.sub(r'-brightness-contrast\s+-?\d+x-?\d+', 
                            f'-brightness-contrast {new_brightness}x{new_contrast}', command)
        else:
            if new_brightness != 0 or new_contrast != 0:
                command = f"-brightness-contrast {new_brightness}x{new_contrast} {command}"
    
    # Apply saturation delta - EXPANDED RANGE
    if 'saturation_delta' in adjustments:
        mod_match = re.search(r'-modulate\s+(\d+),(\d+),(\d+)', command)
        if mod_match:
            current_saturation = int(mod_match.group(2))
            new_saturation = max(50, min(200, current_saturation + adjustments['saturation_delta']))  # Expanded from 90-120 to 50-200
            command = re.sub(r'-modulate\s+\d+,\d+,\d+', 
                            f'-modulate 100,{new_saturation},100', command)
        else:
            new_saturation = max(50, min(200, 108 + adjustments['saturation_delta']))  # Using base of 108
            if new_saturation != 100:
                command = f"-modulate 100,{new_saturation},100 {command}"
    
    # Apply highlights/shadows deltas - NEW
    if 'highlights_delta' in adjustments or 'shadows_delta' in adjustments:
        # Extract current level values if they exist
        level_match = re.search(r'-level\s+([\d.]+)%,([\d.]+)%', command)
        if level_match:
            current_black = float(level_match.group(1))
            current_white = float(level_match.group(2))
        else:
            # Use defaults from base config
            current_black = 3  # Default shadow lift
            current_white = 95  # Default highlight compression
        
        # Apply deltas with expanded ranges
        new_black = max(0, min(30, current_black + adjustments.get('shadows_delta', 0)))
        new_white = max(70, min(100, current_white + adjustments.get('highlights_delta', 0)))
        
        if level_match:
            command = re.sub(r'-level\s+[\d.]+%,[\d.]+%', 
                            f'-level {new_black}%,{new_white}%', command)
        else:
            if new_black != 0 or new_white != 100:
                command = f"-level {new_black}%,{new_white}% {command}"
    
    return command

async def enhanced_analysis_agent(image_path: str, custom_instructions: Optional[str] = None) -> Dict[str, Any]:
    """
    🔍 Enhanced Analysis Agent - Claude Sonnet 4 analyzes image and decides editing strategy
    
    Now determines whether to use Gemini 2.5 Flash Image editing or ImageMagick optimization
    """
    writer = get_stream_writer()
    
    # Check user's background removal preference  
    skip_bg_removal = os.getenv("SKIP_BACKGROUND_REMOVAL", "false").lower() == "true"
    print(f"📊 Analysis: User's background removal preference: {'disabled' if skip_bg_removal else 'enabled'}")
    
    writer({
        "agent": "analysis", 
        "status": "analyzing",
        "message": f"Analyzing {Path(image_path).name} and determining optimal editing strategy"
    })
    
    # Encode image (will convert AVIF to WebP if needed)
    image_base64, actual_image_path = encode_image_to_base64(image_path)
    media_type = get_image_media_type(actual_image_path)  # Get media type of actual/converted image
    
    # Format background removal preference for the prompt
    bg_removal_preference = "disabled by user" if skip_bg_removal else "enabled by user"
    bg_removal_setting = "false" if skip_bg_removal else "true"
    
    # Get base ImageMagick configuration
    base_imagemagick = get_base_imagemagick_command()
    
    # Check if defect repair is enabled
    use_defect_repair = os.getenv("USE_DEFECT_REPAIR")
    
    # Build evaluation criteria based on settings
    evaluation_criteria = [
        "- **Lens Distortion**: Barrel distortion, pincushion distortion, vignetting, chromatic aberration",
        "- **Surface Materials**: Chrome, stainless steel, matte surfaces, glass, plastic",
        "- **Lighting Issues**: Harsh shadows, overexposure, uneven lighting, color casts",
    ]
    
    if use_defect_repair:
        evaluation_criteria.append("- **Dust and Sensor Debris**: Visible dust spots, sensor debris, dirt on surfaces")
    
    evaluation_criteria.extend([
        "- **Complex Problems**: Artifacts, unwanted objects, background issues",
        "- **Color Quality**: Saturation, vibrancy, accuracy needs"
    ])
    
    # Define dust repair section for f-string
    dust_repair_section = """
    - dust_issues: [detected dust problems: spots, sensor_debris, surface_dirt]
    - needs_dust_removal: boolean (true if dust issues detected)""" if use_defect_repair else ""

    # Enhanced analysis prompt for hybrid workflow
    analysis_prompt = f"""
    Analyze this product image and determine the optimal editing strategy. You must decide between:
    1. **Gemini 2.5 Flash Image** - Advanced AI editing for complex tasks
    2. **ImageMagick** - Traditional optimization for simple adjustments
    
    Evaluate the image for:
{chr(10).join(evaluation_criteria)}
    
    **GEMINI EDITING** is best for:
    - Complex lighting corrections and color casts
    - Selective object editing (enhance chrome without affecting other areas)
    - Background modifications and artifact removal{' and dust/debris removal' if use_defect_repair else ''}
    - Advanced color correction
    
    **IMAGEMAGICK** is sufficient for:
    - Simple brightness/contrast adjustments
    - Basic color saturation changes
    - Sharpening and noise reduction
    - Straightforward optimizations
    
    **IMAGEMAGICK BASE CONFIGURATION**:
    Base command: {base_imagemagick}
    
    Suggest ADJUSTMENTS as deltas from the base:
    - gamma_delta: -0.5 to +0.5 (e.g., +0.1 for noticeable brightening, +0.3 for significant brightening)
    - brightness_delta: -15 to +15 (e.g., +8 for noticeably brighter, -10 for much darker)
    - contrast_delta: -15 to +15 (e.g., +10 for strong contrast boost, -8 for softer look)
    - saturation_delta: -50 to +50 (e.g., +20 for vibrant colors, -30 for muted tones)
    - highlights_delta: -30 to +5 (negative to recover blown highlights, e.g., -15 for chrome)
    - shadows_delta: -5 to +20 (positive to lift shadows, e.g., +10 for dark areas)
    
    Provide empty adjustments dict {{}} to use base config as-is.
    Example adjustments: {{"gamma_delta": 0.15, "contrast_delta": 8, "saturation_delta": 15}}
    
    **IMAGEMAGICK ADJUSTMENT GUIDELINES**:
    - You have MORE freedom to make significant adjustments when needed
    - For UNDEREXPOSED images: Use gamma_delta up to +0.3 or brightness_delta up to +12
    - For OVEREXPOSED images: Use gamma_delta down to -0.3 or brightness_delta down to -12
    - For FLAT images: Use contrast_delta up to +15 for dramatic improvement
    - For DULL colors: Use saturation_delta up to +30 for vibrant results
    - EXPANDED LIMITS:
      • brightness-contrast: -20 to +20 for both values
      • gamma: 0.5 to 2.0 (significant range)
      • saturation: 50 to 200 (can make dramatic color changes)
    - Be BOLD when image needs it: -gamma 1.3 for dark images, -brightness-contrast 10x12 for flat images
    - Use larger adjustments for problematic images, smaller for good ones
    
    **LENS CORRECTION POLICY**:
    - Lens corrections (barrel/pincushion distortion, vignetting, chromatic aberration) are handled separately by the lensfun library.
    - Do NOT include lens correction steps in gemini_instructions.
    - ImageMagick lens corrections are fallback options only, to be used when lensfunpy is not available.
    - You may still report lens_issues and needs_lens_correction for downstream processing by lensfun.
    
    **BACKGROUND REMOVAL POLICY**:
    - User's preference: {bg_removal_preference}
    - You MUST respect the user's preference above all else
    - Set remove_background: {bg_removal_setting}
    - Do not override based on image type when user has made a choice
    
    Return analysis as JSON with:
    - lens_issues: [detected lens distortions: barrel, pincushion, vignetting, chromatic_aberration]
    - needs_lens_correction: boolean (true if lens issues detected)
    - lens_corrections_applied: boolean (true if lens corrections will be applied by dedicated lens correction step){dust_repair_section}
    - surface_materials: [materials detected]
    - lighting_issues: [specific problems]
    - color_problems: [color issues]
    - complex_problems: [issues requiring AI editing]
    - editing_strategy: "gemini" or "imagemagick" or "both"
    - gemini_instructions: string (detailed instructions for Gemini editing, exclude lens corrections)
    - imagemagick_command: string (full ImageMagick command with base + adjustments)
    - imagemagick_adjustments: dict (deltas from base: gamma_delta, brightness_delta, contrast_delta, saturation_delta, highlights_delta, shadows_delta)
    - editing_explanation: string (why this strategy was chosen)
    - remove_background: boolean (default: true, unless user explicitly says no)
    - optimization_priority: [ordered list of what to focus on]
    - needs_cropping: boolean (true if composition could be improved by cropping)
    - crop_suggestion: "auto" or dict with {{left, top, width, height}} or null
    - needs_trim: boolean (true if image has excess whitespace/borders that should be trimmed)
    - trim_explanation: string (why trimming is or isn't needed)
    - analyze_after_bg_removal: boolean (true if image should be re-analyzed after background removal)
    """
    
    # Add custom instructions
    if custom_instructions:
        # Check if user wants to skip Gemini
        skip_gemini = "skip gemini" in custom_instructions.lower()
        
        analysis_prompt += f"""

    **CUSTOM USER INSTRUCTIONS**: {custom_instructions}

    Incorporate these user preferences into your editing strategy:
    - If user wants specific styles, use Gemini for complex styling
    - If user wants simple adjustments, ImageMagick may be sufficient
    - Always prioritize user intent in your strategy choice
    - If user mentions "trim", "crop whitespace", or "remove borders", set needs_trim: true
    - Be intelligent about trim detection: product photos often benefit from trimming excess whitespace
    """

        if skip_gemini:
            analysis_prompt += """
    **IMPORTANT**: User explicitly requested to skip Gemini.
    Set editing_strategy to "imagemagick" only, never "gemini" or "both".
    """

    try:
        # Validate API key exists
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise AgentError("ANTHROPIC_API_KEY environment variable is not set")

        print(f"🔑 Using Anthropic API key: {api_key[:8]}...{api_key[-4:]}")

        client = get_anthropic_client()
        print(f"🌐 Connecting to Anthropic API...")

        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1200,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64
                        }
                    },
                    {"type": "text", "text": analysis_prompt}
                ]
            }]
        )
        
        # Parse response
        analysis_text = response.content[0].text
        
        try:
            # Extract JSON from response
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                json_text = analysis_text[json_start:json_end].strip()
            elif "{" in analysis_text:
                json_start = analysis_text.find("{")
                json_end = analysis_text.rfind("}") + 1
                json_text = analysis_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in analysis")
            
            analysis_result = json.loads(json_text)
            
            # Check if user wants to skip Gemini (via instructions or environment variable)
            skip_gemini = (
                (custom_instructions and "skip gemini" in custom_instructions.lower()) or
                os.getenv('SKIP_GEMINI', 'false').lower() == 'true'
            )
            
            if skip_gemini:
                print("DEBUG: Skipping Gemini - forcing imagemagick strategy")
                analysis_result['editing_strategy'] = 'imagemagick'
                analysis_result['gemini_instructions'] = ''
                analysis_result['editing_explanation'] = 'Gemini AI editing disabled'

            # Override background removal based on user preference from UI
            skip_bg_removal = os.getenv('SKIP_BACKGROUND_REMOVAL', 'false').lower() == 'true'
            if skip_bg_removal:
                print("DEBUG: User disabled background removal - overriding AI decision")
                analysis_result['remove_background'] = False
            else:
                # User wants background removal - force it to true
                print("DEBUG: User enabled background removal - ensuring it's enabled")
                analysis_result['remove_background'] = True

            # Apply batch consistency if available
            if os.getenv('BATCH_IMAGEMAGICK_BASE'):
                writer({
                    "agent": "analysis",
                    "status": "info",
                    "message": "Applying batch consistency parameters"
                })
                # Note: The actual batch base will be picked up by imagemagick_agent
                # We just need to clear adjustments to use base as-is
                analysis_result['imagemagick_adjustments'] = {}
                
                # Prepend batch template to Gemini instructions
                batch_template = os.getenv('BATCH_GEMINI_TEMPLATE', '')
                if batch_template and 'gemini_instructions' in analysis_result:
                    analysis_result['gemini_instructions'] = (
                        batch_template + "\n\n" +
                        "Specific to this image: " + analysis_result['gemini_instructions']
                    )
                
                # Add batch context
                analysis_result['batch_mode'] = True
                analysis_result['enhancement_level'] = os.getenv('BATCH_ENHANCEMENT_LEVEL', 'moderate')
            
        except (json.JSONDecodeError, ValueError) as e:
            writer({
                "agent": "analysis",
                "status": "warning", 
                "message": f"JSON parsing failed: {e}, using fallback"
            })
            # Fallback analysis
            skip_bg_removal = os.getenv('SKIP_BACKGROUND_REMOVAL', 'false').lower() == 'true'
            analysis_result = {
                "surface_materials": ["mixed"],
                "lighting_issues": ["general optimization needed"],
                "color_problems": ["needs enhancement"],
                "complex_problems": [],
                "editing_strategy": "imagemagick",
                "gemini_instructions": "",
                "imagemagick_command": get_base_imagemagick_command(),
                "imagemagick_adjustments": {},
                "editing_explanation": "Fallback to basic optimization",
                "remove_background": not skip_bg_removal,  # Respect user preference
                "optimization_priority": ["brightness", "contrast", "saturation"],
                "lens_corrections_applied": False
            }
        
        # Add metadata
        analysis_result["agent"] = "analysis"
        analysis_result["image_path"] = image_path
        
        # Debug output
        print(f"DEBUG: Analysis result strategy: {analysis_result.get('editing_strategy', 'NOT SET')}")
        print(f"DEBUG: Gemini instructions: {analysis_result.get('gemini_instructions', 'NOT SET')}")
        print(f"DEBUG: Full analysis result: {analysis_result}")
        
        writer({
            "agent": "analysis",
            "status": "complete",
            "strategy": analysis_result.get("editing_strategy", "unknown"),
            "message": f"Analysis complete - Strategy: {analysis_result.get('editing_strategy', 'unknown')}"
        })

        return analysis_result
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_type = type(e).__name__
        error_msg = f"Analysis agent failed: {error_type}: {str(e)}"

        # Print detailed error to console
        print(f"❌ DETAILED ERROR in Analysis Agent:")
        print(f"   Error Type: {error_type}")
        print(f"   Error Message: {str(e)}")
        print(f"   Full Traceback:\n{error_details}")

        writer({
            "agent": "analysis",
            "status": "error",
            "message": error_msg
        })
        raise AgentError(error_msg)


async def gemini_edit_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """
    🎨 Gemini Edit Agent - Uses Gemini 2.5 Flash Image or Gemini 3 Pro Image (Nano Banana Pro) for advanced editing

    Supports two models via GEMINI_MODEL environment variable:
    - "gemini-2.5-flash-image-preview" (default): Fast, cost-effective editing
    - "gemini-3-pro-image-preview" (Nano Banana Pro): Higher quality, supports 2K/4K output
    """
    writer = get_stream_writer()

    # Get model configuration
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-image-preview")
    gemini_image_size = os.getenv("GEMINI_IMAGE_SIZE", "1K")  # 1K, 2K, or 4K (for Nano Banana Pro)

    # Determine model display name
    model_display_name = "Gemini 2.5 Flash Image"
    if "gemini-3-pro" in gemini_model:
        model_display_name = "Nano Banana Pro (Gemini 3 Pro Image)"

    writer({
        "agent": "gemini_edit",
        "status": "editing",
        "message": f"Applying AI-powered editing with {model_display_name}"
    })
    
    gemini_instructions = analysis.get("gemini_instructions", "")
    print(f"DEBUG: Gemini agent received instructions: {gemini_instructions}")
    if not gemini_instructions:
        print("DEBUG: No Gemini instructions found!")
        raise AgentError("No Gemini editing instructions provided")
    
    try:
        print("🤖 Starting Gemini AI editing...")
        
        # Check if image has transparency (from background removal) and flatten if needed
        working_image_path = image_path
        background_was_removed = analysis.get('background_was_removed', False)
        
        # Multiple checks for background removal
        if background_was_removed or 'no-bg' in image_path or 'removed' in image_path or image_path.endswith('.png') or image_path.endswith('.webp'):
            from PIL import Image
            import tempfile
            
            # Check if image actually has transparency
            img = Image.open(image_path)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                print("🎨 Detected transparent image from background removal")
                print("⬜ Flattening with white background for Gemini compatibility")
                
                # Create white background
                if img.mode == 'RGBA' or img.mode == 'LA':
                    # Create white background image
                    white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
                    # Composite original over white background
                    white_bg.paste(img, (0, 0), img)
                    img = white_bg.convert('RGB')
                else:
                    # Convert palette images with transparency
                    img = img.convert('RGBA')
                    white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
                    white_bg.paste(img, (0, 0), img)
                    img = white_bg.convert('RGB')
                
                # Save flattened image to temp file
                temp_dir = tempfile.gettempdir()
                flattened_path = Path(temp_dir) / f"{Path(image_path).stem}_flattened.jpg"
                quality_settings = get_quality_settings()
                save_with_quality(img, str(flattened_path), source_format='JPEG', settings=quality_settings)
                working_image_path = str(flattened_path)
                print(f"✅ Created flattened image for Gemini: {flattened_path.name}")
                
                writer({
                    "agent": "gemini_edit",
                    "status": "preprocessing",
                    "message": "Flattened transparent image with white background for Gemini"
                })
        
        # Configure Gemini API
        configure_gemini()
        print(f"🌐 Connecting to Gemini API...")
        print(f"🤖 Using model: {gemini_model}")
        if "gemini-3-pro" in gemini_model:
            print(f"📐 Image size: {gemini_image_size}")

        # Configure Gemini model
        model = genai.GenerativeModel(gemini_model)
        
        # Load image (now potentially flattened)
        print(f"📁 Loading image: {Path(working_image_path).name}")
        with open(working_image_path, 'rb') as image_file:
            image_data = image_file.read()
        
        print(f"📊 Image size: {len(image_data)} bytes")
        
        # Check if dust removal is needed (only if defect repair is enabled)
        dust_removal_text = ""
        if os.getenv("USE_DEFECT_REPAIR"):
            needs_dust_removal = analysis.get("needs_dust_removal", False)
            dust_issues = analysis.get("dust_issues", [])
            
            if needs_dust_removal and dust_issues:
                dust_removal_text = f"""
        IMPORTANT - Remove Visible Dust and Sensor Debris:
        Detected issues: {", ".join(dust_issues)}
        
        Dust Removal Guidelines:
        - Carefully remove dust spots and sensor debris without affecting product details
        - Clean surface dirt while preserving material textures
        - Ensure dust removal does not blur important product features
        - Focus on maintaining sharpness while removing debris
        """
        
        edit_prompt = f"""
        You are a professional product photography editor. Apply these specific improvements to this image:
        
        CRITICAL REQUIREMENT: You MUST preserve the ENTIRE image frame and dimensions. 
        DO NOT crop, trim, or remove ANY part of the image. 
        The output image MUST have the exact same dimensions and show ALL content from edge to edge.
        Return the COMPLETE, FULL IMAGE with all parts visible, including:
        - The entire top portion
        - The complete bottom portion including base/feet/stand
        - Full left and right sides
        - All edges and corners
        
        {dust_removal_text}
        
        {gemini_instructions}
        
        Focus on creating commercial-quality product photography suitable for e-commerce.
        Maintain product authenticity while enhancing visual appeal.
        Preserve important details while improving overall quality.
        REMINDER: Return the FULL, UNCROPPED image with identical dimensions to the input.
        """
        
        print(f"🚀 Sending to {model_display_name}...")
        # Send to Gemini for editing (use working_image_path for correct mime type)
        # For Nano Banana Pro (gemini-3-pro-image-preview), we need to use the new google.genai SDK
        if "gemini-3-pro" in gemini_model:
            # Use new google.genai SDK for Nano Banana Pro
            try:
                from google import genai
                from google.genai import types as genai_types

                # Create client with API key
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

                # Build the content with image
                image_part = genai_types.Part.from_bytes(
                    data=image_data,
                    mime_type=get_image_media_type(working_image_path)
                )

                # Configure for image generation with specified size
                config = genai_types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                    image_config=genai_types.ImageConfig(
                        image_size=gemini_image_size  # "1K", "2K", or "4K"
                    )
                )

                response = client.models.generate_content(
                    model=gemini_model,
                    contents=[edit_prompt, image_part],
                    config=config
                )
                print(f"📐 Requested {gemini_image_size} output from Nano Banana Pro")

                # Extract image from new SDK response format
                image_saved = False
                output_path = str(Path(image_path).parent / f"{Path(image_path).stem}-gemini-edited.webp")

                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        print(f"✅ Found edited image ({part.inline_data.mime_type}, {len(part.inline_data.data)} bytes)")

                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(part.inline_data.data))
                        edited_width, edited_height = img.size

                        original_img = Image.open(image_path)
                        original_width, original_height = original_img.size

                        print(f"📐 Nano Banana Pro output: {edited_width}x{edited_height}, Original: {original_width}x{original_height}")

                        # Save the image
                        quality_settings = get_quality_settings()
                        save_with_quality(img, output_path, source_format='WEBP', settings=quality_settings)

                        if os.path.getsize(output_path) > 0:
                            print(f"✅ Saved Nano Banana Pro output to: {Path(output_path).name}")
                            image_saved = True

                            writer({
                                "agent": "gemini_edit",
                                "status": "complete",
                                "output": output_path,
                                "message": f"Nano Banana Pro editing complete ({gemini_image_size}): {Path(output_path).name}"
                            })
                            return output_path

                if not image_saved:
                    raise AgentError("No edited image received from Nano Banana Pro")

            except ImportError:
                print("⚠️ google-genai SDK not installed, falling back to standard SDK")
                # Fall through to standard SDK below
                gemini_model = "gemini-2.5-flash-image-preview"

        # Standard call for Gemini 2.5 Flash (or fallback)
        if "gemini-2.5-flash" in gemini_model or "gemini-3-pro" not in gemini_model:
            response = model.generate_content([
                edit_prompt,
                {
                    "mime_type": get_image_media_type(working_image_path),
                    "data": image_data
                }
            ])
        
        print("DEBUG: Received response from Gemini")
        print(f"DEBUG: Response type: {type(response)}")
        
        # Debug: Print the raw response structure
        import json
        try:
            if hasattr(response, 'to_dict'):
                print(f"DEBUG: Response dict: {json.dumps(response.to_dict(), indent=2)[:1000]}...")
        except:
            print(f"DEBUG: Response object: {response}")
        
        print(f"DEBUG: Response candidates: {len(response.candidates) if hasattr(response, 'candidates') and response.candidates else 0}")
        
        # Save edited image in same folder as original
        output_path = str(Path(image_path).parent / f"{Path(image_path).stem}-gemini-edited.webp")
        
        print("✅ Response received from Gemini")
        
        
        # Extract image from response - simplified version
        image_saved = False
        
        try:
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                print(f"✅ Found edited image ({part.inline_data.mime_type}, {len(part.inline_data.data)} bytes)")
                                
                                # Load the image
                                from PIL import Image
                                import io
                                img = Image.open(io.BytesIO(part.inline_data.data))
                                edited_width, edited_height = img.size
                                
                                # Get original dimensions
                                original_img = Image.open(image_path)
                                original_width, original_height = original_img.size
                                
                                print(f"📐 Gemini output: {edited_width}x{edited_height}, Original: {original_width}x{original_height}")
                                
                                # Check if AI upscaling is enabled and needed
                                use_ai_upscaling = os.getenv('USE_AI_UPSCALING', 'false').lower() == 'true'
                                needs_upscaling = edited_width < original_width * 0.9 or edited_height < original_height * 0.9
                                
                                if use_ai_upscaling and needs_upscaling:
                                    print(f"⬆️ Upscaling needed from {edited_width}x{edited_height} to {original_width}x{original_height}")
                                    print("🤖 Using Google AI upscaling...")
                                    
                                    try:
                                        # Save current image to temp file
                                        temp_path = f"/tmp/gemini_temp_{Path(image_path).stem}.png"
                                        quality_settings = get_quality_settings()
                                        save_with_quality(img, temp_path, source_format='PNG', settings=quality_settings)
                                        
                                        # Use AI upscaler
                                        from src.ai_upscaler_agent import upscale_with_ai
                                        upscale_result = await upscale_with_ai(
                                            image_path=temp_path,
                                            target_width=original_width,
                                            target_height=original_height,
                                            output_path=temp_path,
                                            service="vertex"
                                        )
                                        
                                        if upscale_result["status"] == "success":
                                            print(f"✅ AI upscaling successful!")
                                            img = Image.open(temp_path)
                                        else:
                                            print(f"⚠️ AI upscaling failed: {upscale_result.get('error', 'Unknown')}")
                                            print("📐 Using local Lanczos upscaling...")
                                            img = img.resize((original_width, original_height), Image.Resampling.LANCZOS)
                                    except Exception as e:
                                        print(f"⚠️ AI upscaling error: {e}")
                                        print("📐 Using local Lanczos upscaling...")
                                        img = img.resize((original_width, original_height), Image.Resampling.LANCZOS)
                                elif needs_upscaling:
                                    print(f"📐 Using enhanced local Lanczos upscaling")
                                    img = img.resize((original_width, original_height), Image.Resampling.LANCZOS)
                                    # Apply better sharpening for upscaled images
                                    from PIL import ImageFilter
                                    img = img.filter(ImageFilter.UnsharpMask(
                                        radius=1.5,
                                        percent=80,
                                        threshold=2
                                    ))
                                
                                # Save the final image with quality preservation
                                quality_settings = get_quality_settings()
                                save_with_quality(img, output_path, source_format='WEBP', settings=quality_settings)
                                
                                # Verify it was saved
                                if os.path.getsize(output_path) > 0:
                                    print(f"✅ Saved Gemini output to: {Path(output_path).name}")
                                    image_saved = True
                                    break
                    if image_saved:
                        break
        except Exception as e:
            print(f"❌ Error extracting Gemini image: {e}")
            import traceback
            traceback.print_exc()
        
        if not image_saved:
            print("❌ No edited image found in Gemini response")
            print(f"DEBUG: Full response structure: {response}")
            raise AgentError("No edited image received from Gemini")
        
        # No transparency restoration needed - background removal happens after Gemini editing
        print("✅ Gemini editing complete - background removal will happen later if needed")
        
        writer({
            "agent": "gemini_edit",
            "status": "complete",
            "output": output_path,
            "message": f"Gemini editing complete: {Path(output_path).name}"
        })
        
        return output_path
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_type = type(e).__name__
        error_msg = f"Gemini editing failed: {error_type}: {str(e)}"

        # Print detailed error to console
        print(f"❌ DETAILED ERROR in Gemini Agent:")
        print(f"   Error Type: {error_type}")
        print(f"   Error Message: {str(e)}")
        print(f"   Full Traceback:\n{error_details}")

        writer({
            "agent": "gemini_edit",
            "status": "error",
            "message": error_msg
        })
        raise AgentError(error_msg)



async def imagemagick_optimization_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """
    ⚡ ImageMagick Optimization Agent - Traditional image processing
    """
    writer = get_stream_writer()
    
    writer({
        "agent": "imagemagick",
        "status": "optimizing",
        "message": f"Applying ImageMagick optimizations"
    })
    
    # Start with base configuration and apply adjustments
    # Check for batch base config first, then custom base, then default
    custom_config_set = False
    
    # Debug environment variables
    batch_config = os.getenv('BATCH_IMAGEMAGICK_BASE')
    custom_config = os.getenv('IMAGEMAGICK_BASE_CONFIG')
    
    writer({
        "agent": "imagemagick",
        "status": "debug",
        "message": f"ENV CHECK - BATCH: {batch_config[:50] if batch_config else 'None'}, CUSTOM: {custom_config[:50] if custom_config else 'None'}"
    })
    
    if batch_config:
        base_command = batch_config
        writer({
            "agent": "imagemagick",
            "status": "info",
            "message": "Using batch base configuration (no adjustments will be applied)"
        })
        custom_config_set = True
    elif custom_config:
        # User has set custom config via sliders
        base_command = custom_config
        writer({
            "agent": "imagemagick",
            "status": "info",
            "message": "Using custom slider configuration (no adjustments will be applied)"
        })
        custom_config_set = True
    else:
        # Use default base command
        base_command = get_base_imagemagick_command()
        writer({
            "agent": "imagemagick",
            "status": "info",
            "message": "Using default base configuration"
        })
    
    adjustments = analysis.get("imagemagick_adjustments", {})
    
    # Only apply adjustments if NO custom config is set
    # When user sets custom config, they want exact control
    if adjustments and not custom_config_set:
        writer({
            "agent": "imagemagick",
            "status": "info",
            "message": f"Applying AI adjustments: {adjustments}"
        })
        imagemagick_command = build_adjusted_imagemagick_command(base_command, adjustments)
    else:
        # Use base command directly (either custom or default)
        imagemagick_command = base_command
        if adjustments and custom_config_set:
            writer({
                "agent": "imagemagick",
                "status": "info",
                "message": f"Ignoring AI adjustments due to custom config: {adjustments}"
            })
    
    writer({
        "agent": "imagemagick",
        "status": "info",
        "message": f"Using command: {imagemagick_command[:100]}..."  # Show first 100 chars
    })
    
    # Add lens correction only as fallback if not already applied by lens correction step
    needs_lens_correction = analysis.get("needs_lens_correction", False)
    lens_issues = analysis.get("lens_issues", [])
    lens_corrections_applied = analysis.get("lens_corrections_applied", False)
    
    if needs_lens_correction and lens_issues and not lens_corrections_applied:
        # Add basic lens correction parameters (fallback only)
        lens_corrections = []
        # Add virtual pixel method to prevent cropping
        lens_corrections.append("-virtual-pixel edge")
        if "barrel" in str(lens_issues).lower() or "pincushion" in str(lens_issues).lower():
            # Basic barrel/pincushion distortion correction using +distort to preserve canvas
            lens_corrections.append("+distort Barrel '0.0 -0.05 0.0'")
        if "vignetting" in str(lens_issues).lower():
            # Skip vignette command as it ADDS vignetting, not removes it
            # Instead use subtle brightening
            lens_corrections.append("-fill white -colorize 2%")
        
        if lens_corrections:
            imagemagick_command = f"{imagemagick_command} {' '.join(lens_corrections)}"
            writer({
                "agent": "imagemagick",
                "status": "info",
                "message": f"Adding fallback lens corrections: {', '.join(lens_issues)}"
            })
    
    # Add dust removal only if dedicated defect repair is enabled
    if os.getenv("USE_DEFECT_REPAIR"):
        needs_dust_removal = analysis.get("needs_dust_removal", False)
        dust_issues = analysis.get("dust_issues", [])
        
        if needs_dust_removal and dust_issues:
            # Add basic dust removal parameters
            dust_corrections = []
            if "spots" in dust_issues or "sensor_debris" in dust_issues:
                # Basic dust spot removal
                dust_corrections.append("-statistic median 3x3")
            if "surface_dirt" in dust_issues:
                # Surface dirt cleanup
                dust_corrections.append("-morphology close disk:1")
            
            if dust_corrections:
                imagemagick_command = f"{imagemagick_command} {' '.join(dust_corrections)}"
                writer({
                    "agent": "imagemagick",
                    "status": "info",
                    "message": f"Adding dust corrections: {', '.join(dust_issues)}"
                })
    
    # Generate output path
    output_path = str(Path(image_path).parent / f"{Path(image_path).stem}-optimized.webp")
    
    # Safety check: prevent aggressive exposure adjustments
    dangerous_commands = ['-auto-level', '-normalize', '-equalize', '-contrast-stretch']
    for dangerous in dangerous_commands:
        if dangerous in imagemagick_command:
            writer({
                "agent": "imagemagick",
                "status": "warning",
                "message": f"Removing dangerous command {dangerous} to prevent overexposure"
            })
            imagemagick_command = imagemagick_command.replace(dangerous, '')
    
    # Comprehensive brightness/contrast/gamma limiting
    import re
    
    # 1. Limit brightness-contrast values
    bc_match = re.search(r'-brightness-contrast\s+(-?\d+)x(-?\d+)', imagemagick_command)
    if bc_match:
        brightness = int(bc_match.group(1))
        contrast = int(bc_match.group(2))
        
        # Clamp brightness between -5 and +5, contrast between -5 and +5
        orig_brightness, orig_contrast = brightness, contrast
        brightness = max(-5, min(5, brightness))
        contrast = max(-5, min(5, contrast))
        
        if orig_brightness != brightness or orig_contrast != contrast:
            writer({
                "agent": "imagemagick",
                "status": "warning",
                "message": f"Clamping brightness-contrast from {orig_brightness}x{orig_contrast} to {brightness}x{contrast}"
            })
            imagemagick_command = re.sub(
                r'-brightness-contrast\s+-?\d+x-?\d+',
                f'-brightness-contrast {brightness}x{contrast}',
                imagemagick_command
            )
    
    # 2. Limit gamma values (0.8 to 1.2 range)
    gamma_match = re.search(r'-gamma\s+([\d.]+)', imagemagick_command)
    if gamma_match:
        gamma = float(gamma_match.group(1))
        orig_gamma = gamma
        gamma = max(0.8, min(1.2, gamma))
        
        if orig_gamma != gamma:
            writer({
                "agent": "imagemagick",
                "status": "warning",
                "message": f"Clamping gamma from {orig_gamma} to {gamma}"
            })
            imagemagick_command = re.sub(
                r'-gamma\s+[\d.]+',
                f'-gamma {gamma}',
                imagemagick_command
            )
    
    # 3. Limit modulate brightness (95-105 range)
    modulate_match = re.search(r'-modulate\s+(\d+),(\d+),(\d+)', imagemagick_command)
    if modulate_match:
        brightness_mod = int(modulate_match.group(1))
        saturation = int(modulate_match.group(2))
        hue = int(modulate_match.group(3))
        
        orig_brightness_mod = brightness_mod
        brightness_mod = max(95, min(105, brightness_mod))
        
        if orig_brightness_mod != brightness_mod:
            writer({
                "agent": "imagemagick",
                "status": "warning",
                "message": f"Clamping modulate brightness from {orig_brightness_mod} to {brightness_mod}"
            })
            imagemagick_command = re.sub(
                r'-modulate\s+\d+,\d+,\d+',
                f'-modulate {brightness_mod},{saturation},{hue}',
                imagemagick_command
            )
    
    try:
        # Build ImageMagick command with platform detection
        magick_cmd = get_imagemagick_command()
        
        # Check if ImageMagick is available
        if not magick_cmd:
            # ImageMagick not installed - skip this agent
            writer({
                "agent": "imagemagick",
                "status": "skipped",
                "message": "ImageMagick not available on this system, using Gemini AI editing only"
            })
            # Return original image path (as string, not dict)
            return image_path
        
        cmd_parts = imagemagick_command.strip().split()

        # Check if image has transparency (from background removal)
        has_transparency = False
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                has_transparency = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
                if has_transparency:
                    writer({
                        "agent": "imagemagick",
                        "status": "info",
                        "message": "Preserving transparency - not using -flatten"
                    })
        except:
            # Check filename hints
            if 'no-bg' in image_path or 'removed' in image_path or 'rembg' in image_path:
                has_transparency = True

        # Build command - only use -flatten if no transparency
        if has_transparency:
            # Preserve transparency - no flatten
            full_cmd = [magick_cmd, image_path] + cmd_parts + [output_path]
        else:
            # No transparency - can use flatten
            full_cmd = [magick_cmd, image_path] + cmd_parts + ["-flatten", output_path]
        
        # Log input size
        input_size = os.path.getsize(image_path)
        print(f"📥 ImageMagick input: {input_size / 1024 / 1024:.1f} MB")

        writer({
            "agent": "imagemagick",
            "status": "processing",
            "command": " ".join(full_cmd[2:-2]),  # Show just the processing part
            "message": f"Executing: {' '.join(cmd_parts)}"
        })

        # Show the full command for debugging
        print(f"🔧 ImageMagick full command: {' '.join(full_cmd)}")

        # Execute command
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            print(f"📤 ImageMagick output: {output_size / 1024 / 1024:.1f} MB")

            writer({
                "agent": "imagemagick",
                "status": "complete",
                "output": output_path,
                "message": f"ImageMagick optimization complete: {Path(output_path).name} ({output_size / 1024 / 1024:.1f} MB)"
            })
            return output_path
        else:
            error_msg = f"ImageMagick failed: {result.stderr}"
            writer({
                "agent": "imagemagick",
                "status": "error",
                "message": error_msg
            })
            raise AgentError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "ImageMagick operation timed out"
        writer({"agent": "imagemagick", "status": "error", "message": error_msg})
        raise AgentError(error_msg)
    except Exception as e:
        error_msg = f"ImageMagick optimization failed: {str(e)}"
        writer({"agent": "imagemagick", "status": "error", "message": error_msg})
        raise AgentError(error_msg)


async def background_removal_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """
    🖼️ Background Removal Agent - Uses remove.bg API or rembg (ML-based)
    """
    writer = get_stream_writer()

    if not analysis.get("remove_background", False):
        writer({
            "agent": "background",
            "status": "skipped",
            "message": "Background removal not needed based on analysis"
        })
        return image_path

    # Determine which method to use
    bg_method = os.getenv("BACKGROUND_REMOVAL_METHOD", "auto").lower()
    api_key = os.getenv("REMOVE_BG_API_KEY")

    # Decide on the method
    use_rembg = False
    if bg_method == "rembg":
        use_rembg = True
    elif bg_method == "remove.bg":
        if not api_key:
            writer({
                "agent": "background",
                "status": "error",
                "message": "remove.bg requested but no API key provided"
            })
            return image_path
        use_rembg = False
    elif bg_method == "auto":
        # Auto mode: use remove.bg if API key exists, otherwise use rembg
        use_rembg = not api_key

    if use_rembg:
        # Use rembg (ML-based local processing)
        writer({
            "agent": "background",
            "status": "removing",
            "message": "Removing background with rembg (ML-based)"
        })

        try:
            from rembg import remove, new_session
            from PIL import Image

            # Load the image
            input_img = Image.open(image_path)

            # Get preferred model from env or use bria-rmbg by default
            model = os.getenv("REMBG_MODEL", "bria-rmbg")

            # Optional: Enable alpha matting for better edges
            use_alpha_matting = os.getenv("REMBG_ALPHA_MATTING", "false").lower() == "true"

            # Create a session with the specified model
            try:
                session = new_session(model)
                writer({
                    "agent": "background",
                    "status": "info",
                    "message": f"Using {model} model for background removal"
                })
            except Exception as e:
                # Fallback to bria-rmbg if specified model fails
                try:
                    session = new_session('bria-rmbg')
                    writer({
                        "agent": "background",
                        "status": "info",
                        "message": f"Model {model} not available, using bria-rmbg (fallback)"
                    })
                except:
                    # If bria-rmbg also fails, let remove() use its default
                    session = None
                    writer({
                        "agent": "background",
                        "status": "info",
                        "message": "Using default u2net model"
                    })

            # Remove background with optional alpha matting for better edges
            remove_kwargs = {}
            if use_alpha_matting:
                remove_kwargs['alpha_matting'] = True
                remove_kwargs['alpha_matting_foreground_threshold'] = 240
                remove_kwargs['alpha_matting_background_threshold'] = 50
                remove_kwargs['alpha_matting_erode_size'] = 10

            if session:
                output_img = remove(input_img, session=session, **remove_kwargs)
            else:
                # Use model_name parameter if no session
                output_img = remove(input_img, model_name=model, **remove_kwargs)

            # Save as PNG first (preserves transparency)
            png_path = str(Path(image_path).parent / f"{Path(image_path).stem}-rembg.png")
            quality_settings = get_quality_settings()
            save_with_quality(output_img, png_path, source_format='PNG', settings=quality_settings)

            writer({
                "agent": "background",
                "status": "converting",
                "message": "Converting PNG to WebP for further processing"
            })

            # Convert to WebP if ImageMagick is available
            webp_path = str(Path(image_path).parent / f"{Path(image_path).stem}-rembg.webp")
            try:
                import subprocess
                magick_cmd = get_imagemagick_command()

                if not magick_cmd:
                    webp_path = png_path
                    result_ok = True
                else:
                    quality_settings = get_quality_settings()
                    quality_value = str(quality_settings.get('imagemagick_quality', 95))
                    cmd = [magick_cmd, png_path, "-quality", quality_value, webp_path]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    result_ok = (result.returncode == 0)

                    if not result_ok:
                        webp_path = png_path
                        result_ok = True

                writer({
                    "agent": "background",
                    "status": "complete",
                    "output": webp_path,
                    "message": f"Background removal complete (rembg): {Path(webp_path).name}"
                })
                return webp_path

            except Exception as convert_error:
                writer({
                    "agent": "background",
                    "status": "warning",
                    "output": png_path,
                    "message": f"Background removal complete (rembg), conversion failed: {convert_error}"
                })
                return png_path

        except ImportError as e:
            error_msg = f"rembg not installed or import error: {str(e)}"
            print(f"❌ DEBUG: {error_msg}")
            print(f"❌ SOLUTION: Make sure you're running with the virtual environment activated:")
            print(f"             ./venv/bin/streamlit run streamlit_app.py")
            print(f"             OR activate venv first: source venv/bin/activate")
            writer({
                "agent": "background",
                "status": "error",
                "message": "rembg not installed. Run: pip install rembg (in venv)"
            })
            # Fall back to remove.bg API if available
            if api_key:
                print(f"🔄 DEBUG: Falling back to remove.bg API since rembg import failed")
                # Use the API code from below
                pass
            return image_path
        except Exception as e:
            error_msg = f"rembg background removal error: {str(e)}"
            print(f"❌ DEBUG: {error_msg}")
            import traceback
            print(f"❌ DEBUG: Full traceback:\n{traceback.format_exc()}")
            writer({
                "agent": "background",
                "status": "error",
                "message": error_msg
            })
            return image_path

    else:
        # Use remove.bg API (original implementation)
        if not api_key:
            writer({
                "agent": "background",
                "status": "skipped",
                "message": "Background removal skipped - no API key"
            })
            return image_path
    
    writer({
        "agent": "background",
        "status": "removing",
        "message": "Removing background with remove.bg API"
    })

    # Log input file size
    input_size = os.path.getsize(image_path)
    print(f"📤 Sending to remove.bg: {Path(image_path).name} ({input_size / 1024 / 1024:.1f} MB)")
    writer({
        "agent": "background",
        "status": "info",
        "message": f"Input file: {input_size / 1024 / 1024:.1f} MB"
    })

    try:
        # Determine size parameter based on quality preset
        quality_settings = get_quality_settings()

        # Check for explicit size parameter override
        size_param = os.getenv('REMOVEBG_SIZE')

        if size_param:
            # User explicitly set the size
            writer({
                "agent": "background",
                "status": "info",
                "message": f"Using user-specified remove.bg size: {size_param}"
            })
        else:
            # Choose size based on quality settings
            if quality_settings.get('preserve_original_format') or quality_settings.get('imagemagick_quality', 95) >= 98:
                # Maximum/Ultra quality - use full resolution
                size_param = 'full'  # Full resolution, preserves all pixels
                writer({
                    "agent": "background",
                    "status": "info",
                    "message": "Using full resolution for remove.bg (highest quality, more credits)"
                })
            elif quality_settings.get('imagemagick_quality', 95) >= 95:
                # High quality - use 4k
                size_param = '4k'  # Up to 10MP
                writer({
                    "agent": "background",
                    "status": "info",
                    "message": "Using 4K resolution for remove.bg (high quality)"
                })
            else:
                # Balanced/Web - use auto
                size_param = 'auto'
                writer({
                    "agent": "background",
                    "status": "info",
                    "message": "Using auto resolution for remove.bg (balanced quality)"
                })

        with open(image_path, 'rb') as image_file:
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': image_file},
                data={'size': size_param},
                headers={'X-Api-Key': api_key},
                timeout=30
            )
        
        if response.status_code == 200:
            # Log response size
            response_size = len(response.content)
            writer({
                "agent": "background",
                "status": "info",
                "message": f"remove.bg API response: {response_size / 1024 / 1024:.1f} MB (requested size: {size_param})"
            })
            print(f"📊 remove.bg response: {response_size / 1024 / 1024:.1f} MB for size '{size_param}'")

            # Step 1: Save as PNG (native format from remove.bg)
            png_path = str(Path(image_path).parent / f"{Path(image_path).stem}-no-bg.png")
            with open(png_path, 'wb') as out_file:
                out_file.write(response.content)
            
            writer({
                "agent": "background",
                "status": "converting",
                "message": "Converting PNG to WebP for further processing"
            })
            
            # Step 2: Convert PNG to WebP with quality preservation
            webp_path = str(Path(image_path).parent / f"{Path(image_path).stem}-no-bg.webp")
            try:
                from PIL import Image
                import subprocess

                # Get file size of PNG from remove.bg
                png_size = os.path.getsize(png_path)
                writer({
                    "agent": "background",
                    "status": "info",
                    "message": f"PNG from remove.bg: {png_size / 1024 / 1024:.1f} MB"
                })

                # Try PIL first for better quality control
                try:
                    img = Image.open(png_path)
                    quality_settings = get_quality_settings()
                    save_with_quality(img, webp_path, source_format='WEBP', settings=quality_settings)
                    img.close()

                    webp_size = os.path.getsize(webp_path)
                    print(f"📦 PNG→WebP conversion: {png_size / 1024 / 1024:.1f} MB → {webp_size / 1024 / 1024:.1f} MB (quality {quality_settings.get('webp_quality', 95)})")
                    writer({
                        "agent": "background",
                        "status": "info",
                        "message": f"Converted to WebP: {webp_size / 1024 / 1024:.1f} MB (quality {quality_settings.get('webp_quality', 95)})"
                    })
                    result_ok = True

                except Exception as pil_error:
                    # Fall back to ImageMagick if PIL fails
                    writer({
                        "agent": "background",
                        "status": "info",
                        "message": f"PIL conversion failed, trying ImageMagick: {pil_error}"
                    })

                    magick_cmd = get_imagemagick_command()
                    if not magick_cmd:
                        # Return PNG directly if no converter available
                        webp_path = png_path
                        result_ok = True
                    else:
                        quality_settings = get_quality_settings()
                        quality_value = str(quality_settings.get('imagemagick_quality', 95))
                        cmd = [magick_cmd, png_path, "-quality", quality_value, webp_path]
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        result_ok = (result.returncode == 0)

                        if not result_ok:
                            # Fallback to PNG if conversion fails
                            webp_path = png_path
                            result_ok = True
                
                if result_ok:
                    writer({
                        "agent": "background",
                        "status": "complete",
                        "output": webp_path,
                        "message": f"Background removal and conversion complete: {Path(webp_path).name}"
                    })
                    return webp_path
                else:
                    # If conversion fails, return the PNG path
                    writer({
                        "agent": "background", 
                        "status": "warning",
                        "output": png_path,
                        "message": f"Background removal complete, WebP conversion failed - using PNG: {Path(png_path).name}"
                    })
                    return png_path
                    
            except Exception as convert_error:
                writer({
                    "agent": "background",
                    "status": "warning",
                    "output": png_path,
                    "message": f"Background removal complete (rembg), conversion failed: {convert_error}"
                })
                return png_path
        else:
            error_msg = f"Background removal failed: HTTP {response.status_code}"
            writer({"agent": "background", "status": "error", "message": error_msg})
            return image_path

    except Exception as e:
        writer({
            "agent": "background",
            "status": "error",
            "message": f"Background removal error: {str(e)}"
        })
        return image_path


async def enhanced_qc_agent(image_path: str, original_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    ✅ Enhanced QC Agent - Evaluates results and decides on ImageMagick fallback
    """
    writer = get_stream_writer()
    
    writer({
        "agent": "qc",
        "status": "evaluating",
        "message": f"Quality control check for {Path(image_path).name}"
    })
    
    # Encode processed image (will convert AVIF if needed)
    image_base64, actual_image_path = encode_image_to_base64(image_path)
    media_type = get_image_media_type(actual_image_path)
    
    # Enhanced QC prompt
    qc_prompt = f"""
    ENHANCED QUALITY CONTROL for e-commerce product image.
    
    Original analysis: {original_analysis.get('optimization_priority', [])}
    Applied strategy: {original_analysis.get('editing_strategy', 'unknown')}
    
    **REALISTIC EVALUATION CRITERIA**:

    1. **Critical Issues (Auto-Fail)**:
       - Visible glitches, severe color bleeding, processing corruption
       - Pink/purple/cyan artifacts or unusual color patches

    2. **Dust and Debris**:
       - Minor dust spots are acceptable for 6-7 range
       - Check that cleaning didn't blur product details

    3. **Professional Standards**:
       - Clean, sharp, suitable for e-commerce
       - Natural product appearance

    4. **Editing Quality**:
       - Natural-looking results preferred
       - Product authenticity maintained
       - Moderate enhancements acceptable

    5. **Technical Quality**:
       - Reasonable focus and exposure
       - Clean edges and adequate contrast

    **SCORING GUIDELINES** (Be realistic, not overly strict):
    - Score 9-10: Excellent - professional grade, ready to use
    - Score 7-8: Good - solid quality, commercially acceptable
    - Score 5-6: Acceptable - usable but could be improved
    - Score 0-4: Poor - needs significant improvement

    **IMPORTANT**: ImageMagick-only processing typically scores 6-8 range, which is ACCEPTABLE.
    Only fail for critical issues (artifacts, corruption, severe problems).

    Return JSON with:
    - passed: boolean (true if score 5+ AND no critical artifacts)
    - quality_score: number (0-10, be realistic not harsh)
    - issues_found: [specific problems]
    - dust_removal_quality: string (excellent, good, fair, poor)
    - needs_imagemagick_fallback: boolean (recommend ImageMagick as backup)
    - imagemagick_suggestions: string (specific ImageMagick commands to try)
    - final_assessment: string (detailed explanation)
    
    **REMEMBER**: If Gemini editing looks artificial or over-processed, recommend ImageMagick fallback.
    """
    
    try:
        client = get_anthropic_client()
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64
                        }
                    },
                    {"type": "text", "text": qc_prompt}
                ]
            }]
        )
        
        qc_text = response.content[0].text
        
        try:
            # Parse QC response
            if "```json" in qc_text:
                json_start = qc_text.find("```json") + 7
                json_end = qc_text.find("```", json_start)
                json_text = qc_text[json_start:json_end].strip()
            elif "{" in qc_text:
                json_start = qc_text.find("{")
                json_end = qc_text.rfind("}") + 1
                json_text = qc_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in QC response")
            
            qc_result = json.loads(json_text)
            
        except (json.JSONDecodeError, ValueError) as e:
            writer({
                "agent": "qc",
                "status": "warning",
                "message": f"QC parsing failed: {e}"
            })
            # Conservative fallback
            qc_result = {
                "passed": False,
                "quality_score": 5.0,
                "issues_found": ["qc_parsing_failed"],
                "needs_imagemagick_fallback": True,
                "imagemagick_suggestions": "-enhance -contrast",
                "final_assessment": "QC parsing failed, recommending ImageMagick fallback"
            }
        
        # Add metadata
        qc_result["agent"] = "qc"
        qc_result["image_path"] = image_path
        
        status = "passed" if qc_result.get("passed", False) else "failed"
        fallback_needed = qc_result.get("needs_imagemagick_fallback", False)
        
        writer({
            "agent": "qc",
            "status": status,
            "quality_score": qc_result.get("quality_score", 0),
            "fallback_recommended": fallback_needed,
            "message": f"QC {status} - Score: {qc_result.get('quality_score', 0)}/10"
        })
        
        return qc_result
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_type = type(e).__name__
        error_msg = f"QC agent failed: {error_type}: {str(e)}"

        # Print detailed error to console
        print(f"❌ DETAILED ERROR in QC Agent:")
        print(f"   Error Type: {error_type}")
        print(f"   Error Message: {str(e)}")
        print(f"   Full Traceback:\n{error_details}")

        writer({"agent": "qc", "status": "error", "message": error_msg})
        raise AgentError(error_msg)


# Export the enhanced agents
__all__ = [
    'enhanced_analysis_agent',
    'gemini_edit_agent', 
    'imagemagick_optimization_agent',
    'background_removal_agent',
    'enhanced_qc_agent',
    'AgentError'
]