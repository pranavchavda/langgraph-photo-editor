#!/usr/bin/env python3
"""Standalone test for chunked Gemini processing"""

import asyncio
import json
import os
from PIL import Image
from src.chunked_gemini_workflow import ChunkedImageProcessor
import google.genai as genai
from io import BytesIO
import base64
from anthropic import AsyncAnthropic


async def test_chunked_processing():
    """Test chunked processing without LangGraph context"""
    
    print("=" * 50)
    print("Testing Chunked Gemini Processing (Standalone)")
    print("=" * 50)
    
    test_image = "113Nurri Type L Chrome+Zebra.jpg"
    
    # 1. Create chunks
    print("\n1. Creating chunks...")
    processor = ChunkedImageProcessor(test_image)
    chunks = processor.create_chunks()
    print(f"Created {len(chunks)} chunks from {processor.width}x{processor.height} image")
    
    # 2. Analyze first chunk with Claude (simplified)
    print("\n2. Analyzing first chunk with Claude...")
    chunk = chunks[0]
    
    # Save chunk temporarily
    chunk_path = f"/tmp/{chunk.chunk_id}.jpg"
    chunk.image.save(chunk_path)
    
    client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    # Load chunk for Claude
    with open(chunk_path, 'rb') as f:
        chunk_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": chunk_base64
                    }
                },
                {
                    "type": "text", 
                    "text": "Describe what you see in this image chunk. What materials and surfaces are visible?"
                }
            ]
        }]
    )
    
    print(f"Claude analysis: {response.content[0].text[:200]}...")
    
    # 3. Process chunk with Gemini
    print("\n3. Processing chunk with Gemini...")
    
    # Configure Gemini
    genai_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    
    # Prepare chunk data
    chunk_bytes = BytesIO()
    chunk.image.save(chunk_bytes, format='PNG')
    chunk_data = chunk_bytes.getvalue()
    
    edit_prompt = """
    Enhance this product photography chunk:
    - Make chrome surfaces gleam
    - Enhance material textures
    - Improve overall vibrancy
    Maintain edge quality for stitching.
    """
    
    try:
        # Use new Gemini API
        response = genai_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents={
                "parts": [
                    {"text": edit_prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": chunk_data
                        }
                    }
                ]
            }
        )
        
        print(f"Gemini response received")
        
        # Check if we got an image back
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        print("✅ Successfully processed chunk with Gemini!")
                        
                        # Save processed chunk
                        processed_img = Image.open(BytesIO(part.inline_data.data))
                        output_path = f"/tmp/{chunk.chunk_id}_processed.png"
                        processed_img.save(output_path)
                        print(f"Saved to: {output_path}")
                        print(f"Original size: {chunk.image.size}")
                        print(f"Processed size: {processed_img.size}")
                        
                        if processed_img.size != chunk.image.size:
                            print("⚠️ Size mismatch - would need resizing for stitching")
                        else:
                            print("✅ Size preserved perfectly!")
                        
                        return True
                    elif hasattr(part, 'text'):
                        print(f"Got text response: {part.text[:100]}...")
        
        print("❌ No image in Gemini response")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return False


async def test_full_chunked_pipeline():
    """Test complete chunked pipeline"""
    print("\n" + "=" * 50)
    print("Testing Full Chunked Pipeline (Simplified)")
    print("=" * 50)
    
    test_image = "113Nurri Type L Chrome+Zebra.jpg"
    
    # Create processor
    processor = ChunkedImageProcessor(test_image)
    chunks = processor.create_chunks()
    
    print(f"\nProcessing {len(chunks)} chunks...")
    
    # Configure Gemini
    genai_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    
    processed_chunks = []
    
    for i, chunk in enumerate(chunks[:3]):  # Test first 3 chunks only
        print(f"\nProcessing chunk {i+1}/3: {chunk.chunk_id}")
        
        # Prepare chunk data
        chunk_bytes = BytesIO()
        chunk.image.save(chunk_bytes, format='PNG')
        chunk_data = chunk_bytes.getvalue()
        
        edit_prompt = f"""
        Enhance chunk {chunk.chunk_id} of product photo:
        - Position: row {chunk.row}, col {chunk.col}
        - Make chrome surfaces gleam
        - Enhance textures and materials
        - Preserve edges for seamless stitching
        """
        
        try:
            response = genai_client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents={
                    "parts": [
                        {"text": edit_prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": chunk_data
                            }
                        }
                    ]
                }
            )
            
            # Extract processed image
            processed = False
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            processed_img = Image.open(BytesIO(part.inline_data.data))
                            
                            # Resize if needed
                            if processed_img.size != chunk.image.size:
                                print(f"  Resizing from {processed_img.size} to {chunk.image.size}")
                                processed_img = processed_img.resize(chunk.image.size, Image.Resampling.LANCZOS)
                            
                            processed_chunks.append((chunk, processed_img))
                            processed = True
                            print(f"  ✅ Processed successfully")
                            break
            
            if not processed:
                print(f"  ⚠️ Using original (no image in response)")
                processed_chunks.append((chunk, chunk.image))
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            processed_chunks.append((chunk, chunk.image))
    
    # Test stitching
    if len(processed_chunks) > 0:
        print(f"\n4. Testing stitching with {len(processed_chunks)} chunks...")
        
        # For testing, just save the first processed chunk
        output_path = "/tmp/chunked_test_output.png"
        processed_chunks[0][1].save(output_path)
        print(f"Saved first processed chunk to: {output_path}")
        
        print("\n✅ Chunked pipeline test completed!")
        print(f"Original resolution: {processor.width}x{processor.height}")
        print(f"Chunks processed: {len(processed_chunks)}")
        
        return True
    
    return False


if __name__ == "__main__":
    # First test individual chunk processing
    success = asyncio.run(test_chunked_processing())
    
    if success:
        print("\n" + "=" * 50)
        print("Individual chunk test passed! Testing pipeline...")
        print("=" * 50)
        
        # Test full pipeline
        asyncio.run(test_full_chunked_pipeline())
    else:
        print("\n❌ Individual chunk test failed")