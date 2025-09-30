# Quality Fix Summary - AVIF Files

## Your Test Results
- **Input**: 10.9 MB AVIF
- **Manual ImageMagick at quality 100**: 19 MB (quality maintained)
- **Manual ImageMagick at quality 95**: ~5 MB (perfect quality)
- **Pipeline output**: 343 KB (97% reduction - quality loss!)

## The Root Cause
Your manual test proves ImageMagick handles AVIF → WebP correctly at high quality. The pipeline's 343 KB output indicates either:

1. **Resolution reduction** (likely if Gemini was used)
2. **Multiple compression stages** with quality loss
3. **Hardcoded quality values** not respecting settings

## Issues Found and Fixed

### 1. **Hardcoded Quality Values**
- ✅ Fixed: ImageMagick commands had hardcoded `-quality 95`
- ✅ Fixed: Background removal had hardcoded `quality=95`
- ✅ Fixed: Now uses quality settings from presets

### 2. **Format Not Preserved**
- ✅ Fixed: AVIF converted to WebP but never converted back
- ✅ Fixed: Added format preservation module
- ✅ Fixed: Maximum preset now preserves original format

### 3. **Quality Settings Not Applied**
- ✅ Fixed: ImageMagick now uses `imagemagick_quality` from preset
- ✅ Fixed: All saves now use quality_config module
- ✅ Fixed: Maximum preset uses quality 100 throughout

## How to Get Best Quality

### For AVIF Files (to match your manual test):

1. **Install AVIF support**:
```bash
pip install pillow-avif-plugin
```

2. **Use Maximum preset** (quality 100, lossless):
```bash
# Set quality preset
export QUALITY_PRESET=maximum

# Or Ultra preset (quality 98)
export QUALITY_PRESET=ultra
```

3. **Avoid Gemini** (it resizes images):
```bash
export SKIP_GEMINI=true
```

4. **In Streamlit**:
   - Select "maximum" from Quality Preset dropdown
   - Uncheck "Use Gemini AI Enhancement"
   - Uncheck "Use Chunked Gemini"
   - Keep "Use ImageMagick Optimization" checked

### Expected Results with Fixes:
- **Maximum preset**: ~19 MB output (matching your manual test at quality 100)
- **Ultra preset**: ~10 MB output (quality 98)
- **High preset**: ~5 MB output (quality 95, matching your manual test)

## Quality Preset Comparison

| Preset | ImageMagick Quality | WebP Quality | AVIF Quality | Expected Size (10.9MB input) |
|--------|-------------------|--------------|--------------|------------------------------|
| Maximum | 100 | 100 (lossless) | 100 | ~19 MB (your test) |
| Ultra | 98 | 98 | 98 | ~10 MB |
| High | 95 | 95 | 95 | ~5 MB (your test) |
| Balanced | 92 | 92 | 92 | ~3 MB |
| Web | 85 | 85 | 85 | ~1 MB |

## Verification Steps

1. Process an AVIF with maximum preset
2. Check console output for:
   - "Converting back to original format: .webp → .avif"
   - "Resolution preserved: [width]x[height]"
   - File size comparison should show reasonable size

3. If file is still 343 KB, check:
   - Was Gemini used? (reduces to 1024x1024)
   - Was chunked Gemini used? (may reduce to 4K)
   - Check resolution in output

## The 343 KB Mystery

Your 343 KB output likely means:
- **Resolution was reduced** from original (check image dimensions)
- If using Gemini: 1024x1024 max
- If using chunked Gemini with 4K mode: 3840px width max
- A 10.9 MB AVIF reduced to 343 KB suggests ~30x reduction
- This matches a resolution reduction from ~6000x4000 to ~1024x1024

## Recommendation

For your high-quality AVIF files:
1. Use **maximum** or **ultra** preset
2. Use **ImageMagick only** (no Gemini)
3. Install `pillow-avif-plugin` for AVIF output
4. This should give you results matching your manual ImageMagick test