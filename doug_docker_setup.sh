#!/bin/bash
# THE ULTIMATE ONE-CLICK SETUP FOR DOUG
# This will install Docker if needed and set up everything automatically

set -e  # Exit on any error

echo "🚀 DOUG'S PHOTO EDITOR - ULTIMATE ONE-CLICK SETUP"
echo "=================================================="
echo ""
echo "This script will:"
echo "  1. Install Docker (if needed)"
echo "  2. Build the photo editor container"
echo "  3. Create all necessary folders"
echo "  4. Set up your API keys"
echo "  5. Give you simple commands to run"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
fi

echo "🖥️  Detected OS: $OS"
echo ""

# Function to install Docker and Docker Compose
install_docker() {
    echo "📦 Installing Docker and Docker Compose..."

    if [[ "$OS" == "mac" ]]; then
        # Check if Homebrew is installed
        if command -v brew &> /dev/null; then
            echo "Installing Docker using Homebrew..."
            brew install --cask docker
            echo ""
            echo "Starting Docker Desktop..."
            open -a Docker
            echo "Waiting for Docker to start (this takes about 30 seconds)..."

            # Wait for Docker to be ready
            counter=0
            while ! docker system info > /dev/null 2>&1; do
                counter=$((counter + 1))
                if [ $counter -gt 30 ]; then
                    echo -e "${YELLOW}Docker is taking longer than expected to start.${NC}"
                    echo "Please make sure Docker Desktop is running and try again."
                    exit 1
                fi
                printf "."
                sleep 2
            done
            echo ""
            echo -e "${GREEN}✅ Docker Desktop is running!${NC}"
        else
            echo "Installing Docker Desktop manually..."
            echo "Downloading Docker Desktop..."
            curl -o ~/Downloads/Docker.dmg "https://desktop.docker.com/mac/main/$(uname -m)/Docker.dmg"
            echo "Please install Docker Desktop from ~/Downloads/Docker.dmg"
            echo "After installation, come back and run this script again!"
            open ~/Downloads/
            exit 0
        fi
    elif [[ "$OS" == "linux" ]]; then
        echo "Installing Docker and Docker Compose on Linux..."

        # Install Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh

        # Install Docker Compose
        echo "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose

        # Add user to docker group
        sudo usermod -aG docker $USER

        # Start Docker service
        sudo systemctl start docker
        sudo systemctl enable docker

        rm get-docker.sh

        # Test if we need to re-login
        if ! docker ps &> /dev/null; then
            echo ""
            echo -e "${YELLOW}⚠️  Docker installed! Please run this command and then re-run the script:${NC}"
            echo ""
            echo "    newgrp docker"
            echo ""
            echo "Or log out and back in, then run this script again."
            exit 0
        fi

        echo -e "${GREEN}✅ Docker and Docker Compose installed successfully!${NC}"
    fi
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found${NC}"
    install_docker
else
    echo -e "${GREEN}✅ Docker is installed${NC}"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    # Try docker compose (newer integrated version)
    if docker compose version &> /dev/null; then
        echo -e "${GREEN}✅ Docker Compose is installed (integrated version)${NC}"
        # Create an alias for this session
        docker-compose() {
            docker compose "$@"
        }
    else
        echo -e "${YELLOW}⚠️  Docker Compose not found, installing...${NC}"
        if [[ "$OS" == "linux" ]]; then
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        elif [[ "$OS" == "mac" ]]; then
            echo "Docker Compose should be included with Docker Desktop."
            echo "Please make sure Docker Desktop is fully installed and running."
        fi
    fi
else
    echo -e "${GREEN}✅ Docker Compose is installed${NC}"
fi

# Check if Docker daemon is running
if ! docker ps &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker daemon not running. Starting...${NC}"
    if [[ "$OS" == "mac" ]]; then
        open -a Docker
        echo "Waiting for Docker to start..."
        sleep 10
    elif [[ "$OS" == "linux" ]]; then
        sudo systemctl start docker
    fi
fi

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p input output processed
echo "  ✅ Created: input/ (put your photos here)"
echo "  ✅ Created: output/ (processed photos go here)"
echo "  ✅ Created: processed/ (archive folder)"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating default configuration..."

    cat > .env << 'EOF'
# API Keys - You'll add these through the web interface
ANTHROPIC_API_KEY=
GEMINI_API_KEY=

# Settings (optimized for product photography)
BACKGROUND_REMOVAL_METHOD=rembg
REMBG_MODEL=bria-rmbg
QUALITY_PRESET=ultra
MAX_CONCURRENT_IMAGES=3
EOF

    echo -e "${GREEN}✅ Configuration file created${NC}"
    echo -e "${YELLOW}📌 You'll add your API keys through the web interface${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Build the Docker image
echo ""
echo "🔨 Building the photo editor (this takes 2-3 minutes the first time)..."

# Use the appropriate docker-compose command with Doug's optimized config
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.doug.yml build
else
    docker compose -f docker-compose.doug.yml build
fi

# Pull the pre-built image as backup
# docker pull ghcr.io/yourusername/langgraph-photo-editor:latest || true

# Create helper scripts
echo ""
echo "📝 Creating easy-to-use scripts..."

# Web UI script
cat > doug_web.sh << 'EOF'
#!/bin/bash
echo "🌐 Starting Photo Editor Web Interface..."
echo "Open your browser to: http://localhost:8501"
echo ""

# Use the appropriate docker-compose command with Doug's optimized config
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.doug.yml up photo-editor
else
    docker compose -f docker-compose.doug.yml up photo-editor
fi
EOF
chmod +x doug_web.sh

# Batch processing script
cat > doug_batch.sh << 'EOF'
#!/bin/bash
echo "🚀 Processing all images in ./input folder..."

# Use the appropriate docker-compose command
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.doug.yml run --rm photo-editor python photo_editor.py batch /data/input --output-dir /data/output
else
    docker compose -f docker-compose.doug.yml run --rm photo-editor python photo_editor.py batch /data/input --output-dir /data/output
fi

echo "✅ Done! Check ./output folder for results"
EOF
chmod +x doug_batch.sh

# Single image script
cat > doug_single.sh << 'EOF'
#!/bin/bash
if [ $# -eq 0 ]; then
    echo "Usage: ./doug_single.sh <image-file> [instructions]"
    echo "Example: ./doug_single.sh photo.jpg 'make it more vibrant'"
    exit 1
fi

IMAGE="$1"
INSTRUCTIONS="${2:-enhance and optimize}"

# Copy image to input folder
cp "$IMAGE" ./input/

# Use the appropriate docker-compose command
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.doug.yml run --rm photo-editor python photo_editor.py process "/data/input/$(basename $IMAGE)" --instructions "$INSTRUCTIONS" --output-dir /data/output
else
    docker compose -f docker-compose.doug.yml run --rm photo-editor python photo_editor.py process "/data/input/$(basename $IMAGE)" --instructions "$INSTRUCTIONS" --output-dir /data/output
fi

echo "✅ Done! Check ./output folder"
EOF
chmod +x doug_single.sh

# Interactive chat mode
cat > doug_chat.sh << 'EOF'
#!/bin/bash
echo "💬 Starting interactive chat mode..."

# Use the appropriate docker-compose command
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.doug.yml run --rm photo-editor python photo_editor.py chat
else
    docker compose -f docker-compose.doug.yml run --rm photo-editor python photo_editor.py chat
fi
EOF
chmod +x doug_chat.sh

# Stop script
cat > doug_stop.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping all containers..."

# Use the appropriate docker-compose command
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.doug.yml down
else
    docker compose -f docker-compose.doug.yml down
fi

echo "✅ All stopped!"
EOF
chmod +x doug_stop.sh

# Final success message
echo ""
echo ""
echo -e "${GREEN}🎉 🎉 🎉  SETUP COMPLETE! 🎉 🎉 🎉${NC}"
echo ""
echo -e "${BLUE}=== SUPER SIMPLE INSTRUCTIONS FOR DOUG ===${NC}"
echo ""
echo -e "${GREEN}STEP 1:${NC} Start the web interface"
echo "         ${YELLOW}./doug_web.sh${NC}"
echo ""
echo -e "${GREEN}STEP 2:${NC} Open your browser to:"
echo "         ${YELLOW}http://localhost:8501${NC}"
echo ""
echo -e "${GREEN}STEP 3:${NC} Enter your API keys in the web interface"
echo "         The app will save them for you!"
echo ""
echo -e "${GREEN}STEP 4:${NC} Upload photos and process!"
echo ""
echo -e "${BLUE}=== OTHER COMMANDS (OPTIONAL) ===${NC}"
echo ""
echo "  ${GREEN}./doug_batch.sh${NC}    → Process all images in ./input folder"
echo "  ${GREEN}./doug_stop.sh${NC}     → Stop everything when done"
echo ""
echo -e "${YELLOW}📸 THAT'S IT!${NC} The web interface handles everything else!"
echo ""
echo -e "🚀 Starting the web interface now..."
echo ""
./doug_web.sh