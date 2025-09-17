#!/bin/bash

echo "🔧 Applying simple workaround..."

cd ~/langgraph-photo-editor

# Make a backup
cp src/agents_enhanced.py src/agents_enhanced.py.original

# Create a new version with all multi-line imports converted to single lines
python3 << 'EOF'
import re

# Read the file
with open('src/agents_enhanced.py', 'r') as f:
    content = f.read()

# Just in case there's a hidden character issue, rewrite the whole file
with open('src/agents_enhanced_fixed.py', 'w') as f:
    f.write(content)

# Also fix workflow_enhanced.py to use single-line imports
with open('src/workflow_enhanced.py', 'r') as f:
    content = f.read()

# Convert the multi-line import to single line
content = content.replace('''from .agents_enhanced import (
    enhanced_analysis_agent,
    gemini_edit_agent,
    imagemagick_optimization_agent,
    background_removal_agent,
    enhanced_qc_agent,
    AgentError,
    get_imagemagick_command
)''', 'from .agents_enhanced_fixed import enhanced_analysis_agent, gemini_edit_agent, imagemagick_optimization_agent, background_removal_agent, enhanced_qc_agent, AgentError, get_imagemagick_command')

with open('src/workflow_enhanced.py', 'w') as f:
    f.write(content)

print("Fixed imports to use agents_enhanced_fixed.py")
EOF

# Rename the new file
mv src/agents_enhanced_fixed.py src/agents_enhanced.py

echo "✅ Workaround applied!"
echo ""
echo "Now try:"
echo "  source venv/bin/activate"
echo "  streamlit run streamlit_app.py"