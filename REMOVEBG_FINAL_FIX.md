# Remove.bg Pipeline - Final Fixes

## Issues Found and Fixed

### 1. ❌ **`-flatten` Flag Removing Transparency**
The ImageMagick command was always using `-flatten` which:
- Removes the alpha channel (transparency)
- Flattens image to white background
- Can cause massive quality/size reduction

**Fix Applied**: Now checks if image has transparency and only uses `-flatten` for non-transparent images.

### 2. ❌ **Remove.bg API Size Parameter**
Was using `size: 'auto'` which lets API choose (often smaller to save credits).

**Fix Applied**: Now uses quality-based size selection:
- Maximum/Ultra preset → `'full'` (preserves all pixels)
- High preset → `'4k'` (up to 10MP)
- Other presets → `'auto'`

### 3. ❌ **Missing Quality Flags in Conversions**
Some conversions didn't explicitly set quality.

**Fix Applied**: All conversions now use quality settings from presets.

### 4. ✅ **Added Comprehensive Logging**
Now logs file sizes at each step to help debug:
- Input file size sent to remove.bg
- Response size from remove.bg API
- PNG and WebP file sizes after conversion

## Complete Fixed Pipeline

```
1. AVIF (10.9 MB)
   ↓
2. Convert to WebP with quality 98-100 (~10 MB)
   ↓
3. Send to remove.bg API with size='full' or '4k'
   ↓
4. Receive PNG from API (should be 5-15 MB if full size)
   ↓
5. Convert PNG to WebP with quality 98-100 (~5-10 MB)
   ↓
6. ImageMagick processing WITHOUT -flatten (~5-10 MB)
   ↓
7. Final output (~5-10 MB)
```

## How to Test

```bash
# Maximum quality with full resolution
export QUALITY_PRESET=maximum
export REMOVEBG_SIZE=full
export BACKGROUND_REMOVAL_METHOD=remove.bg

# Process and watch the logs
python photo_editor.py process test.avif
```

## What to Look For in Console Output

You should see:
```
📤 Sending to remove.bg: test.webp (10.0 MB)
Using full resolution for remove.bg (highest quality, more credits)
📊 remove.bg response: 8.5 MB for size 'full'
PNG from remove.bg: 8.5 MB
Converted to WebP: 7.2 MB (quality 100)
Preserving transparency - not using -flatten
```

## If Still Getting 343 KB

Check the console for:

1. **remove.bg response size** - If it's small (< 1 MB), the API is returning a low-res image despite the size parameter. This could be due to:
   - Account limits
   - API ignoring the parameter
   - Credit restrictions

2. **"Using -flatten"** message - Should NOT appear for images with removed backgrounds

3. **Quality values** - Should show 95-100 depending on preset

## Alternative: Use rembg

Since rembg works perfectly (5 MB output), you can force it:

```bash
export BACKGROUND_REMOVAL_METHOD=rembg
export REMBG_MODEL=bria-rmbg
```

## The Root Cause

The 343 KB output was likely caused by:
1. **`-flatten` removing transparency** and compressing the flattened image
2. **remove.bg API returning small image** (check the response size in logs)
3. **Quality loss through multiple conversions** without explicit quality flags

All three issues are now fixed. The console output will show exactly where any remaining compression happens.

## Quick Debug Test

To isolate if it's remove.bg API or ImageMagick:

```bash
# Skip ImageMagick to test just remove.bg
export SKIP_IMAGEMAGICK=true
export QUALITY_PRESET=maximum
export REMOVEBG_SIZE=full

python photo_editor.py process test.avif

# Check the output size - if it's 343 KB, remove.bg API is the issue
# If it's several MB, then ImageMagick was the problem (now fixed)
```