#!/usr/bin/env python3
"""
Agentic Photo Editor with Gemini 2.5 Flash Integration
AI-powered product photography optimization for e-commerce
"""

import sys
import os
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import and run the enhanced CLI with Gemini integration
from src.cli_enhanced import main

if __name__ == "__main__":
    main()