# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered agentic photo editor that combines Claude Sonnet 4 vision analysis with Gemini 2.5 Flash AI image editing to optimize product photography for e-commerce. The system uses LangGraph for multi-agent workflow orchestration.

## Architecture

**Multi-Agent LangGraph Workflow:**
- **Enhanced Analysis Agent** (Claude Sonnet 4) - Determines optimal processing strategy
- **Gemini Edit Agent** (Gemini 2.5 Flash) - Performs AI image editing with natural language
- **Background Agent** (remove.bg API) - Professional background removal  
- **ImageMagick Agent** - Parameter-based optimizations as fallback
- **QC Agent** (Claude) - Quality validation and retry logic

**Core Technologies:**
- LangGraph with functional API (`@task` decorators, `@entrypoint` orchestrator)
- Claude Sonnet 4 for vision analysis and quality control
- Gemini 2.5 Flash for AI-powered image editing
- ImageMagick for traditional photo optimization
- Rich terminal UI for progress tracking

## Streamlit Web Application

### Deployment on Streamlit Cloud
The app is designed to be deployed on Streamlit Cloud as an alternative to the desktop Electron app:

**URL**: Deploy to `https://[your-app-name].streamlit.app`

**Features:**
- Single-page app with mode toggle (Single Image / Batch Processing)
- Browser-based localStorage for API key persistence
- No installation required for users
- Cross-platform compatibility
- Batch processing with ZIP download

### Running Locally
```bash
streamlit run streamlit_app.py
```

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Main entry point - interactive chat mode
python photo_editor.py chat

# Process single image
python photo_editor.py process image.jpg --instructions "enhance chrome and make more vibrant"

# Batch processing
python photo_editor.py batch ./input-dir/ --output-dir ./output-dir/ --max-concurrent 3

# Configuration test
python photo_editor.py test
```

### Testing and Development
```bash
# Run enhanced workflow tests
python test_enhanced.py

# Debug specific components
python debug_analysis.py    # Test analysis agent
python debug_strategy.py    # Test strategy selection
python debug_workflow.py    # Test full workflow

# Other test files
python test_chat_gemini.py  # Test Gemini integration
python test_trim.py         # Test image processing utilities
```

## Code Structure

**Main Application Files:**
- `photo_editor.py` - Main entry point, delegates to enhanced CLI
- `src/cli_enhanced.py` - Enhanced CLI with Gemini 2.5 Flash support
- `src/workflow_enhanced.py` - 5-agent LangGraph workflow orchestration
- `src/agents_enhanced.py` - Enhanced agent implementations

**Quality & Format Management:**
- `src/quality_config.py` - Quality presets and format-specific settings
- `src/format_preservation.py` - Format conversion and preservation
- `src/background_recovery.py` - Interactive background recovery tools

**Legacy Components:**
- `src/cli.py` - Original CLI implementation
- `src/workflow.py` - Original 4-agent workflow
- `src/agents.py` - Original agent implementations

**Key Architectural Patterns:**
- All agents use async/await with proper error handling
- State management through LangGraph TypedDict schemas
- Progress tracking via StreamWriter for real-time updates
- Quality-based retry logic with parameter refinement
- Concurrent batch processing with configurable limits

## Environment Variables (Required)

```bash
# Core AI APIs
ANTHROPIC_API_KEY=your_claude_key_here        # Claude Sonnet 4
GEMINI_API_KEY=your_gemini_key_here           # Gemini 2.5 Flash

# Optional services
REMOVE_BG_API_KEY=your_removebg_key_here      # Background removal (remove.bg API)

# Background removal configuration
BACKGROUND_REMOVAL_METHOD=auto                # Options: "auto", "remove.bg", "rembg"
                                              # auto: Use remove.bg if API key exists, else rembg
                                              # remove.bg: Use remove.bg API (requires API key)
                                              # rembg: Use local ML model (free, no API needed)

