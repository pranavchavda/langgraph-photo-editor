# 🤖 Agentic Photo Editor

An AI-powered photo editor that transforms your photos with intelligent editing using a 5-agent pipeline powered by **Claude Sonnet 4** and **Gemini 2.5 Flash**. Available as both a **web application** and desktop app.

![Build Status](https://github.com/pranavchavda/langgraph-photo-editor/workflows/Build%20Test/badge.svg)

## ✨ Features

- **🔍 5-Agent AI Pipeline**: Claude analysis → Gemini editing → ImageMagick → Background removal → Quality control
- **🌐 Web Application**: Browser-based interface with no installation required
- **🖥️ Cross-Platform Desktop**: Alternative native apps for macOS, Windows, and Linux
- **🔑 API Key Persistence**: Secure browser storage for seamless sessions
- **📊 Quality Control**: Automated validation with retry logic and quality scoring
- **⚡ Batch Processing**: Concurrent processing with ZIP download for results
- **🎯 Custom Instructions**: Natural language editing commands
- **📱 Mobile-Friendly**: Responsive design works on tablets and mobile devices

## 🚀 Quick Start

### 🌐 Web Application (Recommended)

**Try it instantly in your browser:**

**🔗 [Launch Web App](https://your-app-name.streamlit.app)** - No installation required!

**Features:**
- 🚀 **Instant access** - Works in any modern browser
- 🔑 **API key persistence** - Keys saved securely in browser storage
- 📱 **Mobile-friendly** - Responsive design for all devices
- 📦 **Batch processing** - Upload multiple images, download as ZIP
- 🌍 **Cross-platform** - Windows, macOS, Linux, mobile

### 🖥️ Desktop Application (Alternative)

**For users who prefer native apps:**

Visit the [**Releases**](../../releases) page and download the installer for your platform:

- 🍎 **macOS**: `Agentic Photo Editor-x.x.x.dmg` (drag to Applications)
- 🪟 **Windows**: `Agentic Photo Editor Setup x.x.x.exe` (run installer)  
- 🐧 **Linux**: `Agentic Photo Editor-x.x.x.AppImage` (make executable and run)

### 🛠️ Run Locally

**For developers:**

```bash
git clone https://github.com/pranavchavda/langgraph-photo-editor.git
cd langgraph-photo-editor

# Setup Python environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Run web application locally
streamlit run streamlit_app.py

# OR build desktop app
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

The app needs these API keys:

- **🧠 Claude (Anthropic)**: Get from [console.anthropic.com](https://console.anthropic.com/)
- **✨ Gemini**: Get from [makersuite.google.com](https://makersuite.google.com/app/apikey)  
- **🎨 Remove.bg** (optional): Get from [remove.bg/api](https://www.remove.bg/api)

### First-Time Setup

**Web App:**
1. **Open the web app** - [Launch here](https://your-app-name.streamlit.app)
2. **Enter API keys** - Stored securely in your browser
3. **Upload images** - Single image or batch mode
4. **Download results** - Individual files or ZIP for batches

**Desktop App:**
1. **Launch the app** - Setup wizard appears automatically
2. **Enter API keys** - Real-time validation with help links
3. **Configure settings** - Quality threshold, retry attempts, etc.
4. **Start processing** - Drag & drop images to begin!

## 🏗️ Architecture

### Multi-Agent LangGraph Workflow
- **Enhanced Analysis Agent** (Claude Sonnet 4) - Determines optimal processing strategy
- **Gemini Edit Agent** (Gemini 2.5 Flash) - Performs AI image editing with natural language
- **Background Agent** (remove.bg API) - Professional background removal  
- **ImageMagick Agent** - Parameter-based optimizations as fallback
- **QC Agent** (Claude) - Quality validation and retry logic

### Technology Stack
- **Web Frontend**: Streamlit with responsive design
- **Desktop Frontend**: React + TypeScript + Tailwind CSS with Electron
- **Backend**: Python with LangGraph workflow orchestration using `@task` decorators
- **AI Services**: Claude Sonnet 4, Gemini 2.5 Flash, Remove.bg API
- **Image Processing**: ImageMagick with Darktable-inspired presets
- **Deployment**: Streamlit Cloud for web, GitHub Actions for desktop builds

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

- **🎨 Style Presets**: Custom presets for different product categories  
- **🛒 E-commerce Integration**: Direct integration with Shopify, etc.
- **📈 Analytics Dashboard**: Processing metrics and quality reporting
- **🔧 Advanced Lens Correction**: Support for more camera/lens combinations
- **🤖 GPT-5 Improvements**: Dust & scratch repair, Darktable styles, libvips export

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