#!/usr/bin/env python3
"""
Test Google Merchant API Product Image Upscaling using the client library
Based on: https://developers.google.com/merchant/api/samples/upscale-product-image
"""

import os
import sys
from pathlib import Path

def test_merchant_upscale_client():
    """Test using the Merchant API client library"""
    
    try:
        # Try to import the client library
        from google.shopping import merchant_v1beta
        from google.shopping.merchant_v1beta import ImageServiceClient
        from google.shopping.merchant_v1beta.types import (
            UpscaleProductImageRequest,
            InputImage,
            OutputImageConfig
        )
        print("✅ Merchant client library found")
    except ImportError as e:
        print(f"❌ Merchant client library not installed: {e}")
        print("\nTo install, run:")
        print("pip install google-shopping-merchant")
        print("or")
        print("pip install google-cloud-merchant")
        return
    
    # Configuration
    account_id = "7893408"
    image_path = "/home/pranav/langgraph-photo-editor/enhanced_enhanced_nurri-cropped (4).jpg"
    
    print(f"🏪 Merchant Account ID: {account_id}")
    print(f"📸 Image: {Path(image_path).name}")
    
    try:
        # Create client
        client = ImageServiceClient()
        
        # Read image bytes
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        print(f"📦 Image size: {len(image_bytes)} bytes")
        
        # Create request
        request = UpscaleProductImageRequest(
            name=f"accounts/{account_id}",
            output_config=OutputImageConfig(
                return_image_bytes=True  # Return the upscaled image directly
            ),
            input_image=InputImage(
                image_bytes=image_bytes
            )
        )
        
        print("\n📤 Sending upscale request...")
        
        # Call the API
        response = client.upscale_product_image(request=request)
        
        print("✅ Response received!")
        
        # Save the upscaled image
        if response.output_image and response.output_image.image_bytes:
            output_path = "/tmp/merchant_upscaled.jpg"
            with open(output_path, "wb") as f:
                f.write(response.output_image.image_bytes)
            print(f"💾 Saved upscaled image to: {output_path}")
            
            # Check the size
            from PIL import Image
            img = Image.open(output_path)
            print(f"📐 Upscaled size: {img.size}")
        else:
            print("❌ No image data in response")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nPossible issues:")
        print("- API might not be enabled in Google Cloud Console")
        print("- Need to authenticate: gcloud auth application-default login")
        print("- Merchant account might not have access to this feature")

if __name__ == "__main__":
    test_merchant_upscale_client()