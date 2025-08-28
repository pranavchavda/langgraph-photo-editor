# 📖 User Guide

Complete guide to using the Agentic Photo Editor for product photography optimization.

## 🎯 Overview

The Agentic Photo Editor uses Claude Sonnet 4 AI to analyze your product photos and automatically apply the best optimizations. It's specifically designed for e-commerce product photography, especially for coffee equipment, espresso machines, and similar products.

## 🚀 Getting Started

### 1. Always Activate Virtual Environment First

```bash
# Navigate to project directory
cd langgraph-photo-editor

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your prompt
```

### 2. Choose Your Processing Method

## 💬 Chat Mode (Recommended for Beginners)

The easiest way to use the photo editor. Just describe what you want in natural language!

```bash
python photo_editor.py chat
```

### Chat Examples

```
Your instruction: Make the espresso machines brighter and more vibrant
Your instruction: Process ~/Desktop/coffee-photos/ but keep them natural
Your instruction: Trim whitespace and enhance chrome on all steel machines
Your instruction: Process image.jpg with darker, more professional look
```

### What You Can Ask For:

**Brightness & Contrast:**
- "Make it brighter"
- "Darker and more moody" 
- "More contrast"
- "Natural lighting"

**Colors:**
- "More vibrant colors"
- "Less saturated, more natural"
- "Enhance the chrome"
- "Fix the color cast"

**Cropping & Cleanup:**
- "Trim the whitespace"
- "Remove excess border"
- "Crop tighter"

**Style:**
- "Professional e-commerce look"
- "More dramatic"
- "Clean and minimal"
- "High-end catalog style"

## 🖼️ Single Image Processing

Process one image at a time with full control:

```bash
# Basic processing
python photo_editor.py process image.jpg

# Specify output directory
python photo_editor.py process image.jpg --output-dir ./processed/

# With custom instructions
CUSTOM_PROCESSING_INSTRUCTIONS="make it brighter and trim edges" python photo_editor.py process image.jpg
```

## 📁 Batch Processing

Process entire directories of images:

```bash
# Process all images in a directory
python photo_editor.py batch ~/Desktop/product-photos/

# Specify output directory
python photo_editor.py batch ./input/ --output-dir ./output/

# Control number of simultaneous processing
python photo_editor.py batch ./photos/ --max-concurrent 2

# Process only specific file types
python photo_editor.py batch ./photos/ --pattern "*.jpg"
```

## 🔍 Understanding the Process

The AI goes through 4 stages for each image:

### 1. 🧠 Analysis Phase
Claude examines your image and identifies:
- **Materials**: Chrome, stainless steel, matte surfaces, glass
- **Lighting issues**: Shadows, overexposure, uneven lighting
- **Color problems**: Saturation, color cast, vibrancy needs
- **Background**: Whether to remove background or not

### 2. ⚡ Optimization Phase
Applies ImageMagick commands based on analysis:
- Brightness/contrast adjustments
- Color saturation enhancement
- Gamma correction for tonal balance
- Sharpening for product details
- Trimming excess whitespace

### 3. 🖼️ Background Removal Phase (if needed)
- Uses remove.bg API for professional background removal
- Creates clean transparent backgrounds
- Maintains product quality

### 4. ✅ Quality Control Phase
Claude evaluates the result:
- Professional appearance check
- Color accuracy verification
- Detail preservation assessment
- Background quality review

**Quality Scores**: 0-10 scale where 9+ passes, <9 triggers automatic retry with improvements.

## 🎨 Input & Output Formats

### Supported Input Formats:
- **JPG/JPEG** - Standard photo format
- **PNG** - With transparency support
- **WebP** - Modern web format

### Output Format:
- **Always WebP** - High quality, supports transparency
- Preserves image quality while reducing file size
- Compatible with all modern web browsers

## 🔧 Advanced Usage

### Custom Processing Instructions

You can provide specific instructions using environment variables:

```bash
# Set custom instructions
export CUSTOM_PROCESSING_INSTRUCTIONS="make it darker and more dramatic"
python photo_editor.py process image.jpg

# Or inline
CUSTOM_PROCESSING_INSTRUCTIONS="bright and vibrant" python photo_editor.py process image.jpg
```

### Processing Specific File Types

```bash
# Only process JPG files
python photo_editor.py batch ./photos/ --pattern "*.jpg"

# Process multiple formats
python photo_editor.py batch ./photos/ --pattern "*.{jpg,png}"
```

### Controlling Concurrency

For batch processing, you can control how many images process simultaneously:

```bash
# Conservative (good for older Macs)
python photo_editor.py batch ./photos/ --max-concurrent 1

# Default
python photo_editor.py batch ./photos/ --max-concurrent 3

# Aggressive (good for powerful Macs)
python photo_editor.py batch ./photos/ --max-concurrent 5
```

## 📊 Understanding the Progress Display

During processing, you'll see a rich display showing:

### Real-time Status
- **🔍 Analysis**: AI examining the image
- **⚡ Optimization**: Applying improvements  
- **🖼️ Background**: Removing background (if needed)
- **✅ QC**: Quality control check

### Quality Scores
- **9-10**: Excellent, commercial quality
- **7-8**: Good quality, minor issues
- **5-6**: Acceptable but could be better
- **0-4**: Poor quality, needs significant work

### Retry Information
If quality is below 9, the system automatically:
1. Identifies specific issues
2. Adjusts processing parameters
3. Retries with improved settings
4. Shows retry attempts (up to 2 retries)

## 🎯 Best Practices

### For Best Results:

1. **Start with Good Source Images**
   - Well-lit product photos
   - Decent resolution (1000px+ on longest side)
   - Clear, focused subjects

2. **Use Descriptive Instructions**
   - Be specific: "brighter chrome" vs "better"
   - Mention the product: "espresso machine" vs "it"
   - Include style preferences: "professional e-commerce look"

3. **Process Single Images First**
   - Test with one image before batch processing
   - Understand how the AI interprets your style
   - Refine your instructions based on results

4. **Organize Your Files**
   - Keep source images in one folder
   - Use descriptive file names
   - Create output folders for processed images

### Performance Tips:

1. **For Large Batches**
   - Use lower concurrency on older Macs
   - Process in smaller batches (50-100 images)
   - Ensure stable internet connection

2. **For Consistent Results**
   - Use similar source material (same lighting, setup)
   - Apply the same custom instructions to batches
   - Review and refine based on QC feedback

## 🔄 Handling Issues

### If Processing Fails:
1. **Check your internet connection** (AI analysis requires internet)
2. **Verify API keys** (check your .env file)
3. **Try a single image first** (isolate the problem)
4. **Check file permissions** (make sure files are readable)

### If Quality is Poor:
1. **Try more specific instructions** ("enhance chrome details")
2. **Process source material again** (different source = different results)
3. **Check source image quality** (blurry input = poor output)

### If Background Removal Fails:
1. **Check remove.bg API key** (background removal is optional)
2. **Verify API quota** (free accounts have monthly limits)
3. **Continue without background removal** (optimization still works)

## 📚 Next Steps

- **[FAQ](FAQ.md)** - Common questions and quick answers
- **[Advanced Usage](ADVANCED.md)** - Power user features
- **[Troubleshooting](TROUBLESHOOTING.md)** - Fix technical issues

---

**Pro Tip**: Start with chat mode and experiment with different instructions to understand how the AI interprets your requests!