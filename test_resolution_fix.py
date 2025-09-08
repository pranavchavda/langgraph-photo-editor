#!/usr/bin/env python3
"""Test the resolution preservation fix in Gemini agent"""

import asyncio
from PIL import Image

async def test_resolution_fix():
    """Test if the resolution is preserved after Gemini editing"""
    from src.agents_enhanced import gemini_edit_agent, set_stream_writer
    
    # Set up a simple writer for the agent
    def writer(msg):
        if msg.get("status") or msg.get("message"):
            print(f"  [{msg.get('agent', 'agent')}] {msg.get('message', '')}")
    
    set_stream_writer(writer)
    
    # Test image
    test_image = "/home/pranav/langgraph-photo-editor/113Nurri Type L Chrome+Zebra.jpg"
    
    # Get original dimensions
    original = Image.open(test_image)
    original_width, original_height = original.size
    print(f"Original image: {test_image}")
    print(f"  Resolution: {original_width}x{original_height}")
    print(f"  Megapixels: {(original_width * original_height) / 1_000_000:.2f} MP\n")
    
    # Create test analysis with Gemini instructions
    analysis = {
        "gemini_instructions": "Make the image slightly brighter and enhance the chrome surfaces",
        "needs_dust_removal": False,
        "dust_issues": []
    }
    
    print("Running Gemini edit agent with upscaling fix...")
    
    # Run the agent
    result = await gemini_edit_agent(test_image, analysis)
    
    # Check the result
    print(f"\nResult path: {result}")
    
    # Check final dimensions
    if result:
        final = Image.open(result)
        final_width, final_height = final.size
        print(f"\nFinal image: {result}")
        print(f"  Resolution: {final_width}x{final_height}")
        print(f"  Megapixels: {(final_width * final_height) / 1_000_000:.2f} MP")
        
        if final_width == original_width and final_height == original_height:
            print("\n✅ SUCCESS: Resolution preserved!")
        else:
            print(f"\n⚠️  WARNING: Resolution changed from {original_width}x{original_height} to {final_width}x{final_height}")

if __name__ == "__main__":
    asyncio.run(test_resolution_fix())