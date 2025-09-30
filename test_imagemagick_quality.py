#!/usr/bin/env python3
"""
Test ImageMagick quality behavior with and without explicit quality flags
"""

import subprocess
import tempfile
from pathlib import Path
from PIL import Image
import os

def test_imagemagick_conversions():
    """Test various ImageMagick conversions to understand quality behavior"""

    print("Testing ImageMagick Quality Behavior")
    print("=" * 50)

    # Create a test image
    test_img = Image.new('RGB', (1920, 1080))
    pixels = test_img.load()
    for i in range(1920):
        for j in range(1080):
            # Create a gradient pattern
            pixels[i, j] = (i % 256, j % 256, (i + j) % 256)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Save as high-quality WebP (simulating AVIF)
        source_webp = tmpdir / "source.webp"
        test_img.save(str(source_webp), 'WEBP', quality=100, lossless=True)
        source_size = source_webp.stat().st_size
        print(f"\nSource WebP (lossless): {source_size:,} bytes")

        # Test 1: Convert without quality flag
        output1 = tmpdir / "output_no_quality.webp"
        cmd1 = ["magick", str(source_webp), str(output1)]
        result1 = subprocess.run(cmd1, capture_output=True)

        if result1.returncode == 0:
            size1 = output1.stat().st_size
            print(f"Without -quality flag: {size1:,} bytes ({size1/source_size:.1%} of source)")
        else:
            print(f"Error without quality: {result1.stderr.decode()}")

        # Test 2: Convert with quality 95
        output2 = tmpdir / "output_quality_95.webp"
        cmd2 = ["magick", str(source_webp), "-quality", "95", str(output2)]
        result2 = subprocess.run(cmd2, capture_output=True)

        if result2.returncode == 0:
            size2 = output2.stat().st_size
            print(f"With -quality 95: {size2:,} bytes ({size2/source_size:.1%} of source)")
        else:
            print(f"Error with quality 95: {result2.stderr.decode()}")

        # Test 3: Convert with quality 100
        output3 = tmpdir / "output_quality_100.webp"
        cmd3 = ["magick", str(source_webp), "-quality", "100", str(output3)]
        result3 = subprocess.run(cmd3, capture_output=True)

        if result3.returncode == 0:
            size3 = output3.stat().st_size
            print(f"With -quality 100: {size3:,} bytes ({size3/source_size:.1%} of source)")
        else:
            print(f"Error with quality 100: {result3.stderr.decode()}")

        # Test 4: WebP to PNG without quality
        png_output = tmpdir / "output.png"
        cmd4 = ["magick", str(source_webp), str(png_output)]
        result4 = subprocess.run(cmd4, capture_output=True)

        if result4.returncode == 0:
            png_size = png_output.stat().st_size
            print(f"\nWebP to PNG (no quality): {png_size:,} bytes")

            # Test 5: PNG back to WebP without quality
            webp_from_png = tmpdir / "from_png_no_quality.webp"
            cmd5 = ["magick", str(png_output), str(webp_from_png)]
            result5 = subprocess.run(cmd5, capture_output=True)

            if result5.returncode == 0:
                size5 = webp_from_png.stat().st_size
                print(f"PNG to WebP (no quality): {size5:,} bytes ({size5/source_size:.1%} of source)")

            # Test 6: PNG to WebP with quality 100
            webp_from_png_100 = tmpdir / "from_png_quality_100.webp"
            cmd6 = ["magick", str(png_output), "-quality", "100", str(webp_from_png_100)]
            result6 = subprocess.run(cmd6, capture_output=True)

            if result6.returncode == 0:
                size6 = webp_from_png_100.stat().st_size
                print(f"PNG to WebP (quality 100): {size6:,} bytes ({size6/source_size:.1%} of source)")

def test_default_quality():
    """Test ImageMagick's default quality settings"""
    print("\n\nTesting ImageMagick Default Quality")
    print("=" * 50)

    # Check ImageMagick's default quality
    result = subprocess.run(["magick", "-list", "configure"], capture_output=True, text=True)
    if result.returncode == 0:
        for line in result.stdout.split('\n'):
            if 'WEBP' in line or 'quality' in line.lower():
                print(line)

    # Get version info
    result = subprocess.run(["magick", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        print("\nImageMagick Version:")
        print(result.stdout.split('\n')[0])

if __name__ == "__main__":
    # Check if ImageMagick is available
    result = subprocess.run(["which", "magick"], capture_output=True)
    if result.returncode != 0:
        print("ImageMagick not found. Trying 'convert'...")
        result = subprocess.run(["which", "convert"], capture_output=True)
        if result.returncode != 0:
            print("ImageMagick not installed!")
            exit(1)

    test_imagemagick_conversions()
    test_default_quality()

    print("\n\n⚠️  KEY FINDINGS:")
    print("1. ImageMagick WITHOUT -quality flag uses a LOW default (often 75)")
    print("2. This causes significant quality loss in format conversions")
    print("3. ALWAYS specify -quality explicitly for conversions")
    print("4. For lossless: use -quality 100")
    print("5. For high quality: use -quality 95-98")