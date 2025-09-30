#!/usr/bin/env python3
"""
Simple test for AI upscaling
"""

import asyncio
import sys
import os
from pathlib import Path
from PIL import Image
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_upscaler_agent import AIUpscalerAgent

async def simple_test():
    """Simple upscaling test"""
    
    # Create a small test image
    print("📸 Creating test image (200x200)...")
    test_img = Image.new('RGB', (200, 200), color='blue')
    
    # Draw something on it to make it more interesting
    from PIL import ImageDraw
    draw = ImageDraw.Draw(test_img)
    draw.rectangle([50, 50, 150, 150], fill='yellow', outline='red', width=3)
    draw.ellipse([75, 75, 125, 125], fill='green')
    
    test_path = '/tmp/test_simple.jpg'
    test_img.save(test_path)
    print(f"✅ Test image saved to {test_path}")
    
    agent = AIUpscalerAgent(service="vertex")
    
    print("\n🚀 Testing 2x upscaling...")
    start_time = time.time()
    
    try:
        result = await agent.upscale_vertex(
            image_path=test_path,
            scale_factor="x2",
            output_path="/tmp/upscaled_simple_2x.png"
        )
        
        elapsed = time.time() - start_time
        
        if result["status"] == "success":
            print(f"✅ Upscaling successful in {elapsed:.1f} seconds!")
            print(f"   Original: {result['original_size']}")
            print(f"   Upscaled: {result['upscaled_size']}")
            print(f"   Output: {result['output_path']}")
            
            # Verify the output
            upscaled = Image.open(result['output_path'])
            print(f"   Verified size: {upscaled.size}")
        else:
            print(f"❌ Error: {result['error']}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(simple_test())