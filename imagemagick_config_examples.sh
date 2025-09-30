#!/bin/bash
# ImageMagick Base Configuration Examples
# These environment variables control the base ImageMagick settings

# ==============================================================================
# BASIC ADJUSTMENTS
# ==============================================================================

# Gamma correction (0.8-1.2) - affects overall brightness
export IMAGEMAGICK_GAMMA=1.0

# Brightness adjustment (-10 to +10)
export IMAGEMAGICK_BRIGHTNESS=0

# Contrast adjustment (-10 to +10)
export IMAGEMAGICK_CONTRAST=2

# Saturation (90-120) - color intensity
export IMAGEMAGICK_SATURATION=108

# Sharpness - unsharp mask parameters (e.g., "1.0x0.5")
export IMAGEMAGICK_SHARPNESS="1.0x0.5"

# Highlight recovery (-20 to 0) - negative values darken highlights
export IMAGEMAGICK_HIGHLIGHTS=-5

# Shadow lifting (0 to 20) - positive values brighten shadows
export IMAGEMAGICK_SHADOWS=3

# Output quality (1-100)
export IMAGEMAGICK_QUALITY=95

# ==============================================================================
# ADVANCED COLOR CONTROLS
# ==============================================================================

# Vibrance (-100 to +100) - affects less saturated colors more
export IMAGEMAGICK_VIBRANCE=0

# Hue shift in degrees (-180 to +180)
export IMAGEMAGICK_HUE_SHIFT=0

# Denoise level (0-100) - noise reduction strength
export IMAGEMAGICK_DENOISE=0

# Gaussian blur radius (0-10)
export IMAGEMAGICK_BLUR=0

# ==============================================================================
# AUTO ADJUSTMENTS (USE WITH CAUTION - CAN OVEREXPOSE)
# ==============================================================================

# Auto-level adjustment (true/false)
export IMAGEMAGICK_AUTO_LEVEL=false

# Auto-gamma correction (true/false)
export IMAGEMAGICK_AUTO_GAMMA=false

# Normalize histogram (true/false) - CAREFUL: often overexposes
export IMAGEMAGICK_NORMALIZE=false

# ==============================================================================
# TRIMMING & RESIZING
# ==============================================================================

# Auto-trim whitespace (true/false)
export IMAGEMAGICK_TRIM=false

# Fuzz factor for trimming (1-20%) - tolerance for "whitespace"
export IMAGEMAGICK_TRIM_FUZZ=5

# Resize dimensions (e.g., "1920x1080", "50%", "1920x1080>")
export IMAGEMAGICK_RESIZE=""

# Colorspace conversion (e.g., "sRGB", "Lab", "HSL")
export IMAGEMAGICK_COLORSPACE=""

# ==============================================================================
# PRESET CONFIGURATIONS
# ==============================================================================

# Example 1: Natural Product Photography (subtle enhancement)
natural_product() {
    export IMAGEMAGICK_GAMMA=1.02
    export IMAGEMAGICK_BRIGHTNESS=0
    export IMAGEMAGICK_CONTRAST=1
    export IMAGEMAGICK_SATURATION=105
    export IMAGEMAGICK_SHARPNESS="0.8x0.4"
    export IMAGEMAGICK_HIGHLIGHTS=-3
    export IMAGEMAGICK_SHADOWS=2
    export IMAGEMAGICK_QUALITY=95
    echo "✅ Applied Natural Product preset"
}

# Example 2: Vibrant E-commerce (punchy colors)
vibrant_ecommerce() {
    export IMAGEMAGICK_GAMMA=1.05
    export IMAGEMAGICK_BRIGHTNESS=2
    export IMAGEMAGICK_CONTRAST=3
    export IMAGEMAGICK_SATURATION=115
    export IMAGEMAGICK_VIBRANCE=10
    export IMAGEMAGICK_SHARPNESS="1.2x0.6"
    export IMAGEMAGICK_HIGHLIGHTS=-8
    export IMAGEMAGICK_SHADOWS=5
    export IMAGEMAGICK_QUALITY=95
    echo "✅ Applied Vibrant E-commerce preset"
}

# Example 3: Chrome/Metal Products (highlight control)
chrome_metal() {
    export IMAGEMAGICK_GAMMA=0.95
    export IMAGEMAGICK_BRIGHTNESS=-2
    export IMAGEMAGICK_CONTRAST=4
    export IMAGEMAGICK_SATURATION=102
    export IMAGEMAGICK_SHARPNESS="1.5x0.7"
    export IMAGEMAGICK_HIGHLIGHTS=-12  # Strong highlight recovery
    export IMAGEMAGICK_SHADOWS=3
    export IMAGEMAGICK_QUALITY=95
    echo "✅ Applied Chrome/Metal preset"
}

# Example 4: Soft/Matte Products (gentle processing)
soft_matte() {
    export IMAGEMAGICK_GAMMA=1.0
    export IMAGEMAGICK_BRIGHTNESS=1
    export IMAGEMAGICK_CONTRAST=0
    export IMAGEMAGICK_SATURATION=106
    export IMAGEMAGICK_SHARPNESS="0.6x0.3"
    export IMAGEMAGICK_HIGHLIGHTS=-2
    export IMAGEMAGICK_SHADOWS=4
    export IMAGEMAGICK_DENOISE=20
    export IMAGEMAGICK_QUALITY=95
    echo "✅ Applied Soft/Matte preset"
}

# Example 5: High-key White Background
high_key() {
    export IMAGEMAGICK_GAMMA=1.08
    export IMAGEMAGICK_BRIGHTNESS=3
    export IMAGEMAGICK_CONTRAST=-1
    export IMAGEMAGICK_SATURATION=103
    export IMAGEMAGICK_SHARPNESS="0.8x0.4"
    export IMAGEMAGICK_HIGHLIGHTS=0
    export IMAGEMAGICK_SHADOWS=8
    export IMAGEMAGICK_TRIM=true
    export IMAGEMAGICK_TRIM_FUZZ=8
    export IMAGEMAGICK_QUALITY=95
    echo "✅ Applied High-key preset"
}

# Example 6: Custom full command override
custom_command() {
    # This overrides ALL individual settings
    export IMAGEMAGICK_BASE_CONFIG="-gamma 1.1 -brightness-contrast 2x3 -modulate 105,110,100 -unsharp 1.0x0.5 -quality 95"
    echo "✅ Applied custom command override"
}

# ==============================================================================
# USAGE
# ==============================================================================

echo "ImageMagick Configuration Examples"
echo "==================================="
echo ""
echo "Available presets:"
echo "  source imagemagick_config_examples.sh && natural_product"
echo "  source imagemagick_config_examples.sh && vibrant_ecommerce"
echo "  source imagemagick_config_examples.sh && chrome_metal"
echo "  source imagemagick_config_examples.sh && soft_matte"
echo "  source imagemagick_config_examples.sh && high_key"
echo "  source imagemagick_config_examples.sh && custom_command"
echo ""
echo "Or set individual variables:"
echo "  export IMAGEMAGICK_GAMMA=1.1"
echo "  export IMAGEMAGICK_SATURATION=115"
echo "  export IMAGEMAGICK_TRIM=true"
echo ""
echo "Then run the photo editor:"
echo "  python photo_editor.py process image.jpg"
echo ""