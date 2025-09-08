# Doug's Photo Editor - Complete User Guide

## Quick Start

### 1. Open the App
Navigate to your Streamlit app URL or run locally with:
```bash
streamlit run streamlit_app.py
```

### 2. Enter Your API Keys (First Time Only)
In the left sidebar under **Settings**:
- **Anthropic API Key** (Required) - For image analysis
- **Gemini API Key** (Required for AI enhancement) - For AI-powered editing
- **Remove.bg API Key** (Optional) - For professional background removal

Click **💾 Save Keys** - they'll be saved in your browser for future sessions.

## Processing Modes

### 🖼️ Single Image Mode
Perfect for testing settings or processing individual product photos.

1. **Upload Image**: Click "Choose an image to enhance"
2. **Set Instructions**: Modify the text to describe what you want
3. **Choose Options** (see Processing Options below)
4. **Click Process**: Hit the green "🚀 Process Image" button
5. **Download Result**: Click the large download button when complete

### 📦 Batch Processing Mode
For processing multiple product images with consistent settings.

1. **Switch to Batch Mode**: Click "📦 Batch Processing" at the top
2. **Upload Multiple Images**: Select all images at once
3. **Set Batch Instructions**: Describe desired enhancements
4. **Enable Batch Consistency**: Keep checked for uniform results
5. **Process All**: Click "🚀 Process All Images"
6. **Download ZIP**: Get all processed images in one ZIP file

## Processing Options Explained

### Core Enhancement Options

#### **Use ImageMagick Optimization** ✅ (Recommended ON)
- Traditional image processing for sharpening, color correction, and optimization
- Fast, reliable, always gives consistent results
- Best for: Basic enhancements, color correction, sharpening
- Turn OFF only if you want pure AI enhancement

#### **Use Gemini AI Enhancement** (Default OFF)
- AI-powered editing using natural language instructions
- Can understand complex requests like "make the chrome more reflective"
- Slower and outputs at lower resolution (1024x1024)
- Best for: Complex edits that ImageMagick can't handle

#### **Use Chunked Gemini (High-Res AI)** 🆕 (Advanced)
- Processes large images in chunks to maintain full resolution
- Combines AI editing with high resolution output
- Much slower but preserves image quality
- Best for: When you need both AI editing AND high resolution

#### **🎯 Targeted Gemini Enhancement** (Experimental)
- Only shows when ImageMagick is ON and Gemini is OFF
- Identifies specific areas (chrome, glass, textures) and enhances them with AI
- Surgical precision - only enhances what needs it
- Best for: Products with mixed materials that need selective enhancement

#### **Remove Background** (Default ON)
- Uses Remove.bg API to professionally remove backgrounds
- Creates transparent PNG/WebP files
- Turn OFF for: Lifestyle shots or when you want to keep the background

### 📷 Lens Corrections

#### **Apply Lens Corrections** (Default OFF)
- Fixes distortion, vignetting, and chromatic aberration
- Auto-detects your lens from image EXIF data
- Supported lenses:
  - Sony FE 24-70mm F2.8 GM
  - Sony FE 90mm F2.8 Macro G OSS
  - Sony FE 50mm F1.4 GM
  - Sony FE 70-200mm F2.8 GM OSS

**When to use:**
- Turn ON if you notice barrel distortion (curved edges)
- Turn ON if you see dark corners (vignetting)
- Usually not needed for product photography with good lighting

## Understanding the Workflow

### What Happens When You Click Process:

1. **Analysis** (Claude Sonnet)
   - Examines image for issues
   - Determines optimal enhancement strategy
   - Identifies materials and surfaces

2. **Lens Correction** (if enabled)
   - Fixes optical distortions
   - Removes vignetting
   - Corrects chromatic aberration

3. **Enhancement**
   - **If ImageMagick**: Applies calculated adjustments
   - **If Gemini**: Sends to AI with your instructions
   - **If Both**: Gemini first, then ImageMagick cleanup

4. **Background Removal** (if enabled)
   - Removes background professionally
   - Creates transparent image

