#!/usr/bin/env python3
"""
Test standalone Gemini editing to ensure the correct image is displayed
"""

import asyncio
import os
import sys
from pathlib import Path
from PIL import Image
import tempfile

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.workflow_enhanced import process_single_image_enhanced

async def test_gemini_standalone():
    """Test that Gemini-only editing returns the correct image"""
    
    # Create a simple test image
    print("📸 Creating test image...")
    test_img = Image.new('RGB', (800, 600), color='lightblue')
    
    # Add some details to make it recognizable
    from PIL import ImageDraw
    draw = ImageDraw.Draw(test_img)
    draw.rectangle([100, 100, 700, 500], fill='yellow', outline='red', width=5)
    draw.text((350, 280), "TEST IMAGE", fill='black')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        test_path = tmp.name
        test_img.save(test_path)
    
    print(f"✅ Test image saved to: {test_path}")
    
    # Test 1: Gemini-only without background removal
    print("\n" + "="*60)
    print("TEST 1: Gemini-only editing (no background removal)")
    print("="*60)
    
    # Disable background removal and ImageMagick
    os.environ["SKIP_BACKGROUND_REMOVAL"] = "true"
    os.environ["SKIP_IMAGEMAGICK"] = "true"
    os.environ["USE_AI_UPSCALING"] = "false"
    
    with tempfile.TemporaryDirectory() as output_dir:
        result = await process_single_image_enhanced(
            image_path=test_path,
            custom_instructions="Use Gemini. Make the image more vibrant and colorful.",
            output_dir=output_dir
        )
        
        print(f"\n📊 Result:")
        print(f"   Final image: {result.get('final_image')}")
        print(f"   QC passed: {result.get('qc_passed')}")
        print(f"   Quality score: {result.get('quality_score')}")
        print(f"   Strategy: {result.get('editing_strategy')}")
        print(f"   Gemini used: {result.get('gemini_used')}")
        
        if result.get('final_image'):
            final_path = result['final_image']
            if os.path.exists(final_path):
                img = Image.open(final_path)
                print(f"   Image size: {img.size}")
                print(f"   File size: {os.path.getsize(final_path)} bytes")
                
                # Check if it's the Gemini-edited version
                if "gemini-edited" in final_path:
                    print("   ✅ This IS the Gemini-edited image!")
                else:
                    print("   ⚠️ This is NOT named as Gemini-edited")
                    
                # List all files in output dir to see what was created
                print(f"\n   Files in output directory:")
                for file in Path(output_dir).glob("*"):
                    print(f"      - {file.name} ({file.stat().st_size} bytes)")
    
    # Test 2: Gemini with AI upscaling
    print("\n" + "="*60)
    print("TEST 2: Gemini with AI upscaling")
    print("="*60)
    
    os.environ["USE_AI_UPSCALING"] = "true"
    
    with tempfile.TemporaryDirectory() as output_dir:
        result = await process_single_image_enhanced(
            image_path=test_path,
            custom_instructions="Use Gemini. Enhance the colors.",
            output_dir=output_dir
        )
        
        print(f"\n📊 Result:")
        print(f"   Final image: {result.get('final_image')}")
        print(f"   Quality score: {result.get('quality_score')}")
        
        if result.get('final_image'):
            final_path = result['final_image']
            if os.path.exists(final_path):
                img = Image.open(final_path)
                print(f"   Image size: {img.size}")
                print(f"   File size: {os.path.getsize(final_path)} bytes")
    
    # Clean up
    os.unlink(test_path)
    print("\n✅ Tests complete!")

if __name__ == "__main__":
    asyncio.run(test_gemini_standalone())