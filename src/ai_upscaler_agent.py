"""
Google AI Upscaler Agent - Uses AI to upscale images instead of local resampling
Supports both Vertex AI and Merchant API approaches
"""

import os
import json
import base64
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, Any, Optional, Literal
from PIL import Image
import io
import tempfile
import subprocess

class AIUpscalerAgent:
    """Agent for AI-powered image upscaling using Google APIs"""
    
    def __init__(self, service: Literal["vertex", "merchant"] = "vertex"):
        """
        Initialize the upscaler with chosen service
        
        Args:
            service: Which Google service to use ("vertex" or "merchant")
        """
        self.service = service
        self.project_id = os.getenv('GCP_PROJECT_ID', 'atomic-airship-228716')
        
        if service == "vertex":
            # Vertex AI endpoint for image upscaling
            self.api_endpoint = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/us-central1/publishers/google/models/imagegeneration:predict"
        else:
            # Merchant API endpoint
            merchant_id = os.getenv('MERCHANT_CENTER_ID', '7893408')
            self.api_endpoint = f"https://merchantapi.googleapis.com/v1/accounts/{merchant_id}/productImages:upscale"
    
    def get_auth_token(self) -> str:
        """Get authentication token based on service type"""
        try:
            if self.service == "vertex":
                # Use regular gcloud auth for Vertex AI
                result = subprocess.run(
                    ["gcloud", "auth", "print-access-token"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            else:
                # Merchant API might need different auth
                # For now, use same token but this might need adjustment
                result = subprocess.run(
                    ["gcloud", "auth", "print-access-token"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to get auth token: {e}")
    
    async def upscale_vertex(
        self,
        image_path: str,
        scale_factor: Literal["x2", "x4"] = "x2",
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upscale image using Vertex AI
        
        Args:
            image_path: Path to input image
            scale_factor: Upscaling factor ("x2" or "x4")
            output_path: Optional output path
        
        Returns:
            Dict with status and output path or error
        """
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Get original dimensions for logging
            original_img = Image.open(image_path)
            orig_width, orig_height = original_img.size
            print(f"🔍 Original size: {orig_width}x{orig_height}")
            
            # Build request payload for Vertex AI
            payload = {
                "instances": [
                    {
                        "image": {
                            "bytesBase64Encoded": image_base64
                        }
                    }
                ],
                "parameters": {
                    "sampleCount": 1,  # Required for upscaling mode
                    "mode": "upscale",
                    "upscaleConfig": {
                        "upscaleFactor": scale_factor
                    }
                }
            }
            
            # Get auth token
            token = self.get_auth_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            print(f"📤 Sending to Vertex AI for {scale_factor} upscaling...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "status": "error",
                            "error": f"Vertex AI error {response.status}: {error_text[:200]}"
                        }
                    
                    result = await response.json()
                    
                    # Extract upscaled image
                    if "predictions" in result and len(result["predictions"]) > 0:
                        prediction = result["predictions"][0]
                        
                        if "bytesBase64Encoded" in prediction:
                            upscaled_data = base64.b64decode(prediction["bytesBase64Encoded"])
                        else:
                            return {
                                "status": "error",
                                "error": "No image data in response"
                            }
                        
                        # Save to output path
                        if not output_path:
                            output_path = tempfile.mktemp(suffix='.png')
                        
                        with open(output_path, 'wb') as f:
                            f.write(upscaled_data)
                        
                        # Check new dimensions
                        upscaled_img = Image.open(output_path)
                        new_width, new_height = upscaled_img.size
                        print(f"✅ AI Upscaled to: {new_width}x{new_height}")
                        
                        return {
                            "status": "success",
                            "output_path": output_path,
                            "original_size": (orig_width, orig_height),
                            "upscaled_size": (new_width, new_height),
                            "method": "vertex_ai"
                        }
                    else:
                        return {
                            "status": "error",
                            "error": "No predictions in response"
                        }
                        
        except Exception as e:
            return {
                "status": "error",
                "error": f"Vertex AI upscaling failed: {str(e)}"
            }
    
    async def upscale_to_target(
        self,
        image_path: str,
        target_width: int,
        target_height: int,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upscale image to specific target dimensions
        
        Args:
            image_path: Path to input image
            target_width: Target width in pixels
            target_height: Target height in pixels
            output_path: Optional output path
        
        Returns:
            Dict with status and output path or error
        """
        # Load current image
        current_img = Image.open(image_path)
        current_width, current_height = current_img.size
        
        # Calculate required scale factor
        width_scale = target_width / current_width
        height_scale = target_height / current_height
        avg_scale = (width_scale + height_scale) / 2
        
        # Determine which scale factor to use
        if avg_scale <= 2.5:
            scale_factor = "x2"
        elif avg_scale <= 4.5:
            scale_factor = "x4"
        else:
            # For very large upscaling, do x4 then resize
            scale_factor = "x4"
        
        print(f"📊 Need {avg_scale:.1f}x upscaling, using {scale_factor} AI upscaling")
        
        # First do AI upscaling
        result = await self.upscale_vertex(image_path, scale_factor, output_path)
        
        if result["status"] == "success":
            # Check if we need additional resizing
            upscaled_width, upscaled_height = result["upscaled_size"]
            
            if upscaled_width != target_width or upscaled_height != target_height:
                print(f"🔧 Final resize from {upscaled_width}x{upscaled_height} to {target_width}x{target_height}")
                
                # Do final resize to exact dimensions
                upscaled_img = Image.open(result["output_path"])
                final_img = upscaled_img.resize(
                    (target_width, target_height),
                    Image.Resampling.LANCZOS
                )
                final_img.save(result["output_path"], 'PNG', quality=95)
                
                result["final_size"] = (target_width, target_height)
                result["two_stage"] = True
            else:
                result["two_stage"] = False
        
        return result


async def upscale_with_ai(
    image_path: str,
    target_width: int,
    target_height: int,
    output_path: Optional[str] = None,
    service: Literal["vertex", "merchant"] = "vertex"
) -> Dict[str, Any]:
    """
    Convenience function to upscale an image using AI
    
    Args:
        image_path: Path to input image
        target_width: Target width
        target_height: Target height
        output_path: Optional output path
        service: Which Google service to use
    
    Returns:
        Dict with processing results
    """
    agent = AIUpscalerAgent(service=service)
    return await agent.upscale_to_target(
        image_path=image_path,
        target_width=target_width,
        target_height=target_height,
        output_path=output_path
    )


if __name__ == "__main__":
    # Test the upscaler
    async def test():
        # Create a small test image
        test_img = Image.new('RGB', (256, 256), color='red')
        test_path = '/tmp/test_small.png'
        test_img.save(test_path)
        
        agent = AIUpscalerAgent()
        result = await agent.upscale_vertex(test_path, "x2")
        
        if result["status"] == "success":
            print(f"✅ Upscaling successful!")
            print(f"Original: {result['original_size']}")
            print(f"Upscaled: {result['upscaled_size']}")
            print(f"Output: {result['output_path']}")
        else:
            print(f"❌ Error: {result['error']}")
    
    asyncio.run(test())