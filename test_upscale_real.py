#!/usr/bin/env python3
"""
Test AI upscaling with a real product image
"""

import asyncio
import sys
import os
from pathlib import Path
from PIL import Image

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_upscaler_agent import AIUpscalerAgent

async def test_upscaling():
    """Test AI upscaling with different scenarios"""
    
    # Find a test image - look for any jpg/png in current directory
    test_images = list(Path(".").glob("*.jpg")) + list(Path(".").glob("*.png"))
    
    if not test_images:
        print("❌ No test images found. Creating a sample image...")
        # Create a test image
        test_img = Image.new('RGB', (400, 300), color='lightblue')
        test_path = '/tmp/test_product.jpg'
        test_img.save(test_path)
    else:
        test_path = str(test_images[0])
        print(f"📸 Using test image: {test_path}")
    
    # Load image and show dimensions
    img = Image.open(test_path)
    width, height = img.size
    print(f"Original dimensions: {width}x{height}")
    
    agent = AIUpscalerAgent(service="vertex")
    
    # Test 1: Simple 2x upscaling
    print("\n" + "="*50)
    print("Test 1: Simple 2x upscaling")
    print("="*50)
    
    result = await agent.upscale_vertex(
        image_path=test_path,
        scale_factor="x2",
        output_path="/tmp/upscaled_2x.png"
    )
    
    if result["status"] == "success":
        print(f"✅ 2x upscaling successful!")
        print(f"   Original: {result['original_size']}")
        print(f"   Upscaled: {result['upscaled_size']}")
        print(f"   Output: {result['output_path']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 2: 4x upscaling
    print("\n" + "="*50)
    print("Test 2: 4x upscaling")
    print("="*50)
    
    result = await agent.upscale_vertex(
        image_path=test_path,
        scale_factor="x4",
        output_path="/tmp/upscaled_4x.png"
    )
    
    if result["status"] == "success":
        print(f"✅ 4x upscaling successful!")
        print(f"   Original: {result['original_size']}")
        print(f"   Upscaled: {result['upscaled_size']}")
        print(f"   Output: {result['output_path']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 3: Upscale to specific target dimensions
    print("\n" + "="*50)
    print("Test 3: Upscale to specific dimensions (1920x1080)")
    print("="*50)
    
    result = await agent.upscale_to_target(
        image_path=test_path,
        target_width=1920,
        target_height=1080,
        output_path="/tmp/upscaled_target.png"
    )
    
    if result["status"] == "success":
        print(f"✅ Target upscaling successful!")
        print(f"   Original: {result['original_size']}")
        print(f"   AI Upscaled: {result['upscaled_size']}")
        if 'final_size' in result:
            print(f"   Final size: {result['final_size']}")
        print(f"   Two-stage: {result.get('two_stage', False)}")
        print(f"   Output: {result['output_path']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    print("\n" + "="*50)
    print("✨ All tests complete!")
    print("Check /tmp/upscaled_*.png for results")

if __name__ == "__main__":
    asyncio.run(test_upscaling())