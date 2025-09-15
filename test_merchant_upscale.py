#!/usr/bin/env python3
"""
Test Google Merchant API Product Studio upscaling
"""

import asyncio
import sys
import os
from pathlib import Path
from PIL import Image
import base64
import aiohttp
import json

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

async def test_merchant_upscale():
    """Test upscaling with Merchant API"""
    
    # Use the Nurri espresso machine image
    image_path = "/home/pranav/langgraph-photo-editor/enhanced_enhanced_nurri-cropped (4).jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"📸 Testing with: {Path(image_path).name}")
    
    # Load and check image
    img = Image.open(image_path)
    width, height = img.size
    print(f"   Original size: {width}x{height}")
    
    # Prepare the request
    merchant_id = "7893408"
    api_endpoint = f"https://merchantapi.googleapis.com/v1/accounts/{merchant_id}/productImages:upscale"
    
    print(f"\n🏪 Using Merchant Center ID: {merchant_id}")
    print(f"📍 Endpoint: {api_endpoint}")
    
    # Encode image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    print(f"📦 Image encoded: {len(image_base64)} base64 chars")
    
    # Get auth token
    import subprocess
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True
        )
        token = result.stdout.strip()
        print("✅ Got auth token")
    except Exception as e:
        print(f"❌ Failed to get auth token: {e}")
        return
    
    # Prepare request - Merchant API might have different format
    payload = {
        "image": {
            "rawImageBytes": image_base64  # or might be "imageBytes"
        },
        "upscaleFactor": "2x"  # or might be just "2"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n📤 Sending request to Merchant API...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                api_endpoint,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                print(f"📨 Response status: {response.status}")
                
                response_text = await response.text()
                
                if response.status == 200:
                    print("✅ Success!")
                    result = json.loads(response_text)
                    
                    # Parse response - format might vary
                    if "upscaledImage" in result:
                        print("Found upscaled image in response")
                        # Extract and save
                        upscaled_data = result["upscaledImage"].get("rawImageBytes") or result["upscaledImage"].get("imageBytes")
                        if upscaled_data:
                            upscaled_bytes = base64.b64decode(upscaled_data)
                            output_path = "/tmp/merchant_upscaled.jpg"
                            with open(output_path, 'wb') as f:
                                f.write(upscaled_bytes)
                            print(f"✅ Saved to: {output_path}")
                            
                            # Check new size
                            upscaled_img = Image.open(output_path)
                            print(f"   Upscaled size: {upscaled_img.size}")
                    else:
                        print("Response structure:")
                        print(json.dumps(result, indent=2)[:500])
                else:
                    print(f"❌ API error {response.status}:")
                    try:
                        error_json = json.loads(response_text)
                        print(json.dumps(error_json, indent=2))
                    except:
                        print(response_text[:1000])
                        
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_merchant_upscale())