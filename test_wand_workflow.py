#!/usr/bin/env python3
"""Test the new Wand-based workflow"""

import asyncio
from PIL import Image

async def test_wand_workflow():
    """Test the workflow with Wand and cropping"""
    from src.workflow_enhanced import process_single_image_enhanced
    
    test_image = "113Nurri Type L Chrome+Zebra.jpg"
    
    # Get original dimensions
    orig = Image.open(test_image)
    print(f"Original image: {test_image}")
    print(f"  Resolution: {orig.size[0]}x{orig.size[1]}")
    print(f"  Megapixels: {(orig.size[0] * orig.size[1]) / 1_000_000:.2f} MP\n")
    
    print("Testing with 'Skip Gemini' to use Wand-based ImageMagick...")
    
    result = await process_single_image_enhanced(
        image_path=test_image,
        custom_instructions="Enhance chrome surfaces and wood grain. Make more vibrant. Skip Gemini.",
        output_dir="/tmp"
    )
    
    if result.get('final_image'):
        final = Image.open(result['final_image'])
        print(f"\nFinal image: {result['final_image']}")
        print(f"  Resolution: {final.size[0]}x{final.size[1]}")
        print(f"  Megapixels: {(final.size[0] * final.size[1]) / 1_000_000:.2f} MP")
        print(f"  Strategy used: {result.get('strategy', 'unknown')}")
        print(f"  Quality score: {result.get('final_quality', 'N/A')}")
        
        # Check if resolution was preserved
        if final.size == orig.size:
            print("\n✅ Resolution fully preserved!")
        else:
            reduction = (1 - (final.size[0] * final.size[1]) / (orig.size[0] * orig.size[1])) * 100
            print(f"\n📐 Resolution changed by {reduction:.1f}%")

if __name__ == "__main__":
    asyncio.run(test_wand_workflow())