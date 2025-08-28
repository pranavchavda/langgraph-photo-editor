# 🔧 Troubleshooting Guide

Solutions to common issues when using the Agentic Photo Editor on macOS.

## 🚨 Quick Fixes

### "Command not found" errors
```bash
# Make sure you're in the right directory
cd langgraph-photo-editor

# Activate virtual environment  
source venv/bin/activate

# Should see (venv) in your prompt
```

### "magick: command not found"
```bash
# Install ImageMagick
brew install imagemagick

# Verify installation
magick --version
```

### "No module named..." errors
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

## 🔑 API Key Issues

### "Invalid API key" or Authentication Errors

**Check your .env file:**
```bash
# View your .env file
cat .env

# Should show:
# ANTHROPIC_API_KEY=sk-ant-...
# REMOVE_BG_API_KEY=...
```

**Common issues:**
- **Missing quotes**: Both `KEY=value` and `KEY="value"` work
- **Extra spaces**: Should be `KEY=value`, not `KEY = value`
- **Wrong key format**: Anthropic keys start with `sk-ant-`
- **Expired keys**: Generate new ones if needed

**Fix by recreating .env:**
```bash
# Remove old file
rm .env

# Create new one
touch .env
open -a TextEdit .env

# Add your keys (one per line):
ANTHROPIC_API_KEY=your_actual_key_here
REMOVE_BG_API_KEY=your_actual_key_here
```

### API Quota Exceeded

**remove.bg quota exceeded:**
- **Free account**: 50 images per month
- **Solution**: Upgrade account or skip background removal
- **Skip background removal**: Remove `REMOVE_BG_API_KEY` from .env

