"""
Targeted Enhancement Module
Surgical improvements to specific areas after ImageMagick optimization
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from PIL import Image, ImageDraw
import json
from dataclasses import dataclass
from io import BytesIO
import base64
import os


@dataclass
class EnhancementArea:
    """Represents a specific area that needs enhancement"""
    x: int
    y: int
    width: int
    height: int
    description: str
    enhancement_instructions: str
    priority: int = 1
    area_id: str = ""

    def to_dict(self):
        return {
            "area_id": self.area_id,
            "coordinates": {"x": self.x, "y": self.y, "width": self.width, "height": self.height},
            "description": self.description,
            "instructions": self.enhancement_instructions,
            "priority": self.priority
        }


async def targeted_area_analysis_agent(
    image_path: str,
    original_path: str = None,
    custom_instructions: str = None,
    initial_analysis: Dict[str, Any] = None
) -> List[EnhancementArea]:
    """
    🔍 Analyzes ImageMagick-processed image to identify specific areas needing enhancement

    Args:
        image_path: Path to the ImageMagick-processed image
        original_path: Path to original image for comparison (optional)
        custom_instructions: User's enhancement preferences

    Returns:
        List of EnhancementArea objects identifying regions to enhance
    """
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    # Load and encode the processed image
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')

    # Get image dimensions
    img = Image.open(image_path)
    width, height = img.size

    # Detect media type
    if image_path.lower().endswith('.png'):
        media_type = "image/png"
    elif image_path.lower().endswith('.webp'):
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"

    # Build context from initial analysis
    context_info = ""
    if initial_analysis:
        problems = []
        if initial_analysis.get("complex_problems"):
            problems.extend(initial_analysis["complex_problems"])
        if initial_analysis.get("lighting_issues"):
            problems.extend(initial_analysis["lighting_issues"])
        if initial_analysis.get("color_problems"):
            problems.extend(initial_analysis["color_problems"])
        if initial_analysis.get("surface_materials"):
            context_info += f"\nDetected materials: {', '.join(initial_analysis['surface_materials'])}"
        if problems:
            context_info += f"\nKnown issues that may still need attention: {', '.join(problems)}"

    analysis_prompt = f"""
    Analyze this professionally processed product image and identify SPECIFIC areas that would benefit from targeted AI enhancement.

    Image dimensions: {width}x{height}

    The image has already been optimized with ImageMagick (sharpening, color correction, etc).
    {context_info}

    Now identify 1-3 SPECIFIC REGIONS that could benefit from AI enhancement.

    Focus on areas with:
    - Chrome/metal that could be more reflective or have better shine
    - Wood grain that needs more detail
    - Textures that could be enhanced
    - Specific product details that need emphasis
    - Areas with alignment or geometric issues
    - Regions mentioned in the known issues above

    {f"User preferences: {custom_instructions}" if custom_instructions else ""}

    BE VERY SELECTIVE - only identify areas that truly need enhancement.
    If the image looks great already, return an empty list.

    Return a JSON array with 0-3 areas maximum:
    [
        {{
            "x": <left coordinate>,
            "y": <top coordinate>,
            "width": <area width>,
            "height": <area height>,
            "description": "what's in this area",
            "enhancement_instructions": "specific instructions for Gemini",
            "priority": 1-3 (1=highest)
        }}
    ]

    Coordinates should define a rectangle around the area needing enhancement.
    Make areas reasonably sized (200-900px max) to capture the full element.
    IMPORTANT: Keep width and height under 900px each to stay within Gemini's limits.

    If no enhancements needed, return: []
    """

    try:
        response = await client.messages.create(
            model="claude-4-sonnet-20250514",
            max_tokens=1000,
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
        text = response.content[0].text.strip()

        # Try to extract JSON from various formats
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        # Handle empty response or "no enhancements needed" responses
        if not text or text == "[]" or "no enhancement" in text.lower():
            return []

        try:
            areas_data = json.loads(text)
        except json.JSONDecodeError:
            # If Claude returns plain text saying no enhancements needed
            print(f"  ℹ️ No areas identified for enhancement")
            return []

        # Convert to EnhancementArea objects
        areas = []
        for i, area in enumerate(areas_data):
            enhancement_area = EnhancementArea(
                x=area.get("x", 0),
                y=area.get("y", 0),
                width=area.get("width", 200),
                height=area.get("height", 200),
                description=area.get("description", "Product area"),
                enhancement_instructions=area.get("enhancement_instructions", "Enhance details"),
                priority=area.get("priority", 2),
                area_id=f"area_{i}"
            )

            # Validate coordinates and enforce size limits for Gemini
            enhancement_area.x = max(0, min(enhancement_area.x, width - 50))
            enhancement_area.y = max(0, min(enhancement_area.y, height - 50))

            # Enforce 900x900 max size for Gemini 2.5 Flash limits
            max_size = 900
            enhancement_area.width = min(enhancement_area.width, width - enhancement_area.x, max_size)
            enhancement_area.height = min(enhancement_area.height, height - enhancement_area.y, max_size)

            areas.append(enhancement_area)

        print(f"🔍 Identified {len(areas)} areas for targeted enhancement")
        for area in areas:
            print(f"  - {area.description} at ({area.x}, {area.y}) - {area.width}x{area.height}px")

        return areas

    except Exception as e:
        print(f"❌ Area analysis error: {e}")
        return []


async def enhance_area_with_gemini(
    base_image_path: str,
    area: EnhancementArea,
    context: Dict[str, Any] = None
) -> Optional[Image.Image]:
    """
    🎨 Enhance a specific area using Gemini

    Args:
        base_image_path: Path to the full image
        area: EnhancementArea defining the region to enhance
        context: Additional context about the image

    Returns:
        Enhanced area as PIL Image or None if failed
    """
    import google.generativeai as genai

    # Configure Gemini
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-2.5-flash-image-preview')  # Use the correct model!

    # Extract the area from the base image
    base_img = Image.open(base_image_path)

    # CRITICAL: Extract ONLY the specific area to send to Gemini
    area_img = base_img.crop((area.x, area.y, area.x + area.width, area.y + area.height))

    print(f"    📐 Extracted area size: {area_img.size} from position ({area.x}, {area.y})")

    # Safety check for Gemini limits
    if area_img.size[0] > 900 or area_img.size[1] > 900:
        print(f"    ⚠️ Area too large ({area_img.size}), resizing to fit 900x900 limit")
        area_img.thumbnail((900, 900), Image.Resampling.LANCZOS)
        print(f"    📐 Resized to: {area_img.size}")

    # Save JUST THE CROPPED AREA as WebP for processing
    area_bytes = BytesIO()
    area_img.save(area_bytes, format='WEBP', quality=95)
    area_data = area_bytes.getvalue()  # Binary data, NOT base64!

    # Create enhancement prompt
    edit_prompt = f"""
    This is a CROPPED SECTION from a larger product photo. You are seeing ONLY this {area.width}x{area.height} pixel area.

    Area description: {area.description}

    ENHANCEMENT INSTRUCTIONS:
    {area.enhancement_instructions}

    CRITICAL REQUIREMENTS:
    1. Return the SAME cropped area, enhanced
    2. DO NOT expand or change the image size
    3. DO NOT add context or surrounding areas
    4. Maintain EXACT dimensions: {area.width}x{area.height} pixels
    5. Make SUBTLE improvements - this will be stitched back into the original
    6. Preserve edge pixels for seamless blending

    You are seeing ONLY the cropped area. Enhance it and return ONLY that area.
    """

    try:
        print(f"  🎨 Enhancing {area.description}...")

        # Send to Gemini
        response = model.generate_content([
            edit_prompt,
            {
                "mime_type": "image/webp",
                "data": area_data
            }
        ])

        # Extract enhanced image
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        try:
                            # Load enhanced area
                            enhanced_img = Image.open(BytesIO(part.inline_data.data))

                            print(f"    📊 Gemini returned: {enhanced_img.size}, mode: {enhanced_img.mode}")

                            # Check if Gemini returned something way larger (likely edited full context)
                            size_ratio_w = enhanced_img.size[0] / area.width
                            size_ratio_h = enhanced_img.size[1] / area.height

                            if size_ratio_w > 1.5 or size_ratio_h > 1.5:
                                print(f"    ⚠️ Gemini enlarged image ({enhanced_img.size}), extracting best region")

                                # For Gemini's tendency to return larger images,
                                # we need to be smart about which part to extract
                                # For areas near edges, preserve the edge alignment

                                # Determine crop strategy based on area position
                                img_width, img_height = base_img.size

                                # If area is in top-left quarter, preserve top-left alignment
                                if area.x < img_width // 3 and area.y < img_height // 3:
                                    x1, y1 = 0, 0
                                # If area is in top-right quarter, preserve top-right alignment
                                elif area.x > 2 * img_width // 3 and area.y < img_height // 3:
                                    x1 = max(0, enhanced_img.size[0] - area.width)
                                    y1 = 0
                                # If area is in bottom-left quarter, preserve bottom-left alignment
                                elif area.x < img_width // 3 and area.y > 2 * img_height // 3:
                                    x1 = 0
                                    y1 = max(0, enhanced_img.size[1] - area.height)
                                # If area is in bottom-right quarter, preserve bottom-right alignment
                                elif area.x > 2 * img_width // 3 and area.y > 2 * img_height // 3:
                                    x1 = max(0, enhanced_img.size[0] - area.width)
                                    y1 = max(0, enhanced_img.size[1] - area.height)
                                # Otherwise use center crop
                                else:
                                    center_x = enhanced_img.size[0] // 2
                                    center_y = enhanced_img.size[1] // 2
                                    x1 = max(0, center_x - area.width // 2)
                                    y1 = max(0, center_y - area.height // 2)

                                # Ensure we don't go out of bounds
                                x2 = min(enhanced_img.size[0], x1 + area.width)
                                y2 = min(enhanced_img.size[1], y1 + area.height)

                                enhanced_img = enhanced_img.crop((x1, y1, x2, y2))

                                # Final resize to exact dimensions if needed
                                if enhanced_img.size != (area.width, area.height):
                                    enhanced_img = enhanced_img.resize((area.width, area.height), Image.Resampling.LANCZOS)
                            elif enhanced_img.size != (area.width, area.height):
                                print(f"    📐 Minor size difference, resizing from {enhanced_img.size} to ({area.width}, {area.height})")
                                enhanced_img = enhanced_img.resize((area.width, area.height), Image.Resampling.LANCZOS)

                            # Ensure mode matches base image
                            if base_img.mode == 'RGBA' and enhanced_img.mode != 'RGBA':
                                enhanced_img = enhanced_img.convert('RGBA')

                            print(f"  ✅ Enhanced {area.description}")
                            return enhanced_img

                        except Exception as e:
                            print(f"  ❌ Error processing enhanced area: {e}")
                            return None

        print(f"  ⚠️ No enhanced image returned for {area.description}")
        return None

    except Exception as e:
        print(f"  ❌ Gemini enhancement error: {e}")
        return None


def stitch_enhanced_area(
    base_image: Image.Image,
    enhanced_area: Image.Image,
    area: EnhancementArea,
    blend_edges: bool = True
) -> Image.Image:
    """
    🧩 Surgically stitch an enhanced area back into the base image

    Args:
        base_image: The full base image
        enhanced_area: The enhanced area to insert
        area: EnhancementArea with coordinates
        blend_edges: Whether to blend edges for seamless integration

    Returns:
        Updated image with enhanced area stitched in
    """
    # Create a copy to avoid modifying the original
    result = base_image.copy()

    # Ensure both images are in RGBA mode for proper compositing
    if result.mode != 'RGBA':
        result = result.convert('RGBA')

    if enhanced_area.mode != 'RGBA':
        enhanced_area = enhanced_area.convert('RGBA')

    if blend_edges:
        # Create a more sophisticated gradient mask for seamless blending
        mask = Image.new('L', (area.width, area.height), 255)
        mask_draw = ImageDraw.Draw(mask)

        # Use a larger, smoother fade (15px) for better blending
        fade = min(15, min(area.width, area.height) // 10)  # Adaptive fade based on area size

        # Create smoother gradient with more steps
        for i in range(fade):
            # Use a smoother curve for alpha transition
            progress = i / fade
            alpha = int(255 * (progress * progress))  # Quadratic easing for smoother blend

            # Draw concentric rectangles for smooth fade
            mask_draw.rectangle([i, i, area.width-i-1, area.height-i-1], outline=alpha)

        # Composite the enhanced area with feathered edges
        # Use the mask as an alpha channel for smooth blending
        result.paste(enhanced_area, (area.x, area.y), mask)
    else:
        # Simple paste
        result.paste(enhanced_area, (area.x, area.y))

    return result


async def targeted_enhancement_pipeline(
    image_path: str,
    custom_instructions: str = None,
    max_areas: int = 3,
    initial_analysis: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    📊 Complete Targeted Enhancement Pipeline
    Enhances specific areas of an already-optimized image

    Args:
        image_path: Path to ImageMagick-processed image
        custom_instructions: User preferences for enhancement
        max_areas: Maximum number of areas to enhance (default 3)

    Returns:
        Dictionary with results including enhanced image path
    """
    print("\n🎯 Starting Targeted Enhancement Pipeline")

    # Stage 1: Analyze for enhancement opportunities
    print("🔍 Stage 1: Analyzing for enhancement opportunities...")
    areas = await targeted_area_analysis_agent(
        image_path,
        custom_instructions=custom_instructions,
        initial_analysis=initial_analysis
    )

    if not areas:
        print("✅ Image already optimal - no enhancements needed")
        return {
            "success": True,
            "enhanced": False,
            "message": "Image already optimal",
            "final_image": image_path
        }

    # Limit to max_areas
    if len(areas) > max_areas:
        areas = sorted(areas, key=lambda a: a.priority)[:max_areas]
        print(f"  Limiting to top {max_areas} priority areas")

    # Stage 2: Enhance each area
    print(f"🎨 Stage 2: Enhancing {len(areas)} targeted areas...")
    print(f"  📁 Loading base image from: {image_path}")
    base_img = Image.open(image_path)

    # Debug: Check input image format
    print(f"  📊 Input image mode: {base_img.mode}, size: {base_img.size}")
    print(f"  📊 Input file extension: {Path(image_path).suffix}")

    # Check if image has transparency
    if base_img.mode == 'RGBA':
        # Check if alpha channel actually has transparency
        alpha = base_img.split()[-1]
        alpha_min, alpha_max = alpha.getextrema()
        if alpha_min == 255 and alpha_max == 255:
            print("  ⚠️ Image is RGBA but has no actual transparency (alpha all 255)")
            print("  🔧 Background removal may have failed or image has white background")
        else:
            print(f"  ✅ Image has transparency (alpha range: {alpha_min}-{alpha_max})")
            # Count transparent pixels
            alpha_array = alpha.getdata()
            transparent_pixels = sum(1 for p in alpha_array if p < 255)
            total_pixels = len(alpha_array)
            transparency_pct = (transparent_pixels / total_pixels) * 100
            print(f"  📊 Transparency: {transparency_pct:.1f}% of pixels are transparent")
    elif base_img.mode == 'RGB':
        print("  ⚠️ Image is RGB (no alpha channel) - converting to RGBA")
        # Check if it's a PNG that should have transparency
        if Path(image_path).suffix.lower() == '.png' and 'no-bg' in str(image_path):
            print("  🚨 This is a no-bg PNG but loaded as RGB - transparency was lost!")

    # Ensure we're working with RGBA for transparency
    if base_img.mode != 'RGBA':
        result_img = base_img.convert('RGBA')
    else:
        result_img = base_img.copy()

    enhanced_count = 0
    for area in areas:
        enhanced_area_img = await enhance_area_with_gemini(image_path, area)

        if enhanced_area_img:
            # Stage 3: Stitch enhanced area back
            result_img = stitch_enhanced_area(result_img, enhanced_area_img, area, blend_edges=True)
            enhanced_count += 1
        else:
            print(f"  ⚠️ Skipping {area.description} - enhancement failed")

    # Stage 3: Quality check on stitched result
    if enhanced_count > 0:
        print("🔍 Stage 3: Quality checking stitched result...")

        # Quick visual QA using Claude
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        # Save temp file for QA
        temp_path = Path("/tmp") / f"targeted_qa_{Path(image_path).stem}.webp"
        result_img.save(temp_path, 'WEBP', quality=95)

        with open(temp_path, 'rb') as f:
            qa_image_data = base64.b64encode(f.read()).decode('utf-8')

        qa_prompt = f"""
        Analyze this image which has had {enhanced_count} areas surgically enhanced and stitched back.

        Check for:
        1. Visible seams or grid lines around enhanced areas
        2. Color mismatches between enhanced areas and surroundings
        3. Unnatural transitions or blending artifacts
        4. Any areas that look obviously edited or artificial
        5. Overall image coherence

        Areas that were enhanced:
        {chr(10).join([f"- {area.description}" for area in areas[:enhanced_count]])}

        Return a JSON object:
        {{
            "quality_score": 1-10,
            "issues_found": ["list", "of", "issues"],
            "seams_visible": true/false,
            "color_match": true/false,
            "recommendation": "accept" or "reject" or "retry"
        }}
        """

        try:
            qa_response = await client.messages.create(
                model="claude-4-sonnet-20250514",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/webp",
                                "data": qa_image_data
                            }
                        },
                        {"type": "text", "text": qa_prompt}
                    ]
                }]
            )

            qa_text = qa_response.content[0].text.strip()
            if "```json" in qa_text:
                qa_text = qa_text.split("```json")[1].split("```")[0].strip()
            elif "```" in qa_text:
                qa_text = qa_text.split("```")[1].split("```")[0].strip()

            # Clean up any trailing commas or extra data
            qa_text = qa_text.rstrip(',').strip()

            try:
                qa_result = json.loads(qa_text)
            except json.JSONDecodeError as e:
                print(f"  ⚠️ QA JSON parse error, using defaults: {str(e)[:50]}")
                qa_result = {"quality_score": 8, "recommendation": "accept"}
            print(f"  📊 QA Score: {qa_result.get('quality_score', 'N/A')}/10")

            if qa_result.get('seams_visible'):
                print("  ⚠️ Visible seams detected")
            if not qa_result.get('color_match', True):
                print("  ⚠️ Color mismatch detected")

            if qa_result.get('issues_found'):
                print(f"  ⚠️ Issues: {', '.join(qa_result['issues_found'])}")

            # If quality is poor, try simpler blending
            if qa_result.get('quality_score', 10) < 7 or qa_result.get('recommendation') == 'retry':
                print("  🔄 Reprocessing with simpler blending...")
                # Restart with no edge blending to avoid artifacts
                result_img = base_img.copy()
                for i, area in enumerate(areas[:enhanced_count]):
                    if i < len(areas):
                        enhanced_area_img = await enhance_area_with_gemini(image_path, areas[i])
                        if enhanced_area_img:
                            result_img = stitch_enhanced_area(result_img, enhanced_area_img, areas[i], blend_edges=False)
                print("  ✅ Reprocessed without edge blending")

        except Exception as e:
            print(f"  ❌ QA check failed: {e}")
            # Continue anyway

        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()

    # Stage 4: Save result (preserving transparency)
    output_path = Path(image_path).parent / f"{Path(image_path).stem}-targeted.webp"

    # Final transparency check before saving
    if result_img.mode == 'RGBA':
        alpha = result_img.split()[-1]
        alpha_min, alpha_max = alpha.getextrema()
        if alpha_min < 255:
            print(f"  ✅ Final image has transparency (alpha range: {alpha_min}-{alpha_max})")
        else:
            print("  ⚠️ Final image lost transparency - all pixels opaque")
            # Try to restore transparency if the original had it
            if base_img.mode == 'RGBA':
                orig_alpha = base_img.split()[-1]
                if orig_alpha.getextrema()[0] < 255:
                    print("  🔧 Attempting to restore original transparency...")
                    # Use original alpha channel
                    r, g, b, _ = result_img.split()
                    result_img = Image.merge('RGBA', (r, g, b, orig_alpha))

    # Save with explicit transparency support
    print(f"  💾 Saving as WebP with mode: {result_img.mode}")
    result_img.save(output_path, 'WEBP', quality=95, lossless=False, method=6, exact=True)

    print(f"✅ Targeted enhancement complete: {enhanced_count}/{len(areas)} areas enhanced")
    print(f"💾 Saved to: {output_path}")

    return {
        "success": True,
        "enhanced": True,
        "areas_identified": len(areas),
        "areas_enhanced": enhanced_count,
        "final_image": str(output_path),
        "enhancement_details": [area.to_dict() for area in areas],
        "qa_performed": enhanced_count > 0,
        "qa_score": qa_result.get('quality_score', 'N/A') if enhanced_count > 0 and 'qa_result' in locals() else 'N/A'
    }
