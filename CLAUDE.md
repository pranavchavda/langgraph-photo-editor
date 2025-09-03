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
```

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

## Dependencies

**System Requirements:**
- ImageMagick (must be installed and accessible via command line)
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
