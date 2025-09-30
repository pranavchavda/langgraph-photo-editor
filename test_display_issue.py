#!/usr/bin/env python3
"""
Test if the Streamlit display issue is with the image path or caching
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import tempfile
import shutil

# Create test images to simulate the workflow
def create_test_images():
    """Create test images to simulate different processing stages"""
    
    temp_dir = tempfile.mkdtemp(prefix="gemini_test_")
    print(f"📁 Test directory: {temp_dir}")
    
    # 1. Original image
    original = Image.new('RGB', (800, 600), 'lightgray')
    draw = ImageDraw.Draw(original)
    draw.text((350, 280), "ORIGINAL", fill='black')
    draw.rectangle([100, 100, 700, 500], outline='black', width=5)
    original_path = os.path.join(temp_dir, "test.jpg")
    original.save(original_path)
    print(f"✅ Original: {original_path}")
    
    # 2. Gemini-edited image (should be visibly different)
    gemini = Image.new('RGB', (800, 600), 'lightgreen')  # Different color!
    draw = ImageDraw.Draw(gemini)
    draw.text((300, 280), "GEMINI EDITED", fill='red')
    draw.rectangle([100, 100, 700, 500], outline='red', width=10)
    draw.ellipse([200, 200, 600, 400], fill='yellow', outline='blue', width=5)
    gemini_path = os.path.join(temp_dir, "test-gemini-edited.webp")
    gemini.save(gemini_path)
    print(f"✅ Gemini edited: {gemini_path}")
    
    # 3. Background removed version (if it gets created)
    bg_removed = Image.new('RGBA', (800, 600), (0, 0, 0, 0))  # Transparent
    draw = ImageDraw.Draw(bg_removed)
    draw.text((250, 280), "BACKGROUND REMOVED", fill='blue')
    draw.ellipse([200, 200, 600, 400], fill='green', outline='red', width=5)
    bg_path = os.path.join(temp_dir, "test-gemini-edited-no-bg.webp")
    bg_removed.save(bg_path)
    print(f"✅ BG removed: {bg_path}")
    
    # 4. Final output (quality renamed)
    final = gemini.copy()  # Should be same as Gemini if no BG removal
    draw = ImageDraw.Draw(final)
    draw.text((50, 50), "FINAL", fill='white')
    final_path = os.path.join(temp_dir, "test-gemini-edited-q9.webp")
    final.save(final_path)
    print(f"✅ Final (renamed): {final_path}")
    
    return {
        'temp_dir': temp_dir,
        'original': original_path,
        'gemini': gemini_path,
        'bg_removed': bg_path,
        'final': final_path
    }

def check_which_image(image_path):
    """Check which image this actually is by looking at its content"""
    img = Image.open(image_path)
    width, height = img.size
    
    # Get the center pixel color as a simple check
    center_pixel = img.getpixel((width//2, height//2))
    
    # Get average color of a region
    box = (350, 250, 450, 350)
    region = img.crop(box)
    colors = region.getcolors(maxcolors=10000)
    
    print(f"\n🔍 Analyzing: {Path(image_path).name}")
    print(f"   Size: {width}x{height}")
    print(f"   Center pixel: {center_pixel}")
    print(f"   File size: {os.path.getsize(image_path)} bytes")
    
    # Try to determine which image it is
    if center_pixel[0] > 200 and center_pixel[1] > 200:  # Bright/light
        if center_pixel[1] > center_pixel[0] and center_pixel[1] > center_pixel[2]:
            print("   → Looks like GEMINI EDITED (green tint)")
        else:
            print("   → Looks like ORIGINAL (gray)")
    else:
        print("   → Looks like modified image")
    
    return img

def simulate_workflow_return(paths, skip_bg_removal=True):
    """Simulate what the workflow would return"""
    
    print("\n" + "="*60)
    print("SIMULATING WORKFLOW RETURN")
    print("="*60)
    
    # Simulate the workflow logic
    current_image = paths['original']
    print(f"1. Start with: {Path(current_image).name}")
    
    # Gemini editing
    current_image = paths['gemini']
    print(f"2. After Gemini: {Path(current_image).name}")
    
    # Background removal (conditional)
    if not skip_bg_removal:
        if os.path.exists(paths['bg_removed']):
            current_image = paths['bg_removed']
            print(f"3. After BG removal: {Path(current_image).name}")
    else:
        print("3. BG removal skipped")
    
    # Quality rename (if needed)
    if os.path.exists(paths['final']):
        final_image = paths['final']
        print(f"4. After quality rename: {Path(final_image).name}")
    else:
        final_image = current_image
        print(f"4. No quality rename, using: {Path(final_image).name}")
    
    print(f"\n📤 Workflow would return: {Path(final_image).name}")
    
    # Check what this image actually is
    returned_img = check_which_image(final_image)
    
    return final_image

def main():
    """Run the display issue test"""
    
    print("🧪 TESTING GEMINI DISPLAY ISSUE")
    print("="*60)
    
    # Create test images
    paths = create_test_images()
    
    # Test 1: With background removal disabled
    print("\n" + "="*60)
    print("TEST 1: Gemini editing with BG removal DISABLED")
    print("="*60)
    os.environ["SKIP_BACKGROUND_REMOVAL"] = "true"
    
    final_1 = simulate_workflow_return(paths, skip_bg_removal=True)
    
    # Test 2: With background removal enabled
    print("\n" + "="*60)
    print("TEST 2: Gemini editing with BG removal ENABLED")
    print("="*60)
    os.environ["SKIP_BACKGROUND_REMOVAL"] = "false"
    
    final_2 = simulate_workflow_return(paths, skip_bg_removal=False)
    
    # Compare all images
    print("\n" + "="*60)
    print("VISUAL COMPARISON")
    print("="*60)
    
    # Create comparison image
    comparison = Image.new('RGB', (800*4, 600), 'white')
    
    for i, (label, path) in enumerate([
        ("ORIGINAL", paths['original']),
        ("GEMINI", paths['gemini']),
        ("BG_REMOVED", paths['bg_removed']),
        ("FINAL", paths['final'])
    ]):
        if os.path.exists(path):
            img = Image.open(path)
            if img.mode == 'RGBA':
                # Convert RGBA to RGB for comparison
                bg = Image.new('RGB', img.size, 'white')
                bg.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                img = bg
            comparison.paste(img, (i*800, 0))
    
    comp_path = "/tmp/gemini_display_comparison.png"
    comparison.save(comp_path)
    print(f"✅ Visual comparison saved to: {comp_path}")
    
    # Clean up
    print(f"\n🧹 Test files in: {paths['temp_dir']}")
    print("   (Not cleaning up for inspection)")

if __name__ == "__main__":
    main()