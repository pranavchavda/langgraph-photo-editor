#!/bin/bash

# Agentic Photo Editor - Electron App Setup Script
# Sets up development environment and builds the desktop application

set -e  # Exit on error

echo "🤖 Agentic Photo Editor - Desktop App Setup"
echo "============================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Node.js
if ! command_exists node; then
    echo "❌ Node.js is required but not installed"
    echo "   Please install Node.js from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Node.js: $NODE_VERSION"

# Check npm
if ! command_exists npm; then
    echo "❌ npm is required but not installed"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo "✅ npm: $NPM_VERSION"

# Check Python
if ! command_exists python3; then
    if ! command_exists python; then
        echo "❌ Python is required but not installed"
        echo "   Please install Python 3.8+ from https://python.org/"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo "✅ Python: $PYTHON_VERSION"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Not in electron directory. Please run from electron/ folder"
    exit 1
fi

# Check if parent photo_editor.py exists
PARENT_SCRIPT="../photo_editor.py"
if [ ! -f "$PARENT_SCRIPT" ]; then
    echo "⚠️  Warning: photo_editor.py not found at $PARENT_SCRIPT"
    echo "   The desktop app requires the main Python script to function"
fi

echo
echo "🔧 Setting up development environment..."

# Install dependencies
echo "📦 Installing npm dependencies..."
npm install

# Check for TypeScript compilation
echo "🔍 Checking TypeScript compilation..."
npx tsc --noEmit

echo
echo "🏗️  Building application..."

# Development build
echo "📦 Building for development..."
npm run build

echo
echo "✅ Setup complete!"
echo
echo "📚 Next steps:"
echo "   1. Configure API keys in the Settings panel"
echo "   2. Start development: npm run dev"
echo "   3. Launch app: npm start"
echo
echo "🎯 Production build:"
echo "   - Package app: npm run dist"
echo "   - Installers will be in build/ directory"
echo
echo "📖 See README.md for detailed usage instructions"