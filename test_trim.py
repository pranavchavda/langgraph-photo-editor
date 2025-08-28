#!/usr/bin/env python3
"""Test the ImageMagick command generation"""

import asyncio
import os
import base64
from anthropic import AsyncAnthropic
import json

async def test_trim_command():
    """Test Claude Sonnet 4 generating trim commands"""
    
    image_path = "/tmp/luce_pid_black_fixed.webp"
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        return
    
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Encode image
    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    
    prompt = """
    Analyze this product image for photo editing optimization. Focus on:

    1. **Surface Materials**: Identify chrome, stainless steel, matte surfaces, glass, plastic
    2. **Lighting Issues**: Harsh shadows, overexposure, underexposure, uneven lighting
    3. **Color Quality**: Saturation levels, color cast issues, vibrancy needs
    4. **Background**: Current background type and removal needs
    5. **Specific Problems**: Reflections, blown highlights, dark shadows, color accuracy

    Return analysis as JSON with these fields:
    - surface_materials: [list of materials detected]  
    - lighting_issues: [list of specific problems]
    - color_problems: [list of color issues]
    - background_type: string description
    - optimization_needs: [priority-ordered list of adjustments needed]
    - imagemagick_command: string (complete ImageMagick parameters like "-trim -brightness-contrast 10x5 -modulate 105,110,100")
    - remove_background: boolean
    - command_explanation: string (brief explanation of what the ImageMagick command will do)
    - special_considerations: [any material-specific notes]

    Be specific and actionable in your analysis.
    
    For imagemagick_command, use any combination of these ImageMagick operations:
    - "-trim" (remove whitespace borders)  
    - "-brightness-contrast BxC" (adjust brightness B and contrast C, e.g., "10x5")
    - "-modulate B,S,H" (brightness B%, saturation S%, hue H%, e.g., "105,110,100")
    - "-gamma G" (gamma correction, e.g., "1.2")
    - "-enhance" (enhance image)
    - "-normalize" (normalize contrast)
    - "-unsharp RxS+G+T" (unsharp mask, e.g., "0x1.5+1.0+0.0")
    - "-border N" (add N pixel border)
    - "-bordercolor color" (border color)
    - Any other ImageMagick parameters you think will improve the image
    
    Example: "-trim -brightness-contrast 5x10 -modulate 102,115,100 -border 20 -bordercolor white"
    
    **CRITICAL CUSTOM INSTRUCTIONS**: trim the image to remove excess whitespace
    
    FOLLOW THESE USER PREFERENCES PRECISELY:
    - If user wants "trim", "crop", or "remove whitespace" -> include "-trim" in imagemagick_command
    - If user wants "darker", "natural", or "less bright" -> use negative brightness values
    - If user wants "brighter" or "more vibrant" -> use positive brightness and saturation
    - If user wants "natural" or "less processed" -> use minimal adjustments
    - The custom instructions OVERRIDE default analysis - prioritize user intent
    - Be conservative - better to under-adjust than over-adjust
    """
    
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user", 
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/webp",
                        "data": image_base64
                    }
                },
                {"type": "text", "text": prompt}
            ]
        }]
    )
    
    response_text = response.content[0].text
    print("🔍 Claude Sonnet 4 Response:")
    print("=" * 80)
    print(response_text)
    print("=" * 80)
    
    # Try to parse the JSON
    try:
        if "{" in response_text and "}" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_text = response_text[json_start:json_end].strip()
            
            parsed = json.loads(json_text)
            print(f"\n📊 Key results:")
            print(f"   ImageMagick command: {parsed.get('imagemagick_command', 'NOT FOUND')}")
            print(f"   Command explanation: {parsed.get('command_explanation', 'NOT FOUND')}")
            print(f"   Remove background: {parsed.get('remove_background', 'NOT FOUND')}")
            
        else:
            print("\n❌ No JSON found")
            
    except Exception as e:
        print(f"\n❌ JSON parsing failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_trim_command())