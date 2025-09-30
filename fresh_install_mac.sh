#!/bin/bash

# Fresh installation script for LangGraph Photo Editor on Mac
# This script will remove any existing installation and set up fresh

echo "🚀 Starting fresh installation of LangGraph Photo Editor..."
echo ""

# Navigate to home directory
cd ~

# Remove existing installation if it exists
if [ -d "langgraph-photo-editor" ]; then
    echo "📦 Removing existing installation..."
    rm -rf langgraph-photo-editor
fi

# Clone the repository
echo "📥 Cloning repository from GitHub..."
git clone https://github.com/pranavchavda/langgraph-photo-editor.git

# Check if clone was successful
if [ ! -d "langgraph-photo-editor" ]; then
    echo "❌ Error: Failed to clone repository. Please check your internet connection."
    exit 1
fi

# Navigate to project directory
cd langgraph-photo-editor

# Create virtual environment
echo ""
echo "🐍 Creating Python virtual environment..."
python3.11 -m venv venv 2>/dev/null || python3 -m venv venv

# Check if venv was created
if [ ! -d "venv" ]; then
    echo "❌ Error: Failed to create virtual environment. Please ensure Python 3.11 or Python 3 is installed."
    echo "Install with: brew install python@3.11"
    exit 1
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "📚 Installing required packages (this will take 2-5 minutes)..."
pip install -r requirements.txt

# Check if streamlit was installed
if ! pip show streamlit > /dev/null 2>&1; then
    echo "⚠️  Streamlit not found, installing directly..."
    pip install streamlit
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "🌟 Starting Streamlit app..."
echo "📱 The app will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the app when you're done."
echo ""

# Run the app
streamlit run streamlit_app.py