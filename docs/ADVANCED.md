# ⚙️ Advanced Usage Guide

Power user features and advanced techniques for the Agentic Photo Editor.

## 🎯 Advanced Processing Techniques

### Custom Processing Instructions

Fine-tune the AI's behavior with specific instructions:

```bash
# Environment variable approach
export CUSTOM_PROCESSING_INSTRUCTIONS="enhance chrome surfaces, reduce harsh shadows, professional e-commerce lighting"
python photo_editor.py process machine.jpg

# Inline approach
CUSTOM_PROCESSING_INSTRUCTIONS="darker mood, dramatic lighting" python photo_editor.py process image.jpg
```

### Advanced Instruction Examples

**Material-Specific Instructions:**
```bash
# Chrome and stainless steel
CUSTOM_PROCESSING_INSTRUCTIONS="enhance metallic surfaces, reduce overexposure on chrome, maintain authentic steel colors"

# Matte surfaces
CUSTOM_PROCESSING_INSTRUCTIONS="enhance texture detail, avoid oversaturation, maintain natural matte finish"

# Glass components  
CUSTOM_PROCESSING_INSTRUCTIONS="preserve transparency, enhance clarity, avoid blown highlights on glass"
```

**Lighting Style Instructions:**
```bash
# Professional e-commerce
CUSTOM_PROCESSING_INSTRUCTIONS="clean professional lighting, minimal shadows, high-end catalog style"

# Dramatic product photography
CUSTOM_PROCESSING_INSTRUCTIONS="dramatic shadows, high contrast, premium product aesthetic"

# Natural lighting
CUSTOM_PROCESSING_INSTRUCTIONS="natural daylight appearance, soft shadows, realistic colors"
```

**Quality-Specific Instructions:**
```bash
# Ultra high-end
CUSTOM_PROCESSING_INSTRUCTIONS="luxury product photography, perfect chrome detail, premium commercial quality"

# Fast processing
CUSTOM_PROCESSING_INSTRUCTIONS="minimal processing, natural look, quick optimization"
```

## 🔧 Environment Variables

### Processing Control
```bash
# Custom processing instructions
export CUSTOM_PROCESSING_INSTRUCTIONS="your instructions here"

# Custom adjustments (advanced)
export CUSTOM_ADJUSTMENTS='{"brightness_preference": 2, "contrast_preference": 1, "saturation_preference": -1}'

# Skip background removal
unset REMOVE_BG_API_KEY

# Quality control settings (future feature)
export QC_STRICTNESS="high"  # high, medium, low
```

### Performance Tuning
```bash
# Concurrent processing limits
export MAX_CONCURRENT_IMAGES=5

# Retry settings
export RETRY_ATTEMPTS=3
export QUALITY_THRESHOLD=0.9
```

## 📊 Batch Processing Strategies

### Large-Scale Processing

**Process by categories:**
```bash
# Espresso machines
python photo_editor.py batch ./espresso-machines/ --output-dir ./processed/espresso/
CUSTOM_PROCESSING_INSTRUCTIONS="enhance chrome, professional lighting" python photo_editor.py batch ./espresso-machines/

# Coffee accessories  
CUSTOM_PROCESSING_INSTRUCTIONS="natural colors, soft lighting" python photo_editor.py batch ./accessories/

# Grinders (different style)
CUSTOM_PROCESSING_INSTRUCTIONS="dramatic shadows, premium look" python photo_editor.py batch ./grinders/
```

**Progressive processing:**
```bash
# Process small test batch first
python photo_editor.py batch ./test-sample/ --max-concurrent 1

# Review results, then scale up
python photo_editor.py batch ./full-catalog/ --max-concurrent 3
```

**Resume interrupted batches:**
```bash
# System automatically skips already processed files
python photo_editor.py batch ./catalog/ --output-dir ./processed/
# If interrupted, just run again - it will continue where it left off
```

### Performance Optimization

**Conservative processing (older Macs):**
```bash
python photo_editor.py batch ./images/ \
  --max-concurrent 1 \
  --output-dir ./processed/
```

**Aggressive processing (powerful Macs):**
```bash
python photo_editor.py batch ./images/ \
  --max-concurrent 6 \
  --output-dir ./processed/
```

