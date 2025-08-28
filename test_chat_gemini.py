#!/usr/bin/env python3
"""Test chat mode Gemini functionality"""

import asyncio
import os
from pathlib import Path
import sys

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from src.cli_enhanced import execute_enhanced_chat_instruction

async def test_chat_gemini():
    """Test if chat mode actually uses Gemini"""
    
    instruction = {
        'target': '/home/pranav/idc/photo_edit_test/Profitec RIDE - WebP 4000x 4000 Quick Edit for in House AI BackGround Removal/102Profitec RIDE.webp',
        'mode': 'single',
        'instructions': 'remove unwanted reflections and enhance the chrome surfaces with advanced AI editing techniques'
    }
    
    print("🧪 Testing chat mode with Gemini-triggering instructions...")
    print(f"📁 Target: {instruction['target']}")
    print(f"📝 Instructions: {instruction['instructions']}")
    
    try:
        await execute_enhanced_chat_instruction(instruction, use_enhanced=True)
        print("✅ Chat mode test completed")
    except Exception as e:
        print(f"❌ Chat mode test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat_gemini())