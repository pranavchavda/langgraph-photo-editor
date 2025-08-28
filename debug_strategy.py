#!/usr/bin/env python3
"""Debug why analysis agent always chooses ImageMagick"""

import asyncio
import os
import json
import base64
from pathlib import Path
import sys

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from anthropic import AsyncAnthropic

async def debug_analysis_strategy():
    """Debug the analysis agent directly without LangGraph"""
    
    image_path = "/home/pranav/idc/photo_edit_test/Profitec RIDE - WebP 4000x 4000 Quick Edit for in House AI BackGround Removal/102Profitec RIDE.webp"
    custom_instructions = "remove unwanted reflections and enhance the chrome surfaces with advanced AI editing techniques"
    
    print(f"🔍 Testing analysis strategy decision for: {Path(image_path).name}")
    print(f"📝 Custom instructions: {custom_instructions}")
    
    # Load and encode image
    with open(image_path, 'rb') as f:
        image_data = f.read()
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    media_type = "image/webp"
    
    # Create analysis prompt (simplified version)
    analysis_prompt = f"""
    Analyze this product image for editing requirements. Determine if Gemini 2.5 Flash AI editing or ImageMagick is more appropriate.

    **GEMINI** is needed for:
    - Complex material enhancement (chrome, steel surfaces)
    - Selective object editing (enhance chrome without affecting other areas)
    - Background modifications and artifact removal
    - Material-specific enhancements (making steel look more realistic)
    - Removing unwanted reflections or objects
    - Advanced color correction
    
    **IMAGEMAGICK** is sufficient for:
    - Simple brightness/contrast adjustments
    - Basic color saturation changes
    - Sharpening and noise reduction
    - Straightforward optimizations
    
    CUSTOM USER INSTRUCTIONS: {custom_instructions}
    
    Return analysis as JSON with:
    - editing_strategy: "gemini" or "imagemagick" or "both"
    - gemini_instructions: string (detailed instructions for Gemini editing, if needed)
    - editing_explanation: string (why this strategy was chosen)
    """
    
    try:
        anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
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
                    {
                        "type": "text",
                        "text": analysis_prompt
                    }
                ]
            }]
        )
        
        print(f"\n📄 Raw Claude response:")
        print(response.content[0].text)
        
        # Try to extract JSON
        response_text = response.content[0].text.strip()
        
        # Look for JSON block
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "{" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_text = response_text[json_start:json_end]
        else:
            print("❌ No JSON found in response!")
            return
            
        print(f"\n🔍 Extracted JSON:")
        print(json_text)
        
        # Parse JSON
        try:
            result = json.loads(json_text)
            print(f"\n✅ Parsed successfully:")
            print(f"Strategy: {result.get('editing_strategy', 'NOT SET')}")
            print(f"Explanation: {result.get('editing_explanation', 'NOT SET')}")
            print(f"Gemini instructions: {result.get('gemini_instructions', 'NOT SET')}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_analysis_strategy())