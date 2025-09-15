#!/usr/bin/env python3
"""
Test the updated pipeline with background removal first and trim functionality
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.workflow_enhanced import enhanced_agentic_processor
import uuid

async def test_pipeline():
    """Test the updated pipeline with various scenarios"""
    
    # Test image paths - update these to your test images
    test_images = [
        "/tmp/test_product.jpg",  # Update this path
        # Add more test images
    ]
    
    # Find first existing test image
    test_image = None
    for img in test_images:
        if os.path.exists(img):
            test_image = img
            break
    
    if not test_image:
        print("❌ No test image found. Please provide a test image path.")
        print("   You can use: python test_bg_trim_pipeline.py /path/to/image.jpg")
        return
    
    print(f"📸 Testing with image: {test_image}")
    print("=" * 80)
    
    # Test scenarios
    scenarios = [
        {
            "name": "Background Removal + Trim",
            "env": {
                "SKIP_BACKGROUND_REMOVAL": "false",
                "SKIP_IMAGEMAGICK": "false",
            },
            "instructions": "Remove background and trim excess whitespace"
        },
        {
            "name": "Background Removal Only",
            "env": {
                "SKIP_BACKGROUND_REMOVAL": "false",
                "SKIP_IMAGEMAGICK": "false",
            },
            "instructions": "Remove background"
        },
        {
            "name": "Trim Only (no BG removal)",
            "env": {
                "SKIP_BACKGROUND_REMOVAL": "true",
                "SKIP_IMAGEMAGICK": "false",
            },
            "instructions": "Trim excess whitespace"
        },
    ]
    
    for scenario in scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        print("-" * 40)
        
        # Set environment variables
        for key, value in scenario['env'].items():
            os.environ[key] = value
            print(f"   {key}: {value}")
        
        # Run the pipeline
        try:
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            
            # Check if enhanced_agentic_processor has ainvoke method
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
            
            # Print results
            print(f"\n✅ Result for '{scenario['name']}':")
            print(f"   Final image: {result.get('final_image', 'N/A')}")
            print(f"   Quality score: {result.get('quality_score', 'N/A')}/10")
            print(f"   QC passed: {result.get('qc_passed', False)}")
            print(f"   Strategy: {result.get('editing_strategy', 'N/A')}")
            
            if result.get('final_image') and os.path.exists(result['final_image']):
                file_size = os.path.getsize(result['final_image']) / 1024
                print(f"   File size: {file_size:.1f} KB")
            
        except Exception as e:
            print(f"\n❌ Error in '{scenario['name']}': {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ Pipeline testing complete!")

async def test_single_image(image_path: str, instructions: str = None):
    """Test with a specific image"""
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"📸 Testing with: {image_path}")
    print(f"📝 Instructions: {instructions or 'Default processing'}")
    print("=" * 80)
    
    # Set environment for testing
    os.environ["SKIP_BACKGROUND_REMOVAL"] = "false"  # Enable BG removal
    
    try:
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        
        if hasattr(enhanced_agentic_processor, 'ainvoke'):
            result = await enhanced_agentic_processor.ainvoke({
                "image_path": image_path,
                "custom_instructions": instructions
            }, config=config)
        else:
            result = await enhanced_agentic_processor({
                "image_path": image_path,
                "custom_instructions": instructions
            })
        
        print("\n✅ Processing complete!")
        print(f"   Final image: {result.get('final_image', 'N/A')}")
        print(f"   Quality score: {result.get('quality_score', 'N/A')}/10")
        print(f"   QC passed: {result.get('qc_passed', False)}")
        print(f"   Strategy: {result.get('editing_strategy', 'N/A')}")
        
        if result.get('final_image') and os.path.exists(result['final_image']):
            file_size = os.path.getsize(result['final_image']) / 1024
            print(f"   File size: {file_size:.1f} KB")
            print(f"\n📁 Output saved to: {result['final_image']}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with specific image
        image_path = sys.argv[1]
        instructions = sys.argv[2] if len(sys.argv) > 2 else "Remove background and trim excess whitespace"
        asyncio.run(test_single_image(image_path, instructions))
    else:
        # Run default tests
        asyncio.run(test_pipeline())