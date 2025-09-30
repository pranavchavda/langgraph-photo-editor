# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2025-09-18

### 🐳 Docker Deployment & One-Click Installation

#### Added
- **One-click installer** - Remote installation via `curl | bash`
- **Docker containerization** - Complete Docker setup with multi-stage builds
- **Memory optimization** - 16GB limit, 4GB shared memory for large images
- **Helper scripts** - Simple commands for daily use (`doug_web.sh`, `doug_stop.sh`)
- **UV package manager support** - Alternative Dockerfile with UV for faster builds
- **Installation documentation** - Comprehensive INSTALL.md guide

#### Fixed
- **Container crashes (exit code 137)** - Resolved OOM errors with proper resource limits
- **Missing OpenCV dependencies** - Added libgl1 and related libraries for rembg
- **Logo display in Docker** - Fixed .dockerignore to include logo.jpeg
- **F-string syntax error** - Fixed backslash in f-string in agents_enhanced.py
- **Model download timeouts** - Removed pre-download from build, downloads on first use

#### Changed
- **Resource limits** - Increased from 8GB to 16GB memory limit
- **Docker Compose configuration** - Created doug-specific config with optimizations
- **Installation process** - Simplified to single command execution

#### Files Added
- `Dockerfile` - Production container with pip
- `Dockerfile.uv` - Alternative with UV package manager
- `docker-compose.yml` - Standard Docker Compose configuration
- `docker-compose.doug.yml` - Memory-optimized configuration for Doug
- `install_doug.sh` - Remote installer script
- `doug_docker_setup.sh` - Local Docker setup with automatic installation
- `doug_web.sh` - Start web interface
- `doug_stop.sh` - Stop containers
- `doug_batch.sh` - Batch processing helper
- `doug_single.sh` - Single image processing
- `doug_chat.sh` - Interactive chat mode
- `.dockerignore` - Optimized build context
- `.env.example` - Template for environment variables
- `INSTALL.md` - User-friendly installation guide
- `DOUG_README.md` - Simplified guide specifically for Doug

## [1.1.0] - 2025-09-04

### Lens Correction & Streamlit Fixes

#### Fixed
- **Severe image cropping during lens correction** - Changed from `-distort` to `+distort`
- **Vignetting issues** - Removed incorrect `-vignette` command
- **localStorage persistence** - Implemented with streamlit-local-storage package
- **ImageMagick on Streamlit Cloud** - Added packages.txt for system-level installation

#### Added
- **EXIF lens detection** - Properly detects Sony FE lenses
- **Custom lens profiles** - Support for Sony FE 24-70mm, 90mm Macro, 50mm, 70-200mm

## [1.0.0] - 2025-08-29

### Initial Enhanced Workflow

#### Features
- **5-Agent Pipeline** - Claude analysis → Gemini editing → ImageMagick → Background removal → QC
- **Gemini 2.5 Flash** - AI-powered natural language image editing
- **Quality presets** - Maximum, Ultra, High, Balanced, Web options
- **Format preservation** - Maintains AVIF, WebP, PNG, JPEG formats
- **Batch processing** - Concurrent processing with ZIP download
- **Web interface** - Streamlit app with localStorage for API keys