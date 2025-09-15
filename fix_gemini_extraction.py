#!/usr/bin/env python3
"""
Generate the fixed Gemini image extraction code
"""

fixed_extraction = '''
        # Extract image from response - Gemini 2.5 Flash Image returns inline_data
        image_saved = False
        
        if hasattr(response, 'candidates') and response.candidates:
            for idx, candidate in enumerate(response.candidates):
                print(f"DEBUG: Processing candidate {idx}")
                
                if not hasattr(candidate, 'content') or not candidate.content:
                    continue
                    
                content = candidate.content
                
                if not hasattr(content, 'parts') or not content.parts:
                    continue
                    
                for i, part in enumerate(content.parts):
                    print(f"DEBUG: Part {i} - checking for image data...")
                    
                    # Skip if no inline_data
                    if not hasattr(part, 'inline_data') or not part.inline_data:
                        if hasattr(part, 'text'):
                            print(f"DEBUG: Part {i} is text: {part.text[:100]}...")
                        continue
                    
                    # Found image data!
                    print(f"✅ Found edited image data ({part.inline_data.mime_type}, {len(part.inline_data.data)} bytes)")
                    
                    try:
                        # The data is already decoded binary image data, not base64!
                        image_data = part.inline_data.data
                        
                        # Validate image format
                        if len(image_data) >= 4:
                            if image_data[:4] == b'\\x89PNG':
                                print("📸 Valid PNG format detected")
                            elif image_data[:3] == b'\\xff\\xd8\\xff':
                                print("📸 Valid JPEG format detected") 
                            elif image_data[:4] == b'RIFF':
                                print("📸 Valid WebP format detected")
                            else:
                                print("⚠️  Unknown image format, saving anyway")
                        
                        print(f"💾 Processing edited image ({len(image_data)} bytes)...")
                        
                        # Load the edited image
                        from PIL import Image
                        import io
                        edited_img = Image.open(io.BytesIO(image_data))
                        edited_width, edited_height = edited_img.size
                        
                        # Load original to get target resolution
                        original_img = Image.open(image_path)
                        original_width, original_height = original_img.size
                        
                        print(f"📐 Gemini output: {edited_width}x{edited_height}, Original: {original_width}x{original_height}")
                        
                        # Check if upscaling is needed (if resolution dropped by more than 10%)
                        if edited_width < original_width * 0.9 or edited_height < original_height * 0.9:
                            print(f"⬆️ Upscaling from {edited_width}x{edited_height} to {original_width}x{original_height}")
                            
                            # Simple Lanczos upscaling for now
                            edited_img = edited_img.resize(
                                (original_width, original_height), 
                                Image.Resampling.LANCZOS
                            )
                            print(f"✅ Upscaled to original resolution")
                        
                        # Save the final image
                        edited_img.save(output_path, 'WEBP', quality=95)
                        
                        # Verify the file was written
                        actual_file_size = os.path.getsize(output_path)
                        if actual_file_size > 0:
                            print(f"✅ Successfully saved: {Path(output_path).name} ({actual_file_size:,} bytes)")
                            image_saved = True
                            break  # Exit the parts loop
                        else:
                            print(f"❌ File write failed: file size is 0")
                            
                    except Exception as e:
                        print(f"❌ Error processing image: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                if image_saved:
                    break  # Exit the candidates loop
'''

print(fixed_extraction)