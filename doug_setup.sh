#!/bin/bash
# One-click setup script for Doug - Uses UV for ultra-fast Python setup
# This script is idiot-proof and will work on Mac/Linux

set -e  # Exit on any error

echo "🚀 LangGraph Photo Editor - One-Click Setup for Doug"
echo "=================================================="
echo ""

# Color codes for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
fi

echo "🖥️  Detected OS: $OS"
echo ""

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV (super-fast Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo ""
fi

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo -e "${YELLOW}⚠️  ImageMagick not found. Installing...${NC}"
    if [[ "$OS" == "mac" ]]; then
        if command -v brew &> /dev/null; then
            brew install imagemagick
        else
            echo -e "${RED}❌ Homebrew not found. Please install from https://brew.sh${NC}"
            echo "Then run: brew install imagemagick"
            exit 1
        fi
    elif [[ "$OS" == "linux" ]]; then
        sudo apt-get update && sudo apt-get install -y imagemagick
    fi
    echo ""
fi

# Create virtual environment with UV
echo "🐍 Setting up Python environment with UV..."
uv venv --python 3.11
echo ""

# Install all dependencies with UV (super fast!)
echo "📚 Installing all Python packages (this will be FAST with UV)..."
uv pip install -r requirements.txt
echo ""

# Download rembg models in advance
echo "🤖 Pre-downloading AI models for background removal..."
source .venv/bin/activate
python -c "
import os
os.environ['U2NET_HOME'] = os.path.expanduser('~/.u2net')
from rembg import remove, new_session
print('Downloading bria-rmbg model (best for products)...')
session = new_session('bria-rmbg')
print('✅ Model downloaded successfully!')
"
deactivate
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file for API keys..."
    cat > .env << 'EOF'
# API Keys (Required)
ANTHROPIC_API_KEY=your_claude_key_here
GEMINI_API_KEY=your_gemini_key_here

# Optional: Remove.bg API (if you have it)
# REMOVE_BG_API_KEY=your_removebg_key_here

# Background Removal Settings
BACKGROUND_REMOVAL_METHOD=rembg  # Using local AI, no API needed
REMBG_MODEL=bria-rmbg           # Best model for product photos
REMBG_ALPHA_MATTING=false       # Set to true for smoother edges (slower)

# Quality Settings
QUALITY_PRESET=ultra             # ultra = best quality/size balance
REMOVEBG_SIZE=full              # Maximum resolution

# Processing Settings
MAX_CONCURRENT_IMAGES=3         # Process 3 images at once
RETRY_ATTEMPTS=2                # Retry failed images twice
EOF
    echo -e "${YELLOW}⚠️  Please edit .env file and add your API keys!${NC}"
    echo ""
fi

# Create run scripts
echo "🔧 Creating easy run scripts..."

# Streamlit web app runner
cat > run_web.sh << 'EOF'
#!/bin/bash
source .venv/bin/activate
streamlit run streamlit_app.py
EOF
chmod +x run_web.sh

# CLI runner
cat > run_cli.sh << 'EOF'
#!/bin/bash
source .venv/bin/activate
python photo_editor.py "$@"
EOF
chmod +x run_cli.sh

# Batch processor
cat > run_batch.sh << 'EOF'
#!/bin/bash
if [ $# -lt 1 ]; then
    echo "Usage: ./run_batch.sh <input-directory> [output-directory]"
    echo "Example: ./run_batch.sh ./photos ./processed"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="${2:-./output}"

source .venv/bin/activate
python photo_editor.py batch "$INPUT_DIR" --output-dir "$OUTPUT_DIR" --max-concurrent 3
EOF
chmod +x run_batch.sh

echo ""
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo ""
echo "📖 How to use:"
echo ""
echo "  1. Edit .env file and add your API keys:"
echo "     ${YELLOW}nano .env${NC}"
echo ""
echo "  2. Run the web interface (easiest):"
echo "     ${GREEN}./run_web.sh${NC}"
echo ""
echo "  3. Or use command line:"
echo "     ${GREEN}./run_cli.sh chat${NC}                    # Interactive mode"
echo "     ${GREEN}./run_cli.sh process image.jpg${NC}      # Single image"
echo "     ${GREEN}./run_batch.sh ./photos${NC}             # Batch process folder"
echo ""
echo "🎉 That's it! No Docker needed, everything runs locally with UV!"