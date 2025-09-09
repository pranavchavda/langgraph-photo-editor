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
REMOVE_BG_API_KEY=your_removebg_key_here      # Background removal

# Processing settings (optional)
MAX_CONCURRENT_IMAGES=3                        # Batch concurrency
RETRY_ATTEMPTS=2                              # QC retry attempts
QUALITY_THRESHOLD=0.8                         # Minimum QC score

# ImageMagick base configuration (optional)
IMAGEMAGICK_BASE_CONFIG="-modulate 100,105,100 -unsharp 0.8x0.6 -quality 95"  # Custom base
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

**Customization:**
- Set `IMAGEMAGICK_BASE_CONFIG` environment variable to override the default base
- Batch processing can use `BATCH_IMAGEMAGICK_BASE` for consistent batch settings
- Base values derived from analyzing Darktable XMP sidecar files for professional consistency

## File I/O Patterns

**Input Formats:** JPG, JPEG, PNG, WebP
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

## Development Notes for Claude Code
- Use specialized Claude Code subagents for further coding when available
- The AppImage build process handles Python bundling automatically
- File management is cross-platform compatible
- Gemini processing works seamlessly with proper API keys

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