**Anthropic quota exceeded:**
- **Check usage**: [console.anthropic.com](https://console.anthropic.com/)
- **Add credits**: Add payment method to account
- **Typical cost**: ~$0.01-0.03 per image

## 🐍 Python & Environment Issues

### Virtual Environment Problems

**Can't activate virtual environment:**
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Wrong Python version:**
```bash
# Check Python version
python3 --version

# Should be 3.8 or higher
# If not, install newer Python:
brew install python@3.11
```

### Package Installation Failures

**Pip install errors:**
```bash
# Update pip first
pip install --upgrade pip

# Clear cache and reinstall
pip cache purge
pip install -r requirements.txt --no-cache-dir

# If still failing, try one by one:
pip install anthropic
pip install langchain-anthropic
pip install langgraph
pip install rich
pip install click
pip install requests
pip install pillow
pip install python-dotenv
```

**Permission errors:**
```bash
# Don't use sudo! Use virtual environment instead
source venv/bin/activate
pip install -r requirements.txt
```

## 📁 File & Directory Issues

### File Not Found Errors

**Image file not found:**
```bash
# Check file exists
ls -la path/to/image.jpg

# Use absolute paths if unsure
python photo_editor.py process ~/Desktop/image.jpg
```

**Directory not found:**
```bash
# Check directory exists and has images
ls path/to/directory/

# Look for supported formats
ls path/to/directory/*.{jpg,jpeg,png,webp}
```

### Permission Errors

**Can't read/write files:**
```bash
# Check file permissions
ls -la image.jpg

# Fix permissions if needed
chmod 644 image.jpg

# For directories
chmod 755 directory/
```

**Can't create output files:**
```bash
# Check output directory permissions
ls -la output-directory/

# Create directory if missing
mkdir -p output-directory/
```

## 🖼️ Image Processing Issues

### Processing Hangs or Takes Forever

**Check network connection:**
- AI analysis requires internet
- remove.bg requires stable connection
- Try processing a single image first

**Reduce concurrent processing:**
```bash
# Use only 1 concurrent process
python photo_editor.py batch directory/ --max-concurrent 1
```

**Skip background removal:**
```bash
# Remove remove.bg key temporarily
mv .env .env.backup
echo "ANTHROPIC_API_KEY=your_key" > .env
```

### Poor Quality Results

**Blurry or low-quality output:**
- Check source image quality
- Use higher resolution inputs (1000px+ recommended)
- Ensure source images are sharp and well-lit

**Colors look wrong:**
```bash
# Try more specific instructions
CUSTOM_PROCESSING_INSTRUCTIONS="natural colors, realistic chrome" python photo_editor.py process image.jpg
```

**Too bright/dark:**
```bash
# Adjust with custom instructions
CUSTOM_PROCESSING_INSTRUCTIONS="darker, professional lighting" python photo_editor.py process image.jpg

# Or
CUSTOM_PROCESSING_INSTRUCTIONS="brighter, more vibrant" python photo_editor.py process image.jpg
```

### Constant Retries/Failures

**QC keeps failing:**
1. Check source image quality (not blurry, corrupted, etc.)
2. Try simpler instructions
3. Process a known-good image to isolate the issue

**Background removal fails:**
- remove.bg may be down or quota exceeded
- Check [remove.bg status](https://www.remove.bg/)
- Try without background removal

## 🌐 Network & Connection Issues

### Slow Processing

**Optimize for slow connections:**
```bash
# Process fewer images simultaneously
python photo_editor.py batch directory/ --max-concurrent 1

# Process smaller batches
python photo_editor.py batch directory/ --pattern "*.jpg" | head -10
```

### Timeout Errors

**API timeouts:**
- Check internet stability
- Try processing during off-peak hours
- Restart router/modem if needed

**Connection refused:**
- Check firewall settings
- Ensure outbound HTTPS is allowed
- Try using mobile hotspot temporarily

## 💻 System-Specific Issues

### macOS Specific Problems

**Xcode command line tools:**
```bash
# Install if missing
sudo xcode-select --install
```

**Homebrew issues:**
```bash
# Update Homebrew
brew update

# Reinstall ImageMagick
brew uninstall imagemagick
brew install imagemagick
```

**M1/M2 Mac issues:**
```bash
# Use Rosetta if needed for old packages
arch -x86_64 python3 -m pip install package-name
```

### Performance Issues

**High CPU/Memory usage:**
- Reduce `--max-concurrent` to 1-2
- Process smaller images
- Close other applications
- Check Activity Monitor for resource usage

**Disk space issues:**
```bash
# Check available space
df -h

# Clean up if needed
rm -rf ~/.cache/pip
pip cache purge
```

## 🔍 Debugging & Diagnostics

### Get More Information

**Verbose output:**
```bash
# Add debug information (not built-in, but you can check logs)
python photo_editor.py process image.jpg
```

**Check what's running:**
```bash
# Monitor system resources
top -o cpu

# Check network activity
netstat -an | grep 443
```

### Test Individual Components

**Test Anthropic API:**
```bash
# Simple test
python3 -c "
from anthropic import Anthropic
import os
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
print('Anthropic API working!')
"
```

**Test remove.bg API:**
```bash
# Test with curl
curl -X POST https://api.remove.bg/v1.0/removebg \
  -H "X-Api-Key: YOUR_API_KEY" \
  -F "image_url=https://example.com/test.jpg"
```

**Test ImageMagick:**
```bash
# Create test image and process it
magick -size 100x100 canvas:red test.jpg
magick test.jpg -brightness-contrast 10x5 test-processed.jpg
ls -la test*
```

## 📊 Common Error Messages

### "Rate limit exceeded"
- **remove.bg**: You've used your monthly quota
- **Anthropic**: Too many requests per minute
- **Solution**: Wait or upgrade your plan

### "Image too large"
- **remove.bg**: Max 25MB file size
- **Solution**: Resize image first: `magick large.jpg -resize 50% smaller.jpg`

### "Unsupported format"
- **Solution**: Convert to supported format: `magick image.tiff image.jpg`

### "ModuleNotFoundError"
- **Solution**: Reinstall requirements: `pip install -r requirements.txt`

### "Permission denied"
- **Solution**: Check file permissions and virtual environment activation

## 🆘 When All Else Fails

### Reset Everything
```bash
# Nuclear option - start fresh
cd ..
rm -rf langgraph-photo-editor
# Re-download/copy project
cd langgraph-photo-editor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Recreate .env file
```

### Get Help
1. **Document the exact error message**
2. **Note what you were trying to do**
3. **Check if it works with a simple test image**
4. **Contact Pranav with specific details**

### Minimal Test Case
```bash
# Try the simplest possible case
source venv/bin/activate
python photo_editor.py --help

# If that works, try:
echo "ANTHROPIC_API_KEY=your_key" > .env
python photo_editor.py process small-test-image.jpg
```

## 📚 Additional Resources

- **[macOS Setup](MACOS_SETUP.md)** - Reinstall from scratch
- **[User Guide](USER_GUIDE.md)** - Learn proper usage
- **[FAQ](FAQ.md)** - Quick answers to common questions

---

**Remember**: When reporting issues, always include:
- Exact error message
- What command you ran
- Your macOS version
- Whether virtual environment is activated