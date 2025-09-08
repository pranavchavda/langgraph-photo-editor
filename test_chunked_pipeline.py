#!/usr/bin/env python3
"""Test the chunked Gemini pipeline"""

import asyncio
from PIL import Image
from src.chunked_gemini_workflow import ChunkedImageProcessor, chunked_gemini_pipeline

def test_chunking():
    """Test the chunking logic"""
    print("=" * 50)
    print("Testing Chunking Logic")
    print("=" * 50)
    
    test_image = "113Nurri Type L Chrome+Zebra.jpg"
    
    # Load image
    img = Image.open(test_image)
    print(f"Image: {test_image}")
    print(f"Resolution: {img.size[0]}x{img.size[1]}")
    print(f"Megapixels: {(img.size[0] * img.size[1]) / 1_000_000:.2f} MP")
    
    # Test chunking
    processor = ChunkedImageProcessor(test_image)
    chunks_x, chunks_y = processor.calculate_optimal_chunks()
    
    print(f"\nOptimal chunk layout: {chunks_x}x{chunks_y} = {chunks_x * chunks_y} chunks")
    print(f"Max chunk size: {processor.MAX_CHUNK_SIZE}px")
    print(f"Overlap: {processor.OVERLAP_PIXELS}px")
    
    # Create chunks
    chunks = processor.create_chunks()
    print(f"\nCreated {len(chunks)} chunks:")
    
    for chunk in chunks:
        print(f"  {chunk.chunk_id}: {chunk.width}x{chunk.height} at ({chunk.x_start}, {chunk.y_start})")
    
    # Test if chunks cover the entire image
    coverage_map = set()
    for chunk in chunks:
        for x in range(chunk.x_start, chunk.x_start + chunk.width):
            for y in range(chunk.y_start, chunk.y_start + chunk.height):
                coverage_map.add((x, y))
    
    expected_pixels = img.size[0] * img.size[1]
    covered_pixels = len(coverage_map)
    coverage_percent = (covered_pixels / expected_pixels) * 100
    
    print(f"\nCoverage test: {coverage_percent:.1f}% of image covered")
    if coverage_percent >= 100:
        print("✅ Full image coverage achieved!")
    else:
        print(f"⚠️ Missing coverage: {100 - coverage_percent:.1f}%")


async def test_full_pipeline():
    """Test the complete chunked pipeline"""
    print("\n" + "=" * 50)
    print("Testing Full Chunked Pipeline")
    print("=" * 50)
    
    test_image = "113Nurri Type L Chrome+Zebra.jpg"
    
    # Test with sample instructions
    instructions = """
    Enhance this espresso machine for professional e-commerce.
    Make the chrome surfaces gleam and the wood grain rich.
    Increase overall vibrancy and professional appearance.
    """
    
    print(f"Image: {test_image}")
    print(f"Instructions: {instructions[:100]}...")
    
    try:
        result = await chunked_gemini_pipeline(
            image_path=test_image,
            custom_instructions=instructions,
            output_dir="/tmp"
        )
        
        print(f"\n✅ Pipeline completed successfully!")
        print(f"Output: {result.get('final_image')}")
        print(f"Chunks processed: {result.get('chunks_processed')}")
        print(f"Quality score: {result.get('quality_score')}")
        print(f"Original resolution: {result.get('original_resolution')}")
        print(f"Final resolution: {result.get('final_resolution')}")
        
        # Check resolution preservation
        if result.get('original_resolution') == result.get('final_resolution'):
            print("\n✅ Resolution perfectly preserved!")
        else:
            print(f"\n⚠️ Resolution changed from {result.get('original_resolution')} to {result.get('final_resolution')}")
            
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Test chunking logic
    test_chunking()
    
    # Test full pipeline automatically
    print("\nRunning full pipeline test...")
    asyncio.run(test_full_pipeline())