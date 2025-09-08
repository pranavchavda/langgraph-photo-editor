#!/usr/bin/env python3
"""Simple test for chunked processing using existing working Gemini config"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image
from src.chunked_gemini_workflow import ChunkedImageProcessor
import google.genai as genai
from io import BytesIO


def test_working_gemini():
    """Test that regular Gemini still works"""
    print("Testing existing Gemini configuration...")
    
    # Use the existing working configuration
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
    
    # Test with small image
    test_img = Image.new('RGB', (512, 512), color='white')
    img_bytes = BytesIO()
    test_img.save(img_bytes, format='PNG')
    img_data = img_bytes.getvalue()
    
    try:
        response = model.generate_content([
            "Describe this image",
            {
                "mime_type": "image/png",
                "data": img_data
            }
        ])
        
        print(f"✅ Gemini working: {response.text[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return False


def test_chunking_only():
    """Test just the chunking logic"""
    print("\n" + "=" * 50)
    print("Testing Chunking Implementation")
    print("=" * 50)
    
    test_image = "113Nurri Type L Chrome+Zebra.jpg"
    
    # Test chunking
    processor = ChunkedImageProcessor(test_image)
    chunks = processor.create_chunks()
    
    print(f"Original: {processor.width}x{processor.height} = {(processor.width * processor.height) / 1_000_000:.2f} MP")
    print(f"Created {len(chunks)} chunks")
    
    # Test coverage
    total_pixels = 0
    for chunk in chunks:
        pixels = chunk.width * chunk.height
        total_pixels += pixels
        print(f"  {chunk.chunk_id}: {chunk.width}x{chunk.height} = {pixels/1_000_000:.2f} MP at ({chunk.x_start}, {chunk.y_start})")
    
    print(f"\nTotal chunk pixels: {total_pixels/1_000_000:.2f} MP")
    print(f"With overlap factor: {total_pixels / (processor.width * processor.height):.2f}x")
    
    # Test stitching with original chunks
    print("\nTesting stitching with unprocessed chunks...")
    chunks_with_originals = [(chunk, chunk.image) for chunk in chunks]
    stitched = processor.stitch_chunks(chunks_with_originals)
    
    if stitched.size == (processor.width, processor.height):
        print(f"✅ Stitching successful: {stitched.size}")
        # Save for inspection
        stitched.save("/tmp/test_stitch_original.jpg")
        print("Saved to: /tmp/test_stitch_original.jpg")
    else:
        print(f"❌ Size mismatch: {stitched.size} vs {(processor.width, processor.height)}")
    
    return True


def test_single_chunk_gemini():
    """Test processing a single chunk with working Gemini"""
    print("\n" + "=" * 50)
    print("Testing Single Chunk with Gemini")
    print("=" * 50)
    
    test_image = "113Nurri Type L Chrome+Zebra.jpg"
    
    # Get middle chunk (more interesting content)
    processor = ChunkedImageProcessor(test_image)
    chunks = processor.create_chunks()
    
    # Pick a middle chunk
    middle_chunk = chunks[len(chunks)//2]
    print(f"Testing chunk: {middle_chunk.chunk_id}")
    print(f"Position: ({middle_chunk.x_start}, {middle_chunk.y_start})")
    print(f"Size: {middle_chunk.width}x{middle_chunk.height}")
    
    # Configure Gemini
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
    
    # Prepare chunk
    chunk_bytes = BytesIO()
    middle_chunk.image.save(chunk_bytes, format='PNG')
    chunk_data = chunk_bytes.getvalue()
    
    edit_prompt = """
    Enhance this product photo chunk:
    - Make chrome surfaces gleam
    - Enhance textures
    - Improve vibrancy
    CRITICAL: Return at EXACTLY the same dimensions.
    """
    
    try:
        print("Sending to Gemini...")
        response = model.generate_content([
            edit_prompt,
            {
                "mime_type": "image/png",
                "data": chunk_data
            }
        ])
        
        # Check for image in response
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        print("✅ Got edited image from Gemini!")
                        
                        # Load and check
                        edited_img = Image.open(BytesIO(part.inline_data.data))
                        print(f"Original chunk size: {middle_chunk.image.size}")
                        print(f"Edited chunk size: {edited_img.size}")
                        
                        if edited_img.size != middle_chunk.image.size:
                            print("⚠️ Size changed - resizing...")
                            edited_img = edited_img.resize(middle_chunk.image.size, Image.Resampling.LANCZOS)
                        
                        # Save for inspection
                        edited_img.save(f"/tmp/{middle_chunk.chunk_id}_edited.png")
                        print(f"Saved to: /tmp/{middle_chunk.chunk_id}_edited.png")
                        
                        return True
                    elif hasattr(part, 'text'):
                        print(f"Text response: {part.text[:200]}...")
        
        print("❌ No image in response")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test 1: Verify Gemini works
    if not test_working_gemini():
        print("\n⚠️ Gemini not working, check API key")
        sys.exit(1)
    
    # Test 2: Chunking logic
    if not test_chunking_only():
        print("\n⚠️ Chunking failed")
        sys.exit(1)
    
    # Test 3: Single chunk with Gemini
    if test_single_chunk_gemini():
        print("\n✅ All tests passed! Ready for full pipeline.")
    else:
        print("\n⚠️ Gemini chunk processing needs work")