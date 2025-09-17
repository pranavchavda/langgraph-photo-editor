# Manual Fix for Doug

Doug, let's do this manually to make sure it works:

1. Open the file in a text editor:
```bash
nano ~/langgraph-photo-editor/src/workflow_enhanced.py
```

2. Go to line 17 (you'll see `from .agents_enhanced import (`)

3. Delete lines 17-25 (the entire import block from `from .agents_enhanced import (` to the closing `)`)

4. Replace it with this single line:
```python
from .agents_enhanced import enhanced_analysis_agent, gemini_edit_agent, imagemagick_optimization_agent, background_removal_agent, enhanced_qc_agent, AgentError, get_imagemagick_command
```

5. Save and exit:
   - Press `Ctrl + O` to save
   - Press `Enter` to confirm
   - Press `Ctrl + X` to exit

6. Now run:
```bash
cd ~/langgraph-photo-editor
source venv/bin/activate
streamlit run streamlit_app.py
```

This should fix it!