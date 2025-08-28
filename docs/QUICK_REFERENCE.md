# 🚀 Quick Reference

Essential commands and tips for the Agentic Photo Editor.

## 🔥 Most Common Commands

```bash
# Setup (do once)
cd langgraph-photo-editor
source venv/bin/activate

# Chat mode (easiest!)
python photo_editor.py chat

# Single image
python photo_editor.py process image.jpg

# Batch processing
python photo_editor.py batch ./photos/

# Get help
python photo_editor.py --help
```

## 💬 Chat Mode Examples

```
Make the espresso machines brighter and more vibrant
Process ~/Desktop/coffee-photos/ but keep them natural
Trim whitespace and enhance chrome on all steel machines
Process image.jpg with darker, more professional look
Remove backgrounds and make colors more vibrant
```

## 🎨 Custom Instructions

```bash
# Bright and vibrant
CUSTOM_PROCESSING_INSTRUCTIONS="brighter, more vibrant colors" python photo_editor.py process image.jpg

# Professional e-commerce
CUSTOM_PROCESSING_INSTRUCTIONS="professional lighting, enhance chrome" python photo_editor.py process image.jpg

# Natural look
CUSTOM_PROCESSING_INSTRUCTIONS="natural colors, minimal processing" python photo_editor.py process image.jpg

# Dramatic style
CUSTOM_PROCESSING_INSTRUCTIONS="dramatic shadows, high contrast" python photo_editor.py process image.jpg
```

## 🔧 Troubleshooting Quick Fixes

```bash
# Command not found
source venv/bin/activate

# ImageMagick missing
brew install imagemagick

# Python packages missing
pip install -r requirements.txt --no-cache-dir

# API key issues
cat .env  # Check your keys are there

# Virtual environment broken
rm -rf venv && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

## 📁 File Organization

```bash
# Input formats: JPG, PNG, WebP
# Output format: Always WebP (high quality, supports transparency)

# Default output location: same directory as input with "-processed" suffix
input.jpg → input-processed.webp

# Custom output location
python photo_editor.py process input.jpg --output-dir ./processed/
```

## 🎯 Quality Scores

- **9-10**: Excellent (passes QC)
- **7-8**: Good quality 
- **5-6**: Needs improvement
- **0-4**: Poor quality
- **Auto-retry**: <9 triggers automatic retry

## 💰 Costs

- **Anthropic**: ~$0.01-0.03 per image (AI analysis)
- **remove.bg**: 50 free/month, then ~$0.20 per image
- **Total**: ~$0.01-0.23 per image

## ⚡ Performance Tips

```bash
# Slower/safer (older Macs)
python photo_editor.py batch ./photos/ --max-concurrent 1

# Faster (powerful Macs)  
python photo_editor.py batch ./photos/ --max-concurrent 5

# Skip background removal (faster + cheaper)
# Remove REMOVE_BG_API_KEY from .env file
```

## 🆘 Emergency Reset

```bash
# Nuclear option - start completely fresh
cd ..
rm -rf langgraph-photo-editor
# Re-copy project from Pranav
cd langgraph-photo-editor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Recreate .env with your API keys
```

## 📚 Documentation

- **Setup**: [macOS Setup Guide](MACOS_SETUP.md)
- **Learning**: [User Guide](USER_GUIDE.md)  
- **Problems**: [FAQ](FAQ.md) & [Troubleshooting](TROUBLESHOOTING.md)
- **Advanced**: [Advanced Usage](ADVANCED.md)

---

## 🎯 Doug's Quick Start

1. **Setup once**: Follow [macOS Setup Guide](MACOS_SETUP.md)
2. **Daily use**: `source venv/bin/activate` then `python photo_editor.py chat`
3. **When stuck**: Check [FAQ](FAQ.md)
4. **For help**: Contact Pranav

**Remember**: Always activate virtual environment first!