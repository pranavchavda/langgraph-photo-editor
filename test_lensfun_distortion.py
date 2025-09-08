#!/usr/bin/env python3
"""Test lensfunpy geometry distortion to see if it's cropping"""

import numpy as np
from PIL import Image
import lensfunpy as lf

# Test image path
test_image = "/home/pranav/langgraph-photo-editor/113Nurri Type L Chrome+Zebra.jpg"

print(f"Testing with: {test_image}")

# Load image
img = Image.open(test_image)
img_array = np.array(img)
height, width = img_array.shape[:2]
print(f"Original image shape: {img_array.shape}")
print(f"Original dimensions: {width}x{height}")

# Initialize lensfun database
db = lf.Database()

# Find Sony camera
cameras = [cam for cam in db.cameras if 'Sony' in cam.maker and 'ILCE' in cam.model]
if cameras:
    camera = cameras[0]
    print(f"Using camera: {camera.maker} {camera.model}")
else:
    print("No Sony ILCE camera found")
    exit(1)

# Find the FE 24-70mm lens
all_lenses = db.lenses
fe_24_70_lenses = [l for l in all_lenses if 'FE 24-70mm f/2.8 GM' in l.model or 'FE 24-70mm F2.8 GM' in l.model]

if fe_24_70_lenses:
    lens = fe_24_70_lenses[0]
    print(f"Found lens: {lens.maker} {lens.model}")
    
    # Create modifier
    mod = lf.Modifier(lens, lens.crop_factor, width, height)
    
    # Initialize at 34mm (from EXIF)
    focal_length = 34.0
    aperture = 8.0
    
    print(f"\nInitializing modifier with focal={focal_length}, aperture={aperture}")
    mod.initialize(focal_length, aperture, 1.0, 1.0)
    
    # Test geometry distortion
    print("\n=== Testing Geometry Distortion ===")
    coords = mod.apply_geometry_distortion()
    
    if coords is not None:
        print(f"Coordinates array shape: {coords.shape}")
        coords_reshaped = coords.reshape(height, width, 2)
        
        # Check if coordinates go outside image bounds
        x_coords = coords_reshaped[:, :, 0]
        y_coords = coords_reshaped[:, :, 1]
        
        print(f"X coordinate range: {x_coords.min():.2f} to {x_coords.max():.2f} (image width: {width})")
        print(f"Y coordinate range: {y_coords.min():.2f} to {y_coords.max():.2f} (image height: {height})")
        
        # Check corners specifically
        print("\n=== Corner Coordinates ===")
        print(f"Top-left: ({x_coords[0,0]:.2f}, {y_coords[0,0]:.2f})")
        print(f"Top-right: ({x_coords[0,-1]:.2f}, {y_coords[0,-1]:.2f})")
        print(f"Bottom-left: ({x_coords[-1,0]:.2f}, {y_coords[-1,0]:.2f})")
        print(f"Bottom-right: ({x_coords[-1,-1]:.2f}, {y_coords[-1,-1]:.2f})")
        
        # Check if remapping would cause cropping
        if x_coords.min() < 0 or y_coords.min() < 0:
            print("\n⚠️ WARNING: Coordinates go below 0 - this will cause black borders!")
        if x_coords.max() > width or y_coords.max() > height:
            print("\n⚠️ WARNING: Coordinates exceed image bounds - this will cause cropping!")
            
        # The issue: map_coordinates with mode='reflect' will still produce a full-size image
        # but the content gets shifted/cropped if the distortion moves pixels outside bounds
        
        print("\n=== Testing actual distortion correction ===")
        from scipy.ndimage import map_coordinates
        
        # Apply to a test channel
        img_float = img_array.astype(np.float32) / 255.0
        test_channel = img_float[:, :, 0]
        
        corrected = map_coordinates(
            test_channel,
            [coords_reshaped[:, :, 1], coords_reshaped[:, :, 0]],
            order=1,
            mode='reflect'  # This is the problem - 'reflect' doesn't preserve the full image!
        )
        
        print(f"Corrected shape: {corrected.shape}")
        print("Note: Even though shape is preserved, content may be cropped due to coordinate remapping!")
        
    else:
        print("No geometry distortion correction available")
else:
    print("FE 24-70mm lens not found")