#!/bin/bash

echo "🔧 Fixing Python import issue..."

cd ~/langgraph-photo-editor

# Backup original files
cp src/workflow_enhanced.py src/workflow_enhanced.py.backup
cp streamlit_app.py streamlit_app.py.backup

# Fix the multi-line import in workflow_enhanced.py (line 17-22)
# Replace the multi-line import with a single line
sed -i '' '/^from \.agents_enhanced import ($/,/^)$/{
  s/^from \.agents_enhanced import ($/from .agents_enhanced import enhanced_analysis_agent, gemini_edit_agent, imagemagick_optimization_agent, background_removal_agent, qc_agent/
  /^[[:space:]]*enhanced_analysis_agent,$/d
  /^[[:space:]]*gemini_edit_agent,$/d
  /^[[:space:]]*imagemagick_optimization_agent,$/d
  /^[[:space:]]*background_removal_agent,$/d
  /^[[:space:]]*qc_agent$/d
  /^)$/d
}' src/workflow_enhanced.py

# Fix the multi-line import in streamlit_app.py (line 20)
sed -i '' 's/^from src\.workflow_enhanced import process_single_image_enhanced$/from src.workflow_enhanced import process_single_image_enhanced/' streamlit_app.py

echo "✅ Imports fixed!"
echo ""
echo "Now run:"
echo "  cd ~/langgraph-photo-editor"
echo "  source venv/bin/activate"
echo "  streamlit run streamlit_app.py"
echo ""
echo "The app should open at http://localhost:8501"