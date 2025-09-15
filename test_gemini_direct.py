#!/usr/bin/env python3
"""
Test Gemini editing directly to see what it produces
"""

import asyncio
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import tempfile

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.agents_enhanced import gemini_edit_agent

async def test_gemini_direct():
    """Test Gemini agent directly"""
    
    # Create a test image with clear features
    print("📸 Creating test image...")
    test_img = Image.new('RGB', (800, 600), color='lightgray')
    draw = ImageDraw.Draw(test_img)
    
    # Draw distinctive features
    draw.rectangle([50, 50, 750, 550], outline='black', width=10)
    draw.ellipse([200, 150, 600, 450], fill='blue', outline='red', width=5)
    draw.text((300, 280), "ORIGINAL", fill='white')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        test_path = tmp.name
        test_img.save(test_path, quality=95)
    
    print(f"✅ Test image saved to: {test_path}")
    print(f"   Size: {test_img.size}")
    print(f"   File size: {os.path.getsize(test_path)} bytes")
    
    # Create a simple analysis
    analysis = {
        "editing_strategy": "gemini",
        "instructions": "Make the image much more vibrant and colorful. Change the blue circle to bright green. Add dramatic lighting effects.",
        "remove_background": False,
        "quality_issues": ["lacks vibrancy", "dull colors"],
        "enhancement_suggestions": ["increase saturation", "boost contrast", "add dramatic lighting"]
    }
    
    print("\n🎨 Calling Gemini edit agent...")
    print(f"   Instructions: {analysis['instructions']}")
    
    try:
        # Set environment for no upscaling
        os.environ["USE_AI_UPSCALING"] = "false"
        
        result_path = await gemini_edit_agent(test_path, analysis)
        
        print(f"\n✅ Gemini editing complete!")
        print(f"   Output path: {result_path}")
        print(f"   File exists: {os.path.exists(result_path)}")
        
        if os.path.exists(result_path):
            result_img = Image.open(result_path)
            print(f"   Output size: {result_img.size}")
            print(f"   Output file size: {os.path.getsize(result_path)} bytes")
            
            # Check if it's named correctly
            if "gemini-edited" in result_path:
                print("   ✅ Correctly named as gemini-edited")
            else:
                print("   ⚠️ Not named as gemini-edited")
            
            # Compare with original
            print("\n📊 Comparison:")
            print(f"   Original: {test_path}")
            print(f"   Edited: {result_path}")
            
            # Save both images side by side for visual comparison
            comparison = Image.new('RGB', (1600, 600), 'white')
            comparison.paste(test_img, (0, 0))
            comparison.paste(result_img.resize((800, 600)), (800, 0))
            
            comp_path = "/tmp/gemini_comparison.png"
            comparison.save(comp_path)
            print(f"\n📸 Side-by-side comparison saved to: {comp_path}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if os.path.exists(test_path):
            os.unlink(test_path)
        print("\n✨ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_gemini_direct())