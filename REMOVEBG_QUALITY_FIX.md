# Remove.bg API Quality Fix

## The Problem
- **rembg (local ML)**: Works fine, outputs 5MB high-quality image
- **remove.bg API**: Outputs 343KB low-quality image (97% reduction)

## Root Causes Found

### 1. Remove.bg API Size Parameter
The API was using `size: 'auto'` which may choose lower resolution to save credits:
- **"auto"** - Chooses resolution based on credits (may downscale)
- **"preview"** - 0.25 megapixels (625×400) - very low quality
- **"4k"** - Up to 10 megapixels (4000×2500)
- **"full"** - Full resolution, preserves all pixels

### 2. PNG to WebP Conversion
After remove.bg returns PNG, conversion to WebP wasn't optimally handled.

## Fixes Applied

### 1. Dynamic Size Parameter Based on Quality Preset
```python
# Maximum/Ultra preset (quality ≥ 98)
size_param = 'full'  # Full resolution

# High preset (quality ≥ 95)
size_param = '4k'    # Up to 10MP

# Balanced/Web preset
size_param = 'auto'  # Let API choose
```

### 2. Better PNG to WebP Conversion
- Now uses PIL with quality_config settings first
- Falls back to ImageMagick with explicit quality flag
- Logs file sizes for debugging

### 3. Environment Variable Override
```bash
# Force specific remove.bg size
export REMOVEBG_SIZE=full    # Options: preview, auto, small, medium, hd, 4k, full, 50MP
```

## How to Use

### For Maximum Quality with remove.bg API:

```bash
# Option 1: Use maximum preset (automatically uses 'full' size)
export QUALITY_PRESET=maximum
export BACKGROUND_REMOVAL_METHOD=remove.bg

# Option 2: Explicitly set size
export QUALITY_PRESET=ultra
export REMOVEBG_SIZE=full
export BACKGROUND_REMOVAL_METHOD=remove.bg

# Process
python photo_editor.py process image.avif
```

### Expected Results:
- **With 'full' size**: Original resolution preserved
- **With '4k' size**: Up to 10MP (good for most uses)
- **With 'auto' size**: Variable (API decides based on credits)

## In Streamlit:

1. Select **"maximum"** or **"ultra"** quality preset
2. This automatically uses 'full' or '4k' size for remove.bg
3. Monitor console output for:
   - "Using full resolution for remove.bg"
   - "PNG from remove.bg: X.X MB"
   - "Converted to WebP: X.X MB"

## Cost Considerations

Remove.bg API credits vary by size:
- **preview**: Cheapest (but very low quality)
- **auto**: Variable cost
- **4k**: Medium cost
- **full**: Higher cost
- **50MP**: Highest cost (1 credit per image)

For production, consider:
- Use **rembg** (free, local) for most images
- Use **remove.bg API with 4k** for important images
- Use **remove.bg API with full** only when maximum quality is critical

## Debugging

The pipeline now logs:
1. Which size parameter is being used
2. PNG file size from remove.bg
3. WebP file size after conversion

If you still get low quality:
- Check console for "Using X resolution for remove.bg"
- Verify PNG size from API (should be several MB)
- Ensure quality preset is applied

## Alternative: Use rembg

Since rembg works fine for you:
```bash
# Force rembg (free, local, no API needed)
export BACKGROUND_REMOVAL_METHOD=rembg
export REMBG_MODEL=bria-rmbg  # Best for products

# This gives you 5MB high-quality output
```

## Summary

The remove.bg API issue was caused by:
1. **'auto' size parameter** potentially downscaling
2. **Suboptimal PNG → WebP conversion**

Now fixed with:
- Quality-based size selection ('full' for max quality)
- Proper conversion with quality preservation
- File size logging for verification

The pipeline should now produce similar quality to rembg when using remove.bg API with proper settings.