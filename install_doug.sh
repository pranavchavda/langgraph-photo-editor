#!/bin/bash
# DOUG'S PHOTO EDITOR - REMOTE INSTALLER
# This script can be run from anywhere and will set everything up

set -e  # Exit on any error

echo "🚀 DOUG'S PHOTO EDITOR - ONE-CLICK INSTALLER"
echo "============================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REPO_URL="https://github.com/pranavchavda/langgraph-photo-editor.git"
INSTALL_DIR="$HOME/DougPhotoEditor"

echo "📍 This will install to: $INSTALL_DIR"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}Installing git...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install git
        else
            echo -e "${RED}Please install git first: brew install git${NC}"
            exit 1
        fi
    else
        sudo apt-get update && sudo apt-get install -y git
    fi
fi

# Clone or update the repository
if [ -d "$INSTALL_DIR" ]; then
    echo "📂 Directory exists. Updating to latest version..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "📥 Downloading Doug's Photo Editor..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo ""
echo -e "${GREEN}✅ Downloaded successfully!${NC}"
echo ""

# Run the main setup script
echo "🔧 Starting Docker setup..."
chmod +x doug_docker_setup.sh
./doug_docker_setup.sh

echo ""
echo -e "${GREEN}🎉 Installation complete!${NC}"
echo ""
echo "📁 Installation location: $INSTALL_DIR"
echo ""
echo "To use the photo editor:"
echo "  1. cd $INSTALL_DIR"
echo "  2. ./doug_web.sh"
echo ""
echo "The web interface will open at http://localhost:8501"