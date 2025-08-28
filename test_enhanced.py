#!/usr/bin/env python3
"""Test the enhanced Gemini 2.5 Flash Image workflow"""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents_enhanced import enhanced_analysis_agent

async def test_enhanced_analysis():
    """Test the enhanced analysis agent"""
    
    test_image = "/tmp/luce_pid_white_simple.webp"
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        print("Please ensure you have a test image available")
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
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
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
    
    asyncio.run(test_enhanced_analysis())