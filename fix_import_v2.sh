#!/bin/bash

echo "🔧 Fixing Python import issue (v2)..."

cd ~/langgraph-photo-editor

# Restore from backup if it exists
if [ -f src/workflow_enhanced.py.backup ]; then
    echo "Restoring from backup..."
    cp src/workflow_enhanced.py.backup src/workflow_enhanced.py
fi

# Create a temporary Python script to fix the imports properly
cat > fix_imports.py << 'EOF'
import re

# Fix workflow_enhanced.py
with open('src/workflow_enhanced.py', 'r') as f:
    content = f.read()

# Replace multi-line import with single line
pattern = r'from \.agents_enhanced import \(\s*\n\s*enhanced_analysis_agent,\s*\n\s*gemini_edit_agent,\s*\n\s*imagemagick_optimization_agent,\s*\n\s*background_removal_agent,\s*\n\s*qc_agent\s*\n\)'
replacement = 'from .agents_enhanced import enhanced_analysis_agent, gemini_edit_agent, imagemagick_optimization_agent, background_removal_agent, qc_agent'

content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

# Also handle any leftover orphaned lines
content = re.sub(r'\n\s*imagemagick_optimization_agent,\s*\n', '\n', content)
content = re.sub(r'\n\s*enhanced_analysis_agent,\s*\n', '\n', content)
content = re.sub(r'\n\s*gemini_edit_agent,\s*\n', '\n', content)
content = re.sub(r'\n\s*background_removal_agent,\s*\n', '\n', content)
content = re.sub(r'\n\s*qc_agent\s*\n', '\n', content)

with open('src/workflow_enhanced.py', 'w') as f:
    f.write(content)

print("✅ Fixed workflow_enhanced.py")
EOF

# Run the Python fix script
python fix_imports.py

# Clean up
rm fix_imports.py

echo "✅ All imports fixed!"
echo ""
echo "Now run:"
echo "  cd ~/langgraph-photo-editor"
echo "  source venv/bin/activate"
echo "  streamlit run streamlit_app.py"
echo ""
echo "The app should open at http://localhost:8501"