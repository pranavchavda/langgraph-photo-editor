#!/usr/bin/env python3
"""Test Gemini output resolution vs input resolution"""

import os
from PIL import Image
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_gemini_resolution(image_path):
    """Test the resolution of Gemini edited images"""
    
    # Configure Gemini
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
    
    # Load original image
    original = Image.open(image_path)
    original_width, original_height = original.size
    original_pixels = original_width * original_height
    
    print(f"Original image: {Path(image_path).name}")
    print(f"  Resolution: {original_width}x{original_height}")
    print(f"  Total pixels: {original_pixels:,}")
    print(f"  Megapixels: {original_pixels/1_000_000:.2f} MP")
    
    # Prepare image for Gemini
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Simple edit request
    prompt = """
    Make this image slightly brighter and more vibrant.
    CRITICAL: Preserve the original resolution and image quality.
    Return the FULL resolution image.
    """
    
    print("\nSending to Gemini 2.5 Flash Image Preview...")
    
    # Send to Gemini
    response = model.generate_content([
        prompt,
        {
            "mime_type": "image/jpeg",
            "data": image_data
        }
    ])
    
    # Extract edited image
    if response.candidates and len(response.candidates) > 0:
        candidate = response.candidates[0]
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    edited_data = part.inline_data.data
                    
                    # Save and check edited image
                    output_path = f"/tmp/gemini_resolution_test.jpg"
                    with open(output_path, 'wb') as f:
                        f.write(edited_data)
                    
                    # Check edited resolution
                    edited = Image.open(output_path)
                    edited_width, edited_height = edited.size
                    edited_pixels = edited_width * edited_height
                    
                    print(f"\nEdited image saved to: {output_path}")
                    print(f"  Resolution: {edited_width}x{edited_height}")
                    print(f"  Total pixels: {edited_pixels:,}")
                    print(f"  Megapixels: {edited_pixels/1_000_000:.2f} MP")
                    
                    # Calculate reduction
                    reduction_percent = ((original_pixels - edited_pixels) / original_pixels) * 100
                    print(f"\n📊 Resolution change: {reduction_percent:.1f}% {'reduction' if reduction_percent > 0 else 'increase'}")
                    
                    if edited_width != original_width or edited_height != original_height:
                        print(f"⚠️  WARNING: Resolution changed from {original_width}x{original_height} to {edited_width}x{edited_height}")
                        
                        # Calculate scale factors
                        scale_w = edited_width / original_width
                        scale_h = edited_height / original_height
                        print(f"  Scale factors: {scale_w:.3f}x width, {scale_h:.3f}x height")
                    else:
                        print("✅ Resolution preserved!")
                    
                    return edited_width, edited_height

if __name__ == "__main__":
    # Test with the Nurri espresso image
    test_image = "/home/pranav/langgraph-photo-editor/113Nurri Type L Chrome+Zebra.jpg"
    
    if os.path.exists(test_image):
        test_gemini_resolution(test_image)
    else:
        print(f"Test image not found: {test_image}")
        print("Using any available test image...")
        
        # Find any image in the directory
        for file in Path(".").glob("*.jpg"):
            print(f"Testing with: {file}")
            test_gemini_resolution(str(file))
            break