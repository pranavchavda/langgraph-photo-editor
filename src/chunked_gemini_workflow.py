"""
Chunked Gemini Workflow
High-resolution image processing through intelligent chunking
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from PIL import Image
import math
from dataclasses import dataclass
import json

@dataclass
class ImageChunk:
    """Represents a single image chunk with metadata"""
    image: Image.Image
    row: int
    col: int
    x_start: int
    y_start: int
    width: int
    height: int
    chunk_id: str
    
    def to_dict(self):
        return {
            "chunk_id": self.chunk_id,
            "position": f"row_{self.row}_col_{self.col}",
            "coordinates": {
                "x": self.x_start,
                "y": self.y_start,
                "width": self.width,
                "height": self.height
            }
        }


class ChunkedImageProcessor:
    """Handles chunking and stitching of high-resolution images"""
    
    MAX_CHUNK_SIZE = 1080  # Gemini's effective limit
    OVERLAP_PIXELS = 50    # Overlap for seamless blending
    TARGET_4K_WIDTH = 3840  # Standard 4K width
    TARGET_4K_HEIGHT = 2160 # Standard 4K height
    GEMINI_OUTPUT_SIZE = 1024  # Gemini typically outputs ~1024px
    
    def __init__(self, image_path: str, target_4k: bool = False):
        self.image_path = image_path
        self.original_image = Image.open(image_path)
        self.original_width, self.original_height = self.original_image.size
        self.target_4k = target_4k
        
        # Calculate if we should use 4K mode
        megapixels = (self.original_width * self.original_height) / 1_000_000
        
        if target_4k and megapixels > 12:  # For images over 12MP
            # Calculate target dimensions maintaining aspect ratio
            aspect_ratio = self.original_width / self.original_height
            
            if aspect_ratio > (self.TARGET_4K_WIDTH / self.TARGET_4K_HEIGHT):
                # Width-constrained
                self.width = self.TARGET_4K_WIDTH
                self.height = int(self.TARGET_4K_WIDTH / aspect_ratio)
            else:
                # Height-constrained
                self.height = self.TARGET_4K_HEIGHT
                self.width = int(self.TARGET_4K_HEIGHT * aspect_ratio)
            
            print(f"📐 4K Mode: Downsampling {self.original_width}x{self.original_height} ({megapixels:.1f}MP) to {self.width}x{self.height} (4K)")
            
            # Create working image at 4K resolution
            self.working_image = self.original_image.resize(
                (self.width, self.height), 
                Image.Resampling.LANCZOS
            )
        else:
            # Use original resolution for smaller images
            self.width, self.height = self.original_width, self.original_height
            self.working_image = self.original_image
            
            if megapixels > 8:
                print(f"📐 Full Resolution Mode: Processing {self.width}x{self.height} ({megapixels:.1f}MP) at original size")
        
    def calculate_optimal_chunks(self) -> Tuple[int, int]:
        """Calculate optimal number of chunks to minimize seams"""
        if self.target_4k and self.width != self.original_width:
            # For 4K mode, optimize for Gemini's output size
            # Each chunk will be ~1024px after Gemini processing
            # So we want chunks that result in good coverage at 4K
            
            # Target 4-6 chunks for 4K width (3840px)
            chunks_x = max(2, min(4, math.ceil(self.width / 1000)))
            # Target 2-3 chunks for 4K height (2160px)  
            chunks_y = max(2, min(3, math.ceil(self.height / 1000)))
            
            print(f"  4K chunk layout: {chunks_x}x{chunks_y} = {chunks_x * chunks_y} chunks")
            print(f"  Each chunk ~{self.width//chunks_x}x{self.height//chunks_y}px → Gemini outputs ~1024px")
        else:
            # Standard calculation for full resolution
            chunks_x = math.ceil(self.width / self.MAX_CHUNK_SIZE)
            chunks_y = math.ceil(self.height / self.MAX_CHUNK_SIZE)
            
            # Adjust for better distribution
            chunk_width = self.width / chunks_x
            chunk_height = self.height / chunks_y
            
            # If chunks are too small, reduce count
            if chunk_width < 600:
                chunks_x = max(1, chunks_x - 1)
            if chunk_height < 600:
                chunks_y = max(1, chunks_y - 1)
            
        return chunks_x, chunks_y
    
    def create_chunks(self) -> List[ImageChunk]:
        """Split image into overlapping chunks"""
        chunks_x, chunks_y = self.calculate_optimal_chunks()
        
        # Calculate chunk dimensions
        base_chunk_width = self.width // chunks_x
        base_chunk_height = self.height // chunks_y
        
        chunks = []
        
        for row in range(chunks_y):
            for col in range(chunks_x):
                # Calculate logical grid position (where chunk belongs in final image)
                logical_x = col * base_chunk_width
                logical_y = row * base_chunk_height
                
                # Calculate extraction boundaries with overlap
                extract_x_start = max(0, logical_x - (self.OVERLAP_PIXELS if col > 0 else 0))
                extract_y_start = max(0, logical_y - (self.OVERLAP_PIXELS if row > 0 else 0))
                extract_x_end = min(self.width, logical_x + base_chunk_width + (self.OVERLAP_PIXELS if col < chunks_x - 1 else 0))
                extract_y_end = min(self.height, logical_y + base_chunk_height + (self.OVERLAP_PIXELS if row < chunks_y - 1 else 0))
                
                # Crop chunk from working image
                chunk_img = self.working_image.crop((extract_x_start, extract_y_start, extract_x_end, extract_y_end))
                
                # Ensure chunk maintains the same mode as source (RGBA if transparent)
                if self.working_image.mode == 'RGBA' and chunk_img.mode != 'RGBA':
                    chunk_img = chunk_img.convert('RGBA')
                
                # Create chunk object - store both logical position and actual extraction info
                chunk = ImageChunk(
                    image=chunk_img,
                    row=row,
                    col=col,
                    x_start=logical_x,  # Where to place this chunk in the final image
                    y_start=logical_y,
                    width=extract_x_end - extract_x_start,
                    height=extract_y_end - extract_y_start,
                    chunk_id=f"chunk_{row}_{col}"
                )
                
                chunks.append(chunk)
                
        return chunks
    
    def stitch_chunks(self, processed_chunks: List[Tuple[ImageChunk, Image.Image]]) -> Image.Image:
        """Intelligently stitch processed chunks back together with blending"""
        # Check if the original working image has alpha channel (transparency)
        # This is the most reliable indicator
        has_alpha = self.working_image.mode == 'RGBA'
        
        print(f"  Stitching: working_image mode={self.working_image.mode}, has_alpha={has_alpha}")
        
        # Create output image with appropriate mode
        if has_alpha:
            # Use transparent background for RGBA
            output = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            print(f"  Created RGBA output canvas with transparent background")
        else:
            output = Image.new('RGB', (self.width, self.height), (255, 255, 255))  # White background for RGB
            print(f"  Created RGB output canvas with white background")
        
        # Sort chunks by position for proper layering
        processed_chunks.sort(key=lambda x: (x[0].row, x[0].col))
        
        # Calculate base chunk dimensions for cropping
        chunks_x, chunks_y = self.calculate_optimal_chunks()
        base_chunk_width = self.width // chunks_x
        base_chunk_height = self.height // chunks_y
        
        for chunk_info, processed_img in processed_chunks:
            # Ensure processed image has correct mode
            if has_alpha and processed_img.mode != 'RGBA':
                processed_img = processed_img.convert('RGBA')
            elif not has_alpha and processed_img.mode == 'RGBA':
                # Convert RGBA to RGB with white background
                bg = Image.new('RGB', processed_img.size, (255, 255, 255))
                bg.paste(processed_img, mask=processed_img.split()[3] if len(processed_img.split()) > 3 else None)
                processed_img = bg
            
            # Crop to remove overlap and get the core chunk area
            # Calculate how much overlap to remove from each side
            left_crop = self.OVERLAP_PIXELS if chunk_info.col > 0 else 0
            top_crop = self.OVERLAP_PIXELS if chunk_info.row > 0 else 0
            
            # Calculate the core chunk size (without overlap)
            core_width = min(base_chunk_width, self.width - chunk_info.x_start)
            core_height = min(base_chunk_height, self.height - chunk_info.y_start)
            
            # Crop to get just the core area
            core_chunk = processed_img.crop((
                left_crop,
                top_crop,
                left_crop + core_width,
                top_crop + core_height
            ))
            
            # Paste at the logical grid position
            if has_alpha:
                output.paste(core_chunk, (chunk_info.x_start, chunk_info.y_start), core_chunk)
            else:
                output.paste(core_chunk, (chunk_info.x_start, chunk_info.y_start))
        
        # If we downsampled for 4K, optionally upscale back to original
        # (This is optional - we might want to keep the 4K version)
        if self.target_4k and output.size != (self.original_width, self.original_height):
            print(f"📏 Final output at 4K: {output.size}")
            # Don't upscale by default - 4K is the desired output
            # User can request original size if needed
        
        return output


async def chunk_aware_analysis_agent(
    image_path: str, 
    holistic_analysis: Dict[str, Any],
    custom_instructions: str = None
) -> Dict[str, Any]:
    """
    🔍 Chunk-Aware Analysis Agent (Standalone)
    Creates chunk-specific prompts based on holistic analysis
    """
    from anthropic import AsyncAnthropic
    import os
    
    processor = ChunkedImageProcessor(image_path)
    chunks = processor.create_chunks()
    
    # Get the holistic optimization goals
    holistic_strategy = holistic_analysis.get("gemini_instructions", "")
    optimization_priority = holistic_analysis.get("optimization_priority", [])
    surface_materials = holistic_analysis.get("surface_materials", [])
    
    chunk_prompts = []
    
    for chunk in chunks:
        # Save chunk as WebP to preserve transparency and reduce size
        chunk_path = f"/tmp/{chunk.chunk_id}.webp"
        chunk.image.save(chunk_path, 'WEBP', quality=95)
        
        # Create context-aware prompt for this chunk
        chunk_prompt = f"""
        You are analyzing chunk {chunk.chunk_id} (position: row {chunk.row}, col {chunk.col}) 
        of a larger product image that needs optimization.
        
        HOLISTIC VISION (from full image analysis):
        {holistic_strategy}
        
        Optimization priorities: {', '.join(optimization_priority)}
        Materials present: {', '.join(surface_materials)}
        
        This chunk represents coordinates ({chunk.x_start}, {chunk.y_start}) to 
        ({chunk.x_start + chunk.width}, {chunk.y_start + chunk.height}) of the full image.
        
        Create specific editing instructions for THIS CHUNK that:
        1. Contributes to the overall optimization goals
        2. Maintains consistency with adjacent chunks
        3. Focuses on the specific content visible in this chunk
        4. Preserves edge quality for seamless stitching
        
        Consider:
        - What specific elements are visible in this chunk?
        - How should they be enhanced to match the holistic vision?
        - What adjustments are needed for this specific region?
        
        Return a JSON with:
        - chunk_id: "{chunk.chunk_id}"
        - visible_elements: [what you see in this chunk]
        - gemini_instructions: "specific instructions for this chunk"
        - edge_handling: "how to handle edges for seamless blending"
        - consistency_notes: "what to maintain for consistency with other chunks"
        """
        
        # Get chunk-specific analysis
        client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Load chunk image
        with open(chunk_path, 'rb') as f:
            import base64
            chunk_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Use WebP media type since we save chunks as WebP
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=800,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/webp",  # Chunks are saved as WebP
                            "data": chunk_base64
                        }
                    },
                    {"type": "text", "text": chunk_prompt}
                ]
            }]
        )
        
        # Parse response
        try:
            chunk_analysis = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown
            text = response.content[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            # Clean up common JSON issues
            text = text.strip()
            # Replace newlines in string values
            import re
            text = re.sub(r'"\s*:\s*"[^"]*\n[^"]*"', lambda m: m.group(0).replace('\n', ' '), text)
            try:
                chunk_analysis = json.loads(text)
            except json.JSONDecodeError:
                # Fallback to default analysis
                chunk_analysis = {
                    "chunk_id": chunk.chunk_id,
                    "visible_elements": ["Product portion"],
                    "gemini_instructions": f"Enhance chunk {chunk.chunk_id} with improved vibrancy and sharpness",
                    "edge_handling": "Preserve edges for seamless blending",
                    "consistency_notes": "Maintain color and brightness consistency"
                }
        chunk_analysis["chunk_metadata"] = chunk.to_dict()
        chunk_prompts.append(chunk_analysis)
        
        # Clean up temp file
        Path(chunk_path).unlink()
    
    return {
        "chunks_count": len(chunks),
        "chunks_layout": f"{processor.calculate_optimal_chunks()[0]}x{processor.calculate_optimal_chunks()[1]}",
        "chunk_analyses": chunk_prompts,
        "holistic_context": holistic_analysis,
        "processing_strategy": "chunked_gemini"
    }


async def process_chunk_with_gemini(
    chunk: ImageChunk,
    chunk_analysis: Dict[str, Any],
    holistic_context: Dict[str, Any]
) -> Image.Image:
    """
    🎨 Process individual chunk with Gemini
    """
    import google.generativeai as genai
    from io import BytesIO
    import os
    import numpy as np
    
    # Check if chunk is mostly transparent/empty
    if chunk.image.mode == 'RGBA':
        # Convert to numpy array to analyze alpha channel
        img_array = np.array(chunk.image)
        alpha_channel = img_array[:, :, 3]
        
        # Calculate percentage of transparent pixels (alpha < 10)
        transparent_pixels = np.sum(alpha_channel < 10)
        total_pixels = alpha_channel.size
        transparency_percentage = (transparent_pixels / total_pixels) * 100
        
        if transparency_percentage > 90:
            print(f"  ⏩ Skipping chunk {chunk.chunk_id} - {transparency_percentage:.1f}% transparent")
            return chunk.image  # Return original transparent chunk
    
    # Configure Gemini
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
    
    # Save chunk for processing as WebP
    chunk_bytes = BytesIO()
    chunk.image.save(chunk_bytes, format='WEBP', quality=95)
    chunk_data = chunk_bytes.getvalue()
    
    # Create prompt with full context
    edit_prompt = f"""
    CRITICAL: You are editing chunk {chunk.chunk_id} of a larger image.
    
    HOLISTIC VISION:
    {holistic_context.get('gemini_instructions', '')}
    
    CHUNK-SPECIFIC INSTRUCTIONS:
    {chunk_analysis.get('gemini_instructions', '')}
    
    EDGE HANDLING:
    {chunk_analysis.get('edge_handling', 'Preserve edges for seamless blending')}
    
    CONSISTENCY REQUIREMENTS:
    {chunk_analysis.get('consistency_notes', '')}
    
    CRITICAL REQUIREMENTS:
    1. DO NOT change overall brightness or exposure - maintain the same levels as input
    2. DO NOT alter the background - if transparent, keep transparent; if white, keep white
    3. DO NOT add or generate new content - only enhance what exists
    4. If the chunk is mostly empty/transparent, return it unchanged
    5. Focus ONLY on enhancing existing product details (chrome shine, texture clarity)
    6. Preserve EXACT edge pixels without any modification for seamless stitching
    7. Return at EXACTLY {chunk.width}x{chunk.height} pixels
    
    TRANSPARENCY RULE: If you see transparent/empty areas, they MUST remain transparent/empty.
    Never fill empty space with new content or patterns.
    
    Remember: You're editing part of a larger image. Dramatic changes will create visible seams.
    Apply subtle, consistent enhancements only to existing product elements.
    """
    
    # Send to Gemini
    response = model.generate_content([
        edit_prompt,
        {
            "mime_type": "image/webp",
            "data": chunk_data
        }
    ])
    
    # Extract processed chunk
    if response.candidates and len(response.candidates) > 0:
        candidate = response.candidates[0]
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    try:
                        # Load processed chunk
                        processed_img = Image.open(BytesIO(part.inline_data.data))
                        
                        # Ensure dimensions match
                        if processed_img.size != chunk.image.size:
                            print(f"  ⚠️ Chunk {chunk.chunk_id} resized from {processed_img.size} to {chunk.image.size}")
                            processed_img = processed_img.resize(chunk.image.size, Image.Resampling.LANCZOS)
                        
                        # Ensure mode matches source
                        if chunk.image.mode == 'RGBA' and processed_img.mode != 'RGBA':
                            processed_img = processed_img.convert('RGBA')
                        
                        return processed_img
                    except Exception as e:
                        print(f"  ❌ Error loading chunk {chunk.chunk_id}: {e}")
                        return chunk.image
    
    # Fallback to original if processing fails
    print(f"  ⚠️ No image returned for chunk {chunk.chunk_id}, using original")
    return chunk.image


async def standalone_background_removal(image_path: str) -> str:
    """
    🖼️ Standalone Background Removal Agent
    Removes background using remove.bg API without LangGraph context
    """
    import os
    import requests
    import subprocess
    
    api_key = os.getenv('REMOVE_BG_API_KEY')
    if not api_key:
        print("⚠️ REMOVE_BG_API_KEY not set, skipping background removal")
        return image_path
    
    try:
        print(f"  Calling remove.bg API...")
        
        # Call remove.bg API
        with open(image_path, 'rb') as image_file:
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': image_file},
                data={'size': 'full', 'format': 'png'},
                headers={'X-Api-Key': api_key},
                timeout=60
            )
        
        if response.status_code != 200:
            print(f"  ❌ Remove.bg API error: {response.status_code}")
            return image_path
        
        # Save PNG with transparent background
        png_path = str(Path(image_path).parent / f"{Path(image_path).stem}-no-bg.png")
        with open(png_path, 'wb') as out_file:
            out_file.write(response.content)
        
        print(f"  ✅ Background removed, saved as PNG")
        
        # Try to convert to WebP if ImageMagick is available
        webp_path = str(Path(image_path).parent / f"{Path(image_path).stem}-no-bg.webp")
        try:
            # Check if ImageMagick is available
            result = subprocess.run(["magick", "--version"], capture_output=True)
            if result.returncode == 0:
                # Convert PNG to WebP
                cmd = ["magick", png_path, "-quality", "95", webp_path]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print(f"  ✅ Converted to WebP")
                    # Remove temporary PNG
                    os.remove(png_path)
                    return webp_path
        except:
            pass
        
        # Return PNG if WebP conversion failed
        return png_path
        
    except Exception as e:
        print(f"  ❌ Background removal error: {e}")
        return image_path


async def standalone_analysis_agent(image_path: str, custom_instructions: str = None) -> Dict[str, Any]:
    """
    🔍 Standalone Analysis Agent for Chunked Pipeline
    Analyzes image without LangGraph context
    """
    from anthropic import AsyncAnthropic
    import os
    import base64
    
    client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    # Load and encode image
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # Detect correct media type
    if image_path.lower().endswith('.png'):
        media_type = "image/png"
    elif image_path.lower().endswith('.webp'):
        media_type = "image/webp"
    elif image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
        media_type = "image/jpeg"
    else:
        # Default to PNG for unknown types
        media_type = "image/png"
    
    analysis_prompt = f"""
    Analyze this product image for e-commerce optimization.
    
    {custom_instructions if custom_instructions else ''}
    
    Return a JSON with:
    - gemini_instructions: "specific editing instructions for Gemini"
    - optimization_priority: ["list of priorities"]
    - surface_materials: ["detected materials"]
    - needs_cropping: boolean
    - remove_background: boolean
    """
    
    response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_base64
                    }
                },
                {"type": "text", "text": analysis_prompt}
            ]
        }]
    )
    
    # Parse response
    import json
    text = response.content[0].text
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    
    return json.loads(text)


async def chunked_gemini_pipeline(
    image_path: str,
    custom_instructions: str = None,
    output_dir: str = None,
    target_4k: bool = True,
    remove_background: bool = True
) -> Dict[str, Any]:
    """
    📊 Complete Chunked Gemini Pipeline (Standalone)
    
    Args:
        image_path: Path to input image
        custom_instructions: User instructions for editing
        output_dir: Output directory for results
        target_4k: If True, downsample very large images to 4K for processing
        remove_background: If True, remove background before processing
    """
    
    # Stage 1: Remove Background FIRST (on full resolution image)
    current_image = image_path
    if remove_background:
        print("🖼️ Stage 1: Removing Background")
        bg_removed_path = await standalone_background_removal(current_image)
        if bg_removed_path and bg_removed_path != current_image:
            current_image = bg_removed_path
            print(f"✅ Background removed: {Path(bg_removed_path).name}")
        else:
            print("⚠️ Background removal skipped or failed, continuing with original")
    
    # Stage 2: Holistic Analysis (on bg-removed image if applicable)
    print("🔍 Stage 2: Holistic Analysis")
    holistic_analysis = await standalone_analysis_agent(current_image, custom_instructions)
    
    print(f"📊 Analysis complete: {len(holistic_analysis.get('optimization_priority', []))} priorities identified")
    
    # Stage 3: Chunk-Aware Re-Analysis
    print("🔄 Stage 3: Chunk-Aware Analysis")
    chunk_analysis = await chunk_aware_analysis_agent(current_image, holistic_analysis, custom_instructions)
    
    # Stage 4: Process Chunks
    print(f"🎨 Stage 4: Processing chunks with Gemini")
    processor = ChunkedImageProcessor(current_image, target_4k=target_4k)
    chunks = processor.create_chunks()
    
    # Process all chunks (remove test limit)
    print(f"  Processing {len(chunks)} chunks")
    
    # Ensure we have analysis for all chunks
    chunk_analyses = chunk_analysis.get('chunk_analyses', [])
    if len(chunk_analyses) < len(chunks):
        print(f"  ⚠️ Only {len(chunk_analyses)} analyses for {len(chunks)} chunks, using defaults for remaining")
        # Create default analysis for missing chunks
        while len(chunk_analyses) < len(chunks):
            chunk_analyses.append({
                "gemini_instructions": "Enhance this chunk with improved vibrancy and clarity",
                "edge_handling": "Preserve edges for seamless blending",
                "consistency_notes": "Maintain consistency with other chunks"
            })
    
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        chunk_prompt = chunk_analyses[i] if i < len(chunk_analyses) else chunk_analyses[-1]
        print(f"  Processing chunk {i+1}/{len(chunks)}: {chunk.chunk_id}")
        processed_img = await process_chunk_with_gemini(chunk, chunk_prompt, holistic_analysis)
        processed_chunks.append((chunk, processed_img))
    
    # Stage 5: Stitch chunks
    print("🧩 Stage 5: Stitching chunks")
    # For partial processing, fill in unprocessed chunks with originals
    all_chunks_processed = []
    processed_ids = {c.chunk_id for c, _ in processed_chunks}
    
    for chunk in chunks:
        if chunk.chunk_id in processed_ids:
            # Find the processed version
            for pc, pi in processed_chunks:
                if pc.chunk_id == chunk.chunk_id:
                    all_chunks_processed.append((chunk, pi))
                    break
        else:
            # Use original for unprocessed chunks
            all_chunks_processed.append((chunk, chunk.image))
    
    final_image = processor.stitch_chunks(all_chunks_processed)
    
    # Save output
    output_path = output_dir or Path(image_path).parent
    final_path = Path(output_path) / f"{Path(image_path).stem}-chunked-gemini.webp"
    final_image.save(final_path, 'WEBP', quality=95)
    
    # Stage 6: Quality Check (simplified for standalone)
    print("✅ Stage 6: Quality Check")
    # For now, skip QC in standalone pipeline
    qc_result = {"quality_score": "Pending manual review"}
    
    return {
        "success": True,
        "final_image": str(final_path),
        "chunks_processed": len(processed_chunks),
        "total_chunks": len(chunks),
        "quality_score": qc_result.get("quality_score", "N/A"),
        "processing_method": "chunked_gemini",
        "original_resolution": (processor.original_width, processor.original_height),
        "working_resolution": (processor.width, processor.height),
        "final_resolution": final_image.size,
        "used_4k_mode": processor.target_4k and (processor.width != processor.original_width)
    }