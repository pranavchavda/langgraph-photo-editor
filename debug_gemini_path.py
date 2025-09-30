#!/usr/bin/env python3
"""
Debug script to trace the image path through the workflow
"""

import os
import sys

# Set up the environment to trace Gemini-only editing
os.environ["SKIP_BACKGROUND_REMOVAL"] = "true"
os.environ["SKIP_IMAGEMAGICK"] = "true"
os.environ["USE_AI_UPSCALING"] = "false"
os.environ["SKIP_LENS_CORRECTION"] = "true"
os.environ["SKIP_REPAIR"] = "true"

print("🔍 Environment configured for Gemini-only processing:")
print(f"   SKIP_BACKGROUND_REMOVAL: {os.environ.get('SKIP_BACKGROUND_REMOVAL')}")
print(f"   SKIP_IMAGEMAGICK: {os.environ.get('SKIP_IMAGEMAGICK')}")
print(f"   USE_AI_UPSCALING: {os.environ.get('USE_AI_UPSCALING')}")
print(f"   SKIP_LENS_CORRECTION: {os.environ.get('SKIP_LENS_CORRECTION')}")
print(f"   SKIP_REPAIR: {os.environ.get('SKIP_REPAIR')}")

print("\n📝 Expected workflow path for Gemini-only:")
print("1. Original image → Analysis")
print("2. Analysis → Gemini editing (creates -gemini-edited.webp)")
print("3. Skip ImageMagick")
print("4. Skip background removal")
print("5. Quality control on Gemini output")
print("6. Return Gemini output (possibly renamed for quality)")

print("\n⚠️ Potential issues to check:")
print("1. Is background removal REALLY being skipped?")
print("2. Is the final_image_path correctly pointing to Gemini output?")
print("3. Is quality renaming changing the path unexpectedly?")
print("4. Is the Streamlit app loading from the correct path?")

print("\n💡 Debug points added to workflow:")
print("- Line 421-425: Gemini output path logging")
print("- Line 469-470: Background removal skip logging")
print("- Line 573-574: Final image path logging")

print("\n✅ To test:")
print("1. Run Streamlit app")
print("2. Upload an image")
print("3. Check ONLY 'Use Gemini 2.5 Flash'")
print("4. Process the image")
print("5. Check console output for DEBUG messages")
print("6. Verify the displayed image matches the Gemini output")