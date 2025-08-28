# 📱 macOS Setup Guide

Complete installation guide for Doug's Mac setup. This will get the Agentic Photo Editor running on your macOS system.

## 🛠️ Prerequisites

### 1. Install Homebrew (if not already installed)

Open Terminal and run:

```bash
# Install Homebrew (package manager for macOS)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After installation, follow the instructions to add Homebrew to your PATH.

### 2. Install Python 3.8+ 

```bash
# Install Python (if you don't have a recent version)
brew install python@3.11

# Check Python version
python3 --version
# Should show Python 3.8 or higher
```

### 3. Install ImageMagick 7

```bash
# Install ImageMagick for image processing
brew install imagemagick

# Verify installation
magick --version
# Should show ImageMagick 7.x.x
```

## 📁 Project Setup

### 1. Get the Photo Editor Code

```bash
# Navigate to your preferred directory (e.g., Desktop)
cd ~/Desktop

# If you have the folder from Pranav, just copy it to your Mac
# If using git (optional):
# git clone [repository-url] langgraph-photo-editor

# Navigate to the project
cd langgraph-photo-editor
```

### 2. Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should see (venv) at the beginning of your terminal prompt
```

### 3. Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# This might take a few minutes
```

## 🔑 API Keys Setup

### 1. Get Your API Keys

You'll need two API keys:

**Anthropic API Key (Required):**
1. Go to [https://console.anthropic.com/](https://console.anthropic.com/)
2. Sign up/login
3. Go to "API Keys" section
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

**remove.bg API Key (Optional, for background removal):**
1. Go to [https://www.remove.bg/api](https://www.remove.bg/api)
2. Sign up for free account (50 free images/month)
3. Get your API key

### 2. Configure Environment Variables

Create a `.env` file in the project directory:

```bash
# Create the environment file
touch .env

# Open in TextEdit
open -a TextEdit .env
```

Add your API keys to the file:

```bash
# Required for AI image analysis
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional for background removal
REMOVE_BG_API_KEY=your_removebg_key_here
```

**Save and close the file.**

### 3. Alternative: Terminal Export (Temporary)

If you prefer, you can set environment variables in Terminal (need to do this each session):

```bash
export ANTHROPIC_API_KEY="your_key_here"
export REMOVE_BG_API_KEY="your_removebg_key_here"
```

## ✅ Test Your Installation

```bash
# Make sure virtual environment is active
source venv/bin/activate

# Test the installation
python photo_editor.py --help
```

You should see the help menu with all available commands.

### Test with a Sample Image

```bash
# Test with a sample image (replace with your image path)
python photo_editor.py process ~/Desktop/test-image.jpg
```

## 🚀 Ready to Use!

Your setup is complete! Here are the main ways to use the photo editor:

### Chat Mode (Recommended)
```bash
python photo_editor.py chat
```

### Process Single Image
```bash
python photo_editor.py process path/to/image.jpg
```

### Process Directory
```bash
python photo_editor.py batch path/to/photos/
```

## 🔧 Troubleshooting

### Virtual Environment Issues
```bash
# If you can't activate venv
cd langgraph-photo-editor
source venv/bin/activate

# Should show (venv) in your prompt
```

### ImageMagick Issues
```bash
# If magick command not found
brew reinstall imagemagick

# Check installation
which magick
magick --version
```

### Permission Issues
```bash
# If you get permission errors
sudo xcode-select --install
```

### Python/Pip Issues
```bash
# If pip install fails
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

## 📚 Next Steps

- **[User Guide](USER_GUIDE.md)** - Learn how to use the photo editor
- **[FAQ](FAQ.md)** - Common questions and answers
- **[Troubleshooting](TROUBLESHOOTING.md)** - Fix common issues

## 💡 Tips for Doug

1. **Always activate the virtual environment first**: `source venv/bin/activate`
2. **Start with chat mode**: It's the easiest way to get started
3. **Process a single image first**: Test before doing batch processing
4. **Check the FAQ**: If you run into issues, check the FAQ first

---

**Need help?** Contact Pranav or check the troubleshooting guides!