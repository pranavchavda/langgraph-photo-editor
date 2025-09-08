#!/usr/bin/env python3
"""Test chunked pipeline with background removal"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.chunked_gemini_workflow import chunked_gemini_pipeline
from PIL import Image

async def test_with_background_removal():
    """Test chunked pipeline with background removal"""
    print("=" * 50)
    print("Testing Chunked Pipeline with Background Removal")
    print("=" * 50)
    
    result = await chunked_gemini_pipeline(
        image_path="113Nurri Type L Chrome+Zebra.jpg",
        custom_instructions="Enhance chrome surfaces and wood textures for e-commerce",
        output_dir="/tmp",
        target_4k=False,  # Keep full resolution for testing
        remove_background=True  # Enable background removal
    )
    
    print("\n📊 Pipeline Results:")
    for key, value in result.items():
        if key not in ['original_resolution', 'working_resolution', 'final_resolution']:
            print(f"  {key}: {value}")
        else:
            if isinstance(value, tuple):
                print(f"  {key}: {value[0]}x{value[1]}")
            else:
                print(f"  {key}: {value}")
    
    # Check if background was actually removed
    if result.get("success") and result.get("final_image"):
        final_img = Image.open(result["final_image"])
        if final_img.mode == 'RGBA':
            print("\n✅ Image has alpha channel - background removed successfully!")
        else:
            print("\n⚠️ Image is RGB - check if background was actually removed")
        
        print(f"\nFinal image saved to: {result['final_image']}")
    
    return result

async def test_without_background():
    """Test chunked pipeline without background removal for comparison"""
    print("\n" + "=" * 50)
    print("Testing WITHOUT Background Removal (for comparison)")
    print("=" * 50)
    
    result = await chunked_gemini_pipeline(
        image_path="113Nurri Type L Chrome+Zebra.jpg",
        custom_instructions="Enhance chrome surfaces and wood textures for e-commerce",
        output_dir="/tmp",
        target_4k=False,
        remove_background=False  # Disable background removal
    )
    
    if result.get("success"):
        print(f"✅ Processed without background removal")
        print(f"Output: {result.get('final_image')}")
    
    return result

if __name__ == "__main__":
    print("🚀 Testing Chunked Pipeline with Background Removal\n")
    
    # Test with background removal
    result_with_bg = asyncio.run(test_with_background_removal())
    
    if result_with_bg.get("success"):
        print("\n🎉 Background removal + chunked processing SUCCESS!")
        
        # Optional: test without background removal for comparison
        print("\nRun comparison test without background removal? (y/n): ", end="")
        if input().lower() == 'y':
            result_without_bg = asyncio.run(test_without_background())
            
            print("\n" + "=" * 50)
            print("COMPARISON SUMMARY")
            print("=" * 50)
            print("With Background Removal:")
            print(f"  - File: {result_with_bg.get('final_image')}")
            print(f"  - Chunks: {result_with_bg.get('chunks_processed')}/{result_with_bg.get('total_chunks')}")
            
            print("\nWithout Background Removal:")
            print(f"  - File: {result_without_bg.get('final_image')}")
            print(f"  - Chunks: {result_without_bg.get('chunks_processed')}/{result_without_bg.get('total_chunks')}")
    else:
        print("\n❌ Pipeline failed")