REMBG_MODEL=bria-rmbg                        # rembg model options:
                                              # - bria-rmbg: Best for product photos
                                              # - u2net: General purpose, good quality
                                              # - u2netp: Lightweight/faster version
                                              # - u2net_human_seg: Optimized for people
                                              # - u2net_cloth_seg: For clothing items
                                              # - silueta: Compact model
                                              # - isnet-general-use: High accuracy
                                              # - isnet-anime: For anime/illustrations
                                              # - birefnet-general: Latest architecture
                                              # - birefnet-portrait: For human portraits

REMBG_ALPHA_MATTING=false                    # Enable alpha matting for smoother edges (slower)

# Processing settings (optional)
MAX_CONCURRENT_IMAGES=3                        # Batch concurrency
RETRY_ATTEMPTS=2                              # QC retry attempts
QUALITY_THRESHOLD=0.8                         # Minimum QC score

# Quality Settings (NEW - Important!)
QUALITY_PRESET=maximum                        # Options: maximum, ultra, high, balanced, web
                                              # maximum: Lossless, best quality, larger files
                                              # ultra: Near-lossless, excellent quality (default)
                                              # high: Very good quality, smaller files
                                              # balanced: Good quality, optimized size
                                              # web: Optimized for web, smallest files

REMOVEBG_SIZE=full                           # remove.bg API size parameter
                                              # Options: preview, auto, small, medium, hd, 4k, full, 50MP
                                              # full: Maximum resolution (best quality)
                                              # 4k: Up to 10MP (good balance)
                                              # auto: Let API choose based on credits

# ImageMagick base configuration (optional) - Two approaches:
# 1. Simple: Full command override
IMAGEMAGICK_BASE_CONFIG="-modulate 100,105,100 -unsharp 0.8x0.6 -quality 100"  # Custom base

