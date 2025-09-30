# AVIF Quality Preservation - Complete Solution

## The Quality Loss Problem

Based on your testing:
- **Manual ImageMagick at quality 100**: 10.9 MB → 19 MB (perfect quality)
- **Manual ImageMagick at quality 95**: 10.9 MB → ~5 MB (perfect quality)
- **Pipeline output**: 10.9 MB → 343 KB (97% reduction, quality loss)

The problem was **multiple format conversions without quality flags**:
1. AVIF → WebP (for remove.bg API)
2. remove.bg returns PNG
3. PNG → WebP (final output)

Each conversion without explicit quality uses ImageMagick's default (often 75), causing cumulative quality loss.

## Fixes Applied

### 1. All Format Conversions Now Use Quality Settings
- ✅ AVIF → WebP conversion uses quality from preset
- ✅ PNG → WebP after remove.bg uses quality from preset
- ✅ All ImageMagick commands include `-quality` flag
- ✅ Background removal preserves quality through conversions

### 2. Quality Presets with Proper Settings
```python
# Maximum preset (for archival quality)
"imagemagick_quality": 100
"webp_quality": 100
"webp_lossless": True
"preserve_original_format": True  # Converts back to AVIF

# Ultra preset (recommended for high quality)
"imagemagick_quality": 98
"webp_quality": 98
"webp_lossless": False
"preserve_original_format": False  # Stays as WebP

# High preset (your 95 quality test)
"imagemagick_quality": 95
"webp_quality": 95
```

### 3. Format Preservation (Maximum Preset Only)
- Maximum preset converts back to AVIF at the end
- Requires `pillow-avif-plugin` installed
- Other presets output WebP for compatibility

## How to Use for Best Quality

### Option 1: Maximum Quality with AVIF Output
```bash
# Install AVIF support
pip install pillow-avif-plugin

# Use maximum preset
export QUALITY_PRESET=maximum

# Process with only ImageMagick and remove.bg
export SKIP_GEMINI=true
python photo_editor.py process image.avif
```

**Expected result**: ~19 MB AVIF output (matching your manual test)

### Option 2: Ultra Quality with WebP Output
```bash
# Use ultra preset (98 quality)
export QUALITY_PRESET=ultra
export SKIP_GEMINI=true
python photo_editor.py process image.avif
```

**Expected result**: ~10 MB WebP output with excellent quality

### Option 3: High Quality (Matching Your 95 Test)
```bash
# Use high preset (95 quality)
export QUALITY_PRESET=high
export SKIP_GEMINI=true
python photo_editor.py process image.avif
```

**Expected result**: ~5 MB WebP output (matching your manual test)

## In Streamlit

1. **Select Quality Preset**:
   - "maximum" for AVIF → AVIF with quality 100
   - "ultra" for AVIF → WebP with quality 98
   - "high" for AVIF → WebP with quality 95

2. **Processing Options**:
   - ✅ Use ImageMagick Optimization
   - ✅ Remove Background (if needed)
   - ❌ Use Gemini AI Enhancement (causes resize)
   - ❌ Use Chunked Gemini

## Understanding the Conversions

### With Remove.bg API:
```
AVIF input (10.9 MB)
  ↓ Convert to WebP with quality setting (e.g., 98)
WebP (~10 MB)
  ↓ Send to remove.bg API
PNG from API (~15 MB, lossless)
  ↓ Convert to WebP with quality setting (e.g., 98)
WebP output (~9 MB)
  ↓ (If maximum preset) Convert back to AVIF
AVIF output (~10 MB)
```

### Without Remove.bg:
```
AVIF input (10.9 MB)
  ↓ Convert to WebP with quality setting
WebP (~10 MB)
  ↓ ImageMagick processing with -quality flag
WebP output (~10 MB)
  ↓ (If maximum preset) Convert back to AVIF
AVIF output (~10 MB)
```

## Why 343 KB Output Happened

Your 343 KB output was caused by:
1. **Missing quality flags** in conversions (now fixed)
2. **Default ImageMagick quality** (75) being used
3. **Multiple lossy conversions** compounding quality loss
4. NOT caused by resolution change (you confirmed no resize)

## Verification

After processing, check console output for:
- "🎛️ Final ImageMagick command: ... -quality 98" (or 100/95)
- "✅ Saved as WebP with quality 98" (or your chosen preset)
- "📊 Size: 10.9MB → ~10MB (≈100%)" (should be close to original)

If you still get 343 KB output after these fixes:
1. Check if all quality settings are being applied
2. Verify remove.bg isn't downscaling (check image dimensions)
3. Ensure you're using the latest code with all fixes

## Testing the Fix

```python
# Run the quality test
python test_imagemagick_quality.py

# This shows that ImageMagick without -quality flag
# can cause massive quality loss, especially in
# PNG → WebP conversions (as happens after remove.bg)
```

The fixes ensure every conversion explicitly specifies quality, preventing the default low-quality compression that caused your 97% file size reduction.