#!/usr/bin/env python3
"""Minimal test of chunked pipeline - process just 2 chunks"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.chunked_gemini_workflow import chunked_gemini_pipeline

async def test_minimal():
    """Test with minimal processing"""
    print("=" * 50)
    print("Minimal Chunked Pipeline Test")
    print("=" * 50)
    
    result = await chunked_gemini_pipeline(
        image_path="113Nurri Type L Chrome+Zebra.jpg",
        custom_instructions="Enhance chrome and wood textures",
        output_dir="/tmp"
    )
    
    print("\n✅ Pipeline Results:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    return result

if __name__ == "__main__":
    print("🚀 Running minimal chunked pipeline test...\n")
    result = asyncio.run(test_minimal())
    
    if result.get("success"):
        print("\n🎉 SUCCESS! Chunked pipeline is working!")
        print(f"Output saved to: {result.get('final_image')}")
    else:
        print("\n❌ Pipeline failed")