# 2. Granular: Individual parameter control
IMAGEMAGICK_GAMMA=1.0                         # Gamma correction (0.8-1.2)
IMAGEMAGICK_BRIGHTNESS=0                      # Brightness (-10 to +10)
IMAGEMAGICK_CONTRAST=2                        # Contrast (-10 to +10)
IMAGEMAGICK_SATURATION=108                    # Saturation (90-120)
IMAGEMAGICK_QUALITY=100                       # Output quality (1-100, default 100)
IMAGEMAGICK_VIBRANCE=0                        # Vibrance (-100 to +100)
IMAGEMAGICK_HUE_SHIFT=0                       # Hue rotation (-180 to +180)
IMAGEMAGICK_SHARPNESS="1.0x0.5"               # Unsharp mask parameters
IMAGEMAGICK_HIGHLIGHTS=-5                     # Highlight recovery (-20 to 0)
IMAGEMAGICK_SHADOWS=3                         # Shadow lifting (0 to 20)
IMAGEMAGICK_DENOISE=0                         # Noise reduction (0-100)
IMAGEMAGICK_BLUR=0                            # Gaussian blur (0-10)
IMAGEMAGICK_TRIM=false                        # Auto-trim whitespace
IMAGEMAGICK_TRIM_FUZZ=5                       # Trim tolerance (%)
IMAGEMAGICK_AUTO_LEVEL=false                  # Auto-level (careful!)
IMAGEMAGICK_AUTO_GAMMA=false                  # Auto-gamma
IMAGEMAGICK_NORMALIZE=false                   # Normalize (often overexposes)
IMAGEMAGICK_RESIZE=""                         # Resize (e.g., "1920x1080")
IMAGEMAGICK_COLORSPACE=""                     # Colorspace (e.g., "sRGB")
IMAGEMAGICK_QUALITY=95                        # Output quality (1-100)
```

## ImageMagick Base Configuration System

**Purpose**: Provides consistent baseline ImageMagick optimizations inspired by Darktable professional presets

**Default Base Configuration (Darktable-inspired):**
- Gamma: 1.0 (neutral, matching Darktable)
- Brightness: 0 (no adjustment)
- Contrast: 2 (slight boost from RGB levels)
- Saturation: 108 (moderate boost)
- Sharpness: 1.0x0.5 unsharp mask (Darktable sharpen)
- Highlights: -5 (slight recovery)
- Shadows: +3 (slight lift from RGB levels ~0.613 midpoint)
- Quality: 95

**How it Works:**
1. Analysis agent starts with the Darktable-inspired base configuration
2. Claude suggests adjustments as deltas (e.g., gamma_delta: +0.02)
3. Deltas are applied to create the final command
4. Ensures consistency across generations while allowing flexibility

**Customization Options:**

1. **Simple Override**: Set `IMAGEMAGICK_BASE_CONFIG` for a complete command
   ```bash
   export IMAGEMAGICK_BASE_CONFIG="-gamma 1.1 -modulate 105,110,100 -quality 95"
   ```

2. **Granular Control**: Set individual parameters
   ```bash
   export IMAGEMAGICK_GAMMA=1.05
   export IMAGEMAGICK_SATURATION=115
   export IMAGEMAGICK_TRIM=true
   ```

3. **Use Presets**: Source the config examples
   ```bash
   source imagemagick_config_examples.sh && chrome_metal
   python photo_editor.py process image.jpg
   ```

**Available Presets:**
- `natural_product` - Subtle enhancement for natural look
- `vibrant_ecommerce` - Punchy colors for e-commerce
- `chrome_metal` - Optimized for reflective surfaces
- `soft_matte` - Gentle processing for matte products
- `high_key` - Bright, white background optimization

**Advanced Features:**
- **Vibrance**: Affects less saturated colors more than saturation
- **Color Balance**: Per-channel RGB adjustments
- **CLAHE**: Contrast Limited Adaptive Histogram Equalization
- **Trim with Fuzz**: Intelligent whitespace removal
- **Colorspace Conversion**: Work in different color spaces
- **Per-Channel Operations**: Apply different effects to R/G/B channels

## File I/O Patterns

**Input Formats:** JPG, JPEG, PNG, WebP, AVIF
**Output Format:** Always WebP (preserves transparency from background removal)

**Directory Structure:**
- Input images can be single files or directories
- Output preserves original filenames with quality indicators
- Failed QC results get quality suffix (e.g. `-q6.webp`, `-qfail.webp`)
- Intermediate files are cleaned up automatically

## Development Notes

**LangGraph Functional API Usage:**
- Use `@task` decorators for individual agents
- Use `@entrypoint` for workflow orchestration with checkpointing
- StreamWriter provides real-time progress updates to CLI
- InMemorySaver handles state persistence across retries

**Agent Communication:**
- Agents communicate through structured state objects
- Each agent updates specific state fields and logs progress
- QC agent provides feedback for retry parameter refinement
- Error handling with custom AgentError exceptions

**Testing Strategy:**
- Use test files in root directory for component testing
- Test images should be placed in `/tmp/` for consistency
- Each agent can be tested independently via debug scripts
- Full workflow testing through `test_enhanced.py`

## Lens Correction System

**Supported Lenses (Doug's Kit):**
- Sony FE 24-70mm F2.8 GM (zoom lens with focal-length-specific corrections)
- Sony FE 90mm F2.8 Macro G OSS
- Sony FE 50mm F1.4 GM  
- Sony FE 70-200mm F2.8 GM OSS (zoom lens with focal-length-specific corrections)

**Implementation:**
- Primary: ImageMagick with custom profiles using `+distort Barrel` for distortion correction
- Fallback: Gemini AI for lens issues when ImageMagick unavailable
- lensfunpy disabled: Too aggressive for JPEGs, causes severe cropping

**Key Files:**
- `src/lens_corrections_advanced.py` - Main lens correction logic with EXIF detection
- `src/lens_corrections.py` - Original implementation with Doug's lens profiles
- `packages.txt` - Ensures ImageMagick installation on Streamlit Cloud

## Dependencies

**System Requirements:**
- ImageMagick (installed via packages.txt on Streamlit Cloud)
- Python 3.9+

**Key Python Packages:**
- `langgraph>=0.2.0` - Multi-agent workflow orchestration
- `langchain-anthropic>=0.2.0` - Claude integration
- `anthropic>=0.34.0` - Direct Claude API access
- `google-generativeai>=0.8.0` - Gemini 2.5 Flash image editing
- `click>=8.0.0` - CLI framework
- `rich>=13.0.0` - Terminal UI and progress display
- `pillow>=10.0.0` - Image format handling

## Recent Improvements (Latest)

**Quality Preservation System (November 2024):**
- ✅ **Comprehensive quality management**: New quality_config.py module with presets (maximum, ultra, high, balanced, web)
- ✅ **Fixed remove.bg quality loss**: Now uses 'full' or '4k' size based on quality preset
- ✅ **Lossless WebP for transparency**: Automatically uses lossless compression for images with transparency
- ✅ **No more -flatten on transparent images**: ImageMagick preserves transparency properly
- ✅ **Claude API 5MB limit handling**: Compresses images for analysis only, full quality for processing
- ✅ **Format preservation**: Maximum preset converts back to original format (AVIF support)
- ✅ **Default quality increased**: Changed from 95 to 100 for maximum quality
- ✅ **File size logging**: Comprehensive logging at each pipeline stage for debugging

## Recent Improvements (Latest)

**Lens Correction & Deployment Fixes (September 4, 2025):**
- ✅ **Fixed severe image cropping during lens correction**: lensfunpy was cropping 1/3 of image due to aggressive geometry distortion
- ✅ **ImageMagick lens correction improvements**: Changed from `-distort` to `+distort` to preserve full canvas
- ✅ **Fixed vignetting**: Removed `-vignette` command that was adding instead of removing vignettes  
- ✅ **localStorage persistence working**: Implemented with streamlit-local-storage package, keys persist across sessions
- ✅ **ImageMagick on Streamlit Cloud**: Added packages.txt for system-level ImageMagick installation
- ✅ **Better error logging**: Clear messages when lens corrections can't be applied
- ✅ **EXIF lens detection working**: Properly detects all 4 Sony FE lenses from Doug's kit
- ✅ **Lens correction profiles**: Custom profiles for Sony FE 24-70mm, 90mm Macro, 50mm, 70-200mm

**Streamlit Web App & Deployment Fixes (September 3, 2025):**
- ✅ **Created Streamlit web interface**: Full-featured web app for Doug, avoiding macOS compatibility issues
- ✅ **Single-page app with batch mode**: Toggle between single image and batch processing modes
- ✅ **localStorage API key persistence**: Keys saved in browser, persist across sessions
- ✅ **Fixed Pregel workflow invocation**: Handles both function and Pregel graph invocations
- ✅ **ImageMagick graceful degradation**: Works without ImageMagick, falls back to Gemini AI
- ✅ **Fixed type error in ImageMagick agent**: Returns string path instead of dict when unavailable
- ✅ **Batch processing with ZIP download**: Process multiple images, download all as ZIP
- ✅ **Concurrent processing control**: 1-5 concurrent workers for batch processing

**Previous Improvements (August 29, 2025):**
- ✅ **Fixed file management**: Resolved path mismatch between temp directory and Pictures folder
- ✅ **Enhanced debug logging**: Added comprehensive file movement tracking in CLI
- ✅ **Fixed Electron scandir errors**: Proper handling of file vs directory paths
- ✅ **Optimized Gemini workflow**: Disabled ImageMagick fallback when Gemini is chosen
- ✅ **Cross-platform compatibility**: Dynamic path resolution for Linux/Mac/Windows
- ✅ **API quota handling**: Enhanced error handling for rate limits and processing failures

**Strategy Options:**
- `"imagemagick"` - Traditional parameter-based optimization
- `"gemini"` - AI-powered natural language image editing
- `"both"` - Hybrid approach using both technologies

**File Locations:**
- **Linux/Mac**: `~/Pictures/Agentic Photo Editor/`
- **Windows**: `C:\Users\[username]\Pictures\Agentic Photo Editor\`
- **Fallback**: `~/Documents/Agentic Photo Editor/` if Pictures doesn't exist

## Electron AppImage Distribution

**Build Process:**
```bash
cd electron/
npm run electron:build
```

**Output:** `dist-electron/LangGraph Photo Editor-[version].AppImage`

**Key Features:**
- Self-contained Python environment bundling
- Cross-platform file management
- Real-time processing updates via IPC
- Automatic API key detection from environment

## Quality & Compression Notes

**Important**: File size reduction ≠ quality loss. WebP is extremely efficient:
- **PNG with transparency → WebP**: Often 70-80% smaller with no visible quality loss
- **Large transparent areas**: Compress to almost nothing in WebP
- **Product photos**: Clean edges and uniform backgrounds compress very well

**Quality Presets**:
- **maximum**: Lossless WebP, preserves original format, largest files (~5-6 MB)
- **ultra**: Quality 98, lossy but excellent quality (~1.5-2 MB)
- **high**: Quality 95, very good for e-commerce (~1-1.5 MB)

**Claude API Limits**:
- Images over 5MB are automatically compressed for Claude analysis only
- Full quality image is used for actual processing
- Resolution is maintained during Claude compression

## Development Notes for Claude Code
- Use specialized Claude Code subagents for further coding when available
- The AppImage build process handles Python bundling automatically
- File management is cross-platform compatible
- Gemini processing works seamlessly with proper API keys
- Quality settings are centralized in quality_config.py
- Always check file size logs to diagnose quality issues

## GPT5-Suggested Improvements (In Development - gpt5-improvements branch)

### New Dust & Scratch Repair Pipeline
**Problem Solved**: Explicit defect detection and repair instead of hoping AI enhancement removes them

**New Agents**:
- **Defect Detection Agent** (`src/defect_detection_agent.py`): Uses OpenCV morphological operations to find dust/scratches
- **G'MIC Repair Agent** (`src/gmic_repair_agent.py`): Applies specialized despeckle/inpaint filters
- **OpenCV Inpainting Agent** (`src/opencv_inpaint_agent.py`): Mask-guided defect removal using Telea/NS methods

### Enhanced Batch Consistency System
**Problem Solved**: Deterministic consistency instead of probabilistic AI variance

**New Agents**:
- **Darktable Style Agent** (`src/darktable_agent.py`): Apply fixed "house styles" for consistent grading
- **Libvips Export Agent** (`src/vips_export_agent.py`): 5-10x faster export with consistent parameters

### Updated Workflow Order
1. Analysis → 2. Defect Detection → 3. Repair (G'MIC/OpenCV) → 4. Darktable Normalize → 5. Lens Correction → 
6. Enhancement (ImageMagick/Gemini) → 7. Background → 8. Targeted Enhancement → 9. Vips Export → 10. QC

### Configuration Options
- `USE_GMIC_REPAIR`: Enable automatic dust/scratch repair
- `USE_DARKTABLE_STYLE`: Apply consistent house style
- `USE_VIPS_EXPORT`: Use fast libvips export
- `DEFECT_SENSITIVITY`: Adjust detection threshold (0-100)

### Dependencies
```bash
# System packages
sudo apt-get install gmic darktable libvips-tools

# Python packages
pip install pyvips opencv-python
```

### Performance Improvements
- **Repair**: G'MIC is 3x faster than asking Gemini to remove dust
- **Export**: libvips is 5-10x faster than ImageMagick for resize/export
- **Consistency**: Darktable styles are 100% deterministic vs AI variance 