**Memory-efficient processing:**
```bash
# Process in smaller chunks
for dir in ./catalog/*/; do
  echo "Processing $dir"
  python photo_editor.py batch "$dir" --max-concurrent 2
  sleep 10  # Brief pause between batches
done
```

## 🎨 Quality Control Customization

### Understanding QC Scores

The AI quality control evaluates:
- **9-10**: Perfect commercial quality (passes)
- **7-8**: Good quality, minor improvements possible
- **5-6**: Noticeable issues, needs work
- **0-4**: Poor quality, major problems

### Interpreting QC Feedback

**Common QC issues and solutions:**

```bash
# "Oversaturated colors" - tone it down
CUSTOM_PROCESSING_INSTRUCTIONS="more natural colors, reduce saturation"

# "Harsh shadows" - softer lighting
CUSTOM_PROCESSING_INSTRUCTIONS="soft professional lighting, minimal shadows"

# "Overexposed highlights" - darker processing  
CUSTOM_PROCESSING_INSTRUCTIONS="reduce brightness, preserve detail in chrome"

# "Poor contrast" - enhance contrast
CUSTOM_PROCESSING_INSTRUCTIONS="increase contrast, enhance detail definition"
```

## 🖼️ Format and Output Control

### Input Format Optimization

**Prepare images for best results:**
```bash
# Convert RAW files first
for file in *.CR2; do
  magick "$file" "${file%.CR2}.jpg"
done

# Resize very large images
magick large-image.jpg -resize 2048x2048\> resized-image.jpg

# Enhance poor source material
magick blurry.jpg -unsharp 0x1.5+1.0+0.0 -enhance enhanced.jpg
```

### Output Format Control

**Convert WebP outputs if needed:**
```bash
# Convert single file
magick processed-image.webp final-image.jpg

# Batch convert WebP to JPG
for file in processed/*.webp; do
  magick "$file" "${file%.webp}.jpg"
done

# Convert with quality settings
magick processed.webp -quality 95 high-quality.jpg
```

## 🔄 Workflow Integration

### Shell Scripts for Automation

**Complete processing workflow:**
```bash
#!/bin/bash
# process-catalog.sh

# Setup
source venv/bin/activate
export CUSTOM_PROCESSING_INSTRUCTIONS="professional e-commerce lighting, enhance chrome"

# Process each category
for category in espresso-machines grinders accessories; do
  echo "Processing $category..."
  python photo_editor.py batch "./raw/$category/" \
    --output-dir "./processed/$category/" \
    --max-concurrent 3
  
  # Convert to JPG for legacy systems
  for webp in "./processed/$category/"*.webp; do
    magick "$webp" "${webp%.webp}.jpg"
  done
done

echo "Processing complete!"
```

**Quality check script:**
```bash
#!/bin/bash
# quality-check.sh

# Process single test image from each batch
for dir in ./raw/*/; do
  category=$(basename "$dir")
  test_image=$(find "$dir" -name "*.jpg" | head -1)
  
  if [ -f "$test_image" ]; then
    echo "Testing $category with $test_image"
    python photo_editor.py process "$test_image" --output-dir "./test-results/"
  fi
done
```

### Batch Organization

**Organize by processing requirements:**
```bash
# High-end products (more processing)
mkdir -p ./categories/premium/
CUSTOM_PROCESSING_INSTRUCTIONS="luxury product photography, perfect chrome detail" \
  python photo_editor.py batch ./categories/premium/

# Standard products (balanced processing)  
CUSTOM_PROCESSING_INSTRUCTIONS="clean professional lighting" \
  python photo_editor.py batch ./categories/standard/

# Quick processing (minimal changes)
CUSTOM_PROCESSING_INSTRUCTIONS="natural look, minimal processing" \
  python photo_editor.py batch ./categories/basic/
```

## 🔍 Debugging and Analysis

### Detailed Process Monitoring

**Monitor system resources during processing:**
```bash
# Terminal 1: Run processing
python photo_editor.py batch ./images/ --max-concurrent 3

# Terminal 2: Monitor resources
watch -n 2 'ps aux | grep python; echo "---"; df -h; echo "---"; free -h'
```

