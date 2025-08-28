#!/usr/bin/env python3
"""Debug the workflow to see what's happening"""

import asyncio
import os
import traceback
from src.workflow_enhanced import process_single_image_enhanced

async def debug_workflow():
    """Test the workflow with verbose error reporting"""
    
    image_path = "/home/pranav/idc/photo_edit_test/test1/101Profitec RIDE.webp"
    instructions = "convert this espresso machine to look like a pencil drawing sketch"
    
    print(f"🔍 Testing workflow with:")
    print(f"   Image: {image_path}")
    print(f"   Instructions: {instructions}")
    print(f"   Image exists: {os.path.exists(image_path)}")
    
    try:
        print("\n🚀 Starting enhanced workflow...")
        result = await process_single_image_enhanced(image_path, instructions)
        
        print(f"\n✅ Workflow completed!")
        print(f"   Result keys: {list(result.keys())}")
        print(f"   QC Passed: {result.get('qc_passed', 'Unknown')}")
        print(f"   Quality Score: {result.get('quality_score', 'Unknown')}")
        print(f"   Final Image: {result.get('final_image', 'None')}")
        print(f"   Strategy: {result.get('editing_strategy', 'Unknown')}")
        print(f"   Error: {result.get('error', 'None')}")
        print(f"   Gemini Used: {result.get('gemini_used', 'Unknown')}")
        print(f"   ImageMagick Used: {result.get('imagemagick_used', 'Unknown')}")
        
        if result.get('final_image'):
            final_exists = os.path.exists(result['final_image'])
            print(f"   Final image exists: {final_exists}")
            if final_exists:
                size = os.path.getsize(result['final_image'])
                print(f"   Final image size: {size} bytes")
        
    except Exception as e:
        print(f"\n❌ Workflow failed with exception:")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        print(f"\n📋 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    # Check API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set")
        exit(1)
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set")
        exit(1)
        
    print("✅ API keys are set")
    
    asyncio.run(debug_workflow())