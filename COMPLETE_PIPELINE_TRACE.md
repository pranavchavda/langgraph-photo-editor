# Complete ImageMagick + Remove.bg Pipeline Trace

## Full Pipeline Flow for AVIF Input with Remove.bg

Let me trace exactly what happens to your 10.9 MB AVIF file:

### Step 1: AVIF → WebP Conversion
**Location**: `workflow_enhanced.py:268-293`
```python
# Converts AVIF to WebP since Claude API doesn't support AVIF
quality_settings = get_quality_settings()
save_with_quality(img, str(webp_path), source_format='WEBP', settings=quality_settings)
```
**Status**: ✅ Uses quality settings (98 for ultra, 100 for maximum)
**Output**: Should be ~10 MB WebP

### Step 2: Background Removal (remove.bg API)
**Location**: `workflow_enhanced.py:295-316` → calls `agents_enhanced.py:1390-1450`

#### 2a. Send WebP to remove.bg API
**Location**: `agents_enhanced.py:1390-1430`
```python
# Current code after fix:
if quality >= 98:
    size_param = 'full'  # Full resolution
elif quality >= 95:
    size_param = '4k'    # Up to 10MP
else:
    size_param = 'auto'

response = requests.post(
    'https://api.remove.bg/v1.0/removebg',
    files={'image_file': image_file},
    data={'size': size_param},  # Now uses quality-based size
    headers={'X-Api-Key': api_key}
)
```
**Status**: ✅ Fixed to use 'full' or '4k' based on quality
**Output**: PNG from API (size depends on size_param)

#### 2b. Save PNG from remove.bg
**Location**: `agents_enhanced.py:1401-1404`
```python
png_path = str(Path(image_path).parent / f"{Path(image_path).stem}-no-bg.png")
with open(png_path, 'wb') as out_file:
    out_file.write(response.content)
```
**Status**: ✅ Direct save, no compression
**Output**: PNG file (should be several MB if 'full' size used)

#### 2c. Convert PNG → WebP
**Location**: `agents_enhanced.py:1412-1480`
```python
# After fix - tries PIL first with quality settings
img = Image.open(png_path)
quality_settings = get_quality_settings()
save_with_quality(img, webp_path, source_format='WEBP', settings=quality_settings)

# Or falls back to ImageMagick
quality_value = str(quality_settings.get('imagemagick_quality', 95))
cmd = [magick_cmd, png_path, "-quality", quality_value, webp_path]
```
**Status**: ✅ Uses quality settings
**Output**: WebP with transparency

### Step 3: Analysis Stage
**Location**: `workflow_enhanced.py:318-336`
```python
# Analyzes the image after background removal
analysis = await run_enhanced_analysis(current_image, instructions, json.dumps(custom_params))
```
**Status**: ✅ No conversion happens here

### Step 4: ImageMagick Optimization
**Location**: `workflow_enhanced.py:573-591` → calls `agents_enhanced.py:924-1192`

#### 4a. Build ImageMagick command
**Location**: `agents_enhanced.py:86-246`
```python
def get_base_imagemagick_command():
    quality_settings = get_quality_settings()  # After fix
    config['quality'] = quality_settings.get('imagemagick_quality', 95)
    # ...
    cmd_parts.append(f"-quality {config['quality']}")
```
**Status**: ✅ Uses quality from preset

#### 4b. Execute ImageMagick
**Location**: `agents_enhanced.py:1140-1166`
```python
# Builds command like:
# magick input.webp [processing commands] -quality 98 -flatten output.webp
full_cmd = [magick_cmd, image_path] + cmd_parts + ["-flatten", output_path]
result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
```
**Status**: ✅ Includes quality flag
**Output**: Processed WebP

### Step 5: Quality Control
**Location**: `workflow_enhanced.py:600-605`
```python
qc_result = await run_enhanced_qc_agent(current_image, analysis)
```
**Status**: ✅ No conversion, just analysis

### Step 6: Format Preservation (Maximum preset only)
**Location**: `workflow_enhanced.py:645-651`
```python
if get_quality_settings().get("preserve_original_format", False):
    final_image_path = preserve_original_format(final_image_path, image_path)
```
**Status**: ✅ Converts back to AVIF if maximum preset
**Output**: AVIF (if maximum) or WebP (other presets)

### Step 7: Final Output
**Location**: `workflow_enhanced.py:700-704`
```python
final_output_path = finalize_output_with_quality_and_cleanup(
    final_image_path,
    final_quality,
    intermediate_files,
    passed_qc
)
```
**Status**: ✅ Renames based on quality score

## Potential Issues Still Present

### 1. Check if remove.bg is actually using the size parameter
The API might ignore the size parameter or downscale anyway. Add logging:
```python
print(f"Request size: {size_param}, Response size: {len(response.content)} bytes")
```

### 2. The `-flatten` flag in ImageMagick
This removes transparency! For images with removed backgrounds:
```python
# Should NOT use -flatten for transparent images
if has_transparency:
    full_cmd = [magick_cmd, image_path] + cmd_parts + [output_path]
else:
    full_cmd = [magick_cmd, image_path] + cmd_parts + ["-flatten", output_path]
```

### 3. Check actual file sizes at each step
Add file size logging:
```python
import os
print(f"File size: {os.path.getsize(filepath) / 1024 / 1024:.1f} MB")
```

## Testing Commands

To debug where the compression happens:

```bash
# Set maximum quality and verbose logging
export QUALITY_PRESET=maximum
export REMOVEBG_SIZE=full
export BACKGROUND_REMOVAL_METHOD=remove.bg

# Process and watch the console output
python photo_editor.py process test.avif 2>&1 | tee pipeline.log

# Check file sizes at each step
ls -lah *no-bg* *webp* *avif*
```

## Expected File Sizes

With proper quality settings:

1. **Original AVIF**: 10.9 MB
2. **AVIF → WebP**: ~10 MB (quality 98-100)
3. **Remove.bg PNG**: ~15-20 MB (lossless, with transparency)
4. **PNG → WebP**: ~8-10 MB (quality 98-100, with transparency)
5. **After ImageMagick**: ~8-10 MB (unless -flatten removes transparency)
6. **Final output**: ~8-10 MB WebP or AVIF

If you're getting 343 KB, one of these conversions is using low quality or the API is returning a tiny image.

## The Most Likely Culprit

Based on your test showing rembg works (5 MB output) but remove.bg doesn't (343 KB):

1. **remove.bg API is returning a small image** despite the size parameter
   - Check the actual PNG size from API
   - The API might have account limits or be ignoring the size parameter

2. **The -flatten flag is causing issues**
   - This removes alpha channel and can cause quality loss
   - Should be conditional based on transparency

## Quick Test

Try this to isolate the issue:
```bash
# Just test remove.bg without ImageMagick
export SKIP_IMAGEMAGICK=true
export QUALITY_PRESET=maximum
export REMOVEBG_SIZE=full
python photo_editor.py process test.avif

# Check the PNG from remove.bg
ls -lah *no-bg.png
```

This will show if remove.bg API is the problem or if it's the ImageMagick processing.