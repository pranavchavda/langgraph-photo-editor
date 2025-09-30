"""
Batch Consistency Module
Ensures visual consistency across all images in a batch
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import numpy as np
import base64
from io import BytesIO
import os
import json
from dataclasses import dataclass
from anthropic import AsyncAnthropic


@dataclass
class BatchProfile:
    """Stores consistent parameters for batch processing"""
    # Color and exposure targets
    avg_brightness: float
    target_brightness: float
    brightness_adjustment: str  # ImageMagick command

    # Color balance
    avg_saturation: float
    target_saturation: float
    color_correction: str

    # Style consistency
    enhancement_level: str  # "subtle", "moderate", "strong"
    sharpness_level: float

    # Common issues across batch
    common_problems: List[str]
    lighting_style: str  # "studio", "natural", "mixed"

    # Gemini instructions template
    gemini_template: str
    imagemagick_base: str


async def analyze_batch_consistency(
    image_paths: List[str],
    custom_instructions: Optional[str] = None
) -> BatchProfile:
    """
    Analyze all images in batch to determine consistent processing parameters

    This runs BEFORE individual processing to establish baseline consistency
    """
    client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    # Sample up to 5 representative images for batch analysis
    sample_size = min(5, len(image_paths))
    sample_paths = image_paths[:sample_size] if sample_size < 5 else [
        image_paths[i * len(image_paths) // sample_size] for i in range(sample_size)
    ]

    # Create composite preview for batch analysis
    thumbnails = []
    for path in sample_paths:
        img = Image.open(path)
        # Create small thumbnail for batch preview
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        thumbnails.append(img)

    # Create grid of thumbnails
    grid_width = min(3, len(thumbnails))
    grid_height = (len(thumbnails) + grid_width - 1) // grid_width
    grid_size = (grid_width * 400, grid_height * 400)
    grid = Image.new('RGB', grid_size, (255, 255, 255))

    for i, thumb in enumerate(thumbnails):
        x = (i % grid_width) * 400
        y = (i // grid_width) * 400
        # Center thumbnail in its grid cell
        x_offset = (400 - thumb.width) // 2
        y_offset = (400 - thumb.height) // 2
        grid.paste(thumb, (x + x_offset, y + y_offset))

    # Convert grid to base64
    buffer = BytesIO()
    grid.save(buffer, format='JPEG', quality=85)
    grid_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # Analyze batch for consistency
    batch_prompt = f"""
    Analyze this batch of {len(image_paths)} product images (showing {sample_size} samples).

    Your goal is to establish CONSISTENT processing parameters for the entire batch.

    {f"User requirements: {custom_instructions}" if custom_instructions else ""}

    Analyze:
    1. Overall brightness/exposure levels - what's the average and target?
    2. Color consistency - do they have similar white balance? saturation?
    3. Common issues across all images (dust, reflections, etc.)
    4. Lighting style (studio, natural, mixed)
    5. Product types and materials

    Return a JSON object with:
    {{
        "brightness_analysis": {{
            "average": "dark/normal/bright",
            "variance": "low/medium/high",
            "target": "slightly brighter/maintain/slightly darker",
            "adjustment": "-2"
        }},
        "color_analysis": {{
            "white_balance": "cool/neutral/warm",
            "saturation": "low/normal/high",
            "consistency": "consistent/variable",
            "correction_needed": true
        }},
        "common_issues": ["dust", "reflections", "color cast"],
        "lighting_style": "studio",
        "materials": ["chrome", "wood", "plastic"],
        "recommended_approach": {{
            "enhancement_level": "moderate",
            "priority": "consistency",
            "imagemagick_base": "-brightness-contrast 0x2 -modulate 100,102,100",
            "gemini_focus": "enhance product details while maintaining consistency"
        }}
    }}

    IMPORTANT:
    1. Prioritize CONSISTENCY across the batch over individual perfection
    2. Return ONLY the JSON object, no additional text or explanation
    3. Ensure the JSON is valid and complete
    """

    try:
        response = await client.messages.create(
            model="claude-4-sonnet-20250514",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": grid_base64
                        }
                    },
                    {"type": "text", "text": batch_prompt}
                ]
            }]
        )

        # Parse response
        text = response.content[0].text.strip()

        # Extract JSON from various formats
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        elif "{" in text:
            # Find the JSON object boundaries
            start = text.find("{")
            # Find matching closing brace
            brace_count = 0
            end = start
            for i in range(start, len(text)):
                if text[i] == "{":
                    brace_count += 1
                elif text[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            text = text[start:end]

        # Clean up any trailing commas or extra data
        text = text.strip()
        if text.endswith(","):
            text = text[:-1]

        try:
            analysis = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error: {e}")
            print(f"  Attempted to parse: {text[:200]}...")
            raise

        # Build consistent processing profile
        brightness_adj = analysis['brightness_analysis'].get('adjustment', '0')
        try:
            brightness_val = int(brightness_adj.replace('+', '').replace(' ', '').split('to')[0])
        except:
            brightness_val = 0

        # Conservative ImageMagick base command for consistency
        imagemagick_base = analysis['recommended_approach'].get(
            'imagemagick_base',
            f'-brightness-contrast {brightness_val}x2 -modulate 100,102,100'
        )

        # Ensure commands are within safe limits
        imagemagick_base = imagemagick_base.replace('-normalize', '').replace('-auto-level', '')

        # Build Gemini template for consistency
        gemini_template = f"""
        Process this image as part of a batch with these consistency requirements:
        - Target brightness: {analysis['brightness_analysis']['target']}
        - Enhancement level: {analysis['recommended_approach']['enhancement_level']}
        - Focus areas: {analysis['recommended_approach'].get('gemini_focus', 'product details')}
        - Maintain consistency with: {analysis['color_analysis']['white_balance']} white balance

        Common batch issues to address: {', '.join(analysis.get('common_issues', []))}

        IMPORTANT: Maintain visual consistency with other images in the batch.
        Apply similar enhancement levels and color grading.
        """

        return BatchProfile(
            avg_brightness=0.5,  # Normalized value
            target_brightness=0.5 + (brightness_val * 0.05),
            brightness_adjustment=f"{brightness_val:+d}",
            avg_saturation=0.5,
            target_saturation=0.52 if analysis['recommended_approach']['enhancement_level'] != 'subtle' else 0.5,
            color_correction=analysis['color_analysis'].get('white_balance', 'neutral'),
            enhancement_level=analysis['recommended_approach']['enhancement_level'],
            sharpness_level=0.7 if analysis['recommended_approach']['enhancement_level'] == 'moderate' else 0.5,
            common_problems=analysis.get('common_issues', []),
            lighting_style=analysis.get('lighting_style', 'mixed'),
            gemini_template=gemini_template.strip(),
            imagemagick_base=imagemagick_base
        )

    except Exception as e:
        print(f"⚠️ Batch analysis failed: {e}, using defaults")
        # Return conservative defaults
        return BatchProfile(
            avg_brightness=0.5,
            target_brightness=0.5,
            brightness_adjustment="0",
            avg_saturation=0.5,
            target_saturation=0.5,
            color_correction="neutral",
            enhancement_level="moderate",
            sharpness_level=0.6,
            common_problems=[],
            lighting_style="mixed",
            gemini_template="Enhance this product image with moderate improvements",
            imagemagick_base="-brightness-contrast 0x2 -modulate 100,102,100"
        )


def apply_batch_profile_to_analysis(
    individual_analysis: Dict[str, Any],
    batch_profile: BatchProfile
) -> Dict[str, Any]:
    """
    Modify individual image analysis to incorporate batch consistency parameters
    """
    # Override with batch-consistent parameters
    if 'imagemagick_command' in individual_analysis:
        # Blend individual needs with batch consistency
        # Start with batch base command
        individual_analysis['imagemagick_command'] = batch_profile.imagemagick_base

        # Add individual-specific adjustments only if critical
        if 'critical_issues' in individual_analysis:
            # Allow some individual adjustment but keep it minimal
            pass

    # Update Gemini instructions with batch template
    if 'gemini_instructions' in individual_analysis:
        individual_analysis['gemini_instructions'] = (
            batch_profile.gemini_template + "\n\n" +
            "Specific to this image: " + individual_analysis.get('gemini_instructions', '')
        )

    # Ensure enhancement level matches batch
    individual_analysis['enhancement_level'] = batch_profile.enhancement_level

    # Add batch context
    individual_analysis['batch_context'] = {
        'lighting_style': batch_profile.lighting_style,
        'target_brightness': batch_profile.target_brightness,
        'enhancement_level': batch_profile.enhancement_level,
        'common_problems': batch_profile.common_problems
    }

    return individual_analysis


async def process_batch_with_consistency(
    image_paths: List[str],
    custom_instructions: Optional[str] = None,
    output_dir: Optional[str] = None,
    max_concurrent: int = 3
) -> Dict[str, Any]:
    """
    Process batch with consistency analysis first
    """
    from .workflow_enhanced import process_single_image_enhanced

    print("🔍 Analyzing batch for consistency...")

    # Step 1: Analyze batch for consistency
    batch_profile = await analyze_batch_consistency(image_paths, custom_instructions)

    print(f"📊 Batch Profile:")
    print(f"  - Enhancement: {batch_profile.enhancement_level}")
    print(f"  - Brightness adj: {batch_profile.brightness_adjustment}")
    print(f"  - Lighting: {batch_profile.lighting_style}")
    print(f"  - Base command: {batch_profile.imagemagick_base}")

    # Step 2: Process images with consistent parameters
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_profile(image_path: str) -> Dict[str, Any]:
        async with semaphore:
            # Set environment variable to pass batch profile
            os.environ['BATCH_IMAGEMAGICK_BASE'] = batch_profile.imagemagick_base
            os.environ['BATCH_GEMINI_TEMPLATE'] = batch_profile.gemini_template
            os.environ['BATCH_ENHANCEMENT_LEVEL'] = batch_profile.enhancement_level

            try:
                result = await process_single_image_enhanced(
                    image_path,
                    custom_instructions,
                    output_dir
                )
                result['batch_consistent'] = True
                return result
            finally:
                # Clean up env vars
                os.environ.pop('BATCH_IMAGEMAGICK_BASE', None)
                os.environ.pop('BATCH_GEMINI_TEMPLATE', None)
                os.environ.pop('BATCH_ENHANCEMENT_LEVEL', None)

    # Process all images
    tasks = [process_with_profile(str(path)) for path in image_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Compile results
    successful = sum(1 for r in results if isinstance(r, dict) and r.get("qc_passed", False))
    failed = len(results) - successful

    return {
        "total_images": len(image_paths),
        "successful": successful,
        "failed": failed,
        "results": results,
        "batch_profile": {
            "enhancement_level": batch_profile.enhancement_level,
            "brightness_adjustment": batch_profile.brightness_adjustment,
            "lighting_style": batch_profile.lighting_style
        },
        "consistency_applied": True,
        "success_rate": successful / len(image_paths) if image_paths else 0
    }
