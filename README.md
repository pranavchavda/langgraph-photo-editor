# 🤖 Agentic Photo Editor

A desktop application that transforms your photos with AI-powered intelligent editing using a 5-agent pipeline powered by **Claude Sonnet 4** and **Gemini 2.5 Flash**.

![Build Status](https://github.com/pranavchavda/langgraph-photo-editor/workflows/Build%20Test/badge.svg)

## ✨ Features

- **🔍 5-Agent AI Pipeline**: Claude analysis → Gemini editing → ImageMagick → Background removal → Quality control
- **🖥️ Cross-Platform Desktop**: Native apps for macOS, Windows, and Linux with beautiful UI
- **🧙‍♂️ Setup Wizard**: First-run guided setup for non-technical users
- **🎨 Drag & Drop Interface**: Professional file handling with real-time progress tracking
- **📊 Quality Control**: Automated validation with retry logic and quality scoring
- **⚡ Batch Processing**: Concurrent processing with configurable limits
- **🎯 Custom Instructions**: Natural language editing commands

## 🚀 Quick Start

### 📥 Download Installers (Recommended)

**For non-technical users - just download and install:**

Visit the [**Releases**](../../releases) page and download the installer for your platform:

- 🍎 **macOS**: `Agentic Photo Editor-x.x.x.dmg` (drag to Applications)
- 🪟 **Windows**: `Agentic Photo Editor Setup x.x.x.exe` (run installer)  
- 🐧 **Linux**: `Agentic Photo Editor-x.x.x.AppImage` (make executable and run)

**What you get:**
- 🎨 Professional drag-and-drop interface
- 🧙‍♂️ First-run setup wizard for API keys
- 📊 Real-time progress tracking
- 🚀 Zero technical setup required

### 🛠️ Build from Source

**For developers:**

```bash
git clone https://github.com/pranavchavda/langgraph-photo-editor.git
cd langgraph-photo-editor

# Setup Python environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# Setup Electron desktop app
cd electron
npm install
npm run dev  # Development mode
npm run dist:all  # Build installers
```

### 💻 Command Line Interface

```bash
# Interactive chat mode (natural language)
python photo_editor.py chat

# Process single image
python photo_editor.py process image.jpg --instructions "enhance chrome and make more vibrant"

# Batch process directory  
python photo_editor.py batch ./product-photos/
```

## 🎯 How It Works

### The 5-Agent Workflow

1. **🔍 Analysis Agent** (Claude Sonnet 4) - Analyzes image and determines optimal processing strategy
2. **🤖 Gemini Edit Agent** (Gemini 2.5 Flash) - Performs AI-powered image editing with natural language  
3. **⚡ ImageMagick Agent** - Traditional photo optimizations as fallback
4. **🎨 Background Agent** - Professional background removal when needed
5. **✅ Quality Control Agent** (Claude) - Validates results and triggers retries

### Processing Strategies

**Gemini Strategy** 🤖 - For complex edits requiring AI understanding:
- Chrome/metal surface enhancement with natural reflections
- Artistic color adjustments and vibrance improvements  
- Complex lighting corrections and shadow management

**ImageMagick Strategy** ⚡ - For simple parameter adjustments:
- Basic brightness, contrast, saturation adjustments
- Simple gamma corrections and color cast removal

## 🔧 Setup & Configuration

### API Keys Required

The app needs these API keys (configured through the setup wizard):

- **🧠 Claude (Anthropic)**: Get from [console.anthropic.com](https://console.anthropic.com/)
- **✨ Gemini**: Get from [makersuite.google.com](https://makersuite.google.com/app/apikey)  
- **🎨 Remove.bg** (optional): Get from [remove.bg/api](https://www.remove.bg/api)

### First-Time Setup

1. **Launch the app** - Setup wizard appears automatically
2. **Enter API keys** - Real-time validation with help links
3. **Configure settings** - Quality threshold, retry attempts, etc.
4. **Start processing** - Drag & drop images to begin!

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Tailwind CSS with Electron
- **Backend**: Python with LangGraph workflow orchestration  
- **AI Services**: Claude Sonnet 4, Gemini 2.5 Flash, Remove.bg
- **Build System**: Webpack + electron-builder for cross-platform distribution
- **Deployment**: GitHub Actions automated builds for all platforms

## 🚀 Automated Builds

This repository uses GitHub Actions to automatically build installers for all platforms:

- **🏷️ Tagged Releases**: Create a git tag like `v1.0.0` to trigger release builds
- **🔄 Pull Requests**: Automatically test builds on all platforms  
- **📦 Artifacts**: Download build artifacts from GitHub Actions runs
- **🎯 Manual Triggers**: Use "Actions" tab to manually trigger builds

### Creating a Release

```bash
# Tag a new version
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions will automatically:
# 1. Build installers for macOS, Windows, Linux
# 2. Create a new GitHub release
# 3. Upload all installers as release assets
```

## 🎨 Input/Output

**Supported Formats:**
- 📥 **Input**: JPG, JPEG, PNG, WebP
- 📤 **Output**: WebP (preserves transparency from background removal)

**File Naming:**
- `original-name-enhanced.webp` - Successfully processed
- `original-name-q8.webp` - Quality score of 8/10
- `original-name-qfail.webp` - Failed quality check

## 📊 Performance

- **Processing Time**: ~30-90 seconds per image (depending on complexity)
- **Batch Processing**: 3 concurrent images (configurable)
- **Quality Pass Rate**: 85%+ pass on first attempt, 95%+ after retries
- **File Size**: ~108MB installed app

## 🔮 Future Enhancements

- **🌐 Web Interface**: FastAPI backend with React frontend
- **🎨 Style Presets**: Custom presets for different product categories  
- **🛒 E-commerce Integration**: Direct integration with Shopify, etc.
- **📈 Analytics Dashboard**: Processing metrics and quality reporting

## 📚 Documentation

- **[🎯 User Guide](electron/USER_GUIDE.md)**: Complete end-user documentation with installation guides
- **[🔧 Build Guide](electron/BUILD_GUIDE.md)**: Technical documentation for developers and building  
- **[💻 Development Guide](CLAUDE.md)**: Project setup and development workflow

## 🤝 Contributing

This project follows modern LangGraph patterns with functional API decorators. See the development documentation for setup instructions.

## 📄 License

MIT License - see LICENSE file for details.

---

**🤖 Built with Claude Code and modern AI workflows**  
**⭐ Star this repo if you find it useful!**