**Network monitoring:**
```bash
# Monitor API calls
netstat -an | grep :443 | wc -l  # Count active HTTPS connections
```

### Custom Processing Analysis

**Compare different instruction sets:**
```bash
# Test 1: Natural look
CUSTOM_PROCESSING_INSTRUCTIONS="natural colors, soft lighting" \
  python photo_editor.py process test.jpg --output-dir ./test1/

# Test 2: Enhanced look  
CUSTOM_PROCESSING_INSTRUCTIONS="vibrant colors, enhanced chrome" \
  python photo_editor.py process test.jpg --output-dir ./test2/

# Test 3: Dramatic look
CUSTOM_PROCESSING_INSTRUCTIONS="dramatic shadows, high contrast" \
  python photo_editor.py process test.jpg --output-dir ./test3/
```

## 🚀 Performance Optimization

### System Optimization

**Optimize macOS for processing:**
```bash
# Increase file descriptor limits
ulimit -n 4096

# Monitor memory usage
vm_stat | head -5

# Check available disk space
df -h
```

**Network optimization:**
```bash
# Use Google DNS for faster API calls
networksetup -setdnsservers "Wi-Fi" 8.8.8.8 8.8.4.4

# Check network speed
curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python
```

### Processing Speed Tips

**Optimize image sizes:**
```bash
# Pre-resize large images
find ./input/ -name "*.jpg" -exec magick {} -resize 2048x2048\> {} \;

# Remove EXIF data for faster processing
find ./input/ -name "*.jpg" -exec magick {} -strip {} \;
```

**Parallel processing techniques:**
```bash
# Process multiple directories simultaneously
python photo_editor.py batch ./dir1/ --output-dir ./out1/ &
python photo_editor.py batch ./dir2/ --output-dir ./out2/ &
python photo_editor.py batch ./dir3/ --output-dir ./out3/ &
wait  # Wait for all to complete
```

## 📈 Cost Optimization

### API Cost Management

**Estimate costs before processing:**
```bash
# Count images to process
find ./input/ -name "*.jpg" -o -name "*.png" -o -name "*.webp" | wc -l

# Rough cost calculation:
# Images × $0.02 (without background removal)
# Images × $0.22 (with background removal)
```

**Reduce costs:**
```bash
# Skip background removal for cost savings
mv .env .env.backup
echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" > .env

# Process only changed images
find ./input/ -newer ./last-processed.timestamp -name "*.jpg"
```

## 🔧 Customization Examples

### Industry-Specific Optimizations

**Coffee Equipment Photography:**
```bash
CUSTOM_PROCESSING_INSTRUCTIONS="enhance stainless steel and chrome surfaces, professional commercial lighting, preserve gauge readability, clean background"
```

**Kitchen Appliances:**
```bash
CUSTOM_PROCESSING_INSTRUCTIONS="enhance metallic finishes, reduce harsh reflections, professional product photography, consistent lighting"
```

**Tools and Hardware:**
```bash
CUSTOM_PROCESSING_INSTRUCTIONS="dramatic lighting, enhance metal textures, high contrast, industrial product aesthetic"
```

### Style Presets

Create your own preset commands:
```bash
# Add to your .bashrc or .zshrc
alias process-premium='CUSTOM_PROCESSING_INSTRUCTIONS="luxury product photography, perfect detail, premium commercial quality" python photo_editor.py'
alias process-standard='CUSTOM_PROCESSING_INSTRUCTIONS="clean professional lighting, balanced colors" python photo_editor.py'
alias process-natural='CUSTOM_PROCESSING_INSTRUCTIONS="natural colors, minimal processing, realistic lighting" python photo_editor.py'

# Usage:
process-premium process machine.jpg
process-standard batch ./standard-products/
```

---

## 💡 Pro Tips

1. **Start with single image tests** before batch processing
2. **Document successful instruction combinations** for reuse
3. **Use consistent lighting setups** in source photography for consistent AI results
4. **Monitor API usage** to manage costs
5. **Process in categories** with appropriate instructions for each
6. **Keep backups** of original images
7. **Test new instructions** on small batches first

**For best results**: Combine good source photography with specific, detailed processing instructions tailored to your product categories.