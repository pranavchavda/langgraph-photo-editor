#!/usr/bin/env python3
"""Simple test for the enhanced analysis agent without stream writer context"""

import asyncio
import os
import sys
import base64
import json
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents_enhanced import enhanced_analysis_agent, AgentError

# Mock stream writer for testing
def mock_writer(data):
    """Mock stream writer that just prints to console"""
    print(f"[{data.get('agent', 'unknown')}] {data.get('status', 'unknown')}: {data.get('message', '')}")

# Patch the get_stream_writer function
import src.agents_enhanced
src.agents_enhanced.get_stream_writer = lambda: mock_writer

async def test_simple_analysis():
    """Test the enhanced analysis agent with a mock stream writer"""
    
    # Use the available image from project directory
    test_image = "113Nurri Type L Chrome+Zebra.jpg"
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        print("Available images: 113Nurri Type L Chrome+Zebra.jpg, logo.jpeg")
        return
    
    print("🔍 Testing enhanced analysis with Gemini 2.5 Flash strategy selection...")
    
    try:
        # Test with custom instructions
        result = await enhanced_analysis_agent(
            test_image, 
            "make the chrome more vibrant and remove any background artifacts"
        )
        
        print("\n📊 Enhanced Analysis Results:")
        print(f"   Editing Strategy: {result.get('editing_strategy', 'unknown')}")
        print(f"   Materials Detected: {result.get('surface_materials', [])}")
        print(f"   Complex Problems: {result.get('complex_problems', [])}")
        print(f"   Remove Background: {result.get('remove_background', False)}")
        
        if result.get('editing_strategy') == 'gemini':
            print(f"\n🎨 Gemini Instructions:")
            print(f"   {result.get('gemini_instructions', 'None')}")
        
        if result.get('imagemagick_command'):
            print(f"\n⚡ ImageMagick Command:")
            print(f"   {result.get('imagemagick_command')}")
        
        print(f"\n💡 Strategy Explanation:")
        print(f"   {result.get('editing_explanation', 'No explanation provided')}")
        
    except AgentError as e:
        print(f"❌ Agent error: {e}")
        return
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✅ Enhanced analysis test completed successfully!")

if __name__ == "__main__":
    # Check API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set")
        sys.exit(1)
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set (required for Gemini 2.5 Flash)")
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    asyncio.run(test_simple_analysis())
