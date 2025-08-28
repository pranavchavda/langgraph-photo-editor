#!/usr/bin/env python3
"""Debug analysis agent output"""

import asyncio
import os
from pathlib import Path
import sys

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from src.agents_enhanced import enhanced_analysis_agent

async def debug_analysis():
    image_path = "/home/pranav/idc/photo_edit_test/Profitec RIDE - WebP 4000x 4000 Quick Edit for in House AI BackGround Removal/102Profitec RIDE.webp"
    custom_instructions = "analyze potential optimizations and run it via gemini after bg removal"
    
    print(f"🔍 Testing analysis agent with: {Path(image_path).name}")
    print(f"📝 Custom instructions: {custom_instructions}")
    
    try:
        result = await enhanced_analysis_agent(image_path, custom_instructions)
        print(f"\n✅ Analysis result:")
        print(f"Strategy: {result.get('editing_strategy', 'NOT SET')}")
        print(f"Gemini instructions: {result.get('gemini_instructions', 'NOT SET')}")
        print(f"ImageMagick command: {result.get('imagemagick_command', 'NOT SET')}")
        print(f"Remove background: {result.get('remove_background', 'NOT SET')}")
        print(f"Editing explanation: {result.get('editing_explanation', 'NOT SET')}")
        
        return result
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(debug_analysis())