#!/usr/bin/env python3
"""
Simplest possible fix for Gemini image extraction
"""

simple_extraction = '''
        # Extract image from response
        image_saved = False
        
        try:
            # Navigate through response structure
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                # Found image data!
                                print(f"✅ Found image: {part.inline_data.mime_type}")
                                
                                # Save it
                                from PIL import Image
                                import io
                                img = Image.open(io.BytesIO(part.inline_data.data))
                                img.save(output_path, 'WEBP', quality=95)
                                
                                print(f"✅ Saved to: {output_path}")
                                image_saved = True
                                break
                    if image_saved:
                        break
        except Exception as e:
            print(f"❌ Error extracting image: {e}")
'''

print("This simplified extraction should work without indentation issues.")
print(simple_extraction)