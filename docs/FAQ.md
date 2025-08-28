# ❓ Frequently Asked Questions

Common questions and quick answers for the Agentic Photo Editor.

## 🚀 Getting Started

### Q: I'm new to this. Where do I start?
**A:** Follow this order:
1. **[macOS Setup Guide](MACOS_SETUP.md)** - Get everything installed
2. **Test with one image** - `python photo_editor.py process test-image.jpg`
3. **Try chat mode** - `python photo_editor.py chat` and ask "process test-image.jpg brighter"
4. **Read the [User Guide](USER_GUIDE.md)** - Learn all the features

### Q: Do I need to be technical to use this?
**A:** Not at all! The chat mode lets you use plain English:
- "Make the coffee machine brighter"
- "Process all images in my folder with more vibrant colors"
- "Remove backgrounds and enhance chrome"

### Q: What's the difference between chat mode and the other commands?
**A:** 
- **Chat mode**: Natural language, easiest for beginners
- **Process command**: Direct single image processing
- **Batch command**: Process many images at once

## 🔑 API Keys & Setup

### Q: Where do I get API keys?
**A:** You need two keys:
1. **Anthropic** (Required): [console.anthropic.com](https://console.anthropic.com/) - for AI analysis
2. **remove.bg** (Optional): [remove.bg/api](https://www.remove.bg/api) - for background removal

### Q: Do the API keys cost money?
**A:** 
- **Anthropic**: Yes, but very affordable (~$0.01-0.03 per image)
- **remove.bg**: 50 free images/month, then ~$0.20 per image

### Q: What happens if I don't have a remove.bg key?
**A:** Background removal is skipped, but all other features work perfectly. You'll still get excellent optimization results.

### Q: How do I check if my API keys are working?
**A:** Run: `python photo_editor.py process test-image.jpg`
If it starts analyzing, your Anthropic key works. If it mentions background removal, your remove.bg key works too.

## 📁 File Handling

### Q: What image formats are supported?
**A:** 
- **Input**: JPG, JPEG, PNG, WebP
- **Output**: Always WebP (supports transparency, high quality, smaller files)

### Q: Why does everything output as WebP?
**A:** WebP is perfect for e-commerce:
- Supports transparency (for background removal)
- Better quality than JPEG at smaller file sizes
- Supported by all modern browsers
- Industry standard for product photography

### Q: Can I convert WebP back to JPG?
**A:** Yes! Use ImageMagick: `magick image.webp image.jpg`
Or online converters, but WebP is usually better for web use.

### Q: Where do processed images go?
**A:** 
- **Same directory as input** (with `-processed` suffix) by default
- **Custom location**: Use `--output-dir` flag
- **Example**: `input.jpg` becomes `input-processed.webp`

## 🎨 Image Processing

### Q: How long does processing take?
**A:** Typically 30-90 seconds per image:
- Analysis: 10-20 seconds
- Optimization: 5-10 seconds  
- Background removal: 10-30 seconds (if used)
- Quality control: 5-15 seconds

### Q: Why is it taking so long?
**A:** The AI does a thorough job:
1. **Detailed analysis** of materials, lighting, colors
2. **Custom optimization** for each specific image
3. **Quality control** with possible retries
4. **Professional results** take time vs. one-size-fits-all filters

### Q: Can I make it faster?
**A:** For batch processing:
- Lower `--max-concurrent` to 1 or 2
- Skip background removal (remove remove.bg key from .env)
- Use smaller source images

### Q: What does the quality score mean?
**A:** 0-10 scale:
- **9-10**: Excellent commercial quality (passes)
- **7-8**: Good quality, minor issues 
- **5-6**: Needs improvement
- **0-4**: Poor quality, major issues
- **Auto-retry**: Anything below 9 triggers automatic retry with improvements

### Q: Why did it retry processing?
**A:** The AI quality control detected issues and automatically tried to fix them:
- Too bright/dark
- Color problems
- Artifacts or noise
- Poor contrast
- This is good! It means the system is being thorough.

## 🎯 Results & Quality

### Q: The results don't look good. What's wrong?
**A:** Try these steps:
1. **Better source images** - Well-lit, in-focus photos work best
2. **Specific instructions** - "enhance chrome on espresso machine" vs. "make better"
3. **Check the original** - Poor input = poor output
4. **Try different instructions** - "more natural" vs. "more vibrant"

### Q: How do I get consistent results across multiple images?
**A:** 
1. **Use similar source material** (same lighting setup, angles)
2. **Apply same custom instructions** to entire batch
3. **Process in batches** by product type or style
4. **Review and adjust** based on first few results

### Q: The colors look weird/unnatural
**A:** Try these instructions:
- "More natural colors"
- "Less saturated" 
- "Professional product photography look"
- "Realistic chrome and steel colors"

### Q: It made everything too bright
**A:** Use instructions like:
- "Darker, more professional"
- "Natural lighting"
- "Reduce brightness"
- "Moody product photography"

## 🔧 Technical Issues

### Q: I get "command not found" errors
**A:** Make sure you:
1. **Activated virtual environment**: `source venv/bin/activate`
2. **Are in right directory**: `cd langgraph-photo-editor`
3. **Installed dependencies**: `pip install -r requirements.txt`

### Q: "magick: command not found"
**A:** Install ImageMagick: `brew install imagemagick`
Then verify: `magick --version`

### Q: Python/pip errors during installation
**A:** Try:
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Q: API key errors
**A:** Check your `.env` file:
1. **File exists**: `ls -la .env` (should show the file)
2. **Keys are correct**: `cat .env` (should show your keys)
3. **No extra spaces**: Keys should be exactly as provided
4. **Quotes optional**: `KEY=abc123` or `KEY="abc123"` both work

### Q: "Virtual environment not found"
**A:** 
```bash
# Create new virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 📊 Batch Processing

### Q: How many images can I process at once?
**A:** No limit! But consider:
- **API costs** (Anthropic charges per image)
- **API quotas** (remove.bg has monthly limits)
- **Processing time** (30-90 seconds each)
- **System resources** (memory, CPU)

### Q: Can I pause/resume batch processing?
**A:** Not currently, but you can:
- **Stop with Ctrl+C** (processed images are saved)
- **Resume by processing remaining files** (system skips already processed)
- **Use smaller batches** (50-100 images at a time)

### Q: Some images failed. What happened?
**A:** Common causes:
- **Corrupted source files**
- **Network issues** (API calls failed)
- **API quota exceeded** (especially remove.bg)
- **Unsupported formats** or **very large files**
- Check the error messages for specifics

## 🎨 Customization

### Q: Can I save my favorite settings?
**A:** Not built-in yet, but you can:
- **Save successful instructions** in a text file
- **Use consistent environment variables**
- **Create shell aliases** for common commands

### Q: Can I process RAW files?
**A:** Not directly. Convert to JPG/PNG first:
- **Adobe Lightroom/Photoshop**
- **macOS Photos app** (export as JPEG)
- **Online converters**
- **ImageMagick**: `magick image.CR2 image.jpg`

### Q: Can I adjust the quality control standards?
**A:** The system is designed for commercial e-commerce quality. If you need different standards, contact Pranav for customization.

## 💰 Costs

### Q: How much does it cost to process images?
**A:** 
- **Anthropic**: ~$0.01-0.03 per image (AI analysis)
- **remove.bg**: Free for 50/month, then ~$0.20 per image
- **Total**: ~$0.01-0.23 per image depending on background removal

### Q: Can I estimate costs for large batches?
**A:** 
- **Without background removal**: ~$0.02 × number of images
- **With background removal**: ~$0.22 × number of images
- **Example**: 1000 images ≈ $20-220 depending on background removal

## 📚 Learning More

### Q: I want to understand how it works
**A:** The system uses:
1. **Claude Sonnet 4** for image analysis and quality control
2. **ImageMagick** for actual image processing
3. **remove.bg API** for background removal
4. **LangGraph** for orchestrating the workflow

### Q: Can I see what commands it's running?
**A:** Yes! The system shows:
- Real-time progress for each step
- Quality scores and retry reasons
- You can also check the generated ImageMagick commands in logs

### Q: Where can I learn more about product photography?
**A:** The AI handles the technical optimization, but for better source material:
- **Good lighting** is crucial
- **Clean backgrounds** help
- **Sharp focus** on the product
- **Consistent setup** across batches

---

## 🆘 Still Need Help?

1. **Check [Troubleshooting Guide](TROUBLESHOOTING.md)**
2. **Review [User Guide](USER_GUIDE.md)** for detailed instructions
3. **Contact Pranav** for iDrinkCoffee.com specific questions
4. **Try chat mode** - it's the most forgiving way to experiment!

**Remember**: Start simple, experiment with chat mode, and build up to more complex batch processing!