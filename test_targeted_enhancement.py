#!/usr/bin/env python3
"""
Test Targeted Enhancement Pipeline
Tests the surgical area enhancement approach after ImageMagick optimization
"""

import asyncio
import os
from pathlib import Path
from src.targeted_enhancement import targeted_enhancement_pipeline
from src.workflow_enhanced import process_single_image_enhanced

async def test_targeted_enhancement():
    """Test the targeted enhancement pipeline on a sample image"""
    
    # Test image path
    test_image = "113Nurri Type L Chrome+Zebra.jpg"
    
    if not Path(test_image).exists():
        print(f"❌ Test image not found: {test_image}")
        print("Please ensure you have a test image in the current directory")
        return
    
    print(f"📷 Testing targeted enhancement on: {test_image}")
    print("=" * 60)
    
    # Test 1: Direct targeted enhancement on an image
    print("\n🧪 Test 1: Direct targeted enhancement pipeline")
    print("-" * 40)
    
    result = await targeted_enhancement_pipeline(
        test_image,
        custom_instructions="Enhance chrome reflections and wood grain details",
        max_areas=3
    )
    
    if result.get("enhanced"):
        print(f"✅ Direct test successful!")
        print(f"  - Areas identified: {result.get('areas_identified', 0)}")
        print(f"  - Areas enhanced: {result.get('areas_enhanced', 0)}")
        print(f"  - Output: {result.get('final_image')}")
        
        if result.get("enhancement_details"):
            print("\n📋 Enhancement Details:")
            for area in result["enhancement_details"]:
                print(f"  - {area['description']} at ({area['coordinates']['x']}, {area['coordinates']['y']})")
                print(f"    Instructions: {area['instructions']}")
    else:
        print(f"ℹ️ No enhancements needed - image already optimal")
    
    # Test 2: Full workflow with targeted enhancement enabled
    print("\n🧪 Test 2: Full workflow with targeted enhancement")
    print("-" * 40)
    
    # Enable targeted enhancement
    os.environ["USE_TARGETED_ENHANCEMENT"] = "true"
    
    # Run the full enhanced workflow
    workflow_result = await process_single_image_enhanced(
        test_image,
        custom_instructions="Optimize for e-commerce. Skip Gemini.",
        output_dir="/tmp"
    )
    
    if workflow_result.get("final_image"):
        print(f"✅ Workflow test successful!")
        print(f"  - Quality score: {workflow_result.get('quality_score', 'N/A')}/10")
        print(f"  - Strategy used: {workflow_result.get('editing_strategy', 'N/A')}")
        print(f"  - Targeted enhancement: {workflow_result.get('targeted_enhancement_used', False)}")
        print(f"  - Output: {workflow_result.get('final_image')}")
    else:
        print(f"❌ Workflow failed: {workflow_result.get('error', 'Unknown error')}")
    
    # Clean up
    os.environ["USE_TARGETED_ENHANCEMENT"] = "false"
    
    print("\n" + "=" * 60)
    print("✅ Targeted enhancement testing complete!")
    print("\nNOTE: The targeted enhancement works best when:")
    print("  1. Image has already been optimized with ImageMagick")
    print("  2. Specific areas like chrome, wood, or textures need refinement")
    print("  3. You want surgical improvements without touching the whole image")

if __name__ == "__main__":
    # Check for required API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        exit(1)
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Please set GEMINI_API_KEY environment variable")
        exit(1)
    
    # Run the test
    asyncio.run(test_targeted_enhancement())