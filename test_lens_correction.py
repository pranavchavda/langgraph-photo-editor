#!/usr/bin/env python3
"""Test lens correction on the Nurri espresso machine image"""

from src.lens_corrections_advanced import apply_lens_corrections
from PIL import Image
import os

# Input and output paths
input_path = "/home/pranav/langgraph-photo-editor/113Nurri Type L Chrome+Zebra.jpg"
output_path = "/tmp/test_lens_corrected.jpg"

# Get original dimensions
original = Image.open(input_path)
print(f"Original dimensions: {original.size}")

# Apply lens corrections
result = apply_lens_corrections(
    image_path=input_path,
    output_path=output_path,
    selected_lens=None,  # Auto-detect from EXIF
    focal_length=None
)

print(f"\nResult: {result}")

# Check output dimensions
if os.path.exists(output_path):
    corrected = Image.open(output_path)
    print(f"Corrected dimensions: {corrected.size}")
    
    if corrected.size != original.size:
        print(f"WARNING: Dimensions changed! Original: {original.size}, Corrected: {corrected.size}")
    else:
        print("✓ Dimensions preserved")