5. **Targeted Enhancement** (if enabled)
   - Finds specific areas needing work
   - Applies AI enhancement surgically

6. **Quality Control** (Claude)
   - Checks final result
   - Scores quality (1-10)
   - May retry if quality is too low

## Tips for Best Results

### For Product Photography

#### Chrome/Metal Products:
```
Instructions: "Enhance chrome reflections, increase contrast, make metals look premium and polished"
Settings: ImageMagick ON, Targeted Enhancement ON
```

#### Matte/Textured Products:
```
Instructions: "Enhance texture details, improve lighting, maintain natural material appearance"
Settings: ImageMagick ON, Gemini OFF
```

#### Mixed Materials:
```
Instructions: "Enhance each material appropriately - make chrome reflective, wood natural, plastics vibrant"
Settings: ImageMagick ON, Targeted Enhancement ON
```

### Batch Processing Tips

1. **Always use Batch Consistency Mode** - Ensures all images have similar brightness/color
2. **Test on Single Image First** - Find optimal settings before batch processing
3. **Group Similar Products** - Process chrome items separately from wood items
4. **Monitor First Few Results** - Check quality early to avoid wasting time

### Common Issues & Solutions

#### Image Too Dark/Bright:
- Adjust instructions: "Brighten slightly" or "Reduce exposure slightly"
- ImageMagick usually handles this well

#### Colors Look Wrong:
- Try: "Correct white balance, enhance natural colors"
- Enable lens corrections if using wide angle lens

#### Lost Details in Enhancement:
- Turn OFF Gemini, use ImageMagick only
- Or try Chunked Gemini for high-res AI

#### Processing Too Slow:
- Turn OFF Gemini/Chunked Gemini
- Use ImageMagick only for speed
- Reduce concurrent batch processing

#### Background Removal Issues:
- Make sure Remove.bg API key is entered
- For complex edges, may need manual touchup

## Quality Scores

The system rates each image 1-10:
- **9-10**: Excellent, ready for use
- **7-8**: Good, minor imperfections
- **5-6**: Acceptable, may need manual touchup
- **Below 5**: Poor, system will retry automatically

Files with scores ≤8 get renamed with quality suffix (e.g., `-q7.webp`)

## Advanced Features

### Batch Consistency
When enabled, the system:
1. Analyzes all images first
2. Determines common brightness/color targets
3. Applies consistent adjustments to all
4. Prevents some images being much brighter/darker than others

### Concurrent Processing
- Slider from 1-5 workers
- More workers = faster but uses more memory
- Recommended: 3 for most systems

### Custom Instructions
You can be very specific:
- "Make the chrome 20% more reflective"
- "Warm up the color temperature slightly"
- "Increase contrast but maintain shadow detail"
- "Make it look like Apple product photography"

## Keyboard Shortcuts
- None currently - all interaction through UI

## File Formats
- **Input**: JPG, JPEG, PNG, WebP
- **Output**: WebP (best quality/size ratio)
- Preserves transparency when background removed

## Troubleshooting

### "API Key Invalid"
- Check your API keys in Settings
- Make sure no extra spaces
- Try saving keys again

### "Processing Failed"
- Check error message for details
- Usually means API quota exceeded
- Try with different options (disable Gemini)

### "Quality Check Failed"
- System will retry automatically (up to 2 times)
- If still fails, try different instructions
- May need manual editing

### Images Look Over-Processed
- Reduce enhancement: "Subtle improvements only"
- Turn off Targeted Enhancement
- Use ImageMagick only

## Best Practices

1. **Start Conservative**: Begin with minimal enhancement, increase if needed
2. **Batch Similar Items**: Group products by material and lighting
3. **Save Your Settings**: Note which options work for your products
4. **Monitor API Usage**: Gemini and Remove.bg have quotas
5. **Test First**: Always test on one image before batch processing

## Need Help?

- Error messages are descriptive - read them carefully
- Check the terminal/console for detailed logs
- Most issues are API key or quota related
- For consistent results, prefer ImageMagick over Gemini

---

*Remember: The goal is professional, consistent product photos. When in doubt, less enhancement is often better than more!*