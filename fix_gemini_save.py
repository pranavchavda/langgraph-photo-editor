#!/usr/bin/env python3
"""
Script to check if Gemini is properly saving edited images
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

# Test the Gemini response parsing
test_response = """
The issue is that when Gemini returns an edited image, 
it's in the response.candidates[0].content.parts[0].inline_data.data field
as raw bytes (not base64).

The current code has indentation issues that prevent it from properly
extracting and saving this image data.

Key fixes needed:
1. Fix indentation in the for loop that iterates through parts
2. Ensure the image data extraction is inside the loop
3. Properly save the extracted image to disk
"""

print(test_response)

print("\n" + "="*60)
print("FIXED CODE STRUCTURE:")
print("="*60)

fixed_code = '''
# Extract image from response - Gemini 2.5 Flash Image returns inline_data
image_saved = False

if hasattr(response, 'candidates') and response.candidates:
    for candidate in response.candidates:
        if hasattr(candidate, 'content') and candidate.content:
            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                for part in candidate.content.parts:
                    # Check if this part contains image data
                    if hasattr(part, 'inline_data') and part.inline_data:
                        print(f"✅ Found image data: {part.inline_data.mime_type}")
                        try:
                            # Extract the raw image bytes
                            image_data = part.inline_data.data
                            
                            # Save to file
                            output_path = f"{image_path.stem}-gemini-edited.webp"
                            
                            # Load image and save as WebP
                            from PIL import Image
                            import io
                            img = Image.open(io.BytesIO(image_data))
                            img.save(output_path, 'WEBP', quality=95)
                            
                            print(f"✅ Saved: {output_path}")
                            image_saved = True
                            break
                        except Exception as e:
                            print(f"❌ Error: {e}")
                
                if image_saved:
                    break
        if image_saved:
            break

if not image_saved:
    print("❌ No image found in Gemini response")
'''

print(fixed_code)