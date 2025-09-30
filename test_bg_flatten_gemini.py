#!/usr/bin/env python3
"""
Test background removal + Gemini editing with white background flattening
"""

import asyncio
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.workflow_enhanced import enhanced_agentic_processor
import uuid

def create_test_image_with_alpha():
    """Create a test image with transparency to simulate BG removal"""
    
    # Create RGBA image with transparent background
    img = Image.new('RGBA', (800, 600), (0, 0, 0, 0))
    
    # Draw a product-like shape
    draw = ImageDraw.Draw(img)
    
    # Draw a coffee mug shape with solid colors
    # Mug body
    draw.ellipse([200, 150, 600, 450], fill=(100, 50, 20, 255))  # Brown mug
    # Handle
    draw.ellipse([550, 250, 650, 350], fill=None, outline=(100, 50, 20, 255), width=20)
    # Coffee inside
    draw.ellipse([230, 180, 570, 300], fill=(40, 20, 10, 255))
    # Highlight
    draw.ellipse([250, 200, 350, 250], fill=(150, 100, 50, 128))
    
    # Save with transparency
    transparent_path = Path(tempfile.gettempdir()) / "test_product_no_bg.png"
    img.save(str(transparent_path), 'PNG')
    
    print(f"✅ Created test image with transparency: {transparent_path}")
    return str(transparent_path)

async def test_bg_removal_gemini_pipeline():
    """Test the pipeline with BG removal followed by Gemini editing"""
    
    print("🧪 Testing BG Removal + Gemini Editing with Flattening")
    print("=" * 80)
    
    # Create test image
    test_image = create_test_image_with_alpha()
    
    print(f"\n📸 Test image: {test_image}")
    
    # Test scenarios
    scenarios = [
        {
            "name": "Gemini Edit on Transparent Image",
            "env": {
                "SKIP_BACKGROUND_REMOVAL": "true",  # Already transparent
                "SKIP_GEMINI": "false",
                "SKIP_IMAGEMAGICK": "true",
            },
            "instructions": "Make the product more vibrant and enhance the colors"
        },
        {
            "name": "Full Pipeline with BG Removal First",
            "env": {
                "SKIP_BACKGROUND_REMOVAL": "false",
                "SKIP_GEMINI": "false", 
                "SKIP_IMAGEMAGICK": "true",
            },
            "instructions": "Remove background and enhance colors"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🔬 Testing: {scenario['name']}")
        print("-" * 40)
        
        # Set environment variables
        for key, value in scenario['env'].items():
            os.environ[key] = value
            print(f"   {key}: {value}")
        
        try:
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            
            if hasattr(enhanced_agentic_processor, 'ainvoke'):
                result = await enhanced_agentic_processor.ainvoke({
                    "image_path": test_image,
                    "custom_instructions": scenario['instructions']
                }, config=config)
            else:
                result = await enhanced_agentic_processor({
                    "image_path": test_image,
                    "custom_instructions": scenario['instructions']
                })
            
            print(f"\n✅ Result for '{scenario['name']}':")
            print(f"   Final image: {result.get('final_image', 'N/A')}")
            print(f"   Quality score: {result.get('quality_score', 'N/A')}/10")
            print(f"   Strategy used: {result.get('editing_strategy', 'N/A')}")
            
            # Check if flattening occurred
            if result.get('final_image'):
                final_img = Image.open(result['final_image'])
                print(f"   Final image mode: {final_img.mode}")
                print(f"   Has transparency: {final_img.mode in ('RGBA', 'LA')}")
            
        except Exception as e:
            print(f"\n❌ Error in '{scenario['name']}': {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ Testing complete!")
    print("\nKey Points:")
    print("1. Transparent images are flattened with white background before Gemini")
    print("2. This prevents Gemini from failing on transparent PNGs")
    print("3. Flattening only happens for Gemini, not for other agents")

async def test_manual_gemini_flattening():
    """Test just the flattening logic in isolation"""
    
    print("\n🔬 Testing Flattening Logic in Isolation")
    print("-" * 40)
    
    # Create transparent image
    transparent_img = create_test_image_with_alpha()
    
    # Load and check
    img = Image.open(transparent_img)
    print(f"Original image mode: {img.mode}")
    print(f"Has alpha channel: {img.mode in ('RGBA', 'LA')}")
    
    # Flatten with white background
    if img.mode in ('RGBA', 'LA'):
        print("\n⬜ Flattening with white background...")
        
        # Create white background
        white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
        # Composite original over white
        white_bg.paste(img, (0, 0), img)
        # Convert to RGB
        flattened = white_bg.convert('RGB')
        
        # Save
        flattened_path = Path(tempfile.gettempdir()) / "test_flattened.jpg"
        flattened.save(str(flattened_path), 'JPEG', quality=95)
        
        print(f"✅ Flattened image saved: {flattened_path}")
        print(f"   Mode: {flattened.mode}")
        print(f"   Size: {flattened.size}")

if __name__ == "__main__":
    print("🚀 Starting BG Removal + Gemini Flattening Test\n")
    
    # Run tests
    asyncio.run(test_bg_removal_gemini_pipeline())
    asyncio.run(test_manual_gemini_flattening())