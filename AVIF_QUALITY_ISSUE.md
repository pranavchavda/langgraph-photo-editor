# AVIF Quality and Size Issue - Resolution

## The Problem
- Input: 10.9 MB AVIF file
- Output: 343 KB file (97% size reduction!)
- Quality degradation visible even with "maximum" preset

## Root Causes Identified

### 1. **Format Conversion Without Preservation**
- AVIF files were converted to WebP for processing (Claude API doesn't support AVIF)
- The pipeline never converted back to AVIF format
- WebP compression, even at quality 98-100, can't match AVIF's efficiency for certain images

### 2. **Possible Resolution Changes**
- If Gemini AI was used, images are processed at lower resolution (1024x1024)
- Chunked Gemini processes at 900x900 chunks, potentially at 4K resolution
- Check if either Gemini mode was enabled during processing

### 3. **AVIF's Superior Compression**
- AVIF can achieve 50% better compression than WebP at same quality
- A 10.9 MB AVIF at high quality might only be 1-2 MB in WebP at same visual quality
- The 343 KB output suggests either resolution reduction or quality loss

## Solutions Implemented

### 1. **Format Preservation System**
Created `src/format_preservation.py` to:
- Convert processed images back to original format
- Support AVIF output with `pillow-avif-plugin`
- Preserve original format when using "maximum" or "ultra" presets with `preserve_original_format: true`

### 2. **Quality Configuration Updates**
- Maximum preset now uses `preserve_original_format: true`
- AVIF files are converted to lossless PNG for intermediate processing when using maximum quality
- Added resolution checking to warn about size changes

### 3. **Resolution Preservation**
- Added checks to detect and warn about resolution changes
- File size comparison to identify suspicious reductions

## How to Use

### For Maximum Quality AVIF Preservation:

1. **Install AVIF support**:
```bash
pip install pillow-avif-plugin
```

2. **Use Maximum quality preset**:
```bash
# CLI
python photo_editor.py --quality-preset maximum process image.avif

# Or set environment variable
export QUALITY_PRESET=maximum
```

3. **In Streamlit**:
- Select "maximum" from Quality Preset dropdown
- This will preserve the AVIF format

### Important Settings to Check:

1. **Avoid Gemini AI** for maximum quality:
   - Regular Gemini reduces to 1024x1024
   - Chunked Gemini may reduce to 4K (3840px wide)
   - Use ImageMagick-only mode for full resolution

2. **Environment Variables for Maximum Quality**:
```bash
export QUALITY_PRESET=maximum
export SKIP_GEMINI=true
export PRESERVE_FORMAT=true
export USE_LOSSLESS_INTERMEDIATE=true
```

## Recommendations

### For AVIF Files:
1. **Use "maximum" preset** - Preserves format and uses lossless processing
2. **Avoid Gemini AI modes** - They resize images
3. **Use ImageMagick only** - Maintains full resolution
4. **Install pillow-avif-plugin** - Enables AVIF output

### To Verify Quality:
- Check the console output for resolution warnings
- Look for size comparison messages
- Original AVIF → processed AVIF should be similar size (±20%)
- If size reduces by >50%, likely quality or resolution loss

## Testing

Run this to test AVIF preservation:
```python
python test_avif_preservation.py
```

This will:
1. Process an AVIF with maximum quality
2. Check if format is preserved
3. Verify resolution is maintained
4. Compare file sizes