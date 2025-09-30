#!/usr/bin/env python3
"""
Compare AI upscaling vs Lanczos upscaling
"""

import asyncio
import sys
import os
from pathlib import Path
from PIL import Image
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_upscaler_agent import AIUpscalerAgent

async def compare_methods():
    """Compare AI vs Lanczos upscaling"""
    
    # Use the test image we already created
    test_path = '/tmp/test_simple.jpg'
    
    if not os.path.exists(test_path):
        print("Creating test image...")
        test_img = Image.new('RGB', (200, 200), color='blue')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_img)
        draw.rectangle([50, 50, 150, 150], fill='yellow', outline='red', width=3)
        draw.ellipse([75, 75, 125, 125], fill='green')
        test_img.save(test_path)
    
    original = Image.open(test_path)
    print(f"📸 Original image: {original.size}")
    
    # Method 1: Lanczos upscaling
    print("\n" + "="*50)
    print("Method 1: Traditional Lanczos Upscaling")
    print("="*50)
    
    start_time = time.time()
    lanczos_upscaled = original.resize((400, 400), Image.Resampling.LANCZOS)
    lanczos_path = '/tmp/upscaled_lanczos.png'
    lanczos_upscaled.save(lanczos_path)
    lanczos_time = time.time() - start_time
    
    print(f"✅ Lanczos upscaling completed in {lanczos_time:.3f} seconds")
    print(f"   Output: {lanczos_path}")
    print(f"   Size: {lanczos_upscaled.size}")
    
    # Method 2: AI upscaling
    print("\n" + "="*50)
    print("Method 2: Google AI Upscaling")
    print("="*50)
    
    agent = AIUpscalerAgent(service="vertex")
    
    start_time = time.time()
    result = await agent.upscale_vertex(
        image_path=test_path,
        scale_factor="x2",
        output_path="/tmp/upscaled_ai.png"
    )
    ai_time = time.time() - start_time
    
    if result["status"] == "success":
        print(f"✅ AI upscaling completed in {ai_time:.1f} seconds")
        print(f"   Output: {result['output_path']}")
        print(f"   Size: {result['upscaled_size']}")
    else:
        print(f"❌ Error: {result['error']}")
        return
    
    # Comparison
    print("\n" + "="*50)
    print("📊 Performance Comparison")
    print("="*50)
    
    print(f"Lanczos time: {lanczos_time:.3f} seconds")
    print(f"AI time: {ai_time:.1f} seconds")
    print(f"Speed difference: {ai_time/lanczos_time:.1f}x slower")
    
    print("\n💡 Results:")
    print("- Lanczos: /tmp/upscaled_lanczos.png")
    print("- AI: /tmp/upscaled_ai.png")
    print("\nOpen both images to compare quality!")
    
    # Calculate file sizes
    lanczos_size = os.path.getsize(lanczos_path) / 1024
    ai_size = os.path.getsize(result['output_path']) / 1024
    
    print(f"\n📦 File sizes:")
    print(f"- Lanczos: {lanczos_size:.1f} KB")
    print(f"- AI: {ai_size:.1f} KB")

if __name__ == "__main__":
    asyncio.run(compare_methods())