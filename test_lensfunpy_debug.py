#!/usr/bin/env python3
"""Debug script to test lensfunpy corrections"""

import numpy as np
from PIL import Image
import lensfunpy as lf
import sys

def test_lensfunpy():
    # Test image path
    test_image = "/tmp/test_espresso.jpg"
    
    # Create a simple test image if it doesn't exist
    if not os.path.exists(test_image):
        print(f"Creating test image at {test_image}")
        img = Image.new('RGB', (800, 600), color='red')
        img.save(test_image)
    
    print(f"Testing with: {test_image}")
    
    # Load image
    img = Image.open(test_image)
    img_array = np.array(img)
    height, width = img_array.shape[:2]
    print(f"Image shape: {img_array.shape}")
    
    # Initialize lensfun database
    db = lf.Database()
    print(f"Database loaded: {db}")
    
    # Search for Sony cameras
    cameras = db.find_cameras("Sony", None)
    print(f"Found {len(cameras)} Sony cameras")
    if cameras:
        camera = cameras[0]
        print(f"Using camera: {camera.maker} {camera.model}")
        
        # Search for Sony FE lenses
        lenses = db.find_lenses(camera, None, "FE")
        print(f"Found {len(lenses)} FE lenses")
        
        if lenses:
            lens = lenses[0]
            print(f"Using lens: {lens.maker} {lens.model}")
            print(f"Lens focal range: {lens.min_focal}-{lens.max_focal}")
            print(f"Lens aperture range: {lens.min_aperture}-{lens.max_aperture}")
            
            # Create modifier
            mod = lf.Modifier(lens, lens.crop_factor, width, height)
            
            # Initialize with parameters
            focal_length = lens.min_focal
            aperture = 2.8
            
            print(f"Initializing with focal_length={focal_length}, aperture={aperture}")
            mod.initialize(focal_length, aperture, 1.0, 1.0)
            
            # Convert to float32
            img_float = img_array.astype(np.float32) / 255.0
            print(f"img_float shape: {img_float.shape}, dtype: {img_float.dtype}")
            
            # Test apply_color_modification
            print("\nTesting apply_color_modification...")
            try:
                result = mod.apply_color_modification(img_float)
                print(f"Result type: {type(result)}")
                print(f"Result value: {result}")
                if isinstance(result, np.ndarray):
                    print(f"Result shape: {result.shape}, dtype: {result.dtype}")
                elif result is None:
                    print("Result is None - no vignetting correction available")
                else:
                    print(f"Unexpected result type: {type(result)}")
                    # Try to see what attributes it has
                    if hasattr(result, '__dict__'):
                        print(f"Result attributes: {result.__dict__}")
                    if hasattr(result, 'shape'):
                        print(f"Has shape attribute: {result.shape}")
                    if hasattr(result, 'dtype'):
                        print(f"Has dtype attribute: {result.dtype}")
                        
                    # Let's try to figure out what this is
                    print(f"Result dir: {dir(result)}")
                    
                    # Try converting it
                    try:
                        if hasattr(result, 'clip'):
                            # Looks like it might be a numpy scalar?
                            print("Has clip method - might be numpy scalar")
                            converted = np.asarray(result)
                            print(f"Converted to array: shape={converted.shape}, dtype={converted.dtype}")
                    except Exception as conv_err:
                        print(f"Conversion error: {conv_err}")
                        
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                
            # Test apply_geometry_distortion
            print("\nTesting apply_geometry_distortion...")
            try:
                coords = mod.apply_geometry_distortion()
                if coords is None:
                    print("No geometry distortion correction available")
                else:
                    print(f"Coords type: {type(coords)}")
                    print(f"Coords shape: {coords.shape if hasattr(coords, 'shape') else 'no shape'}")
            except Exception as e:
                print(f"Geometry error: {e}")

if __name__ == "__main__":
    import os
    test_lensfunpy()